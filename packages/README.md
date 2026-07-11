# Packages

Shared libraries consumed by services and apps. **Milestone 0: structure only.**

Shared logic (types, the envelope contract, authz helpers, validation, logging)
lives here instead of being duplicated across services (see
[CODING_RULES §2](../docs/CODING_RULES.md)).

Anticipated packages (added in later milestones):

- `contracts` — internal message envelope + domain types.
- `authz` — RBAC and tenant-scoping helpers.
- `observability` — structured logging, metrics, tracing helpers.

No packages are implemented yet.
