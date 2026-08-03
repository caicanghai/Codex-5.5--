# talk-to-fengge 接入位（实时语音分身）

浏览器连麦式的实时语音 AI 分身（克隆音色 + 人格），融合进 EIOS 栈的接入位。**源码到位前用 profile `fengge` 隔离，不影响现有栈。**

```
交互模式（和 EIOS 不同）
 │
 ├─ EIOS         异步：发消息 → 回一条语音
 └─ talk-to-fengge  实时：浏览器连麦 → 边说边聊（打电话式）
```

## 放源码（源码到手后，在服务器上）

```
integration/talk-to-fengge/src/
  ├─ pyproject.toml
  ├─ worker/          （agent / STT / LLM / TTS）
  ├─ web/
  └─ .env.local       ← 真实 key，只在服务器，已 gitignore
```

## 启动（带 fengge）

```bash
cd integration
docker compose -f docker-compose.stack.yml --profile fengge up -d --build
```

## 三个进程 → 三个容器

```
talk-to-fengge 在栈里
 │
 ├─ livekit         livekit/livekit-server（信令 :7880 + 媒体 UDP 段）
 ├─ fengge-worker   STT(Cartesia) → LLM(DeepSeek/One API) → TTS(ElevenLabs 克隆)
 └─ fengge-web      浏览器前端 :8766 → Caddy 反代 https://{$FENGGE_DOMAIN}
```

## 两个部署要点（Windows → Linux）

```
必须注意
 │
 ├─ ① LiveKit 二进制换成官方镜像
 │     └─ 你本地的 livekit-server.exe（Windows）不能用
 │          └─ compose 里用 livekit/livekit-server 镜像替代
 │
 └─ ② WebRTC 要开 UDP
       └─ 云服务器防火墙放行 7880/tcp、7881/tcp、50000-50100/udp
            └─ 媒体走 UDP，不经 Caddy
```
