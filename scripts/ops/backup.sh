#!/usr/bin/env bash
# Back up the PostgreSQL database to ./backups/db_<timestamp>.sql.gz
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$DIR/_common.sh"

mkdir -p backups
TS="$(date -u +%Y%m%d_%H%M%S)"
OUT="backups/db_${TS}.sql.gz"

echo "Dumping database '${POSTGRES_DB}' as user '${POSTGRES_USER}' ..."
dc exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$OUT"

echo "Backup written: $OUT ($(du -h "$OUT" | cut -f1))"

# Retention: keep the 14 most recent backups.
ls -1t backups/db_*.sql.gz 2>/dev/null | tail -n +15 | xargs -r rm -f
echo "Old backups pruned (keeping 14 most recent)."
