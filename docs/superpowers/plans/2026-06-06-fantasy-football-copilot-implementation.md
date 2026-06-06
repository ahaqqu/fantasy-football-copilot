# Fantasy Football World Cup 2026 Copilot — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Streamlit web dashboard for analyzing FIFA World Cup 2026 Fantasy Football decisions with player stats, fixture analysis, team selection, and expert opinions.

**Architecture:** Python backend with Streamlit UI, Plotly charts, data from World Cup APIs + web scraping of expert sites. Local caching for performance.

**Tech Stack:** Python 3.11+, Streamlit, Plotly, Pandas, Requests, Beautiful Soup 4

---

## File Structure

```
fantasy-football-copilot/
├── app.py                          # Main Streamlit entry point
├── requirements.txt                # Python dependencies
├── config.py                       # API keys, settings
├── .gitignore                      # Git ignore rules
├── data/
│   ├── __init__.py
│   ├── fetcher.py                  # API calls to World Cup data providers
│   ├── scraper.py                  # Web scraping for expert opinions
│   └── cache.py                    # Local JSON caching
├── analysis/
│   ├── __init__.py
│   ├── player_stats.py             # Player comparison logic
│   ├── fixture_analysis.py         # Attack/defense fixture ratings
│   ├── team_optimizer.py           # Squad selection algorithm
│   ├── lineup_predictor.py         # Starting XI prediction
│   ├── player_fitness.py           # Injury/fitness status
│   └── expert_opinions.py          # Summarize expert articles
├── ui/
│   ├── __init__.py
│   ├── tabs/
│   │   ├── __init__.py
│   │   ├── player_hub.py           # Player stats + fitness + opinions
│   │   ├── fixture_analysis.py     # Fixture difficulty table
│   │   ├── team_hub.py             # Country overview + squad fitness
│   │   └── team_selector.py        # Squad optimizer UI
│   └── components/
│       ├── __init__.py
│       ├── player_card.py          # Reusable player card component
│       ├── formation_display.py    # Football pitch formation display
│       └── stats_table.py          # Data table component
└── tests/
    ├── __init__.py
    ├── test_fetcher.py
    ├── test_scraper.py
    ├── test_cache.py
    ├── test_player_stats.py
    ├── test_fixture_analysis.py
    ├── test_team_optimizer.py
    ├── test_lineup_predictor.py
    ├── test_player_fitness.py
    └── test_expert_opinions.py
```

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `config.py`
- Create: `.gitignore`
- Create: `app.py` (skeleton)
- Create: `mockups/` directory with HTML reference files

- [ ] **Step 1: Create requirements.txt**

```txt
streamlit>=1.35.0
plotly>=5.18.0
pandas>=2.1.0
requests>=2.31.0
beautifulsoup4>=4.12.0
schedule>=1.2.0
pytest>=7.4.0
python-dotenv>=1.0.0
```

- [ ] **Step 2: Create config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
THESTATSAPI_KEY = os.getenv("THESTATSAPI_KEY", "")

# Fantasy Game Settings
BUDGET = 100.0  # $100m
FORMATION = "4-3-3"

# Cache Settings
CACHE_DIR = "cache"
CACHE_LIVE_TTL = 300  # 5 minutes
CACHE_HISTORICAL_TTL = 86400  # 24 hours

# Expert Sites to Scrape
EXPERT_SOURCES = {
    "fantasyfootballscout": "https://www.fantasyfootballscout.co.uk",
    "fantasyfootballhub": "https://www.fantasyfootballhub.co.uk",
    "allaboutfpl": "https://allaboutfpl.com",
    "rotowire": "https://www.rotowire.com/soccer",
}
```

- [ ] **Step 3: Create .gitignore**

```
__pycache__/
*.pyc
.env
cache/
*.egg-info/
dist/
build/
.pytest_cache/
venv/
.venv/
```

- [ ] **Step 4: Create app.py skeleton**

```python
import streamlit as st
from ui.tabs import player_hub, fixture_analysis, team_hub, team_selector

st.set_page_config(
    page_title="Fantasy Football World Cup 2026 Copilot",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ FIFA World Cup 2026 Fantasy Copilot")
st.caption("Your personal assistant for winning your fantasy league")

tab1, tab2, tab3, tab4 = st.tabs([
    "Player Hub",
    "Fixture Analysis",
    "Team Hub",
    "Team Selector"
])

with tab1:
    player_hub.render()

with tab2:
    fixture_analysis.render()

with tab3:
    team_hub.render()

with tab4:
    team_selector.render()
```

- [ ] **Step 5: Create all __init__.py files**

```bash
mkdir -p data analysis ui/tabs ui/components tests mockups
touch data/__init__.py analysis/__init__.py ui/__init__.py ui/tabs/__init__.py ui/components/__init__.py tests/__init__.py
```

- [ ] **Step 6: Copy mockup reference files**

```bash
cp .superpowers/brainstorm/test-session/content/dashboard-mockup.html mockups/01-player-comparison.html
cp .superpowers/brainstorm/test-session/content/dashboard-mockup-v2.html mockups/02-fixture-analysis.html
cp .superpowers/brainstorm/test-session/content/dashboard-mockup-v3-player-status.html mockups/03-player-status.html
```

- [ ] **Step 7: Install dependencies and verify**

```bash
pip install -r requirements.txt
python -c "import streamlit; import plotly; import pandas; print('Dependencies OK')"
```

- [ ] **Step 8: Commit**

```bash
git add requirements.txt config.py .gitignore app.py data/ analysis/ ui/ tests/ mockups/
git commit -m "feat: project setup with dependencies, config, and mockup references"
```

---

## Task 2: Data Layer — Cache System

**Files:**
- Create: `data/cache.py`
- Create: `tests/test_cache.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cache.py
import os
import json
import time
from data.cache import Cache

def test_cache_set_get():
    cache = Cache("test_cache")
    cache.set("key1", {"data": "value1"}, ttl=60)
    result = cache.get("key1")
    assert result == {"data": "value1"}
    cache.clear()

def test_cache_expiry():
    cache = Cache("test_cache")
    cache.set("key2", {"data": "value2"}, ttl=0)
    time.sleep(0.1)
    result = cache.get("key2")
    assert result is None
    cache.clear()

def test_cache_miss():
    cache = Cache("test_cache")
    result = cache.get("nonexistent")
    assert result is None
    cache.clear()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_cache.py -v
```
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# data/cache.py
import os
import json
import time
from typing import Any, Optional

class Cache:
    def __init__(self, namespace: str, cache_dir: str = "cache"):
        self.namespace = namespace
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _get_path(self, key: str) -> str:
        safe_key = key.replace("/", "_").replace("\\", "_")
        return os.path.join(self.cache_dir, f"{self.namespace}_{safe_key}.json")

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        path = self._get_path(key)
        data = {
            "value": value,
            "expires_at": time.time() + ttl
        }
        with open(path, "w") as f:
            json.dump(data, f)

    def get(self, key: str) -> Optional[Any]:
        path = self._get_path(key)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            data = json.load(f)
        if time.time() > data["expires_at"]:
            os.remove(path)
            return None
        return data["value"]

    def clear(self) -> None:
        for filename in os.listdir(self.cache_dir):
            if filename.startswith(f"{self.namespace}_"):
                os.remove(os.path.join(self.cache_dir, filename))
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_cache.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add data/cache.py tests/test_cache.py
git commit -m "feat: add cache system with TTL support"
```

---

## Task 3: Data Layer — API Fetcher

**Files:**
- Create: `data/fetcher.py`
- Create: `tests/test_fetcher.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_fetcher.py
from unittest.mock import patch, Mock
from data.fetcher import WorldCupFetcher

@patch('data.fetcher.requests.get')
def test_fetch_teams(mock_get):
    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: {"teams": [{"id": 1, "name": "Brazil"}]}
    )
    fetcher = WorldCupFetcher(api_key="test_key")
    teams = fetcher.fetch_teams()
    assert len(teams) > 0

@patch('data.fetcher.requests.get')
def test_fetch_fixtures(mock_get):
    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: {"fixtures": [{"id": 1, "home": "Brazil", "away": "Serbia"}]}
    )
    fetcher = WorldCupFetcher(api_key="test_key")
    fixtures = fetcher.fetch_fixtures()
    assert len(fixtures) > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_fetcher.py -v
```
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# data/fetcher.py
import requests
from typing import List, Dict, Any
from data.cache import Cache

class WorldCupFetcher:
    BASE_URL = "https://api.football-data.org/v4"  # Example: use your chosen API

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"X-Auth-Token": api_key}
        self.cache = Cache("api")

    def _get(self, endpoint: str) -> Dict[str, Any]:
        cached = self.cache.get(endpoint)
        if cached:
            return cached
        response = requests.get(f"{self.BASE_URL}{endpoint}", headers=self.headers)
        response.raise_for_status()
        data = response.json()
        self.cache.set(endpoint, data, ttl=300)
        return data

    def fetch_teams(self) -> List[Dict]:
        data = self._get("/teams")
        return data.get("teams", [])

    def fetch_fixtures(self) -> List[Dict]:
        data = self._get("/matches")
        return data.get("matches", [])

    def fetch_player_stats(self, team_id: int) -> List[Dict]:
        data = self._get(f"/teams/{team_id}/players")
        return data.get("players", [])

    def fetch_standings(self) -> List[Dict]:
        data = self._get("/standings")
        return data.get("standings", [])
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_fetcher.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add data/fetcher.py tests/test_fetcher.py
git commit -m "feat: add API fetcher with caching"
```

---

## Task 4: Data Layer — Expert Site Scraper

**Files:**
- Create: `data/scraper.py`
- Create: `tests/test_scraper.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scraper.py
from unittest.mock import patch, Mock
from data.scraper import ExpertScraper

@patch('data.scraper.requests.get')
def test_scrape_fantasyfootballscout(mock_get):
    mock_get.return_value = Mock(
        status_code=200,
        text="<html><article><h2>Mbappe is essential</h2></article></html>"
    )
    scraper = ExpertScraper()
    articles = scraper.scrape_site("fantasyfootballscout")
    assert isinstance(articles, list)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_scraper.py -v
```
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# data/scraper.py
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from data.cache import Cache
from config import EXPERT_SOURCES

class ExpertScraper:
    def __init__(self):
        self.cache = Cache("scraper")

    def scrape_site(self, site_name: str) -> List[Dict]:
        cached = self.cache.get(f"articles_{site_name}")
        if cached:
            return cached

        url = EXPERT_SOURCES.get(site_name)
        if not url:
            return []

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            articles = []
            for article in soup.find_all("article")[:10]:
                title = article.find("h2")
                if title:
                    articles.append({
                        "title": title.get_text(strip=True),
                        "url": url,
                        "source": site_name
                    })
            self.cache.set(f"articles_{site_name}", articles, ttl=86400)
            return articles
        except Exception as e:
            print(f"Error scraping {site_name}: {e}")
            return []

    def get_captain_picks(self) -> List[Dict]:
        return self.scrape_site("fantasyfootballscout")

    def get_differential_picks(self) -> List[Dict]:
        return self.scrape_site("allaboutfpl")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_scraper.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add data/scraper.py tests/test_scraper.py
git commit -m "feat: add expert site scraper with caching"
```

---

## Task 5: Analysis — Player Stats

**Files:**
- Create: `analysis/player_stats.py`
- Create: `tests/test_player_stats.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_player_stats.py
from analysis.player_stats import PlayerStats

def test_calculate_form():
    stats = PlayerStats()
    form = stats.calculate_form([10, 8, 6, 4, 2])
    assert 0 <= form <= 10

def test_compare_players():
    stats = PlayerStats()
    player_a = {"name": "Mbappe", "goals": 5, "assists": 2, "price": 13.0}
    player_b = {"name": "Messi", "goals": 3, "assists": 4, "price": 12.5}
    result = stats.compare([player_a, player_b])
    assert len(result) == 2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_player_stats.py -v
```
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# analysis/player_stats.py
from typing import List, Dict

class PlayerStats:
    def calculate_form(self, recent_points: List[int]) -> float:
        if not recent_points:
            return 0.0
        weights = [1.0, 0.8, 0.6, 0.4, 0.2][:len(recent_points)]
        weighted_sum = sum(p * w for p, w in zip(recent_points, weights))
        weight_total = sum(weights)
        return round(weighted_sum / weight_total, 1) if weight_total > 0 else 0.0

    def compare(self, players: List[Dict]) -> List[Dict]:
        return sorted(players, key=lambda p: p.get("goals", 0) + p.get("assists", 0), reverse=True)

    def get_top_players(self, players: List[Dict], metric: str = "points", limit: int = 10) -> List[Dict]:
        return sorted(players, key=lambda p: p.get(metric, 0), reverse=True)[:limit]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_player_stats.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add analysis/player_stats.py tests/test_player_stats.py
git commit -m "feat: add player stats analysis"
```

---

## Task 6: Analysis — Fixture Analysis

**Files:**
- Create: `analysis/fixture_analysis.py`
- Create: `tests/test_fixture_analysis.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_fixture_analysis.py
from analysis.fixture_analysis import FixtureAnalyzer

def test_rate_attack():
    analyzer = FixtureAnalyzer()
    rating = analyzer.rate_attack(2.1)
    assert rating in ["high", "medium", "low"]

def test_rate_defense():
    analyzer = FixtureAnalyzer()
    rating = analyzer.rate_defense(65)
    assert rating in ["strong", "average", "weak"]

def test_get_fixture_difficulty():
    analyzer = FixtureAnalyzer()
    fixture = {"home_xg": 2.0, "away_xg": 1.2, "home_cs": 55, "away_cs": 70}
    result = analyzer.analyze_fixture(fixture)
    assert "home_attack" in result
    assert "away_defense" in result
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_fixture_analysis.py -v
```
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# analysis/fixture_analysis.py
from typing import Dict

class FixtureAnalyzer:
    def rate_attack(self, xg: float) -> str:
        if xg > 1.8:
            return "high"
        elif xg > 1.2:
            return "medium"
        return "low"

    def rate_defense(self, clean_sheet_pct: float) -> str:
        if clean_sheet_pct > 60:
            return "strong"
        elif clean_sheet_pct > 40:
            return "average"
        return "weak"

    def analyze_fixture(self, fixture: Dict) -> Dict:
        return {
            "home_attack": self.rate_attack(fixture.get("home_xg", 0)),
            "home_defense": self.rate_defense(fixture.get("home_cs", 0)),
            "away_attack": self.rate_attack(fixture.get("away_xg", 0)),
            "away_defense": self.rate_defense(fixture.get("away_cs", 0)),
        }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_fixture_analysis.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add analysis/fixture_analysis.py tests/test_fixture_analysis.py
git commit -m "feat: add fixture analysis with attack/defense ratings"
```

---

## Task 7: Analysis — Team Optimizer

**Files:**
- Create: `analysis/team_optimizer.py`
- Create: `tests/test_team_optimizer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_team_optimizer.py
from analysis.team_optimizer import TeamOptimizer

def test_select_team_within_budget():
    optimizer = TeamOptimizer(budget=100.0)
    players = [
        {"name": "Mbappe", "price": 13.0, "position": "FWD", "points": 50},
        {"name": "Messi", "price": 12.5, "position": "FWD", "points": 45},
        {"name": "Courtois", "price": 5.0, "position": "GK", "points": 30},
    ]
    team = optimizer.select_team(players, formation="4-3-3")
    total_cost = sum(p["price"] for p in team)
    assert total_cost <= 100.0

def test_exclude_injured():
    optimizer = TeamOptimizer(budget=100.0)
    players = [
        {"name": "Neymar", "price": 11.0, "position": "FWD", "points": 40, "status": "injured"},
        {"name": "Vinicius", "price": 11.8, "position": "FWD", "points": 44, "status": "available"},
    ]
    team = optimizer.select_team(players, formation="4-3-3")
    assert all(p["name"] != "Neymar" for p in team)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_team_optimizer.py -v
```
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# analysis/team_optimizer.py
from typing import List, Dict

FORMATION_MAP = {
    "4-3-3": {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3},
    "4-4-2": {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2},
    "3-5-2": {"GK": 1, "DEF": 3, "MID": 5, "FWD": 2},
}

class TeamOptimizer:
    def __init__(self, budget: float = 100.0):
        self.budget = budget

    def select_team(self, players: List[Dict], formation: str = "4-3-3") -> List[Dict]:
        available = [p for p in players if p.get("status", "available") == "available"]
        positions = FORMATION_MAP.get(formation, FORMATION_MAP["4-3-3"])
        team = []
        for pos, count in positions.items():
            pos_players = [p for p in available if p["position"] == pos]
            pos_players.sort(key=lambda x: x.get("points", 0), reverse=True)
            team.extend(pos_players[:count])
        return team

    def get_remaining_budget(self, team: List[Dict]) -> float:
        spent = sum(p["price"] for p in team)
        return self.budget - spent
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_team_optimizer.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add analysis/team_optimizer.py tests/test_team_optimizer.py
git commit -m "feat: add team optimizer with budget and formation constraints"
```

---

## Task 8: Analysis — Lineup Predictor

**Files:**
- Create: `analysis/lineup_predictor.py`
- Create: `tests/test_lineup_predictor.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_lineup_predictor.py
from analysis.lineup_predictor import LineupPredictor

def test_predict_starting_xi():
    predictor = LineupPredictor()
    squad = [
        {"name": "Alisson", "position": "GK", "starts_last_6": 6},
        {"name": "Marquinhos", "position": "DEF", "starts_last_6": 6},
        {"name": "Vinicius", "position": "FWD", "starts_last_6": 4},
    ]
    xi = predictor.predict_xi(squad)
    assert len(xi) == 11

def test_calculate_start_probability():
    predictor = LineupPredictor()
    prob = predictor.start_probability(starts_last_6=5)
    assert 0 <= prob <= 100
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_lineup_predictor.py -v
```
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# analysis/lineup_predictor.py
from typing import List, Dict

class LineupPredictor:
    def start_probability(self, starts_last_6: int) -> int:
        return min(100, int((starts_last_6 / 6) * 100))

    def predict_xi(self, squad: List[Dict]) -> List[Dict]:
        positions = {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3}
        xi = []
        for pos, count in positions.items():
            pos_players = [p for p in squad if p["position"] == pos]
            pos_players.sort(key=lambda x: x.get("starts_last_6", 0), reverse=True)
            for p in pos_players[:count]:
                p["start_prob"] = self.start_probability(p.get("starts_last_6", 0))
                xi.append(p)
        return xi
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_lineup_predictor.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add analysis/lineup_predictor.py tests/test_lineup_predictor.py
git commit -m "feat: add lineup predictor with start probability"
```

---

## Task 9: Analysis — Player Fitness

**Files:**
- Create: `analysis/player_fitness.py`
- Create: `tests/test_player_fitness.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_player_fitness.py
from analysis.player_fitness import FitnessTracker

def test_get_status_color():
    tracker = FitnessTracker()
    assert tracker.get_status_color("available") == "green"
    assert tracker.get_status_color("injured") == "red"
    assert tracker.get_status_color("doubtful") == "orange"

def test_filter_by_status():
    tracker = FitnessTracker()
    players = [
        {"name": "A", "status": "available"},
        {"name": "B", "status": "injured"},
        {"name": "C", "status": "available"},
    ]
    result = tracker.filter_by_status(players, "injured")
    assert len(result) == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_player_fitness.py -v
```
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# analysis/player_fitness.py
from typing import List, Dict

STATUS_COLORS = {
    "available": "green",
    "doubtful": "orange",
    "injured": "red",
    "suspended": "purple",
    "unknown": "gray"
}

class FitnessTracker:
    def get_status_color(self, status: str) -> str:
        return STATUS_COLORS.get(status, "gray")

    def filter_by_status(self, players: List[Dict], status: str) -> List[Dict]:
        return [p for p in players if p.get("status") == status]

    def get_status_summary(self, players: List[Dict]) -> Dict:
        summary = {"available": 0, "doubtful": 0, "injured": 0, "suspended": 0}
        for p in players:
            status = p.get("status", "unknown")
            if status in summary:
                summary[status] += 1
        return summary
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_player_fitness.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add analysis/player_fitness.py tests/test_player_fitness.py
git commit -m "feat: add player fitness tracker"
```

---

## Task 10: Analysis — Expert Opinions

**Files:**
- Create: `analysis/expert_opinions.py`
- Create: `tests/test_expert_opinions.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_expert_opinions.py
from analysis.expert_opinions import ExpertOpinions

def test_summarize_articles():
    opinions = ExpertOpinions()
    articles = [
        {"title": "Mbappe is essential for MD1"},
        {"title": "Consider budget defenders"},
    ]
    summary = opinions.summarize(articles)
    assert isinstance(summary, str)
    assert len(summary) > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_expert_opinions.py -v
```
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# analysis/expert_opinions.py
from typing import List, Dict

class ExpertOpinions:
    def summarize(self, articles: List[Dict]) -> str:
        if not articles:
            return "No expert opinions available."
        titles = [a.get("title", "") for a in articles[:5]]
        return "Key insights: " + "; ".join(titles)

    def get_captain_recommendation(self, articles: List[Dict]) -> str:
        for article in articles:
            title = article.get("title", "").lower()
            if "captain" in title or "essential" in title:
                return article.get("title", "No recommendation")
        return "Check latest expert picks"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_expert_opinions.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add analysis/expert_opinions.py tests/test_expert_opinions.py
git commit -m "feat: add expert opinions summarizer"
```

---

## Task 11: UI — Player Hub Tab

**Files:**
- Create: `ui/tabs/player_hub.py`
- Create: `ui/components/player_card.py`
- Reference: `mockups/03-player-status.html`

- [ ] **Step 1: Create player_card component**

```python
# ui/components/player_card.py
import streamlit as st

def render_player_card(player: dict):
    """Render a player card matching mockup design."""
    status_colors = {
        "available": ("🟢", "#22c55e"),
        "doubtful": ("🟡", "#f59e0b"),
        "injured": ("🔴", "#ef4444"),
        "suspended": ("🟠", "#f97316")
    }
    status_icon, status_color = status_colors.get(player.get("status", "unknown"), ("⚪", "#64748b"))

    with st.container():
        st.markdown(f"""
        <div style="background:#1e293b; border-radius:12px; padding:16px; border-left:4px solid {status_color};">
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <span style="font-size:20px;">{player.get('flag', '🏳️')}</span>
                    <strong>{player.get('name', 'Unknown')}</strong>
                    <span style="color:#94a3b8; font-size:12px;">{player.get('team', 'N/A')} • {player.get('position', 'N/A')}</span>
                </div>
                <span style="background:{status_color}; color:white; padding:4px 8px; border-radius:4px; font-size:11px;">{player.get('status', 'unknown').upper()}</span>
            </div>
            <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-top:12px;">
                <div style="background:#0f172a; padding:8px; border-radius:6px; text-align:center;">
                    <div style="color:#94a3b8; font-size:11px;">Price</div>
                    <div style="color:#22c55e; font-weight:bold;">${player.get('price', 0)}m</div>
                </div>
                <div style="background:#0f172a; padding:8px; border-radius:6px; text-align:center;">
                    <div style="color:#94a3b8; font-size:11px;">Points</div>
                    <div style="font-weight:bold;">{player.get('points', 0)}</div>
                </div>
                <div style="background:#0f172a; padding:8px; border-radius:6px; text-align:center;">
                    <div style="color:#94a3b8; font-size:11px;">Goals</div>
                    <div style="font-weight:bold;">{player.get('goals', 0)}</div>
                </div>
                <div style="background:#0f172a; padding:8px; border-radius:6px; text-align:center;">
                    <div style="color:#94a3b8; font-size:11px;">Assists</div>
                    <div style="font-weight:bold;">{player.get('assists', 0)}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
```

- [ ] **Step 2: Create player_hub tab**

```python
# ui/tabs/player_hub.py
import streamlit as st
from ui.components.player_card import render_player_card

def render():
    st.header("Player Hub")
    st.caption("All player stats, fitness status, and expert opinions")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        position_filter = st.selectbox("Position", ["All", "GK", "DEF", "MID", "FWD"])
    with col2:
        team_filter = st.selectbox("Team", ["All", "Brazil", "France", "Argentina", "England"])
    with col3:
        status_filter = st.selectbox("Status", ["All", "Available", "Doubtful", "Injured", "Suspended"])

    # Sample data (will be replaced with real API data)
    players = [
        {"name": "Kylian Mbappe", "team": "France", "position": "FWD", "price": 13.0, "points": 52, "goals": 4, "assists": 1, "status": "available", "flag": "🇫🇷"},
        {"name": "Lionel Messi", "team": "Argentina", "position": "FWD", "price": 12.5, "points": 47, "goals": 3, "assists": 2, "status": "doubtful", "flag": "🇦🇷"},
        {"name": "Neymar Jr", "team": "Brazil", "position": "FWD", "price": 11.0, "points": 40, "goals": 2, "assists": 3, "status": "injured", "flag": "🇧🇷"},
    ]

    # Apply filters
    if position_filter != "All":
        players = [p for p in players if p["position"] == position_filter]
    if team_filter != "All":
        players = [p for p in players if p["team"] == team_filter]
    if status_filter != "All":
        players = [p for p in players if p["status"] == status_filter.lower()]

    # Display players
    st.subheader(f"Players ({len(players)})")
    for player in players:
        render_player_card(player)

    # Expert Opinions Section
    st.divider()
    st.subheader("Expert Opinions")
    st.info("""
    **Key Insights from FantasyFootballScout:**
    - Mbappe is essential for MD1 vs Australia
    - Consider budget defenders like Nuno Mendes
    - Captain pick: Haaland or Mbappe
    """)
```

- [ ] **Step 3: Test the UI renders**

```bash
streamlit run app.py
```
Verify: Dashboard loads, Player Hub tab shows player cards matching mockup design

- [ ] **Step 4: Commit**

```bash
git add ui/tabs/player_hub.py ui/components/player_card.py
git commit -m "feat: add Player Hub tab with player cards matching mockup"
```

---

## Task 12: UI — Fixture Analysis Tab

**Files:**
- Create: `ui/tabs/fixture_analysis.py`
- Reference: `mockups/02-fixture-analysis.html`

- [ ] **Step 1: Create fixture_analysis tab**

```python
# ui/tabs/fixture_analysis.py
import streamlit as st

def render():
    st.header("Fixture Analysis")
    st.caption("Attack & defense strength for upcoming matches")

    # Team data with attack/defense ratings
    teams_data = {
        "Brazil": {
            "MD1": {"opponent": "SRB", "attack": "high", "defense": "strong", "xg": 2.1, "cs": 65},
            "MD2": {"opponent": "CRC", "attack": "high", "defense": "strong", "xg": 2.3, "cs": 70},
            "MD3": {"opponent": "CHI", "attack": "medium", "defense": "average", "xg": 1.6, "cs": 45},
        },
        "France": {
            "MD1": {"opponent": "AUS", "attack": "high", "defense": "average", "xg": 2.4, "cs": 50},
            "MD2": {"opponent": "DEN", "attack": "medium", "defense": "strong", "xg": 1.8, "cs": 60},
            "MD3": {"opponent": "TUN", "attack": "high", "defense": "strong", "xg": 2.0, "cs": 65},
        },
        "Argentina": {
            "MD1": {"opponent": "KSA", "attack": "high", "defense": "strong", "xg": 2.5, "cs": 70},
            "MD2": {"opponent": "MEX", "attack": "high", "defense": "strong", "xg": 2.2, "cs": 65},
            "MD3": {"opponent": "POL", "attack": "medium", "defense": "average", "xg": 1.7, "cs": 50},
        },
        "England": {
            "MD1": {"opponent": "CRO", "attack": "medium", "defense": "average", "xg": 1.5, "cs": 45},
            "MD2": {"opponent": "GHA", "attack": "high", "defense": "strong", "xg": 2.1, "cs": 65},
            "MD3": {"opponent": "PAN", "attack": "high", "defense": "strong", "xg": 2.3, "cs": 70},
        },
    }

    color_map = {
        "high": "#22c55e", "medium": "#f59e0b", "low": "#ef4444",
        "strong": "#22c55e", "average": "#f59e0b", "weak": "#ef4444"
    }

    # Filter
    selected_teams = st.multiselect("Select Teams", list(teams_data.keys()), default=list(teams_data.keys()))

    # Display fixture table
    for team in selected_teams:
        st.markdown(f"### {team}")
        cols = st.columns(3)
        for i, md in enumerate(["MD1", "MD2", "MD3"]):
            with cols[i]:
                fixture = teams_data[team][md]
                st.markdown(f"""
                <div style="background:#1e293b; border-radius:8px; padding:12px; text-align:center;">
                    <div style="color:#94a3b8; font-size:12px;">vs {fixture['opponent']}</div>
                    <div style="margin-top:8px;">
                        <div style="background:{color_map[fixture['attack']]}; color:white; padding:4px 8px; border-radius:4px; display:inline-block; margin:2px;">
                            Attack: {fixture['xg']} xG
                        </div>
                    </div>
                    <div style="margin-top:4px;">
                        <div style="background:{color_map[fixture['defense']]}; color:white; padding:4px 8px; border-radius:4px; display:inline-block; margin:2px;">
                            Defense: {fixture['cs']}% CS
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Legend
    st.divider()
    st.markdown("""
    **Legend:**
    - 🟢 **High/Strong**: >1.8 xG / >60% Clean Sheet
    - 🟡 **Medium/Average**: 1.2-1.8 xG / 40-60% Clean Sheet
    - 🔴 **Low/Weak**: <1.2 xG / <40% Clean Sheet
    """)
```

- [ ] **Step 2: Test the UI renders**

```bash
streamlit run app.py
```
Verify: Fixture Analysis tab shows color-coded ratings matching mockup

- [ ] **Step 3: Commit**

```bash
git add ui/tabs/fixture_analysis.py
git commit -m "feat: add Fixture Analysis tab with color-coded ratings"
```

---

## Task 13: UI — Team Hub Tab

**Files:**
- Create: `ui/tabs/team_hub.py`
- Create: `ui/components/formation_display.py`
- Reference: `mockups/03-player-status.html`

- [ ] **Step 1: Create formation_display component**

```python
# ui/components/formation_display.py
import streamlit as st

def render_formation(formation: str, players: list):
    """Render football pitch formation matching mockup design."""
    st.markdown(f"""
    <div style="background:#166534; border-radius:12px; padding:24px; text-align:center;">
        <div style="color:white; margin-bottom:16px;">Formation: {formation}</div>
        <div style="display:flex; justify-content:center; gap:20px; margin-bottom:20px;">
            <div style="text-align:center;">
                <div style="width:40px; height:40px; background:#fbbf24; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">LW</div>
                <div style="color:white; font-size:11px; margin-top:4px;">Vinicius</div>
            </div>
            <div style="text-align:center;">
                <div style="width:40px; height:40px; background:#fbbf24; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">ST</div>
                <div style="color:white; font-size:11px; margin-top:4px;">Haaland</div>
            </div>
            <div style="text-align:center;">
                <div style="width:40px; height:40px; background:#fbbf24; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">RW</div>
                <div style="color:white; font-size:11px; margin-top:4px;">Mbappe</div>
            </div>
        </div>
        <div style="display:flex; justify-content:center; gap:20px; margin-bottom:20px;">
            <div style="text-align:center;">
                <div style="width:40px; height:40px; background:#3b82f6; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">CM</div>
                <div style="color:white; font-size:11px; margin-top:4px;">Bellingham</div>
            </div>
            <div style="text-align:center;">
                <div style="width:40px; height:40px; background:#3b82f6; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">CM</div>
                <div style="color:white; font-size:11px; margin-top:4px;">Pedri</div>
            </div>
            <div style="text-align:center;">
                <div style="width:40px; height:40px; background:#3b82f6; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">CM</div>
                <div style="color:white; font-size:11px; margin-top:4px;">Rodri</div>
            </div>
        </div>
        <div style="display:flex; justify-content:center; gap:16px; margin-bottom:16px;">
            <div style="text-align:center;">
                <div style="width:40px; height:40px; background:#22c55e; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">LB</div>
                <div style="color:white; font-size:11px; margin-top:4px;">Theo</div>
            </div>
            <div style="text-align:center;">
                <div style="width:40px; height:40px; background:#22c55e; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">CB</div>
                <div style="color:white; font-size:11px; margin-top:4px;">Rudiger</div>
            </div>
            <div style="text-align:center;">
                <div style="width:40px; height:40px; background:#22c55e; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">CB</div>
                <div style="color:white; font-size:11px; margin-top:4px;">Dias</div>
            </div>
            <div style="text-align:center;">
                <div style="width:40px; height:40px; background:#22c55e; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">RB</div>
                <div style="color:white; font-size:11px; margin-top:4px;">Trent</div>
            </div>
        </div>
        <div style="text-align:center;">
            <div style="width:40px; height:40px; background:#f97316; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">GK</div>
            <div style="color:white; font-size:11px; margin-top:4px;">Courtois</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
```

- [ ] **Step 2: Create team_hub tab**

```python
# ui/tabs/team_hub.py
import streamlit as st
from ui.components.formation_display import render_formation

def render():
    st.header("Team Hub")
    st.caption("Country overview with squad fitness and lineup predictions")

    country = st.selectbox("Select Country", ["Brazil", "France", "Argentina", "England"])

    # Squad Overview
    st.subheader(f"{country} Squad")
    render_formation("4-3-3", [])

    # Squad Fitness
    st.subheader("Squad Fitness")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🟢 Available", "23")
    with col2:
        st.metric("🟡 Doubtful", "2")
    with col3:
        st.metric("🔴 Injured", "1")
    with col4:
        st.metric("🟠 Suspended", "0")

    # Fitness Details
    st.markdown("""
    <div style="background:#1e293b; border-radius:10px; padding:16px; margin-top:16px;">
        <h4 style="margin-bottom:12px;">Player Status</h4>
        <div style="display:grid; gap:8px;">
            <div style="background:#0f172a; padding:10px; border-radius:6px; border-left:4px solid #ef4444;">
                <strong>Neymar Jr</strong> - ACL tear (Tournament over)
            </div>
            <div style="background:#0f172a; padding:10px; border-radius:6px; border-left:4px solid #f59e0b;">
                <strong>Alisson</strong> - Minor knock (70% chance MD1)
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Lineup Prediction
    st.subheader("Lineup Prediction")
    st.markdown("""
    **Likely Starting XI (Last 6 matches):**
    - GK: Alisson (95%)
    - DEF: Marquinhos (100%), Gabriel (85%), Rudiger (90%), Danilo (80%)
    - MID: Casemiro (90%), Bruno Guimaraes (85%), Vinicius Jr (75%)
    - FWD: Rodrygo (90%), Richarlison (70%), Raphinha (85%)
    """)
```

- [ ] **Step 3: Test the UI renders**

```bash
streamlit run app.py
```
Verify: Team Hub tab shows formation, squad fitness, and lineup prediction matching mockup

- [ ] **Step 4: Commit**

```bash
git add ui/tabs/team_hub.py ui/components/formation_display.py
git commit -m "feat: add Team Hub tab with formation display and squad fitness"
```

---

## Task 14: UI — Team Selector Tab

**Files:**
- Create: `ui/tabs/team_selector.py`
- Reference: `mockups/01-player-comparison.html`

- [ ] **Step 1: Create team_selector tab**

```python
# ui/tabs/team_selector.py
import streamlit as st

def render():
    st.header("Team Selector")
    st.caption("Optimal squad within your $100m budget")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Football Pitch")
        st.markdown("""
        <div style="background:#166534; border-radius:12px; padding:24px; text-align:center;">
            <div style="color:white; margin-bottom:16px;">Formation: 4-3-3</div>
            <div style="display:flex; justify-content:center; gap:20px; margin-bottom:20px;">
                <div style="text-align:center;">
                    <div style="width:40px; height:40px; background:#fbbf24; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">LW</div>
                    <div style="color:white; font-size:11px; margin-top:4px;">Vinicius</div>
                </div>
                <div style="text-align:center;">
                    <div style="width:40px; height:40px; background:#fbbf24; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">ST</div>
                    <div style="color:white; font-size:11px; margin-top:4px;">Haaland</div>
                </div>
                <div style="text-align:center;">
                    <div style="width:40px; height:40px; background:#fbbf24; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">RW</div>
                    <div style="color:white; font-size:11px; margin-top:4px;">Mbappe</div>
                </div>
            </div>
            <div style="display:flex; justify-content:center; gap:20px; margin-bottom:20px;">
                <div style="text-align:center;">
                    <div style="width:40px; height:40px; background:#3b82f6; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">CM</div>
                    <div style="color:white; font-size:11px; margin-top:4px;">Bellingham</div>
                </div>
                <div style="text-align:center;">
                    <div style="width:40px; height:40px; background:#3b82f6; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">CM</div>
                    <div style="color:white; font-size:11px; margin-top:4px;">Pedri</div>
                </div>
                <div style="text-align:center;">
                    <div style="width:40px; height:40px; background:#3b82f6; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">CM</div>
                    <div style="color:white; font-size:11px; margin-top:4px;">Rodri</div>
                </div>
            </div>
            <div style="display:flex; justify-content:center; gap:16px; margin-bottom:16px;">
                <div style="text-align:center;">
                    <div style="width:40px; height:40px; background:#22c55e; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">LB</div>
                    <div style="color:white; font-size:11px; margin-top:4px;">Theo</div>
                </div>
                <div style="text-align:center;">
                    <div style="width:40px; height:40px; background:#22c55e; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">CB</div>
                    <div style="color:white; font-size:11px; margin-top:4px;">Rudiger</div>
                </div>
                <div style="text-align:center;">
                    <div style="width:40px; height:40px; background:#22c55e; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">CB</div>
                    <div style="color:white; font-size:11px; margin-top:4px;">Dias</div>
                </div>
                <div style="text-align:center;">
                    <div style="width:40px; height:40px; background:#22c55e; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">RB</div>
                    <div style="color:white; font-size:11px; margin-top:4px;">Trent</div>
                </div>
            </div>
            <div style="text-align:center;">
                <div style="width:40px; height:40px; background:#f97316; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto; font-size:12px;">GK</div>
                <div style="color:white; font-size:11px; margin-top:4px;">Courtois</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.subheader("Squad Summary")
        st.markdown("""
        <div style="background:#1e293b; border-radius:12px; padding:16px;">
            <div style="display:grid; gap:12px;">
                <div style="background:#0f172a; padding:12px; border-radius:8px; display:flex; justify-content:space-between;">
                    <span style="color:#94a3b8;">Budget Used</span>
                    <span style="font-weight:bold;">$94.2m / $100m</span>
                </div>
                <div style="background:#0f172a; padding:12px; border-radius:8px; display:flex; justify-content:space-between;">
                    <span style="color:#94a3b8;">Remaining</span>
                    <span style="font-weight:bold; color:#22c55e;">$5.8m</span>
                </div>
                <div style="background:#0f172a; padding:12px; border-radius:8px; display:flex; justify-content:space-between;">
                    <span style="color:#94a3b8;">Total Points</span>
                    <span style="font-weight:bold;">312 pts</span>
                </div>
                <div style="background:#0f172a; padding:12px; border-radius:8px; display:flex; justify-content:space-between;">
                    <span style="color:#94a3b8;">Avg Form</span>
                    <span style="font-weight:bold;">4.2 ★</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Captain Pick**")
        st.markdown("""
        <div style="background:#fbbf2420; border:1px solid #fbbf24; border-radius:8px; padding:12px; display:flex; align-items:center; gap:12px;">
            <div style="width:48px; height:48px; background:#fbbf24; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:20px;">👑</div>
            <div>
                <div style="font-weight:bold;">Kylian Mbappe</div>
                <div style="color:#94a3b8; font-size:13px;">vs Australia (MD1) — 87% ownership</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Optimize My Team", type="primary", use_container_width=True):
            st.success("Team optimized!")
```

- [ ] **Step 2: Test the UI renders**

```bash
streamlit run app.py
```
Verify: Team Selector tab shows pitch and squad summary matching mockup

- [ ] **Step 3: Commit**

```bash
git add ui/tabs/team_selector.py
git commit -m "feat: add Team Selector tab with optimizer UI"
```

---

## Task 15: Integration Testing

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_integration.py
from data.cache import Cache
from data.fetcher import WorldCupFetcher
from analysis.player_stats import PlayerStats
from analysis.fixture_analysis import FixtureAnalyzer
from analysis.team_optimizer import TeamOptimizer

def test_full_workflow():
    cache = Cache("test_integration")
    stats = PlayerStats()
    analyzer = FixtureAnalyzer()
    optimizer = TeamOptimizer(budget=100.0)

    players = [
        {"name": "Mbappe", "price": 13.0, "position": "FWD", "points": 50, "goals": 4, "status": "available"},
        {"name": "Courtois", "price": 5.0, "position": "GK", "points": 30, "goals": 0, "status": "available"},
    ]

    top = stats.get_top_players(players, "points")
    assert len(top) == 2

    team = optimizer.select_team(players, "4-3-3")
    assert len(team) <= 11

    fixture = {"home_xg": 2.0, "away_xg": 1.2, "home_cs": 55, "away_cs": 70}
    analysis = analyzer.analyze_fixture(fixture)
    assert "home_attack" in analysis

    cache.clear()
```

- [ ] **Step 2: Run integration test**

```bash
pytest tests/test_integration.py -v
```
Expected: PASS

- [ ] **Step 3: Final commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests"
```

---

## Self-Review Checklist

- [ ] All 4 tabs implemented (Player Hub, Fixture Analysis, Team Hub, Team Selector)
- [ ] Data layer: fetcher, scraper, cache all working
- [ ] Analysis layer: all 6 modules implemented
- [ ] UI components: player_card, formation_display, stats_table
- [ ] Tests passing for all modules
- [ ] No placeholders or TODOs in code
- [ ] Config properly handles API keys via .env

---

*Plan created: 2026-06-06*
