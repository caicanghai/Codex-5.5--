"""Voice service: provider fallback + owner voice profile management."""

from __future__ import annotations

import asyncio
import logging
import os

from app.config import settings
from app.db import SessionLocal
from app.models import VoiceProfile
from app.voice.base import VoiceError, VoiceProvider
from app.voice.providers.edge import EdgeProvider
from app.voice.providers.elevenlabs import ElevenLabsProvider
from app.voice.providers.fish_audio import FishAudioProvider

log = logging.getLogger("eios.voice")

# Fixed fallback order: Fish Audio -> ElevenLabs -> Edge.
FALLBACK_ORDER = ["fish", "elevenlabs", "edge"]


class VoiceService:
    def __init__(self) -> None:
        self.providers: dict[str, VoiceProvider] = {
            "fish": FishAudioProvider(),
            "elevenlabs": ElevenLabsProvider(),
            "edge": EdgeProvider(),
        }

    # ---- profile persistence ----
    def get_profile(self, owner_id: int) -> VoiceProfile | None:
        with SessionLocal() as s:
            return s.query(VoiceProfile).filter_by(owner_id=owner_id).one_or_none()

    def save_profile(self, owner_id: int, provider: str, voice_id: str) -> None:
        with SessionLocal() as s:
            row = s.query(VoiceProfile).filter_by(owner_id=owner_id).one_or_none()
            if row is None:
                row = VoiceProfile(owner_id=owner_id, provider=provider, voice_id=voice_id)
                s.add(row)
            else:
                row.provider = provider
                row.voice_id = voice_id
            s.commit()

    def delete_profile(self, owner_id: int) -> bool:
        with SessionLocal() as s:
            row = s.query(VoiceProfile).filter_by(owner_id=owner_id).one_or_none()
            if row is None:
                return False
            s.delete(row)
            s.commit()
            return True

    # ---- synthesis with fallback ----
    async def synthesize(self, text: str, owner_id: int | None = None) -> tuple[str, str]:
        """Return (ogg_path, provider_name).

        If the owner has picked a voice (template or clone), that provider is
        tried FIRST so the chosen voice actually wins; otherwise the fixed
        fish -> elevenlabs -> edge fallback order applies.
        """
        profile = self.get_profile(owner_id) if owner_id else None
        order = list(FALLBACK_ORDER)
        if profile and profile.provider in self.providers:
            order = [profile.provider] + [n for n in order if n != profile.provider]
        last_err: Exception | None = None
        for name in order:
            provider = self.providers[name]
            voice_id = None
            if profile and profile.provider == name and profile.voice_id:
                voice_id = profile.voice_id
            try:
                if not await provider.healthcheck():
                    continue
                ogg = await provider.synthesize(text, voice_id=voice_id)
                return ogg, name
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                log.warning("voice provider %s failed: %s", name, exc)
                continue
        raise VoiceError(f"all voice providers failed: {last_err}")

    # ---- owner voice cloning (Fish Audio) ----
    async def set_owner_voice(self, owner_id: int, sample_ogg_path: str) -> tuple[str, str]:
        """Clone/update the owner's voice on Fish Audio; persist profile."""
        fish: FishAudioProvider = self.providers["fish"]  # type: ignore[assignment]
        if not await fish.healthcheck():
            raise VoiceError("Fish Audio is not configured (FISH_AUDIO_API_KEY missing)")
        voice_id = await fish.create_or_update_voice(sample_ogg_path, title=f"eios-{owner_id}")
        self.save_profile(owner_id, "fish", voice_id)
        return "fish", voice_id


async def probe_duration_seconds(path: str) -> float:
    """Return audio duration in seconds via ffprobe (0.0 on failure)."""
    proc = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", path,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
    )
    out, _ = await proc.communicate()
    try:
        return float(out.decode().strip())
    except (ValueError, AttributeError):
        return 0.0


def validate_sample(duration_s: float, size_bytes: int) -> str | None:
    """Return an error message if the sample is invalid, else None."""
    if duration_s < settings.voice_min_duration_seconds:
        return f"样本太短：需要 ≥ {settings.voice_min_duration_seconds}s（收到 {duration_s:.0f}s）"
    if duration_s > settings.voice_max_duration_seconds:
        return f"样本太长：需要 ≤ {settings.voice_max_duration_seconds}s（收到 {duration_s:.0f}s）"
    if size_bytes > settings.voice_max_upload_mb * 1024 * 1024:
        return f"文件过大：需要 ≤ {settings.voice_max_upload_mb}MB"
    return None


voice_service = VoiceService()


def cleanup_paths(*paths: str) -> None:
    VoiceProvider.delete_temporary_files(*[p for p in paths if p])
    # Also remove parent temp dirs.
    for p in paths:
        if p:
            d = os.path.dirname(p)
            if d and os.path.basename(d).startswith("eios-"):
                VoiceProvider.delete_temporary_files(d)
