# Deliverables 14–16: REST API, Authentication & Multi-Tenancy

## Deliverable 14: REST API Boundaries

### API Structure (FastAPI)

**Base**: `/api/v1`  
**Auth**: Bearer token (JWT) or API key (scoped, hashed).  
**Tenant Scoping**: All routes enforce `tenant_id` from auth context.

```
/api/v1/
├── auth/
│   ├── POST /login                      # Email + passkey
│   ├── POST /refresh                    # Refresh token
│   ├── POST /logout                     # Revoke session
│   └── GET /me                          # Current user profile
├── tenants/
│   ├── GET /{tenant_id}                 # Admin only
│   ├── PUT /{tenant_id}                 # Admin only
│   └── GET /{tenant_id}/usage           # Billing metrics
├── users/
│   ├── GET /                            # List (tenant-scoped)
│   ├── POST /                           # Create (admin)
│   ├── GET /{user_id}                   # Read
│   ├── PUT /{user_id}                   # Update self
│   └── DELETE /{user_id}                # Soft delete (admin)
├── devices/
│   ├── GET /                            # My devices
│   ├── POST /register                   # New device + APNs token
│   ├── GET /{device_id}                 # Details
│   └── DELETE /{device_id}              # Revoke
├── api-keys/
│   ├── GET /                            # List my keys
│   ├── POST /                           # Issue new key (shown once)
│   └── DELETE /{key_id}                 # Revoke
├── channel-bindings/
│   ├── GET /                            # My bindings
│   ├── POST /{channel}/start            # Telegram /start flow
│   ├── POST /{channel}/verify/{code}    # Verify OTP
│   ├── GET /{channel}/status            # Binding status
│   └── DELETE /{channel}                # Unbind
├── interests/
│   ├── GET /                            # My topics
│   ├── POST /                           # Create topic
│   ├── PUT /{interest_id}               # Update
│   └── DELETE /{interest_id}            # Delete
├── providers/
│   ├── GET /                            # Available providers
│   ├── POST /ai/test                    # Test AI provider
│   ├── PUT /ai                          # Choose AI provider + key
│   └── PUT /tts                         # Choose TTS + key
├── broadcasts/
│   ├── GET /                            # Delivery history
│   ├── GET /{broadcast_id}              # Details + status
│   └── GET /{broadcast_id}/deliveries  # Per-channel status
├── history/
│   ├── GET /                            # Evidence I received
│   └── GET /{evidence_id}               # Full lineage
└── admin/
    ├── GET /audit                       # Append-only audit log
    ├── GET /rate-limits                 # Current limits
    ├── POST /rate-limits                # Update (tenant settings)
    └── GET /health                      # System health
```

### Key Principles

- **Resource-oriented** — RESTful resource naming, standard HTTP verbs.
- **Tenant-scoped** — Every GET/POST/PUT/DELETE is scoped to `current_user.tenant_id`.
- **Idempotency** — POST/PUT operations include `Idempotency-Key` header (UUID); server deduplicates.
- **OpenAPI schema** — Served at `/api/v1/openapi.json`; published in `docs/openapi/`.
- **No side effects in GET** — All state changes via POST/PUT/DELETE.

---

## Deliverable 15: Authentication & RBAC

### Authentication Flow

```
Client (mobile, web)
    ↓
POST /api/v1/auth/login
    { email, passkey }
    ↓
AuthenticationProvider (OIDC / email+passkey)
    ↓
    ✓ Verified
    ↓
Return JWT + Refresh Token
    ↓
Client stores JWT in secure storage
    ↓
Future requests:
    Authorization: Bearer <JWT>
    ↓
API validates JWT, extracts user_id + tenant_id
    ↓
Query allowed (scoped to tenant_id via RLS)
```

### JWT Token Structure `[ASSUMED]`

```json
{
  "sub": "user_id_uuid",
  "tenant_id": "tenant_id_uuid",
  "roles": ["owner", "member"],
  "iat": 1691000000,
  "exp": 1691003600,
  "iss": "eios-auth"
}
```

**Lifetime**: 1 hour (access token); 30 days (refresh token).

### RBAC Roles & Permissions

**Baseline Roles** `[ASSUMED]`:
- **Owner** — Full access; can manage users, roles, billing.
- **Admin** — Manage users, channels, providers; view audit.
- **Member** — Use channels, view own history, manage own profile.
- **Service** — Limited API access (key-based); used for integrations.

**Permission Matrix**:

| Action | Owner | Admin | Member | Service |
|--------|-------|-------|--------|---------|
| Create tenant | ✓ | ✗ | ✗ | ✗ |
| Manage users | ✓ | ✓ | ✗ | ✗ |
| Manage roles | ✓ | ✗ | ✗ | ✗ |
| Configure providers | ✓ | ✓ | ✗ | ✗ |
| Bind channels | ✓ | ✓ | ✓ | ✗ |
| Send broadcasts | ✓ | ✓ | ✓ | ✓ |
| View history | ✓ | ✓ | ✓ | ✓ (own) |
| View audit | ✓ | ✓ | ✗ | ✗ |

### API Key Management

**Issuance**:
1. User POST `/api/v1/api-keys` with scopes (e.g., `["read:history", "write:broadcasts"]`).
2. Server generates key (random 64-char string), hashes it (SHA256), stores hash.
3. Returns key **once** (client must save).
4. Future requests: `Authorization: Bearer <key>`; server looks up hash + validates scopes.

**Rotation**:
- Manual: User DELETE and re-POST to rotate.
- Automatic `[ASSUMED]`: Configurable expiry; alert before expiry.

---

## Deliverable 16: Multi-Tenant Strategy

### Shared Schema + Row-Level Security (RLS)

**Architecture**: One PostgreSQL database, one schema, one set of tables; every row tagged with `tenant_id`.

**Why RLS over separate schemas/DBs?**
- ✓ Thousands of small tenants on one VPS (lower cost).
- ✓ Tenant provisioning is instant (no new schema/DB to create).
- ✓ Data is isolated at the database layer (defense in depth).
- ✗ Not suitable for regulated/regional tenants (see V8, escalation path).

### RLS Enforcement

```sql
-- Example: RLS policy on "users" table

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY rls_users ON users
  USING (tenant_id = current_setting('app.tenant_id')::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
```

**Setup** (per request):
1. API receives JWT, extracts `tenant_id`.
2. Opens DB connection, sets session variable: `SET app.tenant_id = '<tenant_id>'`.
3. All queries automatically filter by RLS policy.
4. If query tries to access another tenant's row, RLS blocks it (database error).

### Isolation Keys Everywhere

- **Tables**: Every row has `tenant_id` (or inherits via FK).
- **Cache**: Redis keys prefixed by `tenant_id/` (e.g., `tenant_id/user_123/interests`).
- **Queues**: Every message includes `tenant_id`; workers set RLS context before query.
- **Logs**: Every log entry includes `tenant_id` (structured JSON).
- **Object storage**: Keys prefixed by `tenant_id/` (e.g., `tenant_id/documents/doc_123`).
- **Metrics**: Labels per tenant (no cross-tenant aggregates by default).

### Per-Tenant Limits & Fair Sharing

- **Rate limits** — Max requests/second per tenant (configurable per plan).
- **Queue priority** — Tenants share queues; no one tenant starves others (fair-share scheduler).
- **Storage quota** — Max GB stored per tenant (per plan).
- **Concurrency** — Max concurrent workers per tenant (avoid noisy-neighbor).

### Escalation Path (V8, Regulated Tenants)

If a tenant requires:
- China data residency (WeChat/WeCom compliance).
- GDPR/regulatory isolation.
- Physical separation of data.

**Path**: Migrate to schema-per-tenant or DB-per-tenant (v0.5+). RLS design doesn't block this transition; it's an operation change, not a schema change.

---

## Key Security Properties (Verified Principle)

✅ **No cross-tenant data leakage** — RLS enforced at DB layer; API enforces scoping.  
✅ **API keys scoped & hashed** — Keys never shared; hashed at rest; scopes limit what each key can do.  
✅ **JWT short-lived** — Access tokens expire in 1 hour; refresh tokens rotate.  
✅ **Audit trail** — Every sensitive action logged append-only.  
✅ **No secrets in logs** — Structured logging excludes tokens, keys, PII.
