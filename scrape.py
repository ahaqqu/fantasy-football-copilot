"""CLI tool for scraping expert opinions.

Usage:
    python scrape.py              # Scrape (skips previously crawled pages)
    python scrape.py --reset      # Re-crawl everything from scratch
    python scrape.py --retry-llm  # Re-run LLM on cached raw articles (no re-crawl)
"""
import argparse
import logging
import sys


def main():
    parser = argparse.ArgumentParser(description="Expert opinion scraper")
    parser.add_argument("--reset", action="store_true", help="Re-crawl everything")
    parser.add_argument("--retry-llm", action="store_true", help="Re-run LLM on cached raw articles")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stdout,
    )

    if args.retry_llm:
        from data.scraper import retry_llm
        result = retry_llm()
        if result:
            print(f"\nDone! {len(result.get('raw', []))} articles re-processed.")
        else:
            print("\nFailed. No raw articles found.")
            sys.exit(1)
        return

    if args.reset:
        from data.cache import reset_visited
        from data.scraper import _RAW_ARTICLES_FILE
        from config import CACHE_DIR
        n = reset_visited()
        # Also clear cached results so scraper re-crawls
        for f in ["expert_opinions.json", "raw_articles.json"]:
            p = CACHE_DIR / f
            if p.exists():
                p.unlink()
        print(f"Cleared {n} visited URLs + cached results")

    from data.scraper import scrape_expert_opinions
    result = scrape_expert_opinions(use_llm=True)
    print(f"\nDone! {len(result.get('raw', []))} articles scraped.")


if __name__ == "__main__":
    main()
