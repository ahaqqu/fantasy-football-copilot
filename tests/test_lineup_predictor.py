"""Tests for analysis.lineup_predictor — Lineup Predictor."""
from analysis.lineup_predictor import predict_lineup, calculate_start_probability


SAMPLE_SQUAD = [
    {"player": {"id": 1, "name": "GK1", "position": "Goalkeeper"}, "appearances": {"last_6_months": 10, "starts": 9}},
    {"player": {"id": 2, "name": "DEF1", "position": "Defender"}, "appearances": {"last_6_months": 12, "starts": 11}},
    {"player": {"id": 3, "name": "DEF2", "position": "Defender"}, "appearances": {"last_6_months": 10, "starts": 8}},
    {"player": {"id": 4, "name": "DEF3", "position": "Defender"}, "appearances": {"last_6_months": 12, "starts": 12}},
    {"player": {"id": 5, "name": "DEF4", "position": "Defender"}, "appearances": {"last_6_months": 8, "starts": 5}},
    {"player": {"id": 6, "name": "MID1", "position": "Midfielder"}, "appearances": {"last_6_months": 12, "starts": 12}},
    {"player": {"id": 7, "name": "MID2", "position": "Midfielder"}, "appearances": {"last_6_months": 11, "starts": 10}},
    {"player": {"id": 8, "name": "MID3", "position": "Midfielder"}, "appearances": {"last_6_months": 10, "starts": 9}},
    {"player": {"id": 9, "name": "MID4", "position": "Midfielder"}, "appearances": {"last_6_months": 6, "starts": 4}},
    {"player": {"id": 10, "name": "FWD1", "position": "Attacker"}, "appearances": {"last_6_months": 12, "starts": 12}},
    {"player": {"id": 11, "name": "FWD2", "position": "Attacker"}, "appearances": {"last_6_months": 10, "starts": 8}},
]


def test_calculate_start_probability_high():
    """Player who started most games has high probability."""
    prob = calculate_start_probability(11, 12)
    assert prob > 0.8


def test_calculate_start_probability_low():
    """Player who started few games has low probability."""
    prob = calculate_start_probability(4, 12)
    assert prob < 0.5


def test_calculate_start_probability_zero():
    """Player with 0 appearances has 0 probability."""
    prob = calculate_start_probability(0, 0)
    assert prob == 0.0


def test_predict_lineup_returns_11():
    lineup = predict_lineup(SAMPLE_SQUAD, formation="4-4-2")
    assert isinstance(lineup, list)
    assert len(lineup) == 11


def test_predict_lineup_sorted_by_probability():
    lineup = predict_lineup(SAMPLE_SQUAD, formation="4-4-2")
    for i in range(len(lineup) - 1):
        assert lineup[i]["start_probability"] >= lineup[i + 1]["start_probability"]
