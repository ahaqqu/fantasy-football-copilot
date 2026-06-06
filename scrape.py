"""CLI tool for scraping expert opinions.

Usage:
    python scrape.py              # Scrape (skips previously crawled pages)
    python scrape.py --reset      # Re-crawl everything from scratch
"""
import argparse
import logging
import sys


def main():
    parser = argparse.ArgumentParser(description="Expert opinion scraper")
    parser.add_argument("--reset", action="store_true", help="Re-crawl everything")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stdout,
    )

    if args.reset:
        from data.cache import reset_visited
        n = reset_visited()
        print(f"Cleared {n} visited URLs")

    from data.scraper import scrape_expert_opinions
    result = scrape_expert_opinions(use_cache=True, use_llm=True)
    print(f"\nDone! {len(result.get('raw', []))} articles scraped.")


if __name__ == "__main__":
    main()
