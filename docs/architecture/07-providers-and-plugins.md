# Deliverable 7 (Reference): Providers & Plugins Summary

See `05-queues-and-workers.md` and `06-gateway-and-channels.md` for detailed provider and plugin architecture.

## Provider Types (Quick Reference)

1. **AIProvider** — LLM extraction, summarization, embedding (free: OpenRouter/Ollama; premium: Claude, GPT-4).
2. **TTSProvider** — Voice synthesis (Fish Audio, ElevenLabs, Edge TTS).
3. **SearchProvider** — Web search (Google, DuckDuckGo).
4. **StorageProvider** — MinIO, S3, GCS.
5. **NotificationProvider** — APNs (iOS push), FCM (Android).
6. **AuthenticationProvider** — OIDC, email+passkey.
7. **ChannelAdapter** — Telegram, WhatsApp, WeChat, WeCom, iOS (see Deliverable 13).

## Plugin SDK

Extensibility via `packages/plugins/`:
- **StagePlugin** — Extend/replace pipeline stages.
- **ProviderPlugin** — Add/override providers.
- **ChannelPlugin** — Add new channels.

Dynamic loading from `plugins/` directory at runtime.

---

**See detailed sections in previous files for architecture specifics.**
