"""Configuration for Fantasy Football Copilot."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# === Paths ===
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
SHARED_DIR = DATA_DIR / "shared"  # Committed to git, read by Streamlit Cloud

# Ensure directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)
SHARED_DIR.mkdir(parents=True, exist_ok=True)

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

# === Crawler Settings ===
CRAWL_DEPTH = 3  # How many levels deep to follow links (0 = landing page only)
CRAWL_DELAY_MIN = 2  # Min seconds between requests (be polite)
CRAWL_DELAY_MAX = 5  # Max seconds between requests
CRAWL_TIMEOUT = 15  # Request timeout in seconds
CRAWL_MAX_PAGES_PER_SOURCE = 50  # Max pages to crawl per source

# URL patterns to exclude from crawling (glob-style paths)
EXCLUDED_URL_PATTERNS = [
    "fantasyfootballscout.co.uk/profiles/",
]

# Domain-specific URL path restrictions — only URLs matching these prefixes are followed.
# If a domain is listed here, ONLY URLs under the listed paths are crawled.
DOMAIN_URL_PATTERNS = {
    "www.footballcoin.io": ["/blog/"],
    "www.fantasyfootballscout.co.uk": ["/2026/"],
    "allaboutfpl.com": ["/2026/", "/category/"],
}

# URLs with years older than this are excluded (e.g. /2022/ in path)
MIN_ARTICLE_YEAR = 2026

# Browser-like headers to avoid bot detection
CRAWL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# === LLM Extraction Settings ===
# Provider: "openrouter" (recommended), "huggingface", or "gemini"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
HUGGINGFACE_MODEL = "microsoft/Phi-3-mini-4k-instruct"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"

# === OpenRouter Settings ===
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",    # 120B, primary
    "google/gemma-4-31b-it:free",                 # 31B, fast fallback
    "nvidia/nemotron-3-nano-30b-a3b:free",        # 30B, lightweight fallback
]
