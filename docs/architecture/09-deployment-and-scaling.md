# Deliverables 17–19: Deployment, Docker Compose & Scaling

## Deliverable 17: Deployment Topology (Single VPS at Launch)

```
┌─────────────────────────────────────────────────────────┐
│ Ubuntu VPS (t3.medium or similar, 2 CPU, 4 GB RAM)      │
│                                                          │
│ ┌──────────────────────────────────────────────────┐   │
│ │ Caddy / nginx (Reverse Proxy)                    │   │
│ │  - TLS termination                               │   │
│ │  - Route /webhook/* → Gateway                    │   │
│ │  - Route /api/* → API                            │   │
│ │  - Rate limiting (edge)                          │   │
│ │  - Healthchecks                                  │   │
│ └────────────────┬─────────────────────────────────┘   │
│                  │                                       │
│ ┌────────────┬───┴────┬─────────────┐                   │
│ │            │        │             │                   │
│ ▼            ▼        ▼             ▼                   │
│ Gateway    API     Worker×3      Scheduler             │
│ (1×)       (1×)    (per stage)     (1×)                │
│                                                          │
│ ┌──────────────────────────────────────────────────┐   │
│ │ Stateful Services (Private Docker network)       │   │
│ │  - PostgreSQL                                    │   │
│ │  - Redis                                         │   │
│ │  - MinIO                                         │   │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Key Properties**:
- Single VPS for all services (cost-effective at launch).
- Private Docker network (no service exposed except proxy).
- Reverse proxy terminates TLS, handles rate limiting.
- All state in PostgreSQL, Redis, MinIO (backed up).
- Secrets injected via environment or secrets file (never in images).

---

## Deliverable 18: Docker Compose Topology

### Files Structure

```
deployments/
├── docker-compose.dev.yml          # Local dev
├── docker-compose.prod.yml         # Production
├── env/
│   ├── .env.example                # Shape only
│   ├── .env.dev                    # Dev defaults (git-ignored)
│   └── .env.prod                   # Prod template (git-ignored, secured)
└── scripts/
    ├── backup.sh
    ├── restore.sh
    └── healthcheck.sh
```

### docker-compose.prod.yml (Essential Services)

```yaml
version: '3.8'

services:
  proxy:
    image: caddy:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    networks:
      - eios-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s

  gateway:
    image: eios-gateway:latest
    environment:
      - DATABASE_URL=postgresql://eios:change_me@postgres:5432/eios
      - REDIS_URL=redis://redis:6379/0
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - WECOM_ENABLED=${WECOM_ENABLED}
      - WECOM_CORP_ID=${WECOM_CORP_ID}
      - WECOM_TOKEN=${WECOM_TOKEN}
      - WECOM_AES_KEY=${WECOM_AES_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - eios-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]

  api:
    image: eios-api:latest
    environment:
      - DATABASE_URL=postgresql://eios:change_me@postgres:5432/eios
      - REDIS_URL=redis://redis:6379/0
      - AI_API_KEY=${AI_API_KEY}
      - AI_BASE_URL=${AI_BASE_URL}
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - eios-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]

  worker:
    image: eios-worker:latest
    environment:
      - DATABASE_URL=postgresql://eios:change_me@postgres:5432/eios
      - REDIS_URL=redis://redis:6379/0
      - WORKER_STAGE=${WORKER_STAGE}  # or omit for all stages
      - WORKER_CONCURRENCY=4
    deploy:
      replicas: 3  # Scale per stage
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - eios-net

  scheduler:
    image: eios-scheduler:latest
    environment:
      - DATABASE_URL=postgresql://eios:change_me@postgres:5432/eios
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - eios-net

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=eios
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=eios
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-rls.sql:/docker-entrypoint-initdb.d/init-rls.sql
    networks:
      - eios-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U eios"]
      interval: 10s
      timeout: 5s

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - eios-net
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

  minio:
    image: minio/minio:latest
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=${MINIO_PASSWORD}
    volumes:
      - minio_data:/minio/data
    networks:
      - eios-net
    command: minio server /minio/data

volumes:
  postgres_data:
  redis_data:
  minio_data:
  caddy_data:
  caddy_config:

networks:
  eios-net:
    driver: bridge
```

### Environment Variables

```env
# .env.prod.example (source before running docker-compose)
POSTGRES_PASSWORD=<strong-random-password>
TELEGRAM_BOT_TOKEN=<bot-token>
TELEGRAM_OWNER_ID=<your-telegram-id>
WECOM_ENABLED=true
WECOM_CORP_ID=ww0b1b3e2c9a997135
WECOM_AGENT_ID=<agent-id>
WECOM_SECRET=<secret>
WECOM_TOKEN=<token>
WECOM_AES_KEY=<aes-key>
AI_API_KEY=<openrouter-key>
AI_BASE_URL=https://openrouter.ai/api/v1
MINIO_PASSWORD=<strong-password>
```

---

## Deliverable 19: Scaling Roadmap (S0 → S5)

| Phase | Trigger | Action |
|-------|---------|--------|
| **S0: Launch** | Day 1 | All-in-one Compose; 2–3 worker replicas (shared stages). |
| **S1: Queue pressure** | Extract/Summarize queue depth > 50 | Dedicated Extract workers (3→5), Summarize (2→3). Separate TTS workers. |
| **S2: Database bottleneck** | DB CPU/connections sustained > 80% | Managed PostgreSQL (bigger node); add read replicas for history queries. |
| **S3: Storage growth** | Local MinIO approaching disk limit | External S3 (AWS, Tencent COS); keep versioning + replication. |
| **S4: Multi-node** | VPS resources exhausted | Split proxy / api / workers / data onto separate nodes. Redis HA (Sentinel). |
| **S5: Regional** | Multi-country users / China compliance | Region-split deployment (esp. V8 WeChat/WeCom); per-region data plane. |

### Per-Stage Scaling Example (S0 → S1)

```yaml
# S0 (docker-compose.prod.yml)
worker:
  deploy:
    replicas: 3  # Generic, all stages

# S1 (docker-compose.prod.s1.yml)
worker-extract:
  image: eios-worker:latest
  environment:
    - WORKER_STAGE=extract
  deploy:
    replicas: 5  # Dedicated Extract pool

worker-summarize:
  image: eios-worker:latest
  environment:
    - WORKER_STAGE=summarize
  deploy:
    replicas: 3  # Dedicated Summarize pool

worker-broadcast:
  image: eios-worker:latest
  environment:
    - WORKER_STAGE=broadcast
  deploy:
    replicas: 3  # Dedicated Broadcast pool

# ... other stages on shared workers
```

### Cost Projection (S0 → S1 → S2)

| Phase | Infrastructure | Monthly Cost | Users |
|-------|---|---|---|
| S0 | 1 VPS (t3.medium) | ~$30 | 100–1K |
| S1 | 2 VPS (1 app, 1 data) | ~$60 | 1K–10K |
| S2 | 3+ nodes + managed PG | ~$200+ | 10K+ |

---

## Key Design for Scaling

✅ **Stateless app tiers** — Any service can scale up/down; no persistent state.  
✅ **Per-stage queues** — Extract/Summarize can scale independently of others.  
✅ **Provider abstraction** — Multi-AI strategy (failover) prevents single vendor lock-in.  
✅ **Tenant-namespaced storage/cache** — No global key space; isolation baked in.
