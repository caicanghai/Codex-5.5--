# Deliverables 1–2: System Context & Container (C4 Model)

## Deliverable 1: System Context (C4 Level 1)

### Overview

EIOS is a multi-tenant Evidence Intelligence & Omnichannel System that ingests, processes, and broadcasts information across multiple channels (Telegram, WhatsApp, WeChat OA, WeCom) to millions of users. It runs on a single Ubuntu VPS backed by PostgreSQL, Redis, and object storage.

### System Boundary

```
┌─────────────────────────────────────────────────────────────────┐
│ EIOS Platform (Ubuntu VPS, Docker Compose)                      │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ FastAPI Gateway + API + Workers + Scheduler + Data       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
   ↕ (Telegram, WhatsApp, WeChat, WeCom)
   ↕ (External AI/TTS providers)
   ↕ (iOS push notifications via APNs)
```

### Actors

1. **End Users** (millions via Telegram, WhatsApp, WeChat, WeCom, iOS)
   - Send queries, receive AI-powered responses and voice broadcasts.
   - Bind channels (Telegram username, WhatsApp number, WeChat ID, WeCom ID).

2. **Tenant Admins**
   - Manage users, devices, interests, delivery history, and channel bindings.
   - Configure AI/TTS providers, manage rate limits.
   - Review audit logs and manage API keys.

3. **External AI/TTS Providers** (OpenRouter, Fish Audio, ElevenLabs, etc.)
   - Process summarization, embedding, and voice synthesis requests.

4. **Channel Platforms** (Telegram, WhatsApp Meta, WeChat Tencent, WeCom Tencent)
   - Deliver outbound messages and receive inbound webhooks.

5. **APNs (Apple Push Notification service)**
   - Deliver push notifications to iOS devices.

### Key Responsibilities

- **Evidence Ingestion & Processing** — Collect messages/URLs, normalize, deduplicate, extract claims, cross-validate, score confidence, and broadcast.
- **Multi-Tenant Isolation** — Every user and message belongs to a tenant; no cross-tenant data leakage.
- **Omnichannel Delivery** — Dispatch a single message to multiple channels simultaneously.
- **Scalability** — Queue-based workers allow horizontal scaling per pipeline stage.

---

## Deliverable 2: Container (C4 Level 2)

### Architectural Layers

```
┌─────────────────────────────────────────────────────────────────┐
│ Reverse Proxy (Caddy / nginx) — TLS termination, edge rate limit │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   ┌─────────┐        ┌─────────┐       ┌─────────┐
   │ Gateway │        │   API   │       │ Webhook │
   │ (Recv)  │        │(Query)  │       │ (Recv)  │
   └────┬────┘        └────┬────┘       └────┬────┘
        │                  │                  │
        │ Enqueue          │ Enqueue          │ Enqueue
        │ Inbound          │ Command          │ Inbound
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │  Redis Queue (Stage 1: Collect)     │
        └──────────────────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │  Worker Pool (12-stage pipeline)    │
        │  (Scales horizontally)              │
        └──────────────────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │  PostgreSQL + RLS (Tenant data)     │
        │  Redis (Cache, rate-limit state)    │
        │  MinIO (Documents, media)           │
        └─────────────────────────────────────┘
```

### Container Details

#### 1. **Reverse Proxy**
- **Technology**: Caddy or nginx `[ASSUMED — ADR-0009]`
- **Responsibilities**:
  - TLS termination (HTTPS).
  - Route `/webhook/*` to Gateway; `/api/*` to API.
  - Edge rate limiting (per-IP, per-tenant).
  - Health checks, log access logs.
- **Scaling**: Single instance at launch; if CPU-bound, move to separate node (S4).

#### 2. **Gateway (FastAPI)**
- **Responsibilities**:
  - Receive webhooks from Telegram, WhatsApp, WeChat, WeCom.
  - Verify webhook signatures (OAuth + crypto).
  - Parse inbound message, extract user/channel context.
  - Enqueue to Redis Stage 1 (`inbound_queue`).
  - Return 200 OK immediately (async processing).
- **Scaling**: 1–3 replicas; I/O bound (webhook parsing + queue push).
- **No database queries** (except cache lookups for channel credentials and webhook signatures).

#### 3. **API (FastAPI)**
- **Responsibilities**:
  - Serve REST endpoints: `/api/v1/auth`, `/api/v1/users`, `/api/v1/channels`, `/api/v1/history`, `/api/v1/admin`.
  - Tenant-scoped queries (all routes enforce RLS).
  - Enqueue commands to workers (e.g., trigger broadcast, bind channel).
  - Serve OpenAPI schema.
- **Scaling**: 1–3 replicas; CPU/DB-bound.
- **Auth**: Bearer token (JWT `[ASSUMED]`) or API key (scoped, hashed at rest).

#### 4. **Worker Pool**
- **Technology**: Arq or Celery `[ASSUMED — ADR-0006, deferred V6]`
- **Responsibilities**:
  - Pull tasks from Redis queues (one queue per pipeline stage).
  - Execute the stage logic (Normalize, Deduplicate, Document, Extract, Resolve, etc.).
  - Push results to the next stage queue (except final stage, which writes to DB).
  - Log errors; push to DLQ on failure.
- **Scaling**: Replicas per stage (e.g., 3× Normalize, 5× Extract, 2× Send).
- **No shared state** — all isolation via Redis queues and DB RLS.

#### 5. **Scheduler**
- **Technology**: APScheduler or Celery Beat `[ASSUMED]`
- **Responsibilities**:
  - Trigger periodic tasks (e.g., backups, dead-letter-queue (DLQ) retry).
  - Broadcast scheduled messages.
- **Scaling**: Single instance (singleton pattern, leader election if HA is needed later).

#### 6. **PostgreSQL**
- **Tenant/User/Device/Evidence/Broadcast/Delivery** tables.
- **Row-Level Security (RLS)** on all tables; session context `SET app.tenant_id`.
- **Backups**: Nightly logical dumps + continuous WAL archiving.
- **Scaling**: Managed PostgreSQL or larger VPS node (S2); read replicas for history queries (S2).

#### 7. **Redis**
- **12 stage queues** (one per pipeline stage).
- **Cache** (credentials, user sessions, metadata).
- **Rate-limit state** (sliding window counters per tenant/user).
- **Scaling**: Local Redis at launch; persistence (RDB + AOF) enabled; HA with Sentinel (S4).

#### 8. **MinIO (Object Storage)**
- **Document storage** (uploaded PDFs, web scrapes).
- **Media cache** (downloaded images, audio clips).
- **Backups** (versioning, periodic replication to offsite bucket).
- **Scaling**: Local MinIO at launch; external S3 at S3 phase.

---

## Key Architectural Decisions (C2 Level)

- **Async everything** — Gateway and API enqueue; workers process asynchronously.
- **No shared memory** — All cross-component state via Redis queues or PostgreSQL.
- **Tenant context propagation** — `tenant_id` in every message, every row, every cache key, every log.
- **Provider abstraction** — AI/TTS/Search/Embedding behind interfaces; pluggable implementations.
- **Single VPS deployment** — All containers on one machine at launch; scale horizontally when needed.
