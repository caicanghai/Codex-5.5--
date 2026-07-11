# Channel Domain (conceptual)

> Milestone 0: conceptual model only. Adapters are transport-only.

## ChannelRegistration

Registration/config for a channel adapter within a tenant.

| Field             | Type      | Notes                                            |
| ----------------- | --------- | ------------------------------------------------ |
| `id`              | uuid      |                                                  |
| `tenant_id`       | uuid      | tenant scope                                     |
| `channel`         | enum      | telegram / whatsapp / wechat / work_wechat / ios |
| `enabled`         | boolean   |                                                  |
| `credentials_ref` | string    | secrets-manager reference (never inline)         |
| `created_at`      | timestamp |                                                  |

**Invariants:** credentials are never stored in this record — only a reference.
Adapters hold **no business logic**.
