import asyncio
import os
import tempfile

from app.messaging.base import MessagingProvider
from app.messaging.openclaw import OpenClawProvider
from app.messaging.service import MessageRouter
from tests.mock_openclaw import mock_transport


class _FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, k):
        return self.store.get(k)

    def set(self, k, v, ex=None):
        self.store[k] = v


def _configure(monkeypatch, **over):
    from app.config import settings

    monkeypatch.setattr(settings, "openclaw_enabled", True)
    monkeypatch.setattr(settings, "openclaw_base_url", "https://openclaw.local")
    monkeypatch.setattr(settings, "openclaw_api_key", "k")
    monkeypatch.setattr(settings, "openclaw_target", "wxid_1")
    for k, v in over.items():
        monkeypatch.setattr(settings, k, v)


def test_router_delivers_via_openclaw(monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setattr("app.messaging.service.cache.get_client", lambda: _FakeRedis())
    p = OpenClawProvider()
    p._transport = mock_transport()
    results = asyncio.run(MessageRouter(providers=[p]).broadcast("hi"))
    assert results[0].channel == "openclaw" and results[0].ok is True


def test_router_isolates_openclaw_failure(monkeypatch):
    _configure(monkeypatch, openclaw_retry_attempts=1)
    monkeypatch.setattr("app.messaging.service.cache.get_client", lambda: _FakeRedis())

    class _Good(MessagingProvider):
        name = "good"

        def validate_config(self):
            return True

        async def send_text(self, to, text):
            return None

    bad = OpenClawProvider()
    bad._transport = mock_transport(fail_times=99)  # always fails
    results = asyncio.run(MessageRouter(providers=[bad, _Good()]).broadcast("hi"))
    by = {r.channel: r.ok for r in results}
    assert by["good"] is True and by["openclaw"] is False


def test_voice_pipeline_fish_to_openclaw(monkeypatch):
    """Fish OGG -> platform audio codec (SILK for OpenClaw) -> send (codec mocked)."""
    _configure(monkeypatch)

    class _FakeCodec:
        async def encode(self, src, out=None):
            return src  # skip real ffmpeg encoding in tests

    # Mock the get_provider_codec in the module where it's imported
    monkeypatch.setattr("app.messaging.openclaw.get_provider_codec", lambda _: _FakeCodec())
    p = OpenClawProvider()
    p._transport = mock_transport()

    fd, ogg = tempfile.mkstemp(suffix=".ogg")
    os.write(fd, b"fake-ogg-bytes")
    os.close(fd)
    try:
        asyncio.run(p.send_voice("", ogg))  # uploads media + sends voice via mock
    finally:
        if os.path.exists(ogg):
            os.remove(ogg)
