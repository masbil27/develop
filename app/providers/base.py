from abc import ABC, abstractmethod
from pathlib import Path


class TranscriptionError(RuntimeError):
    pass


class TranscriptionProvider(ABC):
    @abstractmethod
    def transcribe_chunk(self, wav_path: Path, language_hint: str) -> str:
        """Transkripsi satu file WAV pendek (hasil chunking) menjadi teks."""
        raise NotImplementedError
