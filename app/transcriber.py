"""Orkestrasi pipeline: file input -> wav -> (chunk) -> transkrip -> gabungan teks."""
import logging
import os
import shutil
import uuid
from pathlib import Path

from . import audio, config_store
from .providers import TranscriptionProvider

logger = logging.getLogger(__name__)


def transcribe_file(input_path: Path, provider: TranscriptionProvider, work_dir: Path) -> str:
    """Transkripsi satu file audio/video lokal menjadi teks penuh."""
    job_dir = work_dir / uuid.uuid4().hex
    job_dir.mkdir(parents=True, exist_ok=True)
    config = config_store.load_config()
    language_hint = config.get("language_hint") or os.environ.get("TRANSCRIPTION_LANGUAGE_HINT", "mixed")
    chunk_seconds = int(os.environ.get("CHUNK_SECONDS", "300"))

    try:
        wav_path = audio.to_wav(input_path, job_dir / "full.wav")
        duration = audio.get_duration_seconds(wav_path)

        if duration <= chunk_seconds:
            chunks = [wav_path]
        else:
            chunks = audio.split_into_chunks(wav_path, job_dir / "chunks", chunk_seconds)

        parts = []
        for i, chunk_path in enumerate(chunks, start=1):
            logger.info("Transcribing chunk %d/%d: %s", i, len(chunks), chunk_path.name)
            text = provider.transcribe_chunk(chunk_path, language_hint)
            parts.append(text)

        return "\n\n".join(p for p in parts if p)
    finally:
        shutil.rmtree(job_dir, ignore_errors=True)
