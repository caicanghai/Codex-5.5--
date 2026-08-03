# Deliverables 10–13: Gateway & Channel Architecture

## Deliverable 10: Gateway Architecture

### Gateway Responsibilities

```
Telegram Webhook ──┐
WhatsApp Webhook ──┤
WeChat Webhook ────┼──> [Gateway] ──> [Signature Verify] ──> [Parse] ──> Queue Stage 1
WeCom Webhook ─────┤
iOS Webhook ───────┤
                   │
                   └──> Return 200 OK immediately (async)
```

**Gateway = FastAPI service listening on `/webhook/*` endpoints.**

- **Endpoint**: `https://your-domain/webhook/{channel}` (Telegram, WhatsApp, WeChat, WeCom, iOS).
- **Responsibilities**:
  1. Receive webhook POST.
  2. Verify signature (crypto handshake specific to platform).
  3. Parse inbound message (extract sender, text, media, timestamp).
  4. Build `ChannelEnvelope` (internal message format).
  5. Extract or infer `user_id` via ChannelBinding lookup.
  6. Enqueue to Redis Stage 1 queue.
  7. Return 200 OK to caller (acknowledgement).

### Gateway Implementation

```python
# File: services/gateway/app/routes.py

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    payload = await request.json()
    if not verify_telegram_signature(payload, settings.telegram_bot_token):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    envelope = parse_telegram_message(payload)
    user_id = lookup_user_binding(envelope.channel, envelope.sender_handle)
    
    await queue.enqueue(
        stage="collect",
        tenant_id=user_id.tenant_id,
        task_id=uuid4(),
        payload=envelope.dict()
    )
    return {"ok": True}

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    payload = await request.json()
    if not verify_whatsapp_signature(payload, settings.whatsapp_app_secret):
        raise HTTPException(status_code=403)
    
    envelope = parse_whatsapp_message(payload)
    user_id = lookup_user_binding("whatsapp", envelope.sender_handle)
    
    await queue.enqueue(
        stage="collect",
        tenant_id=user_id.tenant_id,
        task_id=uuid4(),
        payload=envelope.dict()
    )
    return {"ok": True}

# ... similar for WeChat, WeCom, iOS
```

### Signature Verification `[VERIFIED principle]`

Each platform has its own crypto:
- **Telegram**: SHA256 HMAC.
- **WhatsApp**: HMAC SHA256 (X-Hub-Signature header).
- **WeChat**: SHA1 HMAC (signature parameter in query string).
- **WeCom**: SHA256 HMAC with CorpID + Token.
- **iOS APNs**: JWT token (Bearer header).

All verifications happen before message is processed.

### Rate Limiting

**Gateway-level rate limiting** (edge, via reverse proxy):
- Per IP: 100 req/s.
- Per tenant: 1000 req/min.
- Per user: 100 req/min.

Failed verification returns 429 (Too Many Requests) after limit exceeded.

---

## Deliverable 11: Provider Interface

### Provider Abstraction (Backend Pluggability)

```python
# File: packages/providers/ai_provider.py

class AIProvider(ABC):
    """Interface for LLM-based extraction, summarization, embedding."""
    
    @abstractmethod
    async def extract_claims(self, document: Document) -> List[Claim]:
        """Extract claims from a document."""
        pass
    
    @abstractmethod
    async def summarize(self, text: str, max_words: int = 100) -> str:
        """Summarize text."""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding vector."""
        pass

# Implementations:
class OpenRouterAIProvider(AIProvider): ...
class AnthropicAIProvider(AIProvider): ...
class OfflineAIProvider(AIProvider): ...  # Extractive fallback

# Factory:
def get_ai_provider(config: AIConfig) -> AIProvider:
    if config.ai_api_key:
        return OpenRouterAIProvider(config)
    return OfflineAIProvider()  # Free fallback
```

### Provider Types

1. **AIProvider** — LLM extraction, summarization, embedding.
2. **TTSProvider** — Text-to-speech (Fish Audio, ElevenLabs, Edge).
3. **SearchProvider** — Web search (Google, Bing, DuckDuckGo).
4. **StorageProvider** — Object storage (MinIO, S3, GCS).
5. **NotificationProvider** — APNs, FCM, WeCom push.
6. **AuthenticationProvider** — OIDC, email+passkey, social login.
7. **MessagingProvider** — (See ChannelAdapter below.)

### Key Principle

**No service imports external SDKs directly.** All external integrations go through provider interfaces. This allows:
- ✅ Pluggable implementations (swap OpenRouter for local Ollama).
- ✅ Mock providers for testing.
- ✅ Graceful fallbacks (if AI provider down, use offline summary).
- ✅ Cost tracking per provider.

---

## Deliverable 12: Plugin Architecture

### Plugin SDK

```python
# File: packages/plugins/plugin_base.py

class StagePlugin(ABC):
    """Extend or replace a pipeline stage."""
    
    @abstractmethod
    async def process(self, task: Task) -> Result:
        pass

class ProviderPlugin(ABC):
    """Extend or replace a provider."""
    
    @abstractmethod
    def get_provider(self, config: Config) -> Provider:
        pass

class ChannelPlugin(ABC):
    """Add a new channel (e.g., Signal, Discord)."""
    
    @abstractmethod
    def get_adapter(self) -> ChannelAdapter:
        pass

# Loader:
def load_plugins(plugin_dir: str) -> List[Plugin]:
    """Dynamically load .py or .whl plugins from directory."""
    plugins = []
    for file in Path(plugin_dir).glob("*.py"):
        spec = importlib.util.spec_from_file_location(file.stem, file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "plugin"):
            plugins.append(module.plugin)
    return plugins
```

### Plugin Registration

Plugins declare themselves via a `plugin.yaml` manifest:

```yaml
name: custom-claim-extractor
version: 1.0
type: stage
stage: extract
description: "Custom claim extractor for domain-specific facts"
requires:
  - ai_api_key
```

Workers load plugins at startup; plugins can hook into stages before/after standard logic.

---

## Deliverable 13: Channel Adapter (One Interface, Multiple Implementations)

### ChannelAdapter Interface

```python
# File: packages/channels/channel_adapter.py

class ChannelEnvelope:
    """Internal message format (Deliverable 3: Internal Message Envelope)."""
    
    channel: str                    # telegram, whatsapp, wechat, wecom, ios
    sender_id: UUID
    sender_handle: str              # @username, phone, wechat_id, wecom_userid
    text: str
    media_urls: List[str]           # Optional images, audio, video
    received_at: datetime
    raw_payload: dict               # Platform-specific data
    tenant_id: UUID                 # Isolation key

class ChannelAdapter(ABC):
    """Send/receive messages via a specific platform."""
    
    @abstractmethod
    async def send(self, user_handle: str, message_text: str, 
                   voice_url: Optional[str] = None) -> DeliveryStatus:
        """Send message (text + optional voice) to user on this channel."""
        pass
    
    @abstractmethod
    async def verify_signature(self, request: Request) -> bool:
        """Verify webhook signature."""
        pass

# Implementations:
class TelegramAdapter(ChannelAdapter):
    async def send(self, user_handle: str, message_text: str, 
                   voice_url: Optional[str] = None) -> DeliveryStatus:
        # Call Telegram Bot API
        # If voice_url: also send voice message
        pass

class WhatsAppAdapter(ChannelAdapter): ...
class WeChatAdapter(ChannelAdapter): ...
class WeCom Adapter(ChannelAdapter): ...
class iOSAdapter(ChannelAdapter): ...  # APNs

# Factory:
def get_channel_adapter(channel: str, config: Config) -> ChannelAdapter:
    adapters = {
        "telegram": TelegramAdapter(config),
        "whatsapp": WhatsAppAdapter(config),
        "wechat": WeChatAdapter(config),
        "wecom": WeComAdapter(config),
        "ios": iOSAdapter(config),
    }
    return adapters[channel]
```

### Broadcast Worker Uses Adapters

```python
# In worker: services/worker/app/stages/broadcast.py

async def broadcast_stage(task: Task):
    user_id, channel = task.payload["user_id"], task.payload["channel"]
    envelope = task.payload["message"]
    
    adapter = get_channel_adapter(channel, settings)
    status = await adapter.send(
        user_handle=envelope.sender_handle,
        message_text=envelope.text,
        voice_url=envelope.voice_url
    )
    
    update_delivery_status(delivery_id, status)
```

### Key Properties

- ✅ **One interface** — All channels (Telegram, WhatsApp, WeChat, WeCom, iOS) implement `ChannelAdapter`.
- ✅ **Stateless** — No channel-specific state in workers; all config from environment.
- ✅ **Async I/O** — All send operations are non-blocking.
- ✅ **Tenant-aware** — Each adapter receives `tenant_id` in config (for multi-tenant channels like WeCom).
- ✅ **Pluggable** — New channel = new adapter implementation; no changes to worker code.
