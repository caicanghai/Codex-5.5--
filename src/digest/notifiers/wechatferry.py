"""个人微信群推送（WeChatFerry / wcfhttp）。

比 wechaty(web协议) 稳，主流方案。原理：Windows 上 hook 电脑版微信，
wcfhttp 暴露 HTTP 接口 `POST /text`。本推送器把纯文本每日重点发到指定群。

需要：
  WCF_HTTP_ENDPOINT  wcfhttp 地址，如 http://<你的Windows服务器IP>:9999
  WCF_RECEIVER       目标群的 room id（形如 xxxxx@chatroom；用群名找 id 见部署文档）

⚠️ 非官方 hook，有封号风险，请用小号登录电脑版微信。
未配置或网关不可达时本次失败并告警，不影响其它渠道。
"""

from __future__ import annotations

import logging

import httpx

from ..compose import compose_plaintext
from ..models import Digest

log = logging.getLogger(__name__)


class WeChatFerryNotifier:
    channel_id = "wechatferry"

    def __init__(self, endpoint: str, receiver: str) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.receiver = receiver

    def send(self, digest: Digest, markdown: str) -> bool:
        text = compose_plaintext(digest)  # 微信不渲染 Markdown
        try:
            resp = httpx.post(
                f"{self.endpoint}/text",
                json={"msg": text, "receiver": self.receiver, "aters": ""},
                timeout=40,
            )
            if resp.status_code != 200:
                log.warning("wcfhttp 返回 %s: %s", resp.status_code, resp.text[:200])
                return False
            # 不同 wcfhttp 版本响应字段不一，宽松判断：有明确 status!=0 才算失败
            try:
                data = resp.json()
                if isinstance(data, dict) and data.get("status") not in (0, None):
                    log.warning("wcfhttp 发送失败: %s", data)
                    return False
            except ValueError:
                pass
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("wcfhttp 网关不可达/异常: %s", exc)
            return False
