"""Channel adapter interface.

Telegram is the only ACTIVE delivery channel for this MVP (implemented directly
in app/bot/main.py). This module reserves a common interface so future channels
can be added without touching the pipeline. WeChat is reserved only — not
implemented.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ChannelAdapter(Protocol):
    """Transport-only contract every delivery channel must implement."""

    name: str

    async def send_text(self, chat_id: str, text: str) -> None: ...

    async def send_voice(self, chat_id: str, ogg_path: str) -> None: ...


class WeChatChannelAdapter:
    """Reserved placeholder — NOT implemented in this MVP."""

    name = "wechat"

    async def send_text(self, chat_id: str, text: str) -> None:
        raise NotImplementedError("WeChat channel is reserved for a future release")

    async def send_voice(self, chat_id: str, ogg_path: str) -> None:
        raise NotImplementedError("WeChat channel is reserved for a future release")
