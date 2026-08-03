# ADR-0001: Monorepo vs Polyrepo

**Status**: ADOPTED  
**Date**: 2026-08-03  
**Context**: Repository structure for multi-service EIOS platform.

## Decision

**Use a monorepo** (single Git repository containing all services, packages, documentation, and CI/CD).

## Rationale

- **Atomic commits** — Changes across gateway, api, worker, and shared packages can be tested together before merging.
- **Shared CI/CD** — One pipeline (`deployments/`, `.github/workflows/`) for all components.
- **Dependency management** — Clear visibility of cross-service dependencies (no hidden coupling).
- **Documentation co-location** — Architecture docs, code, and deployment instructions live together.
- **Easier refactoring** — Renaming a domain concept updates all services automatically (IDE refactoring tools work across the repo).

## Tradeoff

- **Repo size** — Monorepo can grow large; mitigated by sparse checkout and shallow clones.
- **Build time** — More code to lint/test per commit; mitigated by per-service CI steps and caching.

## Alternatives Considered

- **Polyrepo** (separate repos per service) — Rejected due to deployment complexity and cross-service dependency management.

## References

- `docs/architecture/01-repository-architecture.md` — Folder structure.
- `.github/CODEOWNERS` — Ownership rules per directory.
