import asyncio

import app.api.main as api
import app.inbound as inbound
from app.messaging.base import MessagingProvider


class _FakeProvider(MessagingProvider):
    name = "whatsapp"

    def __init__(self):
        super().__init__()
        self.texts = []
        self.voices = []

    def validate_config(self):
        return True

    async def send_text(self, to, text):
        self.texts.append((to, text))

    async def send_voice(self, to, ogg_path):
        self.voices.append((to, ogg_path))


def test_reply_and_deliver_text_and_voice(monkeypatch):
    fake = _FakeProvider()
    monkeypatch.setattr(inbound, "all_providers", lambda: {"whatsapp": fake})

    async def _chat(t):
        return f"AI:{t}"

    async def _synth(text, owner_id=None):
        return "/tmp/eios-x.ogg", "fish"

    monkeypatch.setattr(inbound, "chat_reply", _chat)
    monkeypatch.setattr(inbound.voice_service, "synthesize", _synth)
    monkeypatch.setattr(inbound, "cleanup_paths", lambda *a: None)

    reply = asyncio.run(inbound.reply_and_deliver("whatsapp", "user1", "hi"))
    assert reply == "AI:hi"
    assert fake.texts == [("user1", "AI:hi")]
    assert fake.voices == [("user1", "/tmp/eios-x.ogg")]


def test_reply_and_deliver_voice_failure_isolated(monkeypatch):
    fake = _FakeProvider()
    monkeypatch.setattr(inbound, "all_providers", lambda: {"whatsapp": fake})
    monkeypatch.setattr(inbound, "chat_reply", lambda t: _acoro("R"))

    async def _synth_fail(text, owner_id=None):
        raise RuntimeError("voice down")

    monkeypatch.setattr(inbound.voice_service, "synthesize", _synth_fail)
    reply = asyncio.run(inbound.reply_and_deliver("whatsapp", "u", "hi"))
    assert reply == "R"
    assert fake.texts == [("u", "R")]  # text delivered despite voice failure
    assert fake.voices == []


async def _acoro(v):
    return v


def _client(monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.setattr(api, "ensure_schema", lambda: None)
    return TestClient(api.app)


def test_whatsapp_inbound_schedules_reply(monkeypatch):
    seen = []

    async def _record(*a, **k):
        seen.append(a)

    monkeypatch.setattr(api, "reply_and_deliver", _record)
    client = _client(monkeypatch)
    payload = {
        "entry": [
            {"changes": [{"value": {"messages": [
                {"type": "text", "from": "15551234567", "text": {"body": "晚上好"}}
            ]}}]}
        ]
    }
    r = client.post("/webhook/whatsapp", json=payload)
    assert r.status_code == 200
    assert seen and seen[0][0] == "whatsapp" and seen[0][2] == "晚上好"


def test_wechat_inbound_passive_reply(monkeypatch):
    monkeypatch.setattr(api.WeChatOfficialProvider, "verify_webhook", lambda self, *a: True)

    async def _chat(t):
        return "你好回复"

    monkeypatch.setattr(api, "chat_reply", _chat)
    client = _client(monkeypatch)
    xml = (
        "<xml><ToUserName><![CDATA[gh_1]]></ToUserName>"
        "<FromUserName><![CDATA[openid_1]]></FromUserName>"
        "<MsgType><![CDATA[text]]></MsgType>"
        "<Content><![CDATA[你好]]></Content></xml>"
    )
    r = client.post(
        "/webhook/wechat?signature=s&timestamp=t&nonce=n", content=xml
    )
    assert r.status_code == 200
    assert "你好回复" in r.text and "openid_1" in r.text
