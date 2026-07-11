# ADR-0005 · Multi-tenancy via shared-schema + Row-Level Security

- **Status:** Accepted (revisit for regulated/large tenants)
- **Context:** Thousands of small tenants on a single VPS at launch, with strict
  isolation (`tenant_id`/`user_id`/`device_id`, no shared session/memory/keys).
- **Decision:** **Shared-schema** multi-tenancy in PostgreSQL with **Row-Level
  Security** keyed on a session variable `app.tenant_id`. Every table carries
  `tenant_id`; queues, object storage, and Redis keys are tenant-namespaced.
- **Consequences:** Operationally simple and scalable for many small tenants;
  correctness depends on always setting the tenant context (enforced in
  `packages/persistence`/`security`). Large or data-residency-bound tenants
  (open item V8) may later need schema- or DB-per-tenant — the design leaves that
  escalation path open.
