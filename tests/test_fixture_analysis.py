"""Tests for analysis.fixture_analysis — Fixture Analysis."""
from analysis.fixture_analysis import (
    calculate_attack_rating,
    calculate_defense_rating,
    classify_fixture,
    get_fixture_difficulty,
)


def test_attack_rating_positive():
    """Attack rating should be positive for teams that score."""
    rating = calculate_attack_rating(15, 10)
    assert rating > 0


def test_attack_rating_zero_goals():
    """Zero goals gives low rating."""
    rating = calculate_attack_rating(0, 10)
    assert rating < 0.5


def test_defense_rating_good():
    """Good defense (few conceded) gives high rating."""
    rating = calculate_defense_rating(2, 10)
    assert rating > 0.8


def test_defense_rating_poor():
    """Poor defense (many conceded) gives low rating."""
    rating = calculate_defense_rating(20, 10)
    assert rating < 0.5


def test_classify_fixture_easy():
    """Strong vs weak team = easy for strong."""
    result = classify_fixture("Brazil", "USA")
    assert result["home_difficulty"] in ["easy", "medium"]
    assert result["away_difficulty"] in ["hard", "medium"]


def test_classify_fixture_hard():
    """Any team vs Brazil = hard."""
    result = classify_fixture("USA", "Brazil")
    assert result["home_difficulty"] in ["hard", "medium"]


def test_get_fixture_difficulty():
    """Should return a list of difficulty ratings."""
    fixtures = [
        {"teams": {"home": {"name": "USA"}, "away": {"name": "England"}}},
        {"teams": {"home": {"name": "Brazil"}, "away": {"name": "Serbia"}}},
    ]
    result = get_fixture_difficulty(fixtures, "USA")
    assert isinstance(result, list)
    assert len(result) == 1  # USA only appears in first fixture
