"""Curated voice templates the owner can browse and pick from.

`/voice_list` shows these; `/voice_pick <key>` selects one and persists it to
the owner's VoiceProfile. Once picked, VoiceService.synthesize() prefers that
provider + voice_id for every reply, on every channel.

Edge-TTS voices are the default catalog because they need no API key and always
work as the final fallback — so a picked template is guaranteed usable. Fish/
ElevenLabs voice ids can be added here too once those keys are configured.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceTemplate:
    key: str  # short pick id, e.g. "xiaoxiao"
    provider: str  # "edge" | "elevenlabs" | "fish"
    voice_id: str  # provider-specific voice identifier
    label: str  # human-friendly description
    lang: str  # display language tag


# Order = display order in /voice_list.
TEMPLATES: list[VoiceTemplate] = [
    # Owner-provided Fish Audio model (needs FISH_AUDIO_API_KEY on the VPS).
    VoiceTemplate("fish1", "fish", "c51b2779becd499b81b635af3a5defef", "Fish 精选音色①", "Fish"),
    VoiceTemplate("xiaoxiao", "edge", "zh-CN-XiaoxiaoNeural", "晓晓 · 温柔女声", "普通话"),
    VoiceTemplate("xiaoyi", "edge", "zh-CN-XiaoyiNeural", "晓伊 · 亲切女声", "普通话"),
    VoiceTemplate("yunxi", "edge", "zh-CN-YunxiNeural", "云希 · 沉稳男声", "普通话"),
    VoiceTemplate("yunyang", "edge", "zh-CN-YunyangNeural", "云扬 · 专业男声", "普通话"),
    VoiceTemplate("yunjian", "edge", "zh-CN-YunjianNeural", "云健 · 浑厚男声", "普通话"),
    VoiceTemplate("xiaobei", "edge", "zh-CN-liaoning-XiaobeiNeural", "晓北 · 东北女声", "方言"),
    VoiceTemplate("hiugaai", "edge", "zh-HK-HiuGaaiNeural", "曉佳 · 粤语女声", "粤语"),
    VoiceTemplate("hsiaochen", "edge", "zh-TW-HsiaoChenNeural", "曉臻 · 台湾女声", "国语"),
    VoiceTemplate("aria", "edge", "en-US-AriaNeural", "Aria · US female", "English"),
    VoiceTemplate("guy", "edge", "en-US-GuyNeural", "Guy · US male", "English"),
]

# Providers a template may reference.
VALID_PROVIDERS = {"fish", "elevenlabs", "edge"}


def _custom_rows() -> list[VoiceTemplate]:
    """Load runtime-added voices from the DB. Empty on any error so the catalog
    still works without a database (e.g. in unit tests)."""
    try:
        from app.db import SessionLocal
        from app.models import CustomVoice

        with SessionLocal() as s:
            rows = s.query(CustomVoice).order_by(CustomVoice.id).all()
            return [VoiceTemplate(r.key, r.provider, r.voice_id, r.label, r.lang) for r in rows]
    except Exception:
        return []


def all_templates() -> list[VoiceTemplate]:
    """Built-in catalog plus any runtime-added custom voices."""
    return TEMPLATES + _custom_rows()


def by_key(key: str) -> VoiceTemplate | None:
    """Look up a template by its pick key (case-insensitive), built-in or custom."""
    k = (key or "").strip().lower()
    for t in all_templates():
        if t.key == k:
            return t
    return None


def _gen_key(provider: str) -> str:
    """Pick the next free `<provider><n>` key not already in use."""
    existing = {t.key for t in all_templates()}
    i = 1
    while f"{provider}{i}" in existing:
        i += 1
    return f"{provider}{i}"


def add_custom(
    provider: str, voice_id: str, label: str = "", lang: str = "", key: str | None = None
) -> VoiceTemplate:
    """Add (or update by key) a custom voice template. Persists to the DB.

    Only a non-secret voice/model id is stored — never an API key.
    Raises ValueError on an invalid provider or empty voice id.
    """
    provider = (provider or "").strip().lower()
    if provider not in VALID_PROVIDERS:
        raise ValueError(f"provider 必须是 {sorted(VALID_PROVIDERS)} 之一")
    voice_id = (voice_id or "").strip()
    if not voice_id:
        raise ValueError("voice_id 不能为空")
    label = (label or "").strip()
    lang = (lang or "").strip() or provider
    key = (key or _gen_key(provider)).strip().lower()

    from app.db import SessionLocal
    from app.models import CustomVoice

    with SessionLocal() as s:
        row = s.query(CustomVoice).filter_by(key=key).one_or_none()
        if row is None:
            row = CustomVoice(
                key=key, provider=provider, voice_id=voice_id, label=label or key, lang=lang
            )
            s.add(row)
        else:
            row.provider, row.voice_id = provider, voice_id
            row.label = label or row.label
            row.lang = lang
        s.commit()
    return VoiceTemplate(key, provider, voice_id, label or key, lang)


def remove_custom(key: str) -> bool:
    """Delete a custom voice by key. Returns False if it was not found."""
    from app.db import SessionLocal
    from app.models import CustomVoice

    with SessionLocal() as s:
        row = s.query(CustomVoice).filter_by(key=(key or "").strip().lower()).one_or_none()
        if row is None:
            return False
        s.delete(row)
        s.commit()
        return True


def render_list() -> str:
    """Human-readable catalog for the /voice_list command."""
    lines = ["🎧 可选音色模板（发送 /voice_pick <编号> 选择）：", ""]
    for t in all_templates():
        lines.append(f"• `{t.key}` — {t.label}（{t.lang}）")
    lines.append("")
    lines.append(
        "选定后所有回复都会用这个声音。\n"
        "/voice_add <fish|elevenlabs|edge> <voice_id> <名字> 添加新音色；"
        "/voice_remove <编号> 删除；/voice_status 查看当前。"
    )
    return "\n".join(lines)
