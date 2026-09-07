"""Provider transkripsi lewat OpenAI Audio Transcriptions API (Whisper / gpt-4o-transcribe).

Endpoint resmi ini dibuat khusus untuk speech-to-text, jadi umumnya lebih
matang & presisi dibanding audio lewat chat completions. Dipakai sebagai
alternatif kalau OpenRouter tidak memadai.
"""
import time
from pathlib import Path

import requests

from .base import TranscriptionError, TranscriptionProvider

API_URL = "https://api.openai.com/v1/audio/transcriptions"

_LANGUAGE_ISO = {"id": "id", "en": "en", "mixed": None}


class OpenAIProvider(TranscriptionProvider):
    def __init__(self, api_key: str, model: str = "whisper-1", timeout: int = 300, max_retries: int = 2):
        if not api_key:
            raise TranscriptionError(
                "OPENAI_API_KEY belum diisi. Isi di file .env (jangan commit ke git)."
            )
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    def transcribe_chunk(self, wav_path: Path, language_hint: str) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {"model": self.model, "response_format": "text"}
        iso_lang = _LANGUAGE_ISO.get(language_hint)
        if iso_lang:
            data["language"] = iso_lang

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            with wav_path.open("rb") as f:
                files = {"file": (wav_path.name, f, "audio/wav")}
                try:
                    resp = requests.post(
                        API_URL, headers=headers, data=data, files=files, timeout=self.timeout
                    )
                except requests.RequestException as exc:
                    last_error = str(exc)
                    time.sleep(2 * attempt)
                    continue

            if resp.status_code == 200:
                return resp.text.strip()

            if resp.status_code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                last_error = f"HTTP {resp.status_code}: {resp.text[:500]}"
                time.sleep(2 * attempt)
                continue

            raise TranscriptionError(
                f"OpenAI mengembalikan error HTTP {resp.status_code}: {resp.text[:1000]}"
            )

        raise TranscriptionError(f"Gagal menghubungi OpenAI setelah beberapa percobaan: {last_error}")
