"""Text-to-speech via edge-tts, transcoded to OGG/Opus for Telegram voice."""

from __future__ import annotations

import asyncio
import os
import tempfile

import edge_tts

from app.config import settings


class TTSError(RuntimeError):
    pass


async def _mp3(text: str, path: str) -> None:
    communicate = edge_tts.Communicate(text, settings.tts_voice)
    await communicate.save(path)


async def _to_ogg_opus(mp3_path: str, ogg_path: str) -> None:
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-i", mp3_path,
        "-c:a", "libopus", "-b:a", "48k", "-ar", "48000", "-ac", "1",
        ogg_path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0 or not os.path.exists(ogg_path) or os.path.getsize(ogg_path) == 0:
        raise TTSError(f"ffmpeg transcode failed: {stderr.decode(errors='ignore')[:500]}")


async def synthesize_voice(text: str) -> str:
    """Generate an OGG/Opus voice file and return its path. Caller deletes it."""
    text = (text or "").strip()[: settings.tts_max_chars]
    if not text:
        raise TTSError("empty text for TTS")

    tmpdir = tempfile.mkdtemp(prefix="eios-tts-")
    mp3_path = os.path.join(tmpdir, "voice.mp3")
    ogg_path = os.path.join(tmpdir, "voice.ogg")

    await _mp3(text, mp3_path)
    if not os.path.exists(mp3_path) or os.path.getsize(mp3_path) == 0:
        raise TTSError("edge-tts produced no audio")

    await _to_ogg_opus(mp3_path, ogg_path)
    os.remove(mp3_path)
    return ogg_path
