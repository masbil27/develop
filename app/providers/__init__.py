import os

from .. import config_store
from .base import TranscriptionError, TranscriptionProvider
from .openai_provider import OpenAIProvider
from .openrouter import OpenRouterProvider

__all__ = ["TranscriptionError", "TranscriptionProvider", "get_provider"]


def _pick(config_value: str, env_key: str, default: str = "") -> str:
    """Config.json (diisi lewat halaman Pengaturan) diprioritaskan; .env/env var jadi fallback."""
    if config_value:
        return config_value
    return os.environ.get(env_key, default)


def get_provider() -> TranscriptionProvider:
    config = config_store.load_config()
    name = _pick(config.get("provider", ""), "TRANSCRIPTION_PROVIDER", "openrouter").strip().lower()

    if name == "openrouter":
        return OpenRouterProvider(
            api_key=_pick(config.get("openrouter_api_key", ""), "OPENROUTER_API_KEY"),
            model=_pick(config.get("openrouter_model", ""), "OPENROUTER_MODEL", "openai/gpt-4o-audio-preview"),
        )
    if name == "openai":
        return OpenAIProvider(
            api_key=_pick(config.get("openai_api_key", ""), "OPENAI_API_KEY"),
            model=_pick(config.get("openai_model", ""), "OPENAI_TRANSCRIBE_MODEL", "whisper-1"),
        )
    raise TranscriptionError(
        f"Provider '{name}' tidak dikenal. Pakai 'openrouter' atau 'openai' di halaman Pengaturan."
    )
