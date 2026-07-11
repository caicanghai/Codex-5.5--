# 11 — Milestone Roadmap v0.1 → v1.0

Deliverable **25**. Each version is additive and gated on the previous one.
No business feature is built before its milestone. External-channel milestones
are gated on their verification items (V3–V6).

---

| Version | Theme | Delivers | Gates |
|---------|-------|----------|-------|
| **v0.1** | Platform skeleton | Python toolchain migration; `gateway`/`api`/`worker`/`scheduler` boot as empty shells; **Envelope contract v0**; health + structured logging; first real (empty) migration baseline; **OpenClaw added & inspected → ADR-0011 finalized**. | V1/V2 |
| **v0.2** | Identity & tenancy | tenants/users/devices/api-keys; AuthN; RBAC; **RLS**; audit log; API-key isolation; webhook-verification scaffold. | — |
| **v0.3** | Ingestion & evidence core | Collect → Normalize → Deduplicate; `RawItem`/`Document`; object storage; provider interfaces (Model/Search/Embedding). | — |
| **v0.4** | Evidence intelligence | Extract Claims → Resolve Sources → Cross-Validate → Detect Conflicts → Score Confidence → Summarize; end-to-end provenance. | — |
| **v0.5** | Interests & matching | interests/topics; Interest Matching; feedback-loop scaffolding. | — |
| **v0.6** | Delivery core + first channel | Broadcast Engine; **one ChannelAdapter end-to-end (Telegram first [ASSUMED simplest])**; per-tenant rate limiting. | — |
| **v0.7** | Voice + push | `TTSProvider` + APNs `NotificationProvider`; **iOS receives push + voice broadcast**. | V6 |
| **v0.8** | More channels | WhatsApp Cloud, WeChat OA, WeCom via the **same** adapter interface. | V3, V4, V5 |
| **v0.9** | Hardening | monitoring/tracing; backups + **DR drill**; scaling phase S1; security review; Plugin SDK GA. | V7 |
| **v1.0** | GA | Thousands of users; full self-service — login, manage interests, bind Telegram/WhatsApp/WeChat, manage API keys, choose AI/TTS providers, receive voice broadcasts + push, review history, manage devices — with **complete tenant isolation**. | V8 |

## Cross-cutting exit criteria (every version)

- No cross-tenant data access; isolation keys present on all new entities.
- No business logic in channel adapters; all external services behind provider
  interfaces.
- Any new pipeline work preserves the 12-stage order (no stage skipped).
- CI green (lint, type/style check, tests, build, docker validation, secret
  scan); changes flow through PRs.

## Relationship to the prior EIOS roadmap

This supersedes the milestone table in `docs/ROADMAP.md` by adding the
production `v0.1–v1.0` sequence. `docs/ROADMAP.md`'s Milestone 0–5 framing
remains valid at a coarser grain; on approval the two will be reconciled
(documentation-only change).
