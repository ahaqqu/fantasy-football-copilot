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
from data.cache import get_visited, save_visited

logger = logging.getLogger(__name__)


def _extract_links(html: str, base_url: str) -> list[str]:
    """Extract all same-domain links from HTML."""
    soup = BeautifulSoup(html, "lxml")
    base_domain = urlparse(base_url).netloc
    links = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        if parsed.netloc == base_domain and parsed.scheme in ("http", "https"):
            clean_url = parsed._replace(fragment="").geturl()
            if clean_url not in links:
                links.append(clean_url)

    return links


def _is_article_url(url: str) -> bool:
    """Heuristic: is this URL likely an article (not category/tag/page)?"""
    path = urlparse(url).path
    skip_patterns = ["/category/", "/tag/", "/page/", "/author/", "/search", "?s="]
    if any(p in path.lower() for p in skip_patterns):
        return False
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 3:
        return True
    if len(parts) >= 2 and len(parts[-1]) > 10:
        return True
    return False


def crawl_page(url: str, visited: set[str] | None = None) -> dict[str, Any] | None:
    """Fetch a single page and return its content."""
    if visited is not None and url in visited:
        logger.debug("  Skipping (already visited): %s", url[:80])
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

        logger.debug("  Fetched %d bytes from %s", len(resp.text), url[:80])
        return {
            "url": url,
            "content": content[:8000],
            "html": resp.text,
            "status_code": resp.status_code,
        }
    except requests.ConnectionError as e:
        logger.warning("  [FAIL] Connection error: %s -> %s", url[:60], e)
        return None
    except requests.Timeout:
        logger.warning("  [FAIL] Timeout after %ds: %s", CRAWL_TIMEOUT, url[:60])
        return None
    except requests.HTTPError as e:
        logger.warning("  [FAIL] HTTP %s: %s", e.response.status_code if e.response else "?", url[:60])
        return None
    except requests.RequestException as e:
        logger.warning("  [FAIL] Request error: %s -> %s", url[:60], e)
        return None


def crawl_source(
    start_url: str,
    max_depth: int | None = None,
    max_pages: int | None = None,
) -> list[dict[str, Any]]:
    """Crawl a source starting from a URL, following links up to max_depth."""
    if max_depth is None:
        max_depth = CRAWL_DEPTH
    if max_pages is None:
        max_pages = CRAWL_MAX_PAGES_PER_SOURCE

    domain = urlparse(start_url).netloc
    logger.info("--- Starting crawl: %s (depth=%d, max_pages=%d) ---", domain, max_depth, max_pages)

    # Load persistent visited state
    visited = get_visited()
    previously_visited = len(visited)
    if previously_visited > 0:
        logger.info("  Loaded %d previously visited URLs", previously_visited)

    results: list[dict[str, Any]] = []
    queue: list[tuple[str, int]] = [(start_url, 0)]
    queued: set[str] = {start_url}
    failed = 0
    skipped_new = 0

    while queue and len(results) < max_pages:
        url, depth = queue.pop(0)

        if url in visited:
            skipped_new += 1
            continue
        if depth > max_depth:
            logger.debug("  Skipping (max depth reached): %s", url[:80])
            continue

        # Polite delay
        if results:
            delay = random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX)
            logger.debug("  Waiting %.1fs before next request...", delay)
            time.sleep(delay)

        page = crawl_page(url, visited)
        if page is None:
            failed += 1
            continue

        page["depth"] = depth
        results.append(page)
        logger.info("  [OK] depth=%d page=%d/%d %s", depth, len(results), max_pages, url[:72])

        # Find links for next depth level
        if depth < max_depth:
            links = _extract_links(page["html"], url)
            article_links = [link for link in links if _is_article_url(link)]
            other_links = [link for link in links if not _is_article_url(link)]
            logger.debug("  Found %d links (%d articles, %d other)", len(links), len(article_links), len(other_links))

            for link in article_links:
                if link not in visited and link not in queued:
                    queue.insert(0, (link, depth + 1))
                    queued.add(link)
            for link in other_links:
                if link not in visited and link not in queued:
                    queue.append((link, depth + 1))
                    queued.add(link)

    # Save updated visited state
    save_visited(visited)

    # Summary
    new_urls = len(visited) - previously_visited
    logger.info("--- Crawl complete: %s ---", domain)
    logger.info("  New pages crawled: %d", len(results))
    logger.info("  Failed: %d", failed)
    logger.info("  Skipped (seen before): %d", skipped_new)
    logger.info("  Total visited (all time): %d (+%d new)", len(visited), new_urls)
    logger.info("  Queue remaining: %d", len(queue))

    return results
