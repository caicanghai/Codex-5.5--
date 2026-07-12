#!/usr/bin/env bash
# Start (or restart) all services in the background.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$DIR/_common.sh"

dc up -d
dc ps
