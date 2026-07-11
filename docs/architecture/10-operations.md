# 10 — Monitoring, Logging, Backup, DR & Secrets

Deliverables **20 (Monitoring & Logging)**, **21 (Backup)**,
**22 (Disaster Recovery)**, and **23 (Secrets management)**.

---

## 20. Monitoring & Logging

- **Structured JSON logs** with `trace_id`, `tenant_id`, `stage`; **never**
  secrets or raw PII. `[VERIFIED principle]`
- **Metrics [ASSUMED]** (Prometheus-style, viewed in Grafana or hosted):
  queue depth per stage, stage latency, provider latency + cost, delivery
  success/failure, error rates, rate-limit rejections.
- **Tracing [ASSUMED]**: OpenTelemetry spans across
  gateway → queue → worker stages → send.
- **Health**: per-container health endpoints feeding proxy + Compose checks.
- **Alerting [ASSUMED]** on: DLQ growth, provider circuit-breaker trips,
  delivery-failure spikes, backup-job failure, disk pressure.

## 21. Backup strategy

| Asset | Method | Retention `[ASSUMED]` |
|-------|--------|-----------------------|
| PostgreSQL | nightly logical dump **+** continuous WAL archiving to object storage | daily 7 / weekly 4 / monthly 6 |
| Object storage (MinIO) | bucket versioning + periodic offsite replication | per-bucket policy |
| Redis | AOF for short-term durability; treated as **rebuildable** (queues/cache) | not source of truth |
| Secrets | stored/rotated in the secrets manager, backed up there | separate from app data |

- Backups **encrypted at rest**; integrity checked; restores tested (see DR).

## 22. Disaster Recovery strategy

- **Targets [ASSUMED — confirm V7/V8]:** RPO ≤ 24h (dumps) / ≤ 5m (WAL);
  RTO ≤ a few hours on a fresh VPS.
- **Runbook:**
  1. Provision a new Ubuntu VPS.
  2. Restore Postgres (base dump + WAL replay).
  3. Restore MinIO from offsite replica.
  4. Redeploy Compose from **pinned image digests**.
  5. Replay the transactional **outbox** and per-stage DLQs.
  6. Verify healthchecks; resume traffic at the proxy.
- **In-flight pipeline items** resume from their last completed stage — the
  "no stage skipped" invariant survives recovery.
- **Restore drills** run on a schedule to validate backups + runbook.

```mermaid
flowchart LR
    A[Fresh VPS] --> B[Restore Postgres base+WAL]
    B --> C[Restore MinIO]
    C --> D[Redeploy Compose pinned]
    D --> E[Replay outbox + DLQ]
    E --> F[Healthcheck + resume]
```

## 23. Secrets management

- **No secrets in git.** `.env` git-ignored; `*.env.example` documents shape
  only. `[VERIFIED — enforced in Milestone 0]`
- Runtime secrets from environment / a secrets manager. The app persists only
  `credentials_ref`, **never inline** provider or channel credentials.
  `[VERIFIED principle]`
- Per-tenant / per-user credentials isolated; **never shared** across tenants.
- **Rotation** policy for API keys and provider credentials; keys hashed at rest.
- **Secret scanning** (Gitleaks + GitHub native) already wired in Milestone 0 CI.
