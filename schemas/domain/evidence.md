# Evidence Domain (conceptual)

> Milestone 0: conceptual model only.

## Evidence

Structured record derived from raw inbound material by the Evidence
Intelligence Engine.

| Field            | Type           | Notes                                          |
| ---------------- | -------------- | ---------------------------------------------- |
| `id`             | uuid           |                                                |
| `tenant_id`      | uuid           | tenant scope                                   |
| `subject_id`     | uuid → Subject | optional source subject                        |
| `source_channel` | enum           | where the raw material arrived                 |
| `kind`           | string         | classification of the evidence                 |
| `payload_ref`    | string         | object-storage reference (MinIO) for artifacts |
| `structured`     | json           | extracted structured fields                    |
| `confidence`     | number         | 0..1                                           |
| `created_at`     | timestamp      |                                                |

**Invariants:** artifacts live in tenant-scoped object storage prefixes;
`structured` never contains secrets.
