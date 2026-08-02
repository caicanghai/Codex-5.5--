"""WeChat Official Account (微信公众号) provider — official API only.

No personal-WeChat hooks, desktop automation, or reverse-engineered login.
"""

from __future__ import annotations

import hashlib
import os
import time

from app.config import settings
from app.messaging.base import MessagingError, MessagingProvider
from app.messaging.media import to_amr
from app.messaging.wxcrypt import WXBizMsgCrypt


def wechat_encryption_configured() -> bool:
    """True when the OA is in encrypted/compatible mode (AES key present)."""
    return bool(settings.wechat_token and settings.wechat_aes_key and settings.wechat_app_id)


def wechat_crypter() -> WXBizMsgCrypt:
    """Build the WXBizMsgCrypt for WeChat OA inbound (receive_id = AppID)."""
    return WXBizMsgCrypt(settings.wechat_token, settings.wechat_aes_key, settings.wechat_app_id)


def verify_signature(token: str, signature: str, timestamp: str, nonce: str) -> bool:
    """Verify a WeChat Official Account webhook signature (sha1 of sorted args)."""
    if not token or not signature:
        return False
    raw = "".join(sorted([token, timestamp, nonce]))
    digest = hashlib.sha1(raw.encode()).hexdigest()  # noqa: S324 (WeChat spec mandates sha1)
    return digest == signature


def passive_text_reply(to_user: str, from_user: str, content: str) -> str:
    """Build a passive XML text reply for the webhook response."""
    ts = int(time.time())
    return (
        "<xml>"
        f"<ToUserName><![CDATA[{to_user}]]></ToUserName>"
        f"<FromUserName><![CDATA[{from_user}]]></FromUserName>"
        f"<CreateTime>{ts}</CreateTime>"
        "<MsgType><![CDATA[text]]></MsgType>"
        f"<Content><![CDATA[{content}]]></Content>"
        "</xml>"
    )


class WeChatOfficialProvider(MessagingProvider):
    name = "wechat_official"

    def __init__(self) -> None:
        super().__init__()
        self._token = ""
        self._token_exp = 0.0

    def validate_config(self) -> bool:
        return bool(
            settings.wechat_official_enabled
            and settings.wechat_app_id
            and settings.wechat_app_secret
        )

    def verify_webhook(self, signature: str, timestamp: str, nonce: str) -> bool:
        return verify_signature(settings.wechat_token, signature, timestamp, nonce)

    def _base(self) -> str:
        return settings.wechat_base_url.rstrip("/")

    async def _access_token(self) -> str:
        if self._token and time.time() < self._token_exp - 60:
            return self._token
        async with self._client() as c:
            r = await c.get(
                f"{self._base()}/cgi-bin/token",
                params={
                    "grant_type": "client_credential",
                    "appid": settings.wechat_app_id,
                    "secret": settings.wechat_app_secret,
                },
            )
            r.raise_for_status()
            data = r.json()
        if not data.get("access_token"):
            raise MessagingError(f"wechat token failed: errcode={data.get('errcode')}")
        self._token = data["access_token"]
        self._token_exp = time.time() + int(data.get("expires_in", 7200))
        return self._token

    async def healthcheck(self) -> bool:
        if not self.validate_config():
            return False
        try:
            return bool(await self._access_token())
        except Exception:
            return False

    async def _custom_send(self, payload: dict) -> None:
        token = await self._access_token()
        async with self._client() as c:
            r = await c.post(
                f"{self._base()}/cgi-bin/message/custom/send",
                params={"access_token": token}, json=payload,
            )
            r.raise_for_status()
            data = r.json()
        if data.get("errcode", 0) != 0:
            raise MessagingError(f"wechat custom send failed: errcode={data.get('errcode')}")

    async def _upload_media(self, path: str, media_type: str) -> str:
        token = await self._access_token()
        with open(path, "rb") as fh:
            files = {"media": (os.path.basename(path), fh.read())}
        async with self._client(timeout=60.0) as c:
            r = await c.post(
                f"{self._base()}/cgi-bin/media/upload",
                params={"access_token": token, "type": media_type}, files=files,
            )
            r.raise_for_status()
            data = r.json()
        if not data.get("media_id"):
            raise MessagingError(f"wechat media upload failed: errcode={data.get('errcode')}")
        return data["media_id"]

    async def send_text(self, to: str, text: str) -> None:
        await self._custom_send({"touser": to, "msgtype": "text", "text": {"content": text}})

    async def send_image(self, to: str, path_or_url: str, caption: str = "") -> None:
        media_id = await self._upload_media(path_or_url, "image")
        await self._custom_send({"touser": to, "msgtype": "image", "image": {"media_id": media_id}})

    async def send_audio(self, to: str, path: str) -> None:
        await self.send_voice(to, path)

    async def send_file(self, to: str, path: str, filename: str | None = None) -> None:
        media_id = await self._upload_media(path, "file")
        await self._custom_send({"touser": to, "msgtype": "file", "file": {"media_id": media_id}})

    async def send_voice(self, to: str, ogg_path: str) -> None:
        amr = await to_amr(ogg_path)
        try:
            media_id = await self._upload_media(amr, "voice")
            await self._custom_send({"touser": to, "msgtype": "voice", "voice": {"media_id": media_id}})
        finally:
            if os.path.exists(amr) and amr != ogg_path:
                os.remove(amr)
