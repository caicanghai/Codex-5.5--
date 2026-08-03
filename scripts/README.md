# Scripts

Operational and developer scripts for EIOS. **Milestone 0: minimal helpers only.**

| Script | Purpose |
| ------ | ------- |
| `validate-compose.sh` | Validate the dev Docker Compose file (`docker compose config`). Used by CI. |

Scripts are POSIX `sh`/`bash`, executable, and idempotent. They must not embed
secrets and should fail loudly on error (`set -euo pipefail`).
