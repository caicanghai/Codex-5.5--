# Interest Domain (conceptual)

> Milestone 0: conceptual model only.

## Interest

An interest/subscription derived from evidence by the Interest Catalog Engine.

| Field             | Type              | Notes                  |
| ----------------- | ----------------- | ---------------------- |
| `id`              | uuid              |                        |
| `tenant_id`       | uuid              | tenant scope           |
| `subject_id`      | uuid → Subject    | who holds the interest |
| `topic`           | string            | catalog topic key      |
| `weight`          | number            | derived salience       |
| `source_evidence` | uuid[] → Evidence | provenance             |
| `active`          | boolean           |                        |
| `updated_at`      | timestamp         |                        |

**Invariants:** every interest is traceable to source evidence; catalog topics
are tenant-scoped.
