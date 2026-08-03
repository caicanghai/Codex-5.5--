> **⚠️ 已弃用 / DEPRECATED (Milestone 0 planning).** 权威参考见 [`PROJECT_MASTER_AUDIT.md`](./PROJECT_MASTER_AUDIT.md)。本文件仅作历史记录，不再指导开发。

# Architecture Decision Records (ADRs)

This log records significant, hard-to-reverse decisions. Each entry is
immutable once accepted; supersede rather than edit. New records append to the
bottom.

Format: **ID · Title · Status · Context · Decision · Consequences.**

Status values: `Proposed`, `Accepted`, `Superseded by ADR-XXX`, `Deprecated`.

---

## ADR-0001 · Adopt a layered, engine-based architecture

- **Status:** Accepted
- **Context:** EIOS must integrate many channels and evolve them independently
  without a monolith becoming a bottleneck.
- **Decision:** Structure the system as directional layers/engines connected by
  a unified gateway (see [`ARCHITECTURE.md`](./ARCHITECTURE.md)). Channel
  adapters are transport-only.
- **Consequences:** Clear seams and independent evolution, at the cost of more
  explicit contracts between layers.

## ADR-0002 · Preserve upstream via a mirror branch

- **Status:** Accepted
- **Context:** EIOS is derived from an upstream base that must keep receiving
  updates without being hand-edited.
- **Decision:** Track upstream verbatim on `mirror/openclaw` and merge forward
  through sync PRs. Never modify upstream in place. All new capability is
  additive.
- **Consequences:** Clean upstream sync path; requires discipline to keep EIOS
  changes layered rather than intermixed.

## ADR-0003 · PR-only flow with protected mainlines

- **Status:** Accepted
- **Context:** The product mainline must stay releasable and auditable.
- **Decision:** `eios/main` and `develop` are protected; all changes arrive via
  PR with CI green and CODEOWNER approval. `feature/*` → `develop` → `eios/main`.
- **Consequences:** Slower direct changes, higher safety and traceability.

## ADR-0004 · TypeScript strict as the code baseline

- **Status:** Accepted
- **Context:** The system is large, multi-tenant, and long-lived; type safety
  reduces whole classes of defects.
- **Decision:** All EIOS code is TypeScript with `strict: true`, enforced by
  ESLint and CI type-checking. No `any` in shipped code.
- **Consequences:** Higher upfront rigor; fewer runtime surprises.

## ADR-0005 · Contracts before implementations

- **Status:** Accepted
- **Context:** Layers must integrate reliably as teams work in parallel.
- **Decision:** Define schemas ([`/schemas`](../schemas)) and the OpenAPI
  surface ([`/services/api`](../services/api)) before building behavior;
  version public contracts.
- **Consequences:** Predictable integration; requires contract review discipline.

## ADR-0006 · Containerized local topology mirrors production

- **Status:** Accepted
- **Context:** Environment drift causes "works on my machine" failures.
- **Decision:** Provide a Docker Compose development topology
  ([`/deployments`](../deployments)) with the same backing services as
  production (PostgreSQL, Redis, MinIO, and integration placeholders).
- **Consequences:** Reproducible local dev; Compose must be kept in sync with
  real deployment manifests.

## ADR-0007 · Milestone 0 delivers foundation only

- **Status:** Accepted
- **Context:** Building everything at once risks an unmaintainable base.
- **Decision:** Milestone 0 delivers structure, docs, tooling, CI, and
  placeholders only — no business logic, engines, endpoints, or production
  tables. Work stops until Milestone 1 is authorized.
- **Consequences:** A clean, reviewable starting point; feature work is
  deliberately deferred.
