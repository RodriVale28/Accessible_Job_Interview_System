"""S2-2.1 AI client - owner: Prince Nnadi

ask_json(system, user) sends one chat request to an OpenAI-compatible endpoint
(Google Gemini Flash-Lite by default) and returns the reply parsed as a JSON object.

It returns None on ANY failure and never raises: AI turned off, no key or model set,
rate limit (429), timeout, network error, non-200 reply, or a reply that is not a JSON
object. Callers (grading, role matching, feedback) then use their non-AI fallback.

Only send what a feature needs (question, rubric, answer text, job title...). Never send
names, emails or user ids: the Gemini free tier may use prompts to improve its models.
"""
from __future__ import annotations

import json
import logging
import re

import httpx

from app import config

log = logging.getLogger(__name__)

_FENCE = re.compile(r"^\s*```(?:json|JSON)?\s*(.*?)\s*```\s*$", re.DOTALL)


def ai_available() -> bool:
    """True when the AI is turned on and a key and model are set."""
    return bool(config.AI_ENABLED and config.AI_API_KEY and config.LLM_MODEL)


def _parse_reply(text: str) -> dict | None:
    """Parse the model's reply text as a JSON object (``` fences are stripped)."""
    if not isinstance(text, str):
        return None
    text = text.strip()
    fenced = _FENCE.match(text)
    if fenced:
        text = fenced.group(1)
    try:
        data = json.loads(text)
    except ValueError:
        # Some replies wrap the object in a sentence; try the outermost {...}.
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            return None
        try:
            data = json.loads(text[start:end + 1])
        except ValueError:
            return None
    return data if isinstance(data, dict) else None


def ask_json(system: str, user: str) -> dict | None:
    """Ask the AI for a JSON object. Returns None on any failure; never raises."""
    if not ai_available():
        return None
    try:
        response = httpx.post(
            f"{config.AI_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {config.AI_API_KEY}"},
            json={
                "model": config.LLM_MODEL,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=config.AI_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            # 429 = free-tier rate limit. Log the status only, never the prompt or the key.
            log.warning("AI request failed with status %s", response.status_code)
            return None
        content = response.json()["choices"][0]["message"]["content"]
        return _parse_reply(content)
    except Exception as exc:  # timeout, network, unexpected reply shape: always fall back
        log.warning("AI request failed: %s", type(exc).__name__)
        return None
