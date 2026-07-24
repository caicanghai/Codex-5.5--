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

from app import cache
from app.config import settings
from app.db import ensure_schema
from app.messaging.registry import PRIORITY, all_providers, enabled_providers
from app.messaging.service import MessageRouter
from app.pipeline.chat import chat_reply
from app.pipeline.ingest import extract_url
from app.pipeline.service import process_url
from app.voice.service import (
    cleanup_paths,
    probe_duration_seconds,
    validate_sample,
    voice_service,
)
from app.voice.templates import add_custom as add_voice_template
from app.voice.templates import by_key as voice_template_by_key
from app.voice.templates import remove_custom as remove_voice_template
from app.voice.templates import render_list as render_voice_list

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger("eios.bot")

HEARTBEAT_FILE = "/tmp/bot_alive"

WELCOME = (
    "👋 EIOS bot.\n\n"
    "• 直接发消息（如“晚上好”）→ AI 回复 + 原生语音。\n"
    "• 发 URL / RSS 链接 → 摘要 + 语音。\n"
    "• /voice_list 看音色、/voice_pick <编号> 选定；/voice_add 随时加新音色。\n"
    "• /whoami 查看你的 Telegram ID（填 TELEGRAM_OWNER_ID 用）。"
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


SYNC_KEY = "eios:sync_enabled"


def sync_enabled() -> bool:
    try:
        return cache.get_client().get(SYNC_KEY) == "1"
    except Exception:
        return False


def set_sync(on: bool) -> None:
    try:
        cache.get_client().set(SYNC_KEY, "1" if on else "0")
    except Exception:
        pass


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


async def _reply_and_maybe_sync(update: Update, message, text: str) -> None:
    """Telegram voice reply to the requester; if owner + sync on, fan out the
    same text+voice to all other enabled channels. Voice generated ONCE, then
    converted per platform inside each provider. One channel failure is isolated.
    """
    owner = is_owner(update)
    ogg = None
    try:
        try:
            ogg, _prov = await voice_service.synthesize(
                text, owner_id=update.effective_user.id if owner else None
            )
        except Exception:
            ogg = None  # voice optional; text already delivered
        if ogg:
            await message.chat.send_action(ChatAction.RECORD_VOICE)
            with open(ogg, "rb") as voice:
                await message.reply_voice(voice=voice)
        if owner and sync_enabled():
            others = [p for p in enabled_providers() if p.name != "telegram"]
            if others:
                results = await MessageRouter(providers=others).broadcast(text, ogg)
                report = "\n".join(
                    f"- {r.channel}: {'ok' if r.ok else 'FAIL ' + r.detail}" for r in results
                )
                await message.reply_text("🔁 同步投递：\n" + report)
    finally:
        cleanup_paths(ogg or "")


async def on_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(WELCOME)


async def on_whoami(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply with the sender's own numeric Telegram id — auto-discovers
    TELEGRAM_OWNER_ID without needing a third-party bot. Only reveals the
    caller's own id, so it is open to anyone (no owner gate)."""
    if not update.message or not update.effective_user:
        return
    uid = update.effective_user.id
    await update.message.reply_text(
        f"你的 Telegram 数字 ID：`{uid}`\n"
        f"填入 .env 的 TELEGRAM_OWNER_ID={uid}",
        parse_mode="Markdown",
    )


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
    await update.message.reply_text("已删除语音配置，恢复默认回退音色。" if removed else "没有可删除的配置。")


async def on_voice_list(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """List selectable voice templates."""
    if not is_owner(update):
        return
    await update.message.reply_text(render_voice_list(), parse_mode="Markdown")


async def on_voice_pick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pick a voice template by key; persist it as the owner's voice."""
    if not is_owner(update):
        return
    key = (context.args[0] if context.args else "").strip()
    tpl = voice_template_by_key(key)
    if not tpl:
        await update.message.reply_text("未找到该模板。发送 /voice_list 查看可选编号。")
        return
    voice_service.save_profile(update.effective_user.id, tpl.provider, tpl.voice_id)
    await update.message.reply_text(
        f"✅ 已选择音色：{tpl.label}（{tpl.lang}）。\n发一句话试试，之后所有回复都会用这个声音。"
    )


async def on_voice_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a new voice template at runtime: /voice_add <provider> <voice_id> <name>."""
    if not is_owner(update):
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "用法：/voice_add <fish|elevenlabs|edge> <voice_id> <名字>\n"
            "例：/voice_add fish c51b2779becd499b81b635af3a5defef 我的音色"
        )
        return
    provider, voice_id, name = args[0], args[1], " ".join(args[2:])
    try:
        tpl = add_voice_template(provider, voice_id, label=name)
    except ValueError as exc:
        await update.message.reply_text(f"添加失败：{exc}")
        return
    await update.message.reply_text(
        f"✅ 已添加音色 `{tpl.key}` — {tpl.label}。\n用 /voice_pick {tpl.key} 选它。",
        parse_mode="Markdown",
    )


async def on_voice_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a custom voice template: /voice_remove <key>."""
    if not is_owner(update):
        return
    key = (context.args[0] if context.args else "").strip()
    if not key:
        await update.message.reply_text("用法：/voice_remove <编号>（仅能删自己添加的）。")
        return
    removed = remove_voice_template(key)
    await update.message.reply_text(
        f"已删除音色 `{key}`。" if removed else f"未找到可删除的自定义音色 `{key}`（内置模板不可删）。",
        parse_mode="Markdown",
    )


async def on_speak(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    text = " ".join(context.args) if context.args else ""
    if not text.strip():
        await update.message.reply_text("用法：/speak <文本>")
        return
    await _send_voice_for(update.message, text, update.effective_user.id)


async def on_channels(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    providers = all_providers()
    enabled = {p.name for p in enabled_providers()}
    lines = ["渠道状态："]
    for name in PRIORITY:
        configured = providers[name].validate_config()
        mark = "✅ enabled" if name in enabled else ("⚙️ configured" if configured else "❌ off")
        lines.append(f"- {name}: {mark}")
    await update.message.reply_text("\n".join(lines))


async def on_channel_status(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    lines = ["healthcheck："]
    for p in all_providers().values():
        try:
            ok = await p.healthcheck()
        except Exception:
            ok = False
        lines.append(f"- {p.name}: {'ok' if ok else 'unavailable'}")
    await update.message.reply_text("\n".join(lines))


async def on_channel_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    if not context.args:
        await update.message.reply_text("用法：/channel_test <telegram|wecom|wechat|whatsapp>")
        return
    key = context.args[0].strip().lower()
    alias = {"wechat": "wechat_official"}
    name = alias.get(key, key)
    providers = all_providers()
    if name not in providers:
        await update.message.reply_text(f"未知渠道：{key}")
        return
    provider = providers[name]
    if not provider.validate_config():
        await update.message.reply_text(f"{name}: 未配置，已跳过。")
        return
    try:
        await provider.send_text(provider.default_target, "EIOS channel test ✅")
        await update.message.reply_text(f"{name}: 已发送测试消息。")
    except Exception as exc:  # noqa: BLE001
        await update.message.reply_text(f"{name}: 发送失败 {type(exc).__name__}: {exc}")


async def on_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    text = " ".join(context.args) if context.args else ""
    if not text.strip():
        await update.message.reply_text("用法：/broadcast <文本>")
        return
    ogg = None
    try:
        try:
            ogg, _prov = await voice_service.synthesize(text, owner_id=update.effective_user.id)
        except Exception:
            ogg = None  # voice optional; never blocks text broadcast
        results = await MessageRouter().broadcast(text, ogg)
        if not results:
            await update.message.reply_text("没有已启用的渠道（检查 CHANNELS_ENABLED）。")
            return
        summary = "\n".join(f"- {r.channel}: {'ok' if r.ok else 'FAIL ' + r.detail}" for r in results)
        await update.message.reply_text("广播结果：\n" + summary)
    finally:
        cleanup_paths(ogg or "")


async def on_sync_on(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    set_sync(True)
    chans = ", ".join(p.name for p in enabled_providers()) or "(仅 telegram)"
    await update.message.reply_text(f"✅ 同步已开启。启用渠道：{chans}")


async def on_sync_off(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    set_sync(False)
    await update.message.reply_text("⏹️ 同步已关闭（仅回复 Telegram）。")


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

    await message.chat.send_action(ChatAction.TYPING)
    url = extract_url(message.text)

    if url:
        # URL/RSS → summary
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
        reply_text = result.summary
    else:
        # Plain text → AI chat reply (DeepSeek / OpenAI-compatible)
        reply_text = await chat_reply(message.text)
        try:
            await message.reply_text(reply_text)
        except Exception:
            pass

    await _reply_and_maybe_sync(update, message, reply_text)


def _md(text: str) -> str:
    # Minimal Markdown escaping for Telegram's legacy Markdown parser.
    for ch in ("_", "*", "`", "["):
        text = text.replace(ch, f"\\{ch}")
    return text


async def _post_init(app: Application) -> None:
    # Ensure long polling is not blocked by a stale webhook (409 Conflict).
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        log.info("cleared any stale webhook; long polling active")
    except Exception:
        log.exception("delete_webhook failed (continuing)")
    app.create_task(_heartbeat_loop())


async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Never let a handler exception cause silent no-reply; log it.
    log.error("handler error: %s", context.error, exc_info=context.error)


def build_application(token: str) -> Application:
    """Build the bot Application with handlers wired (no network I/O)."""
    application = Application.builder().token(token).post_init(_post_init).build()
    application.add_error_handler(_on_error)
    application.add_handler(CommandHandler("start", on_start))
    application.add_handler(CommandHandler("help", on_start))
    application.add_handler(CommandHandler("whoami", on_whoami))
    # Owner-only voice commands.
    application.add_handler(CommandHandler("voice_set", on_voice_set))
    application.add_handler(CommandHandler("voice_status", on_voice_status))
    application.add_handler(CommandHandler("voice_delete", on_voice_delete))
    application.add_handler(CommandHandler("voice_list", on_voice_list))
    application.add_handler(CommandHandler("voice_pick", on_voice_pick))
    application.add_handler(CommandHandler("voice_add", on_voice_add))
    application.add_handler(CommandHandler("voice_remove", on_voice_remove))
    application.add_handler(CommandHandler("speak", on_speak))
    # Owner-only channel commands.
    application.add_handler(CommandHandler("channels", on_channels))
    application.add_handler(CommandHandler("channel_status", on_channel_status))
    application.add_handler(CommandHandler("channel_test", on_channel_test))
    application.add_handler(CommandHandler("broadcast", on_broadcast))
    application.add_handler(CommandHandler("sync_on", on_sync_on))
    application.add_handler(CommandHandler("sync_off", on_sync_off))
    # Owner voice sample (after /voice_set).
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, on_voice_sample))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    return application


def main() -> None:
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set — cannot start the bot.")

    # DB init must NOT prevent the bot from starting/replying (item 6).
    try:
        ensure_schema()
    except Exception:
        log.exception("ensure_schema failed at startup (continuing; DB features degraded)")
    _touch_heartbeat()

    application = build_application(settings.telegram_bot_token)
    log.info("EIOS bot starting (long polling)…")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
