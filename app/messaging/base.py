"""Messaging provider interface (outbound channel senders). Transport-only."""

from __future__ import annotations

import abc
from dataclasses import dataclass

import httpx


class MessagingError(RuntimeError):
    pass


@dataclass
class DeliveryResult:
    channel: str
    ok: bool
    detail: str = ""


class MessagingProvider(abc.ABC):
    """One uniform interface for every channel. No business logic in providers."""

    name: str = "base"

    def __init__(self) -> None:
        # Tests may inject an httpx transport for mocking.
        self._transport: httpx.AsyncBaseTransport | None = None

    def _client(self, timeout: float = 30.0, **kw: object) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=self._transport, timeout=timeout, **kw)  # type: ignore[arg-type]

    @abc.abstractmethod
    def validate_config(self) -> bool:
        """Return True if this provider has the credentials it needs (no I/O)."""

    async def healthcheck(self) -> bool:
        """Default: usable if configured. Providers may override with a live check."""
        return self.validate_config()

    # Default senders raise NotImplementedError; providers implement what they support.
    async def send_text(self, to: str, text: str) -> None:
        raise NotImplementedError

    async def send_image(self, to: str, path_or_url: str, caption: str = "") -> None:
        raise NotImplementedError

    async def send_audio(self, to: str, path: str) -> None:
        raise NotImplementedError

    async def send_file(self, to: str, path: str, filename: str | None = None) -> None:
        raise NotImplementedError

    async def send_voice(self, to: str, ogg_path: str) -> None:
        raise NotImplementedError

    @property
    def default_target(self) -> str:
        return ""
