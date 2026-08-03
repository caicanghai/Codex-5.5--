# Architecture

Design artifacts for EIOS. The narrative architecture lives in
[`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md); this directory holds
supporting diagrams and per-layer design notes as the system grows.

## Layout

- `diagrams/` — source and exported diagrams (topology, sequence, data flow).
- `decisions/` — links back to ADRs in [`../docs/DECISIONS.md`](../docs/DECISIONS.md).

## Target layers

1. Unified Channel Gateway
2. Identity Layer
3. Evidence Intelligence Engine
4. Interest Catalog Engine
5. Workflow Engine
6. Broadcast Engine
7. TTS Gateway
8. Channel Adapters (transport-only)

> Milestone 0: structure only. No layer is implemented.
