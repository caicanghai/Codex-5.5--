"""Edge-TTS provider (final fallback, no API key required)."""

from __future__ import annotations

import os

import edge_tts

from app.config import settings
from app.voice.base import VoiceError, VoiceProvider


class EdgeProvider(VoiceProvider):
    name = "edge"

    async def healthcheck(self) -> bool:
        # No key required; assume available (network checked at call time).
        return True

    async def synthesize(self, text: str, voice_id: str | None = None) -> str:
        text = (text or "").strip()[: settings.tts_max_chars]
        if not text:
            raise VoiceError("empty text for TTS")
        tmp = self._tempdir("eios-edge-")
        mp3 = os.path.join(tmp, "voice.mp3")
        voice = voice_id or settings.tts_voice
        await edge_tts.Communicate(text, voice).save(mp3)
        if not os.path.exists(mp3) or os.path.getsize(mp3) == 0:
            raise VoiceError("edge-tts produced no audio")
        ogg = await self.normalize_to_ogg(mp3, os.path.join(tmp, "voice.ogg"))
        self.delete_temporary_files(mp3)
        return ogg
