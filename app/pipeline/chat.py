"""Plain-text AI chat reply (OpenAI-compatible, e.g. DeepSeek) with fallback."""

from __future__ import annotations

import httpx

from app.config import settings

SYSTEM_PROMPT = "You are EIOS, a concise, friendly personal assistant. Reply briefly."


async def chat_reply(text: str) -> str:
    """Return an AI reply to a free-form message. Never raises."""
    text = (text or "").strip()
    if not text:
        return "（空消息）"
    if settings.ai_api_key:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{settings.ai_base_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.ai_api_key}"},
                    json={
                        "model": settings.ai_model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": text[:4000]},
                        ],
                        "temperature": 0.6,
                    },
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"].strip()
                if content:
                    return content
        except Exception:
            # AI failure must never cause silence — clear temporary fallback.
            return "EIOS online. AI provider is temporarily unavailable."
    # No AI key configured: still reply (never silent).
    return f"EIOS online. 收到：{text[:200]}"
