"""Scrape expert opinions using depth-aware crawler + LLM extraction."""
import logging
import time
from typing import Any

from config import EXPERT_SOURCES, LLM_PROVIDER
from data.cache import get_cached, save_to_cache
from data.crawler import crawl_source
from analysis.expert_opinions import classify_mentions

logger = logging.getLogger(__name__)


def scrape_expert_opinions(
    sources: list[dict] | None = None,
    use_cache: bool = True,
    use_llm: bool = False,
) -> dict[str, Any]:
    """Scrape opinions using depth-aware crawler and classify by player/country.

    Args:
        sources: List of expert sources to scrape. Defaults to config.
        use_cache: If True, return cached data if available.
        use_llm: If True, use LLM for extraction instead of keyword matching.

    Returns:
        {
            "raw": [...],
            "classified": {"players": {...}, "countries": {...}}
        }
    """
    if sources is None:
        sources = EXPERT_SOURCES

    cache_key = "expert_opinions"
    if use_cache:
        cached = get_cached(cache_key)
        if cached is not None:
            return cached

    all_articles = []

    for source in sources:
        name = source["name"]
        url = source["url"]
        logger.info("Crawling %s from %s", name, url)

        try:
            pages = crawl_source(url)
            for page in pages:
                all_articles.append({
                    "source": name,
                    "content": page["content"],
                    "url": page["url"],
                    "depth": page.get("depth", 0),
                    "timestamp": time.time(),
                })
            logger.info("Crawled %d pages from %s", len(pages), name)
        except Exception as e:
            logger.error("Failed to crawl %s: %s", name, e)

    # Classify mentions
    if use_llm and all_articles:
        classified = _classify_with_llm(all_articles)
    else:
        classified = classify_mentions(all_articles) if all_articles else {"players": {}, "countries": {}}

    output = {"raw": all_articles, "classified": classified}

    if all_articles:
        save_to_cache(cache_key, output)

    return output


def _classify_with_llm(articles: list[dict]) -> dict[str, Any]:
    """Use LLM to extract player/country mentions from articles."""
    from data.extractor import get_provider

    provider = get_provider()
    all_players: dict[str, dict] = {}
    all_countries: dict[str, dict] = {}

    for article in articles:
        try:
            result = provider.extract(article["content"])
            source = article["source"]

            for player in result.get("players", []):
                name = player.get("name", "")
                if not name:
                    continue
                if name not in all_players:
                    all_players[name] = {
                        "country": player.get("country", "Unknown"),
                        "mentions": [],
                    }
                all_players[name]["mentions"].append({
                    "source": source,
                    "sentiment": player.get("sentiment", "neutral"),
                    "context": player.get("context", ""),
                })

            for country_data in result.get("countries", []):
                name = country_data.get("name", "")
                if not name:
                    continue
                if name not in all_countries:
                    all_countries[name] = {"mentions": [], "players_mentioned": []}
                all_countries[name]["mentions"].append({
                    "source": source,
                    "sentiment": country_data.get("sentiment", "neutral"),
                    "context": country_data.get("context", ""),
                })

            logger.info("LLM extracted from %s: %d players, %d countries",
                        source, len(result.get("players", [])), len(result.get("countries", [])))
        except Exception as e:
            logger.warning("LLM extraction failed for %s: %s", article.get("url", ""), e)

    # Link players to countries
    for player_name, data in all_players.items():
        country = data["country"]
        if country in all_countries:
            if player_name not in all_countries[country]["players_mentioned"]:
                all_countries[country]["players_mentioned"].append(player_name)

    return {"players": all_players, "countries": all_countries}
