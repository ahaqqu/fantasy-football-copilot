"""Tests for data.scraper — Expert Site Scraper."""
from unittest.mock import patch, MagicMock
from data.scraper import scrape_expert_opinions, retry_llm, _dedup_articles, _consolidate_classified, _content_hash, _save_json, _load_raw_articles
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

    def test_consolidate_dedup_countries(self):
        classified = {
            "players": {},
            "countries": {
                "Brazil": {
                    "mentions": [
                        {"source": "Scout", "sentiment": "positive"},
                        {"source": "Scout", "sentiment": "positive"},
                    ],
                    "players_mentioned": ["Neymar"],
                }
            },
        }
        result = _consolidate_classified(classified)
        assert len(result["countries"]["Brazil"]["mentions"]) == 1

    def test_consolidate_empty(self):
        classified = {"players": {}, "countries": {}}
        result = _consolidate_classified(classified)
        assert result == {"players": {}, "countries": {}}

    def test_consolidate_different_sentiment_same_source(self):
        classified = {
            "players": {
                "Messi": {
                    "country": "Argentina",
                    "mentions": [
                        {"source": "Scout", "sentiment": "positive"},
                        {"source": "Scout", "sentiment": "negative"},
                    ],
                }
            },
            "countries": {},
        }
        result = _consolidate_classified(classified)
        # Different sentiment from same source should be kept
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

    def test_summarize_empty(self):
        classified = {"players": {}, "countries": {}}
        result = summarize_classified(classified)
        assert result["top_players"] == []
        assert result["top_countries"] == []


class TestRetryLLM:
    def test_retry_llm_no_articles(self):
        """Retry with no articles returns None."""
        with patch("data.scraper._load_raw_articles", return_value=None):
            result = retry_llm()
            assert result is None

    @patch("data.scraper._summarize_with_llm", return_value="Summary text")
    @patch("data.scraper._classify_with_llm", return_value={"players": {}, "countries": {}})
    @patch("data.scraper._load_raw_articles", return_value=[{"url": "http://a.com", "content": "Test"}])
    def test_retry_llm_success(self, mock_load, mock_classify, mock_summary):
        """Retry with articles processes and returns result."""
        result = retry_llm()
        assert result is not None
        assert "raw" in result
        assert "classified" in result
        assert "summary" in result
        assert "llm_summary" in result
        assert result["llm_summary"] == "Summary text"


class TestSaveJson:
    def test_save_json_creates_file(self, tmp_path):
        """_save_json creates JSON file."""
        from pathlib import Path
        test_file = tmp_path / "test.json"
        _save_json(test_file, {"key": "value"})
        assert test_file.exists()
        with open(test_file) as f:
            import json
            data = json.load(f)
        assert data == {"key": "value"}
