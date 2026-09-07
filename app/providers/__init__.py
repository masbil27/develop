import os

from .base import TranscriptionError, TranscriptionProvider
from .openai_provider import OpenAIProvider
from .openrouter import OpenRouterProvider

__all__ = ["TranscriptionError", "TranscriptionProvider", "get_provider"]


def get_provider() -> TranscriptionProvider:
    name = os.environ.get("TRANSCRIPTION_PROVIDER", "openrouter").strip().lower()
    if name == "openrouter":
        return OpenRouterProvider(
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            model=os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-audio-preview"),
        )
    if name == "openai":
        return OpenAIProvider(
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            model=os.environ.get("OPENAI_TRANSCRIBE_MODEL", "whisper-1"),
        )
    raise TranscriptionError(
        f"TRANSCRIPTION_PROVIDER '{name}' tidak dikenal. Pakai 'openrouter' atau 'openai'."
    )
