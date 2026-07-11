# Workflows

Automation and orchestration definitions owned by the (future) Workflow Engine.
**Milestone 0: structure only — no workflows are defined or executed.**

## Intent

- Declarative workflow specs (versioned) live here.
- The Workflow Engine ([architecture](../docs/ARCHITECTURE.md)) executes them.
- External automation surfaces (e.g. n8n) are integrated in a later milestone
  and are **not** implemented now.

## Rules

- Workflows contain orchestration, not transport — adapters stay logic-free.
- Automated steps run within explicit tool permission boundaries
  ([SECURITY.md](../docs/SECURITY.md)).
