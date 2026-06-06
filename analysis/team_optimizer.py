"""Team optimizer — select best XI within budget and formation constraints."""


FORMATION_MAP = {
    "4-4-2": {"Goalkeeper": 1, "Defender": 4, "Midfielder": 4, "Attacker": 2},
    "3-5-2": {"Goalkeeper": 1, "Defender": 3, "Midfielder": 5, "Attacker": 2},
    "4-3-3": {"Goalkeeper": 1, "Defender": 4, "Midfielder": 3, "Attacker": 3},
    "5-3-2": {"Goalkeeper": 1, "Defender": 5, "Midfielder": 3, "Attacker": 2},
    "4-2-3-1": {"Goalkeeper": 1, "Defender": 4, "Midfielder": 3, "Attacker": 1},
}


def validate_formation(formation: str) -> bool:
    """Validate that formation has exactly 10 outfield players + 1 GK."""
    if formation not in FORMATION_MAP:
        return False
    slots = FORMATION_MAP[formation]
    return sum(slots.values()) == 11


def calculate_team_score(team: list[dict]) -> float:
    """Calculate total fantasy points for a team."""
    return float(sum(p.get("fantasy_points", 0) for p in team))


def optimize_team(
    players: list[dict],
    budget: float = 100,
    formation: str = "4-4-2",
) -> list[dict]:
    """Select optimal team within budget and formation constraints."""
    if not validate_formation(formation):
        return []

    slots = FORMATION_MAP[formation]
    team = []
    remaining_budget = budget

    for position, count in slots.items():
        position_players = [
            p for p in players
            if p["player"]["position"] == position
        ]
        # Sort by fantasy points descending
        position_players.sort(key=lambda x: x.get("fantasy_points", 0), reverse=True)

        selected = []
        for p in position_players:
            if len(selected) >= count:
                break
            cost = p["player"].get("market_value", 0)
            if cost <= remaining_budget:
                selected.append(p)
                remaining_budget -= cost
        team.extend(selected)

    return team
