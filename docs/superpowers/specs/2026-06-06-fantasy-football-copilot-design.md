# Fantasy Football World Cup 2026 Copilot — Design Spec

## Overview

A web-based dashboard to help analyze FIFA World Cup 2026 Fantasy Football decisions: which players to buy, who to captain, and how to build an optimal squad.

**Target user:** Single player (personal tool)
**Tech stack:** Python + Streamlit + Plotly charts
**Data sources:** World Cup data APIs + FantasyFootballScout scraping

---

## Goals

1. **Player Hub** — All player stats, fitness status, and expert opinions in one place
2. **Fixture Analysis** — Attack/defense strength for upcoming matches
3. **Team Hub** — Country overview with squad fitness and lineup predictions
4. **Team Selector** — Auto-build optimal squad within budget

---

## Data Sources

### Primary: World Cup Data APIs
- **TheStatsAPI** or **API-Football** for:
  - Fixtures and match schedules
  - Player statistics (goals, assists, xG, minutes)
  - Team statistics (possession, shots, xG against)
  - Standings and group tables
  - Lineups (historical and predicted)
  - Player injuries and fitness status

### Secondary: Expert Opinion Sources

**FantasyFootballScout** (fantasyfootballscout.co.uk)
- Expert team reveals and captain picks
- AI Team Rater tool
- StatsBomb qualifying data
- Player ownership percentages

**FantasyFootballHub** (fantasyfootballhub.co.uk)
- Expert tips from content creators
- AI-powered team ratings
- Fixture difficulty analysis
- Mini-league competition

**AllAboutFPL** (allaboutfpl.com)
- Free guides and tips
- Budget picks and differentials
- Predicted goals for/against tables
- Chip strategy advice

**RotoWire** (rotowire.com)
- Professional rankings
- Projected lineups
- Set piece takers by team
- Matchday-specific picks

**FootballPredictions.com**
- Match result predictions
- Goal predictions
- Form analysis

**Data sources for fitness:**
- Club injury reports (pre-match press conferences)
- FantasyFootballScout news feeds
- API-Football injury endpoints
- Journalist Twitter/X reports

### Data Refresh Strategy
- **Live data:** Auto-refresh every 5 minutes during match days
- **Historical data:** Fetch once per day for last 12 months
- **Scraped content:** Fetch once daily for latest articles

---

## Dashboard Structure

### Tab 1: Player Hub

**All-in-one player view with 3 sections:**

**Section A: Player Stats**
- Player avatar (country flag)
- Name, team, position
- Stats grid: Price ($), Points, Goals, Assists, xG
- Form indicator: Star rating (★★★★☆)
- Club performance (last 12 months)
- International performance (last 12 months)

**Section B: Fitness Status**
- Status icon: 🟢 Available / 🟡 Doubtful / 🔴 Injured / 🟠 Suspended
- Injury type (if applicable)
- Expected return date
- Last updated timestamp

**Section C: Expert Opinions**
- Summary from FantasyFootballScout
- Captain pick recommendations
- Differential suggestions
- Key quotes from expert articles

**Interactions:**
- Search/filter players
- Position and team filters
- Sort by: Price, Points, Form, Fitness status

---

### Tab 2: Fixture Analysis

**Layout:** Color-coded table with attack/defense ratings

**Columns:** Team, MD1, MD2, MD3, R32, R16

**Each cell shows:**
- **Attack strength:** xG (expected goals) + color coding
- **Defense strength:** CS% (clean sheet %) + color coding

**Color coding:**
- Green: High attack (>1.8 xG) / Strong defense (>60% CS)
- Yellow: Medium attack (1.2-1.8 xG) / Average defense (40-60% CS)
- Red: Low attack (<1.2 xG) / Weak defense (<40% CS)

**Interactions:**
- Filter by team
- Toggle between attack/defense view
- Hover for detailed stats

---

### Tab 3: Team Hub

**Country overview with 2 sections:**

**Section A: Squad Overview**
- Country flag and coach name
- Formation display (e.g., 4-3-3)
- All players with position and club

**Section B: Squad Fitness**
- List of all players with status:
  - 🟢 Available (count)
  - 🟡 Doubtful (count)
  - 🔴 Injured (count)
  - 🟠 Suspended (count)
- Individual player cards with injury details

**Section C: Lineup Prediction**
- Likely starting XI with start probability %
- Based on last 6 months of selections
- Color coding for confidence level

**Interactions:**
- Select different countries
- View historical lineups
- Filter by fitness status

---

### Tab 4: Team Selector

**Layout:** Split view

**Left side:** Football pitch with formation (e.g., 4-3-3)
- Players shown in their positions
- Color-coded by position (GK=orange, DEF=green, MID=blue, FWD=yellow)
- Click player to see details

**Right side:** Squad summary panel
- Budget used / remaining
- Total points
- Average form
- Captain recommendation with rationale
- "Optimize My Team" button

**Optimization algorithm:**
- Maximize total expected points
- Stay within budget ($100m)
- Respect formation constraints
- Consider fixture difficulty
- Factor in player form
- Exclude injured/suspended players

---

## Technical Architecture

### Backend (Python)
```
fantasy-copilot/
├── app.py                  # Main Streamlit app
├── requirements.txt        # Dependencies
├── config.py              # API keys, settings
├── data/
│   ├── fetcher.py         # API calls
│   ├── scraper.py         # FantasyFootballScout + expert sites scraping
│   └── cache.py           # Local data caching
├── analysis/
│   ├── player_stats.py    # Player comparison logic
│   ├── fixture_analysis.py # Fixture difficulty calculation
│   ├── team_optimizer.py  # Squad selection algorithm
│   ├── lineup_predictor.py # Starting XI prediction
│   ├── player_fitness.py  # Injury/fitness status tracking
│   └── expert_opinions.py # Scrape & summarize expert articles
└── ui/
    ├── tabs/
    │   ├── player_hub.py       # All player stats + fitness + opinions
    │   ├── fixture_analysis.py # Attack/defense fixture ratings
    │   ├── team_hub.py         # Country overview + squad fitness
    │   └── team_selector.py    # Squad optimizer
    └── components/
        ├── player_card.py
        ├── formation_display.py
        └── stats_table.py
```

### Dependencies
- `streamlit` — Web framework
- `plotly` — Interactive charts
- `pandas` — Data manipulation
- `requests` — API calls
- `beautifulsoup4` — Web scraping
- `schedule` — Data refresh scheduling

### Data Flow
1. **Fetch** → API/scraper collects raw data
2. **Transform** → Clean, normalize, calculate derived stats
3. **Cache** → Store locally to avoid repeated API calls
4. **Analyze** → Run algorithms (optimizer, predictor)
5. **Display** → Streamlit renders dashboard

---

## Success Criteria

1. Dashboard loads in < 3 seconds
2. Player Hub shows all stats, fitness, and expert opinions in one place
3. Fixture analysis correctly identifies easy/hard matchups
4. Team Hub shows squad fitness and lineup predictions
5. Team selector builds valid squads within budget
6. Data refreshes automatically without manual intervention
7. Player fitness status is accurate and updated within 24 hours
8. Expert opinions are scraped and summarized daily

---

## Future Enhancements (Out of Scope)

- Multi-user support
- Mobile-responsive design
- Push notifications for lineup changes
- Historical analysis across multiple tournaments
- Integration with actual FIFA Fantasy API for direct team import

---

## Open Questions

1. **API key budget:** Which API provider to use? (TheStatsAPI has free tier)
2. **Scraping legality:** Is scraping FantasyFootballScout allowed? (For personal use only)
3. **Caching strategy:** How long to cache data? (Suggest: 5 min for live, 24h for historical)
4. **Deployment:** Run locally or deploy to cloud? (Suggest: local for personal tool)

---

## Visual Mockup Reference

See `.superpowers/brainstorm/test-session/content/` for visual mockups:
- `dashboard-mockup.html` - Initial 3-tab layout
- `dashboard-mockup-v2.html` - Enhanced with attack/defense ratings
- `dashboard-mockup-v3-player-status.html` - Player fitness status (now embedded in Player Hub & Team Hub)

---

*Last updated: 2026-06-06*
