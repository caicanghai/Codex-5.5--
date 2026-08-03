# Broadcast Domain (conceptual)

> Milestone 0: conceptual model only.

## BroadcastCampaign

A fan-out of a message to an audience, owned by the Broadcast Engine.

| Field          | Type      | Notes                                       |
| -------------- | --------- | ------------------------------------------- |
| `id`           | uuid      |                                             |
| `tenant_id`    | uuid      | tenant scope                                |
| `audience_ref` | string    | selection derived from the Interest Catalog |
| `channels`     | enum[]    | target channels                             |
| `status`       | enum      | draft / scheduled / sending / sent / failed |
| `created_at`   | timestamp |                                             |

## DeliveryRecord

Per-recipient delivery outcome.

| Field         | Type                     | Notes                       |
| ------------- | ------------------------ | --------------------------- |
| `id`          | uuid                     |                             |
| `tenant_id`   | uuid                     | tenant scope                |
| `campaign_id` | uuid → BroadcastCampaign |                             |
| `subject_id`  | uuid → Subject           |                             |
| `channel`     | enum                     |                             |
| `status`      | enum                     | queued / delivered / failed |
| `attempts`    | int                      |                             |

**Invariants:** delivery respects per-tenant rate limits; the engine decides
_where/whom_, not _what to say_.
