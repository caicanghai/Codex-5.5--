"""采集器：把各类来源统一产出 RawItem。"""

from __future__ import annotations

import logging

from ..config import Source
from .base import Collector
from .rss import RssCollector
from .telegram import TelegramCollector
from .wechat_rss import WeChatRssCollector

log = logging.getLogger(__name__)


def build_collector(source: Source, cfg) -> Collector | None:
    """根据 source.type 选择采集器；无法构建时返回 None 并告警。"""
    try:
        if source.type == "rss":
            return RssCollector(source)
        if source.type == "wechat_rss":
            return WeChatRssCollector(source)
        if source.type == "telegram":
            return TelegramCollector(source, cfg)
    except Exception as exc:  # noqa: BLE001
        log.warning("构建采集器失败 %s: %s", source.id, exc)
        return None
    log.warning("未知来源类型 %s (source=%s)", source.type, source.id)
    return None


__all__ = ["Collector", "RssCollector", "WeChatRssCollector", "TelegramCollector", "build_collector"]
