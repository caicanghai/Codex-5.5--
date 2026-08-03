# 🚀 EIOS 部署指南（真实版）

**EIOS** = Evidence Intelligence & Omnichannel System
**当前形态**: 单体 FastAPI 应用（`app/`）+ Telegram bot，Docker Compose 编排
**渠道支持**: Telegram（最快）、企业微信、微信公众号、WhatsApp、OpenClaw

> ⚠️ **说明**: `docs/architecture/` 里的 25 个文档是**未来目标架构蓝图**（微服务、多租户 RLS 等），
> **不是当前代码的现状**。当前真实可跑的是本文件描述的单体 MVP。别把两者搞混。

---

## 📦 真实的仓库结构

```
Codex-5.5--/
├── docker-compose.yml          # ← 真实部署用这个（根目录，不在 deployments/）
├── .env.example                # ← 真实配置模板（根目录），复制成 .env
├── Dockerfile                  # api 和 bot 都用它构建
├── app/                        # ← 真实代码（单体）
│   ├── api/main.py            #   FastAPI: /health + /ingest + /webhook/*
│   ├── bot/                   #   Telegram bot
│   ├── pipeline/              #   处理管道（chat/summarize）
│   ├── messaging/            #   各渠道发送适配器
│   ├── voice/                #   TTS 语音合成
│   ├── config.py             #   环境变量配置
│   └── dispatch.py           #   消息路由（chat/summarize/workflow）
├── deployments/
│   ├── docker-compose.dev.yml  # 开发用（可选）
│   └── scripts/install.sh      # 一键部署脚本
└── docs/architecture/          # 未来蓝图（非现状）
```

**真实的容器**（`docker-compose.yml` 里只有 4 个）:
| 容器 | 作用 | 端口 |
|------|------|------|
| `db` | PostgreSQL 16 | 内部 5432 |
| `redis` | Redis 7 | 内部 6379 |
| `api` | FastAPI（health + webhook 接收） | **8000** |
| `bot` | Telegram bot 长轮询 | 无 |

---

## ⚡ 部署（在你的 VPS 上执行）

阿里云 ECS 网页控制台点「远程连接」即可打开终端，不用自己装 ssh。

### 第 1 步：拉代码

```bash
cd /opt
git clone https://github.com/caicanghai/Codex-5.5--.git
cd Codex-5.5--
git checkout claude/eios-repository-foundation-hoi3u8
```

### 第 2 步：配置

```bash
cp .env.example .env
nano .env
```

**必填**:
```env
TELEGRAM_BOT_TOKEN=123456789:AA...     # 从 @BotFather 获取
TELEGRAM_OWNER_ID=你的数字ID            # 发消息给 @userinfobot 获取
```

**可选**（留空则用离线摘要，仍能跑通）:
```env
AI_API_KEY=sk-or-v1-...                # OpenRouter 免费key
AI_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL=llama-3.1-8b
```

**数据库密码**（建议改）:
```env
POSTGRES_PASSWORD=换成强密码
```

### 第 3 步：启动

```bash
# Docker Compose v2（较新，推荐）
docker compose up -d --build

# 如果是老的 v1
docker-compose up -d --build
```

### 第 4 步：验证

```bash
docker compose ps                       # 4个容器都应是 Up/healthy
curl http://localhost:8000/health       # 应返回 {"status":"ok"} 或类似
docker compose logs -f bot              # 看 Telegram bot 是否连上
```

**测试**: 在 Telegram 里给你的 bot 发条消息 → 应收到 AI 回复。

---

## 🔧 加渠道（企业微信 / 微信公众号 / WhatsApp）

这些渠道的「接收消息」回调需要**公网 HTTPS 地址**，所以要先有：
- 一个**备案域名**（企业微信要求备案主体一致），或
- 至少一个带 HTTPS 的公网入口（反向代理 + 证书）

### 回调地址（在各平台后台填）

| 渠道 | 回调 URL |
|------|----------|
| 企业微信 | `https://你的域名/webhook/wecom` |
| 微信公众号 | `https://你的域名/webhook/wechat` |
| WhatsApp | `https://你的域名/webhook/whatsapp` |
| OpenClaw | `https://你的域名/webhook/openclaw` |

### 企业微信配置（示例）

`.env` 里填:
```env
WECOM_ENABLED=true
WECOM_CORP_ID=ww...          # 我的企业 → CorpID
WECOM_AGENT_ID=...           # 应用 → AgentId
WECOM_SECRET=...             # 应用 → Secret
WECOM_TOKEN=...              # 接收消息 → Token
WECOM_AES_KEY=...            # 接收消息 → EncodingAESKey（43位）
```

改完重启:
```bash
docker compose up -d
```

> 企业微信后台点「保存」时会来验证你的回调 URL，所以要先启动服务、且域名能通 HTTPS。

---

## 🌐 配 HTTPS（用 Caddy 自动证书）

如果有域名，最省事的是加个 Caddy 容器自动申请 Let's Encrypt 证书。
在根目录建 `Caddyfile`:

```
你的域名 {
    reverse_proxy localhost:8000
}
```

然后单独跑 Caddy（或加进 compose）。域名解析到 `8.217.110.255` 后，
Caddy 会自动签发证书，`https://你的域名/webhook/wecom` 即可用。

> 没有备案域名时，企业微信这类渠道用不了。**先用 Telegram 跑通全链路**，域名备案下来再加。

---

## 📝 常用命令

```bash
docker compose ps                    # 状态
docker compose logs -f api           # API 日志
docker compose logs -f bot           # Telegram bot 日志
docker compose logs | grep -i error  # 找错误
docker compose restart api           # 重启 api
docker compose down                  # 停止全部
docker compose up -d --build         # 改代码后重建

# 进数据库
docker compose exec db psql -U eios -d eios

# 进 Redis
docker compose exec redis redis-cli
```

---

## 🆘 故障排查

| 症状 | 原因 | 解决 |
|------|------|------|
| `bot` 容器反复重启 | `TELEGRAM_BOT_TOKEN` 没填 | `.env` 里填上，`docker compose up -d` |
| API 连不上数据库 | 数据库还没 healthy | 等几秒，`docker compose logs db` 看状态 |
| Telegram 无回复 | token 错 / 网络 | `docker compose logs bot` 看报错 |
| 企业微信保存报错 | 回调 URL 不通/无 HTTPS/域名没备案 | 先确保公网 HTTPS 可达 |
| `no space left` | 磁盘满 | `docker system prune -a` |
| 端口 8000 被占 | 别的程序占用 | `.env` 里改 `API_PORT` |

---

## ✅ 部署完自检清单

- [ ] `docker compose ps` → db/redis/api/bot 四个都 Up
- [ ] `curl localhost:8000/health` → 返回正常
- [ ] Telegram 给 bot 发消息 → 有回复
- [ ] `.env` 已妥善保管（**不要提交到 git**，`.gitignore` 已忽略）
- [ ] （加渠道时）域名 HTTPS 可达 + 回调 URL 填对

---

## 📚 更多文档

- **项目概览**: `PROJECT_SUMMARY.md`
- **未来架构蓝图**: `docs/architecture/README.md`（注意：是设计目标，非现状）
- **配置详解**: `.env.example`（每项都有中文注释）

---

**先用 Telegram 跑通，再逐步加渠道。有报错贴日志。🚀**
