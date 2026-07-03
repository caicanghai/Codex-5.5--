"""配置加载：合并 config.yaml / sources.yaml / watchlist.yaml + 环境变量。

密钥一律从环境变量读取，绝不写进 yaml。缺失的密钥会让对应模块自动跳过并告警，
不会导致整体崩溃——这样即便你只填了一部分，系统也能先跑起来。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@dataclass
class Source:
    id: str
    type: str  # rss | telegram | wechat_rss
    weight: float = 1.0
    enabled: bool = True
    name: str = ""
    url: str = ""
    rss_url: str = ""
    channel: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def feed_url(self) -> str:
        """RSS 类源统一取 url 或 rss_url。"""
        return self.url or self.rss_url

    @property
    def is_ready(self) -> bool:
        """该源是否已具备可采集的最小信息。"""
        if self.type in {"rss", "wechat_rss"}:
            return bool(self.feed_url)
        if self.type == "telegram":
            return bool(self.channel)
        return False


@dataclass
class Config:
    schedule_cron: str = "0 9 * * *"
    lookback_hours: int = 26
    ranker: dict[str, Any] = field(default_factory=dict)
    summarizer: dict[str, Any] = field(default_factory=dict)
    notifiers: dict[str, Any] = field(default_factory=dict)
    sources: list[Source] = field(default_factory=list)
    watchlist: list[dict[str, Any]] = field(default_factory=list)
    db_path: str = "digest.db"

    # ---- 来自环境变量的密钥 ----
    @property
    def anthropic_api_key(self) -> str:
        return os.getenv("ANTHROPIC_API_KEY", "")

    @property
    def telegram_api_id(self) -> str:
        return os.getenv("TELEGRAM_API_ID", "")

    @property
    def telegram_api_hash(self) -> str:
        return os.getenv("TELEGRAM_API_HASH", "")

    @property
    def telegram_bot_token(self) -> str:
        return os.getenv("TELEGRAM_BOT_TOKEN", "")

    @property
    def telegram_chat_id(self) -> str:
        return os.getenv("TELEGRAM_CHAT_ID", "")

    @property
    def wecom_webhook(self) -> str:
        return os.getenv("WECOM_WEBHOOK", "")

    @property
    def serverchan_key(self) -> str:
        return os.getenv("SERVERCHAN_KEY", "")

    def ready_sources(self) -> list[Source]:
        return [s for s in self.sources if s.enabled and s.is_ready]


def load_config(config_dir: Path | None = None) -> Config:
    cfg_dir = config_dir or CONFIG_DIR
    main = _load_yaml(cfg_dir / "config.yaml")
    if not main:  # 允许直接用示例文件跑起来
        main = _load_yaml(cfg_dir / "config.example.yaml")
    sources_raw = _load_yaml(cfg_dir / "sources.yaml").get("sources", [])
    watchlist_raw = _load_yaml(cfg_dir / "watchlist.yaml").get("watchlist", [])

    sources: list[Source] = []
    for item in sources_raw:
        known = {"id", "type", "weight", "enabled", "name", "url", "rss_url", "channel"}
        sources.append(
            Source(
                id=item["id"],
                type=item["type"],
                weight=float(item.get("weight", 1.0)),
                enabled=bool(item.get("enabled", True)),
                name=item.get("name", ""),
                url=item.get("url", ""),
                rss_url=item.get("rss_url", ""),
                channel=item.get("channel", ""),
                extra={k: v for k, v in item.items() if k not in known},
            )
        )

    sched = main.get("schedule", {})
    return Config(
        schedule_cron=sched.get("cron", "0 9 * * *"),
        lookback_hours=int(sched.get("lookback_hours", 26)),
        ranker=main.get("ranker", {}),
        summarizer=main.get("summarizer", {}),
        notifiers=main.get("notifiers", {}),
        sources=sources,
        watchlist=watchlist_raw,
        db_path=main.get("db_path", "digest.db"),
    )
