#!/bin/bash
set -e

echo "🚀 EIOS 一键部署脚本"
echo "===================="

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，正在安装..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，正在安装..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

echo "✅ Docker已安装"

# 克隆代码（如果还没有）
if [ ! -d "Codex-5.5--" ]; then
    echo "📦 克隆EIOS代码..."
    git clone https://github.com/caicanghai/Codex-5.5--.git
    cd Codex-5.5--
    git checkout claude/eios-repository-foundation-hoi3u8
else
    cd Codex-5.5--
    echo "📥 更新EIOS代码..."
    git pull origin claude/eios-repository-foundation-hoi3u8
fi

# 配置环境
if [ ! -f ".env.prod" ]; then
    echo "⚙️  创建 .env.prod..."
    cp deployments/env/.env.example .env.prod

    echo ""
    echo "⚠️  请编辑 .env.prod 文件:"
    echo "   nano .env.prod"
    echo ""
    echo "必填项:"
    echo "  - POSTGRES_PASSWORD (20+ 字符)"
    echo "  - TELEGRAM_BOT_TOKEN (从 @BotFather 获取)"
    echo "  - AI_API_KEY (https://openrouter.ai)"
    echo ""
    echo "然后运行: docker-compose -f deployments/docker-compose.prod.yml up -d"
    exit 0
fi

echo "🐳 启动Docker容器..."
docker-compose -f deployments/docker-compose.prod.yml up -d

echo ""
echo "⏳ 等待容器启动..."
sleep 10

echo ""
echo "✅ 部署完成！"
echo ""
echo "📊 服务状态:"
docker-compose -f deployments/docker-compose.prod.yml ps
echo ""
echo "📝 日志:"
docker-compose -f deployments/docker-compose.prod.yml logs -f api &
sleep 5

echo ""
echo "✨ EIOS 已在运行！"
echo ""
echo "📍 接下来:"
echo "  1. API: http://localhost:8000/health"
echo "  2. Gateway: http://localhost:8001/health"
echo "  3. 查看日志: docker-compose -f deployments/docker-compose.prod.yml logs -f"
echo ""
echo "🎉 完成！"
