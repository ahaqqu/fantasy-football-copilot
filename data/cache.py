"""JSON file-based cache with TTL expiry."""
import json
import time
from pathlib import Path
from typing import Any, Optional

from config import CACHE_DIR


def get_cached(
    key: str,
    cache_dir: Path = CACHE_DIR,
    ttl_hours: int = 24,
) -> Optional[Any]:
    """Return cached data if it exists and is fresh, else None."""
    cache_file = cache_dir / f"{key}.json"
    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
        age_hours = (time.time() - payload["timestamp"]) / 3600
        if age_hours > ttl_hours:
            return None
        return payload["data"]
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def save_to_cache(
    key: str,
    data: Any,
    cache_dir: Path = CACHE_DIR,
) -> None:
    """Save data to a JSON file with timestamp."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{key}.json"
    payload = {"data": data, "timestamp": time.time()}
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)


# === Visited URLs Cache ===
_VISITED_FILE = CACHE_DIR / "visited_urls.json"


def get_visited() -> set[str]:
    """Load previously visited URLs from disk."""
    if not _VISITED_FILE.exists():
        return set()
    try:
        with open(_VISITED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("urls", []))
    except (json.JSONDecodeError, OSError):
        return set()


def save_visited(urls: set[str]) -> None:
    """Save visited URLs to disk."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(_VISITED_FILE, "w", encoding="utf-8") as f:
        json.dump({"urls": sorted(urls), "timestamp": time.time()}, f, indent=2)


def reset_visited() -> int:
    """Delete visited URLs file. Returns number of URLs cleared."""
    if not _VISITED_FILE.exists():
        return 0
    try:
        with open(_VISITED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        count = len(data.get("urls", []))
    except (json.JSONDecodeError, OSError):
        count = 0
    _VISITED_FILE.unlink(missing_ok=True)
    return count


def get_visited_count() -> int:
    """Get number of visited URLs without loading them all."""
    if not _VISITED_FILE.exists():
        return 0
    try:
        with open(_VISITED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return len(data.get("urls", []))
    except (json.JSONDecodeError, OSError):
        return 0
