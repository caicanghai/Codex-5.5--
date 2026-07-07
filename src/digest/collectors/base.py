"""采集器基类。"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from ..models import RawItem


@runtime_checkable
class Collector(Protocol):
    source_id: str

    def fetch(self, since: datetime) -> list[RawItem]:
        """拉取 since 之后的条目。实现应自行容错，失败抛异常由上层捕获。"""
        ...
