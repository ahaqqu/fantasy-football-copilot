"""Tests for analysis.player_stats — Player Statistics."""
from analysis.player_stats import (
    calculate_fantasy_points,
    rank_players,
    compare_players,
    get_top_players_by_position,
)


SAMPLE_PLAYERS = [
    {
        "player": {"id": 1, "name": "Lionel Messi", "age": 38, "position": "Attacker"},
        "statistics": [{"goals": {"total": 10}, "passes": {"key": 25}, "rating": "8.5"}],
    },
    {
        "player": {"id": 2, "name": "Erling Haaland", "age": 25, "position": "Attacker"},
        "statistics": [{"goals": {"total": 15}, "passes": {"key": 10}, "rating": "8.2"}],
    },
    {
        "player": {"id": 3, "name": "Kevin De Bruyne", "age": 34, "position": "Midfielder"},
        "statistics": [{"goals": {"total": 5}, "passes": {"key": 40}, "rating": "8.8"}],
    },
    {
        "player": {"id": 4, "name": "Virgil van Dijk", "age": 34, "position": "Defender"},
        "statistics": [{"goals": {"total": 2}, "passes": {"key": 5}, "rating": "7.5"}],
    },
    {
        "player": {"id": 5, "name": "Thibaut Courtois", "age": 33, "position": "Goalkeeper"},
        "statistics": [{"goals": {"total": 0}, "passes": {"key": 0}, "rating": "7.0"}],
    },
]


def test_calculate_fantasy_points():
    """Fantasy points = goals*6 + assists*3 + key_passes*0.5 + rating*1"""
    pts = calculate_fantasy_points(SAMPLE_PLAYERS[0])
    assert isinstance(pts, float)
    assert pts > 0


def test_rank_players_returns_sorted():
    ranked = rank_players(SAMPLE_PLAYERS)
    assert isinstance(ranked, list)
    assert len(ranked) == len(SAMPLE_PLAYERS)
    # Should be sorted descending by points
    for i in range(len(ranked) - 1):
        assert ranked[i]["fantasy_points"] >= ranked[i + 1]["fantasy_points"]


def test_compare_players_returns_dict():
    result = compare_players(SAMPLE_PLAYERS[0], SAMPLE_PLAYERS[1])
    assert isinstance(result, dict)
    assert "player1" in result
    assert "player2" in result
    assert "winner" in result


def test_get_top_by_position():
    attackers = get_top_players_by_position(SAMPLE_PLAYERS, "Attacker", top_n=2)
    assert len(attackers) == 2
    for p in attackers:
        assert p["player"]["position"] == "Attacker"
