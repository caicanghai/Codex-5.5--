"""Telegram diagnostic — getMe + getWebhookInfo + clear stale webhook.

Run on the VPS:
    docker compose exec bot python -m app.tg_doctor

Never prints the bot token.
"""

from __future__ import annotations

import asyncio

import httpx

from app.config import settings


async def run() -> int:
    token = settings.telegram_bot_token
    if not token:
        print("TELEGRAM_BOT_TOKEN: MISSING")
        return 1
    print("TELEGRAM_BOT_TOKEN: present")
    base = f"https://api.telegram.org/bot{token}"
    async with httpx.AsyncClient(timeout=20.0) as c:
        # getMe
        try:
            r = await c.get(f"{base}/getMe")
            data = r.json()
            if data.get("ok"):
                u = data["result"]
                print(f"getMe: ok  username=@{u.get('username')}  id={u.get('id')}")
            else:
                print(f"getMe: FAIL  error_code={data.get('error_code')}  (token invalid/revoked?)")
                return 2
        except Exception as exc:  # noqa: BLE001
            print(f"getMe: FAIL ({type(exc).__name__})")
            return 2

        # getWebhookInfo
        try:
            r = await c.get(f"{base}/getWebhookInfo")
            info = r.json().get("result", {})
            url = info.get("url") or ""
            print(f"getWebhookInfo: url={'<set>' if url else '<empty>'}  "
                  f"pending={info.get('pending_update_count', 0)}")
            if url:
                d = await c.get(f"{base}/deleteWebhook", params={"drop_pending_updates": "true"})
                print(f"deleteWebhook: {'ok' if d.json().get('ok') else 'FAIL'} "
                      "(long polling unblocked)")
        except Exception as exc:  # noqa: BLE001
            print(f"getWebhookInfo: FAIL ({type(exc).__name__})")
    print("\nIf getMe=ok and webhook empty, long polling can receive updates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
