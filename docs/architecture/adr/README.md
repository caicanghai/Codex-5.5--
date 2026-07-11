# Architecture Decision Records (production architecture)

Deliverable **24**. These ADRs cover the production architecture and complement
the foundational ADRs in [`docs/DECISIONS.md`](../../DECISIONS.md). Format:
Context · Decision · Status · Consequences. Supersede rather than edit.

| ADR | Title | Status |
|-----|-------|--------|
| [0001](./ADR-0001-monorepo-vs-polyrepo.md) | Monorepo vs polyrepo | Accepted |
| [0002](./ADR-0002-language-and-framework.md) | Backend language & framework | Accepted (Python/FastAPI) |
| [0003](./ADR-0003-message-envelope.md) | Internal message Envelope | Accepted |
| [0004](./ADR-0004-single-channel-adapter.md) | One ChannelAdapter interface | Accepted |
| [0005](./ADR-0005-multitenancy-rls.md) | Multi-tenancy: shared-schema + RLS | Accepted |
| [0006](./ADR-0006-queue-library.md) | Queue / worker library | Proposed (open) |
| [0007](./ADR-0007-delivery-guarantees.md) | At-least-once + idempotency + outbox | Accepted |
| [0008](./ADR-0008-provider-abstraction.md) | Provider abstraction for external services | Accepted |
| [0009](./ADR-0009-reverse-proxy.md) | Reverse proxy choice | Proposed (open) |
| [0010](./ADR-0010-object-storage.md) | Object storage: MinIO now, S3 later | Accepted |
| [0011](./ADR-0011-openclaw-upstream-binding.md) | OpenClaw upstream binding | Proposed (pending V1/V2) |
| [0012](./ADR-0012-plugin-sdk.md) | Plugin SDK as extension mechanism | Accepted |
