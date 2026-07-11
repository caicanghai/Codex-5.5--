# EIOS Security Baseline

**Status:** Structure prepared in Milestone 0. **None of the controls below are
implemented yet** — this document defines _where_ and _how_ they will be built
so that later milestones have a clear target.

For vulnerability reporting see [Reporting](#reporting) at the bottom.

---

## 1. Security model overview

EIOS is multi-tenant and channel-facing, so it treats all inbound data as
untrusted and enforces isolation at every layer. Security is designed into the
structure from the foundation, ahead of the features it protects.

## 2. Controls to be implemented

### 2.1 RBAC (Role-Based Access Control)

- Roles and permissions are defined centrally and enforced at the API and
  Workflow layers.
- Prepared location: `services/api` (policy) + `packages` (shared authz).

### 2.2 Multi-tenant isolation

- Every record, queue, and object-storage prefix is tenant-scoped.
- Identity Layer resolves and stamps the tenant on each request.
- No cross-tenant reads without an explicit, audited elevation path.

### 2.3 API key isolation

- Keys are scoped per tenant and per integration, with least privilege.
- Keys are hashed at rest; never logged; rotated on a schedule.

### 2.4 Webhook verification

- All inbound webhooks verify signatures/timestamps before processing.
- Replay protection via nonce/timestamp windows.
- Prepared location: `services/gateway` inbound edge.

### 2.5 Audit logging

- Security-relevant actions emit tamper-evident, append-only audit events.
- Audit records are tenant-scoped and never contain secrets or raw PII.

### 2.6 Secrets management

- Secrets come from the environment / a secrets manager, never source control.
- `.env` files are git-ignored; `deployments/.env.example` documents the shape
  only, with placeholder values.

### 2.7 Rate limiting

- Per-tenant and per-key limits at the gateway and API, backed by Redis.
- Protects against abuse and cost blowups on outbound channels.

### 2.8 Prompt-injection isolation

- Inbound messages and model output are untrusted content, never instructions.
- Any LLM-assisted step runs with a constrained tool surface and cannot escalate
  its own permissions.

### 2.9 Tool permission boundaries

- Automated/agentic steps operate within an explicit allowlist of tools and
  scopes; boundaries are declared, reviewable, and enforced, not implicit.

## 3. Supply-chain security

- **Dependency scanning** via Dependabot (`.github/dependabot.yml`) and CI.
- **Secret scanning** enabled on the repository and validated in CI.
- Pinned versions; PRs required for dependency bumps.

## 4. Data handling principles

- Minimize collection; scope retention.
- Encrypt in transit; encrypt sensitive data at rest.
- Never log secrets, tokens, or raw PII.

## 5. Reporting

If you discover a vulnerability, **do not open a public issue.** Report it
privately to the Security Owner via the repository's private security advisory
channel. Include affected component, reproduction steps, and impact. You will
receive an acknowledgement and a remediation timeline.
