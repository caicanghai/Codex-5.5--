"""Prompt module — EIOS no longer carries its own AI persona prompts.

The persona / "brain" prompts have been intentionally removed so that the
upstream model (e.g. Kimi) owns the persona. EIOS just relays messages and
converts voice; whatever assistant personality you want is defined on the
model side (or via the optional env overrides below).

Nothing here is a baked-in persona anymore:
  * CHAT_SYSTEM_PROMPT / SUMMARY_SYSTEM_PROMPT default to EMPTY. If empty, EIOS
    sends no system message at all and lets the upstream model decide.
  * You may still set a persona without code changes via env:
        EIOS_CHAT_SYSTEM_PROMPT=...    EIOS_SUMMARY_SYSTEM_PROMPT=...
  * summary_user_prompt() is a functional task instruction (not a persona),
    kept so URL/RSS summarization still works.
  * The FALLBACK_* lines are what EIOS says when there is NO AI available —
    they keep it from going silent, and are not model prompts.
"""

from __future__ import annotations

import os

# --- AI persona prompts: removed; empty unless overridden by env ----------
CHAT_SYSTEM_PROMPT = os.getenv("EIOS_CHAT_SYSTEM_PROMPT", "")
SUMMARY_SYSTEM_PROMPT = os.getenv("EIOS_SUMMARY_SYSTEM_PROMPT", "")


# --- Functional summarization instruction (not a persona) -----------------
def summary_user_prompt(text: str, max_sentences: int, max_chars: int = 8000) -> str:
    """Build the per-article summarization instruction."""
    return (
        f"Summarize the following article in at most {max_sentences} clear sentences. "
        "Be factual and concise.\n\n" + text[:max_chars]
    )


# --- User-facing fallback lines (no AI available; not model prompts) ------
FALLBACK_AI_UNAVAILABLE = "EIOS online. AI provider is temporarily unavailable."
FALLBACK_NO_KEY_PREFIX = "EIOS online. 收到："  # + the echoed user text
FALLBACK_EMPTY_MESSAGE = "（空消息）"
