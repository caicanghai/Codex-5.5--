# Internal Message Envelope (conceptual)

> Milestone 0: contract intent only. No implementation.

Every message crossing the Unified Channel Gateway — inbound or outbound — is
normalized to a single versioned envelope. Channel adapters translate between
their native format and this envelope and contain **no business logic**.

## Envelope (v0, draft shape)

| Field | Type | Notes |
| ----- | ---- | ----- |
| `envelope_version` | string | semver of the contract, e.g. `0.1.0` |
| `id` | uuid | message id |
| `tenant_id` | uuid | tenant scope (required) |
| `direction` | enum | `inbound` / `outbound` |
| `channel` | enum | telegram / whatsapp / wechat / work_wechat / ios |
| `subject_ref` | string | resolved by the Identity Layer |
| `content` | json | normalized content parts |
| `metadata` | json | non-sensitive transport metadata |
| `received_at` | timestamp | |

## Rules

- The envelope is the **only** contract engines depend on for messaging.
- Breaking changes bump `envelope_version` major and require an ADR.
- Raw channel payloads are untrusted; validate before mapping into the envelope.
