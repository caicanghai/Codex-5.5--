# ADR-0006 · Queue / worker library

- **Status:** Proposed (open — pending V7 volume sizing)
- **Context:** The pipeline uses per-stage queues on Redis. The Python library
  choice affects async ergonomics, retries, scheduling, and observability.
- **Options:** Celery (mature, broad), Arq (async-native, pairs with FastAPI),
  Dramatiq, RQ (simplest).
- **Decision:** **Deferred.** Leaning Arq or Celery. Pick once expected
  throughput and scheduling needs are confirmed (open item V7).
- **Consequences:** The `packages/messaging` abstraction wraps the queue so the
  library can be chosen/changed without touching worker business code.
