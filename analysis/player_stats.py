"""Player statistics and ranking analysis."""
from typing import Any


def calculate_fantasy_points(player: dict) -> float:
    """Calculate FIFA Fantasy points for a player."""
    stats = player["statistics"][0] if player["statistics"] else {}
    goals = stats.get("goals", {}).get("total", 0) or 0
    passes_key = stats.get("passes", {}).get("key", 0) or 0
    rating = float(stats.get("rating", 0) or 0)
    return goals * 6 + passes_key * 0.5 + rating


def rank_players(players: list[dict]) -> list[dict]:
    """Rank all players by fantasy points (descending)."""
    for p in players:
        p["fantasy_points"] = calculate_fantasy_points(p)
    return sorted(players, key=lambda x: x["fantasy_points"], reverse=True)


def compare_players(player1: dict, player2: dict) -> dict[str, Any]:
    """Compare two players head-to-head."""
    pts1 = calculate_fantasy_points(player1)
    pts2 = calculate_fantasy_points(player2)

    stats1 = player1["statistics"][0] if player1["statistics"] else {}
    stats2 = player2["statistics"][0] if player2["statistics"] else {}

    return {
        "player1": {
            "name": player1["player"]["name"],
            "position": player1["player"]["position"],
            "fantasy_points": pts1,
            "goals": stats1.get("goals", {}).get("total", 0),
            "rating": float(stats1.get("rating", 0) or 0),
        },
        "player2": {
            "name": player2["player"]["name"],
            "position": player2["player"]["position"],
            "fantasy_points": pts2,
            "goals": stats2.get("goals", {}).get("total", 0),
            "rating": float(stats2.get("rating", 0) or 0),
        },
        "winner": player1["player"]["name"] if pts1 >= pts2 else player2["player"]["name"],
    }


def get_top_players_by_position(
    players: list[dict], position: str, top_n: int = 10
) -> list[dict]:
    """Get top N players for a specific position."""
    filtered = [p for p in players if p["player"]["position"] == position]
    ranked = rank_players(filtered)
    return ranked[:top_n]
