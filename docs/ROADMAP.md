# EIOS Roadmap

Milestones are additive. Each unlocks the next; nothing later is started until
its predecessor is accepted. **Only Milestone 0 is in progress.**

---

## Milestone 0 — Repository Foundation ← _current_

Goal: a production-grade, navigable foundation with no business logic.

- [x] Repository structure (`docs/`, `architecture/`, `schemas/`,
      `deployments/`, `workflows/`, `services/`, `tests/`, `packages/`,
      `apps/`, `scripts/`, `.github/`).
- [x] Baseline documentation (charter, architecture, roadmap, contributing,
      coding rules, security, decisions).
- [x] Code quality tooling: TypeScript strict, ESLint, Prettier, EditorConfig.
- [x] CI: install, lint, type-check, test, build, Docker validation.
- [x] Governance: issue/PR templates, CODEOWNERS, Conventional Commits,
      dependency & secret scanning config, branch-protection guidance.
- [x] Docker Compose development topology (placeholders only).
- [x] Migration folders and domain schemas (no production tables).
- [x] OpenAPI skeleton (no endpoints).
- [x] Security structure prepared (not implemented).
- [x] Test folders prepared (no required tests yet).

**Exit criteria:** CI is green, docs are complete, no business feature exists.
Work stops here until Milestone 1 is explicitly authorized.

## Milestone 1 — Platform Skeleton (not started)

- Runtime services (`gateway`, `api`, `worker`) bootable as empty shells.
- Internal message envelope contract defined and versioned.
- Configuration, logging, and health endpoints.
- First real (empty) database migration baseline.

## Milestone 2 — Identity & Tenancy (not started)

- Identity Layer, tenant model, RBAC enforcement.
- API key isolation and webhook verification.

## Milestone 3 — Evidence & Interests (not started)

- Evidence Intelligence Engine.
- Interest Catalog Engine.

## Milestone 4 — Orchestration & Outbound (not started)

- Workflow Engine.
- Broadcast Engine.

## Milestone 5 — Channels & Voice (not started)

- Channel adapters (Telegram, WhatsApp, WeChat, Enterprise WeChat, iOS).
- TTS Gateway.
- Directus / n8n integrations.

---

### Sequencing rules

1. A milestone begins only after the previous one is accepted.
2. Security and audit structure precede the features they protect.
3. Contracts (schemas, OpenAPI, envelopes) precede implementations.
4. No milestone removes upstream functionality.
