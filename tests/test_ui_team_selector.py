"""Tests for ui.tabs.team_selector — Team Selector Tab."""
from ui.tabs.team_selector import render_team_summary, render_formation_display


SAMPLE_TEAM = [
    {"player": {"id": 1, "name": "GK1", "position": "Goalkeeper"}, "fantasy_points": 50, "fitness": {"status": "Healthy", "color": "green"}},
    {"player": {"id": 2, "name": "DEF1", "position": "Defender"}, "fantasy_points": 60, "fitness": {"status": "Healthy", "color": "green"}},
    {"player": {"id": 3, "name": "MID1", "position": "Midfielder"}, "fantasy_points": 70, "fitness": {"status": "Healthy", "color": "green"}},
    {"player": {"id": 4, "name": "FWD1", "position": "Attacker"}, "fantasy_points": 80, "fitness": {"status": "Healthy", "color": "green"}},
]


def test_render_team_summary_returns_string():
    result = render_team_summary(SAMPLE_TEAM)
    assert isinstance(result, str)
    assert "GK1" in result


def test_render_formation_display_returns_string():
    result = render_formation_display(SAMPLE_TEAM)
    assert isinstance(result, str)
    assert "DEF1" in result
