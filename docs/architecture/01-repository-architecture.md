# 01 — Repository Architecture

Deliverable **3**. Every folder's existence is justified. No folder is invented
without a reason; where a folder already exists from Milestone 0 it is reused
rather than duplicated.

---

## Guiding rules

- **[VERIFIED]** Additive over the existing tree. Milestone 0 already created
  `docs/ services/ packages/ apps/ schemas/ deployments/ workflows/ tests/
  scripts/ architecture/ .github/`. This document reuses them and only proposes
  new sub-structure.
- **[VERIFIED]** OpenClaw is never forked into this tree. It is referenced
  through a single bridge package.
- **[ASSUMED]** Monorepo (single repo, multiple deployables) rather than
  multi-repo. Rationale: one VPS deployment, shared contracts, atomic changes
  across gateway/api/worker. See
  [ADR-0001](./adr/ADR-0001-monorepo-vs-polyrepo.md).

---

## Target tree (proposed, not yet created)

```text
Codex-5.5--/                      # repo root (existing)
├── docs/                         # [reuse] all documentation
│   └── architecture/             # [new] this blueprint + ADRs
├── architecture/                 # [reuse M0] diagrams source (kept)
├── schemas/                      # [reuse M0] contracts, single source of truth
│   ├── domain/                   #   conceptual domain models (M0)
│   ├── envelope/                 #   internal message envelope contract (M0)
│   ├── openapi/                  # [new] generated/authored OpenAPI (moved topic)
│   └── migrations/postgres/      #   DB migrations (M0 placeholder)
│
├── services/                     # [reuse M0] deployable runtime services
│   ├── gateway/                  #   inbound edge (FastAPI) — transport only
│   ├── api/                      #   REST surface (FastAPI)
│   ├── worker/                   #   pipeline & broadcast workers
│   └── scheduler/                # [new] periodic job scheduler
│
├── packages/                     # [reuse M0] shared libraries (no deploy unit)
│   ├── contracts/                # [new] envelope + domain types, generated
│   ├── core-domain/              # [new] DDD domain logic (pure, framework-free)
│   ├── providers/                # [new] provider interfaces + implementations
│   │   ├── model/                #     ModelProvider interface + adapters
│   │   ├── tts/                  #     TTSProvider
│   │   ├── storage/              #     StorageProvider
│   │   ├── search/               #     SearchProvider
│   │   ├── embedding/            #     EmbeddingProvider
│   │   ├── notification/         #     NotificationProvider (APNs, etc.)
│   │   └── auth/                 #     AuthenticationProvider
│   ├── channels/                 # [new] ChannelAdapter interface + adapters
│   │   ├── base/                 #     the one shared adapter interface
│   │   ├── telegram/             #     transport only
│   │   ├── whatsapp/             #     transport only
│   │   ├── wechat-oa/            #     transport only
│   │   ├── wecom/                #     transport only
│   │   └── apns/                 #     outbound push transport
│   ├── pipeline/                 # [new] evidence pipeline stage framework
│   ├── plugins/                  # [new] plugin SDK + registry (see 07)
│   ├── openclaw-bridge/          # [new] the ONLY dependency on OpenClaw
│   ├── persistence/              # [new] repositories, RLS helpers, unit-of-work
│   ├── messaging/                # [new] queue abstraction over Redis
│   ├── observability/            # [new] logging, metrics, tracing helpers
│   └── security/                 # [new] RBAC, tenant context, secrets access
│
├── apps/                         # [reuse M0] composition roots (thin)
│   ├── ios/                      # [new] native iOS app (separate toolchain)
│   └── web-admin/                # [new] admin SPA
│
├── plugins/                      # [new] first-party & example plugins (data)
├── deployments/                  # [reuse M0] compose, env templates, infra
│   ├── docker-compose.dev.yml    #   dev topology (M0)
│   ├── docker-compose.prod.yml   # [new] production topology
│   ├── caddy/ or nginx/          # [new] reverse proxy config
│   └── env/                      # [new] per-env .env templates (no secrets)
├── workflows/                    # [reuse M0] workflow/orchestration definitions
├── scripts/                      # [reuse M0] ops & dev scripts
├── tests/                        # [reuse M0] unit/integration/e2e/security/fixtures
└── .github/                      # [reuse M0] CI/CD, templates, CODEOWNERS
```

## Why each new folder exists

| Folder | Justification | Marker |
|--------|---------------|--------|
| `docs/architecture/` | Home for this blueprint + ADRs; keeps design discoverable next to other docs. | [VERIFIED need] |
| `services/scheduler/` | Periodic Collect and maintenance need a leader; separating it from workers avoids duplicate cron firing. | [ASSUMED] |
| `packages/contracts/` | One place for the envelope + shared types so gateway/api/worker never drift. | [VERIFIED principle] |
| `packages/core-domain/` | DDD aggregates/logic kept pure and framework-free so it is testable and replaceable. | [ASSUMED pattern] |
| `packages/providers/*` | Enforces "every external service is abstracted." One sub-package per provider category. | [VERIFIED principle] |
| `packages/channels/*` | Enforces "one identical ChannelAdapter." `base/` holds the single interface; each channel is transport-only. | [VERIFIED principle] |
| `packages/pipeline/` | The 12-stage pipeline needs a shared stage/step framework so no stage is skipped or reordered silently. | [VERIFIED principle] |
| `packages/plugins/` | Plugin SDK + registry (extension without forking core). | [ASSUMED design] |
| `packages/openclaw-bridge/` | The single, isolated dependency on OpenClaw; keeps "extend never fork" mechanically enforceable. | [ASSUMED — requires V1/V2] |
| `packages/persistence/` | Central repositories + RLS/tenant guards so tenant scoping is not re-implemented per service. | [VERIFIED principle] |
| `packages/messaging/` | Queue abstraction so Redis can later be swapped for a broker without touching workers. | [ASSUMED] |
| `packages/observability/` | Uniform logging/metrics/tracing across containers. | [ASSUMED] |
| `packages/security/` | RBAC checks, tenant-context propagation, secrets access in one audited place. | [VERIFIED principle] |
| `apps/ios/` | Native iOS app is a first-class client; its toolchain (Swift) lives apart from backend. | [VERIFIED target] |
| `apps/web-admin/` | Admin console implied by "Web Admin" client. | [ASSUMED] |
| `plugins/` (root) | Ships first-party/example plugins as data/config separate from the SDK code. | [ASSUMED] |
| `deployments/docker-compose.prod.yml` | Production topology distinct from dev; dev already exists. | [VERIFIED need] |
| `deployments/<proxy>/` + `env/` | Reverse-proxy config and per-env templates for reproducible deploys. | [ASSUMED] |

## Folders deliberately NOT added

- No `libs/`, `common/`, `utils/` grab-bags — shared code goes into a **named**
  `packages/*` with a clear owner. **[VERIFIED principle: no unnecessary
  folders.]**
- No per-channel top-level folders — channels live under `packages/channels/*`
  to force the shared interface.
- No `openclaw/` vendored copy — binding is via `openclaw-bridge` only, pending
  [ADR-0011](./adr/ADR-0011-openclaw-upstream-binding.md).

## Language boundary note

**[VERIFIED]** Backend target is Python/FastAPI. Milestone 0 shipped a
TypeScript toolchain. Options (resolve in
[ADR-0002](./adr/ADR-0002-language-and-framework.md)):

1. Adopt Python for all backend `services/*` and `packages/*`; keep the TS
   toolchain only for `apps/web-admin/`. **[ASSUMED recommended]**
2. Re-target M0 tooling to Python (ruff/black/mypy) and retire the TS root
   config.

Either way, `apps/ios/` uses the Swift toolchain independently.
