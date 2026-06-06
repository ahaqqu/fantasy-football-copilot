"""Fixture analysis with attack and defense ratings."""


# FIFA World Cup 2026 qualified teams with approximate strength ratings (0-100)
TEAM_STRENGTH = {
    "Brazil": 88, "France": 87, "England": 86, "Argentina": 85,
    "Spain": 84, "Germany": 83, "Netherlands": 82, "Portugal": 81,
    "Belgium": 80, "Croatia": 79, "Morocco": 78, "USA": 76,
    "Mexico": 74, "Japan": 75, "South Korea": 73, "Senegal": 72,
    "Australia": 70, "Switzerland": 77, "Uruguay": 79, "Ecuador": 71,
    "Serbia": 74, "Canada": 72, "Ghana": 70, "Cameroon": 69,
    "Tunisia": 68, "Iran": 67, "Costa Rica": 66, "Saudi Arabia": 65,
    "Qatar": 64, "New Zealand": 60,
}


def calculate_attack_rating(goals_for: int, games: int) -> float:
    """Calculate attack rating (0-1) based on goals scored per game."""
    if games == 0:
        return 0.0
    gpg = goals_for / games
    # Normalize: 3+ goals per game = 1.0, 0 = 0.0
    return min(gpg / 3.0, 1.0)


def calculate_defense_rating(goals_against: int, games: int) -> float:
    """Calculate defense rating (0-1) based on goals conceded per game. Higher = better."""
    if games == 0:
        return 0.5
    gpg = goals_against / games
    # Invert: 0 conceded = 1.0, 3+ conceded = 0.0
    return max(1.0 - gpg / 3.0, 0.0)


def classify_fixture(home_team: str, away_team: str) -> dict[str, str]:
    """Classify fixture difficulty based on team strength."""
    home_str = TEAM_STRENGTH.get(home_team, 70)
    away_str = TEAM_STRENGTH.get(away_team, 70)
    diff = home_str - away_str

    if diff > 10:
        home_diff = "easy"
        away_diff = "hard"
    elif diff < -10:
        home_diff = "hard"
        away_diff = "easy"
    else:
        home_diff = "medium"
        away_diff = "medium"

    return {"home_difficulty": home_diff, "away_difficulty": away_diff}


def get_fixture_difficulty(fixtures: list[dict], team_name: str) -> list[dict]:
    """Get fixture difficulty for a specific team across all fixtures."""
    results = []
    for fix in fixtures:
        home = fix["teams"]["home"]["name"]
        away = fix["teams"]["away"]["name"]
        if home == team_name or away == team_name:
            classification = classify_fixture(home, away)
            results.append({
                "opponent": away if home == team_name else home,
                "venue": "H" if home == team_name else "A",
                "difficulty": classification["home_difficulty"] if home == team_name else classification["away_difficulty"],
            })
    return results
