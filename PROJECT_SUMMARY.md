# 📱 EIOS 项目总结

**EIOS** = Evidence Intelligence & Omnichannel System  
**类型**: 多渠道AI消息处理平台  
**语言**: Python (FastAPI) + TypeScript (React) + Swift (iOS)  
**部署**: Docker Compose on Ubuntu VPS

> ⚠️ **现状说明（重要，接手前必读）**
> 本文档描述的是**目标产品愿景 + 未来架构蓝图**。
> **当前真实代码**是一个单体 FastAPI 应用（`app/` 目录）+ Telegram bot，Docker Compose 编排（根目录 `docker-compose.yml`，4 个容器：db/redis/api/bot）。
> 下文提到的微服务拆分（gateway/api/worker/scheduler 独立服务）、多租户 RLS、12 阶段管道、iOS 推送等，**属于蓝图，尚未实现**。
> 真实部署方式见 **`DEPLOYMENT.md`**。别把蓝图当现状。

---

## 🎯 项目目标（愿景）

构建一个**多租户、多渠道、智能证据处理平台**，用户可以通过Telegram、WhatsApp、WeChat、WeCom、iOS等多个渠道：
1. 发送信息/URL
2. 系统自动提取关键信息
3. 进行跨源验证、冲突检测、置信度评分
4. 智能匹配用户兴趣
5. 语音 + 文字广播回复

---

## 🏗️ 技术栈

| 层 | 技术 | 说明 |
|---|---|---|
| **前端** | React + TypeScript | 管理后台（web-admin） |
| **移动** | Swift | iOS应用 |
| **后端** | Python 3.11+ | FastAPI (异步框架) |
| **数据库** | PostgreSQL 15 | 行级安全（RLS）多租户隔离 |
| **缓存/队列** | Redis 7 | 12阶段管道队列 + 缓存 |
| **存储** | MinIO / S3 | 文档、媒体存储 |
| **容器化** | Docker & Compose | 一键部署 |
| **反向代理** | Caddy | TLS自动续期 |
| **CI/CD** | GitHub Actions | 自动测试、构建、扫描 |

---

## 🔄 核心流程（12阶段管道）

```
用户消息 (Telegram/WhatsApp/WeChat/WeCom/iOS)
    ↓
① Collect      — 收集并解析消息
    ↓
② Normalize    — 标准化文本格式
    ↓
③ Deduplicate  — 检查是否已处理过
    ↓
④ Document     — 存储为文档记录
    ↓
⑤ Extract      — LLM提取关键声明
    ↓
⑥ Resolve      — 链接到知识库
    ↓
⑦ CrossValidate — 跨源验证
    ↓
⑧ DetectConflict — 检测矛盾
    ↓
⑨ Score        — 评分置信度
    ↓
⑩ Summarize    — 生成摘要
    ↓
⑪ InterestMatch — 匹配用户兴趣
    ↓
⑫ Broadcast    — 语音+文字广播回复
    ↓
多渠道推送（保证至少一次交付）
```

**特点**: 无跳过 — 每条消息必须经过全部12个阶段

---

## 🏢 系统架构

### **四层隔离**

1. **网关层** (Gateway) — Webhook接收、签名验证、消息入队
2. **API层** (API) — 租户API、用户管理、配置、历史查询
3. **工作层** (Worker) — 12阶段异步处理 (可横向扩展)
4. **数据层** (PostgreSQL + Redis + MinIO) — 多租户RLS隔离

### **多渠道支持**

```
Telegram ──┐
WhatsApp ──┤
WeChat ────┼──> 通用 ChannelAdapter 接口 ──> 统一处理
WeCom ─────┤
iOS Push ──┘
```

所有渠道使用**同一个适配器接口**，新增渠道无需改动Worker代码

---

## 🔐 多租户设计

**方案**: 共享数据库 + PostgreSQL 行级安全 (RLS)

```
┌─────────────────────────────────────┐
│  PostgreSQL (一个数据库)             │
├─────────────────────────────────────┤
│  RLS Policy: WHERE tenant_id = ?    │
│                                      │
│  tenants (多个租户)                  │
│  users (租户内的用户)                │
│  evidences (租户的证据)              │
│  ...                                 │
└─────────────────────────────────────┘
```

**隔离保证**:
- 数据库层: RLS强制隔离
- 应用层: 每个API请求都带租户ID
- 缓存层: Redis key前缀包含tenant_id
- 日志层: 所有日志记录tenant_id

---

## 📊 文件结构

```
Codex-5.5--/
├── docs/architecture/          # 完整架构蓝图（25个可交付成果）
├── services/                   # 4个微服务
│   ├── gateway/               # Webhook接收器
│   ├── api/                   # REST API
│   ├── worker/                # 12阶段处理
│   └── scheduler/             # 定时任务
├── packages/                   # 共享库（无独立executable）
│   ├── core/                  # 共享模型
│   ├── domain/                # DDD业务逻辑
│   ├── providers/             # AI/TTS/Search/Storage接口
│   ├── channels/              # 通道适配器
│   ├── infra/                 # DB/Cache/Queue
│   └── security/              # Auth/RBAC/Audit
├── apps/web-admin/            # 管理后台 (React/TS)
├── deployments/               # Docker Compose + 脚本
└── .github/workflows/         # CI/CD
```

---

## 🚀 快速部署

### **系统要求**
- Ubuntu 20.04+ (或任何Linux)
- 2核CPU, 4GB内存 (最小); 推荐 4核, 16GB+
- Docker + Docker Compose
- 备案域名 (可选，生产环境推荐)

### **部署步骤**

```bash
# 1. SSH到VPS
ssh root@your-vps-ip

# 2. 运行一键部署
curl -fsSL https://raw.githubusercontent.com/caicanghai/Codex-5.5--/claude/eios-repository-foundation-hoi3u8/deployments/scripts/install.sh | bash

# 3. 编辑配置
nano .env.prod
# 填入: POSTGRES_PASSWORD, TELEGRAM_BOT_TOKEN, AI_API_KEY等

# 4. 启动
docker-compose -f deployments/docker-compose.prod.yml up -d

# 完成！
```

**部署时间**: ~5分钟 (下载镜像 + 启动容器)

---

## 🔌 API 示例

### **发送消息**
```bash
curl -X POST http://localhost:8000/api/v1/broadcasts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "telegram",
    "user_id": "...",
    "message": "Breaking news about AI safety",
    "voice": true
  }'
```

### **查询历史**
```bash
curl http://localhost:8000/api/v1/history \
  -H "Authorization: Bearer <token>"
```

### **管理兴趣**
```bash
curl -X POST http://localhost:8000/api/v1/interests \
  -H "Authorization: Bearer <token>" \
  -d '{"topic": "AI Safety", "description": "..."}' 
```

完整API文档: `docs/openapi/openapi.json`

---

## 📈 扩展路线图

| 阶段 | 目标 | 预计 |
|------|------|------|
| **v0.1** | 平台骨架（空实现） | 2周 |
| **v0.2** | 身份 & 多租户 | 3周 |
| **v0.3** | 摄入 & 去重 | 2周 |
| **v0.4** | 证据智能 | 3周 |
| **v0.5** | 兴趣匹配 | 2周 |
| **v0.6** | Telegram端到端 | 2周 |
| **v0.7** | 语音 + 推送 | 2周 |
| **v0.8** | 多渠道 (WhatsApp/WeChat/WeCom) | 4周 |
| **v0.9** | 硬化 (监控/备份/安全) | 3周 |
| **v1.0** | GA (生产级) | 2周 |

**总计**: ~6个月从v0.1到v1.0生产版本

---

## 📚 文档

- **部署**: `DEPLOYMENT.md` ← **从这里开始**
- **架构**: `docs/architecture/README.md` (25个可交付成果)
- **API**: `/api/v1/openapi.json`
- **开发**: `Makefile`, `README.md`
- **ADR**: `docs/architecture/adr/`

---

## 🔍 关键特性

✅ **多租户隔离** (RLS) — 支持数千个小租户  
✅ **12阶段管道** — 无跳过、异步处理  
✅ **多渠道** — 一个接口支持所有平台  
✅ **提供者抽象** — AI/TTS/存储可插拔  
✅ **至少一次交付** — 幂等性 + 重试  
✅ **审计日志** — 完整追踪  
✅ **水平扩展** — 无状态Worker  
✅ **备份/灾恢** — nightly dumps + WAL  

---

## 🛠️ 开发栈

- **Linting**: ruff (快速Python linter)
- **Format**: black
- **Type Check**: mypy
- **Testing**: pytest
- **Package Manager**: Poetry / uv
- **CI/CD**: GitHub Actions

```bash
make lint          # 检查代码风格
make format        # 自动格式化
make test          # 运行测试
make dev           # 启动开发环境
```

---

## 👥 团队结构

- **架构师** → `docs/architecture/`
- **后端** → `services/`, `packages/`
- **前端** → `apps/web-admin/`
- **DevOps** → `deployments/`, `.github/workflows/`
- **iOS** → 单独仓库 (Swift)

---

## 📞 获取帮助

1. **架构问题** → 查看 `docs/architecture/README.md`
2. **部署问题** → 查看 `DEPLOYMENT.md` + 容器日志
3. **代码问题** → 查看 `services/*/README.md`
4. **ADR/决策** → `docs/architecture/adr/ADR-INDEX.md`

---

## 📄 许可证

待定 (TBD)

---

**准备好部署了？→ 查看 `DEPLOYMENT.md` 🚀**
