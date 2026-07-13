"""ElevenLabs provider (fallback)."""

from __future__ import annotations

import os

import httpx

from app.config import settings
from app.voice.base import VoiceError, VoiceProvider


class ElevenLabsProvider(VoiceProvider):
    name = "elevenlabs"

    def __init__(self) -> None:
        self.api_key = settings.elevenlabs_api_key
        self.base_url = "https://api.elevenlabs.io/v1"

    async def healthcheck(self) -> bool:
        return bool(self.api_key and (settings.elevenlabs_voice_id))

    async def synthesize(self, text: str, voice_id: str | None = None) -> str:
        if not self.api_key:
            raise VoiceError("ELEVENLABS_API_KEY not set")
        vid = voice_id or settings.elevenlabs_voice_id
        if not vid:
            raise VoiceError("ELEVENLABS_VOICE_ID not set")
        text = (text or "").strip()[: settings.tts_max_chars]
        if not text:
            raise VoiceError("empty text for TTS")
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/text-to-speech/{vid}",
                headers={"xi-api-key": self.api_key, "accept": "audio/mpeg"},
                json={"text": text, "model_id": settings.elevenlabs_model_id},
            )
            resp.raise_for_status()
            audio = resp.content
        if not audio:
            raise VoiceError("elevenlabs returned empty audio")
        tmp = self._tempdir("eios-11l-")
        src = os.path.join(tmp, "voice.mp3")
        with open(src, "wb") as fh:
            fh.write(audio)
        ogg = await self.normalize_to_ogg(src, os.path.join(tmp, "voice.ogg"))
        self.delete_temporary_files(src)
        return ogg
