"""Ingestion: fetch a URL, detect RSS vs HTML, extract title + text."""

from __future__ import annotations

import re
from dataclasses import dataclass

import feedparser
import httpx
from bs4 import BeautifulSoup

from app.config import settings

_UA = "Mozilla/5.0 (compatible; EIOS-MVP/0.1; +https://example.invalid)"
_URL_RE = re.compile(r"https?://\S+")


@dataclass
class Article:
    url: str
    title: str
    text: str
    source: str  # "rss" | "url"


def extract_url(text: str) -> str | None:
    match = _URL_RE.search(text or "")
    return match.group(0).rstrip(").,]") if match else None


async def _fetch(url: str) -> httpx.Response:
    async with httpx.AsyncClient(
        timeout=settings.fetch_timeout_seconds,
        follow_redirects=True,
        headers={"User-Agent": _UA},
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _html_to_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = _clean(soup.title.get_text()) if soup.title else ""
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        tag.decompose()
    # Prefer <article>, then <main>, else body paragraphs.
    container = soup.find("article") or soup.find("main") or soup.body or soup
    paragraphs = [p.get_text(" ", strip=True) for p in container.find_all("p")]
    text = _clean(" ".join(paragraphs)) if paragraphs else _clean(container.get_text(" "))
    return title, text


async def ingest(url: str) -> Article:
    """Fetch and normalize a URL or RSS feed into an Article."""
    resp = await _fetch(url)
    content_type = resp.headers.get("content-type", "").lower()
    body = resp.content

    looks_like_feed = (
        "xml" in content_type
        or "rss" in content_type
        or body[:512].lstrip().startswith((b"<?xml", b"<rss", b"<feed"))
    )

    if looks_like_feed:
        feed = feedparser.parse(body)
        if feed.entries:
            entry = feed.entries[0]
            title = _clean(getattr(entry, "title", "")) or _clean(
                getattr(feed.feed, "title", "")
            )
            summary_html = getattr(entry, "summary", "") or getattr(entry, "description", "")
            text = _clean(BeautifulSoup(summary_html, "html.parser").get_text(" "))
            link = getattr(entry, "link", "")
            if len(text) < 200 and link:
                try:
                    art_resp = await _fetch(link)
                    _, body_text = _html_to_text(art_resp.text)
                    if len(body_text) > len(text):
                        text = body_text
                except Exception:
                    pass
            return Article(
                url=url, title=title or "(untitled)", text=text or title, source="rss"
            )

    # Plain HTML page.
    title, text = _html_to_text(resp.text)
    return Article(url=url, title=title or "(untitled)", text=text, source="url")
