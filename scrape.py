"""CLI tool for scraping expert opinions.

Usage:
    python scrape.py                    # Normal scrape (uses cache)
    python scrape.py --no-cache         # Force fresh scrape
    python scrape.py --llm              # Use LLM extraction
    python scrape.py --reset            # Reset visited URLs + force fresh
    python scrape.py --reset-visited    # Reset visited URLs only
    python scrape.py --status           # Show visited URL count
"""
import argparse
import logging
import sys

from data.cache import reset_visited, get_visited_count


def main():
    parser = argparse.ArgumentParser(description="Expert opinion scraper")
    parser.add_argument("--no-cache", action="store_true", help="Ignore cached results")
    parser.add_argument("--llm", action="store_true", help="Use LLM extraction")
    parser.add_argument("--reset", action="store_true", help="Reset visited URLs + force fresh scrape")
    parser.add_argument("--reset-visited", action="store_true", help="Reset visited URLs only")
    parser.add_argument("--status", action="store_true", help="Show visited URL count")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        stream=sys.stdout,
    )

    if args.status:
        count = get_visited_count()
        print(f"Visited URLs: {count}")
        return

    if args.reset_visited:
        count = reset_visited()
        print(f"Reset {count} visited URLs")
        return

    if args.reset:
        count = reset_visited()
        print(f"Reset {count} visited URLs")

    from data.scraper import scrape_expert_opinions

    use_cache = not args.no_cache and not args.reset
    result = scrape_expert_opinions(use_cache=use_cache, use_llm=args.llm)
    print(f"\nDone! {len(result.get('raw', []))} articles scraped.")


if __name__ == "__main__":
    main()
