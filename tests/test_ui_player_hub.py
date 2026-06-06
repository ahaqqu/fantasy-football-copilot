"""Tests for ui.tabs.player_hub — Player Hub Tab."""
from ui.tabs.player_hub import render_player_card, render_comparison_table


SAMPLE_PLAYER = {
    "player": {"id": 1, "name": "Lionel Messi", "age": 38, "position": "Attacker", "photo": ""},
    "statistics": [{"goals": {"total": 10}, "passes": {"key": 25}, "rating": "8.5", "team": {"name": "Argentina"}}],
    "fantasy_points": 80.0,
    "fitness": {"status": "Healthy", "color": "green", "details": "12 appearances"},
}


def test_render_player_card_returns_string():
    result = render_player_card(SAMPLE_PLAYER)
    assert isinstance(result, str)
    assert "Messi" in result


def test_render_comparison_table_returns_string():
    p1 = SAMPLE_PLAYER
    p2 = {
        "player": {"id": 2, "name": "Erling Haaland", "age": 25, "position": "Attacker"},
        "statistics": [{"goals": {"total": 15}, "passes": {"key": 10}, "rating": "8.2"}],
        "fantasy_points": 95.0,
    }
    result = render_comparison_table(p1, p2)
    assert isinstance(result, str)
    assert "Haaland" in result
