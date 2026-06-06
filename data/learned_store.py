"""Persistent storage for LLM-discovered players."""
import json
import time
from typing import Any

from config import SHARED_DIR
from data.players_reference import PLAYERS_BY_COUNTRY

_LEARNED_FILE = SHARED_DIR / "learned_players.json"


def _ensure_file() -> None:
    """Create learned JSON file if it doesn't exist."""
    if not _LEARNED_FILE.exists():
        SHARED_DIR.mkdir(parents=True, exist_ok=True)
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
