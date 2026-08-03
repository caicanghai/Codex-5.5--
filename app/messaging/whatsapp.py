"""WhatsApp Business — Meta official Cloud API only.

Positioned as a notification / business / support channel, NOT a public
general-purpose AI chatbot.
"""

from __future__ import annotations

import os

from app.config import settings
from app.messaging.base import MessagingError, MessagingProvider
from app.messaging.audio_config import get_provider_codec


def verify_webhook(mode: str, token: str, challenge: str) -> str | None:
    """Return the challenge if the webhook verification matches, else None."""
    if mode == "subscribe" and token and token == settings.whatsapp_verify_token:
        return challenge
    return None


class WhatsAppProvider(MessagingProvider):
    name = "whatsapp"

    def validate_config(self) -> bool:
        return bool(
            settings.whatsapp_enabled
            and settings.whatsapp_access_token
            and settings.whatsapp_phone_number_id
        )

    @property
    def default_target(self) -> str:
        return settings.whatsapp_recipient or ""

    def _base(self) -> str:
        return f"{settings.whatsapp_base_url.rstrip('/')}/{settings.whatsapp_phone_number_id}"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {settings.whatsapp_access_token}"}

    def _to(self, to: str) -> str:
        return to or self.default_target

    async def _post(self, payload: dict) -> None:
        payload = {"messaging_product": "whatsapp", **payload}
        async with self._client() as c:
            r = await c.post(f"{self._base()}/messages", headers=self._headers(), json=payload)
            r.raise_for_status()
            data = r.json()
        if "error" in data:
            raise MessagingError(f"whatsapp send failed: {data['error'].get('code')}")

    async def _upload(self, path: str, mime: str) -> str:
        with open(path, "rb") as fh:
            files = {"file": (os.path.basename(path), fh.read(), mime)}
        data = {"messaging_product": "whatsapp", "type": mime}
        async with self._client(timeout=60.0) as c:
            r = await c.post(
                f"{self._base()}/media", headers=self._headers(), data=data, files=files
            )
            r.raise_for_status()
            body = r.json()
        if not body.get("id"):
            raise MessagingError(f"whatsapp media upload failed: {body}")
        return body["id"]

    async def send_text(self, to: str, text: str) -> None:
        await self._post({"to": self._to(to), "type": "text", "text": {"body": text}})

    async def send_template(self, to: str, name: str, lang: str = "en_US") -> None:
        await self._post({
            "to": self._to(to), "type": "template",
            "template": {"name": name, "language": {"code": lang}},
        })

    async def send_image(self, to: str, path_or_url: str, caption: str = "") -> None:
        media_id = await self._upload(path_or_url, "image/jpeg")
        await self._post({"to": self._to(to), "type": "image", "image": {"id": media_id, "caption": caption}})

    async def send_file(self, to: str, path: str, filename: str | None = None) -> None:
        media_id = await self._upload(path, "application/octet-stream")
        doc = {"id": media_id}
        if filename:
            doc["filename"] = filename
        await self._post({"to": self._to(to), "type": "document", "document": doc})

    async def send_audio(self, to: str, path: str) -> None:
        codec = get_provider_codec("whatsapp")
        encoded = await codec.encode(path)
        try:
            media_id = await self._upload(encoded, "audio/ogg")
            await self._post({"to": self._to(to), "type": "audio", "audio": {"id": media_id}})
        finally:
            if encoded != path and __import__("os").path.exists(encoded):
                __import__("os").remove(encoded)

    async def send_voice(self, to: str, ogg_path: str) -> None:
        await self.send_audio(to, ogg_path)
