"""Pluggable audio codec strategies for platform-specific voice requirements.

Each channel can use its own audio format strategy:
- WeChat: SILK v3 (native voice bubbles)
- WhatsApp: OGG/OPUS (Cloud API standard)
- Telegram: OGG (Bot API flexible)
- Custom: extensible for user-defined codecs
"""

from __future__ import annotations

import abc
import asyncio
import os


class AudioCodec(abc.ABC):
    """Abstract audio codec — converts source to platform-native format."""

    name: str

    @abc.abstractmethod
    async def encode(self, src_path: str, out_path: str | None = None) -> str:
        """Encode source audio to platform format. Return output path."""
        ...


class SilkCodec(AudioCodec):
    """WeChat SILK v3 codec (16kHz mono OPUS in webm container)."""

    name = "silk"

    async def encode(self, src_path: str, out_path: str | None = None) -> str:
        from app.messaging.media import _ffmpeg

        out_path = out_path or os.path.splitext(src_path)[0] + ".silk"
        await _ffmpeg(
            "-i", src_path,
            "-ar", "16000", "-ac", "1",
            "-c:a", "libopus", "-vbr", "on", "-b:a", "24k",
            "-f", "webm", out_path
        )
        return out_path


class OggOpusCodec(AudioCodec):
    """WhatsApp / standard OGG/OPUS codec (variable bitrate)."""

    name = "ogg_opus"

    async def encode(self, src_path: str, out_path: str | None = None) -> str:
        from app.messaging.media import _ffmpeg

        out_path = out_path or os.path.splitext(src_path)[0] + ".ogg"
        await _ffmpeg(
            "-i", src_path,
            "-c:a", "libopus", "-b:a", "32k", "-ac", "1",
            "-f", "ogg", out_path
        )
        return out_path


class AmrCodec(AudioCodec):
    """Legacy AMR-NB codec (for compatibility, not recommended)."""

    name = "amr"

    async def encode(self, src_path: str, out_path: str | None = None) -> str:
        from app.messaging.media import _ffmpeg

        out_path = out_path or os.path.splitext(src_path)[0] + ".amr"
        await _ffmpeg(
            "-i", src_path,
            "-ar", "8000", "-ac", "1",
            "-c:a", "libopencore_amrnb", "-b:a", "12.2k",
            out_path
        )
        return out_path


# Global codec registry
_CODECS: dict[str, type[AudioCodec]] = {
    "silk": SilkCodec,
    "ogg_opus": OggOpusCodec,
    "amr": AmrCodec,
}


def get_codec(name: str) -> AudioCodec:
    """Get a codec instance by name. Defaults to SILK if not found."""
    codec_cls = _CODECS.get(name.lower(), SilkCodec)
    return codec_cls()


def register_codec(codec: AudioCodec) -> None:
    """Register a custom codec for use."""
    _CODECS[codec.name.lower()] = type(codec)
