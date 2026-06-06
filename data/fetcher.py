"""Fetch player and fixture data from API-Football (api-sports.io)."""
import logging
from typing import Any

import requests

from config import API_FOOTBALL_BASE, API_FOOTBALL_KEY
from data.cache import get_cached, save_to_cache

logger = logging.getLogger(__name__)

WORLD_CUP_LEAGUE_ID = 1  # FIFA World Cup
WORLD_CUP_SEASON = 2026


def _api_get(endpoint: str, api_key: str, params: dict) -> dict[str, Any]:
    """Make a GET request to API-Football."""
    headers = {"x-apisports-key": api_key}
    url = f"{API_FOOTBALL_BASE}/{endpoint}"
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_players(
    api_key: str = API_FOOTBALL_KEY,
    league_id: int = WORLD_CUP_LEAGUE_ID,
    season: int = WORLD_CUP_SEASON,
    use_cache: bool = True,
) -> list[dict]:
    """Fetch all World Cup players. Returns list of player dicts."""
    cache_key = f"players_{league_id}_{season}"
    if use_cache:
        cached = get_cached(cache_key)
        if cached is not None:
            return cached

    if not api_key:
        logger.warning("No API key configured — returning empty list")
        return []

    try:
        data = _api_get("players", api_key, {"league": league_id, "season": season})
        players = data.get("response", [])
        save_to_cache(cache_key, players)
        return players
    except requests.RequestException as e:
        logger.error("Failed to fetch players: %s", e)
        return []
    except Exception as e:
        logger.error("Unexpected error fetching players: %s", e)
        return []


def fetch_fixtures(
    api_key: str = API_FOOTBALL_KEY,
    league_id: int = WORLD_CUP_LEAGUE_ID,
    season: int = WORLD_CUP_SEASON,
    use_cache: bool = True,
) -> list[dict]:
    """Fetch World Cup fixtures. Returns list of fixture dicts."""
    cache_key = f"fixtures_{league_id}_{season}"
    if use_cache:
        cached = get_cached(cache_key)
        if cached is not None:
            return cached

    if not api_key:
        logger.warning("No API key configured — returning empty list")
        return []

    try:
        data = _api_get("fixtures", api_key, {"league": league_id, "season": season})
        fixtures = data.get("response", [])
        save_to_cache(cache_key, fixtures)
        return fixtures
    except requests.RequestException as e:
        logger.error("Failed to fetch fixtures: %s", e)
        return []
    except Exception as e:
        logger.error("Unexpected error fetching fixtures: %s", e)
        return []


def fetch_team_players(
    api_key: str = API_FOOTBALL_KEY,
    team_id: int = 0,
    league_id: int = WORLD_CUP_LEAGUE_ID,
    season: int = WORLD_CUP_SEASON,
    use_cache: bool = True,
) -> list[dict]:
    """Fetch players for a specific team."""
    cache_key = f"team_{team_id}_players_{league_id}_{season}"
    if use_cache:
        cached = get_cached(cache_key)
        if cached is not None:
            return cached

    if not api_key:
        logger.warning("No API key configured — returning empty list")
        return []

    try:
        data = _api_get("players", api_key, {"team": team_id, "league": league_id, "season": season})
        players = data.get("response", [])
        save_to_cache(cache_key, players)
        return players
    except requests.RequestException as e:
        logger.error("Failed to fetch team players: %s", e)
        return []
    except Exception as e:
        logger.error("Unexpected error fetching team players: %s", e)
        return []
