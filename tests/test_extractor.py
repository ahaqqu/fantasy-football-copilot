"""Tests for LLM extraction methods."""
import json
from unittest.mock import patch, MagicMock
from data.extractor import (
    OpenRouterProvider,
    _parse_json,
)


def test_parse_json_valid():
    """Should parse valid JSON from text."""
    text = 'Here is the result: {"players": ["Messi"]}'
    result = _parse_json(text)
    assert result == {"players": ["Messi"]}


def test_parse_json_invalid():
    """Should return empty dict for invalid JSON."""
    result = _parse_json("no json here")
    assert result == {}


def test_openrouter_provider_init():
    """Should initialize with API key."""
    provider = OpenRouterProvider(api_key="test_key", model="test-model")
    assert provider.api_key == "test_key"
    assert provider.model == "test-model"
