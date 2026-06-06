"""LLM-based extraction of player/country mentions from article text.

Supports multiple providers via abstract base class:
- HuggingFace Inference API (free tier)
- Google Gemini API (free tier)
"""
import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any

import requests

from config import (
    LLM_PROVIDER,
    HUGGINGFACE_API_KEY,
    HUGGINGFACE_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
)

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Extract football player mentions and country mentions from this article about FIFA World Cup Fantasy.

For each player mentioned, return their name and country.
For each country mentioned, return the country name and any sentiment (positive/negative/neutral).
Also return the overall sentiment toward each player (positive = recommended, negative = avoid, neutral = just mentioned).

Return ONLY valid JSON, no other text:
{
  "players": [
    {"name": "Player Name", "country": "Country", "sentiment": "positive|negative|neutral", "context": "brief reason"}
  ],
  "countries": [
    {"name": "Country", "sentiment": "positive|negative|neutral", "context": "brief reason"}
  ]
}

Article text:
{article_text}"""


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def extract(self, article_text: str) -> dict[str, Any]:
        """Extract player/country mentions from article text."""
        ...


class HuggingFaceProvider(LLMProvider):
    """HuggingFace Inference API provider (free tier)."""

    def __init__(self, api_key: str = HUGGINGFACE_API_KEY, model: str = HUGGINGFACE_MODEL):
        self.api_key = api_key
        self.model = model
        self.api_url = f"https://api-inference.huggingface.co/models/{model}"

    def extract(self, article_text: str) -> dict[str, Any]:
        prompt = EXTRACTION_PROMPT.format(article_text=article_text[:3000])

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            resp = requests.post(
                self.api_url,
                headers=headers,
                json={"inputs": prompt, "parameters": {"max_new_tokens": 1024}},
                timeout=30,
            )
            resp.raise_for_status()
            output = resp.json()

            # HF returns list of generated texts
            if isinstance(output, list) and len(output) > 0:
                text = output[0].get("generated_text", "")
            elif isinstance(output, dict):
                text = output.get("generated_text", "")
            else:
                text = str(output)

            return self._parse_json(text)
        except Exception as e:
            logger.warning("HuggingFace extraction failed: %s", e)
            return {"players": [], "countries": []}

    def _parse_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from LLM response text."""
        # Try to find JSON in the response
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {"players": [], "countries": []}


class GeminiProvider(LLMProvider):
    """Google Gemini API provider (free tier)."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model: str = GEMINI_MODEL):
        self.api_key = api_key
        self.model = model
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    def extract(self, article_text: str) -> dict[str, Any]:
        prompt = EXTRACTION_PROMPT.format(article_text=article_text[:3000])

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1024,
            },
        }

        try:
            resp = requests.post(self.api_url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return self._parse_json(text)
        except Exception as e:
            logger.warning("Gemini extraction failed: %s", e)
            return {"players": [], "countries": []}

    def _parse_json(self, text: str) -> dict[str, Any]:
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {"players": [], "countries": []}


def get_provider(name: str | None = None) -> LLMProvider:
    """Get LLM provider by name. Defaults to config setting."""
    if name is None:
        name = LLM_PROVIDER

    providers = {
        "huggingface": HuggingFaceProvider,
        "gemini": GeminiProvider,
    }

    cls = providers.get(name)
    if cls is None:
        raise ValueError(f"Unknown LLM provider: {name}. Available: {list(providers.keys())}")
    return cls()


def extract_with_llm(article_text: str, provider: LLMProvider | None = None) -> dict[str, Any]:
    """Extract player/country mentions using LLM."""
    if provider is None:
        provider = get_provider()
    return provider.extract(article_text)
