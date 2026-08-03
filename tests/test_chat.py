import asyncio

from app.pipeline.chat import chat_reply


def test_chat_reply_offline_fallback(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ai_api_key", "")  # force fallback (no network)
    out = asyncio.run(chat_reply("晚上好"))
    assert "晚上好" in out


def test_chat_reply_empty():
    assert asyncio.run(chat_reply("   ")) == "（空消息）"


def test_chat_reply_ai_failure_fallback(monkeypatch):
    from app.config import settings
    from app.pipeline import chat as chatmod

    monkeypatch.setattr(settings, "ai_api_key", "k")

    class _Boom:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **k):
            raise RuntimeError("ai down")

    monkeypatch.setattr(chatmod.httpx, "AsyncClient", _Boom)
    out = asyncio.run(chat_reply("你好"))
    assert out == "EIOS online. AI provider is temporarily unavailable."
