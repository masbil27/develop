"""Provider transkripsi lewat OpenRouter (chat completions dengan input audio).

OpenRouter kompatibel dengan format OpenAI chat completions. Untuk model yang
mendukung audio (mis. openai/gpt-4o-audio-preview), audio dikirim sebagai
content block bertipe "input_audio" berisi data base64.

Catatan: dukungan audio di OpenRouter bergantung pada model yang dipilih
(OPENROUTER_MODEL). Cek https://openrouter.ai/models untuk model yang
mendukung modality audio->text sebelum dipakai produksi.
"""
import base64
import time
from pathlib import Path

import requests

from .base import TranscriptionError, TranscriptionProvider

API_URL = "https://openrouter.ai/api/v1/chat/completions"

_LANGUAGE_HINTS = {
    "id": "Bahasa Indonesia",
    "en": "English",
    "mixed": "campuran Bahasa Indonesia dan Inggris (code-switching)",
}

_PROMPT_TEMPLATE = (
    "Transkripsikan audio berikut secara verbatim dan sepresisi mungkin. "
    "Bahasa yang digunakan kemungkinan {language}. "
    "Aturan:\n"
    "1. Tulis persis apa yang diucapkan, jangan meringkas atau menerjemahkan.\n"
    "2. Gunakan tanda baca yang wajar (titik, koma, tanda tanya).\n"
    "3. Jangan tambahkan komentar, judul, atau catatan apa pun selain teks transkrip.\n"
    "4. Jika ada bagian yang tidak jelas terdengar, tandai dengan [tidak jelas].\n"
    "Keluarkan HANYA teks transkripnya."
)


class OpenRouterProvider(TranscriptionProvider):
    def __init__(self, api_key: str, model: str, timeout: int = 300, max_retries: int = 2):
        if not api_key:
            raise TranscriptionError(
                "OPENROUTER_API_KEY belum diisi. Isi di file .env (jangan commit ke git)."
            )
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    def transcribe_chunk(self, wav_path: Path, language_hint: str) -> str:
        audio_b64 = base64.b64encode(wav_path.read_bytes()).decode("ascii")
        language = _LANGUAGE_HINTS.get(language_hint, language_hint)
        payload = {
            "model": self.model,
            "modalities": ["text"],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _PROMPT_TEMPLATE.format(language=language)},
                        {
                            "type": "input_audio",
                            "input_audio": {"data": audio_b64, "format": "wav"},
                        },
                    ],
                }
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.post(API_URL, json=payload, headers=headers, timeout=self.timeout)
            except requests.RequestException as exc:
                last_error = str(exc)
                time.sleep(2 * attempt)
                continue

            if resp.status_code == 200:
                data = resp.json()
                try:
                    return data["choices"][0]["message"]["content"].strip()
                except (KeyError, IndexError) as exc:
                    raise TranscriptionError(
                        f"Respons OpenRouter tidak sesuai format yang diharapkan: {data}"
                    ) from exc

            if resp.status_code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                last_error = f"HTTP {resp.status_code}: {resp.text[:500]}"
                time.sleep(2 * attempt)
                continue

            raise TranscriptionError(
                f"OpenRouter mengembalikan error HTTP {resp.status_code}: {resp.text[:1000]}\n"
                "Jika error menyebut model tidak mendukung audio, ganti OPENROUTER_MODEL "
                "di .env dengan model yang mendukung input audio, atau pakai "
                "TRANSCRIPTION_PROVIDER=openai sebagai alternatif."
            )

        raise TranscriptionError(f"Gagal menghubungi OpenRouter setelah beberapa percobaan: {last_error}")
