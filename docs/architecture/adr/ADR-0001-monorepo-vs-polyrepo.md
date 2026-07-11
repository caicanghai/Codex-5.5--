# ADR-0001 · Monorepo vs polyrepo

- **Status:** Accepted `[ASSUMED — confirm at review]`
- **Context:** EIOS ships multiple deployables (gateway, api, worker, scheduler)
  plus shared packages, an iOS app, and a web admin. They evolve together and
  share contracts (Envelope, domain types).
- **Decision:** Single **monorepo**. Backend services/packages, `apps/ios`, and
  `apps/web-admin` live in one repository with shared `packages/contracts`.
- **Consequences:** Atomic cross-cutting changes and one CI; requires clear
  ownership (CODEOWNERS) and path-scoped builds to avoid coupling. iOS uses its
  own toolchain within the same repo.
