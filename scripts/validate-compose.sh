#!/usr/bin/env bash
# Validate the EIOS development Docker Compose file.
# Milestone 0: only configuration validation, no containers are started.
set -euo pipefail

COMPOSE_FILE="deployments/docker-compose.dev.yml"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is not installed; skipping compose validation." >&2
  exit 0
fi

echo "Validating ${COMPOSE_FILE} ..."
docker compose -f "${COMPOSE_FILE}" config >/dev/null
echo "OK: ${COMPOSE_FILE} is valid."
