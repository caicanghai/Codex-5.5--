# Migrations

Database migration folders. **No production tables are defined in Milestone 0.**
This directory establishes the structure and conventions only.

## Layout

- `postgres/` — PostgreSQL migrations, applied in lexical order.

## Conventions

- One migration per change; name `NNNN_<verb>_<subject>.sql`
  (e.g. `0001_create_tenants.sql`) — **added in later milestones**.
- Migrations are forward-only in production; each has a reviewed rollback plan.
- Every domain table is tenant-scoped (`tenant_id`).
- No migration is added until Milestone 1 authorizes the platform skeleton.
