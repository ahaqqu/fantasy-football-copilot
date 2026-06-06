"""Tests for data.cache — Cache System."""
import json
import time
from unittest.mock import patch
from data.cache import (
    get_cached,
    save_to_cache,
    get_visited,
    save_visited,
    reset_visited,
    get_visited_count,
)


def test_save_and_get(tmp_path):
    """Save data, then retrieve it."""
    save_to_cache("test_key", {"foo": "bar"}, cache_dir=tmp_path)
    result = get_cached("test_key", cache_dir=tmp_path)
    assert result == {"foo": "bar"}


def test_get_expired_returns_none(tmp_path):
    """Expired cache returns None."""
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


class TestVisitedURLs:
    def test_get_visited_empty(self, tmp_path):
        """No file returns empty set."""
        with patch("data.cache._VISITED_FILE", tmp_path / "visited.json"):
            result = get_visited()
            assert result == set()

    def test_save_and_get_visited(self, tmp_path):
        """Save URLs, then retrieve them."""
        visited_file = tmp_path / "visited.json"
        with patch("data.cache._VISITED_FILE", visited_file):
            with patch("data.cache.CACHE_DIR", tmp_path):
                urls = {"http://a.com", "http://b.com", "http://c.com"}
                save_visited(urls)
                result = get_visited()
                assert result == urls

    def test_reset_visited(self, tmp_path):
        """Reset clears file and returns count."""
        visited_file = tmp_path / "visited.json"
        with patch("data.cache._VISITED_FILE", visited_file):
            with patch("data.cache.CACHE_DIR", tmp_path):
                save_visited({"http://a.com", "http://b.com"})
                count = reset_visited()
                assert count == 2
                assert not visited_file.exists()

    def test_reset_visited_no_file(self, tmp_path):
        """Reset with no file returns 0."""
        with patch("data.cache._VISITED_FILE", tmp_path / "nonexistent.json"):
            count = reset_visited()
            assert count == 0

    def test_get_visited_count(self, tmp_path):
        """Count returns number of URLs."""
        visited_file = tmp_path / "visited.json"
        with patch("data.cache._VISITED_FILE", visited_file):
            with patch("data.cache.CACHE_DIR", tmp_path):
                save_visited({"http://a.com", "http://b.com"})
                count = get_visited_count()
                assert count == 2

    def test_get_visited_count_empty(self, tmp_path):
        """Count with no file returns 0."""
        with patch("data.cache._VISITED_FILE", tmp_path / "nonexistent.json"):
            count = get_visited_count()
            assert count == 0

    def test_get_visited_corrupted_file(self, tmp_path):
        """Corrupted file returns empty set."""
        visited_file = tmp_path / "visited.json"
        visited_file.write_text("not valid json {{{")
        with patch("data.cache._VISITED_FILE", visited_file):
            result = get_visited()
            assert result == set()

    def test_save_visited_replaces(self, tmp_path):
        """save_visited replaces previous URLs (not append)."""
        visited_file = tmp_path / "visited.json"
        with patch("data.cache._VISITED_FILE", visited_file):
            with patch("data.cache.CACHE_DIR", tmp_path):
                save_visited({"http://a.com"})
                save_visited({"http://b.com"})
                result = get_visited()
                assert result == {"http://b.com"}