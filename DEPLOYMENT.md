# 🚀 EIOS 完整部署指南

**EIOS** = Evidence Intelligence & Omnichannel System  
**架构**: Python/FastAPI + PostgreSQL + Redis + Docker Compose  
**支持渠道**: Telegram, WhatsApp, WeChat, WeCom, iOS Push

---

## 📋 项目完整构造

```
eios/
├── docs/architecture/              # 完整架构蓝图（25个可交付成果）
├── deployments/
│   ├── docker-compose.prod.yml     # 生产部署配置
│   ├── docker-compose.dev.yml      # 开发配置
│   ├── env/.env.example            # 配置模板
│   └── scripts/                    # 备份/恢复脚本
├── services/
│   ├── gateway/                    # Webhook接收器 (FastAPI)
│   ├── api/                        # REST API (FastAPI)
│   ├── worker/                     # 12阶段管道处理 (async tasks)
│   └── scheduler/                  # 定时任务
├── packages/
│   ├── core/                       # 共享模型 (Tenant, User, Evidence)
│   ├── domain/                     # DDD业务逻辑
│   ├── providers/                  # 可插拔接口 (AI, TTS, Storage)
│   ├── channels/                   # 通道适配器
│   ├── infra/                      # 基础设施 (DB, Cache, Queue)
│   └── security/                   # Auth, RBAC, Audit
├── apps/
│   └── web-admin/                  # 管理后台 (React/TS)
├── .env.example                    # 环境变量示例
├── pyproject.toml                  # Python工作空间配置
├── Makefile                        # 开发任务
└── README.md                       # 快速开始
```

---

## ⚡ 一键部署（5分钟）

### **第1步: SSH连接到VPS**

```bash
ssh root@8.217.110.255
# 或用密钥: ssh -i your_key.pem root@8.217.110.255
```

### **第2步: 运行部署脚本**

```bash
curl -fsSL https://raw.githubusercontent.com/caicanghai/Codex-5.5--/claude/eios-repository-foundation-hoi3u8/deployments/scripts/install.sh | bash
```

或手动执行：

```bash
# 克隆代码
cd /opt
git clone https://github.com/caicanghai/Codex-5.5--.git
cd Codex-5.5--
git checkout claude/eios-repository-foundation-hoi3u8

# 配置环境
cp deployments/env/.env.example .env.prod
nano .env.prod  # 编辑配置（见下面的配置部分）

# 启动所有容器
docker-compose -f deployments/docker-compose.prod.yml up -d

# 验证
docker-compose -f deployments/docker-compose.prod.yml logs -f api
```

### **第3步: 验证部署**

```bash
# 检查所有容器运行状态
docker-compose -f deployments/docker-compose.prod.yml ps

# 测试API健康检查
curl http://localhost:8000/health

# 测试Gateway健康检查
curl http://localhost:8001/health
```

---

## 🔧 配置 (.env.prod)

```env
# ============== 必填项 ==============

# 数据库
POSTGRES_USER=eios
POSTGRES_PASSWORD=your_strong_password_here_min_20_chars
POSTGRES_DB=eios

# Telegram（测试用）
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_OWNER_ID=your_telegram_user_id

# AI模型（免费推荐）
AI_API_KEY=sk-or-v1-your_openrouter_key
AI_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL=llama-3.1-8b

# ============== 可选项（WeCom配置） ==============

WECOM_ENABLED=true
WECOM_CORP_ID=ww0b1b3e2c9a997135
WECOM_AGENT_ID=your_agent_id
WECOM_SECRET=your_secret
WECOM_TOKEN=your_token
WECOM_AES_KEY=your_aes_key

# ============== MinIO存储 ==============
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your_strong_password

# ============== API端口 ==============
API_PORT=8000
GATEWAY_PORT=8001
```

---

## 📊 容器拓扑

```
┌─────────────────────────────────────────┐
│  Caddy (反向代理 + TLS)                  │
│  :80 :443                               │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌─────────┐ ┌────────┐ ┌──────────┐
│Gateway  │ │  API   │ │ Workers  │
│:8001    │ │:8000   │ │ (×3)     │
└────┬────┘ └───┬────┘ └─────┬────┘
     │          │            │
     └──────────┼────────────┘
                │
        ┌───────┼────────┐
        ▼       ▼        ▼
    PostgreSQL Redis  MinIO
    (数据库)  (队列)  (存储)
```

---

## 🚀 启动后的操作

### **1. 验证Telegram集成**

```bash
# 找到你的Telegram用户ID
# 给 @userinfobot 发个消息，会返回你的ID

# 在你的Telegram里搜索你创建的Bot，发个消息
# 应该会收到API回复（或错误日志）

docker logs eios-gateway | grep -i telegram
```

### **2. 配置域名（可选，用于生产）**

如果有备案域名，编辑 `Caddyfile`：

```
your-domain.com {
  reverse_proxy localhost:8001 {
    uri /webhook/*
  }
  reverse_proxy localhost:8000 {
    uri /api/*
  }
  
  tls your_email@example.com {
    on_demand
  }
}
```

然后重启Caddy：
```bash
docker-compose restart proxy
```

### **3. 配置WeCom回调（如果启用）**

在企业微信后台 → 接收消息 → 设置API接收：

**URL**: `http://8.217.110.255:8001/webhook/wecom`  
**Token**: (从.env.prod中复制)  
**EncodingAESKey**: (从.env.prod中复制)

点保存 → 企业微信会验证你的URL

---

## 📝 常用命令

```bash
# 查看所有容器日志
docker-compose -f deployments/docker-compose.prod.yml logs -f

# 查看特定容器日志
docker-compose -f deployments/docker-compose.prod.yml logs -f api
docker-compose -f deployments/docker-compose.prod.yml logs -f gateway
docker-compose -f deployments/docker-compose.prod.yml logs -f worker

# 停止所有容器
docker-compose -f deployments/docker-compose.prod.yml down

# 重启容器
docker-compose -f deployments/docker-compose.prod.yml restart api

# 查看容器状态
docker-compose -f deployments/docker-compose.prod.yml ps

# 进入容器shell
docker exec -it eios-api /bin/bash

# 查看数据库
docker exec -it eios-postgres psql -U eios -d eios

# 备份数据库
docker exec eios-postgres pg_dump -U eios eios > backup_$(date +%Y%m%d).sql

# 查看Redis
docker exec -it eios-redis redis-cli
```

---

## 🔐 安全建议

- [ ] 更改所有默认密码（POSTGRES_PASSWORD, MINIO_ROOT_PASSWORD）
- [ ] 更改JWT密钥（若自定义）
- [ ] 启用TLS证书（Let's Encrypt via Caddy）
- [ ] 配置防火墙（只开放80/443端口）
- [ ] 定期备份数据库（见deployments/scripts/backup.sh）
- [ ] 监控日志（ECS CloudWatch或本地日志）

---

## 📊 架构文档

完整的架构设计文档在 `docs/architecture/` 目录：

- **README.md** — 25个可交付成果索引
- **00-context-and-containers.md** — C4系统设计
- **01-repository-architecture.md** — 代码结构
- **02-domain-model.md** — DDD域模型
- **03-data-model-erd.md** — 数据库设计 + RLS
- **04-evidence-pipeline.md** — 12阶段管道
- **05-queues-and-workers.md** — 队列和工作线程
- **06-gateway-and-channels.md** — 网关和通道适配器
- **08-api-auth-tenancy.md** — API设计、认证、多租户
- **09-deployment-and-scaling.md** — 部署和扩展
- **10-operations.md** — 监控、备份、灾恢
- **11-milestone-roadmap.md** — v0.1→v1.0路线图
- **adr/** — 架构决策记录（ADR-0001→ADR-0012）

---

## 🆘 故障排查

### **问题: API无法连接到PostgreSQL**
```bash
docker logs eios-api | grep -i "connection refused"
# 解决: 确保POSTGRES_PASSWORD在.env.prod中正确设置
docker-compose down
docker-compose up -d
```

### **问题: Telegram消息无法接收**
```bash
docker logs eios-gateway | grep -i "telegram"
# 解决: 检查TELEGRAM_BOT_TOKEN是否正确
# 检查你的Bot是否有webhook配置权限
```

### **问题: 磁盘满了**
```bash
df -h
# 解决: 清理Docker镜像 / 数据库备份转移到外部存储
docker system prune -a
```

---

## 📞 支持

- **架构问题**: 查看 `docs/architecture/`
- **部署问题**: 检查容器日志 `docker-compose logs`
- **代码问题**: 查看 `services/*/README.md`

---

**祝你部署顺利！🎉**
