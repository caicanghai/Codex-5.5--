# ADR-0002 · Backend language & framework

- **Status:** Accepted — **Python / FastAPI** (decided with the user this session)
- **Context:** The deployment target names FastAPI explicitly, but the
  Milestone 0 foundation shipped a TypeScript toolchain. This inconsistency had
  to be resolved before implementation planning.
- **Decision:** Backend `services/*` and backend `packages/*` are **Python**
  (FastAPI, with ruff/black/mypy). **TypeScript is retained only for
  `apps/web-admin/`**; `apps/ios/` uses Swift. The Milestone 0 TS root tooling is
  repurposed toward the web-admin scope; nothing is deleted destructively.
- **Consequences:** CI gains a Python lane (lint/type/test) alongside the JS lane
  for web-admin. `docs/CODING_RULES.md` and `docs/DECISIONS.md` need a
  documentation update to reflect Python as the backend baseline (done on
  approval, additively).
