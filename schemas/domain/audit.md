# Audit Domain (conceptual)

> Milestone 0: conceptual model only.

## AuditEvent

Append-only, tamper-evident record of a security-relevant action.

| Field         | Type      | Notes                                     |
| ------------- | --------- | ----------------------------------------- |
| `id`          | uuid      |                                           |
| `tenant_id`   | uuid      | tenant scope                              |
| `actor`       | string    | subject/key that acted                    |
| `action`      | string    | verb (e.g. `campaign.send`, `key.rotate`) |
| `target`      | string    | affected resource reference               |
| `metadata`    | json      | non-sensitive context                     |
| `occurred_at` | timestamp |                                           |
| `prev_hash`   | string    | chain link for tamper evidence            |

**Invariants:** immutable once written; never contains secrets or raw PII;
chained via `prev_hash` per tenant.
