"""End-to-end launch self-test: Telegram -> AI -> Fish -> native voice.

Run ON THE VPS inside the app container (has .env + network):
    docker compose exec bot python -m app.launch_selftest

On success it delivers a real Telegram VOICE NOTE to TELEGRAM_OWNER_ID and prints
PASS. On failure it prints the exact failing step. Never prints secret values.
"""

from __future__ import annotations

import asyncio
import os

import httpx

from app.config import settings
from app.pipeline.chat import chat_reply
from app.voice.service import cleanup_paths, voice_service


def _line(step: str, ok: bool, detail: str = "") -> bool:
    print(f"[{'PASS' if ok else 'FAIL'}] {step}{(' — ' + detail) if detail else ''}")
    return ok


async def run() -> int:
    ok = True

    # 1. env presence (names only)
    print("== 1. environment ==")
    ok &= _line("TELEGRAM_BOT_TOKEN present", bool(settings.telegram_bot_token))
    owner_ok = _line("TELEGRAM_OWNER_ID set", bool(settings.telegram_owner_id))
    ok &= owner_ok
    _line("AI key present", bool(settings.ai_api_key))  # optional (fallback exists)
    _line("FISH_AUDIO_API_KEY present", bool(settings.fish_audio_api_key))  # optional (edge fallback)
    if not settings.telegram_bot_token or not owner_ok:
        print("\nBlocker: TELEGRAM_BOT_TOKEN and TELEGRAM_OWNER_ID are required.")
        return 1

    base = f"https://api.telegram.org/bot{settings.telegram_bot_token}"
    async with httpx.AsyncClient(timeout=30.0) as c:
        # 2. getMe
        print("\n== 2. Telegram getMe ==")
        try:
            r = await c.get(f"{base}/getMe")
            d = r.json()
            if d.get("ok"):
                u = d["result"]
                _line(f"getMe @{u.get('username')} id={u.get('id')}", True)
            else:
                return 1 if not _line("getMe", False, f"error_code={d.get('error_code')}") else 1
        except Exception as exc:  # noqa: BLE001
            _line("getMe", False, type(exc).__name__)
            return 1

        # 3. clear stale webhook (so polling is not blocked)
        print("\n== 3. webhook ==")
        try:
            info = (await c.get(f"{base}/getWebhookInfo")).json().get("result", {})
            if info.get("url"):
                await c.get(f"{base}/deleteWebhook", params={"drop_pending_updates": "true"})
                _line("stale webhook cleared", True)
            else:
                _line("no webhook set (polling ok)", True)
        except Exception as exc:  # noqa: BLE001
            _line("webhook check", False, type(exc).__name__)

        # 4. AI reply
        print("\n== 4. AI reply ==")
        reply = await chat_reply("晚上好")
        _line("AI/fallback reply", bool(reply), reply[:60])

        # 5. Fish -> voice synth
        print("\n== 5. voice synthesis ==")
        ogg = None
        try:
            ogg, provider = await voice_service.synthesize(reply, owner_id=settings.telegram_owner_id)
            size = os.path.getsize(ogg) if ogg and os.path.exists(ogg) else 0
            ok_v = _line(f"voice via {provider}", size > 0, f"{size} bytes OGG/Opus")
            ok &= ok_v
        except Exception as exc:  # noqa: BLE001
            _line("voice synthesis", False, type(exc).__name__)
            return 1

        # 6. deliver native Telegram voice note to owner
        print("\n== 6. native Telegram voice delivery ==")
        try:
            with open(ogg, "rb") as fh:
                files = {"voice": ("voice.ogg", fh.read(), "audio/ogg")}
            r = await c.post(
                f"{base}/sendVoice", data={"chat_id": settings.telegram_owner_id}, files=files
            )
            d = r.json()
            ok &= _line("sendVoice to owner", bool(d.get("ok")),
                        "check Telegram for a voice bubble" if d.get("ok") else str(d.get("error_code")))
        except Exception as exc:  # noqa: BLE001
            _line("sendVoice", False, type(exc).__name__)
            ok = False
        finally:
            cleanup_paths(ogg or "")

    print("\n== RESULT ==")
    print("PASS: full chain works (owner received a native voice note)." if ok
          else "FAIL: see the first [FAIL] above — that is the current blocker.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
