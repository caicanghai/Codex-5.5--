"""推送渠道。"""

from __future__ import annotations

import logging

from .base import Notifier
from .serverchan import ServerChanNotifier
from .telegram_bot import TelegramBotNotifier
from .wecom import WecomNotifier

log = logging.getLogger(__name__)


def build_notifiers(cfg) -> list[Notifier]:
    """按 config.notifiers 开关 + 密钥可用性构建推送器。"""
    out: list[Notifier] = []
    conf = cfg.notifiers or {}

    if conf.get("telegram_bot", {}).get("enabled") and cfg.telegram_bot_token and cfg.telegram_chat_id:
        out.append(TelegramBotNotifier(cfg.telegram_bot_token, cfg.telegram_chat_id))
    if conf.get("wecom", {}).get("enabled") and cfg.wecom_webhook:
        out.append(WecomNotifier(cfg.wecom_webhook))
    if conf.get("serverchan", {}).get("enabled") and cfg.serverchan_key:
        out.append(ServerChanNotifier(cfg.serverchan_key))

    if not out:
        log.warning("没有可用的推送渠道（检查 config.notifiers 开关与对应环境变量）")
    return out


__all__ = ["Notifier", "build_notifiers"]
