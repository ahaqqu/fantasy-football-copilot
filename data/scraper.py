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
    logger.info("=" * 60)
    logger.info("EXPERT SCRAPER STARTED")
    logger.info("  Sources: %d", total_sources)
    logger.info("  LLM: %s", "ON" if use_llm else "OFF")
    logger.info("  Cache: %s", "enabled" if use_cache else "disabled")
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
    total_time = sum(s["time"] for s in source_stats)
    logger.info("  Total time: %.1fs", total_time)
    logger.info("=" * 60)

    return output


def _build_articles_batch(articles: list[dict], max_articles: int = 10) -> str:
    """Build numbered article text for batch LLM processing."""
    parts = []
    for i, article in enumerate(articles[:max_articles], 1):
        parts.append(f"---ARTICLE {i}---\n{article['content'][:2000]}")
    return "\n\n".join(parts)


def _classify_with_llm_batched(articles: list[dict], provider) -> dict[str, Any]:
    """Classify articles using batched LLM calls."""
    all_players: dict[str, dict] = {}
    all_countries: dict[str, dict] = {}

    batch_size = 10
    for start in range(0, len(articles), batch_size):
        batch = articles[start:start + batch_size]
        batch_text = _build_articles_batch(batch)

        logger.info("[LLM] Processing batch %d-%d of %d articles...",
                     start + 1, min(start + batch_size, len(articles)), len(articles))

        # Call 1: Extract players
        players_by_article = provider.extract_player_names(batch_text)
        for article_idx, player_names in players_by_article.items():
            idx = int(article_idx) - 1
            if 0 <= idx < len(batch):
                source = batch[idx]["source"]
                for name in player_names:
                    if name not in all_players:
                        all_players[name] = {"country": "Unknown", "mentions": []}
                    all_players[name]["mentions"].append({"source": source, "sentiment": "neutral", "context": ""})

        logger.info("  [BATCH] Players extracted: %d", len(players_by_article))

        # Call 2: Extract countries
        countries_by_article = provider.extract_countries(batch_text)
        for article_idx, country_list in countries_by_article.items():
            idx = int(article_idx) - 1
            if 0 <= idx < len(batch):
                source = batch[idx]["source"]
                for country_data in country_list:
                    name = country_data.get("name", "")
                    if name:
                        if name not in all_countries:
                            all_countries[name] = {"mentions": [], "players_mentioned": []}
                        all_countries[name]["mentions"].append({
                            "source": source,
                            "sentiment": country_data.get("sentiment", "neutral"),
                            "context": country_data.get("context", ""),
                        })

        logger.info("  [BATCH] Countries extracted: %d", len(countries_by_article))

    # Find unknown players
    from data.learned_store import get_all_players_merged, save_learned_player
    known = get_all_players_merged()
    unknowns = [name for name in all_players if name not in known]

    # Call 3: Verify unknowns
    if unknowns:
        logger.info("[LLM] Verifying %d unknown players...", len(unknowns))
        verified = provider.verify_players(unknowns)
        logger.info("  [VERIFY] Unknowns: %d, Verified: %d", len(unknowns), len(verified))
        for p in verified:
            logger.info("    + %s (%s)", p.get("full_name", "?"), p.get("country", "?"))
        for player in verified:
            name = player.get("full_name", player.get("name", ""))
            country = player.get("country", "Unknown")
            if name and player.get("is_real", False):
                save_learned_player(name, country, "LLM discovery")
                if name in all_players:
                    all_players[name]["country"] = country

    # Link players to countries
    for player_name, data in all_players.items():
        country = data["country"]
        if country in all_countries:
            if player_name not in all_countries[country]["players_mentioned"]:
                all_countries[country]["players_mentioned"].append(player_name)

    return {"players": all_players, "countries": all_countries}


def _classify_with_llm(articles: list[dict]) -> dict[str, Any]:
    """Use LLM to extract player/country mentions from articles."""
    from data.extractor import get_provider
    provider = get_provider()
    return _classify_with_llm_batched(articles, provider)
