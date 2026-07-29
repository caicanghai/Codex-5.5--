# EIOS 使用说明书

EIOS 是一个跑在你自己服务器上的 AI 语音助手：你在聊天软件里发消息，它用 AI 理解并回复，还能用你选的音色发一条**语音**给你。本手册讲**装好之后怎么用**（怎么部署见 `DEPLOY_GUIDE_PLAIN.md`）。

---

## 一、它能做什么

| 你发的                      | 它做的                           |
| --------------------------- | -------------------------------- |
| 一句话（"晚上好"）          | AI 回复文字 + 一条语音           |
| 一个网址 / RSS 链接         | 抓取内容 → AI 摘要 → 语音播报    |
| 语音样本（配合 /voice_set） | 克隆成你自己的声音，之后用它回复 |

失败兜底：AI 挂了会回一句"暂不可用"，语音合成失败会退回纯文本——**它永远不会一声不吭**。

---

## 二、Telegram 命令大全

在你的机器人对话框里直接发这些命令：

### 基础

| 命令                | 作用                                                   |
| ------------------- | ------------------------------------------------------ |
| `/start` 或 `/help` | 查看欢迎语和命令列表                                   |
| `/whoami`           | 查看你的 Telegram 数字 ID（填 `TELEGRAM_OWNER_ID` 用） |
| 直接发文字          | AI 回复 + 语音                                         |
| 直接发链接          | 摘要 + 语音                                            |

### 音色（选一个好听的声音）

| 命令                                  | 作用                                                   |
| ------------------------------------- | ------------------------------------------------------ |
| `/voice_list`                         | 列出所有可选音色（fish1、fish2、晓晓、云希…）          |
| `/voice_pick <编号>`                  | 选定音色，例：`/voice_pick fish2`（万万雪饼的声音）    |
| `/voice_status`                       | 查看当前用的是哪个音色                                 |
| `/voice_delete`                       | 恢复默认音色                                           |
| `/voice_add <来源> <voice_id> <名字>` | 加一个新音色，例：`/voice_add fish c18df0... 我的音色` |
| `/voice_remove <编号>`                | 删除你自己加的音色                                     |
| `/voice_set`                          | 上传一段你的语音样本，克隆成你自己的声音               |
| `/speak <文字>`                       | 让它立刻用当前音色念一句话                             |

### 多渠道（接了微信/WhatsApp 后才有意义）

| 命令                     | 作用                                |
| ------------------------ | ----------------------------------- |
| `/channels`              | 看哪些渠道已开启                    |
| `/channel_status`        | 测试各渠道连接是否正常              |
| `/channel_test <渠道>`   | 给某个渠道发条测试消息              |
| `/broadcast <文字>`      | 同时发到所有已开启的渠道            |
| `/sync_on` / `/sync_off` | 开/关"发一条消息自动同步到其它渠道" |

---

## 三、最常用的三件事

**1. 换个好听的声音**

```
/voice_list          （看有哪些）
/voice_pick fish2    （选"万万雪饼的声音"）
你好                  （随便发句话，听听效果）
```

**2. 加一个新 Fish 音色**（在 fish.audio 复制链接里的 modelId）

```
/voice_add fish 这里粘贴modelId 音色名字
/voice_pick 刚才提示的编号
```

**3. 克隆你自己的声音**

```
/voice_set           （它会让你发语音样本）
（发一段 15-90 秒的你说话录音）
（等它提示克隆成功，之后回复就是你的声音）
```

---

## 四、日常运维（在服务器上）

| 想干嘛            | 命令（在 /root/eios 目录下）                            |
| ----------------- | ------------------------------------------------------- |
| 看服务是否都正常  | `docker compose ps`                                     |
| 看日志（排错）    | `docker compose logs --tail=50 bot`                     |
| 重启              | `docker compose restart`                                |
| 全链路自检        | `docker compose exec bot python -m app.launch_selftest` |
| Telegram 连接诊断 | `docker compose exec bot python -m app.tg_doctor`       |
| 更新到最新代码    | `git pull && docker compose up -d --build`              |
| 改配置后生效      | 改完 `.env` → `docker compose up -d`                    |

---

## 五、遇到问题

| 现象           | 怎么办                                                                          |
| -------------- | ------------------------------------------------------------------------------- |
| 发消息不回     | 服务器跑 `docker compose exec bot python -m app.tg_doctor`，把结果发我          |
| 有文字没语音   | 大概率没配 `FISH_AUDIO_API_KEY`，或用免费 Edge 音色（`/voice_pick xiaoxiao`）试 |
| 某容器一直重启 | `docker compose logs --tail=50 <容器名>`，把输出发我                            |
| 想接微信公众号 | 需要域名 + HTTPS +（大概率）备案，见 `CONFIG_PORTS.md` 模块 3                   |

---

## 六、安全须知

- **所有密钥只填在服务器 `.env` 里**，这个文件已被 git 忽略，不会进代码库。
- 不要把 token、AppSecret、API key 贴进聊天、截图或提交到 GitHub。
- 一旦某个密钥不小心暴露了（发到公开地方、进了 git 历史），**去对应平台重置/revoke**：
  - Telegram token → @BotFather → `/mybots` → 选 bot → API Token → Revoke
  - Fish/AI key → 各自后台重新生成
