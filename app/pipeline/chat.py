"""Plain-text AI chat reply (OpenAI-compatible, e.g. DeepSeek) with fallback."""

from __future__ import annotations

import httpx

from app.config import settings
from app.prompts import (
    CHAT_SYSTEM_PROMPT,
    FALLBACK_AI_UNAVAILABLE,
    FALLBACK_EMPTY_MESSAGE,
    FALLBACK_NO_KEY_PREFIX,
)
from app.runtime import get_model

# Back-compat alias (tests/other modules may import SYSTEM_PROMPT from here).
SYSTEM_PROMPT = CHAT_SYSTEM_PROMPT


async def _try_ai_backend(
    base_url: str, api_key: str, model: str, messages: list, timeout: float = 60.0
) -> str | None:
    """Try one AI backend. Return content on success, None on any failure."""
    if not base_url or not api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.6,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            return content if content else None
    except Exception:
        return None


async def chat_reply(text: str) -> str:
    """Return an AI reply via multi-level failover. Never raises.

    Priority: main AI → fallback1 → fallback2 → fallback3 → offline summary.
    """
    text = (text or "").strip()
    if not text:
        return FALLBACK_EMPTY_MESSAGE

    if settings.ai_api_key:
        messages = []
        if SYSTEM_PROMPT:
            messages.append({"role": "system", "content": SYSTEM_PROMPT})
        messages.append({"role": "user", "content": text[:4000]})

        # Try main AI
        result = await _try_ai_backend(
            settings.ai_base_url, settings.ai_api_key, get_model(), messages
        )
        if result:
            return result

        # Try fallback 1
        if settings.ai_fallback_url and settings.ai_fallback_key:
            result = await _try_ai_backend(
                settings.ai_fallback_url, settings.ai_fallback_key, get_model(), messages
            )
            if result:
                return result

        # Try fallback 2
        if settings.ai_fallback2_url and settings.ai_fallback2_key:
            result = await _try_ai_backend(
                settings.ai_fallback2_url, settings.ai_fallback2_key, get_model(), messages
            )
            if result:
                return result

        # Try fallback 3
        if settings.ai_fallback3_url and settings.ai_fallback3_key:
            result = await _try_ai_backend(
                settings.ai_fallback3_url, settings.ai_fallback3_key, get_model(), messages
            )
            if result:
                return result

        # All backends failed
        return FALLBACK_AI_UNAVAILABLE

    # No AI key configured: still reply (never silent).
    return f"{FALLBACK_NO_KEY_PREFIX}{text[:200]}"
