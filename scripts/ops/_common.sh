#!/usr/bin/env bash
# Shared helpers for EIOS ops scripts.
set -euo pipefail

# Resolve repo root (two levels up from this file).
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# Use sudo for docker only if the current user cannot talk to the daemon.
DOCKER="docker"
if ! docker info >/dev/null 2>&1; then
  DOCKER="sudo docker"
fi

dc() { $DOCKER compose "$@"; }

# Load POSTGRES_* from .env if present (for backup), with safe defaults.
POSTGRES_USER="${POSTGRES_USER:-eios}"
POSTGRES_DB="${POSTGRES_DB:-eios}"
if [ -f .env ]; then
  # shellcheck disable=SC1091
  set -a; . ./.env; set +a
fi
POSTGRES_USER="${POSTGRES_USER:-eios}"
POSTGRES_DB="${POSTGRES_DB:-eios}"
