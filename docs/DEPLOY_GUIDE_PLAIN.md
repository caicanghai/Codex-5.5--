# EIOS 大白话部署手册（照着抄就行）

> 目标：从「服务器刚买到手」到「Telegram 里能跟你的 AI 助手对话」。
> 全程复制粘贴，看不懂的地方每一步都有一句人话解释。遇到报错，把那几行发我。

---

## 第 0 步：你需要准备的三样东西

1. **一台服务器（VPS）**：2 核 2G 内存、40G 硬盘、系统选 **Ubuntu 24.04**。买完商家会给你：
   - 一个 **IP 地址**（像 `123.45.67.89`）
   - 一个 **root 密码**（或初始密码）
2. **一个 Telegram 机器人 token**：你已经有了（`@facaihaidafubot` 那个）。
3. **一个 AI 的 key**（可选）：DeepSeek 或 OpenAI 的都行；不填也能跑，只是回复质量低一点。

> 微信公众号那条先不管，它要域名+备案，等 Telegram 跑通了再说。

---

## 第 1 步：连上你的服务器

**Windows 用户**：下载一个叫 **Termius** 或 **PuTTY** 的软件（免费），填 IP、用户名 `root`、密码，连上。
**苹果 Mac 用户**：打开自带的「终端」，输入下面这行（把 IP 换成你的）：

```bash
ssh root@123.45.67.89
```

第一次连会问 `yes/no`，输 `yes`，然后输密码（输密码时屏幕不显示，是正常的，输完回车）。

连上后你会看到命令行变成服务器的了，接下来所有命令都在这里敲。

---

## 第 2 步：给服务器装「Docker」（一次性）

Docker 是运行 EIOS 的容器工具。复制这一整段粘贴进去，回车，等它跑完（约 1-2 分钟）：

```bash
curl -fsSL https://get.docker.com | sh
```

跑完输入下面这行验证，能看到版本号就说明装好了：

```bash
docker --version
```

---

## 第 3 步：把 EIOS 代码下载到服务器

复制粘贴（把仓库地址换成你自己的 GitHub 仓库地址）：

```bash
git clone https://github.com/caicanghai/Codex-5.5--.git /root/eios
cd /root/eios
git checkout claude/eios-repository-foundation-hoi3u8
```

> 说明：`git clone` 就是把代码搬到服务器的 `/root/eios` 文件夹；`checkout` 是切到我们做 EIOS 的那个分支。

---

## 第 4 步：填配置（只填 Telegram，最省事）

先复制一份配置模板：

```bash
cp .env.example .env
```

然后把你的 Telegram token 写进去（把 `你的BOT_TOKEN` 换成从 @BotFather 拿到的那串，**不要把真 token 提交到任何代码库**）：

```bash
cat >> .env <<'EOF'
TELEGRAM_BOT_TOKEN=你的BOT_TOKEN
EOF
```

> 如果你有 AI key（比如 DeepSeek），再加这两行（把 sk-xxx 换成你的真 key）：
>
> ```bash
> cat >> .env <<'EOF'
> OPENAI_API_KEY=sk-你的key
> AI_BASE_URL=https://api.deepseek.com/v1
> AI_MODEL=deepseek-chat
> EOF
> ```
>
> 如果你有 Fish 语音 key，也加一行：
>
> ```bash
> echo 'FISH_AUDIO_API_KEY=你的fish密钥' >> .env
> ```

---

## 第 5 步：启动！

一条命令，拉起全部服务（第一次会构建，约 3-5 分钟）：

```bash
docker compose up -d --build
```

跑完看一眼状态，四个都显示 `running` 或 `healthy` 就对了：

```bash
docker compose ps
```

---

## 第 6 步：自检（确认真的通了）

这条命令会自动走一遍「Telegram → AI → 语音」，成功会给你的 Telegram 发一条真实语音：

```bash
docker compose exec bot python -m app.launch_selftest
```

- 看到 **PASS** = 成功，整套通了。
- 看到 **FAIL** = 把那几行发我，我告诉你哪出问题。

---

## 第 7 步：去 Telegram 用起来

1. 打开 Telegram，搜索你的机器人 `@facaihaidafubot`，点「开始 / Start」。
2. 发一句 `/whoami` —— 它会告诉你的数字 ID，回填到 `.env` 的 `TELEGRAM_OWNER_ID`（然后 `docker compose up -d` 重启一下）。
3. 随便发句话（比如"晚上好"）—— 它会用 AI 回复你 + 发一条语音。
4. 发 `/voice_list` 看音色，`/voice_pick fish2` 换成"万万雪饼的声音"。

**到这里，你的私人 AI 语音助手就跑起来了。**

---

## 常见问题

- **命令报 `permission denied` / `command not found`**：大概率没连上服务器或没装好 Docker，回第 1、2 步。
- **`docker compose ps` 里某个容器一直重启**：跑 `docker compose logs --tail=50 bot` 把输出发我。
- **Telegram 不回消息**：跑 `docker compose exec bot python -m app.tg_doctor`，把结果发我。
- **想接微信公众号**：需要域名 + HTTPS +（大概率）备案，等 Telegram 稳定后单独弄。

---

## 之后想更新代码

以后我改了代码，你在服务器上跑这三行就能更新：

```bash
cd /root/eios
git pull
docker compose up -d --build
```
