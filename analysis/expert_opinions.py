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


def get_source_credibility(source_name: str) -> dict[str, str]:
    """Get credibility info for a source."""
    return SOURCE_CREDIBILITY.get(source_name, {"reliability": "unknown", "type": "unknown"})
