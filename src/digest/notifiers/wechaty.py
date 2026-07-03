"""个人微信群推送（经 wechaty 网关）。

⚠️ 非官方方案：需要一个微信小号登录 docker/wechaty 网关，机器人待在目标群里转发。
有封号风险，请勿用主号。网关提供 POST /push {group, text} 接口。

未配置 WECHATY_ENDPOINT / WECHAT_GROUP_TOPIC 时不会启用；网关未登录或不可达时
本次推送失败并告警，不影响其它渠道。
"""

from __future__ import annotations

import logging

import httpx

from ..compose import compose_plaintext
from ..models import Digest

log = logging.getLogger(__name__)


class WechatyNotifier:
    channel_id = "wechaty"

    def __init__(self, endpoint: str, group_topic: str) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.group_topic = group_topic

    def send(self, digest: Digest, markdown: str) -> bool:
        text = compose_plaintext(digest)  # 微信不渲染 Markdown，发纯文本
        try:
            resp = httpx.post(
                f"{self.endpoint}/push",
                json={"group": self.group_topic, "text": text},
                timeout=40,
            )
            data = resp.json()
            if not data.get("ok"):
                log.warning("wechaty 推送失败: %s", data.get("error") or data)
                return False
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("wechaty 网关不可达/异常: %s", exc)
            return False
