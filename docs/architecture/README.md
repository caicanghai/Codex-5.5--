# EIOS Architecture Blueprint v0.1

**Status**: Documentation only — no business logic implemented.  
**Milestone**: 0 (Repository Foundation) approved; Architecture Blueprint in review.

---

## Overview

EIOS (Evidence Intelligence & Omnichannel System) is a production-grade cloud platform designed for multi-tenant deployment on a single Ubuntu VPS with Docker Compose. This documentation contains the complete architecture blueprint comprising 25 deliverables across 11 files + Architecture Decision Records.

### Scope

- **In scope**: Platform architecture, data model, pipeline, deployment, scaling roadmap, and monitoring strategy.
- **Out of scope**: Business feature implementation, Directus, n8n, iOS app code (Swift, separate repo).
- **Branch**: `claude/eios-repository-foundation-hoi3u8`
- **Backend language**: Python/FastAPI (see ADR-0002).

---

## Deliverable Map

| # | Deliverable | File |
|---|-------------|------|
| 1 | System Context (C4 Level 1) | `00-context-and-containers.md` |
| 2 | Container (C4 Level 2) | `00-context-and-containers.md` |
| 3 | Repository Architecture | `01-repository-architecture.md` |
| 4 | DDD Boundaries | `02-domain-model.md` |
| 5 | Domain Model | `02-domain-model.md` |
| 6 | Database ERD | `03-data-model-erd.md` |
| 7 | 12-Stage Evidence Pipeline | `04-evidence-pipeline.md` |
| 8 | Queue & Worker Architecture | `05-queues-and-workers.md` |
| 9 | Worker Stage Mapping | `05-queues-and-workers.md` |
| 10 | Gateway Architecture | `06-gateway-and-channels.md` |
| 11 | Provider Interface | `07-providers-and-plugins.md` |
| 12 | Plugin Architecture | `07-providers-and-plugins.md` |
| 13 | Channel Adapter | `06-gateway-and-channels.md` |
| 14 | REST API Boundaries | `08-api-auth-tenancy.md` |
| 15 | Authentication & RBAC | `08-api-auth-tenancy.md` |
| 16 | Multi-Tenant Strategy | `08-api-auth-tenancy.md` |
| 17 | Deployment Topology | `09-deployment-and-scaling.md` |
| 18 | Docker Compose Topology | `09-deployment-and-scaling.md` |
| 19 | Scaling Roadmap | `09-deployment-and-scaling.md` |
| 20 | Monitoring & Logging | `10-operations.md` |
| 21 | Backup Strategy | `10-operations.md` |
| 22 | Disaster Recovery | `10-operations.md` |
| 23 | Secrets Management | `10-operations.md` |
| 24 | Architecture Decision Records | `adr/ADR-00xx-*.md` |
| 25 | Milestone Roadmap v0.1→v1.0 | `11-milestone-roadmap.md` |

---

## Verification Legend

Every material statement is tagged with one of:

- **`[VERIFIED]`** — Fact or principle enforced in existing code or locked decision (e.g., no secrets in git, tenant_id on every entity, Telegram channel implemented).
- **`[VERIFIED principle]`** — Architectural invariant or design pattern that is enforced or must be enforced (e.g., provider abstraction, no global state).
- **`[ASSUMED]`** — Fact or configuration choice not yet verified; requires confirmation in later milestone phases. Typically external dependencies (AI backend choice, reverse proxy vendor, queue library) or unfinished features (OAuth, APNs integration, China deployment).
- **`[ASSUMED — ADR-00xx]`** — Assumption that is explicitly captured as an Architecture Decision Record for later review and revision.

### Open Verification Items (V1–V8)

These are known unknowns and must be resolved before production release or next major phase:

1. **V1: OpenClaw upstream binding** — Once `openclaw/openclaw` is added to the session and inspected, ADR-0011 finalizes the concrete binding, extension points, and any upstream constraints.

2. **V2: OpenClaw API scope & limitation** — What can/cannot be extended; how it is licensed; whether a fork is ever needed or if all customization is via the plugin SDK.

3. **V3: WeChat ecosystem compliance** — Which Tencent/WeChat integration layers are available and supported; data residency requirements for China deployment (V8).

4. **V4: WhatsApp Cloud API production readiness** — Rate limits, SLA, and cost structure for production volumes (thousands of users).

5. **V5: WeCom callback & RLS interaction** — Ensure that WeCom webhook callbacks (which may carry cross-tenant sensitive data) are properly isolated and don't leak across row-level security boundaries.

6. **V6: Queue library choice (Arq/Celery/other)** — ADR-0006 deferred pending architecture review and v0.1 spike. Library decision unlocks worker interface, retry/DLQ strategy, and deployment topology.

7. **V7: Sizing & failover thresholds** — Empirical data from v0.2–v0.3 stages on per-stage throughput, latency p99, and automatic failover trigger points (e.g., when to escalate Telegram delivery to a retry worker).

8. **V8: Regulated/regional deployment** — China-specific data residency (WeChat/WeCom), GDPR compliance, and whether multi-region or multi-tenancy requires schema/database separation instead of shared-schema RLS. Escalation path defined but deferred to v0.5+.

---

## Critical Provenance Caveat

**This repository is NOT OpenClaw.** OpenClaw's real internals are unverified until the add-and-inspect step runs (step 1 of Execution Plan below). Every statement about OpenClaw internals is marked `[ASSUMED — requires verification]` until ADR-0011 is finalized.

---

## Execution Plan (Architecture Review gate)

**Nothing is committed or pushed until the Architecture Review approves this blueprint.** Steps below are documentation/scaffolding only.

1. **Add & inspect OpenClaw** (requires interactive `add_repo` approval):
   - Add `openclaw/openclaw` to the session.
   - Inspect language, folder structure, extension points, and configuration options.
   - Write `adr/ADR-0011-openclaw-upstream-binding.md` with concrete findings and binding strategy.
   - If repo is not accessible, escalate V1/V2 and pause.

2. **Materialize remaining docs** (deliverables 14–25):
   - Split deliverables 14–25 from this plan into:
     - `08-api-auth-tenancy.md` (deliverables 14–16)
     - `09-deployment-and-scaling.md` (deliverables 17–19)
     - `10-operations.md` (deliverables 20–23)
     - `11-milestone-roadmap.md` (deliverable 25)
   - Create all ADR files listed in deliverable 24.

3. **Record the stack decision**:
   - Update `docs/CODING_RULES.md` or `DECISIONS.md` to reflect:
     - Backend = Python/FastAPI (ADR-0002).
     - TypeScript = web-admin only.
     - iOS = Swift (separate repo).

4. **Commit for review**:
   - All changes additive (no code deleted, no forked repos).
   - Commit message: `docs(architecture): add 25-deliverable blueprint + ADRs`
   - Do **not** open a PR unless requested.
   - **STOP** for next review.

---

## Key Constraints (Verified & Assumed)

- **No business logic in this milestone** — Platform skeleton + interfaces only.
- **Multi-tenancy mandatory** — Every entity must have `tenant_id`, `user_id`, or `device_id` isolation keys `[VERIFIED principle]`.
- **One ChannelAdapter interface** for all platforms (Telegram, WhatsApp, WeChat, WeCom) `[VERIFIED principle]`.
- **All external services behind Provider interfaces** (AI, TTS, Search, Embedding, Storage, Messaging, Notifications) `[VERIFIED principle]`.
- **12-stage pipeline with no stage skipped** — Collect→Normalize→Deduplicate→Document→Extract→Resolve→Cross-Validate→Detect Conflicts→Score→Summarize→Interest Match→Broadcast `[VERIFIED principle]`.
- **No OpenClaw fork** — Upstream binding via the plugin SDK only `[ASSUMED — V1]`.
- **Secrets never in git** — `.env` git-ignored; `.env.example` documents shape only `[VERIFIED]`.

---

## Next Steps for Review

1. Approve or request changes to this blueprint.
2. On approval, run the Execution Plan above.
3. Post-commit: open PR for final sign-off or proceed to v0.1 implementation phase.

---

**Questions?** Refer to the open verification items (V1–V8) and ADRs for context; escalate unknowns before proceeding.
