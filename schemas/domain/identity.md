# Identity Domain (conceptual)

> Milestone 0: conceptual model only. No tables, no runtime types.

## Subject

The internal, channel-agnostic actor.

| Field          | Type      | Notes                   |
| -------------- | --------- | ----------------------- |
| `id`           | uuid      | internal subject id     |
| `tenant_id`    | uuid      | tenant scope (required) |
| `display_name` | string    | optional                |
| `created_at`   | timestamp |                         |

## ExternalIdentity

A channel-specific identity mapped to a Subject.

| Field          | Type           | Notes                                            |
| -------------- | -------------- | ------------------------------------------------ |
| `id`           | uuid           |                                                  |
| `tenant_id`    | uuid           | tenant scope                                     |
| `subject_id`   | uuid → Subject |                                                  |
| `channel`      | enum           | telegram / whatsapp / wechat / work_wechat / ios |
| `external_ref` | string         | channel-native id (hashed where sensitive)       |
| `verified`     | boolean        |                                                  |

**Invariants:** `(tenant_id, channel, external_ref)` is unique. Resolution never
crosses tenant boundaries.
