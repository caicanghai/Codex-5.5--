#!/usr/bin/env bash
# Report container health. With --wait, poll until healthy or timeout.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$DIR/_common.sh"

SERVICES="db redis api bot"

check_once() {
  local all_ok=1
  for svc in $SERVICES; do
    cid="$(dc ps -q "$svc" 2>/dev/null || true)"
    if [ -z "$cid" ]; then
      echo "  $svc: not running"; all_ok=0; continue
    fi
    status="$($DOCKER inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$cid" 2>/dev/null || echo unknown)"
    echo "  $svc: $status"
    case "$status" in
      healthy|running) ;;
      *) all_ok=0 ;;
    esac
  done
  return $((1 - all_ok))
}

if [ "${1:-}" = "--wait" ]; then
  for i in $(seq 1 24); do
    echo "health attempt $i:"
    if check_once; then echo "ALL HEALTHY"; exit 0; fi
    sleep 5
  done
  echo "TIMED OUT waiting for health" >&2
  dc ps
  exit 1
else
  echo "Container health:"
  if check_once; then echo "ALL HEALTHY"; exit 0; else echo "NOT ALL HEALTHY" >&2; exit 1; fi
fi
