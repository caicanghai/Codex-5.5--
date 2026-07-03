"""命令行入口。

用法：
  python -m digest run           跑一次完整流程（会推送）
  python -m digest preview       只预览生成的每日重点，不写库不推送
  python -m digest serve         启动定时调度，按 cron 每日推送
  python -m digest sources       打印来源就绪情况（哪些已可采集/待补配置）
"""

from __future__ import annotations

import logging
import sys

from .config import load_config
from .runner import run_once
from .scheduler import serve


def _load_env() -> None:
    """自动加载项目根目录 .env（若装了 python-dotenv）。"""
    try:
        from pathlib import Path

        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    except ImportError:
        pass


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_sources() -> None:
    cfg = load_config()
    ready = {s.id for s in cfg.ready_sources()}
    print(f"共 {len(cfg.sources)} 个来源，就绪 {len(ready)} 个：\n")
    for s in cfg.sources:
        if s.id in ready:
            flag = "✅"
        elif not s.enabled:
            flag = "🚫 已禁用"
        else:
            flag = "⏳ 待补配置"
        detail = s.feed_url or s.channel or "(需 rss_url/channel)"
        print(f"  {flag}  [{s.type:11}] {s.name or s.id:22} {detail}")


def main(argv: list[str] | None = None) -> int:
    _load_env()
    _setup_logging()
    args = argv if argv is not None else sys.argv[1:]
    cmd = args[0] if args else "preview"

    if cmd == "run":
        run_once(load_config(), dry_run=False)
    elif cmd == "preview":
        print(run_once(load_config(), dry_run=True))
    elif cmd == "serve":
        serve()
    elif cmd == "sources":
        cmd_sources()
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
