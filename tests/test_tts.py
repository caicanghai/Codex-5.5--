import asyncio
import os
import shutil
import subprocess
import tempfile

import pytest

from app.pipeline.tts import TTSError, _to_ogg_opus, synthesize_voice

HAS_FFMPEG = shutil.which("ffmpeg") is not None


def test_empty_text_raises():
    with pytest.raises(TTSError):
        asyncio.run(synthesize_voice("   "))


@pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg not installed")
def test_transcode_produces_ogg_opus():
    d = tempfile.mkdtemp()
    try:
        mp3 = os.path.join(d, "in.mp3")
        ogg = os.path.join(d, "out.ogg")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
             "-c:a", "libmp3lame", mp3],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        asyncio.run(_to_ogg_opus(mp3, ogg))
        assert os.path.getsize(ogg) > 0
        codec = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=codec_name", "-of", "default=nw=1:nk=1", ogg],
            capture_output=True, text=True,
        ).stdout.strip()
        assert codec == "opus"
    finally:
        shutil.rmtree(d, ignore_errors=True)
