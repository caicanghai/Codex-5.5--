"""Pipeline orchestration shared by the API and the Telegram bot."""

from __future__ import annotations

from dataclasses import dataclass

from app.db import SessionLocal
from app.models import Item
from app.pipeline.ingest import ingest
from app.pipeline.summarize import summarize


@dataclass
class ProcessResult:
    id: int | None
    url: str
    title: str
    summary: str
    source: str


async def process_url(url: str, persist: bool = True) -> ProcessResult:
    """Ingest a URL/RSS link and produce a summary. Optionally persist it."""
    article = await ingest(url)
    summary = await summarize(article.text)

    item_id: int | None = None
    if persist:
        try:
            with SessionLocal() as session:
                item = Item(
                    url=article.url,
                    title=article.title[:1024],
                    summary=summary,
                    source=article.source,
                )
                session.add(item)
                session.commit()
                item_id = item.id
        except Exception:
            # Persistence is best-effort for the MVP; never fail the reply.
            item_id = None

    return ProcessResult(
        id=item_id,
        url=article.url,
        title=article.title,
        summary=summary,
        source=article.source,
    )
