# 08 — REST API Boundaries, Authentication & RBAC, Multi-Tenancy

Deliverables **14 (REST API boundaries)**, **15 (Auth & RBAC)**, and
**16 (Multi-tenant strategy)**.

---

## 14. REST API boundaries

**[VERIFIED target]** FastAPI. Resource-oriented, versioned under `/api/v1`.
Every authenticated route is tenant-scoped from the auth context; **no route can
read across tenants** without an explicit, audited elevation.

> The channel **webhooks are a separate ingress** (the Gateway, deliverable 10),
> NOT part of this authenticated API. Keep the two surfaces distinct so channel
> traffic cannot exhaust the user-facing API.

### Resource groups (boundaries, not an exhaustive endpoint list)

| Group | Purpose | Notes |
|-------|---------|-------|
| `auth` | login, token refresh, logout | delegates to `AuthenticationProvider` |
| `tenants` | tenant profile/plan | admin-scoped |
| `users` | user CRUD, status, self-profile | unique `(tenant_id, email)` |
| `devices` | register/list/revoke devices + APNs tokens | push targets |
| `api-keys` | issue/list/revoke | key returned **once**; only hash stored |
| `channel-bindings` | start/verify/list/unbind Telegram/WhatsApp/WeChat/WeCom | verification flow per channel |
| `interests` | CRUD interests + topics | tenant + user scoped |
| `providers` | choose Model/TTS/Search/Embedding provider, submit key ref | stores `credentials_ref` only |
| `broadcasts` / `history` | read delivery history + message detail + feedback | read-mostly |
| `admin` | RBAC, audit read, rate-limit views | permission-gated |

### Boundary rules `[VERIFIED principle]`

- The API owns validation + authorization, then **enqueues commands** to
  workers; it does not run pipeline work inline.
- No provider SDK or channel SDK is imported in the API layer — interfaces only.
- **OpenAPI is the contract**, authored in `schemas/openapi/` and served by the
  API (skeleton already exists from Milestone 0).
- Idempotency keys on all side-effecting POST/PUT.
- Consistent error envelope; never leak internal detail or secrets.

---

## 15. Authentication & RBAC

### Authentication
- Via `AuthenticationProvider` (OIDC / email+passkey — vendor-abstracted).
- Clients present short-lived access tokens (**JWT [ASSUMED]**) + refresh tokens.
- iOS and channel users resolve to an internal `user_id` through a verified
  `ChannelBinding`.

### API keys
- Per-user, per-tenant, **scoped**, **hashed at rest**, **never global**,
  **never shared** across tenants. `[VERIFIED principle]`
- Shown once at creation; revocable; `last_used_at` tracked.

### RBAC
- Roles → permissions, tenant-scoped. Baseline roles `[ASSUMED]`: `owner`,
  `admin`, `member`, `service`.
- Enforcement lives in `packages/security`, applied at the API boundary and on
  sensitive worker actions (e.g. broadcast send).

### Tenant context propagation
- The authenticated principal yields `tenant_id` (+ `user_id`, `device_id`).
- The DB session sets `app.tenant_id` so **RLS applies to every query**.
- Queue messages carry the same keys; workers set context before any DB access.
- All auth-relevant actions emit append-only audit events.

```mermaid
sequenceDiagram
    participant C as Client
    participant API as API (FastAPI)
    participant SEC as security (RBAC)
    participant DB as Postgres (RLS)
    C->>API: request + access token
    API->>SEC: authenticate + authorize(permission)
    SEC-->>API: principal{tenant_id,user_id,roles}
    API->>DB: SET app.tenant_id; query
    DB-->>API: tenant-scoped rows only
    API-->>C: response (+ audit event emitted)
```

---

## 16. Multi-tenant strategy

**[ASSUMED — ADR-0005]** Shared-schema + **Row-Level Security** in PostgreSQL.
One set of tables; every row has `tenant_id`; RLS policies key on the session
`app.tenant_id`. Chosen for thousands of small tenants on one VPS.

### Isolation keys everywhere `[VERIFIED principle]`
- `tenant_id` on **every** entity (always).
- `user_id` and `device_id` where relevant.
- **No global session. No shared memory. No shared API keys.**

### Isolation across the stack

| Layer | Mechanism |
|-------|-----------|
| Database | RLS on `app.tenant_id`; composite indexes lead with `tenant_id`. |
| Queues | `tenant_id` on every message; worker sets context first. |
| Object storage | keys prefixed by `tenant_id`. |
| Cache / rate-limit (Redis) | keys namespaced by `tenant_id`. |
| Providers | credentials resolved per tenant/user; never shared. |

### Fairness & noisy-neighbor
- Per-tenant rate limits and fair-share worker scheduling.
- Low-priority tenants shed first under sustained overload.

### Escalation path
- Schema-per-tenant or DB-per-tenant reserved for large/regulated tenants and
  data-residency needs (open item **V8**, especially WeChat/China).
