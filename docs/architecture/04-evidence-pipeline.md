# Deliverable 7: 12-Stage Evidence Pipeline

## Complete Pipeline Flow

```
Inbound Message (Webhook / API / Upload)
    ↓
[1] Collect — Parse inbound, extract metadata, queue to Stage 2
    ↓
[2] Normalize — Standardize format, language detect, clean text
    ↓
[3] Deduplicate — Check if message/URL already processed; skip if yes
    ↓
[4] Document — Store as Document (title, content, source_url, metadata)
    ↓
[5] Extract — LLM extract claims/facts from document
    ↓
[6] Resolve — Link claims to existing knowledge base; resolve ambiguities
    ↓
[7] Cross-Validate — Check claim against external sources (web search, APIs)
    ↓
[8] Detect Conflicts — Compare against known claims; flag contradictions
    ↓
[9] Score — Assign confidence score (0–1) based on source credibility, conflict count, corroboration
    ↓
[10] Summarize — Generate short summary for broadcast
    ↓
[11] Interest Match — Match evidence against user interests (NLP/ML)
    ↓
[12] Broadcast — Deliver to matched users via Telegram/WhatsApp/WeChat/WeCom + iOS push
```

## Stage Details

### Stage 1: Collect
**Input**: Webhook from Telegram/WhatsApp/WeChat/WeCom, or API POST, or uploaded file.  
**Output**: `RawItem` persisted; metadata extracted (sender, channel, timestamp).  
**Workers**: Gateway (synchronous webhook parsing) + 1–2 Collect workers.  
**Idempotency**: Dedup on `(channel, sender_id, message_hash, received_at)`.  
**Failure mode**: Log error; return 200 OK to caller; push to DLQ.

### Stage 2: Normalize
**Input**: `RawItem`.  
**Output**: Cleaned text, language code, encoding validation.  
**Workers**: 2–3 Normalize workers (I/O light, CPU medium for NLP).  
**Idempotency**: Idempotent (same input → same output).  
**Failure mode**: Retry with exponential backoff; DLQ after N attempts.

### Stage 3: Deduplicate
**Input**: `RawItem` normalized text + source URL.  
**Output**: `Document` link or skip (if already processed).  
**Workers**: 1–2 Dedup workers (query-heavy, cache-friendly).  
**Dedup key**: `(tenant_id, hash(normalized_text), source_url)`.  
**Idempotency**: Idempotent.  
**Failure mode**: Retry + DLQ.

### Stage 4: Document
**Input**: Deduplicated `RawItem`.  
**Output**: `Document` row created; content indexed; metadata stored; object reference created (MinIO).  
**Workers**: 2–3 Document workers (storage I/O).  
**Idempotency**: Idempotent (same raw_item → same document).  
**Failure mode**: Retry + DLQ.

### Stage 5: Extract
**Input**: `Document`.  
**Output**: `Claim` rows (one per extracted fact).  
**Workers**: 3–5 Extract workers (LLM-heavy; call external AI provider).  
**Idempotency**: Idempotent (same document → same claims).  
**Failure mode**: Retry with fallback AI provider (see `app/pipeline/chat.py` multi-level failover); DLQ if all fail.

### Stage 6: Resolve
**Input**: `Claim`.  
**Output**: Link claim to existing knowledge base entries; resolve entity references.  
**Workers**: 2–3 Resolve workers (knowledge base queries).  
**Idempotency**: Idempotent.  
**Failure mode**: Retry + DLQ; graceful degradation (unresolved claims still proceed).

### Stage 7: Cross-Validate
**Input**: `Claim`.  
**Output**: Corroboration signals (did external sources confirm?).  
**Workers**: 2–3 Cross-Validate workers (web search API calls).  
**Idempotency**: Idempotent.  
**Failure mode**: Retry + DLQ; graceful degradation (unvalidated claims still proceed).

### Stage 8: Detect Conflicts
**Input**: `Claim` + resolved knowledge base.  
**Output**: `Conflict` rows if contradiction detected.  
**Workers**: 1–2 Detect Conflict workers (query-heavy).  
**Idempotency**: Idempotent.  
**Failure mode**: Retry + DLQ.

### Stage 9: Score
**Input**: `Claim` + Conflict count + Cross-Validation signals.  
**Output**: Confidence score (0–1); store in `Evidence`.  
**Workers**: 1–2 Score workers (CPU light; ML inference `[ASSUMED]`).  
**Idempotency**: Idempotent.  
**Failure mode**: Retry + DLQ; fallback to heuristic score.

### Stage 10: Summarize
**Input**: `Evidence` (scored claim).  
**Output**: Short summary text (1–3 sentences).  
**Workers**: 2–3 Summarize workers (LLM call).  
**Idempotency**: Idempotent.  
**Failure mode**: Retry with fallback LLM; DLQ if all fail.

### Stage 11: Interest Match
**Input**: `Evidence` (summarized).  
**Output**: List of `(user_id, interest_id)` pairs for broadcast.  
**Workers**: 2–3 Interest Match workers (query + NLP/ML).  
**Idempotency**: Idempotent.  
**Failure mode**: Retry + DLQ; broadcast to all users if matching fails (fallback).

### Stage 12: Broadcast
**Input**: `Evidence` + list of matched users.  
**Output**: `Delivery` rows created (one per user × channel); async send to platforms.  
**Workers**: 3–5 Broadcast workers (networking-heavy; send via ChannelAdapter).  
**Idempotency**: `dedup_key = (broadcast_id, user_id, channel)` ensures one delivery per combination.  
**Failure mode**: Retry with exponential backoff; DLQ after exhausted.

---

## Queue & Worker Topology

```
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│ Collect  │Normalize │Deduplicate│Document │  Extract │
│  Queue   │  Queue   │   Queue   │  Queue  │  Queue   │
│ (2 work) │(2 work)  │ (1 work)  │(3 work) │(3 work)  │
└──────────┴──────────┴──────────┴──────────┴──────────┘
     ↓         ↓          ↓          ↓          ↓
  Worker Pool (scales per queue depth)
```

---

## No Stage Skipping (Verified Principle)

Every message must pass through all 12 stages in order. Even if a stage fails or is skipped in a test, the pipeline resumes from that stage, not after it:

- **Dedup finds existing Document?** → Still run Extract (maybe new claims exist).
- **Extract fails (LLM unavailable)?** → Retry + DLQ; don't skip to Summarize.
- **Interest Match fails?** → Broadcast to all users (fallback); don't skip Broadcast.

This ensures:
- ✅ No evidence is broadcast without being scored.
- ✅ No claim is scored without being cross-validated and conflict-checked.
- ✅ No conflict detection is skipped even if document is old.

---

## Failure Modes & Retry Strategy

| Stage | Failure Mode | Retry | Fallback | DLQ Threshold |
|-------|--------------|-------|----------|---------------|
| Collect | Webhook parse fails | No (return 200 OK) | — | N/A |
| Normalize | Text encoding error | Yes (exp backoff) | Return raw text | 3 attempts |
| Deduplicate | DB query fails | Yes | Assume not duplified | 3 attempts |
| Document | Storage write fails | Yes | Retry object upload | 3 attempts |
| Extract | LLM unavailable | Yes (multi-level failover) | Extractive summary fallback | 3 attempts |
| Resolve | Knowledge base query fails | Yes | Unresolved claim proceeds | 3 attempts |
| Cross-Validate | Web search fails | Yes | No corroboration signals | 3 attempts |
| Detect Conflicts | DB query fails | Yes | No conflict detected | 3 attempts |
| Score | Inference fails | Yes | Heuristic score | 3 attempts |
| Summarize | LLM fails | Yes (multi-level failover) | Extractive summary | 3 attempts |
| Interest Match | Query fails | Yes | Broadcast to all | 3 attempts |
| Broadcast | Send fails | Yes (exp backoff) | — | 5 attempts then exhausted |

---

## Performance & Scaling

| Stage | Throughput (msgs/sec) | Latency (p99) | Worker Count | Scaling Trigger |
|-------|---|---|---|---|
| Collect | 100 | 100ms | 2 | Queue depth > 50 |
| Normalize | 50 | 200ms | 2 | Queue depth > 100 |
| Deduplicate | 30 | 500ms | 1 | Queue depth > 50 |
| Document | 20 | 1s | 3 | Queue depth > 50 |
| Extract | 10 | 5s | 3–5 | Queue depth > 20 (LLM bottleneck) |
| Resolve | 15 | 1s | 2 | Queue depth > 50 |
| Cross-Validate | 12 | 2s | 2 | Queue depth > 30 |
| Detect Conflicts | 25 | 500ms | 1 | Queue depth > 50 |
| Score | 50 | 200ms | 1 | Queue depth > 100 |
| Summarize | 15 | 3s | 2–3 | Queue depth > 30 (LLM bottleneck) |
| Interest Match | 20 | 1s | 2 | Queue depth > 50 |
| Broadcast | 30 | 500ms | 3–5 | Queue depth > 100 |

**Bottlenecks**: Extract and Summarize (LLM-dependent); Cross-Validate (web search).  
**Optimization**: Dedicated worker pools for Extract + Summarize; caching of resolved/validated claims.
