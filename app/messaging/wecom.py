"""Official WeCom / WeChat Official Account sender — PLACEHOLDER.

Reserved for the OFFICIAL WeCom/WeChat Official Account HTTP APIs only.
Personal-WeChat hooks, UI automation, and reverse-engineered login are
explicitly NOT used and will not be implemented here.
"""

from __future__ import annotations

from app.messaging.base import MessagingProvider


class WeComOfficialProvider(MessagingProvider):
    """Reserved placeholder — not implemented in this phase."""

    name = "wecom_official"

    async def send_text(self, to: str, text: str) -> None:
        raise NotImplementedError("Official WeCom sender is reserved for a future release")

    async def send_voice(self, to: str, ogg_path: str) -> None:
        raise NotImplementedError("Official WeCom sender is reserved for a future release")

    async def healthcheck(self) -> bool:
        return False


class WeChatOfficialProvider(MessagingProvider):
    """Reserved placeholder — official WeChat Official Account API only."""

    name = "wechat_official"

    async def send_text(self, to: str, text: str) -> None:
        raise NotImplementedError("Official WeChat sender is reserved for a future release")

    async def send_voice(self, to: str, ogg_path: str) -> None:
        raise NotImplementedError("Official WeChat sender is reserved for a future release")

    async def healthcheck(self) -> bool:
        return False
