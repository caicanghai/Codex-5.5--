# Deployments

Local development topology for EIOS. **Milestone 0 provides placeholders only** —
no application logic runs. The Compose file describes the *shape* of the system
so local and production environments stay aligned (see
[ADR-0006](../docs/DECISIONS.md)).

## Contents

- `docker-compose.dev.yml` — development topology (backing services + app
  service placeholders).
- `.env.example` — documents required environment variables with placeholder
  values only. Copy to `.env` (git-ignored) for local use.

## Services

Backing services:

| Service | Purpose |
| ------- | ------- |
| `postgres` | primary relational store |
| `redis` | queues, cache, rate limiting |
| `minio` | S3-compatible object storage |
| `directus` | headless data/admin layer (placeholder, not implemented) |
| `n8n` | external automation surface (placeholder, not implemented) |

Application services (placeholders — no logic in M0):

| Service | Purpose |
| ------- | ------- |
| `gateway` | Unified Channel Gateway edge |
| `api` | HTTP / OpenAPI surface |
| `worker` | asynchronous engine/broadcast processing |

## Usage (once services are implemented)

```bash
cp deployments/.env.example deployments/.env   # then edit values
docker compose -f deployments/docker-compose.dev.yml config   # validate
docker compose -f deployments/docker-compose.dev.yml up -d    # (later milestones)
```

> In Milestone 0 the `gateway`, `api`, and `worker` services are commented
> placeholders with no images to build. Only `config` validation is exercised
> by CI.
