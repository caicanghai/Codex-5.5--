#!/usr/bin/env bash
# 本地一键启动（Mac/Linux）。首次会建虚拟环境+装依赖+准备 .env，然后预览今日重点。
set -e
cd "$(dirname "$0")"

echo "==> 1/4 创建虚拟环境 .venv"
[ -d .venv ] || python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> 2/4 安装依赖"
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "==> 3/4 检查 .env"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "    已从模板生成 .env —— 请先编辑填入 token（至少 TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID）"
  echo "    填法见 docs/接入清单.md，填完再运行本脚本。"
fi

echo "==> 4/4 来源就绪情况 + 预览（不推送、不写库）"
export PYTHONPATH=src
python -m digest sources
echo "------ 预览今日重点 ------"
python -m digest preview

echo
echo "满意后正式推送：  PYTHONPATH=src .venv/bin/python -m digest run"
echo "常驻每日自动推：  PYTHONPATH=src .venv/bin/python -m digest serve"
