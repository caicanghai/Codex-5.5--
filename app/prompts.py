"""Prompt module — every LLM prompt EIOS uses, in one place.

Extracted so the prompts can be reviewed, tuned, or reused (e.g. integrated
into another assistant like Kimi) without touching the pipeline logic.

There are only three prompts in EIOS:
  1. CHAT_SYSTEM_PROMPT     — persona for free-form chat replies
  2. SUMMARY_SYSTEM_PROMPT  — persona for article summarization
  3. summary_user_prompt()  — the per-article summarization instruction

The user-facing fallback lines (used when the AI is unavailable) live here too
so all model-facing / assistant-voice text is in a single file.
"""

from __future__ import annotations

# --- 1. Chat persona (app/pipeline/chat.py) -------------------------------
CHAT_SYSTEM_PROMPT = "You are EIOS, a concise, friendly personal assistant. Reply briefly."

# --- 2. Summarizer persona (app/pipeline/summarize.py) --------------------
SUMMARY_SYSTEM_PROMPT = "You are a concise news summarizer."


# --- 3. Summarization instruction ----------------------------------------
def summary_user_prompt(text: str, max_sentences: int, max_chars: int = 8000) -> str:
    """Build the per-article summarization instruction."""
    return (
        f"Summarize the following article in at most {max_sentences} clear sentences. "
        "Be factual and concise.\n\n" + text[:max_chars]
    )


# --- User-facing fallback lines (no AI available) ------------------------
FALLBACK_AI_UNAVAILABLE = "EIOS online. AI provider is temporarily unavailable."
FALLBACK_NO_KEY_PREFIX = "EIOS online. 收到："  # + the echoed user text
FALLBACK_EMPTY_MESSAGE = "（空消息）"
