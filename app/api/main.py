"""FastAPI application — health check and the single /ingest endpoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import text

from app import cache
from app.db import SessionLocal, ensure_schema
from app.messaging.wechat_official import WeChatOfficialProvider
from app.messaging.whatsapp import verify_webhook as whatsapp_verify_webhook
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
async def whatsapp_receive(_: Request) -> dict:
    # Acknowledge receipt; message handling is added when inbound flows are needed.
    return {"status": "received"}


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
    return Response(content="success", media_type="text/plain")
