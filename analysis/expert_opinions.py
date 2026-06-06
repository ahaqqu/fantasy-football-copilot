"""Expert opinion analysis and recommendation extraction."""
import re
from typing import Any


SOURCE_CREDIBILITY = {
    "FantasyFootballScout": {"reliability": "high", "type": "written"},
    "FantasyFootballHub": {"reliability": "high", "type": "data-driven"},
    "AllAboutFPL": {"reliability": "medium", "type": "blog"},
    "RotoWire": {"reliability": "high", "type": "professional"},
    "FootballPredictions": {"reliability": "medium", "type": "predictions"},
}


def summarize_expert_opinions(opinions: list[dict]) -> dict[str, Any]:
    """Summarize expert opinions across all sources."""
    sources = list(set(o["source"] for o in opinions))
    return {
        "sources": sources,
        "total_opinions": len(opinions),
        "latest_timestamp": max((o.get("timestamp", 0) for o in opinions), default=0),
    }


def extract_recommendations(opinions: list[dict]) -> list[dict[str, str]]:
    """Extract player recommendations from expert opinions."""
    recommendations = []
    seen_players = set()

    # Common positive sentiment keywords
    positive = ["top pick", "essential", "must-have", "strong", "best", "value", "great", "premium"]
    negative = ["avoid", "overpriced", "risk", "doubt", "bench"]

    for opinion in opinions:
        content = opinion["content"].lower()
        # Find capitalized words that look like player names
        words = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', opinion["content"])

        for name in words:
            if name in seen_players:
                continue
            seen_players.add(name)

            # Determine sentiment
            name_lower = name.lower()
            # Check context around the name
            idx = content.find(name_lower)
            if idx == -1:
                continue
            context = content[max(0, idx - 50):idx + len(name) + 50]

            sentiment = "neutral"
            if any(w in context for w in positive):
                sentiment = "positive"
            elif any(w in context for w in negative):
                sentiment = "negative"

            recommendations.append({
                "player_name": name,
                "sentiment": sentiment,
                "source": opinion["source"],
                "context": context.strip(),
            })

    return recommendations


def get_source_credibility(source_name: str) -> dict[str, str]:
    """Get credibility info for a source."""
    return SOURCE_CREDIBILITY.get(source_name, {"reliability": "unknown", "type": "unknown"})
