# Workflow Domain (conceptual)

> Milestone 0: conceptual model only.

## WorkflowDefinition

A declarative automation owned by the Workflow Engine.

| Field       | Type   | Notes                 |
| ----------- | ------ | --------------------- |
| `id`        | uuid   |                       |
| `tenant_id` | uuid   | tenant scope          |
| `name`      | string |                       |
| `version`   | int    | versioned definition  |
| `spec`      | json   | steps and transitions |

## WorkflowRun

One execution of a definition.

| Field           | Type                      | Notes                                  |
| --------------- | ------------------------- | -------------------------------------- |
| `id`            | uuid                      |                                        |
| `tenant_id`     | uuid                      | tenant scope                           |
| `definition_id` | uuid → WorkflowDefinition |                                        |
| `status`        | enum                      | pending / running / succeeded / failed |
| `started_at`    | timestamp                 |                                        |
| `finished_at`   | timestamp                 | nullable                               |

**Invariants:** automated steps run within explicit tool permission boundaries
(see [SECURITY.md](../../docs/SECURITY.md)).
