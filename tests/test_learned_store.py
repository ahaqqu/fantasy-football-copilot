"""Tests for learned players storage."""
from data.learned_store import get_learned_players, save_learned_player, get_all_players_merged


def test_get_learned_players_returns_dict(tmp_path):
    """Should return dict with players and stats keys."""
    from data import learned_store
    learned_store._LEARNED_FILE = tmp_path / "learned.json"
    result = get_learned_players()
    assert "players" in result
    assert "stats" in result


def test_save_learned_player_adds_player(tmp_path):
    """Should save a new player to learned JSON."""
    from data import learned_store
    learned_store._LEARNED_FILE = tmp_path / "learned.json"
    save_learned_player("Test Player", "Testland", "TestSource")
    data = get_learned_players()
    assert "Test Player" in data["players"]
    assert data["players"]["Test Player"]["country"] == "Testland"
    assert data["players"]["Test Player"]["source"] == "TestSource"
    assert data["stats"]["total_verified"] == 1


def test_save_learned_player_deduplicates(tmp_path):
    """Should not save the same player twice."""
    from data import learned_store
    learned_store._LEARNED_FILE = tmp_path / "learned.json"
    save_learned_player("Test Player", "Testland", "Source1")
    save_learned_player("Test Player", "Testland", "Source2")
    data = get_learned_players()
    assert data["stats"]["total_verified"] == 1


def test_get_all_players_merged_includes_hardcoded(tmp_path):
    """Should include players from PLAYERS_BY_COUNTRY."""
    from data import learned_store
    learned_store._LEARNED_FILE = tmp_path / "learned.json"
    result = get_all_players_merged()
    assert "Lionel Messi" in result
    assert result["Lionel Messi"] == "Argentina"


def test_get_all_players_merged_includes_learned(tmp_path):
    """Should include learned players."""
    from data import learned_store
    learned_store._LEARNED_FILE = tmp_path / "learned.json"
    save_learned_player("Learned Player", "Learnland", "Source")
    result = get_all_players_merged()
    assert "Learned Player" in result
    assert result["Learned Player"] == "Learnland"
