"""Predict starting lineup based on national team selection history."""
FORMATION_MAP = {
    "4-4-2": {"Goalkeeper": 1, "Defender": 4, "Midfielder": 4, "Attacker": 2},
    "3-5-2": {"Goalkeeper": 1, "Defender": 3, "Midfielder": 5, "Attacker": 2},
    "4-3-3": {"Goalkeeper": 1, "Defender": 4, "Midfielder": 3, "Attacker": 3},
    "5-3-2": {"Goalkeeper": 1, "Defender": 5, "Midfielder": 3, "Attacker": 2},
    "4-2-3-1": {"Goalkeeper": 1, "Defender": 4, "Midfielder": 3, "Attacker": 1},
}


def calculate_start_probability(starts: int, total_games: int) -> float:
    """Calculate probability of starting based on last 6 months history."""
    if total_games == 0:
        return 0.0
    return starts / total_games


def predict_lineup(
    squad: list[dict],
    formation: str = "4-4-2",
) -> list[dict]:
    """Predict starting XI based on formation and start probability."""
    if formation not in FORMATION_MAP:
        return []

    slots = FORMATION_MAP[formation]
    lineup = []

    for position, count in slots.items():
        position_players = [
            p for p in squad
            if p["player"]["position"] == position
        ]
        for p in position_players:
            apps = p.get("appearances", {})
            starts = apps.get("starts", 0)
            total = apps.get("last_6_months", 0)
            p["start_probability"] = calculate_start_probability(starts, total)

        position_players.sort(key=lambda x: x["start_probability"], reverse=True)
        lineup.extend(position_players[:count])

    lineup.sort(key=lambda x: x["start_probability"], reverse=True)
    return lineup
