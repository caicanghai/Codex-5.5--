"""WeCom (企业微信) self-built app provider — official API only."""

from __future__ import annotations

import os
import time

from app.config import settings
from app.messaging.base import MessagingError, MessagingProvider
from app.messaging.media import to_amr


class WeComProvider(MessagingProvider):
    name = "wecom"

    def __init__(self) -> None:
        super().__init__()
        self._token: str = ""
        self._token_exp: float = 0.0

    def validate_config(self) -> bool:
        return bool(
            settings.wecom_enabled
            and settings.wecom_corp_id
            and settings.wecom_secret
            and settings.wecom_agent_id
        )

    @property
    def default_target(self) -> str:
        return settings.wecom_target_user or ""

    def _base(self) -> str:
        return settings.wecom_base_url.rstrip("/")

    def _targets(self, to: str) -> dict:
        if to:
            return {"touser": to}
        t: dict = {}
        if settings.wecom_target_user:
            t["touser"] = settings.wecom_target_user
        if settings.wecom_target_party:
            t["toparty"] = settings.wecom_target_party
        if settings.wecom_target_tag:
            t["totag"] = settings.wecom_target_tag
        return t or {"touser": "@all"}

    async def _access_token(self) -> str:
        if self._token and time.time() < self._token_exp - 60:
            return self._token
        async with self._client() as c:
            r = await c.get(
                f"{self._base()}/cgi-bin/gettoken",
                params={"corpid": settings.wecom_corp_id, "corpsecret": settings.wecom_secret},
            )
            r.raise_for_status()
            data = r.json()
        if data.get("errcode", 0) != 0 or not data.get("access_token"):
            raise MessagingError(f"wecom gettoken failed: errcode={data.get('errcode')}")
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

    async def _post_message(self, payload: dict) -> None:
        token = await self._access_token()
        payload = {**payload, "agentid": int(settings.wecom_agent_id)}
        async with self._client() as c:
            r = await c.post(
                f"{self._base()}/cgi-bin/message/send", params={"access_token": token}, json=payload
            )
            r.raise_for_status()
            data = r.json()
        if data.get("errcode", 0) != 0:
            raise MessagingError(f"wecom send failed: errcode={data.get('errcode')}")

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
            raise MessagingError(f"wecom media upload failed: errcode={data.get('errcode')}")
        return data["media_id"]

    async def send_text(self, to: str, text: str) -> None:
        await self._post_message({**self._targets(to), "msgtype": "text", "text": {"content": text}})

    async def send_image(self, to: str, path_or_url: str, caption: str = "") -> None:
        media_id = await self._upload_media(path_or_url, "image")
        await self._post_message({**self._targets(to), "msgtype": "image", "image": {"media_id": media_id}})

    async def send_file(self, to: str, path: str, filename: str | None = None) -> None:
        media_id = await self._upload_media(path, "file")
        await self._post_message({**self._targets(to), "msgtype": "file", "file": {"media_id": media_id}})

    async def send_audio(self, to: str, path: str) -> None:
        await self.send_voice(to, path)

    async def send_voice(self, to: str, ogg_path: str) -> None:
        amr = await to_amr(ogg_path)
        try:
            media_id = await self._upload_media(amr, "voice")
            await self._post_message({**self._targets(to), "msgtype": "voice", "voice": {"media_id": media_id}})
        finally:
            if os.path.exists(amr) and amr != ogg_path:
                os.remove(amr)
