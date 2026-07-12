> **⚠️ 已弃用 / DEPRECATED (Milestone 0 planning).** 权威参考见 [`PROJECT_MASTER_AUDIT.md`](./PROJECT_MASTER_AUDIT.md)。本文件仅作历史记录，不再指导开发。

# EIOS Architecture

**Status:** Foundation (Milestone 0). This describes the _target_ architecture
the repository is being shaped toward. No engine is implemented yet.

---

## 1. High-level topology

Signals flow inbound through a single gateway, are normalized and enriched by a
chain of engines, and eventually drive outbound communication through channel
adapters. Adapters are transport-only.

```
                     ┌──────────────────────┐
   inbound channels  │  OpenClaw Gateway     │  (existing upstream base)
   ───────────────▶  └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │ Unified Channel       │  one internal message contract
                     │ Gateway               │  for every channel
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │ Identity Layer        │  resolve + unify identities,
                     │                       │  tenant isolation
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │ Evidence Intelligence │  raw material → structured
                     │ Engine                │  evidence
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │ Interest Catalog      │  derive + maintain interests
                     │ Engine                │
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │ Workflow Engine       │  orchestration + automation
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │ Broadcast Engine      │  fan-out to channels
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │ TTS Gateway           │  text → speech (optional path)
                     └──────────┬───────────┘
                                │
   ┌────────────┬───────────────┼───────────────┬─────────────┐
   ▼            ▼               ▼               ▼             ▼
Telegram    WhatsApp         WeChat      Enterprise WeChat    iOS
(adapter)   (adapter)        (adapter)   (adapter)            (adapter)
```

## 2. Layer responsibilities

| Layer                            | Responsibility                                                                       | Must NOT do                                    |
| -------------------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------- |
| **Unified Channel Gateway**      | Normalize every inbound/outbound message to one internal envelope; route to engines. | Contain business rules.                        |
| **Identity Layer**               | Resolve external identities to internal subjects; enforce tenant boundaries.         | Persist evidence.                              |
| **Evidence Intelligence Engine** | Convert raw input into structured, queryable evidence.                               | Talk to channels directly.                     |
| **Interest Catalog Engine**      | Derive and maintain interests/subscriptions from evidence.                           | Send messages.                                 |
| **Workflow Engine**              | Orchestrate multi-step automations and decisions.                                    | Own transport.                                 |
| **Broadcast Engine**             | Fan messages out to selected channels/audiences.                                     | Decide _what_ to say (that is upstream logic). |
| **TTS Gateway**                  | Turn text into speech for voice-capable channels.                                    | Store data.                                    |
| **Channel Adapters**             | Transport only: translate the internal envelope to/from a specific channel API.      | Contain any business logic.                    |

## 3. Runtime services

The deployable units (see [`/deployments`](../deployments)) map to these
long-term services:

- **gateway** — hosts the Unified Channel Gateway edge.
- **api** — HTTP/OpenAPI surface for management and integration.
- **worker** — asynchronous processing for engines and broadcasts.

Backing services (development topology):

- **PostgreSQL** — primary relational store (per-tenant schemas/rows).
- **Redis** — queues, caching, rate limiting, ephemeral state.
- **MinIO** — S3-compatible object storage for media/evidence artifacts.
- **Directus** — headless data/admin layer (placeholder in M0).
- **n8n** — external automation surface (placeholder in M0).

## 4. Cross-cutting concerns

- **Multi-tenancy** — every record and request is scoped to a tenant; isolation
  is enforced at the Identity Layer and persisted with tenant keys.
- **Security** — RBAC, API key isolation, webhook verification, audit logging,
  secrets management, rate limiting, prompt-injection isolation, and tool
  permission boundaries. See [`SECURITY.md`](./SECURITY.md).
- **Observability** — structured logging, metrics, and tracing are expected at
  every service boundary.
- **Contracts** — the internal message envelope, domain schemas
  ([`/schemas`](../schemas)), and the API surface
  ([`/services/api`](../services/api)) are the stable seams between layers.

## 5. Repository ↔ architecture mapping

| Concern                               | Location                           |
| ------------------------------------- | ---------------------------------- |
| Architecture notes & diagrams         | [`/architecture`](../architecture) |
| Domain & message schemas              | [`/schemas`](../schemas)           |
| Deployment topology                   | [`/deployments`](../deployments)   |
| Automation definitions                | [`/workflows`](../workflows)       |
| Runtime services                      | [`/services`](../services)         |
| Shared libraries                      | [`/packages`](../packages)         |
| Deployable applications               | [`/apps`](../apps)                 |
| Operational scripts                   | [`/scripts`](../scripts)           |
| Tests (unit/integration/e2e/security) | [`/tests`](../tests)               |

## 6. Constraints

- Adapters never embed business logic.
- Engines communicate through explicit contracts, not shared mutable state.
- No layer reaches "downstream" past its neighbor; flow is directional.
- The upstream gateway base is preserved and wrapped, not rewritten.
