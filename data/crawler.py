"""Depth-aware web crawler with deduplication and polite delays."""
import logging
import random
import time
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import (
    CRAWL_DEPTH,
    CRAWL_DELAY_MIN,
    CRAWL_DELAY_MAX,
    CRAWL_TIMEOUT,
    CRAWL_MAX_PAGES_PER_SOURCE,
    CRAWL_HEADERS,
)

logger = logging.getLogger(__name__)


def _extract_links(html: str, base_url: str) -> list[str]:
    """Extract all same-domain links from HTML."""
    soup = BeautifulSoup(html, "lxml")
    base_domain = urlparse(base_url).netloc
    links = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        # Resolve relative URLs
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        # Only follow same-domain links
        if parsed.netloc == base_domain and parsed.scheme in ("http", "https"):
            # Strip fragments
            clean_url = parsed._replace(fragment="").geturl()
            if clean_url not in links:
                links.append(clean_url)

    return links


def _is_article_url(url: str) -> bool:
    """Heuristic: is this URL likely an article (not category/tag/page)?"""
    path = urlparse(url).path
    # Articles often have dates or slugs with hyphens
    # Skip category, tag, page, author pages
    skip_patterns = ["/category/", "/tag/", "/page/", "/author/", "/search", "?s="]
    if any(p in path.lower() for p in skip_patterns):
        return False
    # Articles usually have a date-like pattern or long slug
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 3:  # e.g. /2026/06/05/article-slug
        return True
    if len(parts) >= 2 and len(parts[-1]) > 10:  # e.g. /blog/article-slug
        return True
    return False


def crawl_page(url: str, visited: set[str] | None = None) -> dict[str, Any] | None:
    """Fetch a single page and return its content."""
    if visited is not None and url in visited:
        return None

    try:
        resp = requests.get(url, headers=CRAWL_HEADERS, timeout=CRAWL_TIMEOUT)
        resp.raise_for_status()
        if visited is not None:
            visited.add(url)

        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        body = soup.find("body")
        content = body.get_text(separator="\n", strip=True) if body else soup.get_text(separator="\n", strip=True)

        return {
            "url": url,
            "content": content[:8000],
            "html": resp.text,
            "status_code": resp.status_code,
        }
    except requests.RequestException as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return None


def crawl_source(
    start_url: str,
    max_depth: int | None = None,
    max_pages: int | None = None,
) -> list[dict[str, Any]]:
    """Crawl a source starting from a URL, following links up to max_depth.

    Returns list of crawled page dicts with url, content, html, depth.
    """
    if max_depth is None:
        max_depth = CRAWL_DEPTH
    if max_pages is None:
        max_pages = CRAWL_MAX_PAGES_PER_SOURCE

    visited: set[str] = set()
    results: list[dict[str, Any]] = []
    # Queue: list of (url, depth)
    queue: list[tuple[str, int]] = [(start_url, 0)]

    while queue and len(results) < max_pages:
        url, depth = queue.pop(0)

        if url in visited:
            continue
        if depth > max_depth:
            continue

        # Polite delay
        if results:
            delay = random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX)
            time.sleep(delay)

        page = crawl_page(url, visited)
        if page is None:
            continue

        page["depth"] = depth
        results.append(page)
        logger.info("Crawled depth=%d %s", depth, url[:80])

        # Find links for next depth level
        if depth < max_depth:
            links = _extract_links(page["html"], url)
            for link in links:
                if link not in visited:
                    # Prefer article-like URLs
                    if _is_article_url(link):
                        queue.insert(0, (link, depth + 1))
                    else:
                        queue.append((link, depth + 1))

    return results
