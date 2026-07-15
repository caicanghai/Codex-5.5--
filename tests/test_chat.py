import asyncio

from app.pipeline.chat import chat_reply


def test_chat_reply_offline_fallback(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ai_api_key", "")  # force fallback (no network)
    out = asyncio.run(chat_reply("晚上好"))
    assert "晚上好" in out


def test_chat_reply_empty():
    assert asyncio.run(chat_reply("   ")) == "（空消息）"
