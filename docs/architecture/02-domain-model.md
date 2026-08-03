# Deliverables 4–5: DDD Boundaries & Domain Model

## Deliverable 4: DDD Boundaries (Bounded Contexts)

### Bounded Contexts Map

```
┌────────────────────────────────────────────────────────────────┐
│                       EIOS Multi-Tenant Platform               │
│                                                                 │
│  ┌───────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐   │
│  │ Identity  │  │ Evidence │  │ Interest │  │ Broadcast  │   │
│  │ Context   │  │ Context  │  │ Context  │  │ Context    │   │
│  │           │  │          │  │          │  │            │   │
│  │ • Tenant  │  │ • Collect│  │• Interest│  │• Broadcast │   │
│  │ • User    │  │ • Extract│  │• Matching│  │• Delivery  │   │
│  │ • Device  │  │ • Resolve│  │• Feedback│  │• Channel   │   │
│  │ • AuthN   │  │ • Score  │  │          │  │  Adapter   │   │
│  │ • RBAC    │  │ • Summary│  │          │  │            │   │
│  └─────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘   │
│        │              │             │              │           │
│        │ tenant_id    │tenant_id    │tenant_id    │tenant_id  │
│        └──────────────┴─────────────┴──────────────┘           │
│                       │                                        │
│          ┌────────────▼────────────┐                          │
│          │  Infra & Shared Services │                         │
│          │                          │                         │
│          │ • PostgreSQL + RLS       │                         │
│          │ • Redis queues & cache   │                         │
│          │ • Object storage (MinIO) │                         │
│          │ • Providers (AI, TTS)    │                         │
│          │ • Logging, Tracing       │                         │
│          └──────────────────────────┘                         │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### Context 1: Identity Context
**Responsibility**: Manage tenants, users, devices, authentication, RBAC, and audit.

**Entities**:
- **Tenant** — Root aggregation; owns all other data. Has `plan`, `status`, `rate_limits`.
- **User** — Belongs to a tenant; has `email`, `roles`, `status`.
- **Device** — User's endpoint (iOS app); stores APNs token, last active, geolocation `[ASSUMED]`.
- **APIKey** — Per-user, per-tenant; scoped, hashed at rest, never returned after creation.
- **ChannelBinding** — User's binding to Telegram/WhatsApp/WeChat/WeCom (stores handle/ID, no credentials).
- **AuditEvent** — Append-only log of sensitive actions (login, role change, API key issue, channel bind).

**Key Invariants**:
- Every user belongs to exactly one tenant.
- Every device belongs to exactly one user.
- Tenant isolation is enforced via RLS; no query can cross tenants.
- API keys are hashed; the key is shown only once at creation.

**Interactions**:
- **→ Evidence Context**: User is the initiator; can view evidence associated with their interests.
- **→ Broadcast Context**: User receives broadcasts scoped to their interests and devices.
- **← Infra (Auth Provider)**: Delegates AuthN to OIDC / email+passkey provider.

---

### Context 2: Evidence Context
**Responsibility**: Ingest, process, and score information (claims, sources, conflicts, confidence).

**Entities**:
- **RawItem** — Unprocessed inbound message (webhook, API, uploaded file). Parent for all processing.
- **Document** — Structured ingestion result (title, content, source URL, metadata). One per ingestion.
- **Claim** — Extracted fact (e.g., "Biden age is 81"). Multiple per document.
- **Evidence** — Resolved claim with cross-validation, conflict detection, and confidence score.
- **Conflict** — Two claims in direct contradiction; score severity.
- **Provenance** — Immutable record of which documents contributed to each claim (for auditing).

**Key Invariants**:
- Every Claim traces back to a Document and RawItem (full lineage).
- Every Evidence has exactly one Confidence Score.
- Conflicts are bidirectional (if A conflicts with B, then B conflicts with A).
- No stage skipped — all 12 stages execute in order (Collect→Normalize→Deduplicate→Document→Extract→Resolve→Cross-Validate→Detect Conflicts→Score→Summarize→Interest Match→Broadcast).

**Interactions**:
- **← Identity Context**: RawItem initiator is a user.
- **→ Interest Context**: Evidence is matched against user interests.
- **→ Broadcast Context**: Summarized evidence is broadcast to matched users.

---

### Context 3: Interest Context
**Responsibility**: Manage user interests/topics and match evidence to interests.

**Entities**:
- **Interest** — A topic the user cares about (e.g., "climate change", "AI safety"). User-scoped.
- **InterestMatch** — Declarative rule matching evidence against interests (keyword, NLP `[ASSUMED]`, ML model `[ASSUMED]`).
- **Feedback** — User indicates "this is relevant" or "not relevant" (trains interest matching loop).

**Key Invariants**:
- Each interest belongs to exactly one user.
- An InterestMatch is a predicate; it's applied at broadcast time to decide if evidence goes to this user.
- Feedback is append-only; used to retrain matching rules (offline or online `[ASSUMED]`).

**Interactions**:
- **← Evidence Context**: Match evidence against user's interests.
- **→ Broadcast Context**: Deliver evidence matching the user's interests.

---

### Context 4: Broadcast Context
**Responsibility**: Deliver evidence to users across multiple channels.

**Entities**:
- **Broadcast** — A single piece of evidence + delivery plan (which users, which channels, when).
- **Delivery** — One broadcast + one user + one channel + status (pending, sent, failed, retry).
- **DeliveryStatus** — {pending, sent, failed, retrying, exhausted, blocked}.
- **ChannelAdapterCallback** — Webhook response from Telegram/WhatsApp/WeChat (delivery confirmation, read receipt `[ASSUMED]`).

**Key Invariants**:
- One Broadcast may produce many Deliveries (one per user × channel combination).
- Delivery idempotency via dedup key (same evidence to same user+channel = one delivery, not many).
- Failed deliveries are retried with exponential backoff; exhausted after N attempts (→ DLQ).
- Delivery status is updated via channel callbacks or timeout.

**Interactions**:
- **← Evidence Context**: Input is summarized evidence.
- **← Interest Context**: Delivery recipients determined by interest matching.
- **→ Infra (ChannelAdapter)**: Sends message via Telegram/WhatsApp/WeChat/WeCom.

---

## Deliverable 5: Domain Model (ER Sketch)

### Core Tables (Simplified)

```
Identity Context:
├── tenants (id, name, plan, status, ...)
├── users (id, tenant_id, email, roles, status, ...)
├── devices (id, user_id, device_id, apns_token, last_active, ...)
├── channel_bindings (id, user_id, channel, handle/id, status, ...)
├── api_keys (id, user_id, key_hash, scopes, created_at, rotated_at, ...)
└── audit_events (id, tenant_id, actor_id, action, resource, timestamp, ...)

Evidence Context:
├── raw_items (id, tenant_id, channel, sender_id, text, received_at, ...)
├── documents (id, tenant_id, raw_item_id, title, content, source_url, indexed_at, ...)
├── claims (id, document_id, statement, confidence, extracted_at, ...)
├── evidences (id, tenant_id, claim_id, status, confidence_score, resolved_at, ...)
├── conflicts (id, evidence_a_id, evidence_b_id, severity, detected_at, ...)
└── provenances (id, evidence_id, document_id, raw_item_id, ...)

Interest Context:
├── interests (id, user_id, topic, description, created_at, ...)
├── interest_matches (id, interest_id, rule_type, rule_config, active, ...)
└── feedbacks (id, user_id, evidence_id, is_relevant, timestamp, ...)

Broadcast Context:
├── broadcasts (id, tenant_id, evidence_id, created_at, ...)
├── deliveries (id, broadcast_id, user_id, channel, status, attempted_at, delivered_at, ...)
└── delivery_callbacks (id, delivery_id, source_delivery_id, callback_type, data, received_at, ...)
```

### Key Cross-Context Relationships

- **RawItem → User** (who sent it via which channel).
- **Document → RawItem** (where it came from).
- **Claim → Document** (which document it was extracted from).
- **Evidence → Claim + Document + RawItem** (full lineage).
- **Delivery → Broadcast + User + Channel** (where evidence goes).
- **InterestMatch → Interest** (which topics trigger delivery).

### Isolation Keys (Tenant Safety)

Every row must have at least one of:
- `tenant_id` (most tables, except sessions/temp).
- `user_id` (scoped within a tenant).
- `device_id` (scoped within a user).

Enforced via:
- **NOT NULL constraints** on isolation keys.
- **Row-Level Security (RLS) policies** in PostgreSQL (see deliverable 6).
- **Query filters in application code** (belt-and-suspenders).

---

## Validation of Design Constraints

✅ **No stage skipped** — All 12 stages are distinct entities/flows in the domain.  
✅ **Multi-tenant mandatory** — `tenant_id` or `user_id` on every table; RLS enforced.  
✅ **Provider abstraction** — Evidence Context does not import any external SDK; uses provider interfaces.  
✅ **One ChannelAdapter interface** — Broadcast Context routes via a single abstraction.  
✅ **Idempotency** — Deliveries are deduplicated via (broadcast_id, user_id, channel) key.
