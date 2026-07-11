"""Thin Redis helper (best-effort cache; never fatal)."""

from __future__ import annotations

import redis

from app.config import settings

_client: redis.Redis | None = None


def get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def ping() -> bool:
    try:
        return bool(get_client().ping())
    except Exception:
        return False
