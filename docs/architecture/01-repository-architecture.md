# Deliverable 3: Repository Architecture

## Folder Structure & Justification

```
eios/
├── docs/
│   ├── architecture/               # This blueprint (25 deliverables)
│   │   ├── README.md
│   │   ├── 00-*.md through 11-*.md
│   │   └── adr/
│   ├── CODING_RULES.md            # Python/FastAPI, ruff/black/mypy, iOS (Swift), web-admin (TS)
│   └── DECISIONS.md                # Stack decisions, trace of ADRs
│
├── deployments/
│   ├── docker-compose.dev.yml      # Local dev (Telegram + offline AI)
│   ├── docker-compose.prod.yml     # Production (all channels, external providers)
│   ├── env/
│   │   ├── .env.example            # Shape only, no secrets
│   │   ├── .env.dev.example        # Dev defaults
│   │   └── .env.prod.example       # Prod template
│   └── scripts/
│       ├── backup.sh               # Nightly DB/MinIO backup
│       ├── restore.sh              # DR runbook
│       └── healthcheck.sh          # Proxy healthchecks
│
├── services/
│   ├── gateway/                    # Webhook receiver (FastAPI)
│   │   ├── app/
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── api/                        # REST API (FastAPI)
│   │   ├── app/
│   │   │   ├── routes/
│   │   │   ├── schemas/
│   │   │   └── security/
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── worker/                     # Pipeline stages (Arq/Celery tasks)
│   │   ├── app/
│   │   │   ├── stages/             # Normalize, Extract, Resolve, etc. (one module per stage)
│   │   │   └── tasks.py            # Queue registration
│   │   ├── tests/
│   │   └── pyproject.toml
│   └── scheduler/                  # Periodic jobs (APScheduler)
│       ├── app/
│       └── pyproject.toml
│
├── packages/
│   ├── core/                       # Shared kernel
│   │   ├── models.py               # Pydantic models (Tenant, User, Device, Document, RawItem, Evidence, Broadcast)
│   │   ├── enums.py                # Enums (Status, Channel, Provider, Intent)
│   │   └── errors.py               # Exception hierarchy
│   │
│   ├── domain/                     # DDD Bounded Contexts (no business logic in services/)
│   │   ├── evidence/               # Extract, Resolve, Cross-Validate, Score, Summarize
│   │   │   ├── claim.py
│   │   │   ├── resolution.py
│   │   │   ├── conflict_detector.py
│   │   │   └── scorer.py
│   │   ├── interest/               # Interest matching & feedback loop
│   │   │   ├── interest.py
│   │   │   └── matcher.py
│   │   ├── broadcast/              # Broadcast engine
│   │   │   ├── broadcast.py
│   │   │   ├── delivery.py
│   │   │   └── status.py
│   │   └── tenancy/                # Multi-tenant context & RLS
│   │       └── context.py
│   │
│   ├── providers/                  # Provider interfaces (abstraction layer)
│   │   ├── ai_provider.py          # Summarization, embedding
│   │   ├── tts_provider.py         # Text-to-speech
│   │   ├── search_provider.py      # Web search
│   │   ├── storage_provider.py     # Object storage (S3-compatible)
│   │   ├── notification_provider.py # APNs, FCM
│   │   ├── auth_provider.py        # OIDC, email+passkey
│   │   └── messaging_provider.py   # Channel adapters (Telegram, WhatsApp, etc.)
│   │
│   ├── channels/                   # ChannelAdapter implementations (one per platform)
│   │   ├── telegram_adapter.py
│   │   ├── whatsapp_adapter.py
│   │   ├── wechat_adapter.py
│   │   ├── wecom_adapter.py
│   │   └── channel_envelope.py     # Internal message format (Deliverable 3)
│   │
│   ├── infra/                      # Infrastructure (no business logic)
│   │   ├── db/
│   │   │   ├── session.py          # SQLAlchemy + RLS context
│   │   │   ├── migrations/         # Alembic (flyway alternative)
│   │   │   └── rls_policies.sql    # Row-level security policies
│   │   ├── cache/
│   │   │   └── redis_client.py
│   │   ├── queue/
│   │   │   └── queue_client.py
│   │   ├── storage/
│   │   │   └── minio_client.py
│   │   └── logging/
│   │       └── structured_logger.py
│   │
│   ├── security/                   # Auth & RBAC (no business logic)
│   │   ├── auth.py                 # JWT validation, API key hashing
│   │   ├── rbac.py                 # Permission checks
│   │   ├── audit.py                # Append-only audit events
│   │   └── secrets.py              # Secret rotation policy
│   │
│   ├── plugins/                    # Plugin SDK
│   │   ├── plugin_base.py          # Base class (stage handler, provider extension)
│   │   ├── loader.py               # Dynamic plugin loading
│   │   └── examples/               # Example plugins (optional in v0.1)
│   │
│   └── shared_tests/               # Fixtures, helpers
│       └── factories.py            # Test data factories
│
├── apps/
│   └── web-admin/                  # Admin dashboard (React/TS — kept from M0)
│       ├── src/
│       ├── tsconfig.json
│       └── package.json
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                  # Lint, test, type-check, secret-scan
│   │   ├── build.yml               # Docker build
│   │   └── deploy.yml              # Deploy to prod VPS
│   └── CODEOWNERS
│
├── pyproject.toml                  # Workspace root (Poetry or uv)
├── .env.example                    # Config shape (no secrets, git-checked)
├── Makefile                        # Dev tasks (test, lint, format)
├── README.md                        # Quick start (repo description)
└── .gitignore                      # .env, __pycache__, secrets, etc.
```

---

## Folder Design Decisions

### services/ — Deployable units

- Each service has its own `pyproject.toml` and can be deployed independently.
- **gateway**: Stateless, scales horizontally, processes webhooks.
- **api**: Stateless, scales horizontally, serves REST + OpenAPI.
- **worker**: Scales per pipeline stage; pulls from Redis queues.
- **scheduler**: Stateful (single leader or HA), triggers periodic tasks and DLQ retry.

### packages/ — Shared libraries (no executable code)

- **core**: Models, enums, errors used by all services.
- **domain**: Bounded contexts (business logic in isolation).
- **providers**: Interface definitions (implementations vary by config).
- **channels**: Channel adapters (one ChannelAdapter interface, one implementation per platform).
- **infra**: DB sessions, cache clients, queue clients (not executable; imported by services).
- **security**: Auth, RBAC, audit (not executable; imported by services).
- **plugins**: Plugin SDK for extending stages and providers.

### apps/ — Web frontends

- **web-admin**: Admin dashboard (TypeScript/React, built separately).
- iOS app is in a separate repository (Swift).

### deployments/ — Infrastructure-as-code

- `docker-compose.*.yml` defines all containers, networks, volumes.
- `.env.*.example` documents configuration shape (no secrets).
- Scripts for backup, restore, health checks.

### docs/architecture/ — Blueprint & ADRs

- This documentation suite (25 deliverables).
- ADRs for decisions (locked or open for review).

---

## Key Constraints (Verified & Assumed)

- **No business logic in service main files** — All logic is in `packages/domain/` modules, imported by workers/API.
- **No cross-service direct calls** — All communication via Redis queues (async) or PostgreSQL (via API calls).
- **Multi-tenancy mandatory in every layer** — `tenant_id` on every table row, every cache key, every log message, every queue message.
- **Provider abstraction enforceable** — No service imports external SDK directly (e.g., no `import openai`); instead, import from `packages/providers/`.
- **Secrets never in git** — `.env` git-ignored; `.env.example` is shape only.
- **CI/CD from git** — All deployment driven by GitHub Actions (build, test, scan, deploy).

---

## File Ownership (CODEOWNERS)

```
# In .github/CODEOWNERS:
/docs/architecture/         @architect
/packages/domain/           @domain-owners
/packages/providers/        @providers-lead
/services/gateway/          @gateway-team
/services/api/              @api-team
/services/worker/           @worker-team
```
