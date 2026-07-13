"""Telegram messaging provider (official Bot API via python-telegram-bot)."""

from __future__ import annotations

from telegram import Bot

from app.config import settings
from app.messaging.base import MessagingProvider


class TelegramProvider(MessagingProvider):
    name = "telegram"

    def validate_config(self) -> bool:
        return bool(settings.telegram_bot_token)

    def _bot(self) -> Bot:
        return Bot(settings.telegram_bot_token)

    @property
    def default_target(self) -> str:
        return str(settings.telegram_owner_id) if settings.telegram_owner_id else ""

    def _chat(self, to: str) -> str:
        return to or self.default_target

    async def send_text(self, to: str, text: str) -> None:
        await self._bot().send_message(chat_id=self._chat(to), text=text)

    async def send_image(self, to: str, path_or_url: str, caption: str = "") -> None:
        with open(path_or_url, "rb") as fh:
            await self._bot().send_photo(chat_id=self._chat(to), photo=fh, caption=caption or None)

    async def send_audio(self, to: str, path: str) -> None:
        with open(path, "rb") as fh:
            await self._bot().send_audio(chat_id=self._chat(to), audio=fh)

    async def send_file(self, to: str, path: str, filename: str | None = None) -> None:
        with open(path, "rb") as fh:
            await self._bot().send_document(chat_id=self._chat(to), document=fh, filename=filename)

    async def send_voice(self, to: str, ogg_path: str) -> None:
        with open(ogg_path, "rb") as fh:
            await self._bot().send_voice(chat_id=self._chat(to), voice=fh)
