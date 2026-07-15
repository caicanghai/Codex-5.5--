"""OpenClaw (openclaw-weixin) provider — external WeChat bridge.

Treated as an EXTERNAL provider. Everything is implemented except reliance on a
live endpoint: the HTTP surface is fully coded and exercised against a mock
transport. Includes request/response serialization, retry with backoff,
timeout, streaming (SSE) parsing, and stream reconnect.
"""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncIterator

import httpx

from app.config import settings
from app.messaging.base import MessagingError, MessagingProvider
from app.messaging.media import to_amr

# ---- serializer ---------------------------------------------------------------


def serialize_request(prompt: str, *, model: str, session: str, stream: bool) -> dict:
    """Serialize a chat request to the OpenClaw wire format."""
    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": stream,
    }
    if session:
        payload["session"] = session
    return payload


def parse_response(data: dict) -> str:
    """Deserialize a non-streaming OpenClaw response to text."""
    if "choices" in data and data["choices"]:
        msg = data["choices"][0].get("message", {})
        if "content" in msg:
            return msg["content"] or ""
    return data.get("reply") or data.get("content") or ""


def parse_stream_line(line: str) -> str | None:
    """Parse one SSE line -> content delta, or None to skip. '' signals DONE."""
    line = line.strip()
    if not line or not line.startswith("data:"):
        return None
    body = line[len("data:") :].strip()
    if body == "[DONE]":
        return ""  # sentinel: end of stream
    try:
        obj = json.loads(body)
    except json.JSONDecodeError:
        return None
    if "choices" in obj and obj["choices"]:
        delta = obj["choices"][0].get("delta", {})
        return delta.get("content")
    return obj.get("content")


# ---- provider -----------------------------------------------------------------


class OpenClawProvider(MessagingProvider):
    name = "openclaw"

    def __init__(self) -> None:
        super().__init__()
        self.timeout = settings.openclaw_timeout_seconds
        self.retries = max(1, settings.openclaw_retry_attempts)

    def validate_config(self) -> bool:
        return bool(
            settings.openclaw_enabled
            and settings.openclaw_base_url
            and settings.openclaw_api_key
        )

    @property
    def default_target(self) -> str:
        return settings.openclaw_target or settings.openclaw_session or ""

    def _base(self) -> str:
        return settings.openclaw_base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {settings.openclaw_api_key}"}

    async def healthcheck(self) -> bool:
        if not self.validate_config():
            return False
        try:
            async with self._client(timeout=self.timeout) as c:
                r = await c.get(f"{self._base()}/healthz", headers=self._headers())
            return r.status_code == 200
        except Exception:
            return False

    # ---- retry + timeout ----
    async def _retry(self, factory):
        last: Exception | None = None
        for attempt in range(self.retries):
            try:
                return await factory()
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                last = exc
                if attempt < self.retries - 1:
                    await asyncio.sleep(min(2**attempt, 8) * 0.01)
        raise MessagingError(f"openclaw request failed: {type(last).__name__}")

    async def _post(self, path: str, *, json_body: dict | None = None, files=None, data=None) -> dict:
        async def call() -> dict:
            async with self._client(timeout=self.timeout) as c:
                r = await c.post(
                    f"{self._base()}{path}", headers=self._headers(),
                    json=json_body, files=files, data=data,
                )
                r.raise_for_status()
                return r.json()

        return await self._retry(call)

    # ---- chat (non-streaming) ----
    async def chat(self, prompt: str) -> str:
        payload = serialize_request(
            prompt, model=settings.openclaw_model, session=settings.openclaw_session, stream=False
        )
        data = await self._post("/v1/chat/completions", json_body=payload)
        return parse_response(data)

    # ---- chat (streaming + reconnect) ----
    async def chat_stream(self, prompt: str) -> AsyncIterator[str]:
        payload = serialize_request(
            prompt, model=settings.openclaw_model, session=settings.openclaw_session, stream=True
        )
        last: Exception | None = None
        for attempt in range(self.retries):  # reconnect on transient stream errors
            try:
                async with self._client(timeout=self.timeout) as c:
                    async with c.stream(
                        "POST", f"{self._base()}/v1/chat/completions",
                        headers=self._headers(), json=payload,
                    ) as resp:
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            delta = parse_stream_line(line)
                            if delta == "":
                                return
                            if delta:
                                yield delta
                        return
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                last = exc
                if attempt < self.retries - 1:
                    await asyncio.sleep(min(2**attempt, 8) * 0.01)
        raise MessagingError(f"openclaw stream failed: {type(last).__name__ if last else 'unknown'}")

    # ---- messaging ----
    async def send_text(self, to: str, text: str) -> None:
        await self._post(
            "/send",
            json_body={"session": to or self.default_target, "type": "text", "text": text},
        )

    async def _upload_media(self, path: str, media_type: str) -> str:
        with open(path, "rb") as fh:
            files = {"media": (os.path.basename(path), fh.read())}
        data = await self._post("/media", data={"type": media_type}, files=files)
        media_id = data.get("media_id") or data.get("id")
        if not media_id:
            raise MessagingError("openclaw media upload returned no id")
        return str(media_id)

    async def send_voice(self, to: str, ogg_path: str) -> None:
        """Fish Audio OGG -> WeChat-native voice adapter (AMR) -> openclaw send."""
        amr = await to_amr(ogg_path)
        try:
            media_id = await self._upload_media(amr, "voice")
            await self._post(
                "/send",
                json_body={"session": to or self.default_target, "type": "voice", "media_id": media_id},
            )
        finally:
            if os.path.exists(amr) and amr != ogg_path:
                os.remove(amr)
