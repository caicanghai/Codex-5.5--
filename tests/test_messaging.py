import asyncio

import pytest

from app.messaging.wecom import WeChatOfficialProvider, WeComOfficialProvider


def test_wecom_placeholder_not_implemented():
    p = WeComOfficialProvider()
    assert p.name == "wecom_official"
    assert asyncio.run(p.healthcheck()) is False
    with pytest.raises(NotImplementedError):
        asyncio.run(p.send_text("to", "hi"))


def test_wechat_placeholder_not_implemented():
    p = WeChatOfficialProvider()
    with pytest.raises(NotImplementedError):
        asyncio.run(p.send_voice("to", "/tmp/x.ogg"))
