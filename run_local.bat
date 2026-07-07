@echo off
REM 本地一键启动（Windows）。首次会建虚拟环境+装依赖+准备 .env，然后预览今日重点。
setlocal
cd /d "%~dp0"

echo ==> 1/4 创建虚拟环境 .venv
if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate.bat

echo ==> 2/4 安装依赖
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt

echo ==> 3/4 检查 .env
if not exist .env (
  copy .env.example .env >nul
  echo     已从模板生成 .env —— 请先编辑填入 token（至少 TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID）
  echo     填法见 docs\接入清单.md，填完再运行本脚本。
)

echo ==> 4/4 来源就绪情况 + 预览（不推送、不写库）
set PYTHONPATH=src
python -m digest sources
echo ------ 预览今日重点 ------
python -m digest preview

echo.
echo 满意后正式推送：  set PYTHONPATH=src ^&^& .venv\Scripts\python -m digest run
echo 常驻每日自动推：  set PYTHONPATH=src ^&^& .venv\Scripts\python -m digest serve
endlocal
