# EIOS 配置端口表（按模块分开）

按渠道模块拆分：每个模块自己的密钥、回调地址、去哪拿、开关，全部写在它自己底下。
**密钥只填在服务器的 `.env` 里，永不贴进聊天。** 对应可填写文件：仓库根目录 `.env.example`（`cp .env.example .env` 后逐项填）。

回调 URL 里的 `你的域名` 换成真实 HTTPS 域名（反向代理到 `API_PORT`，默认 8000，全部渠道共用同一个端口、不同路径）。

启用总开关：`CHANNELS_ENABLED=telegram,wecom,...`（逗号列表，加了名字才会真正投递）。

---

## 模块 1：Telegram

最先跑通、最简单的渠道，无需公网回调（长轮询出站）。

| 项目                                            | 变量                 | 去哪拿                                   |
| ----------------------------------------------- | -------------------- | ---------------------------------------- |
| 机器人 token（发/收都靠它）                     | `TELEGRAM_BOT_TOKEN` | @BotFather                               |
| 你的 owner 身份（用于 `/voice_set` 等管理命令） | `TELEGRAM_OWNER_ID`  | Telegram 数字 user id（问 @userinfobot） |

**回调地址**：无需（出站长轮询，不用在任何后台配置）。

**附带功能**（都在 Telegram 里直接用）：

- `/voice_list` — 浏览音色模板
- `/voice_pick <编号>` — 选定音色，全渠道回复都用它
- `/voice_add <provider> <voice_id> <名字>` — 运行时新增音色
- `/voice_remove <编号>` — 删除自定义音色
- `/voice_set` — 上传样本克隆你自己的声音（Fish）
- `/voice_status` / `/voice_delete` — 查看 / 清除当前音色
- `/speak <文本>` — 让 bot 立即用当前音色念一段话
- `/channels` / `/channel_status` / `/channel_test` — 查看/测试各渠道状态
- `/broadcast` — 同时广播到多个渠道
- `/sync_on` / `/sync_off` — 开关跨渠道语音同步

**最小启动**：只填 `TELEGRAM_BOT_TOKEN` + `TELEGRAM_OWNER_ID` 就能跑（AI/语音留空会自动降级，不会沉默）。

---

## 模块 2：企业微信 WeCom

| 项目                                     | 变量                                                            | 去哪拿                         |
| ---------------------------------------- | --------------------------------------------------------------- | ------------------------------ |
| 总开关                                   | `WECOM_ENABLED=true`                                            | —                              |
| 企业 ID                                  | `WECOM_CORP_ID`                                                 | 企业微信管理后台 → 我的企业    |
| 应用 ID / 密钥（发消息用）               | `WECOM_AGENT_ID` / `WECOM_SECRET`                               | 管理后台 → 应用管理 → 自建应用 |
| 收消息 Token / AES Key（能回复你，必填） | `WECOM_TOKEN` / `WECOM_AES_KEY`（43 位）                        | 应用 → 接收消息 → API 接收     |
| 默认发送对象（可选）                     | `WECOM_TARGET_USER` / `WECOM_TARGET_PARTY` / `WECOM_TARGET_TAG` | 留空 = @all                    |

**回调地址**：`https://你的域名/webhook/wecom`（填在「接收消息」配置里）。

**附带功能**：入站消息走 AES 加解密（`WXBizMsgCrypt`），解密后走统一 AI 回复 + 语音合成链路——和 Telegram 收到消息后的处理完全一样，用的是同一套音色（`/voice_pick` 选的那个）。

---

## 模块 3：微信公众号 WeChat Official Account

| 项目                           | 变量                                  | 去哪拿                         |
| ------------------------------ | ------------------------------------- | ------------------------------ |
| 总开关                         | `WECHAT_OFFICIAL_ENABLED=true`        | —                              |
| AppID / AppSecret（发消息用）  | `WECHAT_APP_ID` / `WECHAT_APP_SECRET` | 微信公众平台 → 开发 → 基本配置 |
| 收消息 Token（必填）           | `WECHAT_TOKEN`                        | 公众平台 → 服务器配置          |
| 加密模式再加（明文模式可不填） | `WECHAT_AES_KEY`（43 位）             | 服务器配置 → 消息加解密方式    |

**回调地址**：`https://你的域名/webhook/wechat`（填在「服务器配置」里，明文/安全/兼容模式都支持）。

**附带功能**：与 WeCom 共用同一套 `WXBizMsgCrypt` 加解密模块；回复走客服接口，能带语音（不只是被动文本）。

---

## 模块 4：WhatsApp Business（Meta 官方 Cloud API）

| 项目                             | 变量                                                 | 去哪拿                                    |
| -------------------------------- | ---------------------------------------------------- | ----------------------------------------- |
| 总开关                           | `WHATSAPP_ENABLED=true`                              | —                                         |
| 访问令牌 / 手机号 ID（发消息用） | `WHATSAPP_ACCESS_TOKEN` / `WHATSAPP_PHONE_NUMBER_ID` | Meta for Developers → WhatsApp → API 设置 |
| Business Account ID（可选）      | `WHATSAPP_BUSINESS_ACCOUNT_ID`                       | 同上                                      |
| 收消息校验（必填）               | `WHATSAPP_VERIFY_TOKEN` / `WHATSAPP_APP_SECRET`      | 自定义字符串 + App 设置里的 secret        |
| 默认接收人（可选）               | `WHATSAPP_RECIPIENT`                                 | —                                         |

**回调地址**：`https://你的域名/webhook/whatsapp`（填在 Meta 后台 Webhook 配置里，`WHATSAPP_VERIFY_TOKEN` 要跟这里填的一致）。

---

## 模块 5：OpenClaw（openclaw-weixin 外部微信桥）

| 项目                  | 变量                                                      | 去哪拿                     |
| --------------------- | --------------------------------------------------------- | -------------------------- |
| 总开关                | `OPENCLAW_ENABLED=true`                                   | —                          |
| 桥服务地址 / 密钥     | `OPENCLAW_BASE_URL` / `OPENCLAW_API_KEY`                  | openclaw-weixin 部署方提供 |
| 模型/会话标识（可选） | `OPENCLAW_MODEL` / `OPENCLAW_SESSION` / `OPENCLAW_TARGET` | 默认值一般够用             |

**回调地址**：`https://你的域名/webhook/openclaw`。

---

## 模块 6：AI 大模型（所有渠道共用）

不属于某个渠道，是全局的回复大脑。

| 变量             | 说明                                                  | 去哪拿                         |
| ---------------- | ----------------------------------------------------- | ------------------------------ |
| `OPENAI_API_KEY` | OpenAI 兼容 key（留空则用离线摘要，仍会回复不会沉默） | OpenAI / DeepSeek / OpenRouter |
| `AI_BASE_URL`    | 非 OpenAI 时改成对应网关                              | 供应商文档                     |
| `AI_MODEL`       | 模型名，如 `gpt-4o-mini`、`deepseek-chat`             | 供应商文档                     |

---

## 模块 7：音色（所有渠道共用）

不属于某个渠道，选定后**全部渠道**回复都用这个声音。合成顺序 **Fish → ElevenLabs → Edge**。

| 变量 / 命令                                  | 说明                                           |
| -------------------------------------------- | ---------------------------------------------- |
| `FISH_AUDIO_API_KEY`                         | Fish Audio 密钥（主力，支持克隆 + 精选音色）   |
| `FISH_AUDIO_VOICE_ID`                        | 默认 Fish 音色：fish.audio 链接里的 `modelId`  |
| `ELEVENLABS_API_KEY` / `ELEVENLABS_VOICE_ID` | ElevenLabs 备用                                |
| `TTS_VOICE`                                  | Edge 免密钥兜底音色，如 `zh-CN-XiaoxiaoNeural` |

**内置音色模板**（`/voice_list` 可见，`app/voice/templates.py` 里维护）：

| 编号                            | 提供方 | 说明                                        |
| ------------------------------- | ------ | ------------------------------------------- |
| `fish1`                         | fish   | Fish 精选音色①（需配 `FISH_AUDIO_API_KEY`） |
| `fish2`                         | fish   | 万万雪饼的声音（需配 `FISH_AUDIO_API_KEY`） |
| `xiaoxiao` / `xiaoyi`           | edge   | 温柔 / 亲切女声（普通话）                   |
| `yunxi` / `yunyang` / `yunjian` | edge   | 沉稳 / 专业 / 浑厚男声（普通话）            |
| `xiaobei`                       | edge   | 东北女声（方言）                            |
| `hiugaai`                       | edge   | 粤语女声                                    |
| `hsiaochen`                     | edge   | 台湾女声                                    |
| `aria` / `guy`                  | edge   | US female / male（英文）                    |

> 要加更多 Fish/ElevenLabs 音色：把 `provider | voice_id | 名字` 发给我，我加进 `templates.py`；
> 或自己在 Telegram 发 `/voice_add fish <modelId> 我的音色`，无需改代码。

---

## 模块 8：基础设施（所有渠道共用）

| 变量                                                  | 默认                    | 说明                                                                                            |
| ----------------------------------------------------- | ----------------------- | ----------------------------------------------------------------------------------------------- |
| `API_PORT`                                            | `8000`                  | api 容器监听端口；反向代理 `https://你的域名` → 此端口，全渠道 webhook 共用这一个端口的不同路径 |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | eios / change_me / eios | 数据库凭证（`PASSWORD` 请改）                                                                   |
| `DATABASE_URL` / `REDIS_URL`                          | compose 内置            | 一般无需改                                                                                      |

---

## 验证

```bash
cd /root/eios && git pull && docker compose up -d --build
docker compose exec bot python -m app.launch_selftest
```
