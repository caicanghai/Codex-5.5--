"""Audio format conversion helpers for channel media requirements."""

from __future__ import annotations

import asyncio
import os


async def _ffmpeg(*args: str) -> None:
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", *args,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    out = args[-1]
    if proc.returncode != 0 or not os.path.exists(out) or os.path.getsize(out) == 0:
        raise RuntimeError(f"ffmpeg failed: {stderr.decode(errors='ignore')[:200]}")


async def to_amr(src_path: str, out_path: str | None = None) -> str:
    """Convert to AMR-NB (WeCom / WeChat Official voice media)."""
    out_path = out_path or os.path.splitext(src_path)[0] + ".amr"
    await _ffmpeg("-i", src_path, "-ar", "8000", "-ac", "1", "-c:a", "libopencore_amrnb", "-b:a", "12.2k", out_path)
    return out_path


async def to_mp3(src_path: str, out_path: str | None = None) -> str:
    out_path = out_path or os.path.splitext(src_path)[0] + ".mp3"
    await _ffmpeg("-i", src_path, "-c:a", "libmp3lame", "-b:a", "64k", out_path)
    return out_path
