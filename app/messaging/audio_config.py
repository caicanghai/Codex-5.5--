"""Per-provider audio codec configuration.

Map each messaging provider to its required audio codec.
Easily customizable via environment variables or config changes.
"""

from __future__ import annotations

import os
from app.messaging.audio_codec import get_codec, AudioCodec


# Default codec per provider
_PROVIDER_CODECS: dict[str, str] = {
    "wechat_official": "silk",      # WeChat Official Account
    "wecom": "silk",                # Enterprise WeChat
    "openclaw": "silk",             # OpenClaw (WeChat bridge)
    "whatsapp": "ogg_opus",         # WhatsApp Cloud API
    "telegram": "ogg_opus",         # Telegram Bot API (flexible)
}


def get_provider_codec(provider_name: str) -> AudioCodec:
    """Get audio codec for a messaging provider.

    Override with env var: AUDIO_CODEC_{PROVIDER_NAME}
    Example: AUDIO_CODEC_TELEGRAM=silk
    """
    env_key = f"AUDIO_CODEC_{provider_name.upper()}"
    codec_name = os.getenv(env_key, _PROVIDER_CODECS.get(provider_name, "ogg_opus"))
    return get_codec(codec_name)


def set_provider_codec(provider_name: str, codec_name: str) -> None:
    """Override codec for a provider at runtime."""
    _PROVIDER_CODECS[provider_name.lower()] = codec_name.lower()
