"""Telegram Bot 推送（官方 Bot API，最稳）。"""

from __future__ import annotations

import logging

import httpx

from ..models import Digest

log = logging.getLogger(__name__)

_MAX = 4000  # Telegram 单条消息上限约 4096，留余量


class TelegramBotNotifier:
    channel_id = "telegram_bot"

    def __init__(self, token: str, chat_id: str) -> None:
        self.api = f"https://api.telegram.org/bot{token}/sendMessage"
        self.chat_id = chat_id

    def send(self, digest: Digest, markdown: str) -> bool:
        ok = True
        for chunk in _split(markdown, _MAX):
            try:
                resp = httpx.post(
                    self.api,
                    json={
                        "chat_id": self.chat_id,
                        "text": chunk,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": True,
                    },
                    timeout=20,
                )
                if resp.status_code != 200:
                    log.warning("Telegram 推送失败 %s: %s", resp.status_code, resp.text[:200])
                    ok = False
            except Exception as exc:  # noqa: BLE001
                log.warning("Telegram 推送异常: %s", exc)
                ok = False
        return ok


def _split(text: str, size: int) -> list[str]:
    if len(text) <= size:
        return [text]
    parts, cur = [], ""
    for line in text.splitlines(keepends=True):
        if len(cur) + len(line) > size:
            parts.append(cur)
            cur = ""
        cur += line
    if cur:
        parts.append(cur)
    return parts
