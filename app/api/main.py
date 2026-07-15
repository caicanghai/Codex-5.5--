"""FastAPI application — health check and the single /ingest endpoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from xml.etree import ElementTree

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import text

from app import cache
from app.db import SessionLocal, ensure_schema
from app.inbound import reply_and_deliver
from app.messaging.wechat_official import WeChatOfficialProvider, passive_text_reply
from app.messaging.whatsapp import verify_webhook as whatsapp_verify_webhook
from app.pipeline.chat import chat_reply
from app.pipeline.service import process_url


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_schema()
    yield


app = FastAPI(title="EIOS MVP", version="0.1.0", lifespan=lifespan)


class IngestRequest(BaseModel):
    url: str = Field(..., examples=["https://example.com/article"])


class IngestResponse(BaseModel):
    id: int | None
    url: str
    title: str
    summary: str
    source: str


@app.get("/health")
def health() -> dict:
    db_ok = False
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    redis_ok = cache.ping()
    status = "ok" if (db_ok and redis_ok) else "degraded"
    if status != "ok":
        raise HTTPException(status_code=503, detail={"db": db_ok, "redis": redis_ok})
    return {"status": status, "db": db_ok, "redis": redis_ok}


@app.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint(body: IngestRequest) -> IngestResponse:
    url = body.url.strip()
    if not url.lower().startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="url must start with http(s)://")
    try:
        result = await process_url(url)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"ingest failed: {exc}") from exc
    return IngestResponse(
        id=result.id,
        url=result.url,
        title=result.title,
        summary=result.summary,
        source=result.source,
    )


# ---- Inbound webhooks (official APIs only; isolated from the Telegram bot) ----
@app.get("/webhook/whatsapp")
def whatsapp_verify(request: Request):
    q = request.query_params
    challenge = whatsapp_verify_webhook(
        q.get("hub.mode", ""), q.get("hub.verify_token", ""), q.get("hub.challenge", "")
    )
    if challenge is None:
        raise HTTPException(status_code=403, detail="verification failed")
    return Response(content=challenge, media_type="text/plain")


@app.post("/webhook/whatsapp")
async def whatsapp_receive(request: Request, background: BackgroundTasks) -> dict:
    """Parse inbound WhatsApp messages -> AI reply + native voice (async)."""
    try:
        body = await request.json()
    except Exception:
        return {"status": "ignored"}
    for msg in _extract_whatsapp_messages(body):
        background.add_task(reply_and_deliver, "whatsapp", msg["from"], msg["text"])
    return {"status": "received"}


def _extract_whatsapp_messages(body: dict) -> list[dict]:
    out: list[dict] = []
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            for m in change.get("value", {}).get("messages", []):
                if m.get("type") == "text":
                    out.append({"from": m.get("from", ""), "text": m.get("text", {}).get("body", "")})
    return out


@app.get("/webhook/wechat")
def wechat_verify(request: Request):
    q = request.query_params
    provider = WeChatOfficialProvider()
    if provider.verify_webhook(q.get("signature", ""), q.get("timestamp", ""), q.get("nonce", "")):
        return Response(content=q.get("echostr", ""), media_type="text/plain")
    raise HTTPException(status_code=403, detail="signature mismatch")


@app.post("/webhook/wechat")
async def wechat_receive(request: Request):
    q = request.query_params
    provider = WeChatOfficialProvider()
    if not provider.verify_webhook(q.get("signature", ""), q.get("timestamp", ""), q.get("nonce", "")):
        raise HTTPException(status_code=403, detail="signature mismatch")
    raw = (await request.body()).decode(errors="ignore")
    msg = _parse_wechat_xml(raw)
    if msg.get("MsgType") == "text" and msg.get("Content"):
        reply = await chat_reply(msg["Content"])
        xml = passive_text_reply(msg.get("FromUserName", ""), msg.get("ToUserName", ""), reply)
        return Response(content=xml, media_type="application/xml")
    return Response(content="success", media_type="text/plain")


def _parse_wechat_xml(raw: str) -> dict:
    out: dict[str, str] = {}
    try:
        root = ElementTree.fromstring(raw)
        for child in root:
            out[child.tag] = (child.text or "").strip()
    except Exception:
        pass
    return out


class OpenClawInbound(BaseModel):
    session: str
    text: str


@app.post("/webhook/openclaw")
async def openclaw_receive(body: OpenClawInbound, background: BackgroundTasks) -> dict:
    """Inbound from the OpenClaw (openclaw-weixin) bridge -> AI reply + voice."""
    if not body.text.strip():
        return {"status": "ignored"}
    background.add_task(reply_and_deliver, "openclaw", body.session, body.text)
    return {"status": "received"}
