# Domain Schemas

Conceptual domain models for EIOS. **Milestone 0 defines intent only** — these
describe the shapes each engine will own, not database tables or runtime types.
Concrete schemas (e.g. JSON Schema, Zod, SQL) are added in later milestones.

Each domain is tenant-scoped: every entity carries a `tenant_id`.

## Domains

### Identity (`identity.md`)
Subjects, external identities, and their resolution to internal subjects.

### Evidence (`evidence.md`)
Structured evidence derived from raw inbound material.

### Interest (`interest.md`)
Interests/subscriptions derived from evidence.

### Channel (`channel.md`)
Channel registrations and adapter transport metadata (no business logic).

### Workflow (`workflow.md`)
Workflow definitions and runs.

### Broadcast (`broadcast.md`)
Broadcast campaigns and delivery records.

### Audit (`audit.md`)
Append-only, tamper-evident audit events.
