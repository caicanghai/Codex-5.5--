"""编排整条流水线：采集 → 去重 → 打分 → 摘要 → 组装 → 推送。"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from .collectors import build_collector
from .compose import build_digest, compose_markdown
from .config import Config, load_config
from .models import Event
from .notifiers import build_notifiers
from .pipeline import Ranker, Summarizer, dedup
from .store import Store

log = logging.getLogger(__name__)


def run_once(cfg: Config | None = None, dry_run: bool = False) -> str:
    """执行一次完整流程，返回生成的 Markdown（便于预览/测试）。"""
    cfg = cfg or load_config()
    store = Store(cfg.db_path)
    since = datetime.now(timezone.utc) - timedelta(hours=cfg.lookback_hours)

    ready = cfg.ready_sources()
    log.info("可用来源 %d/%d 个", len(ready), len(cfg.sources))

    # 1) 采集
    collected: list[Event] = []
    for source in ready:
        collector = build_collector(source, cfg)
        if collector is None:
            continue
        try:
            raws = collector.fetch(since)
            for raw in raws:
                collected.append(Event.from_raw(raw, source.weight))
            store.set_cursor(source.id, datetime.now(timezone.utc))
            log.info("  %-24s 采集 %d 条", source.id, len(raws))
        except Exception as exc:  # noqa: BLE001
            log.warning("采集失败 %s: %s", source.id, exc)

    total_collected = len(collected)

    # 2) 去重（dry_run 不写状态库，避免污染）
    unique = dedup(collected, None if dry_run else store)
    total_after_dedup = len(unique)

    # 3) 打分筛选
    ranker = Ranker(cfg.ranker, cfg.watchlist)
    ranked = ranker.rank(unique)

    # 4) LLM 摘要 + 选 TOP
    summarizer = Summarizer(cfg.summarizer, cfg.anthropic_api_key)
    tops = summarizer.summarize(ranked)

    # 5) 组装
    date = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    digest = build_digest(date, tops, ranked, total_collected, total_after_dedup)
    markdown = compose_markdown(digest)

    # 6) 推送
    pushed = 0
    if not dry_run and not digest.is_empty:
        for notifier in build_notifiers(cfg):
            if notifier.send(digest, markdown):
                pushed += 1
                log.info("已推送 -> %s", notifier.channel_id)
        store.mark_pushed([e.id for e in ranked])

    if not dry_run:
        store.record_run(total_collected, total_after_dedup, pushed)
    log.info("完成：采集%d 去重后%d 重点%d 推送渠道%d",
             total_collected, total_after_dedup, len(ranked), pushed)
    return markdown
