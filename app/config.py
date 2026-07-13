"""Runtime configuration, loaded from environment variables."""

from __future__ import annotations

from pydantic import AliasChoices, Field
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
    # Accepts AI_API_KEY or OPENAI_API_KEY.
    ai_api_key: str = Field(
        default="", validation_alias=AliasChoices("AI_API_KEY", "OPENAI_API_KEY")
    )
    ai_base_url: str = Field(
        default="https://api.openai.com/v1",
        validation_alias=AliasChoices("AI_BASE_URL", "OPENAI_BASE_URL"),
    )
    ai_model: str = "gpt-4o-mini"

    # TTS (Edge fallback voice)
    tts_voice: str = "en-US-AriaNeural"

    # Owner-only voice controls
    telegram_owner_id: int = 0
    tts_provider: str = "fish"

    # Fish Audio (primary voice-clone provider)
    fish_audio_api_key: str = ""
    fish_audio_base_url: str = "https://api.fish.audio"
    fish_audio_voice_id: str = ""

    # ElevenLabs (fallback)
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    elevenlabs_model_id: str = "eleven_multilingual_v2"

    # Voice sample constraints
    voice_min_duration_seconds: int = 15
    voice_max_duration_seconds: int = 90
    voice_max_upload_mb: int = 20
    voice_sample_retention: bool = False

    # Limits
    summary_sentences: int = 5
    tts_max_chars: int = 1800
    fetch_timeout_seconds: float = 20.0


settings = Settings()
