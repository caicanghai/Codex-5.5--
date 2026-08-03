# 🔑 EIOS 项目交接文档（唯一权威版）

> 本文件是**接手这个项目的第一份必读**。它讲的是**真实现状**，不是愿景。
> 最后更新：2026-08-03

---

## 一、这个项目到底是什么

**EIOS** = 一个多渠道 AI 消息机器人。用户从 Telegram / 微信 / 企业微信 / WhatsApp 发消息，
系统用 AI 处理（对话、总结链接、转工作流），再把回复（含语音）发回去。

**当前真实形态**：单体 FastAPI 应用 + Telegram bot，Docker Compose 编排。**不是**微服务。

---

## 二、真实的代码结构（别信架构蓝图，信这个）

```
Codex-5.5--/
├── docker-compose.yml       # ← 部署用这个（根目录）。4容器：db / redis / api / bot
├── .env.example             # ← 配置模板（根目录）。复制成 .env 填写
├── Dockerfile               # api 和 bot 共用
├── app/                     # ← 全部真实代码在这
│   ├── api/main.py          #   FastAPI：/health、/ingest、/webhook/{whatsapp,wechat,wecom,openclaw}
│   ├── bot/                 #   Telegram bot（长轮询）
│   ├── dispatch.py          #   消息路由：链接→总结 / 关键词→n8n工作流 / 其它→AI对话
│   ├── pipeline/            #   chat（AI对话，多级故障转移）+ summarize（链接总结）
│   ├── messaging/           #   5个渠道发送实现（见下）
│   │   ├── telegram.py
│   │   ├── wecom.py         #   企业微信
│   │   ├── wechat_official.py #  微信公众号
│   │   ├── whatsapp.py
│   │   ├── openclaw.py      #   OpenClaw 微信桥
│   │   └── wxcrypt.py       #   微信/企业微信消息加解密
│   ├── voice/               #   TTS 语音合成（Fish→ElevenLabs→Edge 三级）
│   └── config.py            #   所有环境变量定义
├── deployments/scripts/install.sh   # 一键部署脚本（已修正为真实路径）
├── DEPLOYMENT.md            # 真实部署步骤
├── PROJECT_SUMMARY.md       # 项目概览（顶部已标注哪些是愿景）
└── docs/architecture/       # ⚠️ 未来架构蓝图（微服务/多租户RLS/12阶段）—— 是设计目标，非现状
```

> **重要**：`docs/architecture/` 里的 25 个文档描述的是**未来想做成的样子**
> （微服务拆分、多租户 RLS、iOS 推送等），**目前都还没实现**。接手别照那个去找代码。

---

## 三、五个渠道的真实状态（最关键的表）

代码层面 **5 个渠道全部写好了**（`app/messaging/` + `/webhook/*` 路由都在）。
能不能用，卡在**凭证**和**域名/外部服务**上：

| 渠道 | 代码 | 能立刻用吗 | 卡在什么 | 需要域名吗 |
|------|------|-----------|---------|-----------|
| **Telegram** | ✅ | ✅ **能** | 只需填 Bot Token | ❌ 不用 |
| **企业微信-推送** | ✅ | ✅ **能** | 只需 CorpID+AgentID+Secret | ❌ 不用 |
| **企业微信-收消息** | ✅ | ❌ | 需**备案域名**做回调 | ✅ 要备案 |
| **微信公众号** | ✅ | ❌ | 需**备案域名** + 公众号凭证 | ✅ 要备案 |
| **WhatsApp** | ✅ | ⚠️ | 需 Meta 凭证 + HTTPS（**不用备案**） | ✅ 要HTTPS，不用备案 |
| **微信-走OpenClaw** | ✅ | ⚠️ | 需一个**活的 OpenClaw 服务**（外部） | ❌ 不用 |

### 三个关键真相

1. **Telegram 零门槛** —— 现在就能双向跑通（对话+语音）。**先用它验证整个系统。**

2. **企业微信可"只推送不接收"** —— 主动推送通知**不需要回调、不需要域名**。
   只有想让员工"发消息给 bot 并收到回复"才需要备案域名。配置见第五节。

3. **备案是硬门槛，绕不过** —— 企业微信收消息、微信公众号，腾讯**强制要求 ICP 备案**
   （备案主体=企业主体）。没有任何技术手段能绕过。ngrok / Cloudflare 隧道都不行。

---

## 四、怎么部署（在 VPS 上，5 分钟）

阿里云 ECS 网页控制台点「远程连接」开终端，无需自己装 ssh。

```bash
# 1. 拉代码
cd /opt
git clone https://github.com/caicanghai/Codex-5.5--.git
cd Codex-5.5--
git checkout claude/eios-repository-foundation-hoi3u8

# 2. 配置
cp .env.example .env
nano .env          # 至少填 TELEGRAM_BOT_TOKEN 和 TELEGRAM_OWNER_ID

# 3. 启动
docker compose up -d --build      # 老版本用 docker-compose up -d --build

# 4. 验证
docker compose ps                 # db/redis/api/bot 四个都要 Up
curl http://localhost:8000/health
docker compose logs -f bot        # 看 Telegram 是否连上
```

**测试**：Telegram 给你的 bot 发消息 → 应收到 AI 回复。

---

## 五、各渠道配置速查（填在 VPS 的 `.env` 里）

> ⚠️ **安全铁律**：密钥只填在服务器的 `.env` 文件里，**永远不要贴进聊天/截图/git**。
> `.gitignore` 已忽略 `.env`。

### Telegram（现在就能用）
```env
TELEGRAM_BOT_TOKEN=123456789:AA...   # @BotFather 获取
TELEGRAM_OWNER_ID=你的数字ID          # @userinfobot 获取
CHANNELS_ENABLED=telegram
```

### 企业微信-只推送（现在就能用，不需域名）
```env
CHANNELS_ENABLED=telegram,wecom
WECOM_ENABLED=true
WECOM_CORP_ID=ww...       # 我的企业 → CorpID
WECOM_AGENT_ID=...        # 应用 → AgentId
WECOM_SECRET=...          # 应用 → Secret
# 不填 WECOM_TOKEN / WECOM_AES_KEY —— 那俩是"收消息"才要的
```

### 企业微信-收消息（要备案域名）
```env
# 在上面基础上再加：
WECOM_TOKEN=...           # 应用→接收消息→Token
WECOM_AES_KEY=...         # 应用→接收消息→EncodingAESKey（43位）
# 企业微信后台回调URL填：https://你的备案域名/webhook/wecom
```

### WhatsApp（要 HTTPS，不用备案；域名你已有）
```env
CHANNELS_ENABLED=telegram,whatsapp
WHATSAPP_ENABLED=true
WHATSAPP_ACCESS_TOKEN=...          # Meta 开发者后台
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_BUSINESS_ACCOUNT_ID=...
WHATSAPP_VERIFY_TOKEN=自定义字符串   # 和 Meta 后台填的一致
WHATSAPP_APP_SECRET=...
# Meta 后台回调URL填：https://tripsking.top/webhook/whatsapp
```

### 微信-走 OpenClaw（不用域名，但要外部 OpenClaw 服务）
```env
CHANNELS_ENABLED=telegram,openclaw
OPENCLAW_ENABLED=true
OPENCLAW_BASE_URL=https://你的openclaw服务地址   # ← 关键：得先有这个服务
OPENCLAW_API_KEY=...
OPENCLAW_SESSION=...      # 会话/目标标识
OPENCLAW_TARGET=...
```

---

## 六、域名怎么用（你有 trip-king.top / tripsking.art / tripsking.top）

**关键区分：买了域名 ≠ 备案了。备案要单独申请，2-3 周。**

- **给 WhatsApp 用** → **现在就能用**（WhatsApp 不管中国备案）：
  1. 域名解析 A 记录 → `8.217.110.255`
  2. 用 Caddy 自动配 HTTPS（下面命令）
  3. 回调 URL：`https://tripsking.top/webhook/whatsapp`

- **给企业微信收消息 / 微信公众号用** → **必须先备案**，域名才能通过腾讯校验。

### 用 Caddy 自动 HTTPS（有域名后）
根目录建 `Caddyfile`：
```
tripsking.top {
    reverse_proxy localhost:8000
}
```
把域名解析到 `8.217.110.255`，跑 Caddy，它自动申请 Let's Encrypt 证书。
`https://tripsking.top/webhook/whatsapp` 即可用（WhatsApp 不用备案）。

---

## 七、还差什么（TODO / 阻塞项）

| 项 | 状态 | 谁能解决 |
|----|------|---------|
| Telegram 跑通 | ✅ 只差填 token | 你，填 .env 即可 |
| WhatsApp Meta 凭证 | ❌ 没有 | 你去 Meta 开发者后台申请 |
| WhatsApp HTTPS | 🟡 域名有了，待配 Caddy | 部署时配 |
| OpenClaw 服务地址 | ❌ 没有 | 需自建 openclaw-weixin 或找提供方 |
| 域名备案 | ❌ 未备案（估计） | 阿里云备案，2-3周 |
| 企业微信双向 | 🔴 等备案 | 备案后即可 |
| 微信公众号 | 🔴 等备案+凭证 | 备案后即可 |

---

## 八、重要提醒 / 坑

1. **架构文档 ≠ 现状**。`docs/architecture/` 是蓝图，代码在 `app/`。
2. **我（AI）无法 SSH 到服务器**。所有部署命令需要你/接手人在 VPS 上手动执行。
3. **OpenClaw 桥接个人微信有封号风险**，违反微信 ToS，别用于正经业务。
4. **企业微信收消息、微信公众号 = 备案硬门槛**，无法绕过。
5. **密钥别进聊天/git**，只填服务器 `.env`。
6. **AI 留空也能跑**（用离线摘要），但质量低；建议填 OpenRouter 免费 key。

---

## 九、常用运维命令

```bash
docker compose ps                 # 状态
docker compose logs -f api        # API日志
docker compose logs -f bot        # Telegram日志
docker compose logs | grep -i error
docker compose restart api        # 重启
docker compose down               # 停
docker compose up -d --build      # 改代码后重建
docker compose exec db psql -U eios -d eios   # 进数据库
```

---

## 十、代码位置索引（接手人快速定位）

| 想改什么 | 看哪个文件 |
|---------|-----------|
| 消息怎么路由（对话/总结/工作流） | `app/dispatch.py` |
| AI 对话逻辑、故障转移 | `app/pipeline/chat.py` |
| 链接总结 | `app/pipeline/` |
| 加/改渠道发送 | `app/messaging/<渠道>.py` |
| webhook 接收 | `app/api/main.py` |
| 微信/企微加解密 | `app/messaging/wxcrypt.py` |
| 语音合成 | `app/voice/` |
| 所有配置项 | `app/config.py` + `.env.example` |
| 部署 | `docker-compose.yml` + `DEPLOYMENT.md` |

---

**一句话总结**：代码 5 渠道都写好了；**Telegram 现在就能跑**；企业微信能"只推送"；
WhatsApp 差 Meta 凭证（域名你有）；微信双向/公众号卡备案；OpenClaw 差外部服务。
**先用 Telegram 把系统跑起来，其余按凭证/备案到位逐个开。**
