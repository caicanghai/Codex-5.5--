import asyncio
import hashlib

import httpx
import pytest

from app.messaging.base import MessagingProvider
from app.messaging.service import MessageRouter
from app.messaging.wechat_official import WeChatOfficialProvider, verify_signature
from app.messaging.wecom import WeComProvider
from app.messaging.whatsapp import WhatsAppProvider, verify_webhook


# ---- config-driven auto-disable ----
def test_providers_disabled_without_config():
    assert WeComProvider().validate_config() is False
    assert WeChatOfficialProvider().validate_config() is False
    assert WhatsAppProvider().validate_config() is False


# ---- WeChat Official webhook signature ----
def test_wechat_signature():
    token, ts, nonce = "tok", "1700000000", "abc123"
    good = hashlib.sha1("".join(sorted([token, ts, nonce])).encode()).hexdigest()
    assert verify_signature(token, good, ts, nonce) is True
    assert verify_signature(token, "deadbeef", ts, nonce) is False


# ---- WhatsApp webhook verification ----
def test_whatsapp_webhook_verify(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "whatsapp_verify_token", "vt")
    assert verify_webhook("subscribe", "vt", "CHAL") == "CHAL"
    assert verify_webhook("subscribe", "wrong", "CHAL") is None


# ---- WeChat Official media send (mock) ----
def test_wechat_official_send_file_mock(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "wechat_official_enabled", True)
    monkeypatch.setattr(settings, "wechat_app_id", "app123")
    monkeypatch.setattr(settings, "wechat_app_secret", "secret123")

    calls = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return httpx.Response(200, json={"access_token": "AT", "expires_in": 7200})
        if request.url.path.endswith("/media/upload"):
            calls["media_uploaded"] = True
            return httpx.Response(200, json={"media_id": "mid-123", "type": "file"})
        if request.url.path.endswith("/message/custom/send"):
            calls["sent"] = True
            return httpx.Response(200, json={"errcode": 0})
        return httpx.Response(404, json={})

    p = WeChatOfficialProvider()
    p._transport = httpx.MockTransport(handler)
    assert p.validate_config() is True
    asyncio.run(p.send_file("user123", "tests/fixtures/test.pdf"))
    assert calls.get("media_uploaded") is True
    assert calls.get("sent") is True


# ---- WeCom mock API (token + send) ----
def test_wecom_send_text_mock(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "wecom_enabled", True)
    monkeypatch.setattr(settings, "wecom_corp_id", "corp")
    monkeypatch.setattr(settings, "wecom_secret", "sec")
    monkeypatch.setattr(settings, "wecom_agent_id", "1000002")
    monkeypatch.setattr(settings, "wecom_target_user", "user1")

    calls = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/gettoken"):
            return httpx.Response(200, json={"errcode": 0, "access_token": "TT", "expires_in": 7200})
        if request.url.path.endswith("/message/send"):
            calls["sent"] = True
            return httpx.Response(200, json={"errcode": 0})
        return httpx.Response(404, json={})

    p = WeComProvider()
    p._transport = httpx.MockTransport(handler)
    assert p.validate_config() is True
    asyncio.run(p.send_text("", "hi"))
    assert calls.get("sent") is True


# ---- WhatsApp send-message mock ----
def test_whatsapp_send_text_mock(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "whatsapp_enabled", True)
    monkeypatch.setattr(settings, "whatsapp_access_token", "tok")
    monkeypatch.setattr(settings, "whatsapp_phone_number_id", "123")
    monkeypatch.setattr(settings, "whatsapp_recipient", "1555")

    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        return httpx.Response(200, json={"messages": [{"id": "wamid.1"}]})

    p = WhatsAppProvider()
    p._transport = httpx.MockTransport(handler)
    asyncio.run(p.send_text("", "hello"))
    assert seen["path"].endswith("/messages")


# ---- MessageRouter: partial failure isolation + no-secret detail ----
class _Good(MessagingProvider):
    name = "good"

    def __init__(self):
        super().__init__()
        self.sent = []

    def validate_config(self):
        return True

    async def send_text(self, to, text):
        self.sent.append(text)


class _Bad(MessagingProvider):
    name = "bad"

    def validate_config(self):
        return True

    async def send_text(self, to, text):
        raise RuntimeError("secret-tok-XYZ")  # detail must NOT leak this


class _FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, k):
        return self.store.get(k)

    def set(self, k, v, ex=None):
        self.store[k] = v


def test_router_partial_failure_and_no_secret(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setattr("app.messaging.service.cache.get_client", lambda: fake)
    good, bad = _Good(), _Bad()
    router = MessageRouter(providers=[good, bad])
    results = asyncio.run(router.broadcast("hello world"))
    by = {r.channel: r for r in results}
    assert by["good"].ok is True
    assert by["bad"].ok is False
    assert "secret-tok-XYZ" not in by["bad"].detail  # only exception type name
    assert by["bad"].detail == "RuntimeError"


def test_router_idempotent_dedup(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setattr("app.messaging.service.cache.get_client", lambda: fake)
    good = _Good()
    router = MessageRouter(providers=[good])
    asyncio.run(router.broadcast("same-text"))
    r2 = asyncio.run(router.broadcast("same-text"))
    assert len(good.sent) == 1  # second send deduped
    assert r2[0].detail == "skipped-duplicate"


# ---- audio conversion ----
def test_to_mp3_conversion():
    import os
    import shutil
    import subprocess
    import tempfile

    from app.messaging.media import to_mp3

    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not installed")
    d = tempfile.mkdtemp()
    src = os.path.join(d, "a.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1", src],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    out = asyncio.run(to_mp3(src))
    assert os.path.getsize(out) > 0
    shutil.rmtree(d, ignore_errors=True)
