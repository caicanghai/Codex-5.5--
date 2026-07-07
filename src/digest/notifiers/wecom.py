"""企业微信群机器人推送（官方 webhook，markdown 消息）。"""

from __future__ import annotations

import logging

import httpx

from ..models import Digest

log = logging.getLogger(__name__)

_MAX = 4000  # 企业微信 markdown 上限约 4096 字节


class WecomNotifier:
    channel_id = "wecom"

    def __init__(self, webhook: str) -> None:
        self.webhook = webhook

    def send(self, digest: Digest, markdown: str) -> bool:
        ok = True
        for chunk in _split(markdown, _MAX):
            try:
                resp = httpx.post(
                    self.webhook,
                    json={"msgtype": "markdown", "markdown": {"content": chunk}},
                    timeout=20,
                )
                data = resp.json()
                if data.get("errcode") != 0:
                    log.warning("企业微信推送失败: %s", data)
                    ok = False
            except Exception as exc:  # noqa: BLE001
                log.warning("企业微信推送异常: %s", exc)
                ok = False
        return ok


def _split(text: str, size: int) -> list[str]:
    if len(text.encode("utf-8")) <= size:
        return [text]
    parts, cur = [], ""
    for line in text.splitlines(keepends=True):
        if len((cur + line).encode("utf-8")) > size:
            parts.append(cur)
            cur = ""
        cur += line
    if cur:
        parts.append(cur)
    return parts
