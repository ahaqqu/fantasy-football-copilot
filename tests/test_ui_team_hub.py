"""Tests for ui.tabs.team_hub — Team Hub Tab."""
from ui.tabs.team_hub import render_squad_list, render_lineup_formation


SAMPLE_SQUAD = [
    {"player": {"id": 1, "name": "GK1", "position": "Goalkeeper"}, "start_probability": 0.9, "fitness": {"status": "Healthy", "color": "green"}},
    {"player": {"id": 2, "name": "DEF1", "position": "Defender"}, "start_probability": 0.85, "fitness": {"status": "Healthy", "color": "green"}},
    {"player": {"id": 3, "name": "MID1", "position": "Midfielder"}, "start_probability": 0.7, "fitness": {"status": "Rotation Risk", "color": "yellow"}},
    {"player": {"id": 4, "name": "FWD1", "position": "Attacker"}, "start_probability": 0.95, "fitness": {"status": "Healthy", "color": "green"}},
]


def test_render_squad_list_returns_string():
    result = render_squad_list(SAMPLE_SQUAD)
    assert isinstance(result, str)
    assert "GK1" in result


def test_render_lineup_formation_returns_string():
    result = render_lineup_formation(SAMPLE_SQUAD[:11] if len(SAMPLE_SQUAD) >= 11 else SAMPLE_SQUAD)
    assert isinstance(result, str)
    assert "GK1" in result
