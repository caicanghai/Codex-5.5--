# Deliverable 25: Milestone Roadmap v0.1 → v1.0

## Version Releases

### v0.1: Platform Skeleton
**Goal**: Empty but working platform; all infrastructure wired up.

**Deliverables**:
- Python migration complete (gateway, api, worker, scheduler all in Python/FastAPI).
- Envelope contract v0 finalized (internal message format).
- Docker Compose (dev + prod) working; healthchecks passing.
- Logging & structured JSON output.
- First RLS policies in PostgreSQL.
- CI/CD pipeline (lint, test, build, secret scan).
- OpenClaw added & inspected → ADR-0011 final.
- Empty worker pipeline (all 12 stages exist; execute but no-op).

**Milestone gate**: Architecture Review approval + implementation review.

---

### v0.2: Identity & Tenancy
**Goal**: Tenants, users, devices, authentication, RBAC, and audit.

**Features**:
- User registration (email + passkey `[ASSUMED]`).
- Tenant provisioning & admin panel.
- JWT-based authentication.
- API key issuance, scoping, and hashing.
- Role-based access control (owner, admin, member, service).
- Row-Level Security (RLS) on all tables.
- Audit events (append-only log).
- Device registration (iOS; stores APNs token).
- Channel bindings (user → Telegram/WhatsApp/WeChat/WeCom).

**API routes**: `/auth`, `/tenants`, `/users`, `/devices`, `/api-keys`, `/channel-bindings`.

---

### v0.3: Ingestion & Evidence Core
**Goal**: Ingest messages/URLs, normalize, deduplicate, store as documents.

**Features**:
- Webhook receivers (Gateway for all 5 channels).
- Signature verification (per-platform crypto).
- Message parsing (extract text, media, metadata).
- Normalize stage (text cleaning, language detection).
- Deduplicate stage (check if seen before).
- Document storage (title, content, source URL).
- Object storage integration (MinIO; store docs, media).
- Provider interfaces (AI, TTS, Search, Storage, Auth).

**Pipeline stages**: 1–4 (Collect, Normalize, Deduplicate, Document).

---

### v0.4: Evidence Intelligence
**Goal**: Extract claims, cross-validate, detect conflicts, score confidence, summarize.

**Features**:
- Extract stage (LLM extract claims from document).
- Resolve stage (link claims to knowledge base).
- Cross-Validate stage (web search, corroboration).
- Detect Conflicts stage (check for contradictions).
- Score stage (assign confidence score).
- Summarize stage (generate short summary).
- Multi-level fallback (Extract/Summarize with offline alternatives).

**Pipeline stages**: 5–10.

---

### v0.5: Interests & Matching
**Goal**: Users define interests; evidence matched to interests.

**Features**:
- Interest CRUD (user topics).
- Interest matching rules (keyword, NLP, ML model `[ASSUMED]`).
- Feedback mechanism (user says "relevant" or "not relevant").
- Matching engine (stage 11).
- Feedback loop (use feedback to retrain matchers).

**Pipeline stage**: 11.

---

### v0.6: Delivery Core + First Channel (Telegram)
**Goal**: Broadcast engine + end-to-end Telegram delivery.

**Features**:
- Broadcast engine (create broadcast for matched users).
- Delivery tracking (pending, sent, failed, retrying, exhausted).
- Dedup (same evidence × user × channel = one delivery).
- Telegram ChannelAdapter (send text + voice via Bot API).
- Rate limiting per user/tenant.
- Delivery history API.

**Pipeline stage**: 12 (Broadcast).

**Testing**: Full end-to-end: user sends message via Telegram → evidence pipeline → summary broadcast back to users.

---

### v0.7: Voice + Push
**Goal**: TTS provider integration + iOS push notifications.

**Features**:
- TTSProvider interface (Fish Audio, ElevenLabs, Edge TTS).
- Voice synthesis (broadcast includes voice message option).
- APNs NotificationProvider (iOS push).
- Device management (APNs tokens per device).
- iOS webhook (APNs delivery confirmation).

**Channels**: Telegram (with voice), iOS (push + voice).

---

### v0.8: More Channels (WhatsApp, WeChat, WeCom)
**Goal**: Multi-channel broadcast.

**Gated on**: V3 (WeChat compliance), V4 (WhatsApp SLA), V5 (WeCom isolation).

**Features**:
- WhatsApp ChannelAdapter (Cloud API).
- WeChat OA ChannelAdapter.
- WeCom ChannelAdapter (enterprise).
- Channel binding flow (QR code, OTP verification per platform).
- Per-channel rate limits.

**Broadcast reach**: 5 channels (Telegram, WhatsApp, WeChat, WeCom, iOS).

---

### v0.9: Hardening
**Goal**: Production-ready: monitoring, backups, security, scalability.

**Features**:
- Prometheus metrics + Grafana dashboards.
- OpenTelemetry tracing.
- Backup strategy (nightly dumps, WAL archiving, MinIO versioning).
- Disaster recovery runbook + drills.
- Scaling S1 (per-stage worker pools).
- Security review (OWASP, crypto, secret handling).
- Plugin SDK v1 (extensibility for stages, providers, channels).
- Load testing (1K concurrent users, simulate v0.8 spike).

---

### v1.0: GA (General Availability)
**Goal**: Full self-service, thousands of users, production SLA.

**Features**:
- User registration + email verification.
- Self-serve interest management.
- Channel binding (all 5 platforms).
- Broadcast history + replay.
- Device management (add/remove iOS devices).
- API key management (create/revoke/rotate).
- Provider choice (users can select AI/TTS providers, submit keys).
- Feedback mechanism (evidence relevance → improve matching).
- Admin dashboard (tenant admins manage users, view audit).
- Audit log export (compliance).
- GDPR compliance (data export, deletion).
- SLA monitoring (99% uptime, p99 latency < 2s).

**Metrics**: Thousands of users, hundreds of thousands of messages/day, multi-tenant isolation verified.

---

## Milestone Timeline (Estimate)

| Milestone | Duration | Status |
|-----------|----------|--------|
| v0.1 | 2 weeks | Sprint 1 |
| v0.2 | 3 weeks | Sprint 2–3 |
| v0.3 | 2 weeks | Sprint 4 |
| v0.4 | 3 weeks | Sprint 5–6 (LLM integration) |
| v0.5 | 2 weeks | Sprint 7 |
| v0.6 | 2 weeks | Sprint 8 (Telegram end-to-end) |
| v0.7 | 2 weeks | Sprint 9 (TTS + APNs) |
| v0.8 | 4 weeks | Sprint 10–11 (multiple channels) |
| v0.9 | 3 weeks | Sprint 12–13 (hardening) |
| v1.0 | 2 weeks | Sprint 14 (final polish + GA) |

**Total**: ~24 weeks (~6 months) from architecture approval to v1.0 GA.

---

## Success Criteria

- ✅ All 12 pipeline stages execute end-to-end for every message.
- ✅ Multi-tenant isolation enforced at DB layer (RLS) + application layer.
- ✅ Evidence broadcast to ≥2 channels (e.g., Telegram + iOS).
- ✅ Provider failover tested (Extract fallback if OpenRouter fails).
- ✅ Backups working; restore tested weekly.
- ✅ Load test: 1000 concurrent users, <2s p99 latency.
- ✅ Audit trail 100% complete (no sensitive actions missed).
- ✅ Security review passed (OWASP, crypto, secret handling).
- ✅ Documentation complete (architecture, API, deployment, runbooks).
