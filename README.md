# Fantasy Football World Cup 2026 Copilot

A Streamlit dashboard for analyzing FIFA World Cup 2026 Fantasy Football decisions — player comparison, fixture analysis, team selection, and expert opinions.

## Features

- **Player Hub** — search, rank, and compare players by position, goals, fantasy points, and fitness status. Includes expert recommendations from FantasyFootballScout, FantasyFootballHub, AllAboutFPL, RotoWire, and FootballPredictions.com.
- **Fixture Analysis** — view fixtures with attack (xG) and defense (CS%) ratings. Color-coded easy/medium/hard difficulty per team.
- **Team Hub** — browse national team squads, predict starting XI based on last 6 months of selections, and track player fitness (Healthy / Rotation Risk / Injury Risk / Doubtful / Suspended).
- **Team Selector** — auto-optimize your fantasy XI within budget and formation constraints, or manually pick players.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set API key (optional but recommended)

Get a free API key from [API-Football](https://www.api-football.com/), then create a `.env` file in the project root:

```
API_FOOTBALL_KEY=your_api_key_here
```

The app loads it automatically on startup. `.env` is git-ignored so your key stays local.

Without an API key the dashboard still loads but shows empty data.

### 3. Scrape expert opinions

Expert opinions are scraped from 5 fantasy football sites and cached locally.

```bash
python -c "from data.scraper import scrape_expert_opinions; scrape_expert_opinions(use_cache=False); print('Scraping done')"
```

### 4. Fetch player and fixture data

Fetches World Cup players and fixtures from API-Football, saves to local JSON cache.

```bash
python -c "from data.fetcher import fetch_players, fetch_fixtures; fetch_players(use_cache=False); fetch_fixtures(use_cache=False); print('Fetch done')"
```

### 5. Run the dashboard

```bash
streamlit run app.py
```

Opens in your browser at `http://localhost:8501`.

### 6. Open the dashboard

Once the server is running, open your browser and go to:

```
http://localhost:8501
```

You should see the 4-tab dashboard:
1. Click **Player Hub** to search and compare players
2. Click **Fixture Analysis** to see upcoming fixtures with difficulty ratings
3. Click **Team Hub** to view a national team's squad and predicted lineup
4. Click **Team Selector** to auto-optimize or manually build your fantasy XI

## Data Caching

All fetched data is cached as JSON files in `data/cache/` with a 24-hour TTL. To force a refresh:

```bash
python -c "
from data.fetcher import fetch_players, fetch_fixtures
from data.scraper import scrape_expert_opinions

fetch_players(use_cache=False)
fetch_fixtures(use_cache=False)
scrape_expert_opinions(use_cache=False)
print('All data refreshed')
"
```

## Project Structure

```
fantasy-football-copilot/
├── app.py                  # Streamlit entry point
├── config.py               # API keys, settings, paths
├── requirements.txt        # Python dependencies
├── data/
│   ├── cache.py            # JSON cache with TTL
│   ├── fetcher.py          # API-Football data fetcher
│   └── scraper.py          # Expert site scraper
├── analysis/
│   ├── player_stats.py     # Player ranking & comparison
│   ├── fixture_analysis.py # Fixture difficulty ratings
│   ├── team_optimizer.py   # Auto-optimize fantasy XI
│   ├── lineup_predictor.py # Starting XI prediction
│   ├── player_fitness.py   # Fitness & status assessment
│   └── expert_opinions.py  # Expert recommendation extraction
├── ui/
│   ├── tabs/
│   │   ├── player_hub.py
│   │   ├── fixture_analysis.py
│   │   ├── team_hub.py
│   │   └── team_selector.py
│   └── components/
├── tests/                  # Test suite (52 tests)
└── mockups/                # HTML mockup references
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Tech Stack

- **Python** + **Streamlit** — dashboard framework
- **Plotly** — interactive charts
- **Pandas** — data manipulation
- **BeautifulSoup4** — web scraping
- **Requests** — API calls
