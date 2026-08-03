# talk-to-fengge 容器镜像（实时语音分身 worker / web_server）
#
# 用法：把 talk-to-fengge-src.tar.gz 解压到本目录 src/（含 pyproject.toml、worker/、web/）。
# 依赖安装与交接文档一致：uv 装 pyproject 依赖 + 额外的 cartesia/deepgram/openai/elevenlabs 插件。
# LiveKit 服务器不在本镜像内，用官方 livekit/livekit-server 镜像单独跑（见 compose）。

FROM python:3.12-slim

# ffmpeg 供音频处理；curl 供 uv 安装
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY src/ ./

# 安装项目依赖 + 交接文档里额外补装的插件（elevenlabs 克隆音色 / cartesia STT / deepseek）
RUN uv pip install --system -e . \
    && uv pip install --system \
    "livekit-agents[cartesia,deepgram,openai,google]~=1.6" \
    "livekit-plugins-elevenlabs~=1.6"

ENV PYTHONUNBUFFERED=1

# 默认起 agent worker；web_server 由 compose 覆盖 command 起（见 fengge-web 服务）
CMD ["python", "-m", "worker.main", "start"]
