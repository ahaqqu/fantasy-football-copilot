"""Tests for data.scraper — Expert Site Scraper."""
from unittest.mock import patch
from data.scraper import scrape_expert_opinions


class TestScrapeExpertOpinions:
    @patch("data.scraper.crawl_source")
    def test_scrape_returns_dict(self, mock_crawl):
        mock_crawl.return_value = [
            {"url": "https://example.com/1", "content": "Expert advice here", "html": "", "depth": 0}
        ]
        result = scrape_expert_opinions(use_cache=False)
        assert isinstance(result, dict)
        assert "raw" in result
        assert "classified" in result
        assert len(result["raw"]) > 0

    @patch("data.scraper.crawl_source")
    def test_scrape_caches_results(self, mock_crawl):
        mock_crawl.return_value = [
            {"url": "https://example.com/1", "content": "Content", "html": "", "depth": 0}
        ]
        result1 = scrape_expert_opinions(use_cache=False)
        result2 = scrape_expert_opinions(use_cache=True)
        assert result1 == result2

    @patch("data.scraper.crawl_source")
    def test_scrape_handles_network_error(self, mock_crawl):
        mock_crawl.side_effect = Exception("Network down")
        result = scrape_expert_opinions(use_cache=False)
        assert isinstance(result, dict)
        assert result["raw"] == []
