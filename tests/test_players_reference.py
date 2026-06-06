"""Tests for players reference merge."""
from data.players_reference import get_all_players


def test_get_all_players_returns_dict():
    """Should return a dict of player names to countries."""
    result = get_all_players()
    assert isinstance(result, dict)
    assert len(result) > 0


def test_get_all_players_includes_hardcoded():
    """Should include players from PLAYERS_BY_COUNTRY."""
    result = get_all_players()
    assert "Lionel Messi" in result
    assert "Kylian Mbappe" in result
