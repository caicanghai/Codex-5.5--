# Worker Service (placeholder)

**Milestone 0: placeholder — no logic.**

Asynchronous processing for engines and broadcasts. Future responsibility:

- Consume work from Redis-backed queues.
- Run Evidence Intelligence, Interest Catalog, Workflow, and Broadcast steps.
- Respect per-tenant rate limits and tool permission boundaries.

**Boundaries:** no HTTP surface; no direct inbound channel handling.
