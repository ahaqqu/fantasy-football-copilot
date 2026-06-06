"""Tests for analysis.player_fitness — Player Fitness & Status."""
from analysis.player_fitness import assess_fitness_status, get_fitness_color


def test_assess_fitness_healthy():
    """Healthy player with full appearances."""
    player = {"appearances": {"last_6_months": 12, "injuries": 0, "suspended": False}}
    status = assess_fitness_status(player)
    assert status["status"] == "Healthy"
    assert status["color"] == "green"


def test_assess_fitness_injured():
    """Player with recent injury."""
    player = {"appearances": {"last_6_months": 5, "injuries": 2, "suspended": False}}
    status = assess_fitness_status(player)
    assert status["status"] in ["Injury Risk", "Doubtful"]
    assert status["color"] in ["yellow", "red"]


def test_assess_fitness_suspended():
    """Suspended player."""
    player = {"appearances": {"last_6_months": 10, "injuries": 0, "suspended": True}}
    status = assess_fitness_status(player)
    assert status["status"] == "Suspended"
    assert status["color"] == "red"


def test_get_fitness_color():
    assert get_fitness_color("Healthy") == "green"
    assert get_fitness_color("Suspended") == "red"
    assert get_fitness_color("Doubtful") == "red"
