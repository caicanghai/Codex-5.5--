# Deliverables 20–23: Monitoring, Backup, DR & Secrets

## Deliverable 20: Monitoring & Logging

### Structured Logging (JSON)

Every log entry includes:
```json
{
  "timestamp": "2026-08-03T12:34:56Z",
  "level": "INFO",
  "service": "gateway",
  "trace_id": "uuid",
  "tenant_id": "uuid",
  "user_id": "uuid",
  "stage": "extract",
  "message": "Successfully extracted 5 claims",
  "latency_ms": 1250,
  "error": null
}
```

**No secrets/PII in logs** — Token/key redacted; email masked (if logged).

### Metrics (Prometheus-style)

```
# Queue depth per stage
eios_queue_depth{stage="extract", tenant_id="uuid"} 23
eios_queue_depth{stage="summarize", tenant_id="uuid"} 15

# Task latency per stage (histogram)
eios_task_latency_seconds_bucket{stage="extract", le="1.0"} 10
eios_task_latency_seconds_bucket{stage="extract", le="5.0"} 28

# Error rate per stage
eios_task_errors_total{stage="broadcast", reason="network"} 5
eios_task_errors_total{stage="summarize", reason="llm_timeout"} 2

# Delivery status
eios_deliveries_total{status="sent", channel="telegram"} 1024
eios_deliveries_total{status="failed", channel="wecom"} 3

# Provider latency
eios_provider_latency_seconds{provider="openrouter", operation="extract"} 2.15
```

### Tracing (OpenTelemetry `[ASSUMED]`)

Trace spans across:
- Gateway → Queue → Worker stages → DB/External API calls.
- Each span includes `trace_id`, `span_id`, `parent_id`, `tenant_id`.
- Sent to observability backend (Jaeger, Lightstep, etc. `[ASSUMED]`).

### Health Endpoints

```
GET /health
  → Returns 200 if all dependencies (DB, Redis) are up.

GET /metrics
  → Prometheus-compatible metrics endpoint (port 9090).

GET /readiness
  → Returns 200 if service is ready to serve traffic.
```

### Alerting Rules `[ASSUMED]`

- **DLQ size > 100** → Alert; investigate failed tasks.
- **Provider latency > 10s** → Alert; possible rate limiting or outage.
- **Delivery failure rate > 5%** → Alert; check platform webhooks.
- **Backup failure** → Alert; on-call investigates.
- **Database replication lag > 1s** → Alert; check network.

---

## Deliverable 21: Backup Strategy

### PostgreSQL Backups

- **Frequency**: Nightly logical dumps (midnight UTC).
- **Retention**: Daily (7), Weekly (4), Monthly (6) = ~35 backups on-disk.
- **Location**: Object storage (MinIO or S3).
- **WAL Archiving**: Continuous (every 1 MB, or every 60s).
  - Enables point-in-time recovery (PITR) within 24 hours.
  - Sent to object storage; separate from dumps.

```bash
# Backup script (cron: 0 0 * * *)
pg_dump postgresql://eios:pass@localhost/eios | gzip > /backup/pg_dump_$(date +%Y%m%d).sql.gz
aws s3 cp /backup/pg_dump_*.sql.gz s3://eios-backups/postgres/
```

### MinIO Backups

- **Versioning**: Enabled on all buckets (keeps deleted objects).
- **Replication**: Nightly sync to an offsite S3 bucket (e.g., Backblaze B2).
- **Retention**: Tiered (30 days recent, 1 year archive on cheaper storage).

### Redis Backups

- **RDB snapshots**: Periodic (hourly), saved to object storage.
- **AOF**: Enabled (append-only file); survives crashes.
- **Note**: Redis is rebuilt from Postgres on recovery; not the source of truth.

### Backup Encryption

- All backups encrypted at rest (AES-256).
- Decryption key stored in secrets manager (separate from backup storage).
- Backups cannot be restored without the key (defense against unauthorized access).

---

## Deliverable 22: Disaster Recovery Strategy

### RPO/RTO Targets `[ASSUMED — V7/V8 confirmation]`

- **RPO (Recovery Point Objective)**: ≤ 24 hours (nightly dumps) / ≤ 5 minutes (WAL).
- **RTO (Recovery Time Objective)**: ≤ 2 hours (provision VPS → restore Postgres → redeploy).

### Runbook: Full VPS Loss

1. **Provision new VPS** (same size, OS).
2. **Restore PostgreSQL**:
   - Download latest dump from S3.
   - `psql < pg_dump.sql`.
   - Replay WAL logs (PITR to last good state).
3. **Restore MinIO**:
   - Download versioned buckets from backup replica.
   - Restore to local MinIO.
4. **Redeploy Containers**:
   - `git clone` source repo.
   - `docker-compose -f docker-compose.prod.yml up -d`.
   - Containers pull secrets from environment (Vault or AWS Secrets Manager).
5. **Replay Outbox**:
   - Check DLQ for unprocessed tasks; replay from State 1.
   - Check Delivery table for pending items; retry.
6. **Verify Healthchecks**:
   - `curl http://localhost/health` (proxy).
   - `curl http://localhost/api/v1/health` (API).
   - Monitor logs for errors.

**Total time: ~30 minutes to 2 hours (depending on data size).**

### Regular Restore Drills

- **Frequency**: Monthly.
- **Procedure**: Restore dumps to a test VPS; verify data integrity.
- **Outcome**: Confirm runbook is up-to-date and achieves RTO/RPO targets.

### Backup Verification

- Nightly: Verify dump integrity (`pg_restore --list`).
- Weekly: Test restore to staging environment.
- Monthly: Full DR drill (see above).

---

## Deliverable 23: Secrets Management

### Principle: Never in Git

```
✗ .env (git-ignored)
✗ config.yaml with API keys
✗ Docker env secrets in Dockerfile

✓ .env.example (shape only, no secrets)
✓ Secrets injected at runtime from:
  - Environment variables (VPS / CI/CD system)
  - Secrets manager (Vault, AWS Secrets Manager, Tencent Secrets Manager)
```

### Secret Types & Policies

| Secret | Issuance | Rotation | Scope |
|--------|----------|----------|-------|
| **DB password** | At setup | Annual (or emergency) | Tenant (all users share same DB pw) |
| **API keys (third-party)** | Per tenant/user config | Per user, 90 days | Per user or per tenant |
| **JWT secret** | At deployment | Annual | Global (signs all tokens) |
| **Redis AOF password** | At setup | Annual | Local |
| **Telegram bot token** | BotFather | Per user/tenant | Per tenant |
| **WeCom secret** | WeCom admin | Per app/tenant | Per tenant |
| **Webhook signatures** | Platform-specific | Platform-managed | Per integration |

### Rotation Workflow

1. **Generate new secret** (e.g., new DB password via AWS Secrets Manager).
2. **Update consumers** (app config, scripts, etc.) to use new secret.
3. **Test** in staging environment.
4. **Rotate in production** (minimal downtime; old secret still accepted for X minutes).
5. **Verify** all services connected with new secret.
6. **Archive** old secret in audit log (immutable).

### Credential Masking in App

```python
# In settings.py
class Settings(BaseSettings):
    ai_api_key: str = Field(...)
    
    def __repr__(self):
        # Mask secret in repr/logs
        return f"Settings(ai_api_key='***')"
```

### Audit Trail (Secrets Access)

- Every secret read logged: `timestamp`, `actor`, `secret_id`, `reason`.
- Append-only; no deletion.
- Alerts on unusual access patterns (e.g., secret read from unexpected service).

---

## Security Checklist (Pre-Production)

- [ ] No .env or secrets in git repository.
- [ ] Secrets scanning (Gitleaks) enabled in CI.
- [ ] All external API keys rotated (or new keys issued for prod).
- [ ] Database user password is strong (20+ chars, random).
- [ ] TLS certificate installed (Caddy auto-renew from Let's Encrypt).
- [ ] Rate limiting enabled on proxy.
- [ ] CORS configured (only trusted origins).
- [ ] SQL injection testing (ORM-protected, parameterized queries).
- [ ] XSS protection (API returns JSON; web-admin CSP headers).
- [ ] CSRF tokens on state-changing endpoints.
- [ ] Backup restore tested (weekly).
- [ ] Audit logs retained (≥90 days).

✅ See `CODING_RULES.md` for full security guidelines.
