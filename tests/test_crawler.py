"""Tests for data.crawler — Depth-aware web crawler."""
from unittest.mock import patch, MagicMock
from data.crawler import crawl_page, crawl_source, _extract_links, _is_article_url


class TestExtractLinks:
    def test_extracts_same_domain_links(self):
        html = '<a href="/article/2026/06/05/test">Link</a><a href="https://other.com/page">Other</a>'
        links = _extract_links(html, "https://example.com/page")
        assert len(links) == 1
        assert "example.com" in links[0]

    def test_resolves_relative_urls(self):
        html = '<a href="relative-page">Link</a>'
        links = _extract_links(html, "https://example.com/category/")
        assert len(links) == 1
        assert links[0].startswith("https://example.com/")

    def test_strips_fragments(self):
        html = '<a href="/page#section">Link</a>'
        links = _extract_links(html, "https://example.com/")
        assert "#" not in links[0]


class TestIsArticleUrl:
    def test_article_with_date(self):
        assert _is_article_url("https://example.com/2026/06/05/best-picks") is True

    def test_category_url(self):
        assert _is_article_url("https://example.com/category/world-cup") is False

    def test_tag_url(self):
        assert _is_article_url("https://example.com/tag/messi") is False

    def test_page_url(self):
        assert _is_article_url("https://example.com/page/2") is False


class TestCrawlPage:
    @patch("data.crawler.requests.get")
    def test_returns_page_content(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html><body><p>Hello</p></body></html>"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        result = crawl_page("https://example.com/")
        assert result is not None
        assert "Hello" in result["content"]

    @patch("data.crawler.requests.get")
    def test_skips_already_visited(self, mock_get):
        visited = {"https://example.com/"}
        result = crawl_page("https://example.com/", visited)
        assert result is None
        mock_get.assert_not_called()

    @patch("data.crawler.requests.get")
    def test_returns_none_on_error(self, mock_get):
        import requests as req
        mock_get.side_effect = req.ConnectionError("down")
        result = crawl_page("https://example.com/")
        assert result is None
