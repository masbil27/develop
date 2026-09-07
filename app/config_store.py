"""Penyimpanan konfigurasi lokal (config.json) supaya user bisa isi API key
lewat halaman web, tanpa perlu edit file .env secara manual."""
import json
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

DEFAULTS: dict[str, Any] = {
    "provider": "openrouter",
    "openrouter_api_key": "",
    "openrouter_model": "openai/gpt-4o-audio-preview",
    "openai_api_key": "",
    "openai_model": "whisper-1",
    "language_hint": "mixed",
}


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return dict(DEFAULTS)
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)
    merged = dict(DEFAULTS)
    merged.update({k: v for k, v in data.items() if k in DEFAULTS})
    return merged


def save_config(data: dict[str, Any]) -> None:
    current = load_config()
    current.update({k: v for k, v in data.items() if k in DEFAULTS})
    CONFIG_PATH.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")


def is_configured(config: dict[str, Any]) -> bool:
    if config["provider"] == "openrouter":
        return bool(config.get("openrouter_api_key"))
    if config["provider"] == "openai":
        return bool(config.get("openai_api_key"))
    return False
