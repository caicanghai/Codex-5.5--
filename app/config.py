"""Runtime configuration, loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Infrastructure
    database_url: str = "postgresql+psycopg2://eios:eios@db:5432/eios"
    redis_url: str = "redis://redis:6379/0"

    # Telegram
    telegram_bot_token: str = ""

    # AI summarization (OpenAI-compatible). If no key, an offline extractive
    # summarizer is used so the pipeline still works end to end.
    ai_api_key: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4o-mini"

    # TTS
    tts_voice: str = "en-US-AriaNeural"

    # Limits
    summary_sentences: int = 5
    tts_max_chars: int = 1800
    fetch_timeout_seconds: float = 20.0


settings = Settings()
