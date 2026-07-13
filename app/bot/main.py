"""Telegram bot (long polling): URL/RSS -> summary -> voice message."""

from __future__ import annotations

import asyncio
import logging
import os
import time

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import settings
from app.db import ensure_schema
from app.pipeline.ingest import extract_url
from app.pipeline.service import process_url
from app.voice.service import (
    cleanup_paths,
    probe_duration_seconds,
    validate_sample,
    voice_service,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger("eios.bot")

HEARTBEAT_FILE = "/tmp/bot_alive"

WELCOME = (
    "👋 EIOS MVP bot.\n\n"
    "Send me a URL or an RSS feed link. I will read it, summarize it, "
    "and send you a voice message of the summary."
)


def _touch_heartbeat() -> None:
    try:
        with open(HEARTBEAT_FILE, "w") as fh:
            fh.write(str(time.time()))
    except Exception:
        pass


async def _heartbeat_loop() -> None:
    while True:
        _touch_heartbeat()
        await asyncio.sleep(20)


def is_owner(update: Update) -> bool:
    owner = settings.telegram_owner_id
    user = update.effective_user
    return bool(owner) and user is not None and user.id == owner


async def _send_voice_for(message, text: str, owner_id: int | None) -> None:
    """Generate cloned/fallback voice and send it. Never raises."""
    await message.chat.send_action(ChatAction.RECORD_VOICE)
    ogg = None
    try:
        ogg, provider = await voice_service.synthesize(text, owner_id=owner_id)
        with open(ogg, "rb") as voice:
            await message.reply_voice(voice=voice)
        log.info("voice sent via %s", provider)
    except Exception as exc:  # noqa: BLE001
        log.exception("voice generation failed")
        await message.reply_text(f"(Voice generation failed: {exc})")
    finally:
        cleanup_paths(ogg or "")


async def on_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(WELCOME)


async def on_voice_set(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    context.user_data["awaiting_voice_sample"] = True
    await update.message.reply_text(
        "🎙️ 请发送一段你的语音/音频样本 "
        f"（{settings.voice_min_duration_seconds}–{settings.voice_max_duration_seconds} 秒）。"
    )


async def on_voice_status(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    profile = voice_service.get_profile(update.effective_user.id)
    if profile:
        await update.message.reply_text(
            f"当前语音：provider={profile.provider} voice_id={profile.voice_id}"
        )
    else:
        await update.message.reply_text("未设置克隆语音；当前使用回退 TTS（Edge）。")


async def on_voice_delete(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    removed = voice_service.delete_profile(update.effective_user.id)
    await update.message.reply_text("已删除克隆语音配置。" if removed else "没有可删除的配置。")


async def on_speak(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    text = " ".join(context.args) if context.args else ""
    if not text.strip():
        await update.message.reply_text("用法：/speak <文本>")
        return
    await _send_voice_for(update.message, text, update.effective_user.id)


async def on_voice_sample(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Receive an owner voice sample after /voice_set."""
    if not is_owner(update) or not context.user_data.get("awaiting_voice_sample"):
        return
    context.user_data["awaiting_voice_sample"] = False
    message = update.message
    media = message.voice or message.audio
    if media is None:
        await message.reply_text("请发送语音或音频文件。")
        return

    size = getattr(media, "file_size", 0) or 0
    if size > settings.voice_max_upload_mb * 1024 * 1024:
        await message.reply_text(f"文件过大：需 ≤ {settings.voice_max_upload_mb}MB")
        return

    tmp = voice_service.providers["edge"]._tempdir("eios-sample-")
    raw = os.path.join(tmp, "sample.input")
    ogg = os.path.join(tmp, "sample.ogg")
    try:
        tg_file = await media.get_file()
        await tg_file.download_to_drive(raw)
        await voice_service.providers["edge"].normalize_to_ogg(raw, ogg)
        duration = getattr(media, "duration", None) or await probe_duration_seconds(ogg)
        err = validate_sample(float(duration), os.path.getsize(ogg))
        if err:
            await message.reply_text(f"⚠️ {err}")
            return
        _, voice_id = await voice_service.set_owner_voice(update.effective_user.id, ogg)
        await message.reply_text(f"✅ 语音已创建/更新（fish, voice_id={voice_id}）。")
    except Exception as exc:  # noqa: BLE001
        log.exception("voice_set failed")
        await message.reply_text(f"⚠️ 语音设置失败：{exc}")
    finally:
        if not settings.voice_sample_retention:
            cleanup_paths(raw, ogg)


async def on_message(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or not message.text:
        return

    url = extract_url(message.text)
    if not url:
        await message.reply_text("Please send a valid URL or RSS link (http/https).")
        return

    await message.chat.send_action(ChatAction.TYPING)
    status = await message.reply_text("🔎 Reading and summarizing…")

    try:
        result = await process_url(url)
    except Exception as exc:  # noqa: BLE001
        log.exception("processing failed")
        await status.edit_text(f"⚠️ Could not process that link: {exc}")
        return

    header = f"*{_md(result.title)}*\n\n{_md(result.summary)}"
    try:
        await status.edit_text(header, parse_mode="Markdown")
    except Exception:
        await status.edit_text(f"{result.title}\n\n{result.summary}")

    owner_id = update.effective_user.id if is_owner(update) else None
    await _send_voice_for(message, result.summary, owner_id)


def _md(text: str) -> str:
    # Minimal Markdown escaping for Telegram's legacy Markdown parser.
    for ch in ("_", "*", "`", "["):
        text = text.replace(ch, f"\\{ch}")
    return text


async def _post_init(app: Application) -> None:
    app.create_task(_heartbeat_loop())


def build_application(token: str) -> Application:
    """Build the bot Application with handlers wired (no network I/O)."""
    application = Application.builder().token(token).post_init(_post_init).build()
    application.add_handler(CommandHandler("start", on_start))
    application.add_handler(CommandHandler("help", on_start))
    # Owner-only voice commands.
    application.add_handler(CommandHandler("voice_set", on_voice_set))
    application.add_handler(CommandHandler("voice_status", on_voice_status))
    application.add_handler(CommandHandler("voice_delete", on_voice_delete))
    application.add_handler(CommandHandler("speak", on_speak))
    # Owner voice sample (after /voice_set).
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, on_voice_sample))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    return application


def main() -> None:
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set — cannot start the bot.")

    ensure_schema()
    _touch_heartbeat()

    application = build_application(settings.telegram_bot_token)
    log.info("EIOS bot starting (long polling)…")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
