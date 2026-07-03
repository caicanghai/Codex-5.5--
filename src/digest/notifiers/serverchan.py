"""Server酱推送（转发到个人微信）。长文会被截断，放摘要+链接即可。"""

from __future__ import annotations

import logging

import httpx

from ..models import Digest

log = logging.getLogger(__name__)


class ServerChanNotifier:
    channel_id = "serverchan"

    def __init__(self, sendkey: str) -> None:
        self.api = f"https://sctapi.ftqq.com/{sendkey}.send"

    def send(self, digest: Digest, markdown: str) -> bool:
        title = f"安全资讯每日重点 · {digest.date}"
        try:
            resp = httpx.post(
                self.api,
                data={"title": title, "desp": markdown[:9000]},
                timeout=20,
            )
            data = resp.json()
            if data.get("code") not in (0, None):
                log.warning("Server酱推送失败: %s", data)
                return False
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("Server酱推送异常: %s", exc)
            return False
