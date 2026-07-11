# Tests

Test suites for EIOS. **Milestone 0: folders only — no tests are required yet.**
The structure exists so later milestones drop tests into the right place.

| Folder | Scope |
| ------ | ----- |
| `unit/` | Pure, isolated logic. No external services; use `fixtures/`. |
| `integration/` | Multiple units together, backing services via Compose. |
| `e2e/` | Full flows across services. |
| `security/` | Authz, tenant isolation, webhook verification, injection isolation. |
| `fixtures/` | Shared deterministic test data. |

## Rules

- Tests are deterministic and independent (see [CODING_RULES §7](../docs/CODING_RULES.md)).
- New behavior ships with tests in the matching folder.
- The CI `test` job runs the configured runner; in Milestone 0 it is a no-op
  placeholder that succeeds with no tests present.
