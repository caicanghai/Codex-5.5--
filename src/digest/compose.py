"""把 Digest 组装成 Markdown 卡片。"""

from __future__ import annotations

from .models import Digest, Event

_CATEGORY_ORDER = ["漏洞与利用", "威胁情报", "工具与项目", "视频与教程", "其他"]


def compose_markdown(digest: Digest) -> str:
    lines: list[str] = [f"# 🛡️ 安全资讯每日重点 · {digest.date}", ""]

    if digest.top_highlights:
        lines.append("## 🔥 今日 TOP")
        for i, ev in enumerate(digest.top_highlights, 1):
            lines.append(f"{i}. **{ev.title}**")
            if ev.highlight_summary:
                lines.append(f"   {ev.highlight_summary}")
            lines.append(f"   〔{ev.source_name}〕[原文]({ev.url})")
        lines.append("")

    for cat in _CATEGORY_ORDER:
        evs = digest.by_category.get(cat)
        if not evs:
            continue
        lines.append(f"## {cat}")
        for ev in evs:
            summary = f" — {ev.highlight_summary}" if ev.highlight_summary else ""
            lines.append(f"- [{ev.title}]({ev.url}){summary} 〔{ev.source_name}〕")
        lines.append("")

    lines.append(
        f"---\n采集 {digest.total_collected} 条 · 去重后 {digest.total_after_dedup} 条 · "
        f"重点 {sum(len(v) for v in digest.by_category.values())} 条"
    )
    return "\n".join(lines)


def compose_plaintext(digest: Digest) -> str:
    """纯文本版（微信等不渲染 Markdown 的渠道用）。链接直接内联。"""
    lines: list[str] = [f"🛡️ 安全资讯每日重点 · {digest.date}", ""]

    if digest.top_highlights:
        lines.append("🔥 今日 TOP")
        for i, ev in enumerate(digest.top_highlights, 1):
            lines.append(f"{i}. {ev.title}")
            if ev.highlight_summary:
                lines.append(f"   {ev.highlight_summary}")
            lines.append(f"   〔{ev.source_name}〕{ev.url}")
        lines.append("")

    for cat in _CATEGORY_ORDER:
        evs = digest.by_category.get(cat)
        if not evs:
            continue
        lines.append(f"【{cat}】")
        for ev in evs:
            lines.append(f"· {ev.title}")
            lines.append(f"  〔{ev.source_name}〕{ev.url}")
        lines.append("")

    lines.append(
        f"—— 采集 {digest.total_collected} · 去重后 {digest.total_after_dedup} · "
        f"重点 {sum(len(v) for v in digest.by_category.values())}"
    )
    return "\n".join(lines)


def build_digest(date: str, tops: list[Event], ranked: list[Event],
                 total_collected: int, total_after_dedup: int) -> Digest:
    by_category: dict[str, list[Event]] = {}
    top_ids = {e.id for e in tops}
    for ev in ranked:
        if ev.id in top_ids:
            continue
        by_category.setdefault(ev.category, []).append(ev)
    return Digest(
        date=date,
        top_highlights=tops,
        by_category=by_category,
        total_collected=total_collected,
        total_after_dedup=total_after_dedup,
    )
