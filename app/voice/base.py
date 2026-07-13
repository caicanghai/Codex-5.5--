"""Voice provider interface and shared audio helpers."""

from __future__ import annotations

import abc
import asyncio
import os
import shutil
import tempfile


class VoiceError(RuntimeError):
    pass


class VoiceProvider(abc.ABC):
    """Transport-only TTS provider. No business logic beyond synthesis."""

    name: str = "base"

    @abc.abstractmethod
    async def synthesize(self, text: str, voice_id: str | None = None) -> str:
        """Return path to an OGG/Opus file. Caller deletes it."""

    @abc.abstractmethod
    async def healthcheck(self) -> bool:
        """Return True if the provider is usable (configured/reachable)."""

    @staticmethod
    async def normalize_to_ogg(src_path: str, ogg_path: str | None = None) -> str:
        """Transcode any audio file to OGG/Opus (Telegram voice format)."""
        if ogg_path is None:
            ogg_path = os.path.splitext(src_path)[0] + ".ogg"
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-i", src_path,
            "-c:a", "libopus", "-b:a", "48k", "-ar", "48000", "-ac", "1",
            ogg_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0 or not os.path.exists(ogg_path) or os.path.getsize(ogg_path) == 0:
            raise VoiceError(f"ffmpeg failed: {stderr.decode(errors='ignore')[:300]}")
        return ogg_path

    @staticmethod
    def delete_temporary_files(*paths: str) -> None:
        """Remove temp files/dirs, never raising."""
        for p in paths:
            if not p:
                continue
            try:
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                elif os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

    @staticmethod
    def _tempdir(prefix: str = "eios-voice-") -> str:
        return tempfile.mkdtemp(prefix=prefix)
