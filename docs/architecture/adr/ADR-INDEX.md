# Architecture Decision Record Index

| ADR | Title | Status | Rationale |
|-----|-------|--------|-----------|
| [ADR-0001](./ADR-0001-monorepo.md) | Monorepo vs Polyrepo | ADOPTED | Single Git repo for all services; atomic commits; shared CI/CD. |
| [ADR-0002](./ADR-0002-python-fastapi.md) | Backend Language: Python/FastAPI | ADOPTED (locked) | Mature ML ecosystem; modern async framework; consistency across services. |
| ADR-0003 | Internal Message Envelope Contract | ADOPTED | `ChannelEnvelope` (tenant_id, sender, channel, text, raw_payload) as internal format across all stages. |
| ADR-0004 | One ChannelAdapter Interface | ADOPTED | Single `ChannelAdapter` abstraction; all platforms (Telegram, WhatsApp, WeChat, WeCom, iOS) implement it. Enables new channels without worker changes. |
| [ADR-0005](./ADR-0005-multitenant-rls.md) | Multi-Tenancy: Shared Schema + RLS | ADOPTED | PostgreSQL RLS on all tables; every row has `tenant_id`; session context enforces isolation. Escalation path to schema/DB-per-tenant for regulated tenants. |
| ADR-0006 | Queue/Worker Library (Celery/Arq/…) | OPEN (V6) | Deferred pending v0.1 spike and Architecture Review feedback. Will finalize on interface choice (Python `asyncio` + Redis vs Celery vs Arq). |
| ADR-0007 | At-Least-Once + Idempotency + Outbox | ADOPTED | Tasks may execute >1x; idempotency keys (task_id) prevent data corruption. Transactional outbox for reliable message emission. |
| ADR-0008 | Provider Abstraction (Pluggable) | ADOPTED | All external services (AI, TTS, Search, Storage, Auth, Notifications) behind interfaces. Enables multi-level failover, cost tracking, and swappable implementations. |
| ADR-0009 | Reverse Proxy (Caddy vs nginx) | OPEN | Both viable; Caddy auto-renews TLS (fewer moving parts). Decision deferred to v0.1 deployment. |
| ADR-0010 | Object Storage (MinIO now / S3 later) | ADOPTED | MinIO on local VPS (v0.1–v0.2); migrate to S3/Tencent COS at S3 scaling phase. Interface abstraction allows seamless swap. |
| ADR-0011 | OpenClaw Upstream Binding | PENDING (V1/V2) | Will finalize after add-and-inspect. Binding strategy, extension points, upstream constraints to be documented. |
| ADR-0012 | Plugin SDK as Extension Mechanism | ADOPTED | Dynamic plugin loading; `StagePlugin`, `ProviderPlugin`, `ChannelPlugin` base classes. Plugins loaded from `plugins/` directory at runtime. |

---

## Decision Status Legend

- **ADOPTED** — Locked and implemented.
- **ADOPTED (locked this session)** — Locked in this Architecture Review session; not yet implemented.
- **OPEN** — Under discussion; decision deferred to later milestone.
- **PENDING** — Waiting for external verification (e.g., add-and-inspect).

---

## Open Items (Verification Required Before v1.0)

| Item | Status | Next Step |
|------|--------|-----------|
| V1: OpenClaw upstream binding | PENDING | Add & inspect `openclaw/openclaw`; finalize ADR-0011. |
| V2: OpenClaw API scope & extensibility | PENDING | Review upstream docs; confirm fork necessity. |
| V3: WeChat ecosystem compliance | OPEN | Consult Tencent Weixin documentation + legal. |
| V4: WhatsApp Cloud API production SLA | OPEN | Verify rate limits, cost structure, uptime SLA. |
| V5: WeCom callback + RLS interaction | OPEN | Security review of webhook isolation across tenants. |
| V6: Queue library choice | OPEN | v0.1 spike to evaluate Celery, Arq, native asyncio+Redis. |
| V7: Sizing & failover thresholds | OPEN | Empirical data from v0.2–v0.3 on stage throughput. |
| V8: Regulated/regional deployment | OPEN | China data residency (WeChat/WeCom); GDPR compliance; multi-region strategy. |

---

## Locked Decisions (This Session)

- Backend = Python/FastAPI (ADR-0002).
- TypeScript = web-admin only.
- iOS = Swift (separate repo).

All other ADRs either ADOPTED (pre-existing code/decisions) or OPEN for review and v0.1 implementation.
