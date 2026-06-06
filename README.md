# Fantasy Football World Cup 2026 Copilot

A Streamlit dashboard for analyzing FIFA World Cup 2026 Fantasy Football decisions — player comparison, fixture analysis, team selection, and expert opinions.

## Features

- **Player Hub** — search, rank, and compare players by position, goals, fantasy points, and fitness status. Includes expert recommendations classified by player and country.
- **Fixture Analysis** — view fixtures with attack (xG) and defense (CS%) ratings. Color-coded easy/medium/hard difficulty per team.
- **Team Hub** — browse national team squads, predict starting XI based on last 6 months of selections, and track player fitness (Healthy / Rotation Risk / Injury Risk / Doubtful / Suspended).
- **Team Selector** — auto-optimize your fantasy XI within budget and formation constraints, or manually pick players.
- **Auto-Discover Players** — LLM automatically discovers new players from articles, verifies they are real, and adds to database

### Expert Scraping

- Depth-aware crawler (configurable, default 2 levels deep)
- Deduplicates visited URLs across sources
- Polite delays between requests (2-5 seconds)
- Full browser-like headers to avoid bot detection
- Classified by player and country with sentiment analysis
- Optional LLM extraction (HuggingFace free tier or Google Gemini)

### Auto-Discover Players

The scraper automatically discovers new football players from expert articles using LLM verification:

1. Extracts player names from all articles (batched)
2. Filters out already-known players
3. Verifies unknowns with LLM ("Is this a real football player?")
4. Saves verified players to `data/learned_players.json`

To reset learned players:
```bash
rm data/cache/learned_players.json
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set API keys (optional but recommended)

Create a `.env` file in the project root:

```
API_FOOTBALL_KEY=your_api_key_here

# Optional: for better article extraction
LLM_PROVIDER=huggingface
HUGGINGFACE_API_KEY=your_token_here
```

Get a free API key from [API-Football](https://www.api-football.com/) (100 req/day free).
Get a free HuggingFace token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).

### 3. Scrape expert opinions

```bash
python scrape.py              # Normal scrape (skips already-crawled pages)
python scrape.py --reset      # Re-crawl everything from scratch
```

### 4. Fetch player and fixture data

```bash
python -c "from data.fetcher import fetch_players, fetch_fixtures; fetch_players(use_cache=False); fetch_fixtures(use_cache=False); print('Done')"
```

### 5. Run the dashboard

```bash
streamlit run app.py
```

Opens at `http://localhost:8501` with 4 tabs.

## Configuration

All settings in `config.py` (or override via `.env`):

| Setting | Default | Description |
|---------|---------|-------------|
| `CRAWL_DEPTH` | `2` | How many levels deep to follow links |
| `CRAWL_DELAY_MIN` | `2` | Min seconds between requests |
| `CRAWL_DELAY_MAX` | `5` | Max seconds between requests |
| `CRAWL_MAX_PAGES_PER_SOURCE` | `10` | Max pages to crawl per source |
| `LLM_PROVIDER` | `openrouter` | LLM provider: `openrouter`, `huggingface`, or `gemini` |
| `HUGGINGFACE_MODEL` | `microsoft/Phi-3-mini-4k-instruct` | HF model to use |
| `CACHE_TTL_HOURS` | `24` | How long to cache fetched data |
| `OPENROUTER_API_KEY` | (required for LLM) | OpenRouter API key for better model quality |
| `OPENROUTER_MODELS` | `["nvidia/nemotron-3-super:free", ...]` | Fallback model array |

## Project Structure

```
fantasy-football-copilot/
├── app.py                  # Streamlit entry point
├── config.py               # All settings
├── .env.example            # Environment variable template
├── requirements.txt        # Python dependencies
├── data/
│   ├── cache.py            # JSON cache with TTL
│   ├── crawler.py          # Depth-aware web crawler
│   ├── extractor.py        # LLM extraction (HF, Gemini)
│   ├── fetcher.py          # API-Football data fetcher
│   ├── scraper.py          # Orchestrates crawler + extraction
│   └── players_reference.py # ~120 WC players for name matching
├── analysis/
│   ├── player_stats.py     # Player ranking & comparison
│   ├── fixture_analysis.py # Fixture difficulty ratings
│   ├── team_optimizer.py   # Auto-optimize fantasy XI
│   ├── lineup_predictor.py # Starting XI prediction
│   ├── player_fitness.py   # Fitness & status assessment
│   └── expert_opinions.py  # Player/country mention classification
├── ui/
│   └── tabs/
│       ├── player_hub.py
│       ├── fixture_analysis.py
│       ├── team_hub.py
│       └── team_selector.py
├── tests/                  # 63 tests
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
- **BeautifulSoup4** — web scraping/crawling
- **Requests** — API calls
- **OpenRouter** — LLM extraction (free models with fallback)

## Deploy to Streamlit Community Cloud

Access your dashboard from any device — free, permanent URL.

### 1. Go to [share.streamlit.io](https://share.streamlit.io)

Sign in with your GitHub account.

### 2. Create a new app

- **Repository:** `ahaqqu/fantasy-football-copilot`
- **Branch:** `main`
- **Main file path:** `app.py`

### 3. Add secrets

Click "Advanced settings" → "Secrets" and paste:

```toml
API_FOOTBALL_KEY = "your_api_football_key"

# OpenRouter (recommended)
LLM_PROVIDER = "openrouter"
OPENROUTER_API_KEY = "your_openrouter_key"

# OR HuggingFace (fallback)
# LLM_PROVIDER = "huggingface"
# HUGGINGFACE_API_KEY = "your_hf_token"
```

### 4. Deploy

Click "Deploy". You'll get a URL like:
```
https://your-app-name.streamlit.app
```

### 5. Scrape on cloud

Click "Scrape Now" button in the Expert Picks tab, or run:
```bash
# Local: scrape first, then deploy
python scrape.py
git add data/cache/
git commit -m "data: add scraped expert opinions"
git push
```

### Notes

- **Free tier limits:** Streamlit Community Cloud has 1GB memory, 1 CPU
- **Scraping works:** The crawler runs on Streamlit's servers
- **No paid APIs needed:** Uses free OpenRouter models
- **Data persists:** Cache files stay in the repo (commit them)
