# ADR-0003 · Internal message Envelope as the channel contract

- **Status:** Accepted
- **Context:** Many channels (Telegram, WhatsApp, WeChat, WeCom, APNs, future
  Android) with different payloads must feed one pipeline without leaking
  platform specifics inward.
- **Decision:** All inbound/outbound messages normalize to a single **versioned
  Envelope** owned by `packages/contracts` (conceptually defined in
  `schemas/envelope/`). Adapters and pipeline stages depend only on the Envelope.
- **Consequences:** Channels become swappable; breaking Envelope changes bump the
  major version and require an ADR. Slightly more mapping code per adapter, paid
  back by a stable internal contract.
