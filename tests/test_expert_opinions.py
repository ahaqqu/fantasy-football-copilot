"""Tests for analysis.expert_opinions — Expert Opinions."""
from analysis.expert_opinions import (
    summarize_expert_opinions,
    classify_mentions,
    get_source_credibility,
)


SAMPLE_OPINIONS = [
    {
        "source": "FantasyFootballScout",
        "content": "Messi is the top pick for captain. Haaland also strong. Avoid defenders from small nations.",
        "url": "https://example.com/1",
        "timestamp": 1000000,
    },
    {
        "source": "FantasyFootballHub",
        "content": "De Bruyne essential pick. Budget midfielders like Saka offer value. France looking strong.",
        "url": "https://example.com/2",
        "timestamp": 1000001,
    },
]


def test_summarize_returns_dict():
    result = summarize_expert_opinions(SAMPLE_OPINIONS)
    assert isinstance(result, dict)
    assert "sources" in result
    assert "total_opinions" in result


def test_classify_mentions_returns_structure():
    result = classify_mentions(SAMPLE_OPINIONS)
    assert isinstance(result, dict)
    assert "players" in result
    assert "countries" in result


def test_classify_mentions_finds_players():
    result = classify_mentions(SAMPLE_OPINIONS)
    players = result["players"]
    assert "Lionel Messi" in players
    assert players["Lionel Messi"]["country"] == "Argentina"
    assert len(players["Lionel Messi"]["mentions"]) > 0


def test_classify_mentions_finds_sentiment():
    result = classify_mentions(SAMPLE_OPINIONS)
    messi = result["players"]["Lionel Messi"]
    sentiments = [m["sentiment"] for m in messi["mentions"]]
    assert "positive" in sentiments


def test_classify_mentions_finds_countries():
    result = classify_mentions(SAMPLE_OPINIONS)
    countries = result["countries"]
    assert "France" in countries


def test_classify_mentions_groups_by_player():
    result = classify_mentions(SAMPLE_OPINIONS)
    # Messi should have mentions from FantasyFootballScout
    messi = result["players"]["Lionel Messi"]
    sources = [m["source"] for m in messi["mentions"]]
    assert "FantasyFootballScout" in sources


def test_get_source_credibility():
    cred = get_source_credibility("FantasyFootballScout")
    assert isinstance(cred, dict)
    assert "reliability" in cred
