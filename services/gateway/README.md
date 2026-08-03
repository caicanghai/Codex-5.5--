# Gateway Service (placeholder)

**Milestone 0: placeholder — no logic.**

The Unified Channel Gateway edge. Its future responsibility:

- Terminate inbound channel traffic and verify webhooks (signatures, replay).
- Normalize every message to the internal envelope
  ([`../../schemas/envelope`](../../schemas/envelope)).
- Route normalized messages to downstream engines.
- Enforce per-tenant rate limiting at the edge.

**Boundaries:** transport + normalization only — **no business logic**.
