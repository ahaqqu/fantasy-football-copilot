"""Scrape expert opinions from fantasy football sites."""
import logging
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

from config import EXPERT_SOURCES
from data.cache import get_cached, save_to_cache

logger = logging.getLogger(__name__)


def parse_expert_content(html: str, source_name: str) -> dict[str, Any]:
    """Parse HTML content from an expert source into structured data."""
    soup = BeautifulSoup(html, "lxml")

    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Get main content text
    body = soup.find("body")
    content = body.get_text(separator="\n", strip=True) if body else soup.get_text(separator="\n", strip=True)

    # Truncate to reasonable length
    content = content[:5000]

    return {
        "source": source_name,
        "content": content,
        "url": "",
        "timestamp": time.time(),
    }


def scrape_expert_opinions(
    sources: list[dict] | None = None,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    """Scrape opinions from all expert sources."""
    if sources is None:
        sources = EXPERT_SOURCES

    cache_key = "expert_opinions"
    if use_cache:
        cached = get_cached(cache_key)
        if cached is not None:
            return cached

    results = []
    for source in sources:
        name = source["name"]
        url = source["url"]
        try:
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            resp.raise_for_status()
            parsed = parse_expert_content(resp.text, name)
            parsed["url"] = url
            results.append(parsed)
            logger.info("Scraped %s successfully", name)
        except requests.RequestException as e:
            logger.warning("Failed to scrape %s: %s", name, e)
        except Exception as e:
            logger.error("Unexpected error scraping %s: %s", name, e)

    if results:
        save_to_cache(cache_key, results)

    return results
