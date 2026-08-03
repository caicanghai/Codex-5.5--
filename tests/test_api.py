import app.api.main as api
from app.pipeline.service import ProcessResult


def _client(monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.setattr(api, "ensure_schema", lambda: None)
    return TestClient(api.app)


def test_health_degraded_without_infra(monkeypatch):
    client = _client(monkeypatch)
    r = client.get("/health")
    assert r.status_code == 503


def test_ingest_rejects_bad_scheme(monkeypatch):
    client = _client(monkeypatch)
    r = client.post("/ingest", json={"url": "ftp://nope"})
    assert r.status_code == 400


def test_whatsapp_webhook_verify_endpoint(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "whatsapp_verify_token", "vt")
    client = _client(monkeypatch)
    r = client.get(
        "/webhook/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": "vt", "hub.challenge": "123"},
    )
    assert r.status_code == 200 and r.text == "123"
    r2 = client.get(
        "/webhook/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": "bad", "hub.challenge": "123"},
    )
    assert r2.status_code == 403


def test_wecom_verify_needs_config(monkeypatch):
    """Without callback creds the WeCom endpoint reports unconfigured (503)."""
    from app.config import settings

    monkeypatch.setattr(settings, "wecom_token", "")
    monkeypatch.setattr(settings, "wecom_aes_key", "")
    client = _client(monkeypatch)
    r = client.get("/webhook/wecom", params={"echostr": "x"})
    assert r.status_code == 503


def test_wecom_inbound_decrypts_and_replies(monkeypatch):
    """A valid encrypted WeCom body is decrypted and routed to reply_and_deliver."""
    import base64
    import os

    from app.config import settings
    from app.messaging.wxcrypt import WXBizMsgCrypt, extract_encrypt, message_signature

    key = base64.b64encode(os.urandom(32)).decode()[:43]
    monkeypatch.setattr(settings, "wecom_token", "tok")
    monkeypatch.setattr(settings, "wecom_aes_key", key)
    monkeypatch.setattr(settings, "wecom_corp_id", "corp1")

    captured = {}

    async def fake_reply(channel, sender, text, **kw):
        captured["args"] = (channel, sender, text)
        return text

    monkeypatch.setattr(api, "reply_and_deliver", fake_reply)

    c = WXBizMsgCrypt("tok", key, "corp1")
    inner = "<xml><FromUserName><![CDATA[userA]]></FromUserName>" \
            "<MsgType><![CDATA[text]]></MsgType><Content><![CDATA[hi]]></Content></xml>"
    envelope = c.encrypt_message(inner, nonce="n", timestamp="123")
    encrypt = extract_encrypt(envelope)
    sig = message_signature("tok", "123", "n", encrypt)

    client = _client(monkeypatch)
    r = client.post(
        "/webhook/wecom",
        params={"msg_signature": sig, "timestamp": "123", "nonce": "n"},
        content=envelope,
    )
    assert r.status_code == 200
    assert captured["args"] == ("wecom", "userA", "hi")


def test_ingest_success(monkeypatch):
    async def fake_process(url, persist=True):
        return ProcessResult(id=1, url=url, title="T", summary="S", source="url")

    monkeypatch.setattr(api, "process_url", fake_process)
    client = _client(monkeypatch)
    r = client.post("/ingest", json={"url": "https://example.com/a"})
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "T" and body["summary"] == "S" and body["id"] == 1
