"""去重：批内按 id 折叠 + 跨源相似标题折叠 + 状态库历史去重。"""

from __future__ import annotations

import re

from ..models import Event
from ..store import Store

_NON_WORD = re.compile(r"[^\w一-鿿]+")


def _title_key(title: str) -> str:
    """标题归一化指纹，用于折叠多家媒体报道的同一事件。"""
    return _NON_WORD.sub("", title.lower())[:40]


def dedup(events: list[Event], store: Store | None = None) -> list[Event]:
    """返回去重后的事件列表。保留每组中来源权重最高者。"""
    by_id: dict[str, Event] = {}
    for ev in events:
        if ev.id not in by_id:
            by_id[ev.id] = ev

    # 跨源相似标题折叠
    by_title: dict[str, Event] = {}
    for ev in by_id.values():
        key = _title_key(ev.title)
        if not key:
            by_title[ev.id] = ev
            continue
        existing = by_title.get(key)
        if existing is None or ev.source_weight > existing.source_weight:
            by_title[key] = ev

    unique = list(by_title.values())

    # 历史去重：已见过就丢弃；未见过则登记
    if store is not None:
        fresh: list[Event] = []
        for ev in unique:
            if store.is_seen(ev.id):
                continue
            store.mark_seen(ev.id, ev.source_id, ev.title, ev.url)
            fresh.append(ev)
        return fresh
    return unique
