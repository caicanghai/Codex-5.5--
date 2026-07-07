"""Telegram 频道采集器（Telethon 用户端）。

需要环境变量 TELEGRAM_API_ID / TELEGRAM_API_HASH（在 https://my.telegram.org 申请），
首次运行会要求登录一次并生成本地 session 文件。只读频道历史，不发言。

若未配置凭证或未安装 telethon，fetch 返回空列表并告警，不影响其他来源。
"""

from __future__ import annotations

import logging
from datetime import datetime

from ..config import Source
from ..models import RawItem

log = logging.getLogger(__name__)

_SESSION = "tg_digest.session"


class TelegramCollector:
    def __init__(self, source: Source, cfg) -> None:
        self.source = source
        self.source_id = source.id
        self.cfg = cfg

    def fetch(self, since: datetime) -> list[RawItem]:
        api_id = self.cfg.telegram_api_id
        api_hash = self.cfg.telegram_api_hash
        if not api_id or not api_hash:
            log.info("Telegram 未配置 API_ID/API_HASH，跳过 %s", self.source_id)
            return []
        try:
            from telethon.sync import TelegramClient  # 延迟导入，未安装则跳过
        except ImportError:
            log.warning("未安装 telethon，跳过 Telegram 采集（pip install telethon）")
            return []

        channel = self.source.channel
        items: list[RawItem] = []
        try:
            with TelegramClient(_SESSION, int(api_id), api_hash) as client:
                for msg in client.iter_messages(channel, offset_date=None, limit=50):
                    if msg.date and msg.date < since:
                        break
                    text = (msg.message or "").strip()
                    if not text:
                        continue
                    title = text.splitlines()[0][:120]
                    url = f"https://t.me/{channel.lstrip('@')}/{msg.id}"
                    items.append(
                        RawItem(
                            source_id=self.source_id,
                            source_name=self.source.name or channel,
                            title=title,
                            url=url,
                            published_at=msg.date,
                            summary_raw=text[:500],
                            lang="zh",
                        )
                    )
        except Exception as exc:  # noqa: BLE001
            log.warning("Telegram 采集失败 %s: %s", self.source_id, exc)
        return items
