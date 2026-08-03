"""Dispatch brain — decide what an incoming message should do, then route it.

Every inbound message (from any channel) is classified into one intent:

  1. workflow  — starts with a configured keyword -> forward to an n8n workflow
  2. summarize — is a URL/link            -> fetch + AI summary
  3. chat      — anything else            -> AI chat reply (default)

Workflow routing is config-driven via N8N_WORKFLOWS ("提醒=remind;天气=weather"),
so new workflows are added by editing .env — no code change. Never raises; any
failure degrades to a normal chat reply so the user always gets an answer.
"""

from __future__ import annotations

import logging

import httpx

from app.config import settings
from app.pipeline.chat import chat_reply
from app.pipeline.ingest import extract_url
from app.pipeline.service import process_url

log = logging.getLogger("eios.dispatch")


def workflow_map() -> dict[str, str]:
    """Parse N8N_WORKFLOWS ("kw=path;kw2=path2") into {keyword: webhook_path}."""
    out: dict[str, str] = {}
    for pair in (settings.n8n_workflows or "").split(";"):
        pair = pair.strip()
        if "=" in pair:
            kw, path = pair.split("=", 1)
            kw, path = kw.strip(), path.strip().strip("/")
            if kw and path:
                out[kw] = path
    return out


def match_workflow(text: str) -> tuple[str, str] | None:
    """Return (keyword, webhook_path) if the message triggers a workflow."""
    if not settings.n8n_base_url:
        return None
    t = (text or "").strip().lstrip("/#")
    for kw, path in workflow_map().items():
        if t.startswith(kw):
            return kw, path
    return None


def classify(text: str) -> str:
    """Return the intent: 'workflow' | 'summarize' | 'chat'."""
    t = (text or "").strip()
    if match_workflow(t):
        return "workflow"
    if t.lower().startswith(("http://", "https://")) or extract_url(t):
        return "summarize"
    return "chat"


async def _run_workflow(kw: str, path: str, channel: str, sender: str, text: str) -> str:
    """Forward the message to an n8n workflow webhook; return its reply text."""
    url = f"{settings.n8n_base_url.rstrip('/')}/webhook/{path}"
    payload = {"channel": channel, "sender": sender, "text": text, "keyword": kw}
    try:
        async with httpx.AsyncClient(timeout=settings.n8n_timeout_seconds) as c:
            r = await c.post(url, json=payload)
            r.raise_for_status()
            body = r.text.strip()
        if not body:
            return f"已转交「{kw}」工作流处理。"
        # n8n often returns JSON like {"reply": "..."}; surface a friendly string.
        try:
            data = r.json()
            if isinstance(data, dict):
                return str(data.get("reply") or data.get("text") or body)
        except Exception:  # noqa: BLE001
            pass
        return body
    except Exception:  # noqa: BLE001
        log.exception("dispatch: n8n workflow '%s' failed; falling back to chat", kw)
        return await chat_reply(text)


async def dispatch_reply(channel: str, sender: str, text: str) -> str:
    """Route the message by intent and return the reply text. Never raises."""
    text = (text or "").strip()
    wf = match_workflow(text)
    if wf:
        return await _run_workflow(wf[0], wf[1], channel, sender, text)

    if classify(text) == "summarize":
        try:
            url = text if text.lower().startswith(("http://", "https://")) else extract_url(text)
            result = await process_url(url)
            title = (result.title or "").strip()
            summary = (result.summary or "").strip()
            return f"{title}\n\n{summary}".strip() or await chat_reply(text)
        except Exception:  # noqa: BLE001
            log.exception("dispatch: summarize failed; falling back to chat")
            return await chat_reply(text)

    return await chat_reply(text)
