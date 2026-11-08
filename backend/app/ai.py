

"""AI JSON client with safe fallback when AI is unavailable."""

import json

import httpx

from app import config


def ask_json(system: str, user: str) -> dict | None:
    """Ask the configured AI model for JSON, or return None on failure."""
    if not config.AI_ENABLED or not config.AI_API_KEY or not config.LLM_MODEL:
        return None

    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.AI_API_KEY}",
                "Content-Type": "application/json",
            },
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
        response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            return None

        content = content.strip()
        if content.startswith("```"):
            lines = content.splitlines()
            if len(lines) < 3 or not lines[-1].strip() == "```":
                return None
            content = "\n".join(lines[1:-1]).strip()

        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None

    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        return None
