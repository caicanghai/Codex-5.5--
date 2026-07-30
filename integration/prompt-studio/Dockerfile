# prompt-studio 容器镜像（Node 22 静态托管 + /relay 中转代理）
#
# 用法：把「提示词工作站-源代码.zip」解压到本目录（integration/prompt-studio/src/），
# 使其包含 package.json / server/serve.mjs / 前端源码，然后 compose 用 profile "studio"
# 构建即可。构建步骤与你的公网部署文档一致（npm install → npm run build → serve.mjs）。

FROM node:22-alpine

WORKDIR /app

# 只先拷贝依赖清单以利用缓存（源码放在 src/ 下）
COPY src/package*.json ./
RUN npm install --no-audit --no-fund

# 拷贝其余源码并构建 dist/
COPY src/ ./
RUN npm run build

ENV PORT=8080
EXPOSE 8080

# serve.mjs：静态托管 dist/ + /relay 中转代理（/health 返回 {"ok":true}）
CMD ["node", "server/serve.mjs"]
