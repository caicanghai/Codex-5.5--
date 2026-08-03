# ADR-0005: Multi-Tenancy Strategy (Shared Schema + RLS)

**Status**: ADOPTED  
**Date**: 2026-08-03  
**Context**: EIOS targets thousands of small tenants on a single VPS.

## Decision

**Use shared-schema multi-tenancy with PostgreSQL Row-Level Security (RLS)** instead of schema-per-tenant or database-per-tenant.

## Rationale

- **Cost-effective** — Thousands of small tenants on one VPS; no per-tenant database overhead.
- **Tenant provisioning** — Instant; just insert a row into `tenants` table.
- **Isolation at DB layer** — RLS enforces tenant boundaries at the database level (defense in depth).
- **Data queries** — All queries automatically filtered by `tenant_id`; no SQL injection risk.

## Escalation Path

For regulated tenants (China, GDPR, data residency), escalate to schema-per-tenant or database-per-tenant (v0.5+). RLS design does not block this; it's an operational change.

## Implementation

- Every table has `tenant_id` (or inherits via FK).
- RLS policies on all tables; keyed on `current_setting('app.tenant_id')`.
- API sets session context: `SET app.tenant_id = '<tenant_id>'` before queries.
- Queue messages carry `tenant_id`; workers set context before executing.

## Tradeoff

- **Performance** — RLS adds minimal overhead (one extra WHERE clause).
- **Complexity** — Requires careful isolation key management; mistakes leak data.

## Alternatives Considered

- **Schema-per-tenant** — Better isolation; higher operational cost.
- **Database-per-tenant** — Complete isolation; very high cost.

## References

- `docs/architecture/03-data-model-erd.md` — RLS policies and isolation keys.
- `docs/architecture/08-api-auth-tenancy.md` — Tenant context setup.
