"""Scrape expert opinions using depth-aware crawler + LLM extraction."""
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

from config import EXPERT_SOURCES, LLM_PROVIDER, SHARED_DIR
from data.cache import save_to_cache
from data.crawler import crawl_source
from analysis.expert_opinions import classify_mentions

logger = logging.getLogger(__name__)

_RAW_ARTICLES_FILE = SHARED_DIR / "raw_articles.json"


def _content_hash(text: str) -> str:
    """Hash article content for deduplication."""
    return hashlib.md5(text.strip().encode("utf-8")).hexdigest()


def _dedup_articles(articles: list[dict]) -> list[dict]:
    """Remove duplicate articles by URL and content hash."""
    seen_urls = set()
    seen_hashes = set()
    deduped = []
    for article in articles:
        url = article["url"]
        content_hash = _content_hash(article.get("content", ""))
        if url in seen_urls or content_hash in seen_hashes:
            continue
        seen_urls.add(url)
        seen_hashes.add(content_hash)
        deduped.append(article)
    return deduped


def _consolidate_classified(classified: dict) -> dict:
    """Dedup mentions per player/country by source name."""
    players = classified.get("players", {})
    countries = classified.get("countries", {})

    for name, data in players.items():
        seen = set()
        unique_mentions = []
        for m in data.get("mentions", []):
            key = (m.get("source", ""), m.get("sentiment", ""))
            if key not in seen:
                seen.add(key)
                unique_mentions.append(m)
        data["mentions"] = unique_mentions

    for name, data in countries.items():
        seen = set()
        unique_mentions = []
        for m in data.get("mentions", []):
            key = (m.get("source", ""), m.get("sentiment", ""))
            if key not in seen:
                seen.add(key)
                unique_mentions.append(m)
        data["mentions"] = unique_mentions

    return classified


def scrape_expert_opinions(
    sources: list[dict] | None = None,
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
    logger.info("=" * 60)

    # Load existing raw articles (if any)
    existing_articles = _load_raw_articles() or []
    logger.info("  Existing articles: %d", len(existing_articles))
    existing_urls = {a["url"] for a in existing_articles}

    new_articles = []
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

            new_count = 0
            for page in pages:
                if page["url"] not in existing_urls:
                    new_articles.append({
                        "source": name,
                        "content": page["content"],
                        "url": page["url"],
                        "depth": page.get("depth", 0),
                        "timestamp": time.time(),
                    })
                    new_count += 1

            stats = {"source": name, "pages": len(pages), "new": new_count, "time": elapsed, "ok": True}
            source_stats.append(stats)
            logger.info("  [DONE] %d pages (%d new) in %.1fs", len(pages), new_count, elapsed)

        except Exception as e:
            elapsed = time.time() - start_time
            stats = {"source": name, "pages": 0, "new": 0, "time": elapsed, "ok": False, "error": str(e)}
            source_stats.append(stats)
            logger.error("  [FAIL] %s after %.1fs: %s", name, elapsed, e)

    # Merge existing + new, then dedup
    all_articles = _dedup_articles(existing_articles + new_articles)
    total_new = len(new_articles)
    deduped_count = len(existing_articles) + len(new_articles) - len(all_articles)
    logger.info("")
    logger.info("-" * 60)
    logger.info("MERGE")
    logger.info("  Existing: %d | New: %d | Deduped: %d | Total: %d", len(existing_articles), total_new, deduped_count, len(all_articles))

    # Save raw articles IMMEDIATELY (before LLM, so they survive termination)
    if all_articles:
        _save_raw_articles(all_articles)
        logger.info("  [SAVE] Raw articles saved to: data/shared/raw_articles.json")

    # Classification
    logger.info("")
    logger.info("-" * 60)
    logger.info("CLASSIFICATION")

    if use_llm and all_articles:
        logger.info("  Mode: LLM extraction (provider: %s)", LLM_PROVIDER)
        classified = _classify_with_llm(all_articles)
    else:
        logger.info("  Mode: Keyword matching")
        classified = classify_mentions(all_articles) if all_articles else {"players": {}, "countries": {}}

    # Consolidate: dedup mentions per source
    classified = _consolidate_classified(classified)

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
    from analysis.expert_opinions import summarize_classified
    summary = summarize_classified(classified)

    # LLM natural language summary
    llm_summary = ""
    if use_llm and classified.get("players"):
        logger.info("")
        logger.info("-" * 60)
        logger.info("LLM SUMMARY")
        llm_summary = _summarize_with_llm(summary)
        if llm_summary:
            logger.info("  %s", llm_summary[:200])

    output = {
        "raw": all_articles,
        "classified": classified,
        "summary": summary,
        "llm_summary": llm_summary,
    }

    if all_articles:
        # Save to shared directory (committed to git)
        _save_json(SHARED_DIR / "expert_opinions.json", output)
        logger.info("")
        logger.info("  FILES SAVED:")
        logger.info("    data/shared/expert_opinions.json  (classified results)")
        logger.info("    data/shared/raw_articles.json     (raw articles for LLM retry)")
        if use_llm:
            logger.info("")
            logger.info("  To review raw articles:")
            logger.info("    cat data/shared/raw_articles.json")
        else:
            logger.info("")
            logger.info("  To run LLM extraction later:")
            logger.info("    python scrape.py --retry-llm")

    logger.info("")
    logger.info("=" * 60)
    logger.info("EXPERT SCRAPER COMPLETE")
    logger.info("  Sources: %d/%d successful", sum(1 for s in source_stats if s["ok"]), total_sources)
    logger.info("  New pages: %d | Total: %d", total_new, len(all_articles))
    logger.info("  Players: %d | Countries: %d", n_players, n_countries)
    total_time = sum(s["time"] for s in source_stats)
    logger.info("  Total time: %.1fs", total_time)
    logger.info("=" * 60)

    return output


def _save_json(path: Path, data: Any) -> None:
    """Save data as JSON file."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("  [SAVE] Failed to save %s: %s", path, e)


def _save_raw_articles(articles: list[dict]) -> None:
    """Save raw articles for LLM retry without re-crawling."""
    _save_json(_RAW_ARTICLES_FILE, articles)
    logger.info("  [RAW] Saved %d articles", len(articles))


def _load_raw_articles() -> list[dict] | None:
    """Load raw articles from shared directory for LLM retry."""
    if not _RAW_ARTICLES_FILE.exists():
        return None
    try:
        with open(_RAW_ARTICLES_FILE, "r", encoding="utf-8") as f:
            articles = json.load(f)
        logger.info("[LOAD] Loaded %d raw articles from %s", len(articles), _RAW_ARTICLES_FILE)
        return articles
    except Exception as e:
        logger.error("[LOAD] Failed to load %s: %s", _RAW_ARTICLES_FILE, e)
        return None


def retry_llm() -> dict[str, Any] | None:
    """Re-run LLM extraction on cached raw articles without re-crawling."""
    logger.info("=" * 60)
    logger.info("LLM RETRY STARTED")
    logger.info("=" * 60)

    articles = _load_raw_articles()
    if not articles:
        logger.error("No raw articles found at: data/shared/raw_articles.json")
        logger.error("Run 'python scrape.py' first to scrape articles.")
        return None

    logger.info("  Source: data/shared/raw_articles.json")
    logger.info("  Articles: %d", len(articles))
    logger.info("  Provider: %s", LLM_PROVIDER)

    classified = _classify_with_llm(articles)

    n_players = len(classified.get("players", {}))
    n_countries = len(classified.get("countries", {}))
    logger.info("  Players found: %d", n_players)
    logger.info("  Countries found: %d", n_countries)

    # Update the cached expert_opinions.json with new classification
    from analysis.expert_opinions import summarize_classified
    summary = summarize_classified(classified)

    # LLM natural language summary
    logger.info("")
    logger.info("-" * 60)
    logger.info("LLM SUMMARY")
    llm_summary = _summarize_with_llm(summary)
    if llm_summary:
        logger.info("  %s", llm_summary[:200])

    output = {
        "raw": articles,
        "classified": classified,
        "summary": summary,
        "llm_summary": llm_summary,
    }
    _save_json(SHARED_DIR / "expert_opinions.json", output)
    logger.info("  Saved to: data/shared/expert_opinions.json")

    logger.info("=" * 60)
    logger.info("LLM RETRY COMPLETE")
    logger.info("  Players: %d | Countries: %d", n_players, n_countries)
    logger.info("=" * 60)

    return output


def _build_articles_batch(articles: list[dict], max_articles: int = 10) -> str:
    """Build numbered article text for batch LLM processing."""
    parts = []
    for i, article in enumerate(articles[:max_articles], 1):
        parts.append(f"---ARTICLE {i}---\n{article['content'][:1000]}")
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
                article_url = batch[idx]["url"]
                for name in player_names:
                    if name not in all_players:
                        all_players[name] = {"country": "Unknown", "mentions": []}
                    all_players[name]["mentions"].append({
                        "source": source,
                        "url": article_url,
                        "sentiment": "neutral",
                        "context": "",
                    })

        logger.info("  [BATCH] Players extracted: %d", len(players_by_article))

        # Call 2: Extract countries
        countries_by_article = provider.extract_countries(batch_text)
        for article_idx, country_list in countries_by_article.items():
            idx = int(article_idx) - 1
            if 0 <= idx < len(batch):
                source = batch[idx]["source"]
                article_url = batch[idx]["url"]
                for country_data in country_list:
                    name = country_data.get("name", "")
                    if name:
                        if name not in all_countries:
                            all_countries[name] = {"mentions": [], "players_mentioned": []}
                        all_countries[name]["mentions"].append({
                            "source": source,
                            "url": article_url,
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


def _summarize_with_llm(summary_data: dict) -> str:
    """Generate natural language summary using LLM."""
    from data.extractor import get_provider
    provider = get_provider()
    if hasattr(provider, "summarize_opinions"):
        return provider.summarize_opinions(summary_data)
    return ""
