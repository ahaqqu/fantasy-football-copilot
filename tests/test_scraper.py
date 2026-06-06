"""Tests for data.scraper — Expert Site Scraper."""
from unittest.mock import patch, MagicMock
from data.scraper import scrape_expert_opinions, parse_expert_content


class TestParseExpertContent:
    def test_parse_returns_dict(self):
        html = "<html><body><h1>Best Players</h1><p>Messi is top pick</p></body></html>"
        result = parse_expert_content(html, "TestSource")
        assert isinstance(result, dict)
        assert result["source"] == "TestSource"
        assert "content" in result
        assert "url" in result
        assert "timestamp" in result

    def test_parse_extracts_text(self):
        html = "<html><body><p>Haaland is the best striker for FPL</p></body></html>"
        result = parse_expert_content(html, "TestSource")
        assert "Haaland" in result["content"]

    def test_parse_handles_empty_html(self):
        result = parse_expert_content("", "TestSource")
        assert result["source"] == "TestSource"
        assert isinstance(result["content"], str)


class TestScrapeExpertOpinions:
    @patch("data.scraper.requests.get")
    def test_scrape_returns_list(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html><body><p>Expert advice here</p></body></html>"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        result = scrape_expert_opinions(use_cache=False)
        assert isinstance(result, list)
        assert len(result) > 0

    @patch("data.scraper.requests.get")
    def test_scrape_caches_results(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html><body><p>Content</p></body></html>"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        # First call hits network
        result1 = scrape_expert_opinions(use_cache=False)
        # Second call should use cache
        result2 = scrape_expert_opinions(use_cache=True)
        assert result1 == result2

    @patch("data.scraper.requests.get")
    def test_scrape_handles_network_error(self, mock_get):
        import requests as req
        mock_get.side_effect = req.ConnectionError("Network down")
        result = scrape_expert_opinions(use_cache=False)
        assert isinstance(result, list)
        # Should return empty list on error, not crash
