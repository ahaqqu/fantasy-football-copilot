"""Tests for data.cache — Cache System."""
import json
import time
from data.cache import get_cached, save_to_cache


def test_save_and_get(tmp_path):
    """Save data, then retrieve it."""
    save_to_cache("test_key", {"foo": "bar"}, cache_dir=tmp_path)
    result = get_cached("test_key", cache_dir=tmp_path)
    assert result == {"foo": "bar"}


def test_get_expired_returns_none(tmp_path):
    """Expired cache returns None."""
    # Create a file with timestamp 99999 hours in the past
    cache_file = tmp_path / "expired_key.json"
    old_time = time.time() - (99999 * 3600)
    with open(cache_file, "w") as f:
        json.dump({"data": {"old": True}, "timestamp": old_time}, f)
    result = get_cached("expired_key", cache_dir=tmp_path, ttl_hours=24)
    assert result is None


def test_missing_key_returns_none(tmp_path):
    """Non-existent key returns None."""
    result = get_cached("nonexistent", cache_dir=tmp_path)
    assert result is None


def test_save_creates_directory(tmp_path):
    """save_to_cache creates cache dir if missing."""
    sub_dir = tmp_path / "nested" / "cache"
    save_to_cache("key", {"a": 1}, cache_dir=sub_dir)
    result = get_cached("key", cache_dir=sub_dir)
    assert result == {"a": 1}