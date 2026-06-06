"""Configuration for Fantasy Football Copilot."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# === Paths ===
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"

# Ensure directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# === API Keys ===
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
API_FOOTBALL_BASE = "https://v3.football.api-sports.io"

# TheStatsAPI (soccer) — optional alternative
STATS_API_KEY = os.getenv("STATS_API_KEY", "")
STATS_API_BASE = "https://api.thestatsapi.com/v1"

# === Cache Settings ===
CACHE_TTL_HOURS = 24  # Re-fetch data after this many hours

# === Tournament Settings ===
WORLD_CUP_YEAR = 2026
WORLD_CUP_HOST = "USA, Canada, Mexico"
BUDGET_LIMIT = 100  # FIFA Fantasy budget
SQUAD_SIZE = 11
FORMATION = "4-4-2"  # Default formation

# === Expert Sources ===
EXPERT_SOURCES = [
    {"name": "FantasyFootballScout", "url": "https://www.fantasyfootballscout.co.uk/fantasy-fifa-world-cup-2026-ultimate-guide-best-players-tips-team-reveals-more"},
    {"name": "FantasyFootballHub", "url": "https://www.fantasyfootballhub.co.uk/world-cup-fantasy-tips-ultimate-guide"},
    {"name": "AllAboutFPL", "url": "https://allaboutfpl.com/category/2026-fifa-world-cup-fantasy/"},
    {"name": "FootballCoin", "url": "https://www.footballcoin.io/blog/fantasy-football-world-cup-2026-top-picks-budget-alternatives"},
]
