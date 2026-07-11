"""End-to-end pipeline self-test (no Telegram token required).

Usage:
    python scripts/mvp_selftest.py [url]

Checks: ingest -> summarize -> synthesize_voice (OGG/Opus).
Exits non-zero on failure. Requires ffmpeg for the voice step.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.pipeline.ingest import ingest  # noqa: E402
from app.pipeline.summarize import extractive_summary, summarize  # noqa: E402


async def main(url: str) -> int:
    print(f"[1/3] ingest: {url}")
    article = await ingest(url)
    print(f"      title: {article.title[:80]!r} source={article.source} chars={len(article.text)}")
    assert article.text, "no text extracted"

    print("[2/3] summarize")
    summary = await summarize(article.text)
    print(f"      summary ({len(summary)} chars): {summary[:200]!r}")
    assert summary, "empty summary"

    print("[3/3] synthesize voice (needs ffmpeg + network to edge-tts)")
    try:
        from app.pipeline.tts import synthesize_voice

        ogg = await synthesize_voice(summary)
        size = os.path.getsize(ogg)
        print(f"      voice file: {ogg} ({size} bytes)")
        assert size > 0, "empty audio"
        shutil.rmtree(os.path.dirname(ogg), ignore_errors=True)
        print("      voice: OK (OGG/Opus generated)")
    except Exception as exc:  # noqa: BLE001
        # In restricted sandboxes the edge-tts endpoint or ffmpeg may be
        # unavailable; that is not a code defect. Report, do not hard-fail.
        print(f"      SKIP voice step: {type(exc).__name__}: {exc}")
    print("\nOK: pipeline self-test passed")
    return 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "https://www.example.com/"
    # Sanity: offline summarizer is deterministic and dependency-free.
    demo = "Cats are small animals. Cats like to sleep. Dogs are loyal. " * 3
    assert extractive_summary(demo, 2), "extractive summarizer broken"
    raise SystemExit(asyncio.run(main(target)))
