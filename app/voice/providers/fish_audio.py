"""Fish Audio provider (primary): TTS + owner voice cloning."""

from __future__ import annotations

import os

import httpx

from app.config import settings
from app.voice.base import VoiceError, VoiceProvider


class FishAudioProvider(VoiceProvider):
    name = "fish"

    def __init__(self) -> None:
        self.api_key = settings.fish_audio_api_key
        self.base_url = settings.fish_audio_base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    async def healthcheck(self) -> bool:
        return bool(self.api_key)

    async def synthesize(self, text: str, voice_id: str | None = None) -> str:
        if not self.api_key:
            raise VoiceError("FISH_AUDIO_API_KEY not set")
        text = (text or "").strip()[: settings.tts_max_chars]
        if not text:
            raise VoiceError("empty text for TTS")
        ref = voice_id or settings.fish_audio_voice_id
        payload: dict = {"text": text, "format": "mp3"}
        if ref:
            payload["reference_id"] = ref
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/v1/tts", headers=self._headers(), json=payload
            )
            resp.raise_for_status()
            audio = resp.content
        if not audio:
            raise VoiceError("fish audio returned empty audio")
        tmp = self._tempdir("eios-fish-")
        src = os.path.join(tmp, "voice.mp3")
        with open(src, "wb") as fh:
            fh.write(audio)
        ogg = await self.normalize_to_ogg(src, os.path.join(tmp, "voice.ogg"))
        self.delete_temporary_files(src)
        return ogg

    async def create_or_update_voice(self, sample_path: str, title: str = "eios-owner") -> str:
        """Create a Fish Audio voice model from a sample; return its voice id."""
        if not self.api_key:
            raise VoiceError("FISH_AUDIO_API_KEY not set")
        with open(sample_path, "rb") as fh:
            files = {"voices": (os.path.basename(sample_path), fh.read(), "audio/ogg")}
        data = {"title": title, "type": "tts", "train_mode": "fast"}
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/model", headers=self._headers(), data=data, files=files
            )
            resp.raise_for_status()
            body = resp.json()
        voice_id = body.get("_id") or body.get("id") or body.get("reference_id")
        if not voice_id:
            raise VoiceError(f"fish audio did not return a voice id: {body}")
        return str(voice_id)
