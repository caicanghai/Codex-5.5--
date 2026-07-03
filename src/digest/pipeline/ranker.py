"""打分与筛选：决定什么算「重点」。

score = 来源权重 + 关键词命中(watchlist + config) + 时效 + 跨源热度
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..models import Event


class Ranker:
    def __init__(self, ranker_cfg: dict, watchlist: list[dict]) -> None:
        self.top_n = int(ranker_cfg.get("top_n", 20))
        self.min_score = float(ranker_cfg.get("min_score", 2.0))
        # 合并 config.ranker.keyword_weights 与 watchlist 展开的权重
        self.keyword_weights: dict[str, float] = {}
        for kw, w in (ranker_cfg.get("keyword_weights") or {}).items():
            self.keyword_weights[kw.lower()] = float(w)
        for entry in watchlist or []:
            weight = float(entry.get("weight", 1))
            for alias in entry.get("aliases", []):
                self.keyword_weights[str(alias).lower()] = max(
                    self.keyword_weights.get(str(alias).lower(), 0), weight
                )

    def rank(self, events: list[Event]) -> list[Event]:
        # 跨源热度：相同标题指纹出现次数
        heat: dict[str, int] = {}
        for ev in events:
            key = ev.title[:20]
            heat[key] = heat.get(key, 0) + 1

        now = datetime.now(timezone.utc)
        for ev in events:
            score = ev.source_weight
            text = f"{ev.title} {ev.summary_raw}".lower()
            matched = []
            for kw, w in self.keyword_weights.items():
                if kw and kw in text:
                    score += w
                    matched.append(kw)
            ev.matched_keywords = matched

            # 时效：越新越高，最多 +2
            age_h = max(0.0, (now - ev.published_at).total_seconds() / 3600)
            score += max(0.0, 2.0 - age_h / 12.0)

            # 热度：被多源报道加分
            score += min(2.0, (heat.get(ev.title[:20], 1) - 1) * 1.0)

            ev.category = _categorize(ev, matched)
            ev.score = round(score, 3)

        ranked = sorted(events, key=lambda e: e.score, reverse=True)
        return [e for e in ranked if e.score >= self.min_score][: self.top_n]


def _categorize(ev: Event, matched: list[str]) -> str:
    text = f"{ev.title} {ev.summary_raw}".lower()
    if any(k in text for k in ["cve", "rce", "0day", "漏洞", "poc", "exp", "在野"]):
        return "漏洞与利用"
    if any(k in text for k in ["apt", "勒索", "ransom", "窃密", "stealer", "木马", "钓鱼", "供应链", "泄露"]):
        return "威胁情报"
    if any(k in text for k in ["github", "开源", "工具", "tool", "release", "框架"]):
        return "工具与项目"
    if any(k in text for k in ["视频", "教程", "复现", "实战", "youtube", "bilibili"]):
        return "视频与教程"
    return "其他"
