# Deliverables 8–9: Queue & Worker Architecture

## Deliverable 8: Queue Architecture

### Queue Topology

```
┌─────────────────────────────────────────────────┐
│ Redis (Single instance at launch; HA via S4)    │
├─────────────────────────────────────────────────┤
│                                                  │
│  Queue 1: inbound_<stage1>      (1 queue/stage) │
│  Queue 2: inbound_<stage2>                      │
│  ...                                            │
│  Queue 12: inbound_<stage12>                    │
│                                                  │
│  DLQ: failed_tasks (poison messages)            │
│  Cache: credentials, interests, knowledge       │
│  Rate-limit state: (tenant_id, user_id)        │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Queue Characteristics

- **Technology**: Arq or Celery `[ASSUMED — ADR-0006, V6]`
- **Delivery guarantee**: At-least-once (with idempotency keys for safety).
- **Message format**: JSON envelope with `tenant_id`, `task_id`, `attempt_count`, `payload`.
- **TTL**: 24 hours (messages older than 24h auto-expire; retry to DLQ).
- **Persistence**: Redis AOF enabled (logs all operations); RDB snapshots for faster recovery.
- **Size per message**: ~1–10 KB (small metadata + IDs; large payloads stored in MinIO + referenced via key).

### Message Envelope

```json
{
  "task_id": "uuid",
  "tenant_id": "uuid",
  "stage": "extract",
  "attempt": 1,
  "enqueued_at": "2026-08-03T12:34:56Z",
  "timeout_at": "2026-08-03T12:35:56Z",
  "payload": {
    "document_id": "uuid",
    "raw_content": "Text or reference to MinIO key"
  },
  "trace_id": "uuid"  // For distributed tracing
}
```

### Scaling Model

- **Queue depth monitoring**: Prometheus metrics on queue length per stage.
- **Auto-scaling trigger**: When queue depth > threshold, deploy additional worker replicas (Kubernetes style; manual scaling for Docker Compose at launch).
- **Per-stage scaling**: Extract + Summarize scale faster (LLM bottleneck); Document + Deduplicate scale slower (query-heavy).

---

## Deliverable 9: Worker Stage Mapping

### Worker Classes

| Worker Class | Stages | Replicas | Purpose |
|---|---|---|---|
| Collect Worker | 1 | 2 | Parse webhook, enqueue to stage 2 |
| Normalize Worker | 2 | 2 | Text cleaning, language detection |
| Dedup Worker | 3 | 1 | Query DB for existing documents |
| Document Worker | 4 | 3 | Store document, object upload |
| Extract Worker | 5 | 3–5 | LLM extraction (bottleneck) |
| Resolve Worker | 6 | 2 | Knowledge base linking |
| CrossValidate Worker | 7 | 2 | Web search, corroboration |
| ConflictDetect Worker | 8 | 1 | Conflict detection query |
| Score Worker | 9 | 1 | Confidence scoring |
| Summarize Worker | 10 | 2–3 | LLM summarization (bottleneck) |
| InterestMatch Worker | 11 | 2 | Interest matching + NLP |
| Broadcast Worker | 12 | 3–5 | Send via ChannelAdapter |

### Worker Lifecycle

```
Worker starts
    ↓
Connect to Redis, database, configure tenant context
    ↓
Poll queue (stage 1, 2, 3, ...)
    ↓ (message available)
Pull message from queue
    ↓
SET app.tenant_id = message.tenant_id (RLS context)
    ↓
Execute stage logic (Extract, Summarize, etc.)
    ↓
On success:
    - Mark message processed
    - Push to next stage queue (or DB if final stage)
    - Emit success metric
    ↓
On failure:
    - Increment attempt counter
    - If attempts < max: re-enqueue with backoff delay
    - If attempts >= max: push to DLQ, emit alert
    ↓
(Loop back to poll)
```

### Error Handling & Retry

- **Transient errors** (network, timeout): Exponential backoff (1s, 2s, 4s, 8s, 16s).
- **Permanent errors** (invalid claim format, storage full): Push to DLQ immediately.
- **Max attempts**: 3 for most stages; 5 for Broadcast (higher tolerance for delivery retries).
- **DLQ processing**: Periodic job (Scheduler) attempts replay of old DLQ items; logs for manual review.

### Stateless by Design

- **No in-memory state** — Workers pull from queue, compute, push to next queue/DB; no local cache.
- **Tenant context injection** — `tenant_id` from message envelope; RLS enforced at DB layer.
- **Horizontal scaling** — Workers are stateless; scale up/down freely.
- **No worker-to-worker messaging** — All communication via Redis queues or database.

### Worker Configuration (Environment)

```env
WORKER_STAGE=extract          # Which stage(s) this worker handles
WORKER_CONCURRENCY=4          # Async tasks per worker process
WORKER_TIMEOUT=300            # Seconds per task
WORKER_MAX_RETRIES=3
WORKER_RETRY_BACKOFF=exponential
```

### Monitoring & Observability

- **Queue depth per stage** (Prometheus gauge).
- **Task latency per stage** (histogram, p50/p99).
- **Error rate per stage** (counter).
- **DLQ size** (alert if > threshold).
- **Worker CPU/memory** (standard container metrics).

---

## Architecture Diagram (All Stages)

```
┌─────────────┐
│   Gateway   │  Webhook receiver
└──────┬──────┘
       │ enqueue(stage1)
       ↓
┌──────────────────────────────────────────────────────┐
│ Redis Queues (12 stages + DLQ)                       │
├──────────────────────────────────────────────────────┤
│  [Collect] [Normalize] [Dedup] ... [Broadcast] [DLQ] │
└──┬──┬──┬──────────────┬──────────────┬──┬──┬──┬─────┘
   │  │  │              │              │  │  │  │
   ▼  ▼  ▼              ▼              ▼  ▼  ▼  ▼
 [W1][W1][W2]        [W5][W5][W5]    [W12]    [DLQ]
 [W1][W2][W2]        [W5][W5]        [W12]    Processor
 [W2]                [W5]            [W12]
                                     [W12]
       (Worker Pool, scales horizontally)
       ↓
   PostgreSQL (RLS enforced, tenant_id in context)
   + MinIO (object storage)
   + Redis cache
```

---

## Key Invariants (Verified Principle)

- ✅ **At-least-once delivery** — Tasks may execute twice; idempotency keys ensure no data corruption.
- ✅ **No stage skipped** — Even if a stage is fast/empty, it still executes.
- ✅ **Tenant isolation in queue messages** — Every message carries `tenant_id`; workers set RLS context.
- ✅ **No cross-worker shared state** — All state in Redis queues or PostgreSQL (no in-memory worker state).
