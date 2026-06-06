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

## LLM Provider: OpenRouter

Switch from HuggingFace to OpenRouter for better model quality.

| Feature | HuggingFace | OpenRouter |
|---------|-------------|------------|
| Free models | ~10B params max | 120B params (Nemotron 3 Super) |
| Rate limit | ~1000 req/day | 200 req/day (with $10 top-up) |
| Quality | Basic | Significantly better |
| API format | Custom | OpenAI-compatible |

**Recommended model**: `nvidia/nemotron-3-super:free` — 120B params, 1M context, best free model available.

**Config changes**:
- `LLM_PROVIDER = "openrouter"`
- `OPENROUTER_API_KEY` in `.env`
- `OPENROUTER_MODEL = "nvidia/nemotron-3-super:free"`
- API base: `https://openrouter.ai/api/v1`

## Data Flow

Batched approach — process articles in groups to respect context window limits:

```
All articles (numbered 1-N)
    ↓
Split into batches of ~10 articles each
    ↓
For each batch:
    LLM Call 1: Extract player names from batch
    LLM Call 2: Extract countries + sentiment from batch
    ↓
Filter ALL unknowns across all batches: remove known players
    ↓
LLM Call 3: Verify ALL unknowns in one batch (if any)
    ↓
Save verified players to learned_players.json
    ↓
Merge all results into classification output
```

**Savings**: From 3N calls (N=articles) to ~0.3N calls (3 calls per ~10 articles).

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

### Call 1 — Extract player names (batch)
```
Extract all football player names from these articles. Each article is numbered.

Return ONLY valid JSON:
{"1": ["Player A", "Player B"], "2": ["Player C"], ...}

Articles:
---ARTICLE 1---
{content_1}
---ARTICLE 2---
{content_2}
...
```

### Call 2 — Extract countries (batch)
```
Extract country mentions from these articles about FIFA World Cup Fantasy.
Each article is numbered. For each country, return sentiment and brief context.

Return ONLY valid JSON:
{"1": [{"name": "Country", "sentiment": "positive|negative|neutral", "context": "..."}], ...}

Articles:
---ARTICLE 1---
{content_1}
---ARTICLE 2---
{content_2}
...
```

### Call 3 — Verify unknown players (single batch)
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

### 1. `config.py`
- Add `OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")`
- Add `OPENROUTER_MODEL = "deepseek/deepseek-chat-v3-0324:free"`
- Update `LLM_PROVIDER` default to `"openrouter"`

### 2. `data/extractor.py`
- Add `OpenRouterProvider` class (OpenAI-compatible API)
- Replace `EXTRACTION_PROMPT` with 3 new prompts:
  - `EXTRACT_PLAYERS_PROMPT`
  - `EXTRACT_COUNTRIES_PROMPT`
  - `VERIFY_PLAYERS_PROMPT`
- Add methods:
  - `extract_player_names(article_text) -> list[str]`
  - `extract_countries(article_text) -> list[dict]`
  - `verify_players(names: list[str]) -> list[dict]`
- Keep HuggingFaceProvider and GeminiProvider as fallbacks

### 3. `data/scraper.py`
- Rewrite `_classify_with_llm()` to use 3 separate calls
- After extraction, run discovery flow for unknown players
- Load known players from `players_reference.py` + `learned_players.json`
- Filter out already-known names
- Call `verify_players()` for unknowns
- Save new verified players to `learned_players.json`
- Return merged results: `{players, countries}`

### 4. `data/players_reference.py`
- Add `get_all_players() -> dict[str, str]` function
- Returns merged dict: `PLAYERS_BY_COUNTRY` + learned players
- Called by `expert_opinions.py` instead of direct `PLAYERS_BY_COUNTRY` access

### 5. `analysis/expert_opinions.py`
- Update `classify_mentions()` to call `get_all_players()` instead of `PLAYERS_BY_COUNTRY`
- No other changes needed

### 6. New file: `data/learned_players.json`
- Created on first run if doesn't exist
- Format: `{"players": {...}, "stats": {...}}`

### 7. `.env.example`
- Add `OPENROUTER_API_KEY=your_key_here`

## Edge Cases

- **Non-Latin names**: Pass 3 prompt explicitly requests Latin/English transliteration
- **Duplicate detection**: Check both `PLAYERS_BY_COUNTRY` and `learned_players.json` before verifying
- **LLM returns non-player**: `is_real: false` → skip, don't save
- **LLM fails**: Log warning, continue with next article, don't block scraping
- **Empty results**: No save, no error
- **Already known player**: Skip verification, use existing data
- **OpenRouter rate limit**: Fall back to HuggingFace if OpenRouter fails

## Exit Criteria

- [ ] Clear logging for all LLM calls (batch progress, results, failures)
- [ ] Unit tests with good coverage (all new functions)
- [ ] Documentation updated (README, config, usage examples)
- [ ] All existing tests pass (63+)
- [ ] Linting clean
- [ ] Committed and pushed

## Testing

- Unit test `get_all_players()` merges correctly
- Unit test `extract_player_names()` parses LLM output
- Unit test `extract_countries()` parses LLM output
- Unit test `verify_players()` filters `is_real: false`
- Unit test `learned_players.json` read/write
- Unit test dedup: known players skipped
- Unit test OpenRouter provider makes correct API calls
- Unit test batch splitting respects size limits
- Integration test: full scrape discovers new player (mock LLM)
