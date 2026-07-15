"""Unified inbound pipeline: received message -> AI reply -> voice -> delivery.

One code path reused by every channel's webhook. Per-channel voice conversion
happens inside each provider's send_voice. One failure never blocks the rest.
"""

from __future__ import annotations

import logging

from app.messaging.registry import all_providers
from app.pipeline.chat import chat_reply
from app.voice.service import cleanup_paths, voice_service

log = logging.getLogger("eios.inbound")


async def reply_and_deliver(channel: str, sender: str, text: str, *, with_voice: bool = True) -> str:
    """Generate an AI reply and deliver text (+native voice) back on `channel`.

    Returns the reply text. Never raises; logs failures per step.
    """
    reply = await chat_reply(text)
    providers = all_providers()
    provider = providers.get(channel)
    if provider is None or not provider.validate_config():
        log.warning("inbound %s: provider unavailable, reply not delivered", channel)
        return reply

    try:
        await provider.send_text(sender, reply)
    except Exception:  # noqa: BLE001
        log.exception("inbound %s: send_text failed", channel)

    if with_voice:
        ogg = None
        try:
            ogg, _prov = await voice_service.synthesize(reply)
            await provider.send_voice(sender, ogg)
        except Exception:  # noqa: BLE001
            log.exception("inbound %s: voice delivery failed (text already sent)", channel)
        finally:
            cleanup_paths(ogg or "")
    return reply
