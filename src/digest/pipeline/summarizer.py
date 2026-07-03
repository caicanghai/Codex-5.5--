"""LLM 摘要：用 Claude 为候选事件生成中文重点摘要，并选出今日 TOP。

未配置 ANTHROPIC_API_KEY 或未安装 anthropic 时，自动降级：
用原始标题/摘要作为 highlight，按 score 取前 N 作为 TOP。系统照常出摘要。
"""

from __future__ import annotations

import json
import logging

from ..models import Event

log = logging.getLogger(__name__)


class Summarizer:
    def __init__(self, cfg: dict, api_key: str) -> None:
        self.model = cfg.get("model", "claude-haiku-4-5")
        self.top_highlights = int(cfg.get("top_highlights", 3))
        self.api_key = api_key

    def summarize(self, events: list[Event]) -> list[Event]:
        """就地填充 highlight_summary，返回 top_highlights 数量的重点事件。"""
        if not events:
            return []
        if not self.api_key:
            return self._fallback(events)
        try:
            return self._with_claude(events)
        except Exception as exc:  # noqa: BLE001
            log.warning("LLM 摘要失败，降级为原始摘要: %s", exc)
            return self._fallback(events)

    # ---- 降级：无 LLM ----
    def _fallback(self, events: list[Event]) -> list[Event]:
        for ev in events:
            ev.highlight_summary = (ev.summary_raw or ev.title)[:120]
        return events[: self.top_highlights]

    # ---- Claude ----
    def _with_claude(self, events: list[Event]) -> list[Event]:
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)
        payload = [
            {"idx": i, "title": ev.title, "source": ev.source_name,
             "summary": ev.summary_raw[:300]}
            for i, ev in enumerate(events)
        ]
        prompt = (
            "你是安全资讯编辑。下面是今日候选安全事件（JSON）。请：\n"
            "1) 为每条生成一句话中文重点摘要（不超过40字，聚焦影响与关键信息）；\n"
            "2) 选出最值得关注的 TOP" + str(self.top_highlights) + " 的 idx。\n"
            "只输出 JSON：{\"summaries\":{\"idx\":\"摘要\"},\"top\":[idx,...]}。\n\n"
            + json.dumps(payload, ensure_ascii=False)
        )
        resp = client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        data = _extract_json(text)
        summaries = data.get("summaries", {})
        for i, ev in enumerate(events):
            ev.highlight_summary = summaries.get(str(i)) or (ev.summary_raw or ev.title)[:120]
        top_idx = data.get("top", [])[: self.top_highlights]
        tops = [events[i] for i in top_idx if isinstance(i, int) and 0 <= i < len(events)]
        return tops or events[: self.top_highlights]


def _extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    return {}
