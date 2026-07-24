import asyncio
from types import SimpleNamespace

from app.bot.main import build_application, on_whoami


def test_whoami_replies_with_sender_id():
    """/whoami must echo back the caller's own numeric id — no owner gate,
    since it only ever reveals the caller's own id (auto-discovery for
    TELEGRAM_OWNER_ID, no third-party bot needed)."""
    sent = {}

    async def fake_reply(text, **kw):
        sent["text"] = text

    update = SimpleNamespace(
        message=SimpleNamespace(reply_text=fake_reply),
        effective_user=SimpleNamespace(id=987654321),
    )
    asyncio.run(on_whoami(update, None))
    assert "987654321" in sent["text"]


def test_build_application_wires_handlers():
    app = build_application("123456:ABCDEF")
    # start, help, whoami, voice_set/status/delete/list/pick/add/remove,
    # speak, channels, channel_status, channel_test, broadcast, sync_on/off,
    # voice-sample, text
    handlers = app.handlers[0]
    assert len(handlers) == 19
    # An error handler must be registered so handler exceptions never go silent.
    assert len(app.error_handlers) >= 1
