"""Runtime-switchable settings (model choice) backed by Redis.

Lets the owner switch which model EIOS asks the AI gateway for — at runtime,
via /model — without editing .env or restarting. The gateway (One API) is
provider-agnostic, so the model string can be any model configured there
(KIMI, DeepSeek, OpenAI, Claude, Gemini, ...). Falls back to settings.ai_model
if Redis is unavailable.
"""

from __future__ import annotations

from app import cache
from app.config import settings

MODEL_KEY = "eios:ai_model"


def get_model() -> str:
    """Current model name: runtime override (Redis) or the configured default."""
    try:
        val = cache.get_client().get(MODEL_KEY)
        if val:
            return val
    except Exception:
        pass
    return settings.ai_model


def set_model(name: str) -> bool:
    """Persist a runtime model override. Returns False if it could not be saved."""
    name = (name or "").strip()
    if not name:
        return False
    try:
        cache.get_client().set(MODEL_KEY, name)
        return True
    except Exception:
        return False


def clear_model() -> None:
    """Drop the override and fall back to settings.ai_model."""
    try:
        cache.get_client().delete(MODEL_KEY)
    except Exception:
        pass
