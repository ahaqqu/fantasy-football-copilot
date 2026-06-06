"""Integration test for full LLM scraping flow."""
from unittest.mock import patch, MagicMock
from data.scraper import scrape_expert_opinions


def test_full_scrape_discovers_new_player(tmp_path):
    """Should discover and save a new player from articles."""
    from data import learned_store
    learned_store._LEARNED_FILE = tmp_path / "learned.json"

    mock_provider = MagicMock()
    mock_provider.extract_player_names.return_value = {
        "1": ["Khvicha Kvaratskhelia", "Messi"]
    }
    mock_provider.extract_countries.return_value = {
        "1": [{"name": "Georgia", "sentiment": "positive", "context": "..."}]
    }
    mock_provider.verify_players.return_value = [
        {
            "name": "Kvaratskhelia",
            "full_name": "Khvicha Kvaratskhelia",
            "country": "Georgia",
            "is_real": True,
        }
    ]

    articles = [
        {"source": "Test", "content": "Kvaratskhelia is amazing", "url": "http://test.com"}
    ]

    with patch("data.extractor.get_provider", return_value=mock_provider):
        with patch("data.scraper.crawl_source", return_value=articles):
            scrape_expert_opinions(use_cache=False, use_llm=True)

    from data.learned_store import get_learned_players

    learned = get_learned_players()
    assert "Khvicha Kvaratskhelia" in learned["players"]
    assert learned["players"]["Khvicha Kvaratskhelia"]["country"] == "Georgia"
