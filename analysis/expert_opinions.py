"""Expert opinion analysis — classify mentions by player and country."""
import re
from typing import Any

from data.players_reference import get_all_players, COUNTRY_NAMES


POSITIVE_KEYWORDS = [
    "top pick", "essential", "must-have", "must have", "strong", "best",
    "value", "great", "premium", "captain", "differential", "in-form",
    "form", "score", "goals", "assist", "clean sheet", "recommend",
    "target", "pick", "own", "starting", "key", "star", "favourite",
    "favorite", "bargain", "cheap", "enables", "enable",
]

NEGATIVE_KEYWORDS = [
    "avoid", "overpriced", "risk", "doubt", "bench", "injury",
    "suspended", "dropped", "rotation", "rotation risk", "unfit",
    "ruled out", "misses", "miss", "out", "unavailable",
]

SOURCE_CREDIBILITY = {
    "FantasyFootballScout": {"reliability": "high", "type": "written"},
    "FantasyFootballHub": {"reliability": "high", "type": "data-driven"},
    "AllAboutFPL": {"reliability": "medium", "type": "blog"},
    "FootballCoin": {"reliability": "medium", "type": "predictions"},
}


def _name_variants(full_name: str) -> list[str]:
    """Generate searchable variants for a player name.

    'Lionel Messi' -> ['Lionel Messi', 'Messi', 'Lionel']
    'Virgil van Dijk' -> ['Virgil van Dijk', 'van Dijk', 'Virgil']
    'Vinicius Junior' -> ['Vinicius Junior', 'Vinicius']
    """
    parts = full_name.split()
    variants = [full_name]

    # Last name (most common way to refer to players)
    if len(parts) >= 2:
        # For multi-word last names like "van Dijk" or "de Bruyne"
        # Check if second-to-last is a short preposition
        if len(parts) >= 3 and len(parts[-2]) <= 3:
            last_name = " ".join(parts[-2:])  # "van Dijk"
        else:
            last_name = parts[-1]  # "Messi"
        if last_name != full_name:
            variants.append(last_name)

    # First name
    if len(parts) >= 2 and parts[0] != full_name:
        variants.append(parts[0])

    return list(dict.fromkeys(variants))  # dedupe preserving order


def _sentiment_around(text: str, match_start: int, match_end: int) -> str:
    """Determine sentiment from text context around a match."""
    start = max(0, match_start - 80)
    end = min(len(text), match_end + 80)
    context = text[start:end].lower()

    pos = sum(1 for w in POSITIVE_KEYWORDS if w in context)
    neg = sum(1 for w in NEGATIVE_KEYWORDS if w in context)

    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    return "neutral"


def classify_mentions(opinions: list[dict]) -> dict[str, Any]:
    """Classify scraped opinions by player and country mentions.

    Returns:
        {
            "players": {
                "Lionel Messi": {
                    "country": "Argentina",
                    "mentions": [{"source": "...", "sentiment": "...", "context": "..."}]
                }
            },
            "countries": {
                "Argentina": {
                    "mentions": [{"source": "...", "sentiment": "...", "context": "..."}],
                    "players_mentioned": ["Messi", "Alvarez"]
                }
            }
        }
    """
    players_result: dict[str, dict] = {}
    countries_result: dict[str, dict] = {}

    for opinion in opinions:
        source = opinion["source"]
        content = opinion["content"]
        article_url = opinion.get("url", "#")

        # --- Match players (try all name variants) ---
        all_players = get_all_players()
        for player_name, country in all_players.items():
            for variant in _name_variants(player_name):
                pattern = re.compile(r'\b' + re.escape(variant) + r'\b', re.IGNORECASE)
                match = pattern.search(content)
                if match:
                    sentiment = _sentiment_around(content, match.start(), match.end())
                    ctx_start = max(0, match.start() - 60)
                    ctx_end = min(len(content), match.end() + 60)
                    context_snippet = content[ctx_start:ctx_end].strip()

                    if player_name not in players_result:
                        players_result[player_name] = {"country": country, "mentions": []}
                    players_result[player_name]["mentions"].append({
                        "source": source,
                        "url": article_url,
                        "sentiment": sentiment,
                        "context": context_snippet,
                    })
                    break  # only match once per player per article

        # --- Match countries ---
        for country in COUNTRY_NAMES:
            if len(country) < 3:
                continue
            pattern = re.compile(r'\b' + re.escape(country) + r'\b', re.IGNORECASE)
            match = pattern.search(content)
            if not match:
                continue

            sentiment = _sentiment_around(content, match.start(), match.end())
            ctx_start = max(0, match.start() - 60)
            ctx_end = min(len(content), match.end() + 60)
            context_snippet = content[ctx_start:ctx_end].strip()

            if country not in countries_result:
                countries_result[country] = {"mentions": [], "players_mentioned": []}
            countries_result[country]["mentions"].append({
                "source": source,
                "url": article_url,
                "sentiment": sentiment,
                "context": context_snippet,
            })

    # Add players mentioned per country
    for player_name, data in players_result.items():
        country = data["country"]
        if country in countries_result:
            if player_name not in countries_result[country]["players_mentioned"]:
                countries_result[country]["players_mentioned"].append(player_name)

    return {"players": players_result, "countries": countries_result}


def summarize_expert_opinions(opinions: list[dict]) -> dict[str, Any]:
    """Summarize expert opinions across all sources."""
    sources = list(set(o["source"] for o in opinions))
    return {
        "sources": sources,
        "total_opinions": len(opinions),
        "latest_timestamp": max((o.get("timestamp", 0) for o in opinions), default=0),
    }


def summarize_classified(classified: dict) -> dict[str, Any]:
    """Summarize classified expert opinions into actionable insights.

    Returns:
        {
            "players": {
                "Messi": {
                    "country": "Argentina",
                    "mention_count": 5,
                    "source_count": 3,
                    "sources": ["Scout", "Hub"],
                    "sentiment": {"positive": 4, "neutral": 1, "negative": 0},
                    "verdict": "highly_recommended"
                }
            },
            "countries": {
                "Argentina": {
                    "mention_count": 12,
                    "players_mentioned": ["Messi", "Alvarez"],
                    "sentiment": {"positive": 10, "neutral": 2, "negative": 0},
                    "verdict": "strong_contender"
                }
            },
            "top_players": [...],
            "top_countries": [...]
        }
    """
    players_summary = {}
    countries_summary = {}

    # Summarize players
    for name, data in classified.get("players", {}).items():
        mentions = data.get("mentions", [])
        sources = list(set(m.get("source", "") for m in mentions))
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        for m in mentions:
            s = m.get("sentiment", "neutral")
            sentiment_counts[s] = sentiment_counts.get(s, 0) + 1

        total = len(mentions)
        pos_ratio = sentiment_counts["positive"] / total if total > 0 else 0
        neg_ratio = sentiment_counts["negative"] / total if total > 0 else 0

        if pos_ratio >= 0.7:
            verdict = "highly_recommended"
        elif pos_ratio >= 0.4:
            verdict = "recommended"
        elif neg_ratio >= 0.7:
            verdict = "avoid"
        elif neg_ratio >= 0.4:
            verdict = "risky"
        else:
            verdict = "neutral"

        players_summary[name] = {
            "country": data.get("country", "Unknown"),
            "mention_count": total,
            "source_count": len(sources),
            "sources": sources,
            "sentiment": sentiment_counts,
            "verdict": verdict,
        }

    # Summarize countries
    for name, data in classified.get("countries", {}).items():
        mentions = data.get("mentions", [])
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        for m in mentions:
            s = m.get("sentiment", "neutral")
            sentiment_counts[s] = sentiment_counts.get(s, 0) + 1

        total = len(mentions)
        pos_ratio = sentiment_counts["positive"] / total if total > 0 else 0

        if pos_ratio >= 0.6:
            verdict = "strong_contender"
        elif pos_ratio >= 0.3:
            verdict = "dark_horse"
        else:
            verdict = "underdog"

        countries_summary[name] = {
            "mention_count": total,
            "players_mentioned": data.get("players_mentioned", []),
            "sentiment": sentiment_counts,
            "verdict": verdict,
        }

    # Top players by mention count
    top_players = sorted(
        [{"name": n, **v} for n, v in players_summary.items()],
        key=lambda x: x["mention_count"],
        reverse=True,
    )[:15]

    # Top countries by mention count
    top_countries = sorted(
        [{"name": n, **v} for n, v in countries_summary.items()],
        key=lambda x: x["mention_count"],
        reverse=True,
    )[:15]

    return {
        "players": players_summary,
        "countries": countries_summary,
        "top_players": top_players,
        "top_countries": top_countries,
    }


def get_source_credibility(source_name: str) -> dict[str, str]:
    """Get credibility info for a source."""
    return SOURCE_CREDIBILITY.get(source_name, {"reliability": "unknown", "type": "unknown"})
