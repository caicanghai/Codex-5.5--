# EIOS 项目主控审计文档 · PROJECT MASTER AUDIT

> 本文档是 EIOS 项目的**唯一合并参考**（single consolidated reference）。
> 之前分散的 planning / architecture / roadmap / ADR / 临时状态内容在此汇总。
> 英文标识符、路径、命令、环境变量名、类名、分支名保持原文。
>
> 生成时间（UTC）：`20260712-065028`
> 对应提交（backup）：`e6d54768542a52e60ea572b530735ed87851da35`
> 仓库：`caicanghai/Codex-5.5--` · 默认分支 `main`

---

## 1. 产品目标 (Product objective)

EIOS（Evidence Intelligence & Omnichannel System，证据智能与全渠道系统）的长期目标是：从多渠道采集信息，进行证据抽取与交叉验证，按用户兴趣匹配，并通过多渠道（Telegram / WhatsApp / WeChat / 企业微信 / iOS）以文本与语音方式推送。

## 2. 当前可用 MVP 目标 (Current usable MVP objective)

今晚交付一个**可个人使用**的最小系统：Telegram 机器人接收 URL/RSS → AI 摘要 → edge-tts 生成语音 → 回发可播放的 Telegram 语音消息（OGG/Opus）。一条命令 `docker compose up -d` 启动。

## 3. 当前实现状态 (Current implementation status)

MVP 代码**已完成并通过本地验证**，尚未在 VPS 上完成部署（部署为下一步，需要用户提供 VPS 与密钥）。

## 4. 已完成的功能 (Features already completed)

- FastAPI 应用：`GET /health`、`POST /ingest`
- URL 抓取 + HTML 正文提取（`httpx` + `BeautifulSoup`）
- RSS 识别与解析（`feedparser`）
- AI 摘要：OpenAI 兼容接口，**无密钥时自动降级**为离线抽取式摘要
- edge-tts 语音合成 + `ffmpeg` 转码为 OGG/Opus
- Telegram 机器人（`python-telegram-bot`，长轮询 long polling）
- PostgreSQL 持久化（`items` 表，best-effort）
- Redis 健康探测
- Docker Compose 四服务编排 + 健康检查
- 运维脚本（deploy / start / update / backup / healthcheck / setup_swap）
- 预留 `WeChatChannelAdapter` 接口（未实现）

## 5. 已成功测试的功能 (Features tested successfully)

本地 `pytest` 共 **16 项通过**，另有针对性验证：

- `extract_url` / `extractive_summary`（单元）
- `ingest`：真实 RSS 与 HTML 页面（pypi.org）实测成功
- `POST /ingest` 与 `GET /health`（TestClient，mock 网络）
- Telegram `build_application` 装配 3 个 handler
- TTS：`ffmpeg` 将 MP3 转 OGG/Opus，`ffprobe` 确认 `codec=opus`（Telegram 语音兼容）
- `docker compose config` 校验通过
- Node 侧 `eslint` / `prettier` / `tsc` 通过

## 6. 尚未实现的功能 (Features not yet implemented)

VPS 实机部署验证、真实 Telegram 端到端收发、真实 AI 密钥调用、WeChat/WhatsApp/iOS 渠道、独立 worker 容器、Web Admin。

## 7. 仓库与分支策略 (Repository and branch strategy)

- 远端 `origin` = `https://github.com/caicanghai/Codex-5.5--`，默认分支 `main`
- 开发分支：`claude/eios-repository-foundation-hoi3u8`（MVP 所在）
- 本次清理分支：`chore/project-consolidation-cleanup`
- 备份分支/标签：`backup/pre-cleanup-20260712-065028`
- 兄弟分支（其他会话，勿动）：`claude/wechat-telegram-daily-digest-iwh9ul`
- 规则：不 force push、不删远端分支、不自动并入 `main`、不 `reset --hard`

## 8. 目录结构与说明 (Directory structure)

```
app/                    Python 后端（MVP 运行代码）
  api/main.py           FastAPI：/health、/ingest
  bot/main.py           Telegram 机器人（长轮询）
  pipeline/             ingest / summarize / tts / service
  channels.py           ChannelAdapter 协议 + 预留 WeChatChannelAdapter
  config.py db.py models.py cache.py
tests/                  pytest 测试（test_*.py）
scripts/mvp_selftest.py 离线管线自测
scripts/ops/*.sh        运维脚本
Dockerfile              python:3.12-slim + ffmpeg
docker-compose.yml      MVP 编排：db / redis / api / bot
requirements*.txt pyproject.toml   依赖与工具配置
.env.example            环境变量模板（无密钥）
.github/workflows/      ci.yml / python-ci.yml / secret-scan.yml
docs/                   本主控文档 + SECURITY.md、CONTRIBUTING.md +
                        已弃用规划文档（顶部加 DEPRECATED 横幅，见第 35 节）
（保留的 M0 脚手架）architecture/ packages/ apps/ services/ schemas/ workflows/ deployments/
（上游保留）codex-instruct.py examples/ assets/ README.md LICENSE
```

## 9. 后端架构 (Backend architecture)

Python 3.12 / FastAPI。管线：`ingest → summarize → (persist) → tts → deliver`。渠道适配器仅做传输，业务在 pipeline。Telegram 机器人直接调用 `app.pipeline`，无独立 worker 容器（MVP 简化）。

## 10. FastAPI 端点 (FastAPI endpoints)

- `GET /health` — 检查 DB + Redis，健康返回 200，否则 503
- `POST /ingest` — 请求体 `{ "url": "..." }`，返回 `{ id, url, title, summary, source }`

## 11. PostgreSQL 用途 (PostgreSQL usage)

存储 `items`（`id, url, title, summary, source, created_at`）。启动时 `ensure_schema()` 用 `Base.metadata.create_all` 建表（MVP 不强制跑 Alembic）。写入为 best-effort，不阻塞回复。

## 12. Redis 用途 (Redis usage)

健康探测（`ping`）；为未来缓存/限流预留。当前不承担核心逻辑。

## 13. Telegram Bot 工作流 (Telegram Bot workflow)

`/start`,`/help` 返回欢迎语；收到文本 → `extract_url` → `process_url`（抓取+摘要）→ 回文本 → `synthesize_voice` → `reply_voice`（OGG/Opus）。后台协程周期性写 `/tmp/bot_alive` 供容器健康检查。缺 `TELEGRAM_BOT_TOKEN` 时以清晰错误退出。

## 14. RSS / URL 采集工作流 (RSS and URL ingestion)

`_fetch` 抓取（`httpx`，跟随跳转，UA 头）→ 根据 content-type / 首部字节判断是否 feed；feed 用 `feedparser` 取首条，正文过短则回抓条目链接；否则 `_html_to_text` 用 `BeautifulSoup` 去除脚本样式并抽取 `<article>/<main>/<p>` 正文。

## 15. AI 摘要工作流 (AI summarization)

若配置密钥 → 调用 OpenAI 兼容 `/chat/completions`；异常或无密钥 → `extractive_summary`（词频抽取式）。永不因 AI 失败而中断管线。

## 16. TTS 与 OGG/Opus 工作流 (TTS and OGG/Opus)

`edge_tts.Communicate(text, voice).save(mp3)` → `ffmpeg -c:a libopus -b:a 48k -ar 48000 -ac 1` 转 `.ogg` → 经 `reply_voice` 发送；临时目录用后即删。

## 17. Docker Compose 服务 (Docker Compose services)

`db`(postgres:16-alpine)、`redis`(redis:7-alpine)、`api`(FastAPI)、`bot`(Telegram)。均含 healthcheck；`api`/`bot` 依赖 `db`/`redis` 健康后启动。**无独立 worker 容器**（bot 内处理）。`deployments/docker-compose.dev.yml` 为 M0 占位（含 MinIO/Directus/n8n），**MVP 不使用**。

## 18. 健康检查 (Health checks)

- `db`: `pg_isready`
- `redis`: `redis-cli ping`
- `api`: 请求 `http://localhost:8000/health`
- `bot`: 检查 `/tmp/bot_alive` 心跳新鲜度

## 19. 部署脚本 (Deployment scripts)

`scripts/ops/`：`deploy.sh`（建 `.env`→swap→`up -d --build`→等待健康）、`start.sh`、`update.sh`（`git pull` + rebuild + prune）、`backup.sh`（`pg_dump` → `backups/*.sql.gz`，保留 14 份）、`healthcheck.sh`（`--wait` 轮询）、`setup_swap.sh`（2GB swap）。

## 20. 环境变量名（仅名称，绝不含值） (Environment variable NAMES only)

`TELEGRAM_BOT_TOKEN`、`OPENAI_API_KEY`（或 `AI_API_KEY`）、`AI_BASE_URL`（或 `OPENAI_BASE_URL`）、`AI_MODEL`、`TTS_VOICE`、`POSTGRES_USER`、`POSTGRES_PASSWORD`、`POSTGRES_DB`、`API_PORT`、`DATABASE_URL`、`REDIS_URL`。

> ⚠️ 本文档、备份、提交、日志中**绝不包含任何实际值或密钥**。

## 21. 本地开发命令 (Local development commands)

```
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
```

## 22. 测试命令 (Test commands)

```
ruff check app scripts tests
pytest
python scripts/mvp_selftest.py <url>     # 离线管线自测
```

## 23. 部署命令 (Deployment commands)

```
cp .env.example .env    # 在 VPS 上填入密钥
docker compose up -d --build
bash scripts/ops/deploy.sh
```

## 24. 更新命令 (Update commands)

```
bash scripts/ops/update.sh     # git pull + rebuild + 健康检查
```

## 25. 备份与恢复命令 (Backup and restore commands)

```
bash scripts/ops/backup.sh                       # 数据库备份
git clone EIOS-full-<ts>.bundle EIOS-restored    # 从 bundle 恢复全history
git checkout backup/pre-cleanup-<ts>             # 恢复清理前状态
```

## 26. 当前 VPS 目标配置 (Current VPS target)

Ubuntu 24.04 LTS，新加坡，1 vCPU / 2GB RAM / 25–40GB SSD，仅 Docker Compose，无 Kubernetes。目标用户 ≤ 3（常态 1）。2GB 内存需启用 swap 以防构建 OOM。

## 27. 当前 Telegram-first MVP 范围 (Telegram-first MVP scope)

Telegram 为**唯一活跃投递渠道**。其余渠道推迟。

## 28. 未来 owner-only 出站 WeChat 策略 (Future owner-only outbound WeChat)

仅预留 `WeChatChannelAdapter`（`app/channels.py`，抛 `NotImplementedError`）。未来实现应遵循同一 `ChannelAdapter` 协议，且渠道适配器不含业务逻辑。

## 29. 未来扩展 (Future expansion)

REST API 扩充、WhatsApp Cloud API、iOS/APNs、图像与短视频，均通过统一 `ChannelAdapter` 与 Provider 抽象扩展，不 fork 上游、不改渠道适配器业务边界。

## 30. 已知缺陷 (Known defects)

- 未做真实 VPS 端到端验证（受限于本环境无 daemon/外网）
- 无独立 worker，长文本处理在 bot 进程内同步执行（低负载可接受）
- Alembic 已列依赖但运行期用 `create_all`，未接迁移流程
- `docs/CONTRIBUTING.md` 中的分支模型（`mirror/openclaw→eios/main→develop`）**已弃用**，与当前 `main`/`claude/*` 实际不一致

## 31. 技术风险 (Technical risks)

2GB 内存构建可能 OOM（已用 swap 缓解）；edge-tts 依赖微软公网端点（沙箱被墙，VPS 正常）；`python-telegram-bot` 与 `httpx` 版本需锁定兼容（已 `httpx>=0.27,<0.28`）。

## 32. 安全风险 (Security risks)

仓库内**无已提交密钥**。`.env` 已被 `.gitignore` 覆盖。上游 `codex-instruct.py` 与 `examples/gpt5.5-unrestricted.md` 为上游“越狱”内容，非本项目功能，保留但不使用。**VPS root 密码此前在对话中暴露**（不在仓库内）——见第 39 节与末尾提醒。

## 33. 重复/冲突的历史指令 (Duplicate/conflicting historical instructions)

- 语言栈：M0 曾配置 TypeScript 工具链，后**最终决定后端用 Python**（TS 仅保留给未来 web-admin 与 CI）。
- 文档策略：先要求大量 architecture/ADR/roadmap，后**永久关闭规划阶段**，只做 MVP。
- 分支模型：`CONTRIBUTING.md` 的 `mirror/openclaw→eios/main→develop` 与实际 `main`+`claude/*` 冲突，以后者为准。

## 34. 当前生效的最终决定 (Final decisions in force)

1. 后端 = Python 3.12 / FastAPI（最终）
2. 仅交付 MVP，不做企业特性（RBAC/多租户/Admin 等）
3. Telegram 为唯一活跃渠道；WeChat 仅预留接口
4. 一条命令 `docker compose up -d` 启动，四服务
5. 部署目标 = 单台 Ubuntu 24.04 VPS + Docker Compose
6. 不 fork 上游、不改上游文件

## 35. 已弃用、不再指导开发的决定 (Deprecated decisions)

- M0 规划文档 `docs/{CHARTER,ARCHITECTURE,ROADMAP,DECISIONS,CODING_RULES,README}.md`：
  **保留但已在文件顶部加 DEPRECATED 横幅**，权威参考为本文档。之所以保留而非删除/归档，
  是因为审计发现它们仍被 11+ 个文件引用（`git grep` 证据），不满足“确认无用”标准。
- `mirror/openclaw→eios/main→develop` 分支模型
- MinIO/Directus/n8n/Kubernetes/多租户/RBAC 等 M0 规划范围（推迟）

## 36. 让当前 MVP 可用的确切下一步 (Exact next steps to make MVP usable)

1. 购买并登录 Ubuntu 24.04 VPS
2. 安装 Docker Engine + Compose plugin
3. `git clone -b claude/eios-repository-foundation-hoi3u8 <repo> eios && cd eios`
4. `cp .env.example .env`，在 VPS 上填入 `TELEGRAM_BOT_TOKEN`（可选 `OPENAI_API_KEY`）
5. `bash scripts/ops/deploy.sh`（含 swap + 构建 + 健康等待）
6. 向机器人发送一条 URL/RSS，确认收到可播放语音

## 37. Keep/Delete/Archive 审计 (见下方完整表)

见 [第 40 节 · 完整审计表](#40-完整-keepdeletearchive-审计表)。

## 38. GitHub 分支/提交/发布状态 (GitHub status)

- 分支：`main`（默认）、`claude/eios-repository-foundation-hoi3u8`（MVP，已推送）、`chore/project-consolidation-cleanup`（本次）、`backup/pre-cleanup-20260712-065028`
- 标签：`backup-pre-cleanup-20260712-065028`（本地；无其它 release 标签）
- Release：无
- MVP 最新提交：`e6d5476`

## 39. 若清理导致问题的恢复流程 (Recovery procedure)

```
# 1) 从备份分支/标签恢复被误动文件：
git checkout backup/pre-cleanup-20260712-065028 -- <path>
# 2) 或整体检出清理前状态：
git checkout backup/pre-cleanup-20260712-065028
# 3) 或从 bundle 完整恢复：
git clone <backup-dir>/EIOS-full-20260712-065028.bundle EIOS-restored
```

> 说明：本次清理**未删除任何源文件**，仅新增主控文档、为已弃用规划文档加横幅、清理未跟踪缓存。

---

## 40. 完整 Keep/Delete/Archive 审计表

分类：KEEP / DELETE / ARCHIVE / GENERATED / SECRET-RISK / UNKNOWN。

| 路径 / Path                                                                                                                                                                                            | 分类             | 证据 / 理由                                                                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------- | ------------------------------------------------------------------------------------------------------------ |
| `app/**`                                                                                                                                                                                               | KEEP             | MVP 运行入口，被 compose/tests 引用                                                                          |
| `tests/test_*.py`                                                                                                                                                                                      | KEEP             | 验证当前功能的测试                                                                                           |
| `scripts/mvp_selftest.py`, `scripts/ops/*.sh`                                                                                                                                                          | KEEP             | 部署与自测脚本                                                                                               |
| `Dockerfile`, `docker-compose.yml`, `.dockerignore`                                                                                                                                                    | KEEP             | 部署使用                                                                                                     |
| `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`                                                                                                                                           | KEEP             | 依赖/工具配置                                                                                                |
| `.env.example`, `deployments/.env.example`                                                                                                                                                             | KEEP             | 环境模板（无密钥）                                                                                           |
| `.github/workflows/ci.yml`, `python-ci.yml`, `secret-scan.yml`                                                                                                                                         | KEEP             | 活跃 CI 工作流                                                                                               |
| `.github/{CODEOWNERS,dependabot.yml,PULL_REQUEST_TEMPLATE.md,ISSUE_TEMPLATE/*}`                                                                                                                        | KEEP             | 治理文件                                                                                                     |
| `README.md`, `LICENSE`                                                                                                                                                                                 | KEEP             | 必需                                                                                                         |
| `docs/SECURITY.md`, `docs/CONTRIBUTING.md`                                                                                                                                                             | KEEP             | 安全/贡献，明确保留                                                                                          |
| `docs/PROJECT_MASTER_AUDIT.md`                                                                                                                                                                         | KEEP             | 本合并主控文档                                                                                               |
| TS 工具链：`package*.json`, `tsconfig*.json`, `eslint.config.mjs`, `.prettier*`, `.editorconfig`, `.nvmrc`, `commitlint.config.cjs`, `types/eios.d.ts`, `scripts/*.mjs`, `scripts/validate-compose.sh` | KEEP             | CI 使用；未来 web-admin                                                                                      |
| M0 脚手架：`architecture/`, `packages/`, `apps/`, `services/`, `schemas/`, `workflows/`, `deployments/`                                                                                                | KEEP             | 已文档化的基础结构，功能清晰，保守保留                                                                       |
| 上游：`codex-instruct.py`, `examples/`, `assets/`, `.devcontainer/`, `.vscode/`, `.github/workflows/python-app.yml Py配置`                                                                             | KEEP             | 上游文件，不改动上游；末者文件名畸形（非 `.yml`，GitHub 不执行），保留但记录                                 |
| `docs/CHARTER.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/DECISIONS.md`, `docs/CODING_RULES.md`, `docs/README.md`                                                                            | KEEP（弃用横幅） | 已弃用规划/架构/路线/ADR；精华并入本文档并加 DEPRECATED 横幅。仍被 11+ 文件引用，故不删除/归档（保守、可逆） |
| `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`                                                                                                                                                       | GENERATED        | 可再生缓存，从工作区清理（未被 git 跟踪）                                                                    |
| `.venv/`, `node_modules/`                                                                                                                                                                              | GENERATED        | 未跟踪；本任务验证期间保留，已被 `.gitignore` 覆盖                                                           |
| 任何 `.env` / 私钥 / token                                                                                                                                                                             | SECRET-RISK      | 仓库内无（未跟踪/不存在）；VPS 凭据仅在对话中，需轮换                                                        |
| （无）                                                                                                                                                                                                 | UNKNOWN          | 所有文件均可判定，无需归为 UNKNOWN                                                                           |
