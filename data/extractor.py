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
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODELS,
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


EXTRACT_PLAYERS_PROMPT = """Extract all football player names from these articles. Each article is numbered.

Return ONLY valid JSON:
{{"1": ["Player A", "Player B"], "2": ["Player C"]}}

Articles:
{articles}"""

EXTRACT_COUNTRIES_PROMPT = """Extract country mentions from these articles about FIFA World Cup Fantasy.
Each article is numbered. For each country, return sentiment and brief context.

Return ONLY valid JSON:
{{"1": [{{"name": "Country", "sentiment": "positive|negative|neutral", "context": "brief reason"}}]}}

Articles:
{articles}"""

VERIFY_PLAYERS_PROMPT = """For each player name below, verify:
1. Is this a real professional football player?
2. What is their full name in Latin/English characters? (e.g. "Takefusa Kubo" not "久保建英")
3. What country do they play for (national team)?

Return ONLY valid JSON:
{{"players": [{{"name": "...", "full_name": "...", "country": "...", "is_real": true|false}}]}}

Names to verify: {names}"""

SUMMARY_PROMPT = """Based on these expert opinions about FIFA World Cup Fantasy Football, write a brief summary.

Include:
- Top recommended players and why
- Players to avoid and why
- Top contender countries
- Key insights from experts

Keep it concise (5-8 sentences). Be direct, no fluff.

Expert data:
{data}"""


def _parse_json(text: str) -> dict[str, Any]:
    """Extract JSON from LLM response text."""
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError as e:
            logger.debug("[LLM] JSON parse failed: %s", e)
    return {}


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
        logger.info("[LLM] HuggingFace provider initialized (model=%s, key=%s)",
                     model, "set" if api_key else "NOT SET")

    def extract(self, article_text: str) -> dict[str, Any]:
        prompt = EXTRACTION_PROMPT.format(article_text=article_text[:3000])

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            logger.debug("[LLM] Sending request to HuggingFace (%d chars)...", len(prompt))
            resp = requests.post(
                self.api_url,
                headers=headers,
                json={"inputs": prompt, "parameters": {"max_new_tokens": 1024}},
                timeout=30,
            )

            if resp.status_code == 503:
                logger.warning("[LLM] Model is loading (503). Retry in a few seconds.")
                return {"players": [], "countries": []}

            resp.raise_for_status()
            output = resp.json()

            if isinstance(output, list) and len(output) > 0:
                text = output[0].get("generated_text", "")
            elif isinstance(output, dict):
                text = output.get("generated_text", "")
            else:
                text = str(output)

            result = self._parse_json(text)
            logger.debug("[LLM] Parsed: %d players, %d countries",
                         len(result.get("players", [])), len(result.get("countries", [])))
            return result

        except requests.ConnectionError as e:
            logger.warning("[LLM] Connection failed: %s", e)
            return {"players": [], "countries": []}
        except requests.Timeout:
            logger.warning("[LLM] Request timed out (30s)")
            return {"players": [], "countries": []}
        except Exception as e:
            logger.warning("[LLM] HuggingFace error: %s", e)
            return {"players": [], "countries": []}

    def _parse_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from LLM response text."""
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError as e:
                logger.debug("[LLM] JSON parse failed: %s", e)
        return {"players": [], "countries": []}


class GeminiProvider(LLMProvider):
    """Google Gemini API provider (free tier)."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model: str = GEMINI_MODEL):
        self.api_key = api_key
        self.model = model
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        logger.info("[LLM] Gemini provider initialized (model=%s, key=%s)",
                     model, "set" if api_key else "NOT SET")

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
            logger.debug("[LLM] Sending request to Gemini (%d chars)...", len(prompt))
            resp = requests.post(self.api_url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            result = self._parse_json(text)
            logger.debug("[LLM] Parsed: %d players, %d countries",
                         len(result.get("players", [])), len(result.get("countries", [])))
            return result

        except requests.ConnectionError as e:
            logger.warning("[LLM] Connection failed: %s", e)
            return {"players": [], "countries": []}
        except requests.Timeout:
            logger.warning("[LLM] Request timed out (30s)")
            return {"players": [], "countries": []}
        except Exception as e:
            logger.warning("[LLM] Gemini error: %s", e)
            return {"players": [], "countries": []}

    def _parse_json(self, text: str) -> dict[str, Any]:
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError as e:
                logger.debug("[LLM] JSON parse failed: %s", e)
        return {"players": [], "countries": []}


class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider with model fallback."""

    def __init__(self, api_key: str = OPENROUTER_API_KEY, model: str | None = None, models: list[str] | None = None):
        self.api_key = api_key
        if models:
            self.models = models
            self.model = models[0]
        elif model:
            self.models = [model]
            self.model = model
        else:
            self.models = OPENROUTER_MODELS
            self.model = OPENROUTER_MODELS[0]
        self.base_url = OPENROUTER_BASE_URL
        logger.info("[LLM] OpenRouter provider initialized (models=%s, key=%s)",
                     self.models, "set" if api_key else "NOT SET")

    def _call_with_fallback(self, prompt: str) -> dict[str, Any]:
        """Try each model in order until one succeeds."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 2048,
        }

        for model in self.models:
            try:
                logger.info("[LLM] Trying model: %s", model)
                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json={**payload, "model": model},
                    timeout=60,
                )
                if resp.status_code == 429:
                    logger.warning("[LLM] Rate limited on %s, trying next...", model)
                    continue
                resp.raise_for_status()
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                logger.info("[LLM] Success with model: %s", model)
                return _parse_json(text)
            except requests.Timeout:
                logger.warning("[LLM] Timeout on %s, trying next...", model)
                continue
            except Exception as e:
                logger.warning("[LLM] Error on %s: %s, trying next...", model, e)
                continue

        logger.error("[LLM] All models failed")
        return {}

    def extract(self, article_text: str) -> dict[str, Any]:
        prompt = EXTRACTION_PROMPT.format(article_text=article_text[:3000])
        return self._call_with_fallback(prompt)

    def extract_player_names(self, articles_text: str) -> dict[str, list[str]]:
        """Extract player names from batched articles."""
        prompt = EXTRACT_PLAYERS_PROMPT.format(articles=articles_text)
        return self._call_with_fallback(prompt)

    def extract_countries(self, articles_text: str) -> dict[str, list[dict]]:
        """Extract countries from batched articles."""
        prompt = EXTRACT_COUNTRIES_PROMPT.format(articles=articles_text)
        return self._call_with_fallback(prompt)

    def verify_players(self, names: list[str]) -> list[dict]:
        """Verify if names are real football players."""
        prompt = VERIFY_PLAYERS_PROMPT.format(names=", ".join(names))
        result = self._call_with_fallback(prompt)
        return [p for p in result.get("players", []) if p.get("is_real", False)]

    def summarize_opinions(self, summary_data: dict) -> str:
        """Generate natural language summary of expert opinions."""
        data_text = json.dumps(summary_data, indent=2, ensure_ascii=False)[:4000]
        prompt = SUMMARY_PROMPT.format(data=data_text)
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 512,
        }

        for model in self.models:
            try:
                logger.info("[LLM] Summarizing with model: %s", model)
                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json={**payload, "model": model},
                    timeout=60,
                )
                if resp.status_code == 429:
                    continue
                resp.raise_for_status()
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                logger.info("[LLM] Summary generated (%d chars)", len(text))
                return text.strip()
            except Exception as e:
                logger.warning("[LLM] Summary failed on %s: %s", model, e)
                continue

        logger.error("[LLM] All models failed for summary")
        return ""


def get_provider(name: str | None = None) -> LLMProvider:
    """Get LLM provider by name. Defaults to config setting."""
    if name is None:
        name = LLM_PROVIDER

    providers = {
        "openrouter": OpenRouterProvider,
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
