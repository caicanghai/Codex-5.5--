"""FastAPI application — health check and the single /ingest endpoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from app import cache
from app.db import SessionLocal, ensure_schema
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
