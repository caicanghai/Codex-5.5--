"""Dispatch brain: classification + workflow routing + safe fallback."""

import asyncio

from app import dispatch


def test_classify_chat_by_default(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "n8n_base_url", "")
    monkeypatch.setattr(settings, "n8n_workflows", "")
    assert dispatch.classify("晚上好") == "chat"


def test_classify_summarize_on_url():
    assert dispatch.classify("https://example.com/article") == "summarize"


def test_classify_workflow_on_keyword(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "n8n_base_url", "http://n8n:5678")
    monkeypatch.setattr(settings, "n8n_workflows", "提醒=remind;天气=weather")
    assert dispatch.classify("提醒我明天开会") == "workflow"
    assert dispatch.match_workflow("提醒我明天开会") == ("提醒", "remind")
    assert dispatch.match_workflow("随便聊聊") is None


def test_workflow_map_parsing(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "n8n_workflows", " 提醒=/remind/ ; 天气 = weather ; bad ")
    assert dispatch.workflow_map() == {"提醒": "remind", "天气": "weather"}


def test_dispatch_routes_to_workflow(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "n8n_base_url", "http://n8n:5678")
    monkeypatch.setattr(settings, "n8n_workflows", "下单=order")

    captured = {}

    class _Resp:
        status_code = 200

        def raise_for_status(self):
            pass

        @property
        def text(self):
            return '{"reply": "订单已创建"}'

        def json(self):
            return {"reply": "订单已创建"}

    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json):
            captured["url"] = url
            captured["json"] = json
            return _Resp()

    monkeypatch.setattr(dispatch.httpx, "AsyncClient", _Client)
    out = asyncio.run(dispatch.dispatch_reply("telegram", "u1", "下单 两杯咖啡"))
    assert out == "订单已创建"
    assert captured["url"] == "http://n8n:5678/webhook/order"
    assert captured["json"]["keyword"] == "下单"


def test_workflow_failure_falls_back_to_chat(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "n8n_base_url", "http://n8n:5678")
    monkeypatch.setattr(settings, "n8n_workflows", "下单=order")

    async def fake_chat(t):
        return "（改用聊天回复）"

    monkeypatch.setattr(dispatch, "chat_reply", fake_chat)

    class _Boom:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **k):
            raise RuntimeError("n8n down")

    monkeypatch.setattr(dispatch.httpx, "AsyncClient", _Boom)
    out = asyncio.run(dispatch.dispatch_reply("telegram", "u1", "下单 咖啡"))
    assert out == "（改用聊天回复）"
