"""Telegram bot (long polling): URL/RSS -> summary -> voice message."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
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
from app.pipeline.tts import synthesize_voice

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


async def on_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(WELCOME)


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

    await message.chat.send_action(ChatAction.RECORD_VOICE)
    ogg_path = None
    try:
        ogg_path = await synthesize_voice(result.summary)
        with open(ogg_path, "rb") as voice:
            await message.reply_voice(voice=voice)
    except Exception as exc:  # noqa: BLE001
        log.exception("tts/send failed")
        await message.reply_text(f"(Voice generation failed: {exc})")
    finally:
        if ogg_path and os.path.exists(ogg_path):
            shutil.rmtree(os.path.dirname(ogg_path), ignore_errors=True)


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
