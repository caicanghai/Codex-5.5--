#!/usr/bin/env bash
# First-time deploy: ensure .env, enable swap, build, start, verify health.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$DIR/_common.sh"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example."
  echo ">>> Edit .env and set TELEGRAM_BOT_TOKEN (and OPENAI_API_KEY if used), then re-run:"
  echo "    bash scripts/ops/deploy.sh"
  exit 1
fi

if ! grep -qE '^TELEGRAM_BOT_TOKEN=.+' .env; then
  echo "ERROR: TELEGRAM_BOT_TOKEN is empty in .env. Set it, then re-run." >&2
  exit 1
fi

echo "== Ensuring swap =="
bash "$DIR/setup_swap.sh" || echo "(swap step skipped)"

echo "== Building and starting containers =="
dc up -d --build

echo "== Waiting for health (up to ~120s) =="
bash "$DIR/healthcheck.sh" --wait

echo "Deploy complete."
