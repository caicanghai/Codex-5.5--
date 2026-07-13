"""MessageRouter: fan-out to enabled channels with isolation, retry, dedup."""

from __future__ import annotations

import asyncio
import hashlib
import logging

from app import cache
from app.config import settings
from app.messaging.base import DeliveryResult, MessagingProvider
from app.messaging.registry import enabled_providers

log = logging.getLogger("eios.router")


def _digest(text: str) -> str:
    return hashlib.sha256((text or "").encode()).hexdigest()[:16]


class MessageRouter:
    def __init__(self, providers: list[MessagingProvider] | None = None) -> None:
        self.providers = providers if providers is not None else enabled_providers()

    # ---- Redis-backed idempotency (best-effort) ----
    def _dedup_key(self, channel: str, digest: str) -> str:
        return f"eios:deliv:{channel}:{digest}"

    def _already_sent(self, channel: str, digest: str) -> bool:
        try:
            return bool(cache.get_client().get(self._dedup_key(channel, digest)))
        except Exception:
            return False

    def _mark_sent(self, channel: str, digest: str) -> None:
        try:
            cache.get_client().set(
                self._dedup_key(channel, digest), "1", ex=settings.delivery_dedup_ttl_seconds
            )
        except Exception:
            pass

    async def _retry(self, coro_factory) -> None:
        last: Exception | None = None
        for _ in range(max(1, settings.channel_retry_attempts)):
            try:
                await coro_factory()
                return
            except Exception as exc:  # noqa: BLE001
                last = exc
                await asyncio.sleep(0)
        raise last if last else RuntimeError("send failed")

    async def _send_channel(
        self, provider: MessagingProvider, text: str, ogg_path: str | None
    ) -> DeliveryResult:
        ch = provider.name
        digest = _digest(text)
        if text and self._already_sent(ch, digest):
            return DeliveryResult(ch, True, "skipped-duplicate")
        target = provider.default_target
        try:
            if text:
                await self._retry(lambda: provider.send_text(target, text))
                self._mark_sent(ch, digest)
            # Voice is additive; its failure must NOT fail the text delivery.
            if ogg_path:
                try:
                    await self._retry(lambda: provider.send_voice(target, ogg_path))
                except Exception as exc:  # noqa: BLE001
                    log.warning("voice send failed channel=%s: %s", ch, type(exc).__name__)
            log.info("delivery channel=%s ok digest=%s", ch, digest)
            return DeliveryResult(ch, True, "")
        except Exception as exc:  # noqa: BLE001
            log.warning("delivery channel=%s FAILED digest=%s err=%s", ch, digest, type(exc).__name__)
            return DeliveryResult(ch, False, type(exc).__name__)

    async def broadcast(self, text: str, ogg_path: str | None = None) -> list[DeliveryResult]:
        """Send to all enabled channels independently. One failure never stops others."""
        if not self.providers:
            return []
        results = await asyncio.gather(
            *(self._send_channel(p, text, ogg_path) for p in self.providers)
        )
        return list(results)
