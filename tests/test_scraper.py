"""Tests for data.scraper — Expert Site Scraper."""
from unittest.mock import patch
from data.scraper import scrape_expert_opinions, _dedup_articles, _consolidate_classified, _content_hash
from analysis.expert_opinions import summarize_classified


class TestDedup:
    def test_content_hash_deterministic(self):
        assert _content_hash("hello") == _content_hash("hello")
        assert _content_hash("hello") != _content_hash("world")

    def test_dedup_by_url(self):
        articles = [
            {"url": "http://a.com", "content": "A"},
            {"url": "http://a.com", "content": "A"},
        ]
        assert len(_dedup_articles(articles)) == 1

    def test_dedup_by_content(self):
        articles = [
            {"url": "http://a.com", "content": "Same content"},
            {"url": "http://b.com", "content": "Same content"},
        ]
        assert len(_dedup_articles(articles)) == 1

    def test_keeps_different_articles(self):
        articles = [
            {"url": "http://a.com", "content": "Article A"},
            {"url": "http://b.com", "content": "Article B"},
        ]
        assert len(_dedup_articles(articles)) == 2

    def test_consolidate_dedup_mentions(self):
        classified = {
            "players": {
                "Messi": {
                    "country": "Argentina",
                    "mentions": [
                        {"source": "Scout", "sentiment": "positive"},
                        {"source": "Scout", "sentiment": "positive"},
                        {"source": "Hub", "sentiment": "neutral"},
                    ],
                }
            },
            "countries": {},
        }
        result = _consolidate_classified(classified)
        assert len(result["players"]["Messi"]["mentions"]) == 2

    def test_consolidate_keeps_different_sources(self):
        classified = {
            "players": {
                "Messi": {
                    "country": "Argentina",
                    "mentions": [
                        {"source": "Scout", "sentiment": "positive"},
                        {"source": "Hub", "sentiment": "positive"},
                    ],
                }
            },
            "countries": {},
        }
        result = _consolidate_classified(classified)
        assert len(result["players"]["Messi"]["mentions"]) == 2


class TestScrapeExpertOpinions:
    @patch("data.scraper._load_raw_articles", return_value=None)
    @patch("data.scraper.crawl_source")
    def test_scrape_returns_dict(self, mock_crawl, mock_load):
        mock_crawl.return_value = [
            {"url": "https://example.com/1", "content": "Expert advice here", "html": "", "depth": 0}
        ]
        result = scrape_expert_opinions()
        assert isinstance(result, dict)
        assert "raw" in result
        assert "classified" in result
        assert "summary" in result
        assert "llm_summary" in result
        assert len(result["raw"]) > 0

    @patch("data.scraper._load_raw_articles", return_value=None)
    @patch("data.scraper.crawl_source")
    def test_scrape_handles_network_error(self, mock_crawl, mock_load):
        mock_crawl.side_effect = Exception("Network down")
        result = scrape_expert_opinions()
        assert isinstance(result, dict)
        assert result["raw"] == []

    @patch("data.scraper._load_raw_articles", return_value=[
        {"url": "https://example.com/old", "content": "Old article", "source": "Test", "depth": 0, "timestamp": 0}
    ])
    @patch("data.scraper.crawl_source")
    def test_scrape_merges_existing_articles(self, mock_crawl, mock_load):
        mock_crawl.return_value = [
            {"url": "https://example.com/new", "content": "New article", "html": "", "depth": 0}
        ]
        result = scrape_expert_opinions()
        urls = [a["url"] for a in result["raw"]]
        assert "https://example.com/old" in urls
        assert "https://example.com/new" in urls

    @patch("data.scraper._load_raw_articles", return_value=[
        {"url": "https://example.com/same", "content": "Existing", "source": "Test", "depth": 0, "timestamp": 0}
    ])
    @patch("data.scraper.crawl_source")
    def test_scrape_deduplicates_urls(self, mock_crawl, mock_load):
        mock_crawl.return_value = [
            {"url": "https://example.com/same", "content": "Duplicate", "html": "", "depth": 0}
        ]
        result = scrape_expert_opinions()
        matching = [a for a in result["raw"] if a["url"] == "https://example.com/same"]
        assert len(matching) == 1


class TestSummarizeClassified:
    def test_summarize_players(self):
        classified = {
            "players": {
                "Messi": {
                    "country": "Argentina",
                    "mentions": [
                        {"source": "Scout", "sentiment": "positive"},
                        {"source": "Hub", "sentiment": "positive"},
                        {"source": "Blog", "sentiment": "positive"},
                    ],
                }
            },
            "countries": {},
        }
        result = summarize_classified(classified)
        assert "Messi" in result["players"]
        assert result["players"]["Messi"]["mention_count"] == 3
        assert result["players"]["Messi"]["source_count"] == 3
        assert result["players"]["Messi"]["verdict"] == "highly_recommended"
        assert len(result["top_players"]) == 1

    def test_summarize_countries(self):
        classified = {
            "players": {},
            "countries": {
                "Argentina": {
                    "mentions": [
                        {"source": "Scout", "sentiment": "positive"},
                        {"source": "Hub", "sentiment": "positive"},
                    ],
                    "players_mentioned": ["Messi"],
                }
            },
        }
        result = summarize_classified(classified)
        assert "Argentina" in result["countries"]
        assert result["countries"]["Argentina"]["mention_count"] == 2
        assert result["countries"]["Argentina"]["verdict"] == "strong_contender"

    def test_top_players_sorted_by_mentions(self):
        classified = {
            "players": {
                "A": {"country": "X", "mentions": [{"source": "S", "sentiment": "positive"}] * 5},
                "B": {"country": "Y", "mentions": [{"source": "S", "sentiment": "positive"}] * 10},
                "C": {"country": "Z", "mentions": [{"source": "S", "sentiment": "positive"}] * 3},
            },
            "countries": {},
        }
        result = summarize_classified(classified)
        assert result["top_players"][0]["name"] == "B"
        assert result["top_players"][1]["name"] == "A"
        assert result["top_players"][2]["name"] == "C"
