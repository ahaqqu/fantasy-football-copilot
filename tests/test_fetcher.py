"""Tests for data.fetcher — API Fetcher."""
from unittest.mock import patch, MagicMock
import requests
from data.fetcher import fetch_players, fetch_fixtures, fetch_team_players


class TestFetchPlayers:
    @patch("data.fetcher.requests.get")
    def test_fetch_players_returns_list(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "response": [
                {
                    "player": {"id": 1, "name": "Test Player", "age": 25, "position": "Attacker"},
                    "statistics": [{"team": {"id": 10, "name": "Test Country"}, "goals": {"total": 5}}]
                }
            ]
        }
        mock_get.return_value = mock_resp
        result = fetch_players("test_key", league_id=1, season=2026)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["player"]["name"] == "Test Player"

    @patch("data.fetcher.requests.get")
    def test_fetch_players_api_error_returns_empty(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.json.return_value = {"errors": {"token": "invalid"}}
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
        mock_get.return_value = mock_resp
        result = fetch_players("bad_key", league_id=1, season=2026, use_cache=False)
        assert result == []


class TestFetchFixtures:
    @patch("data.fetcher.requests.get")
    def test_fetch_fixtures_returns_list(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "response": [
                {
                    "fixture": {"id": 100, "date": "2026-06-11T18:00:00+00:00"},
                    "teams": {"home": {"name": "USA"}, "away": {"name": "England"}},
                    "goals": {"home": 1, "away": 2},
                }
            ]
        }
        mock_get.return_value = mock_resp
        result = fetch_fixtures("test_key", league_id=1, season=2026)
        assert isinstance(result, list)
        assert result[0]["teams"]["home"]["name"] == "USA"

    @patch("data.fetcher.requests.get")
    def test_fetch_fixtures_api_error_returns_empty(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.json.return_value = {"errors": {"server": "error"}}
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_get.return_value = mock_resp
        result = fetch_fixtures("bad_key", league_id=1, season=2026, use_cache=False)
        assert result == []


class TestFetchTeamPlayers:
    @patch("data.fetcher.requests.get")
    def test_fetch_team_players_returns_list(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "response": [
                {
                    "player": {"id": 1, "name": "Team Player", "age": 28, "position": "Midfielder"},
                    "statistics": [{"team": {"id": 10, "name": "USA"}, "goals": {"total": 3}}]
                }
            ]
        }
        mock_get.return_value = mock_resp
        result = fetch_team_players("test_key", team_id=10, league_id=1, season=2026)
        assert isinstance(result, list)
        assert result[0]["player"]["name"] == "Team Player"

    @patch("data.fetcher.requests.get")
    def test_fetch_team_players_api_error_returns_empty(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.json.return_value = {"errors": {"forbidden": "access denied"}}
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("403 Forbidden")
        mock_get.return_value = mock_resp
        result = fetch_team_players("bad_key", team_id=10, league_id=1, season=2026, use_cache=False)
        assert result == []
