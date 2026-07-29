"""Summarization: AI (OpenAI-compatible) with an offline extractive fallback."""

from __future__ import annotations

import re
from collections import Counter

import httpx

from app.config import settings
from app.prompts import SUMMARY_SYSTEM_PROMPT, summary_user_prompt

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[A-Za-z0-9']+")
_STOP = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "been", "as", "at", "by", "it", "its",
    "this", "that", "these", "those", "from", "has", "have", "had", "not", "he",
    "she", "they", "we", "you", "i", "his", "her", "their", "our", "your", "will",
    "would", "can", "could", "should", "may", "might", "do", "does", "did", "so",
}


def extractive_summary(text: str, max_sentences: int) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    sentences = [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]
    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    freq: Counter[str] = Counter()
    for sent in sentences:
        for word in _WORD.findall(sent.lower()):
            if word not in _STOP and len(word) > 2:
                freq[word] += 1
    if not freq:
        return " ".join(sentences[:max_sentences])

    scored: list[tuple[int, float]] = []
    for idx, sent in enumerate(sentences):
        words = [w for w in _WORD.findall(sent.lower()) if w not in _STOP]
        if not words:
            continue
        score = sum(freq[w] for w in words) / len(words)
        scored.append((idx, score))

    top = sorted(scored, key=lambda x: x[1], reverse=True)[:max_sentences]
    chosen = sorted(i for i, _ in top)
    return " ".join(sentences[i] for i in chosen)


async def _ai_summary(text: str) -> str:
    prompt = summary_user_prompt(text, settings.summary_sentences)
    messages = []
    if SUMMARY_SYSTEM_PROMPT:  # persona removed by default; only sent if configured
        messages.append({"role": "system", "content": SUMMARY_SYSTEM_PROMPT})
    messages.append({"role": "user", "content": prompt})
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.ai_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.ai_api_key}"},
            json={
                "model": settings.ai_model,
                "messages": messages,
                "temperature": 0.3,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


async def summarize(text: str) -> str:
    """Return a summary. Uses AI if configured, else extractive fallback."""
    text = (text or "").strip()
    if not text:
        return "No readable content was found at that link."

    if settings.ai_api_key:
        try:
            summary = await _ai_summary(text)
            if summary:
                return summary
        except Exception:
            # Fall through to the offline summarizer — never fail the pipeline.
            pass

    return extractive_summary(text, settings.summary_sentences)
