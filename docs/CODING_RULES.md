# EIOS Coding Rules

These rules are binding for all EIOS code. They exist to keep the system
modular, secure, and reviewable. Process and branching live in
[`CONTRIBUTING.md`](./CONTRIBUTING.md).

---

## 1. Language & typing

- **TypeScript with `strict: true`.** No `any` in shipped code; use `unknown`
  and narrow. No implicit `any`, no unchecked index access.
- Prefer explicit return types on exported functions.
- No unused variables, parameters, or imports (enforced by ESLint).
- Prefer immutable data (`const`, `readonly`) and pure functions.

## 2. Architecture boundaries

- **No business logic in channel adapters.** Adapters translate transport only.
- Engines communicate through explicit contracts, never shared mutable state.
- Cross-layer calls follow the directional flow in
  [`ARCHITECTURE.md`](./ARCHITECTURE.md); no reaching past a neighbor.
- Shared logic goes in [`/packages`](../packages), not copy-pasted.

## 3. Contracts first

- Define/extend schemas in [`/schemas`](../schemas) and the OpenAPI document in
  [`/services/api`](../services/api) **before** implementing behavior.
- Message envelopes and public types are versioned; breaking changes require a
  decision record ([`DECISIONS.md`](./DECISIONS.md)).

## 4. Formatting & style

- **Prettier** is the single source of truth for formatting. Do not hand-format.
- **ESLint** enforces correctness rules; do not disable rules inline without a
  comment explaining why.
- `.editorconfig` governs whitespace/encoding across editors.
- File and directory names are `kebab-case`; TypeScript types are `PascalCase`;
  variables/functions are `camelCase`; constants are `UPPER_SNAKE_CASE`.

## 5. Security rules

- Never commit secrets. Use environment variables and the secrets management
  approach in [`SECURITY.md`](./SECURITY.md). `.env` files are git-ignored.
- Validate all external input at the boundary; never trust channel payloads.
- Every persisted record and request is tenant-scoped.
- Treat model/LLM output and inbound messages as untrusted (prompt-injection
  isolation); keep tool permission boundaries explicit.

## 6. Errors & logging

- Fail loudly at boundaries; never swallow errors silently.
- Log structured, non-sensitive context. Never log secrets, tokens, or raw PII.
- User-facing errors must not leak internal detail.

## 7. Testing

- New behavior ships with tests in the matching folder under
  [`/tests`](../tests) (unit / integration / e2e / security).
- Tests are deterministic and independent; no reliance on external services in
  unit tests (use fixtures in `tests/fixtures`).

## 8. Commits & reviews

- [Conventional Commits](https://www.conventionalcommits.org/) are mandatory.
- Every change goes through a PR with green CI and CODEOWNER approval.
- Keep diffs additive and focused.

## 9. Dependencies

- Prefer the standard library and existing `packages/` before adding a
  dependency.
- New dependencies must pass dependency and secret scanning in CI.
- Pin versions; review transitive risk.
