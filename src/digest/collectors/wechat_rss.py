"""微信公众号采集器。

本质仍是 RSS：公众号需先经 wechat2rss / feeddd 转成 RSS，把生成的地址回填到
sources.yaml 的 rss_url。单独成类，便于后续加公众号专属清洗（去广告尾巴、二维码等）。
"""

from __future__ import annotations

import logging
import re
from datetime import datetime

from ..config import Source
from ..models import RawItem
from .rss import RssCollector

log = logging.getLogger(__name__)

# 公众号文章常见的尾部噪音
_TAIL_NOISE = re.compile(r"(点击.*阅读原文|长按.*识别二维码|扫码关注|微信扫一扫).*$")


class WeChatRssCollector:
    def __init__(self, source: Source) -> None:
        self.source = source
        self.source_id = source.id
        self._inner = RssCollector(source)

    def fetch(self, since: datetime) -> list[RawItem]:
        if not self.source.feed_url:
            log.info("公众号 %s 尚未配置 rss_url（需 wechat2rss），跳过", self.source_id)
            return []
        items = self._inner.fetch(since)
        for item in items:
            item.summary_raw = _TAIL_NOISE.sub("", item.summary_raw).strip()
            if not item.source_name:
                item.source_name = self.source.name
        return items
