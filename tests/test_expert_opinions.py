"""Tests for analysis.expert_opinions — Expert Opinions."""
from analysis.expert_opinions import (
    summarize_expert_opinions,
    extract_recommendations,
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
        "content": "De Bruyne essential pick. Budget midfielders like Saka offer value.",
        "url": "https://example.com/2",
        "timestamp": 1000001,
    },
]


def test_summarize_returns_dict():
    result = summarize_expert_opinions(SAMPLE_OPINIONS)
    assert isinstance(result, dict)
    assert "sources" in result
    assert "total_opinions" in result


def test_extract_recommendations():
    recs = extract_recommendations(SAMPLE_OPINIONS)
    assert isinstance(recs, list)
    assert len(recs) > 0
    assert "player_name" in recs[0]
    assert "sentiment" in recs[0]


def test_get_source_credibility():
    cred = get_source_credibility("FantasyFootballScout")
    assert isinstance(cred, dict)
    assert "reliability" in cred
