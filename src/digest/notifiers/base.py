"""推送器基类。"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models import Digest


@runtime_checkable
class Notifier(Protocol):
    channel_id: str

    def send(self, digest: Digest, markdown: str) -> bool:
        """发送每日摘要，返回是否成功。实现内部自行容错。"""
        ...
