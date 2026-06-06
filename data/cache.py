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