"""Voice templates: catalog lookup + that a picked provider is tried first."""

import asyncio

from app.voice import templates
from app.voice.service import FALLBACK_ORDER, VoiceService


def test_catalog_lookup_case_insensitive():
    assert templates.by_key("xiaoxiao") is not None
    assert templates.by_key("XIAOXIAO").voice_id == "zh-CN-XiaoxiaoNeural"
    assert templates.by_key("nope") is None


def test_render_list_mentions_pick_command():
    text = templates.render_list()
    assert "/voice_pick" in text
    assert "xiaoxiao" in text


def test_add_custom_rejects_bad_provider():
    import pytest

    with pytest.raises(ValueError):
        templates.add_custom("not-a-provider", "vid", "name")


def test_add_custom_rejects_empty_voice_id():
    import pytest

    with pytest.raises(ValueError):
        templates.add_custom("fish", "   ", "name")


def test_gen_key_avoids_collision_with_builtins(monkeypatch):
    # fish1 is a built-in; a new fish voice must get the next free key.
    monkeypatch.setattr(templates, "_custom_rows", lambda: [])
    assert templates._gen_key("fish") == "fish2"


def test_all_templates_merges_custom(monkeypatch):
    extra = templates.VoiceTemplate("mine", "fish", "abc123", "我的音色", "Fish")
    monkeypatch.setattr(templates, "_custom_rows", lambda: [extra])
    keys = {t.key for t in templates.all_templates()}
    assert "mine" in keys and "xiaoxiao" in keys
    assert templates.by_key("MINE").voice_id == "abc123"


def test_picked_provider_is_tried_first(monkeypatch):
    """A profile selecting 'edge' must make edge win even though fish is first
    in the fallback order."""
    svc = VoiceService()

    class _Profile:
        provider = "edge"
        voice_id = "zh-CN-XiaoxiaoNeural"

    monkeypatch.setattr(svc, "get_profile", lambda oid: _Profile())

    tried: list[str] = []

    async def _mk(name):
        async def healthcheck():
            return True

        async def synthesize(text, voice_id=None):
            tried.append(name)
            assert name != "edge" or voice_id == "zh-CN-XiaoxiaoNeural"
            return f"/tmp/{name}.ogg"

        p = svc.providers[name]
        monkeypatch.setattr(p, "healthcheck", healthcheck)
        monkeypatch.setattr(p, "synthesize", synthesize)

    for n in FALLBACK_ORDER:
        asyncio.run(_mk(n))

    ogg, provider = asyncio.run(svc.synthesize("hi", owner_id=42))
    assert provider == "edge"  # picked provider won, not fish
    assert tried == ["edge"]  # and nothing before it was attempted
