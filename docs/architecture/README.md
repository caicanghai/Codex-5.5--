# EIOS Production Architecture Blueprint

**Author role:** Chief System Architect
**Status:** DRAFT — awaiting Architecture Review. **Nothing here is committed or
implemented.**
**Scope:** Documentation only. No production code. No feature work.

---

## How to read this blueprint

The blueprint is split into focused documents. The 25 required deliverables map
to them as follows:

| # | Deliverable | Document |
|---|-------------|----------|
| 1 | System Context Diagram | [00-context-and-containers.md](./00-context-and-containers.md) |
| 2 | Container Diagram | [00-context-and-containers.md](./00-context-and-containers.md) |
| 3 | Repository Architecture | [01-repository-architecture.md](./01-repository-architecture.md) |
| 4 | Domain-Driven Design boundaries | [02-domain-model.md](./02-domain-model.md) |
| 5 | Domain Model | [02-domain-model.md](./02-domain-model.md) |
| 6 | Database Entity Relationship | [03-data-model-erd.md](./03-data-model-erd.md) |
| 7 | Evidence Pipeline | [04-evidence-pipeline.md](./04-evidence-pipeline.md) |
| 8 | Queue Architecture | [05-queues-and-workers.md](./05-queues-and-workers.md) |
| 9 | Worker Architecture | [05-queues-and-workers.md](./05-queues-and-workers.md) |
| 10 | Gateway Architecture | [06-gateway-and-channels.md](./06-gateway-and-channels.md) |
| 11 | Provider Architecture | [07-providers-and-plugins.md](./07-providers-and-plugins.md) |
| 12 | Plugin Architecture | [07-providers-and-plugins.md](./07-providers-and-plugins.md) |
| 13 | Channel Adapter Architecture | [06-gateway-and-channels.md](./06-gateway-and-channels.md) |
| 14 | REST API boundaries | [08-api-auth-tenancy.md](./08-api-auth-tenancy.md) |
| 15 | Authentication & RBAC | [08-api-auth-tenancy.md](./08-api-auth-tenancy.md) |
| 16 | Multi-tenant strategy | [08-api-auth-tenancy.md](./08-api-auth-tenancy.md) |
| 17 | Deployment topology | [09-deployment-and-scaling.md](./09-deployment-and-scaling.md) |
| 18 | Docker Compose topology | [09-deployment-and-scaling.md](./09-deployment-and-scaling.md) |
| 19 | Scaling roadmap | [09-deployment-and-scaling.md](./09-deployment-and-scaling.md) |
| 20 | Monitoring & Logging | [10-operations.md](./10-operations.md) |
| 21 | Backup strategy | [10-operations.md](./10-operations.md) |
| 22 | Disaster Recovery strategy | [10-operations.md](./10-operations.md) |
| 23 | Secrets management | [10-operations.md](./10-operations.md) |
| 24 | Architecture Decision Records | [adr/](./adr/) |
| 25 | Milestone roadmap v0.1 → v1.0 | [11-milestone-roadmap.md](./11-milestone-roadmap.md) |

---

## Verification legend (required by the task)

Every material statement in this blueprint is tagged:

- **[VERIFIED]** — I can confirm this from the repository contents, from the
  Milestone 0 foundation already merged, or from stable, well-established facts
  about the named technology (e.g. "PostgreSQL supports row-level security").
- **[ASSUMED]** — a design decision, projection, or external fact I have **not**
  confirmed against ground truth. Anything tagged ASSUMED that touches an
  external system is also called out under "Open verification items" below.

When a statement would require checking something I cannot currently see, it is
tagged **[ASSUMED — requires verification]** and listed in
[§ Open verification items](#open-verification-items).

---

## Critical provenance caveat: "OpenClaw"

**[VERIFIED]** The repository this blueprint lives in (`caicanghai/Codex-5.5--`)
is **not** an OpenClaw codebase. Its tracked contents are a Python CLI tool plus
the EIOS Milestone 0 foundation added in the previous milestone. There is no
OpenClaw source, gateway, or business logic present here.

**[ASSUMED — requires verification]** The mission statement treats
`openclaw/openclaw` as the upstream base ("OpenClaw Gateway", "extend OpenClaw",
"reuse existing OpenClaw structure"). I have **not** inspected that repository. I
do not know its language, module layout, extension points, license, or whether
the "OpenClaw Gateway" in the target diagram refers to a messaging gateway, an
agent runtime, or something else.

Consequences for this blueprint:

1. Wherever the design says "extends OpenClaw" or "reuses OpenClaw structure,"
   that is a **placeholder contract**, not a verified integration. It is modeled
   as an upstream dependency behind an adapter (`packages/openclaw-bridge`) so
   that EIOS never forks OpenClaw and can bind to whatever OpenClaw actually
   exposes once verified.
2. The repository layout in
   [01-repository-architecture.md](./01-repository-architecture.md) is designed
   to be **additive** and to accommodate OpenClaw either as a git submodule, a
   vendored dependency, or a separately deployed service — the decision is
   deferred to [ADR-0011](./adr/ADR-0011-openclaw-upstream-binding.md) pending
   verification.

**To resolve this, I need one of:** access to `openclaw/openclaw` (I can request
it be added to this session), or a pointer to its real location and a short
description of what "OpenClaw Gateway" is in your architecture.

---

## Open verification items

These must be confirmed before implementation planning (Milestone 1) begins:

| ID | Item | Why it matters |
|----|------|----------------|
| V1 | Real identity, language, and structure of `openclaw/openclaw` | Determines the upstream binding strategy and whether "extend, never fork" is even mechanically possible. |
| V2 | Meaning of "OpenClaw Gateway" as a box in the target diagram | Changes whether the Unified Channel Gateway wraps OpenClaw or sits beside it. |
| V3 | WhatsApp Cloud API account tier & messaging limits | Affects rate-limit and template-message design in the Broadcast Engine. |
| V4 | WeChat Official Account vs. Service Account type | Determines which WeChat APIs (and which message capabilities) are available. |
| V5 | Enterprise WeChat (WeCom) app provisioning model | Affects the callback/verification design in the channel adapter. |
| V6 | APNs delivery model (token-based vs. certificate) & team identifiers | Required for the iOS push adapter. |
| V7 | Target VPS sizing and expected tenant/user volume at launch | Calibrates the scaling roadmap and Compose resource limits. |
| V8 | Data residency / compliance obligations (esp. for WeChat/China) | May force region-split deployment and change the DR design. |

> None of the above is guessed as fact anywhere in this blueprint. Where a value
> is needed to proceed, a **conservative ASSUMED default** is stated and flagged.

---

## Global architecture principles (restated, [VERIFIED] as project intent)

1. **OpenClaw stays upstream; extend, never fork.** All EIOS capability is
   additive and lives outside OpenClaw's tree, behind a bridge package.
2. **Everything modular and replaceable.** Subsystems communicate through
   explicit contracts (schemas, queues, provider interfaces).
3. **Multi-tenant by construction.** Every entity carries `tenant_id`,
   `user_id`, and (where relevant) `device_id`. No global session, no shared
   memory, no shared API keys.
4. **Every external service is abstracted** behind a provider interface
   (Model, TTS, Storage, Search, Embedding, Notification, Authentication).
5. **Every channel implements one identical `ChannelAdapter` interface**
   (Telegram, WhatsApp, WeChat, Enterprise WeChat, APNs, future Android).
6. **The Evidence Intelligence pipeline is canonical** and no stage is skipped:
   Collect → Normalize → Deduplicate → Extract Claims → Resolve Sources →
   Cross-Validate → Detect Conflicts → Score Confidence → Summarize →
   Interest Matching → Broadcast → Feedback.
