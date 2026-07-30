# prompt-studio 接入位（等源码）

提示词工作站（prompt-studio）融合进 EIOS 栈的接入位。**源码到位前，这一块用 compose profile `studio` 隔离，不影响现有栈启动。**

## 你要做的一步（源码到手后）

```
放源码
 │
 └─ 把「提示词工作站-源代码.zip」解压到：
      integration/prompt-studio/src/
        ├─ package.json
        ├─ server/serve.mjs      （静态托管 + /relay 代理，:8080，/health）
        ├─ server/proxy.mjs
        └─ …（前端源码，npm run build 产出 dist/）
```

## 启动（带 studio 一起）

```bash
cd integration
docker compose -f docker-compose.stack.yml --profile studio up -d --build
```

不带 `--profile studio` 时，prompt-studio 不参与，现有栈照常跑。

## 融合关系

```
prompt-studio 在栈里的位置
 │
 ├─ 容器 studio        Node 22 · serve.mjs :8080
 │     └─ Caddy 反代 → https://{$STUDIO_DOMAIN}（带 Basic Auth）
 │
 ├─ AI 精修端点         → 指向 One API（http://oneapi:3000/v1）
 │     └─ 访客不用各填 key，统一走中转
 │
 └─ /relay 开放代理     → Caddy 层加 Basic Auth 防裸奔
       （对应你部署文档里的 Nginx htpasswd）
```

## 边界说明（如实，来自你的部署文档）

```
公网可用 vs 依赖本地
 │
 ├─ ✅ 公网可用：提示词生成 / 术语改写 / OCR(前端) / AI 精修 / 模块系统
 └─ ⚠️ 依赖本地：文生图/图生图/视频 等媒体功能走本地 A1111/ComfyUI
       └─ 服务器上没有 → 需另配 GPU 机器或云 API 才能用
```
