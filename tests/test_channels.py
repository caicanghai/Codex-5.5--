import asyncio

import pytest

from app.channels import ChannelAdapter, WeChatChannelAdapter


def test_wechat_is_reserved_not_implemented():
    adapter = WeChatChannelAdapter()
    assert adapter.name == "wechat"
    with pytest.raises(NotImplementedError):
        asyncio.run(adapter.send_text("chat", "hi"))
    with pytest.raises(NotImplementedError):
        asyncio.run(adapter.send_voice("chat", "/tmp/x.ogg"))


def test_wechat_satisfies_channel_protocol():
    assert isinstance(WeChatChannelAdapter(), ChannelAdapter)
