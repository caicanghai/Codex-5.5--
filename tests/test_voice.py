import asyncio
import os
import tempfile
from types import SimpleNamespace

from app.voice.base import VoiceProvider
from app.voice.service import VoiceService, validate_sample


class _Fake(VoiceProvider):
    def __init__(self, name, healthy=True, ok=True, path="/tmp/eios-x.ogg"):
        self.name = name
        self._healthy = healthy
        self._ok = ok
        self._path = path

    async def healthcheck(self):
        return self._healthy

    async def synthesize(self, text, voice_id=None):
        if not self._ok:
            raise RuntimeError(f"{self.name} boom")
        return self._path


def _svc(fish_ok, eleven_ok, edge_ok):
    svc = VoiceService()
    svc.providers = {
        "fish": _Fake("fish", ok=fish_ok, path="/tmp/fish.ogg"),
        "elevenlabs": _Fake("elevenlabs", ok=eleven_ok, path="/tmp/11l.ogg"),
        "edge": _Fake("edge", ok=edge_ok, path="/tmp/edge.ogg"),
    }
    return svc


def test_fallback_uses_fish_first():
    ogg, name = asyncio.run(_svc(True, True, True).synthesize("hi"))
    assert name == "fish"


def test_fallback_fish_fails_then_elevenlabs():
    ogg, name = asyncio.run(_svc(False, True, True).synthesize("hi"))
    assert name == "elevenlabs"


def test_fallback_to_edge_when_others_fail():
    ogg, name = asyncio.run(_svc(False, False, True).synthesize("hi"))
    assert name == "edge"


def test_validate_sample():
    assert validate_sample(5, 1000) is not None      # too short
    assert validate_sample(200, 1000) is not None     # too long
    assert validate_sample(30, 999 * 1024 * 1024) is not None  # too big
    assert validate_sample(30, 1000) is None          # ok


def test_delete_temporary_files():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    assert os.path.exists(path)
    VoiceProvider.delete_temporary_files(path)
    assert not os.path.exists(path)


def test_owner_authorization(monkeypatch):
    from app.bot import main as bot
    from app.config import settings

    monkeypatch.setattr(settings, "telegram_owner_id", 4242)
    owner = SimpleNamespace(effective_user=SimpleNamespace(id=4242))
    stranger = SimpleNamespace(effective_user=SimpleNamespace(id=1))
    assert bot.is_owner(owner) is True
    assert bot.is_owner(stranger) is False
    monkeypatch.setattr(settings, "telegram_owner_id", 0)
    assert bot.is_owner(owner) is False  # unset owner => nobody authorized


def test_command_routing_registers_handlers():
    from app.bot.main import build_application

    app = build_application("123456:ABCDEF")
    handlers = app.handlers[0]
    assert len(handlers) == 14


def test_sync_toggle(monkeypatch):
    from app.bot import main as bot

    class _R:
        def __init__(self):
            self.v = {}

        def get(self, k):
            return self.v.get(k)

        def set(self, k, val, ex=None):
            self.v[k] = val

    r = _R()
    monkeypatch.setattr("app.bot.main.cache.get_client", lambda: r)
    assert bot.sync_enabled() is False
    bot.set_sync(True)
    assert bot.sync_enabled() is True
    bot.set_sync(False)
    assert bot.sync_enabled() is False
