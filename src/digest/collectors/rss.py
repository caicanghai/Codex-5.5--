"""通用 RSS/Atom 采集器，覆盖清单里绝大多数来源。"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import feedparser
import httpx

from ..config import Source
from ..models import RawItem

log = logging.getLogger(__name__)

# 伪装常见浏览器 UA，减少被简单反爬拦截
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 DailyDigestBot/0.1"


class RssCollector:
    def __init__(self, source: Source) -> None:
        self.source = source
        self.source_id = source.id

    def _download(self, url: str) -> str | bytes | None:
        """优先用 httpx 拉取（正确走系统代理），失败则交给 feedparser 直接取。"""
        try:
            resp = httpx.get(
                url, timeout=25, follow_redirects=True,
                headers={"User-Agent": _UA},
            )
            resp.raise_for_status()
            return resp.content
        except Exception as exc:  # noqa: BLE001
            log.debug("httpx 拉取失败 %s，回退 feedparser: %s", self.source_id, exc)
            return None

    def fetch(self, since: datetime) -> list[RawItem]:
        url = self.source.feed_url
        if not url:
            return []
        content = self._download(url)
        parsed = feedparser.parse(content if content is not None else url, agent=_UA)
        if parsed.bozo and not parsed.entries:
            log.warning("RSS 解析失败 %s: %s", self.source_id, parsed.get("bozo_exception"))
            return []

        items: list[RawItem] = []
        name = self.source.name or parsed.feed.get("title", self.source_id)
        for entry in parsed.entries:
            published = _entry_datetime(entry)
            if published and published < since:
                continue
            title = entry.get("title", "").strip()
            link = entry.get("link", "")
            if not title or not link:
                continue
            items.append(
                RawItem(
                    source_id=self.source_id,
                    source_name=name,
                    title=title,
                    url=link,
                    published_at=published or datetime.now(timezone.utc),
                    summary_raw=entry.get("summary", "") or entry.get("description", ""),
                    lang="zh",
                )
            )
        return items


def _entry_datetime(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        val = entry.get(key)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                continue
    return None
