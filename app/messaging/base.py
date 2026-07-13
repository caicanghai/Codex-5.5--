"""Messaging provider interface (outbound channel senders)."""

from __future__ import annotations

import abc


class MessagingProvider(abc.ABC):
    """Transport-only outbound sender. No business logic."""

    name: str = "base"

    @abc.abstractmethod
    async def send_text(self, to: str, text: str) -> None: ...

    @abc.abstractmethod
    async def send_voice(self, to: str, ogg_path: str) -> None: ...

    @abc.abstractmethod
    async def healthcheck(self) -> bool: ...
