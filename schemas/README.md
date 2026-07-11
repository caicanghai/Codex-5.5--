# Schemas

Contract definitions for EIOS: the internal message envelope, domain models,
and database migrations. **Contracts are defined here before implementations
exist** (see [Coding Rules §3](../docs/CODING_RULES.md)).

## Layout

- `domain/` — domain schemas (conceptual models only in Milestone 0).
- `envelope/` — the internal message envelope contract shared by all channels.
- `migrations/` — database migration folders (no production tables yet).

## Rules

- Domain schemas are the source of truth for shapes crossing layer boundaries.
- Public contracts are versioned; breaking changes require an ADR.
- No production tables are defined in Milestone 0 — only structure and intent.
