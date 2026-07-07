# 每日安全资讯聚合推送 —— 应用镜像
FROM python:3.11-slim

WORKDIR /app

# 先装依赖（含可选全量：anthropic/telethon/apscheduler/dotenv）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝代码与默认配置
COPY src/ ./src/
COPY config/ ./config/

ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    DIGEST_DB=/app/data/digest.db

# 状态库与 telethon session 落在挂载卷上，便于持久化
VOLUME ["/app/data"]

# 默认常驻定时调度；也可 docker compose run digest python -m digest preview
CMD ["python", "-m", "digest", "serve"]
