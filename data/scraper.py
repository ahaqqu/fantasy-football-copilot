"""Scrape expert opinions using depth-aware crawler + LLM extraction."""
import logging
import time
from typing import Any

from config import EXPERT_SOURCES, LLM_PROVIDER
from data.cache import get_cached, save_to_cache, get_visited_count, reset_visited
from data.crawler import crawl_source
from analysis.expert_opinions import classify_mentions

logger = logging.getLogger(__name__)


def scrape_expert_opinions(
    sources: list[dict] | None = None,
    use_cache: bool = True,
    use_llm: bool = False,
) -> dict[str, Any]:
    """Scrape opinions using depth-aware crawler and classify by player/country."""
    if sources is None:
        sources = EXPERT_SOURCES

    total_sources = len(sources)
    visited_count = get_visited_count()
    logger.info("=" * 60)
    logger.info("EXPERT SCRAPER STARTED")
    logger.info("  Sources: %d", total_sources)
    logger.info("  LLM extraction: %s", "ON" if use_llm else "OFF (keyword matching)")
    logger.info("  Cache: %s", "enabled" if use_cache else "disabled")
    logger.info("  Visited URLs (all time): %d", visited_count)
    logger.info("=" * 60)

    cache_key = "expert_opinions"
    if use_cache:
        cached = get_cached(cache_key)
        if cached is not None:
            logger.info("[CACHE HIT] Returning cached data")
            return cached
        logger.info("[CACHE MISS] Will scrape fresh data")

    all_articles = []
    source_stats = []

    for i, source in enumerate(sources, 1):
        name = source["name"]
        url = source["url"]

        logger.info("")
        logger.info("[%d/%d] %s", i, total_sources, name)
        logger.info("  URL: %s", url)
        start_time = time.time()

        try:
            pages = crawl_source(url)
            elapsed = time.time() - start_time

            for page in pages:
                all_articles.append({
                    "source": name,
                    "content": page["content"],
                    "url": page["url"],
                    "depth": page.get("depth", 0),
                    "timestamp": time.time(),
                })

            stats = {"source": name, "pages": len(pages), "time": elapsed, "ok": True}
            source_stats.append(stats)
            logger.info("  [DONE] %d pages in %.1fs", len(pages), elapsed)

        except Exception as e:
            elapsed = time.time() - start_time
            stats = {"source": name, "pages": 0, "time": elapsed, "ok": False, "error": str(e)}
            source_stats.append(stats)
            logger.error("  [FAIL] %s after %.1fs: %s", name, elapsed, e)

    # Classification
    logger.info("")
    logger.info("-" * 60)
    logger.info("CLASSIFICATION")
    logger.info("  Total articles: %d", len(all_articles))

    if use_llm and all_articles:
        logger.info("  Mode: LLM extraction (provider: %s)", LLM_PROVIDER)
        classified = _classify_with_llm(all_articles)
    else:
        logger.info("  Mode: Keyword matching")
        classified = classify_mentions(all_articles) if all_articles else {"players": {}, "countries": {}}

    n_players = len(classified.get("players", {}))
    n_countries = len(classified.get("countries", {}))
    logger.info("  Players found: %d", n_players)
    logger.info("  Countries found: %d", n_countries)

    # Print player summary
    if n_players > 0:
        logger.info("  Top players:")
        for name, data in list(classified["players"].items())[:10]:
            mentions = len(data.get("mentions", []))
            logger.info("    - %s (%s): %d mentions", name, data.get("country", "?"), mentions)

    # Print country summary
    if n_countries > 0:
        logger.info("  Countries:")
        for name, data in sorted(classified["countries"].items(), key=lambda x: len(x[1].get("mentions", [])), reverse=True):
            mentions = len(data.get("mentions", []))
            logger.info("    - %s: %d mentions", name, mentions)

    # Final summary
    output = {"raw": all_articles, "classified": classified}

    if all_articles:
        save_to_cache(cache_key, output)
        logger.info("  Cached to: data/cache/expert_opinions.json")

    logger.info("")
    logger.info("=" * 60)
    logger.info("EXPERT SCRAPER COMPLETE")
    logger.info("  Sources: %d/%d successful", sum(1 for s in source_stats if s["ok"]), total_sources)
    logger.info("  Total pages: %d", len(all_articles))
    logger.info("  Players: %d | Countries: %d", n_players, n_countries)
    logger.info("  Visited URLs (total): %d", get_visited_count())
    total_time = sum(s["time"] for s in source_stats)
    logger.info("  Total time: %.1fs", total_time)
    logger.info("=" * 60)

    return output


def _classify_with_llm(articles: list[dict]) -> dict[str, Any]:
    """Use LLM to extract player/country mentions from articles."""
    from data.extractor import get_provider

    provider = get_provider()
    all_players: dict[str, dict] = {}
    all_countries: dict[str, dict] = {}
    total = len(articles)
    success = 0
    failed = 0

    logger.info("  LLM processing %d articles...", total)

    for i, article in enumerate(articles, 1):
        source = article["source"]
        url = article.get("url", "?")[:60]

        try:
            result = provider.extract(article["content"])

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

            n_p = len(result.get("players", []))
            n_c = len(result.get("countries", []))
            success += 1
            logger.info("  [%d/%d] OK %s: %d players, %d countries", i, total, source, n_p, n_c)

        except Exception as e:
            failed += 1
            logger.warning("  [%d/%d] FAIL %s: %s", i, total, url, e)

    # Link players to countries
    for player_name, data in all_players.items():
        country = data["country"]
        if country in all_countries:
            if player_name not in all_countries[country]["players_mentioned"]:
                all_countries[country]["players_mentioned"].append(player_name)

    logger.info("  LLM done: %d success, %d failed", success, failed)
    return {"players": all_players, "countries": all_countries}
