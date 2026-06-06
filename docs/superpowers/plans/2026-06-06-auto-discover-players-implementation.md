# Auto-Discover Players Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically discover and verify new football players from scraped articles using LLM, growing the player database over time.

**Architecture:** Two-pass LLM extraction (extract → verify) with OpenRouter as primary provider and model fallback array for resilience. Learned players stored in JSON, merged at runtime with hardcoded reference list.

**Tech Stack:** Python, OpenRouter API (OpenAI-compatible), BeautifulSoup (existing), pytest

---

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `config.py` | Modify | Add OpenRouter settings, model array |
| `data/extractor.py` | Modify | Add OpenRouterProvider, new prompts, extraction methods |
| `data/learned_store.py` | Create | Read/write learned_players.json |
| `data/players_reference.py` | Modify | Add get_all_players() merge function |
| `data/scraper.py` | Modify | Rewrite _classify_with_llm() for batched flow |
| `analysis/expert_opinions.py` | Modify | Use get_all_players() instead of PLAYERS_BY_COUNTRY |
| `.env.example` | Modify | Add OPENROUTER_API_KEY |
| `tests/test_learned_store.py` | Create | Tests for learned players storage |
| `tests/test_extractor.py` | Create | Tests for new extraction methods |
| `tests/test_players_reference.py` | Create | Tests for merge function |
| `tests/test_scraper_llm.py` | Create | Integration tests for LLM scraping |

---

### Task 1: Config — Add OpenRouter Settings

**Files:**
- Modify: `config.py`
- Modify: `.env.example`

- [ ] **Step 1: Add OpenRouter config to config.py**

Add after the existing LLM settings (line ~71):

```python
# === OpenRouter Settings ===
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODELS = [
    "nvidia/nemotron-3-super:free",           # 120B, primary
    "google/gemma-4-31b:free",                # 31B, fast fallback
    "nvidia/nemotron-3-nano-30b-a3b:free",    # 30B, lightweight fallback
]
```

- [ ] **Step 2: Update .env.example**

Add after HUGGINGFACE_API_KEY line:

```
OPENROUTER_API_KEY=your_openrouter_key_here
```

- [ ] **Step 3: Commit**

```bash
git add config.py .env.example
git commit -m "config: add OpenRouter settings with model fallback array"
```

---

### Task 2: Learned Players Store — Read/Write JSON

**Files:**
- Create: `data/learned_store.py`
- Create: `tests/test_learned_store.py`

- [ ] **Step 1: Write failing tests for learned_store.py**

```python
# tests/test_learned_store.py
"""Tests for learned players storage."""
import json
import time
from pathlib import Path
from data.learned_store import get_learned_players, save_learned_player, get_all_players_merged


def test_get_learned_players_returns_dict(tmp_path):
    """Should return dict with players and stats keys."""
    from data import learned_store
    learned_store._LEARNED_FILE = tmp_path / "learned.json"
    result = get_learned_players()
    assert "players" in result
    assert "stats" in result


def test_save_learned_player_adds_player(tmp_path):
    """Should save a new player to learned JSON."""
    from data import learned_store
    learned_store._LEARNED_FILE = tmp_path / "learned.json"
    save_learned_player("Test Player", "Testland", "TestSource")
    data = get_learned_players()
    assert "Test Player" in data["players"]
    assert data["players"]["Test Player"]["country"] == "Testland"
    assert data["players"]["Test Player"]["source"] == "TestSource"
    assert data["stats"]["total_verified"] == 1


def test_save_learned_player_deduplicates(tmp_path):
    """Should not save the same player twice."""
    from data import learned_store
    learned_store._LEARNED_FILE = tmp_path / "learned.json"
    save_learned_player("Test Player", "Testland", "Source1")
    save_learned_player("Test Player", "Testland", "Source2")
    data = get_learned_players()
    assert data["stats"]["total_verified"] == 1


def test_get_all_players_merged_includes_hardcoded(tmp_path):
    """Should include players from PLAYERS_BY_COUNTRY."""
    from data import learned_store
    learned_store._LEARNED_FILE = tmp_path / "learned.json"
    result = get_all_players_merged()
    assert "Lionel Messi" in result
    assert result["Lionel Messi"] == "Argentina"


def test_get_all_players_merged_includes_learned(tmp_path):
    """Should include learned players."""
    from data import learned_store
    learned_store._LEARNED_FILE = tmp_path / "learned.json"
    save_learned_player("Learned Player", "Learnland", "Source")
    result = get_all_players_merged()
    assert "Learned Player" in result
    assert result["Learned Player"] == "Learnland"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_learned_store.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Implement learned_store.py**

```python
# data/learned_store.py
"""Persistent storage for LLM-discovered players."""
import json
import time
from pathlib import Path
from typing import Any

from config import CACHE_DIR
from data.players_reference import PLAYERS_BY_COUNTRY

_LEARNED_FILE = CACHE_DIR / "learned_players.json"


def _ensure_file() -> None:
    """Create learned JSON file if it doesn't exist."""
    if not _LEARNED_FILE.exists():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(_LEARNED_FILE, "w", encoding="utf-8") as f:
            json.dump({"players": {}, "stats": {"total_discovered": 0, "total_verified": 0, "last_scrape": None}}, f, indent=2)


def get_learned_players() -> dict[str, Any]:
    """Load learned players from disk."""
    _ensure_file()
    try:
        with open(_LEARNED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"players": {}, "stats": {"total_discovered": 0, "total_verified": 0, "last_scrape": None}}


def save_learned_player(name: str, country: str, source: str) -> None:
    """Save a verified player to learned JSON."""
    data = get_learned_players()
    if name in data["players"]:
        return  # deduplicate

    data["players"][name] = {
        "country": country,
        "added_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": source,
        "verified": True,
    }
    data["stats"]["total_verified"] = len(data["players"])
    data["stats"]["last_scrape"] = time.strftime("%Y-%m-%dT%H:%M:%S")

    with open(_LEARNED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_all_players_merged() -> dict[str, str]:
    """Merge hardcoded + learned players into single dict."""
    merged = dict(PLAYERS_BY_COUNTRY)
    data = get_learned_players()
    for name, info in data.get("players", {}).items():
        if name not in merged:
            merged[name] = info.get("country", "Unknown")
    return merged
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_learned_store.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add data/learned_store.py tests/test_learned_store.py
git commit -m "feat: add learned players storage with merge function"
```

---

### Task 3: Players Reference — Add get_all_players()

**Files:**
- Modify: `data/players_reference.py`
- Create: `tests/test_players_reference.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_players_reference.py
"""Tests for players reference merge."""
from data.players_reference import get_all_players


def test_get_all_players_returns_dict():
    """Should return a dict of player names to countries."""
    result = get_all_players()
    assert isinstance(result, dict)
    assert len(result) > 0


def test_get_all_players_includes_hardcoded():
    """Should include players from PLAYERS_BY_COUNTRY."""
    result = get_all_players()
    assert "Lionel Messi" in result
    assert "Kylian Mbappe" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_players_reference.py -v`
Expected: FAIL (function doesn't exist yet)

- [ ] **Step 3: Implement get_all_players()**

Add at the end of `data/players_reference.py`:

```python
def get_all_players() -> dict[str, str]:
    """Get all players (hardcoded + learned) merged."""
    from data.learned_store import get_all_players_merged
    return get_all_players_merged()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_players_reference.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add data/players_reference.py tests/test_players_reference.py
git commit -m "feat: add get_all_players() merge function"
```

---

### Task 4: Extractor — Add OpenRouter Provider

**Files:**
- Modify: `data/extractor.py`
- Create: `tests/test_extractor.py`

- [ ] **Step 1: Write failing tests for OpenRouter provider**

```python
# tests/test_extractor.py
"""Tests for LLM extraction methods."""
import json
from unittest.mock import patch, MagicMock
from data.extractor import (
    OpenRouterProvider,
    extract_player_names,
    extract_countries,
    verify_players,
    _parse_json,
)


def test_parse_json_valid():
    """Should parse valid JSON from text."""
    text = 'Here is the result: {"players": ["Messi"]}'
    result = _parse_json(text)
    assert result == {"players": ["Messi"]}


def test_parse_json_invalid():
    """Should return empty dict for invalid JSON."""
    result = _parse_json("no json here")
    assert result == {}


def test_openrouter_provider_init():
    """Should initialize with API key."""
    provider = OpenRouterProvider(api_key="test_key", model="test-model")
    assert provider.api_key == "test_key"
    assert provider.model == "test-model"


def test_extract_player_names_returns_list():
    """Should extract player names from LLM response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": json.dumps({"1": ["Messi", "Ronaldo"], "2": ["Neymar"]})}}]
    }
    with patch("data.extractor.requests.post", return_value=mock_response):
        provider = OpenRouterProvider(api_key="test", model="test")
        result = provider.extract_player_names("Article 1\nArticle 2")
        assert isinstance(result, dict)
        assert "1" in result
        assert "Messi" in result["1"]


def test_verify_players_filters_non_players():
    """Should filter out entries where is_real is false."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": json.dumps({
            "players": [
                {"name": "Messi", "full_name": "Lionel Messi", "country": "Argentina", "is_real": True},
                {"name": "Fake", "full_name": "Fake Person", "country": "Nowhere", "is_real": False},
            ]
        })}}]
    }
    with patch("data.extractor.requests.post", return_value=mock_response):
        provider = OpenRouterProvider(api_key="test", model="test")
        result = provider.verify_players(["Messi", "Fake"])
        assert len(result) == 1
        assert result[0]["name"] == "Messi"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_extractor.py -v`
Expected: FAIL (OpenRouterProvider doesn't exist)

- [ ] **Step 3: Implement OpenRouterProvider and extraction methods**

Update `data/extractor.py`:

```python
# Add after existing imports
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODELS

# Add new prompts
EXTRACT_PLAYERS_PROMPT = """Extract all football player names from these articles. Each article is numbered.

Return ONLY valid JSON:
{{"1": ["Player A", "Player B"], "2": ["Player C"]}}

Articles:
{articles}"""

EXTRACT_COUNTRIES_PROMPT = """Extract country mentions from these articles about FIFA World Cup Fantasy.
Each article is numbered. For each country, return sentiment and brief context.

Return ONLY valid JSON:
{{"1": [{{"name": "Country", "sentiment": "positive|negative|neutral", "context": "brief reason"}}]}}

Articles:
{articles}"""

VERIFY_PLAYERS_PROMPT = """For each player name below, verify:
1. Is this a real professional football player?
2. What is their full name in Latin/English characters? (e.g. "Takefusa Kubo" not "久保建英")
3. What country do they play for (national team)?

Return ONLY valid JSON:
{{"players": [{{"name": "...", "full_name": "...", "country": "...", "is_real": true|false}}]}}

Names to verify: {names}"""

# Add OpenRouterProvider class
class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider with model fallback."""

    def __init__(self, api_key: str = OPENROUTER_API_KEY, models: list[str] | None = None):
        self.api_key = api_key
        self.models = models or OPENROUTER_MODELS
        self.base_url = OPENROUTER_BASE_URL
        logger.info("[LLM] OpenRouter provider initialized (models=%s, key=%s)",
                     self.models, "set" if api_key else "NOT SET")

    def _call_with_fallback(self, prompt: str) -> dict[str, Any]:
        """Try each model in order until one succeeds."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 2048,
        }

        for model in self.models:
            try:
                logger.info("[LLM] Trying model: %s", model)
                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json={**payload, "model": model},
                    timeout=60,
                )
                if resp.status_code == 429:
                    logger.warning("[LLM] Rate limited on %s, trying next...", model)
                    continue
                resp.raise_for_status()
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                logger.info("[LLM] Success with model: %s", model)
                return _parse_json(text)
            except requests.Timeout:
                logger.warning("[LLM] Timeout on %s, trying next...", model)
                continue
            except Exception as e:
                logger.warning("[LLM] Error on %s: %s, trying next...", model, e)
                continue

        logger.error("[LLM] All models failed")
        return {}

    def extract(self, article_text: str) -> dict[str, Any]:
        prompt = EXTRACTION_PROMPT.format(article_text=article_text[:3000])
        return self._call_with_fallback(prompt)

    def extract_player_names(self, articles_text: str) -> dict[str, list[str]]:
        """Extract player names from batched articles."""
        prompt = EXTRACT_PLAYERS_PROMPT.format(articles=articles_text)
        return self._call_with_fallback(prompt)

    def extract_countries(self, articles_text: str) -> dict[str, list[dict]]:
        """Extract countries from batched articles."""
        prompt = EXTRACT_COUNTRIES_PROMPT.format(articles=articles_text)
        return self._call_with_fallback(prompt)

    def verify_players(self, names: list[str]) -> list[dict]:
        """Verify if names are real football players."""
        prompt = VERIFY_PLAYERS_PROMPT.format(names=", ".join(names))
        result = self._call_with_fallback(prompt)
        return [p for p in result.get("players", []) if p.get("is_real", False)]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_extractor.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add data/extractor.py tests/test_extractor.py
git commit -m "feat: add OpenRouter provider with model fallback and extraction prompts"
```

---

### Task 5: Expert Opinions — Use get_all_players()

**Files:**
- Modify: `analysis/expert_opinions.py:1-5,101`

- [ ] **Step 1: Update import and usage**

Change line 5 from:
```python
from data.players_reference import PLAYERS_BY_COUNTRY, COUNTRY_NAMES
```
to:
```python
from data.players_reference import get_all_players, COUNTRY_NAMES
```

Change line 101 from:
```python
for player_name, country in PLAYERS_BY_COUNTRY.items():
```
to:
```python
all_players = get_all_players()
for player_name, country in all_players.items():
```

- [ ] **Step 2: Run existing tests to verify no regressions**

Run: `pytest tests/test_expert_opinions.py -v`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add analysis/expert_opinions.py
git commit -m "refactor: use get_all_players() for dynamic player list"
```

---

### Task 6: Scraper — Rewrite _classify_with_llm()

**Files:**
- Modify: `data/scraper.py:76-128`
- Create: `tests/test_scraper_llm.py`

- [ ] **Step 1: Write failing tests for batched LLM scraping**

```python
# tests/test_scraper_llm.py
"""Tests for LLM-based scraping with batching."""
import json
from unittest.mock import patch, MagicMock
from data.scraper import _build_articles_batch, _classify_with_llm_batched


def test_build_articles_batch_creates_numbered_text():
    """Should create numbered article text for batch processing."""
    articles = [
        {"source": "A", "content": "Messi is great"},
        {"source": "B", "content": "Ronaldo scores"},
    ]
    result = _build_articles_batch(articles)
    assert "---ARTICLE 1---" in result
    assert "Messi is great" in result
    assert "---ARTICLE 2---" in result
    assert "Ronaldo scores" in result


def test_classify_with_llm_batched_returns_structure():
    """Should return players and countries dicts."""
    mock_provider = MagicMock()
    mock_provider.extract_player_names.return_value = {"1": ["Messi"], "2": ["Ronaldo"]}
    mock_provider.extract_countries.return_value = {"1": [{"name": "Argentina", "sentiment": "positive", "context": "..."}]}
    mock_provider.verify_players.return_value = []

    articles = [
        {"source": "A", "content": "Messi is great", "url": "http://a.com"},
        {"source": "B", "content": "Ronaldo scores", "url": "http://b.com"},
    ]
    result = _classify_with_llm_batched(articles, mock_provider)
    assert "players" in result
    assert "countries" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_scraper_llm.py -v`
Expected: FAIL (functions don't exist)

- [ ] **Step 3: Implement batched LLM classification**

Add to `data/scraper.py`:

```python
def _build_articles_batch(articles: list[dict], max_articles: int = 10) -> str:
    """Build numbered article text for batch LLM processing."""
    parts = []
    for i, article in enumerate(articles[:max_articles], 1):
        parts.append(f"---ARTICLE {i}---\n{article['content'][:2000]}")
    return "\n\n".join(parts)


def _classify_with_llm_batched(articles: list[dict], provider) -> dict[str, Any]:
    """Classify articles using batched LLM calls."""
    all_players: dict[str, dict] = {}
    all_countries: dict[str, dict] = {}

    # Process in batches of 10
    batch_size = 10
    for start in range(0, len(articles), batch_size):
        batch = articles[start:start + batch_size]
        batch_text = _build_articles_batch(batch)

        logger.info("[LLM] Processing batch %d-%d of %d articles...",
                     start + 1, min(start + batch_size, len(articles)), len(articles))

        # Call 1: Extract players
        players_by_article = provider.extract_player_names(batch_text)
        for article_idx, player_names in players_by_article.items():
            idx = int(article_idx) - 1
            if 0 <= idx < len(batch):
                source = batch[idx]["source"]
                for name in player_names:
                    if name not in all_players:
                        all_players[name] = {"country": "Unknown", "mentions": []}
                    all_players[name]["mentions"].append({"source": source, "sentiment": "neutral", "context": ""})

        # Call 2: Extract countries
        countries_by_article = provider.extract_countries(batch_text)
        for article_idx, country_list in countries_by_article.items():
            idx = int(article_idx) - 1
            if 0 <= idx < len(batch):
                source = batch[idx]["source"]
                for country_data in country_list:
                    name = country_data.get("name", "")
                    if name:
                        if name not in all_countries:
                            all_countries[name] = {"mentions": [], "players_mentioned": []}
                        all_countries[name]["mentions"].append({
                            "source": source,
                            "sentiment": country_data.get("sentiment", "neutral"),
                            "context": country_data.get("context", ""),
                        })

    # Find unknown players
    from data.learned_store import get_all_players_merged, save_learned_player
    known = get_all_players_merged()
    unknowns = [name for name in all_players if name not in known]

    # Call 3: Verify unknowns
    if unknowns:
        logger.info("[LLM] Verifying %d unknown players...", len(unknowns))
        verified = provider.verify_players(unknowns)
        for player in verified:
            name = player.get("full_name", player.get("name", ""))
            country = player.get("country", "Unknown")
            if name and player.get("is_real", False):
                save_learned_player(name, country, "LLM discovery")
                # Update player data
                if name in all_players:
                    all_players[name]["country"] = country

    # Link players to countries
    for player_name, data in all_players.items():
        country = data["country"]
        if country in all_countries:
            if player_name not in all_countries[country]["players_mentioned"]:
                all_countries[country]["players_mentioned"].append(player_name)

    return {"players": all_players, "countries": all_countries}
```

- [ ] **Step 4: Update _classify_with_llm to use batched version**

Replace existing `_classify_with_llm` function body with:

```python
def _classify_with_llm(articles: list[dict]) -> dict[str, Any]:
    """Use LLM to extract player/country mentions from articles."""
    from data.extractor import get_provider
    provider = get_provider()
    return _classify_with_llm_batched(articles, provider)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_scraper_llm.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add data/scraper.py tests/test_scraper_llm.py
git commit -m "feat: rewrite LLM classification with batched processing"
```

---

### Task 7: Logging — Add Detailed LLM Logging

**Files:**
- Modify: `data/scraper.py`
- Modify: `data/extractor.py`

- [ ] **Step 1: Add batch progress logging to scraper**

In `_classify_with_llm_batched`, add logging after each batch:

```python
logger.info("  [BATCH] Players extracted: %d", len(players_by_article))
logger.info("  [BATCH] Countries extracted: %d", len(countries_by_article))
```

- [ ] **Step 2: Add verification logging**

After verification call:

```python
logger.info("  [VERIFY] Unknowns: %d, Verified: %d", len(unknowns), len(verified))
for p in verified:
    logger.info("    + %s (%s)", p.get("full_name", "?"), p.get("country", "?"))
```

- [ ] **Step 3: Commit**

```bash
git add data/scraper.py
git commit -m "logging: add detailed batch and verification progress logs"
```

---

### Task 8: Integration Tests

**Files:**
- Create: `tests/test_integration_llm.py`

- [ ] **Step 1: Write integration test with mock LLM**

```python
# tests/test_integration_llm.py
"""Integration test for full LLM scraping flow."""
from unittest.mock import patch, MagicMock
from data.scraper import scrape_expert_opinions


def test_full_scrape_discovers_new_player(tmp_path):
    """Should discover and save a new player from articles."""
    from data import learned_store
    learned_store._LEARNED_FILE = tmp_path / "learned.json"

    mock_provider = MagicMock()
    mock_provider.extract_player_names.return_value = {"1": ["Khvicha Kvaratskhelia", "Messi"]}
    mock_provider.extract_countries.return_value = {"1": [{"name": "Georgia", "sentiment": "positive", "context": "..."}]}
    mock_provider.verify_players.return_value = [
        {"name": "Kvaratskhelia", "full_name": "Khvicha Kvaratskhelia", "country": "Georgia", "is_real": True}
    ]

    articles = [{"source": "Test", "content": "Kvaratskhelia is amazing", "url": "http://test.com"}]

    with patch("data.scraper.get_provider", return_value=mock_provider):
        with patch("data.scraper.crawl_source", return_value=articles):
            result = scrape_expert_opinions(use_cache=False, use_llm=True)

    # Check player was discovered
    from data.learned_store import get_learned_players
    learned = get_learned_players()
    assert "Khvicha Kvaratskhelia" in learned["players"]
    assert learned["players"]["Khvicha Kvaratskhelia"]["country"] == "Georgia"
```

- [ ] **Step 2: Run integration test**

Run: `pytest tests/test_integration_llm.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration_llm.py
git commit -m "test: add integration test for LLM player discovery"
```

---

### Task 9: Run All Tests and Lint

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: All PASS (63 existing + new tests)

- [ ] **Step 2: Run linting**

Run: `python -m flake8 data/ analysis/ tests/ --max-line-length=120`
Expected: Clean or only warnings

- [ ] **Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix: resolve lint issues"
```

---

### Task 10: Update Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README with new features**

Add to Features section:
```markdown
- **Auto-Discover Players** — LLM automatically discovers new players from articles, verifies they are real, and adds to database
```

Add to Configuration table:
```markdown
| `OPENROUTER_API_KEY` | (required for LLM) | OpenRouter API key for better model quality |
| `OPENROUTER_MODELS` | `["nvidia/nemotron-3-super:free", ...]` | Fallback model array |
```

Add new section:
```markdown
## Auto-Discover Players

The scraper automatically discovers new football players from expert articles using LLM verification:

1. Extracts player names from all articles (batched)
2. Filters out already-known players
3. Verifies unknowns with LLM ("Is this a real football player?")
4. Saves verified players to `data/learned_players.json`

To reset learned players:
```bash
rm data/cache/learned_players.json
```
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README with auto-discover players feature"
```

---

### Task 11: Final Verification and Push

**Files:** None (verification only)

- [ ] **Step 1: Run all tests one final time**

Run: `python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 2: Check git status**

Run: `git status`
Expected: Clean working tree

- [ ] **Step 3: Push to remote**

Run: `git push`
Expected: Push successful

- [ ] **Step 4: Update todo list**

Mark all tasks as completed.
