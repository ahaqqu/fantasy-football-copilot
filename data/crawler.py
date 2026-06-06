"""Depth-aware web crawler with deduplication and polite delays."""
import json
import logging
import random
import re
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
    EXCLUDED_URL_PATTERNS,
    DOMAIN_URL_PATTERNS,
    MIN_ARTICLE_YEAR,
)
from data.cache import get_visited, save_visited

logger = logging.getLogger(__name__)

_YEAR_RE = re.compile(r"(?:^|/)(\d{4})(?:/|$)")
# Matches ISO dates: 2018-06-15 or 2018-06-15T10:00:00+00:00
_ISO_DATE_RE = re.compile(r"(?<!\d)(\d{4})-\d{2}-\d{2}(?!\d)")
# Matches visible dates: "June 15, 2018" or "Mar 10, 2019"
_MONTH_DATE_RE = re.compile(
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December"
    r"|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"\s+\d{1,2},?\s+(\d{4})",
    re.IGNORECASE,
)


def _is_old_article_url(url: str) -> bool:
    """Return True if URL path contains a year older than MIN_ARTICLE_YEAR.

    Checks for 4-digit year patterns in the URL path (e.g., /2022/, /2023/).
    Used to pre-filter old article URLs before fetching the page.
    """
    for m in _YEAR_RE.finditer(url):
        year = int(m.group(1))
        if 1900 < year < MIN_ARTICLE_YEAR:
            return True
    return False


def _is_old_content(html: str) -> bool:
    """Return True if the article's publication date is older than MIN_ARTICLE_YEAR.

    Only checks structured publication dates (meta tags, JSON-LD, __NEXT_DATA__),
    NOT dates mentioned in body text, to avoid false positives from articles
    that reference older content.

    Supported sources (checked in order):
      1. article:published_time meta tag — used by most CMS (WordPress, Next.js, etc.)
      2. JSON-LD datePublished/dateCreated — structured data from Yoast, Schema.org
      3. <time datetime="..."> elements — semantic HTML5 date markup
      4. __NEXT_DATA__ post date — Next.js embedded page props
      5. Visible date elements (p.date, span.date) — WordPress theme fallback
    """
    soup = BeautifulSoup(html, "lxml")

    # --- 1. article:published_time meta tag (most reliable, used by WordPress/Yoast) ---
    meta = soup.find("meta", property="article:published_time")
    if meta and meta.get("content"):
        m = _ISO_DATE_RE.search(meta["content"])
        if m and int(m.group(1)) < MIN_ARTICLE_YEAR:
            return True

    # --- 2. JSON-LD datePublished (Schema.org structured data) ---
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            for obj in ([data] if isinstance(data, dict) else data):
                if isinstance(obj, dict):
                    for key in ("datePublished", "dateCreated"):
                        val = obj.get(key, "")
                        m = _ISO_DATE_RE.search(str(val))
                        if m and int(m.group(1)) < MIN_ARTICLE_YEAR:
                            return True
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass

    # --- 3. <time datetime="..."> (HTML5 semantic date element) ---
    for tag in soup.find_all("time", datetime=True):
        m = _ISO_DATE_RE.search(tag["datetime"])
        if m and int(m.group(1)) < MIN_ARTICLE_YEAR:
            return True

    # --- 4. __NEXT_DATA__ post date (Next.js SSG embedded props) ---
    script = soup.find("script", id="__NEXT_DATA__")
    if script and script.string:
        try:
            nd = json.loads(script.string)
            for post in nd.get("props", {}).get("pageProps", {}).get("allPosts", []):
                val = post.get("date", "")
                m = _ISO_DATE_RE.search(str(val))
                if m and int(m.group(1)) < MIN_ARTICLE_YEAR:
                    return True
        except (json.JSONDecodeError, TypeError):
            pass

    # --- 5. Visible date elements (WordPress theme fallback: p.date, span.date) ---
    # Targets only elements with class="date" — not body text that may mention old years.
    # Checks both ISO format (2018-06-15) and visible format (June 15, 2018).
    for tag in soup.find_all(["p", "span", "div"], class_="date"):
        text = tag.get_text()
        m = _ISO_DATE_RE.search(text) or _MONTH_DATE_RE.search(text)
        if m and int(m.group(1)) < MIN_ARTICLE_YEAR:
            return True

    return False


def _extract_next_data_links(html: str, base_url: str) -> list[str]:
    """Extract article links from Next.js __NEXT_DATA__ JSON embedded in HTML.

    Next.js SSG apps embed page data in <script id="__NEXT_DATA__">. This function
    recursively walks the JSON looking for 'slug' fields and constructs full URLs.
    Used to discover article links that aren't in <a> tags (SPA navigation).
    """
    soup = BeautifulSoup(html, "lxml")
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        return []

    try:
        data = json.loads(script.string)
    except (json.JSONDecodeError, TypeError):
        return []

    base_domain = urlparse(base_url).netloc
    base_path = urlparse(base_url).path.rstrip("/")
    links = []

    def _walk(obj: Any) -> None:
        """Recursively walk JSON looking for slug/title/url fields."""
        if isinstance(obj, dict):
            slug = obj.get("slug")
            if isinstance(slug, str) and slug:
                full_url = urljoin(base_url + "/", slug)
                parsed = urlparse(full_url)
                if parsed.netloc == base_domain:
                    clean = parsed._replace(fragment="").geturl()
                    if clean not in links:
                        links.append(clean)
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(data)
    return links


def _is_allowed_url(url: str) -> bool:
    """Return True if URL matches domain-specific path restrictions.

    If the URL's domain has entries in DOMAIN_URL_PATTERNS, the URL must start
    with one of the listed path prefixes. Domains not in the config are unrestricted.
    """
    parsed = urlparse(url)
    allowed_paths = DOMAIN_URL_PATTERNS.get(parsed.netloc)
    if allowed_paths is None:
        return True
    return any(parsed.path.startswith(p) for p in allowed_paths)


def _extract_links(html: str, base_url: str) -> list[str]:
    """Extract all same-domain links from HTML, combining <a> tags and __NEXT_DATA__.

    Merges links from traditional <a href> tags with links discovered from
    Next.js __NEXT_DATA__ JSON. Applies EXCLUDED_URL_PATTERNS, domain-specific
    path restrictions, and old article URL filtering to all discovered links.
    """
    soup = BeautifulSoup(html, "lxml")
    base_domain = urlparse(base_url).netloc
    links = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        if parsed.netloc == base_domain and parsed.scheme in ("http", "https"):
            clean_url = parsed._replace(fragment="").geturl()
            if not _is_allowed_url(clean_url):
                logger.debug("  Excluding (domain path restriction): %s", clean_url[:80])
                continue
            if any(pattern in clean_url for pattern in EXCLUDED_URL_PATTERNS):
                logger.debug("  Excluding (blocked pattern): %s", clean_url[:80])
                continue
            if _is_old_article_url(clean_url):
                logger.debug("  Excluding (old article): %s", clean_url[:80])
                continue
            if clean_url not in links:
                links.append(clean_url)

    next_links = _extract_next_data_links(html, base_url)
    added = 0
    for url in next_links:
        if url not in links:
            if not _is_allowed_url(url):
                continue
            if any(pattern in url for pattern in EXCLUDED_URL_PATTERNS):
                continue
            if _is_old_article_url(url):
                continue
            links.append(url)
            added += 1
    if added:
        logger.debug("  Found %d links from __NEXT_DATA__", added)

    return links


def _is_article_url(url: str) -> bool:
    """Heuristic: is this URL likely an article (not category/tag/page)?

    Classifies URLs by path structure:
      - Skips: /category/, /tag/, /page/, /author/, /search
      - Articles: >= 3 path segments, or 2 segments with long slug (>10 chars),
        or single segment with long slug (>15 chars, for Next.js SSG slugs)
    """
    path = urlparse(url).path
    skip_patterns = ["/category/", "/tag/", "/page/", "/author/", "/search", "?s="]
    if any(p in path.lower() for p in skip_patterns):
        return False
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 3:
        return True
    if len(parts) >= 2 and len(parts[-1]) > 10:
        return True
    if len(parts) == 1 and len(parts[0]) > 15:
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

        if _is_old_content(page["html"]):
            visited.add(url)
            logger.info("  [SKIP] Old article (date < %d): %s", MIN_ARTICLE_YEAR, url[:72])
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
