#!/usr/bin/env bash
# Pull latest code, rebuild, restart, and prune old images.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$DIR/_common.sh"

echo "== Pulling latest code =="
git pull --ff-only

echo "== Rebuilding and restarting =="
dc up -d --build

echo "== Pruning dangling images =="
$DOCKER image prune -f >/dev/null || true

bash "$DIR/healthcheck.sh" --wait
echo "Update complete."
