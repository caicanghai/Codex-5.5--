# Contributing to EIOS

Thank you for contributing. This document defines the branching model, commit
conventions, and review process. Code standards live in
[`CODING_RULES.md`](./CODING_RULES.md).

---

## Branching model

EIOS layers on top of an upstream base and flows changes strictly downward
through Pull Requests:

```
mirror/openclaw     ← tracks upstream verbatim; never hand-edited
      │  (sync PRs only)
      ▼
eios/main           ← protected; product mainline; PRs only
      │
      ▼
develop             ← integration branch for the next release
      │
      ▼
feature/*           ← one branch per unit of work
```

Rules:

- **Never commit directly to `eios/main`.** All changes arrive via PR.
- **Never modify upstream in place.** Upstream updates land on `mirror/openclaw`
  and are merged forward through a sync PR.
- `feature/*` branches off `develop`; when complete it is PR'd back into
  `develop`. Releases promote `develop` → `eios/main`.
- Keep changes **additive**. Do not remove existing functionality.

> **Automation note:** In this managed environment, foundation work is committed
> on the designated working branch and promoted through PRs. The protected
> branch names above are the target model; branch-protection settings are
> described under "Branch protection" below and applied by a maintainer with
> repository admin rights.

## Conventional Commits

All commits follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional scope>): <description>

[optional body]

[optional footer(s)]
```

Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`,
`build`, `ci`, `chore`, `revert`.

Examples:

- `docs(charter): add project charter`
- `chore(repo): scaffold milestone 0 foundation`
- `ci(actions): add lint and type-check jobs`

Commit messages are linted by `commitlint` (see `commitlint.config.cjs`).

## Pull Requests

1. Branch from `develop` using `feature/<short-topic>`.
2. Keep PRs focused and small.
3. Fill in the PR template completely.
4. Ensure CI is green: install, lint, type-check, test, build, docker validation.
5. At least one CODEOWNER approval is required (see
   [`.github/CODEOWNERS`](../.github/CODEOWNERS)).
6. Squash-merge with a Conventional Commit title.

## Branch protection (target configuration)

Maintainers configure these on `eios/main` and `develop`:

- Require PRs before merging; disallow direct pushes.
- Require status checks to pass (the `ci` workflow).
- Require at least one approving review from CODEOWNERS.
- Require branches to be up to date before merging.
- Require signed commits (recommended).
- Restrict force-pushes and deletions.

## Local setup

```bash
npm install            # install workspace tooling
npm run lint           # ESLint
npm run format:check   # Prettier
npm run typecheck      # tsc --noEmit (strict)
npm test               # test runner (placeholder in M0)
npm run build          # workspace build (placeholder in M0)
```

See [`/deployments`](../deployments) for the local Docker topology.

## Code of conduct

Be respectful and constructive. Assume good intent; review the code, not the
person.
