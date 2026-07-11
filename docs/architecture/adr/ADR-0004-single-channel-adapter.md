# ADR-0004 · One ChannelAdapter interface for all platforms

- **Status:** Accepted
- **Context:** The mission mandates that every communication platform implement
  exactly the same interface, with no business logic inside adapters.
- **Decision:** A single `ChannelAdapter` interface in `packages/channels/base`
  (`verify`, `parse`, `can_send`, `send`, `register`, `healthcheck`). Every
  platform provides a transport-only implementation. Capability differences are
  expressed via `can_send`/capability flags, never business branching.
- **Consequences:** New channels = new adapter, no core changes. Enforces the
  "adapters are transport-only" rule structurally. Capability negotiation must be
  designed carefully (e.g. WhatsApp templates, voice notes).
