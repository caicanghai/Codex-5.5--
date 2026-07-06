"""命令行入口。

用法：
  python -m digest run           跑一次完整流程（会推送）
  python -m digest preview       只预览生成的每日重点，不写库不推送
  python -m digest serve         启动定时调度，按 cron 每日推送
  python -m digest sources       打印来源就绪情况（哪些已可采集/待补配置）
  python -m digest tg-chats      列出 bot 能看到的会话及 chat_id（帮你拿群 id）
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


def cmd_tgchats() -> None:
    """列出 bot 能看到的会话及其 chat_id（在你本机运行，帮你拿到群 id）。

    前提：已在 .env 或环境变量填 TELEGRAM_BOT_TOKEN；已把 bot 拉进目标群并在群里发过消息。
    """
    import os

    import httpx

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("❌ 没读到 TELEGRAM_BOT_TOKEN。先在 .env 填上再运行本命令。")
        return
    try:
        me = httpx.get(f"https://api.telegram.org/bot{token}/getMe", timeout=20).json()
        if not me.get("ok"):
            print(f"❌ token 无效：{me}")
            return
        print(f"✅ Bot 正常：@{me['result'].get('username')}")
        data = httpx.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=20).json()
    except Exception as exc:  # noqa: BLE001
        print(f"❌ 连不上 Telegram（本机需能访问 api.telegram.org）：{exc}")
        return

    chats: dict[int, str] = {}
    for upd in data.get("result", []):
        msg = upd.get("message") or upd.get("channel_post") or upd.get("my_chat_member") or {}
        chat = msg.get("chat")
        if chat:
            title = chat.get("title") or chat.get("username") or chat.get("first_name") or ""
            chats[chat["id"]] = f"{chat.get('type','')} · {title}"
    if not chats:
        print("⚠️ 还没看到任何会话。请把 bot 拉进目标群，在群里发一条消息（或 @它 一下），再运行一次本命令。")
        print("   提示：若群里发消息后仍看不到，去 BotFather 关掉 bot 的 Group Privacy，或把 bot 设为群管理员。")
        return
    print("\n找到以下会话，把目标群那行的 id 填进 .env 的 TELEGRAM_CHAT_ID：")
    for cid, desc in chats.items():
        print(f"   chat_id = {cid:>16}   {desc}")


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
    elif cmd in ("tg-chats", "tgchats", "tg"):
        cmd_tgchats()
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
