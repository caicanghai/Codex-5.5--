# EIOS 配置端口表

一张总表：每个接入点需要填的密钥、去哪拿、以及「接收消息」的回调地址。
**密钥只填在服务器的 `.env` 里，永不贴进聊天。** 对应可填写文件：仓库根目录 `.env.example`（`cp .env.example .env` 后逐项填）。

回调 URL 里的 `你的域名` 换成真实 HTTPS 域名（反向代理到 `API_PORT`，默认 8000）。

---

## 一、渠道接入表

| 渠道 | 发消息需要 | 收消息(能回复你)需要 | 回调地址 | 去哪拿 |
|---|---|---|---|---|
| **Telegram** | `TELEGRAM_BOT_TOKEN` | 同左（长轮询，无需回调） | 无（出站长轮询） | @BotFather |
| **企业微信 WeCom** | `WECOM_CORP_ID`·`WECOM_AGENT_ID`·`WECOM_SECRET` | `WECOM_TOKEN`·`WECOM_AES_KEY` | `/webhook/wecom` | 企业微信管理后台 → 我的企业 / 应用 → 接收消息 |
| **微信公众号** | `WECHAT_APP_ID`·`WECHAT_APP_SECRET` | `WECHAT_TOKEN`（安全模式再加 `WECHAT_AES_KEY`） | `/webhook/wechat` | 微信公众平台 → 开发 → 基本配置 / 服务器配置 |
| **WhatsApp** | `WHATSAPP_ACCESS_TOKEN`·`WHATSAPP_PHONE_NUMBER_ID` | `WHATSAPP_VERIFY_TOKEN`·`WHATSAPP_APP_SECRET` | `/webhook/whatsapp` | Meta for Developers → WhatsApp |
| **OpenClaw** | `OPENCLAW_BASE_URL`·`OPENCLAW_API_KEY` | 同左 | `/webhook/openclaw` | openclaw-weixin 桥服务 |

> `WECOM_AES_KEY` / `WECHAT_AES_KEY` 是 43 位的 EncodingAESKey。
> 每个渠道还要在 `CHANNELS_ENABLED` 里加上名字并把对应 `*_ENABLED=true`，才会真正投递。

---

## 二、AI 大模型

| 变量 | 说明 | 去哪拿 |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI 兼容 key（留空则用离线摘要） | OpenAI / DeepSeek / OpenRouter |
| `AI_BASE_URL` | 非 OpenAI 时改成对应网关 | 供应商文档 |
| `AI_MODEL` | 模型名，如 `gpt-4o-mini`、`deepseek-chat` | 供应商文档 |

---

## 三、音色（语音回复）

合成顺序 **Fish → ElevenLabs → Edge**；选定音色后该音色排到最前，全渠道回复都用它。

| 变量 / 命令 | 说明 |
|---|---|
| `FISH_AUDIO_API_KEY` | Fish Audio 密钥（主力，支持克隆 + 精选音色） |
| `FISH_AUDIO_VOICE_ID` | 默认 Fish 音色：fish.audio 链接里的 `modelId` |
| `ELEVENLABS_API_KEY` / `ELEVENLABS_VOICE_ID` | ElevenLabs 备用 |
| `TTS_VOICE` | Edge 免密钥兜底音色，如 `zh-CN-XiaoxiaoNeural` |
| `/voice_list` | 在 Telegram 里浏览可选音色模板 |
| `/voice_pick <编号>` | 选定音色（如 `fish1`、`xiaoxiao`） |
| `/voice_set` | 上传语音样本克隆你自己的声音（Fish） |

**内置音色模板**（`/voice_list` 可见，`app/voice/templates.py` 里维护）：

| 编号 | 提供方 | 说明 |
|---|---|---|
| `fish1` | fish | Fish 精选音色①（需配 `FISH_AUDIO_API_KEY`） |
| `xiaoxiao` / `xiaoyi` | edge | 温柔 / 亲切女声（普通话） |
| `yunxi` / `yunyang` / `yunjian` | edge | 沉稳 / 专业 / 浑厚男声（普通话） |
| `xiaobei` | edge | 东北女声（方言） |
| `hiugaai` | edge | 粤语女声 |
| `hsiaochen` | edge | 台湾女声 |
| `aria` / `guy` | edge | US female / male（英文） |

> 要加更多 Fish/ElevenLabs 音色：把 `provider | voice_id | 名字` 发给我，我加进 `templates.py`。

---

## 四、基础设施 / 端口

| 变量 | 默认 | 说明 |
|---|---|---|
| `API_PORT` | `8000` | api 容器监听端口；反向代理 `https://你的域名` → 此端口 |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | eios / change_me / eios | 数据库凭证（`PASSWORD` 请改） |
| `DATABASE_URL` / `REDIS_URL` | compose 内置 | 一般无需改 |

---

## 五、最小启动组合

- **只跑 Telegram**：填 `TELEGRAM_BOT_TOKEN` + `TELEGRAM_OWNER_ID`（+ 可选 `OPENAI_API_KEY`、`FISH_AUDIO_API_KEY`）即可。
- **加语音克隆/精选音色**：再填 `FISH_AUDIO_API_KEY`。
- **接微信/企业微信收发**：按上表填对应发送 + 收消息变量，在平台后台填回调 URL，并把渠道加入 `CHANNELS_ENABLED`。

验证：
```bash
cd /root/eios && git pull && docker compose up -d --build
docker compose exec bot python -m app.launch_selftest
```
