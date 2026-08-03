#!/bin/bash
# EIOS 一键部署脚本 — 使用根目录真实的 docker-compose.yml
set -e

REPO_URL="https://github.com/caicanghai/Codex-5.5--.git"
BRANCH="claude/eios-repository-foundation-hoi3u8"
DIR="Codex-5.5--"

echo "🚀 EIOS 一键部署"
echo "================"

# --- 1. 检查 Docker ---
if ! command -v docker &> /dev/null; then
    echo "📦 安装 Docker..."
    curl -fsSL https://get.docker.com | sh
fi
echo "✅ Docker 已就绪"

# docker compose (v2) 还是 docker-compose (v1)?
if docker compose version &> /dev/null; then
    DC="docker compose"
elif command -v docker-compose &> /dev/null; then
    DC="docker-compose"
else
    echo "❌ 找不到 docker compose,请先安装"; exit 1
fi
echo "✅ 使用: $DC"

# --- 2. 拉代码 ---
if [ ! -d "$DIR" ]; then
    echo "📥 克隆代码..."
    git clone "$REPO_URL"
    cd "$DIR"
    git checkout "$BRANCH"
else
    cd "$DIR"
    echo "📥 更新代码..."
    git fetch origin "$BRANCH" && git checkout "$BRANCH" && git pull origin "$BRANCH"
fi

# --- 3. 配置 .env ---
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  已生成 .env,请填写必填项后再启动:"
    echo "    nano .env"
    echo ""
    echo "必填:"
    echo "  TELEGRAM_BOT_TOKEN  (从 @BotFather 获取)"
    echo "  TELEGRAM_OWNER_ID   (你的 Telegram 数字ID,发消息给 @userinfobot 获取)"
    echo "可选:"
    echo "  AI_API_KEY / AI_BASE_URL / AI_MODEL  (留空则用离线摘要)"
    echo "  WECOM_* / WECHAT_* / WHATSAPP_*      (对应渠道)"
    echo ""
    echo "填完后运行:  $DC up -d"
    exit 0
fi

# --- 4. 启动 ---
echo "🐳 构建并启动容器..."
$DC up -d --build

echo ""
echo "⏳ 等待启动 (20秒)..."
sleep 20

echo ""
echo "📊 服务状态:"
$DC ps

echo ""
echo "🩺 健康检查:"
curl -sf http://localhost:8000/health && echo " ✅ API 正常" || echo " ⚠️  API 还没起来,查看日志: $DC logs api"

echo ""
echo "✨ 完成! 常用命令:"
echo "  $DC logs -f api      # 看API日志"
echo "  $DC logs -f bot      # 看Telegram bot日志"
echo "  $DC ps               # 看状态"
echo "  $DC down             # 停止"
