"""Tests for ui.tabs.fixture_analysis — Fixture Analysis Tab."""
from ui.tabs.fixture_analysis import render_fixture_card, render_difficulty_chart


SAMPLE_FIXTURE = {
    "fixture": {"id": 100, "date": "2026-06-11T18:00:00+00:00"},
    "teams": {"home": {"name": "USA", "logo": ""}, "away": {"name": "England", "logo": ""}},
    "goals": {"home": None, "away": None},
}


def test_render_fixture_card_returns_string():
    result = render_fixture_card(SAMPLE_FIXTURE, home_difficulty="medium", away_difficulty="hard")
    assert isinstance(result, str)
    assert "USA" in result
    assert "England" in result


def test_render_difficulty_chart_returns_fig():
    import plotly.graph_objects as go
    fixtures = [
        {"opponent": "England", "venue": "H", "difficulty": "medium"},
        {"opponent": "Brazil", "venue": "A", "difficulty": "hard"},
    ]
    result = render_difficulty_chart(fixtures)
    assert isinstance(result, go.Figure)
