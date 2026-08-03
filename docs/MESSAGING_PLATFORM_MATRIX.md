# EIOS 消息平台矩阵 · MESSAGING PLATFORM MATRIX

统一接口：`app/messaging/base.py::MessagingProvider`
（`send_text / send_image / send_audio / send_file / send_voice / healthcheck / validate_config`）。
路由：`app/messaging/service.py::MessageRouter`（优先级 telegram → wecom → wechat_official → whatsapp，渠道隔离、独立重试、Redis 幂等去重）。

## 实现状态 (this phase)

| 平台                     | 状态             | 官方 API           | 文字 | 图片    | 文件      | 语音          | Webhook          | 群/多目标         | 主动推送      | 所需凭据                                             | 难度  | 优先级 |
| ------------------------ | ---------------- | ------------------ | ---- | ------- | --------- | ------------- | ---------------- | ----------------- | ------------- | ---------------------------------------------------- | ----- | ------ |
| Telegram                 | ✅ 完成          | 是 (Bot API)       | ✅   | ✅      | ✅        | ✅ voice note | 轮询(现)         | ✅ chat           | ✅            | `TELEGRAM_BOT_TOKEN`                                 | 低    | P0     |
| 企业微信 WeCom           | ✅ 完成          | 是 (自建应用)      | ✅   | ✅      | ✅        | ✅ AMR        | 可选             | ✅ user/party/tag | ✅            | `WECOM_CORP_ID/AGENT_ID/SECRET`                      | 中    | P0     |
| 微信公众号 WeChat OA     | ✅ 完成          | 是 (公众平台)      | ✅   | ✅      | ⛔ 无原生 | ✅ AMR        | ✅ 验签+被动回复 | ⛔                | 客服消息(48h) | `WECHAT_APP_ID/SECRET/TOKEN`                         | 中-高 | P0     |
| WhatsApp Business        | ✅ 完成          | 是 (Meta Cloud)    | ✅   | ✅      | ✅        | ✅ OGG/Opus   | ✅ 验证+接收     | 模板              | 模板消息      | `WHATSAPP_ACCESS_TOKEN/PHONE_NUMBER_ID/VERIFY_TOKEN` | 中    | P0     |
| Email SMTP               | 🔲 接口/配置模板 | 是                 | ✅   | 附件    | 附件      | 附件          | N/A              | ✅                | ✅            | SMTP host/user/pass                                  | 低    | P0     |
| Generic Webhook          | 🔲 接口/配置模板 | N/A                | ✅   | url     | url       | url           | 出站             | ✅                | ✅            | URL(+HMAC)                                           | 低    | P0     |
| Discord                  | 🔲 占位          | 是                 | ✅   | ✅      | ✅        | ✅            | ✅               | ✅                | ✅            | Bot Token                                            | 低    | P1     |
| Slack                    | 🔲 占位          | 是                 | ✅   | ✅      | ✅        | ✅            | ✅               | ✅                | ✅            | Bot Token                                            | 低    | P1     |
| Microsoft Teams          | 🔲 占位          | 是                 | ✅   | ✅      | ✅        | ⛔            | ✅               | ✅                | ✅            | App/Graph                                            | 高    | P1     |
| LINE                     | 🔲 占位          | 是                 | ✅   | ✅      | ✅        | ✅            | ✅               | ✅                | 推送(计费)    | Channel Token                                        | 中    | P1     |
| Facebook Messenger       | 🔲 占位          | 是                 | ✅   | ✅      | ✅        | ✅            | ✅               | ⛔                | 24h窗口       | Page Token                                           | 中    | P1     |
| Instagram Messaging      | 🔲 占位          | 是                 | ✅   | ✅      | ⛔        | ✅            | ✅               | ⛔                | 24h窗口       | Page/IG Token                                        | 中    | P1     |
| Matrix                   | 🔲 占位          | 是                 | ✅   | ✅      | ✅        | ✅            | ✅               | ✅                | ✅            | Homeserver+Token                                     | 中    | P2     |
| Signal                   | 🔲 占位          | 非官方(signal-cli) | ✅   | ✅      | ✅        | ✅            | 有限             | ✅                | ✅            | 独立网关                                             | 高    | P2     |
| SMS (Twilio 等)          | 🔲 占位          | 是                 | ✅   | ⛔(MMS) | ⛔        | ⛔            | ✅               | ⛔                | ✅            | Account/Token                                        | 低    | P2     |
| Web Push                 | 🔲 占位          | 是 (VAPID)         | ✅   | ⛔      | ⛔        | ⛔            | N/A              | ✅                | ✅            | VAPID keys                                           | 中    | P2     |
| APNs / FCM (Mobile Push) | 🔲 占位          | 是                 | ✅   | 有限    | ⛔        | ⛔            | N/A              | ✅ topic          | ✅            | 证书/Server Key                                      | 中-高 | P2     |

图例：✅ 已实现 · 🔲 接口/配置模板(占位) · ⛔ 平台不支持/不适用。

## 分类

- **已完成 (P0 完整实现)**：Telegram、WeCom、WeChat Official、WhatsApp Business。
- **部分完成**：Email SMTP、Generic Webhook（接口 + 配置模板，未实现发送逻辑）。
- **占位 (P1/P2)**：Discord、Slack、Teams、LINE、Messenger、Instagram、Matrix、Signal、SMS、Web Push、APNs/FCM —— 仅纳入矩阵与优先级，未写实现代码，避免无限扩张。
- **未接入**：其余未列平台。

## 优先级

- **P0**：Telegram、企业微信、微信公众号、WhatsApp Business、Email、Generic Webhook。
- **P1**：Discord、Slack、Microsoft Teams、LINE、Facebook Messenger、Instagram Messaging。
- **P2**：Matrix、Signal、SMS、Web Push、APNs / FCM。

本阶段仅完整实现 P0 中的四个即时通讯渠道；Email / Generic Webhook 及全部 P1/P2 保留接口与配置模板。

## 备注

- 所有渠道凭据仅通过环境变量注入；日志与投递状态**不记录** Token/Secret/完整私密消息。
- WhatsApp 定位为通知/业务/客服通道，**不**作为公开通用 AI 聊天机器人。
- 微信/企业微信仅用官方 API，**不使用**个人微信 Hook、桌面自动化或逆向登录。
- 真实平台密钥缺失时，本阶段所有联通性均以 **Mock 测试**验证，未声称真实 API 已连接。
