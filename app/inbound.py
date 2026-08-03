"""Unified inbound pipeline: received message -> AI reply -> voice -> delivery.

One code path reused by every channel's webhook. Per-channel voice conversion
happens inside each provider's send_voice. One failure never blocks the rest.
"""

from __future__ import annotations

import logging

from app.config import settings
from app.dispatch import dispatch_reply
from app.messaging.registry import all_providers
from app.voice.service import cleanup_paths, voice_service

log = logging.getLogger("eios.inbound")


async def reply_and_deliver(channel: str, sender: str, text: str, *, with_voice: bool = True) -> str:
    """Generate an AI reply and deliver text (+native voice) back on `channel`.

    Returns the reply text. Never raises; logs failures per step.

    The dispatch brain routes the message first: workflow (n8n) / summarize / chat.
    """
    reply = await dispatch_reply(channel, sender, text)
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
            # Use the owner's picked voice template/clone for every channel.
            ogg, _prov = await voice_service.synthesize(
                reply, owner_id=settings.telegram_owner_id or None
            )
            await provider.send_voice(sender, ogg)
        except Exception:  # noqa: BLE001
            log.exception("inbound %s: voice delivery failed (text already sent)", channel)
        finally:
            cleanup_paths(ogg or "")
    return reply
