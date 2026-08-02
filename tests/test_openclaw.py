import asyncio

import pytest

from app.messaging.openclaw import (
    OpenClawProvider,
    parse_response,
    parse_stream_line,
    serialize_request,
)
from tests.mock_openclaw import mock_transport


def _configure(monkeypatch, **over):
    from app.config import settings

    monkeypatch.setattr(settings, "openclaw_enabled", True)
    monkeypatch.setattr(settings, "openclaw_base_url", "https://openclaw.local")
    monkeypatch.setattr(settings, "openclaw_api_key", "k")
    monkeypatch.setattr(settings, "openclaw_model", "openclaw-weixin")
    monkeypatch.setattr(settings, "openclaw_session", "sess1")
    for k, v in over.items():
        monkeypatch.setattr(settings, k, v)


# ---- serializer ----
def test_serialize_request():
    p = serialize_request("hi", model="m", session="s", stream=True)
    assert p["model"] == "m" and p["stream"] is True
    assert p["messages"][0]["content"] == "hi" and p["session"] == "s"


def test_parse_response_variants():
    assert parse_response({"choices": [{"message": {"content": "x"}}]}) == "x"
    assert parse_response({"reply": "y"}) == "y"
    assert parse_response({"content": "z"}) == "z"
    assert parse_response({}) == ""


def test_parse_stream_line():
    assert parse_stream_line('data: {"choices":[{"delta":{"content":"A"}}]}') == "A"
    assert parse_stream_line("data: [DONE]") == ""      # DONE sentinel
    assert parse_stream_line(": comment") is None
    assert parse_stream_line("data: not-json") is None


# ---- config gating ----
def test_disabled_without_config():
    assert OpenClawProvider().validate_config() is False


# ---- health + chat (mock) ----
def test_healthcheck_ok(monkeypatch):
    _configure(monkeypatch)
    p = OpenClawProvider()
    p._transport = mock_transport()
    assert asyncio.run(p.healthcheck()) is True


def test_chat_non_stream(monkeypatch):
    _configure(monkeypatch)
    p = OpenClawProvider()
    p._transport = mock_transport()
    assert asyncio.run(p.chat("hi")) == "Hello world"


def test_chat_stream(monkeypatch):
    _configure(monkeypatch)
    p = OpenClawProvider()
    p._transport = mock_transport()

    async def collect():
        return "".join([c async for c in p.chat_stream("hi")])

    assert asyncio.run(collect()) == "Hello world"


# ---- retry / reconnect ----
def test_retry_recovers(monkeypatch):
    _configure(monkeypatch, openclaw_retry_attempts=3)
    p = OpenClawProvider()
    p._transport = mock_transport(fail_times=2)  # 2 failures then success
    assert asyncio.run(p.chat("hi")) == "Hello world"


def test_retry_exhausted_raises(monkeypatch):
    from app.messaging.base import MessagingError

    _configure(monkeypatch, openclaw_retry_attempts=2)
    p = OpenClawProvider()
    p._transport = mock_transport(fail_times=5)
    with pytest.raises(MessagingError):
        asyncio.run(p.chat("hi"))


# ---- send text / media (mock) ----
def test_send_text(monkeypatch):
    _configure(monkeypatch, openclaw_target="wxid_1")
    p = OpenClawProvider()
    p._transport = mock_transport()
    asyncio.run(p.send_text("", "hello"))  # no exception = ok


def test_send_image(monkeypatch):
    _configure(monkeypatch, openclaw_target="wxid_1")
    p = OpenClawProvider()
    p._transport = mock_transport()
    asyncio.run(p.send_image("", "tests/fixtures/test.png"))  # no exception = ok


def test_send_file(monkeypatch):
    _configure(monkeypatch, openclaw_target="wxid_1")
    p = OpenClawProvider()
    p._transport = mock_transport()
    asyncio.run(p.send_file("", "tests/fixtures/test.pdf"))  # no exception = ok
