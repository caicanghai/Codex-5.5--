# EIOS 项目实时状态 & 待办清单（给接手 agent）

> 更新时间：2026-08-03
> 用途：交给 agent 继续推进部署 + 渠道接入。先读这份，再读仓库根目录 `HANDOFF.md`。

---

## 0. 一句话现状

EIOS（多渠道 AI 消息机器人）准备部署到阿里云。代码就绪，**Telegram 可立即跑通**；
**WhatsApp 接入进行到一半**（差 access token）；微信走 OpenClaw（卡 Node 版本）；
企业微信/公众号卡备案域名。

---

## 1. 基础设施（已确认的事实）

| 项 | 值 |
|----|----|
| 代码仓库 | https://github.com/caicanghai/Codex-5.5-- |
| 分支 | `claude/eios-repository-foundation-hoi3u8` |
| 服务器 | 阿里云 ECS，**中国香港**，公网 IP `8.217.110.255` |
| 规格 | Ubuntu 22.04，2核16G，40G盘，已装 Docker 社区版 |
| 域名 | `trip-king.top` / `tripsking.art` / `tripsking.top`（**均未备案**） |
| 部署方式 | 根目录 `docker-compose.yml`（4容器：db/redis/api/bot），端口 8000 |
| 真实代码 | 在 `app/`（单体 FastAPI）；`docs/architecture/` 是未来蓝图，非现状 |

**重要约束**：
- AI 助手**无法 SSH 进这台服务器**（沙箱网络限制）。需要人在阿里云网页「远程连接」里执行命令。
- 密钥只填服务器 `.env`，**不进聊天/git**。

---

## 2. 分渠道进度

### ✅ Telegram —— 可立即跑通（未做）
- 代码：✅ 完成（`app/bot/`）
- 缺：`TELEGRAM_BOT_TOKEN`（@BotFather 拿）+ `TELEGRAM_OWNER_ID`（@userinfobot 拿）
- **待办**：填 `.env` → `docker compose up -d --build` → 测试

### 🟡 WhatsApp —— 进行到一半
已完成：
- WhatsApp 业务账户（WABA）已建，状态**审核中**（正常）
  - **WABA ID（BUSINESS_ACCOUNT_ID）= `2448528952314302`**
- 手机号已加：柬埔寨 `+855 96 761 1765`
  - **PHONE_NUMBER_ID = `1238587366009579`**
- 开发者 App 已建：名「稍安勿躁」，**App ID = `2218017788931551`**，开发模式

还差：
- ⚠️ App 里**加错了产品**：加成了「Facebook 登录」，需要**改加 WhatsApp 产品**
- ⬜ `WHATSAPP_ACCESS_TOKEN`（App → WhatsApp → API 设置里的临时令牌，或建 System User 拿永久令牌）
- ⬜ `WHATSAPP_APP_SECRET`（App → 设置 → 基本 → 应用密钥）
- ⬜ `WHATSAPP_VERIFY_TOKEN`（自己编一个，如 `eios_verify_2026`）
- ⬜ 配 webhook 回调：`https://tripsking.top/webhook/whatsapp`（需先给域名配 HTTPS，WhatsApp **不需要备案**）

**下一步具体动作**：
1. developers.facebook.com/apps → 进「稍安勿躁」App
2. 加 **WhatsApp** 产品（不是 Facebook 登录）→ 关联业务组合
3. 进 WhatsApp → API 设置 → 复制临时 access token
4. 应用设置→基本→拿 App Secret
5. 5 个值填服务器 `.env`
6. 临时 token 24h 过期，正式用要在 business.facebook.com→系统用户建永久 token

### 🟡 微信（走 OpenClaw）—— 卡 Node 版本
- 现状：OpenClaw 装在**用户的 Windows 电脑**（DESKTOP-MBS7J1P），不是服务器
- 问题：OpenClaw 需要 **Node.js v22.19+**，但：
  - 安装目录是 `C:\node-v22.14.0-win-x64\`（v22.14，太老）
  - 系统实际跑 v24.15.0（太新，OpenClaw 不认）
  - `openclaw status` 命令 failed，微信里显示「暂无法连接 OpenClaw」
- **待决策**：微信放哪？
  - Windows 上跑（号安全）→ 装 Node v22.19，穿透连回服务器
  - 阿里云上跑（用户要求全上云）→ **⚠️ 个人微信登录香港服务器 IP 极易封号**，只能用小号
- **待办**：先让 Windows 上的本地 agent 跑这三条给出真实报错：
  ```
  node -v
  & "C:\node-v22.14.0-win-x64\node_modules\.bin\openclaw" --version
  & "C:\node-v22.14.0-win-x64\node_modules\.bin\openclaw" status
  ```

### 🟢 企业微信-推送 —— 可做（不用域名）
- 只要 CorpID + AgentID + Secret 即可主动推送，**不需要回调、不需要域名**
- CorpID 已知：`ww0b1b3e2c9a997135`
- **待办**：拿 AgentID + Secret 填 `.env`，`WECOM_ENABLED=true`（不填 TOKEN/AESKey）

### 🔴 企业微信-收消息 —— 卡备案
- 需要备案域名做回调 `https://域名/webhook/wecom`，腾讯强制 ICP 备案，**无法绕过**
- 用户之前截图暴露过 Token/AESKey，**建议后台「随机获取」重新生成**当泄露处理

### 🔴 微信公众号 —— 卡备案
- 同样需要备案域名 + 公众号 AppID/AppSecret

---

## 3. 域名 / HTTPS（关键瓶颈）

- 三个域名**都没备案**
- **WhatsApp 用**：不需要备案！可立即用 —— 域名解析到 `8.217.110.255` + Caddy 自动 HTTPS
- **企业微信收消息 / 公众号用**：必须先备案（2-3周），无法绕过
- **待办（给 WhatsApp）**：
  1. `tripsking.top` A 记录 → `8.217.110.255`
  2. 根目录建 `Caddyfile`：`tripsking.top { reverse_proxy localhost:8000 }`
  3. 跑 Caddy，自动签 Let's Encrypt 证书

---

## 4. 优先级建议（给 agent 的执行顺序）

1. **【最高】部署 EIOS + 跑通 Telegram** —— 零门槛，验证整个系统能跑
2. **【高】WhatsApp 拿 token** —— 只差 App 加 WhatsApp 产品 + 拿 token；域名已有，配 Caddy 即可
3. **【中】企业微信-推送** —— 拿 AgentID/Secret 即可，不用域名
4. **【低/待决策】微信-OpenClaw** —— 先出真实报错，再定放 Windows 还是服务器（有封号风险）
5. **【阻塞】企业微信双向 / 公众号** —— 等域名备案，无法提前

---

## 5. 已收集的凭证/ID（非敏感，可用）

| 项 | 值 | 敏感 |
|----|----|----|
| VPS IP | 8.217.110.255 | 否 |
| WhatsApp WABA ID | 2448528952314302 | 否 |
| WhatsApp Phone Number ID | 1238587366009579 | 否 |
| WhatsApp 手机号 | +855 96 761 1765 | 否 |
| Meta App ID | 2218017788931551 | 否 |
| Meta App 名 | 稍安勿躁 | 否 |
| 企业微信 CorpID | ww0b1b3e2c9a997135 | 否 |
| WhatsApp ACCESS_TOKEN | ⬜ 未拿 | **是** |
| WhatsApp APP_SECRET | ⬜ 未拿 | **是** |
| 企业微信 AgentID/Secret | ⬜ 未拿 | **是** |
| Telegram Bot Token | ⬜ 未拿 | **是** |

> 敏感项拿到后**只填服务器 `.env`**，不要回贴聊天/截图。

---

## 6. 阻塞项汇总

| 阻塞 | 影响渠道 | 解法 | 时间 |
|------|---------|------|------|
| 域名未备案 | 企业微信双向、公众号 | 阿里云备案 | 2-3周 |
| 没 WhatsApp token | WhatsApp | App 加 WhatsApp 产品拿 token | 分钟级 |
| 没 Meta 凭证（token/secret） | WhatsApp | 同上 | 分钟级 |
| OpenClaw Node 版本 | 微信 | 装 Node v22.19 | 分钟级 |
| AI 无法 SSH | 全部部署 | 人在阿里云远程连接执行 | —— |
| 微信服务器 IP 封号风险 | 微信上云 | 用小号 或 留 Windows | 决策 |
```
