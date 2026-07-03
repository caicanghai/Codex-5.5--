"""统一数据模型。所有来源归一化为 Event，最终组装成 Digest。"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _canonical_url(url: str) -> str:
    """归一化 URL：去掉常见跟踪参数与 fragment，便于去重。"""
    if not url:
        return ""
    url = url.split("#", 1)[0]
    if "?" in url:
        base, query = url.split("?", 1)
        keep = []
        for kv in query.split("&"):
            key = kv.split("=", 1)[0].lower()
            if key.startswith("utm_") or key in {
                "spm", "src", "from", "share_token", "chksm", "scene", "clicktime",
            }:
                continue
            keep.append(kv)
        url = base + ("?" + "&".join(keep) if keep else "")
    return url.rstrip("/")


def make_event_id(url: str, source_id: str, title: str) -> str:
    """稳定指纹：优先用归一化 URL，退化到 source_id+title。"""
    basis = _canonical_url(url) or f"{source_id}::{title.strip()}"
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]


@dataclass
class RawItem:
    """采集器产出的原始条目，尚未归一化。"""

    source_id: str
    source_name: str
    title: str
    url: str
    published_at: datetime
    summary_raw: str = ""
    lang: str = "zh"


@dataclass
class Event:
    """归一化后的事件，贯穿整条流水线。"""

    id: str
    source_id: str
    source_name: str
    title: str
    url: str
    published_at: datetime
    summary_raw: str = ""
    lang: str = "zh"
    source_weight: float = 1.0
    # 流水线后续阶段填充
    score: float = 0.0
    matched_keywords: list[str] = field(default_factory=list)
    category: str = "其他"
    highlight_summary: str | None = None

    @classmethod
    def from_raw(cls, raw: RawItem, source_weight: float = 1.0) -> "Event":
        canonical = _canonical_url(raw.url)
        return cls(
            id=make_event_id(raw.url, raw.source_id, raw.title),
            source_id=raw.source_id,
            source_name=raw.source_name,
            title=raw.title.strip(),
            url=canonical or raw.url,
            published_at=_ensure_tz(raw.published_at),
            summary_raw=_clean_text(raw.summary_raw),
            lang=raw.lang,
            source_weight=source_weight,
        )


@dataclass
class Digest:
    """最终推送的每日摘要。"""

    date: str
    top_highlights: list[Event] = field(default_factory=list)
    by_category: dict[str, list[Event]] = field(default_factory=dict)
    total_collected: int = 0
    total_after_dedup: int = 0

    @property
    def is_empty(self) -> bool:
        return not self.top_highlights and not any(self.by_category.values())


def _ensure_tz(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


_WS = re.compile(r"\s+")
_TAG = re.compile(r"<[^>]+>")


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = _TAG.sub("", text)
    return _WS.sub(" ", text).strip()
