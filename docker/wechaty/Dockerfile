# wechaty 网关镜像。wechaty-puppet-wechat 走 web 协议，依赖 Chromium。
FROM node:18-bullseye-slim

# puppeteer/chromium 运行所需系统库
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium ca-certificates fonts-liberation libnss3 libatk-bridge2.0-0 \
    libgtk-3-0 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libasound2 libpangocairo-1.0-0 libxshmfence1 \
  && rm -rf /var/lib/apt/lists/*

ENV PUPPETEER_SKIP_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

WORKDIR /app
COPY package.json .
RUN npm install --omit=dev
COPY bot.js .

EXPOSE 8788
CMD ["node", "bot.js"]
