# ADR-0002: Backend Language & Framework (Python/FastAPI)

**Status**: ADOPTED (locked this session)  
**Date**: 2026-08-03  
**Context**: EIOS is a multi-service platform requiring async I/O, rapid iteration, and a mature ML/NLP ecosystem.

## Decision

**Use Python with FastAPI for all backend services** (gateway, api, worker, scheduler).  
**Use TypeScript only for web-admin dashboard** (React/Next.js).  
**Use Swift for iOS app** (separate repository).

## Rationale

- **Python** — Mature ML/NLP ecosystem (spaCy, transformers, scikit-learn); strong async support (asyncio, httpx); production-ready frameworks (FastAPI).
- **FastAPI** — Modern async framework; automatic OpenAPI schema generation; fast (Uvicorn + Starlette); great type hints + Pydantic validation.
- **Consistency** — All backend services speak the same language; easier hiring, code review, shared patterns.
- **TS for web-admin only** — UI framework of choice; no backend in web-admin (all queries via `/api/v1`).
- **Swift for iOS** — Apple's native language; best performance and ecosystem support.

## Tradeoff

- **Performance** — Python is slower than Go/Rust; mitigated by async I/O and caching (Redis).
- **Cold starts** — Serverless deployment would be slow; but VPS deployment masks this.
- **Typing** — Python typing is opt-in (Pydantic enforces at boundaries; mypy for static checks).

## Tooling

- **Linting**: ruff (fast, Rust-based).
- **Formatting**: black.
- **Type checking**: mypy.
- **Testing**: pytest.
- **Package manager**: Poetry or uv (for deterministic builds).

## Alternatives Considered

- **Go** — Fast, good concurrency; rejected due to lack of mature ML/NLP ecosystem.
- **Rust** — Safest; rejected due to learning curve and slower iteration.
- **Node.js** — Mature async; rejected due to weaker type system and ML support.

## References

- `docs/CODING_RULES.md` — Python style guide, ruff/black/mypy config.
- `services/*/pyproject.toml` — Per-service dependencies.
