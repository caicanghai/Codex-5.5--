"""Live credential + API health checks. Run ON THE VPS where .env exists.

SECURITY: validates only whether each variable is present (by NAME) and whether
a real API request succeeds. It NEVER prints, logs, or returns any secret value.

Usage (on the VPS, inside the app container so it sees the env):
    docker compose exec bot python -m app.healthcheck_live
"""

from __future__ import annotations

import asyncio

import httpx

from app.config import settings
from app.messaging.registry import all_providers

REDACT = "<present>"


def _present(value: object) -> bool:
    if isinstance(value, int):
        return value != 0
    return bool(value)


def presence_report() -> list[tuple[str, bool]]:
    """(VAR_NAME, present?) — never the value."""
    checks: list[tuple[str, bool]] = [
        ("TELEGRAM_BOT_TOKEN", _present(settings.telegram_bot_token)),
        ("TELEGRAM_OWNER_ID", _present(settings.telegram_owner_id)),
        ("OPENAI_API_KEY/AI_API_KEY", _present(settings.ai_api_key)),
        ("AI_BASE_URL", _present(settings.ai_base_url)),
        ("AI_MODEL", _present(settings.ai_model)),
        ("FISH_AUDIO_API_KEY", _present(settings.fish_audio_api_key)),
        ("FISH_AUDIO_VOICE_ID", _present(settings.fish_audio_voice_id)),
        ("ELEVENLABS_API_KEY", _present(settings.elevenlabs_api_key)),
        ("WECOM_CORP_ID", _present(settings.wecom_corp_id)),
        ("WECOM_AGENT_ID", _present(settings.wecom_agent_id)),
        ("WECOM_SECRET", _present(settings.wecom_secret)),
        ("WECHAT_APP_ID", _present(settings.wechat_app_id)),
        ("WECHAT_APP_SECRET", _present(settings.wechat_app_secret)),
        ("WECHAT_TOKEN", _present(settings.wechat_token)),
        ("WHATSAPP_ACCESS_TOKEN", _present(settings.whatsapp_access_token)),
        ("WHATSAPP_PHONE_NUMBER_ID", _present(settings.whatsapp_phone_number_id)),
        ("WHATSAPP_VERIFY_TOKEN", _present(settings.whatsapp_verify_token)),
    ]
    return checks


async def _ai_check() -> str:
    if not settings.ai_api_key:
        return "skipped (no key)"
    try:
        async with httpx.AsyncClient(timeout=20.0) as c:
            r = await c.get(
                f"{settings.ai_base_url.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {settings.ai_api_key}"},
            )
        return "ok" if r.status_code == 200 else f"fail (HTTP {r.status_code})"
    except Exception as exc:  # noqa: BLE001
        return f"fail ({type(exc).__name__})"


async def _fish_check() -> str:
    if not settings.fish_audio_api_key:
        return "skipped (no key)"
    try:
        async with httpx.AsyncClient(timeout=20.0) as c:
            r = await c.get(
                f"{settings.fish_audio_base_url.rstrip('/')}/model",
                headers={"Authorization": f"Bearer {settings.fish_audio_api_key}"},
                params={"page_size": 1},
            )
        return "ok" if r.status_code == 200 else f"fail (HTTP {r.status_code})"
    except Exception as exc:  # noqa: BLE001
        return f"fail ({type(exc).__name__})"


async def _telegram_check() -> str:
    if not settings.telegram_bot_token:
        return "skipped (no token)"
    try:
        async with httpx.AsyncClient(timeout=20.0) as c:
            r = await c.get(f"https://api.telegram.org/bot{settings.telegram_bot_token}/getMe")
        return "ok" if r.status_code == 200 and r.json().get("ok") else f"fail (HTTP {r.status_code})"
    except Exception as exc:  # noqa: BLE001
        return f"fail ({type(exc).__name__})"


async def _whatsapp_check() -> str:
    if not (settings.whatsapp_access_token and settings.whatsapp_phone_number_id):
        return "skipped (not configured)"
    try:
        async with httpx.AsyncClient(timeout=20.0) as c:
            r = await c.get(
                f"{settings.whatsapp_base_url.rstrip('/')}/{settings.whatsapp_phone_number_id}",
                headers={"Authorization": f"Bearer {settings.whatsapp_access_token}"},
                params={"fields": "id"},
            )
        return "ok" if r.status_code == 200 else f"fail (HTTP {r.status_code})"
    except Exception as exc:  # noqa: BLE001
        return f"fail ({type(exc).__name__})"


async def _provider_check(name: str) -> str:
    provider = all_providers()[name]
    if not provider.validate_config():
        return "skipped (not configured)"
    try:
        return "ok" if await provider.healthcheck() else "fail (auth)"
    except Exception as exc:  # noqa: BLE001
        return f"fail ({type(exc).__name__})"


async def run() -> int:
    print("== EIOS live health check (no secret values shown) ==\n")
    print("[Variable presence]")
    missing = []
    for name, present in presence_report():
        print(f"  {name}: {'present' if present else 'MISSING'}")
        if not present:
            missing.append(name)

    print("\n[Live API checks]")
    results = {
        "ai (openai/deepseek)": await _ai_check(),
        "fish_audio": await _fish_check(),
        "telegram": await _telegram_check(),
        "wecom": await _provider_check("wecom"),
        "wechat_official": await _provider_check("wechat_official"),
        "whatsapp": await _whatsapp_check(),
    }
    for comp, status in results.items():
        print(f"  {comp}: {status}")

    if missing:
        print(f"\nMissing variables (names only): {', '.join(missing)}")
    print("\nEnd-to-end voice/delivery: use the Telegram owner commands "
          "/channel_test <name>, /speak <text>, /broadcast <text>.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
