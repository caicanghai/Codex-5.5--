> **⚠️ 已弃用 / DEPRECATED (Milestone 0 planning).** 权威参考见 [`PROJECT_MASTER_AUDIT.md`](./PROJECT_MASTER_AUDIT.md)。本文件仅作历史记录，不再指导开发。

# EIOS Project Charter

**Project:** EIOS — Evidence Intelligence & Omnichannel System
**Status:** Milestone 0 (Repository Foundation)
**Document owner:** Lead Software Architect
**Last updated:** 2026-07-11

---

## 1. Purpose

EIOS is a modular platform for ingesting, organizing, and acting on evidence
and interest signals, then coordinating outbound communication across many
channels. The system is built as a set of independent engines connected by a
unified gateway rather than a monolith, so that channels, storage, and
intelligence can evolve independently.

This charter defines _why_ the project exists and the boundaries within which
it is built. Concrete design lives in [`ARCHITECTURE.md`](./ARCHITECTURE.md);
sequencing lives in [`ROADMAP.md`](./ROADMAP.md).

## 2. Vision

A single, auditable backbone that can:

- Receive inbound signals from any channel through one gateway.
- Resolve and unify identities across channels and tenants.
- Turn raw material into structured, queryable evidence.
- Maintain a catalog of interests derived from that evidence.
- Drive workflows and broadcasts safely, with full audit trails.

## 3. Scope

### In scope (long term)

- Unified Channel Gateway and a stable internal message contract.
- Identity Layer with multi-tenant isolation.
- Evidence Intelligence Engine and Interest Catalog Engine.
- Workflow Engine and Broadcast Engine.
- TTS Gateway and channel adapters (as thin transport layers only).
- Operational concerns: observability, security, audit, and deployment.

### Explicitly out of scope for Milestone 0

Milestone 0 delivers **only the repository foundation**. No business logic,
no channel integrations, no engines, and no production tables are implemented.
See [`ROADMAP.md`](./ROADMAP.md) for what each milestone unlocks.

## 4. Principles

1. **Additive over destructive.** Existing upstream functionality is preserved;
   new capability is added alongside it.
2. **Modularity.** Each engine is independently buildable, testable, and
   replaceable. No business logic lives inside channel adapters.
3. **Contracts first.** Interfaces (schemas, OpenAPI, message envelopes) are
   defined before implementations.
4. **Everything through review.** Changes reach protected branches only via
   Pull Requests.
5. **Secure by construction.** Multi-tenancy, RBAC, and audit are designed into
   the structure from day one, even before they are implemented.
6. **Reproducible.** Local development mirrors production topology through
   containerized services.

## 5. Stakeholders

| Role                    | Responsibility                                  |
| ----------------------- | ----------------------------------------------- |
| Lead Software Architect | System design, architectural decision records   |
| Principal Engineer      | Implementation standards, code quality          |
| Repository Maintainer   | Branch policy, releases, CI/CD health           |
| Security Owner          | Threat model, secrets, audit, access boundaries |

## 6. Success criteria for Milestone 0

- A documented, navigable repository structure exists.
- Baseline documentation (charter, architecture, roadmap, contributing,
  coding rules, security, decisions) is in place.
- Code quality tooling (TypeScript strict, ESLint, Prettier, EditorConfig) is
  configured.
- CI validates install, lint, type-check, test, build, and Docker config.
- Docker Compose describes the local development topology as placeholders.
- Migration folders, domain schemas, and an OpenAPI skeleton exist without any
  production tables or endpoints.

## 7. Relationship to upstream

EIOS is derived from an upstream base and tracks it through a dedicated mirror
branch. Upstream is never modified in place; all EIOS work is layered on top.
See the branching model in [`CONTRIBUTING.md`](./CONTRIBUTING.md).
