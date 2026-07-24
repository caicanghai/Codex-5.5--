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

_BY_KEY = {t.key: t for t in TEMPLATES}


def by_key(key: str) -> VoiceTemplate | None:
    """Look up a template by its pick key (case-insensitive)."""
    return _BY_KEY.get((key or "").strip().lower())


def render_list() -> str:
    """Human-readable catalog for the /voice_list command."""
    lines = ["🎧 可选音色模板（发送 /voice_pick <编号> 选择）：", ""]
    for t in TEMPLATES:
        lines.append(f"• `{t.key}` — {t.label}（{t.lang}）")
    lines.append("")
    lines.append("选定后所有回复都会用这个声音。/voice_status 查看当前，/voice_delete 恢复默认。")
    return "\n".join(lines)
