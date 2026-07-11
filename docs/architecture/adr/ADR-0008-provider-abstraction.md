# ADR-0008 · Provider abstraction for all external services

- **Status:** Accepted
- **Context:** The mission requires every external service to be abstracted with
  no provider-specific business logic in the core (Model, TTS, Storage, Search,
  Embedding, Notification, Authentication).
- **Decision:** Define a stable interface per provider category in
  `packages/providers/*`. Vendor SDKs live only in that provider's adapter. A
  `ProviderResolver` selects the concrete implementation per tenant/user from
  `provider_bindings`, with a safe platform default. Calls go through a
  resilience wrapper (timeout/retry/circuit-breaker) and cost/rate metering.
- **Consequences:** Vendors are swappable per tenant without core changes;
  credentials stay per-tenant (`credentials_ref`, never shared). Requires
  disciplined interface design so capabilities aren't leaked vendor-specifically.
