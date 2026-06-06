# tests/test_scraper_llm.py
"""Tests for LLM-based scraping with batching."""
from unittest.mock import MagicMock
from data.scraper import _build_articles_batch, _classify_with_llm_batched


def test_build_articles_batch_creates_numbered_text():
    """Should create numbered article text for batch processing."""
    articles = [
        {"source": "A", "content": "Messi is great"},
        {"source": "B", "content": "Ronaldo scores"},
    ]
    result = _build_articles_batch(articles)
    assert "---ARTICLE 1---" in result
    assert "Messi is great" in result
    assert "---ARTICLE 2---" in result
    assert "Ronaldo scores" in result


def test_classify_with_llm_batched_returns_structure():
    """Should return players and countries dicts."""
    mock_provider = MagicMock()
    mock_provider.extract_player_names.return_value = {"1": ["Messi"], "2": ["Ronaldo"]}
    mock_provider.extract_countries.return_value = {"1": [{"name": "Argentina", "sentiment": "positive", "context": "..."}]}
    mock_provider.verify_players.return_value = []

    articles = [
        {"source": "A", "content": "Messi is great", "url": "http://a.com"},
        {"source": "B", "content": "Ronaldo scores", "url": "http://b.com"},
    ]
    result = _classify_with_llm_batched(articles, mock_provider)
    assert "players" in result
    assert "countries" in result