"""Tests for analysis.team_optimizer — Team Optimizer."""
from analysis.team_optimizer import optimize_team, validate_formation, calculate_team_score


SAMPLE_PLAYERS = [
    {"player": {"id": 1, "name": "GK1", "position": "Goalkeeper", "market_value": 5}, "fantasy_points": 50},
    {"player": {"id": 2, "name": "DEF1", "position": "Defender", "market_value": 8}, "fantasy_points": 60},
    {"player": {"id": 3, "name": "DEF2", "position": "Defender", "market_value": 7}, "fantasy_points": 55},
    {"player": {"id": 4, "name": "DEF3", "position": "Defender", "market_value": 6}, "fantasy_points": 50},
    {"player": {"id": 5, "name": "DEF4", "position": "Defender", "market_value": 5}, "fantasy_points": 45},
    {"player": {"id": 6, "name": "MID1", "position": "Midfielder", "market_value": 12}, "fantasy_points": 80},
    {"player": {"id": 7, "name": "MID2", "position": "Midfielder", "market_value": 10}, "fantasy_points": 70},
    {"player": {"id": 8, "name": "MID3", "position": "Midfielder", "market_value": 8}, "fantasy_points": 60},
    {"player": {"id": 9, "name": "MID4", "position": "Midfielder", "market_value": 7}, "fantasy_points": 55},
    {"player": {"id": 10, "name": "FWD1", "position": "Attacker", "market_value": 15}, "fantasy_points": 90},
    {"player": {"id": 11, "name": "FWD2", "position": "Attacker", "market_value": 12}, "fantasy_points": 75},
]


def test_validate_formation_valid():
    assert validate_formation("4-4-2") is True
    assert validate_formation("3-5-2") is True


def test_validate_formation_invalid():
    assert validate_formation("5-6-1") is False  # too many players


def test_calculate_team_score():
    team = SAMPLE_PLAYERS[:11]
    score = calculate_team_score(team)
    assert isinstance(score, float)
    assert score > 0


def test_optimize_team_returns_11():
    result = optimize_team(SAMPLE_PLAYERS, budget=100, formation="4-4-2")
    assert isinstance(result, list)
    assert len(result) == 11


def test_optimize_team_respects_budget():
    result = optimize_team(SAMPLE_PLAYERS, budget=50, formation="4-4-2")
    total_cost = sum(p["player"]["market_value"] for p in result)
    assert total_cost <= 50
