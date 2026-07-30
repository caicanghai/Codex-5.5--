# EIOS 融合栈（EIOS + One API + n8n 一键部署）

一台服务器上同时跑三样，用一套 `docker-compose` 管理：

| 服务 | 作用 | 访问 |
| --- | --- | --- |
| **EIOS** | 微信/Telegram 语音助手（收消息 → AI → 语音回复） | `https://{EIOS_DOMAIN}` |
| **One API** | AI 中转中枢：统一管理 KIMI/DeepSeek/OpenAI 的 key，EIOS 的 AI 都走它 | `https://{ONEAPI_DOMAIN}` |
| **n8n** | 自动化工作流（定时任务、触发 EIOS 发消息等） | `https://{N8N_DOMAIN}` |
| Postgres / Redis | 共享数据层 | 仅内网 |
| Caddy | 反向代理 + 自动 HTTPS | 对外 80/443 |

数据流：**你(微信/TG) → EIOS → One API → KIMI/DeepSeek → EIOS 合成语音 → 发回你**。

---

## 部署步骤（在服务器上）

**1. 准备**：一台 2 核 4G+（跑这三样建议 4G 起，8G 舒服）的 VPS，Ubuntu 24.04，装好 Docker。
三个子域名（`eios.` / `oneapi.` / `n8n.`）都解析到服务器 IP（无域名见 `Caddyfile` 底部临时方案）。

**2. 拉代码 + 配置**

```bash
git clone <你的仓库地址> /root/eios && cd /root/eios/integration
cp .env.stack.example .env
nano .env          # 填 token、域名、各处密码/随机串
```

**3. 启动**

```bash
docker compose -f docker-compose.stack.yml up -d --build
docker compose -f docker-compose.stack.yml ps      # 看是否都 healthy
```

**4. 配 One API（让 EIOS 能调 KIMI）**

1. 打开 `https://{ONEAPI_DOMAIN}`，默认账号 `root` / 密码 `123456`（首次登录后**立刻改密码**）。
2. 「渠道」→ 新建 → 类型选 **Moonshot（KIMI）**，填你的 KIMI 官方 key，模型填 `moonshot-v1-8k`。
3. 「令牌」→ 新建一个令牌，复制它（形如 `sk-xxxx`）。
4. 把这个令牌填回 `.env` 的 `AI_API_KEY=`，然后 `docker compose -f docker-compose.stack.yml up -d` 重启。

> 之后想加 DeepSeek/OpenAI，只在 One API 面板加渠道即可，EIOS 不用动。

**5. 验收 EIOS**

```bash
docker compose -f docker-compose.stack.yml exec bot python -m app.launch_selftest
```

Telegram 里跟 bot 说句话，应收到 AI 回复 + 语音。

**6. n8n**：打开 `https://{N8N_DOMAIN}`，用 `.env` 里设的账号密码登录，开始搭工作流。

---

## 融合关系

- **EIOS 的 AI 出口 = One API**（`AI_BASE_URL=http://oneapi:3000/v1`）。切换 KIMI/DeepSeek 只在 One API 面板操作。
- **n8n 可反向触发 EIOS**：在 n8n 里用 HTTP 节点调 EIOS 的 `POST /ingest`（摘要某链接）或后续开放的发送接口，实现"定时把某内容播报给你"。
- **三者共享同一台机器的 Postgres/Redis**，互不干扰、各自独立重启。

---

## 边界说明

- 本融合只用**官方镜像 + 官方 API**：One API、n8n 官方镜像，KIMI/DeepSeek 官方接口。
- **不包含**任何逆向个人微信、逆向免费 KIMI 网页版之类的组件。
- 微信公众号接入需域名 + HTTPS +（大概率）ICP 备案，见主仓库 `docs/CONFIG_PORTS.md` 模块 3。
