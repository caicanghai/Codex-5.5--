"""Channel provider registry + enablement resolution."""

from __future__ import annotations

from app.config import settings
from app.messaging.base import MessagingProvider
from app.messaging.telegram import TelegramProvider
from app.messaging.wechat_official import WeChatOfficialProvider
from app.messaging.wecom import WeComProvider
from app.messaging.whatsapp import WhatsAppProvider

# Fixed delivery priority order.
PRIORITY = ["telegram", "wecom", "wechat_official", "whatsapp"]


def all_providers() -> dict[str, MessagingProvider]:
    return {
        "telegram": TelegramProvider(),
        "wecom": WeComProvider(),
        "wechat_official": WeChatOfficialProvider(),
        "whatsapp": WhatsAppProvider(),
    }


def _requested() -> set[str]:
    raw = settings.channels_enabled or ""
    return {c.strip() for c in raw.split(",") if c.strip()}


def enabled_providers() -> list[MessagingProvider]:
    """Providers that are both requested via CHANNELS_ENABLED and configured."""
    requested = _requested()
    providers = all_providers()
    out: list[MessagingProvider] = []
    for name in PRIORITY:
        if name in requested and providers[name].validate_config():
            out.append(providers[name])
    return out
