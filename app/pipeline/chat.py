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

# Back-compat alias (tests/other modules may import SYSTEM_PROMPT from here).
SYSTEM_PROMPT = CHAT_SYSTEM_PROMPT


async def chat_reply(text: str) -> str:
    """Return an AI reply to a free-form message. Never raises."""
    text = (text or "").strip()
    if not text:
        return FALLBACK_EMPTY_MESSAGE
    if settings.ai_api_key:
        try:
            messages = []
            if SYSTEM_PROMPT:  # persona removed by default; only sent if configured
                messages.append({"role": "system", "content": SYSTEM_PROMPT})
            messages.append({"role": "user", "content": text[:4000]})
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{settings.ai_base_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.ai_api_key}"},
                    json={
                        "model": settings.ai_model,
                        "messages": messages,
                        "temperature": 0.6,
                    },
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"].strip()
                if content:
                    return content
        except Exception:
            # AI failure must never cause silence — clear temporary fallback.
            return FALLBACK_AI_UNAVAILABLE
    # No AI key configured: still reply (never silent).
    return f"{FALLBACK_NO_KEY_PREFIX}{text[:200]}"
