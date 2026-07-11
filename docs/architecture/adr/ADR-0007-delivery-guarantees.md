# ADR-0007 · At-least-once delivery + idempotency + transactional outbox

- **Status:** Accepted
- **Context:** Pipeline stages hop through Redis queues; crashes and retries must
  not corrupt state or skip stages.
- **Decision:** **At-least-once** processing with **idempotent** stages (keyed
  writes via `idempotency_key`) → effectively-once outcomes. A **transactional
  outbox** in Postgres guarantees DB commits and queue publishes cannot diverge;
  a relay publishes outbox rows to Redis.
- **Consequences:** Simpler and cheaper than exactly-once (which Redis alone
  cannot guarantee). Requires every stage to define an idempotency key and every
  emitting write to go through the outbox.
