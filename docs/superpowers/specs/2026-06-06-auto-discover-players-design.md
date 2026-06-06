# Auto-Discover Players via LLM Verification

**Date:** 2026-06-06
**Status:** Approved
**Goal:** Automatically discover and verify new football players from scraped articles using LLM, growing the player database over time.

## Problem

Currently `players_reference.py` has ~120 hardcoded players. Expert articles often mention players not in this list (e.g., breakout stars, lesser-known nations). The system misses these mentions entirely.

## Solution

Three LLM calls per article:
1. Extract player names
2. Extract country mentions with sentiment
3. Verify unknown player names — "Is this a real football player? Full name? Country?"

Verified players saved to `data/learned_players.json` and merged into classification at runtime.

## Data Flow

```
Article text
    ↓
LLM Call 1: Extract player names (JSON list)
    ↓
LLM Call 2: Extract countries + sentiment
    ↓
Filter: remove known players (PLAYERS_BY_COUNTRY + learned_players.json)
    ↓
LLM Call 3: Verify unknowns → is_real, full_name (Latin), country
    ↓
Save verified players to learned_players.json
    ↓
Merge all results into classification output
```

## Storage Format

`data/learned_players.json`:
```json
{
  "players": {
    "Khvicha Kvaratskhelia": {
      "country": "Georgia",
      "added_at": "2026-06-06T10:30:00",
      "source": "FantasyFootballScout",
      "verified": true
    }
  },
  "stats": {
    "total_discovered": 15,
    "total_verified": 12,
    "last_scrape": "2026-06-06T10:30:00"
  }
}
```

- `verified: true` — LLM confirmed this is a real player
- `source` — which article discovered them (for auditing)
- `stats` — quick summary without loading all players

## LLM Prompts

### Call 1 — Extract player names
```
Extract all football player names mentioned in this article.
Return ONLY valid JSON: {"players": ["Name 1", "Name 2"]}
Article text: {content}
```

### Call 2 — Extract countries
```
Extract country mentions from this article about FIFA World Cup Fantasy.
For each country, return the sentiment (positive/negative/neutral) and brief context.

Return ONLY valid JSON:
{"countries": [{"name": "Country", "sentiment": "positive|negative|neutral", "context": "brief reason"}]}

Article text: {content}
```

### Call 3 — Verify unknown players
```
For each player name below, verify:
1. Is this a real professional football player?
2. What is their full name in Latin/English characters? (e.g. "Takefusa Kubo" not "久保建英")
3. What country do they play for (national team)?

Return ONLY valid JSON:
{"players": [{"name": "...", "full_name": "...", "country": "...", "is_real": true|false}]}

Names to verify: {unknown_names}
```

## Integration Points

### 1. `data/extractor.py`
- Replace `EXTRACTION_PROMPT` with 3 new prompts:
  - `EXTRACT_PLAYERS_PROMPT`
  - `EXTRACT_COUNTRIES_PROMPT`
  - `VERIFY_PLAYERS_PROMPT`
- Add methods:
  - `extract_player_names(article_text) -> list[str]`
  - `extract_countries(article_text) -> list[dict]`
  - `verify_players(names: list[str]) -> list[dict]`
- All use existing `HuggingFaceProvider` / `GeminiProvider` infrastructure

### 2. `data/scraper.py`
- Rewrite `_classify_with_llm()` to use 3 separate calls
- After extraction, run discovery flow for unknown players
- Load known players from `players_reference.py` + `learned_players.json`
- Filter out already-known names
- Call `verify_players()` for unknowns
- Save new verified players to `learned_players.json`
- Return merged results: `{players, countries}`

### 3. `data/players_reference.py`
- Add `get_all_players() -> dict[str, str]` function
- Returns merged dict: `PLAYERS_BY_COUNTRY` + learned players
- Called by `expert_opinions.py` instead of direct `PLAYERS_BY_COUNTRY` access

### 4. `analysis/expert_opinions.py`
- Update `classify_mentions()` to call `get_all_players()` instead of `PLAYERS_BY_COUNTRY`
- No other changes needed

### 5. New file: `data/learned_players.json`
- Created on first run if doesn't exist
- Format: `{"players": {...}, "stats": {...}}`

## Edge Cases

- **Non-Latin names**: Pass 3 prompt explicitly requests Latin/English transliteration
- **Duplicate detection**: Check both `PLAYERS_BY_COUNTRY` and `learned_players.json` before verifying
- **LLM returns non-player**: `is_real: false` → skip, don't save
- **LLM fails**: Log warning, continue with next article, don't block scraping
- **Empty results**: No save, no error
- **Already known player**: Skip verification, use existing data

## Testing

- Unit test `get_all_players()` merges correctly
- Unit test `extract_player_names()` parses LLM output
- Unit test `extract_countries()` parses LLM output
- Unit test `verify_players()` filters `is_real: false`
- Unit test `learned_players.json` read/write
- Unit test dedup: known players skipped
- Integration test: full scrape discovers new player (mock LLM)
