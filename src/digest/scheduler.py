"""定时调度：按 config.schedule.cron 每日触发 run_once。"""

from __future__ import annotations

import logging

from .config import load_config
from .runner import run_once

log = logging.getLogger(__name__)


def serve() -> None:
    cfg = load_config()
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        raise SystemExit("需要 apscheduler：pip install apscheduler")

    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(
        lambda: run_once(load_config()),
        CronTrigger.from_crontab(cfg.schedule_cron),
        id="daily_digest",
        misfire_grace_time=3600,
    )
    log.info("调度已启动，cron=%s（Asia/Shanghai）。Ctrl-C 退出。", cfg.schedule_cron)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("调度已停止")
