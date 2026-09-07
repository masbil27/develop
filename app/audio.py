"""Ekstraksi & pemotongan audio pakai ffmpeg (harus terpasang di sistem)."""
import json
import shutil
import subprocess
from pathlib import Path


class FfmpegNotFoundError(RuntimeError):
    pass


class AudioProcessingError(RuntimeError):
    pass


def _require_ffmpeg(binary: str = "ffmpeg") -> None:
    if shutil.which(binary) is None:
        raise FfmpegNotFoundError(
            f"'{binary}' tidak ditemukan di PATH. Install dulu, mis. `apt install ffmpeg` "
            "atau `brew install ffmpeg`, lalu jalankan ulang."
        )


def to_wav(input_path: Path, output_path: Path, sample_rate: int = 16000) -> Path:
    """Konversi file audio/video apa pun menjadi WAV mono 16kHz (format standar untuk ASR)."""
    _require_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vn", "-ac", "1", "-ar", str(sample_rate),
        "-f", "wav", str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise AudioProcessingError(
            f"Gagal mengekstrak audio dari '{input_path.name}'. Detail ffmpeg:\n{result.stderr[-2000:]}"
        )
    return output_path


def get_duration_seconds(path: Path) -> float:
    _require_ffmpeg("ffprobe")
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise AudioProcessingError(f"Gagal membaca durasi '{path.name}': {result.stderr[-500:]}")
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def split_into_chunks(wav_path: Path, out_dir: Path, chunk_seconds: int = 300) -> list[Path]:
    """Pecah file WAV panjang menjadi beberapa chunk agar aman dikirim ke API transkripsi."""
    _require_ffmpeg()
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = out_dir / "chunk_%04d.wav"
    cmd = [
        "ffmpeg", "-y", "-i", str(wav_path),
        "-f", "segment", "-segment_time", str(chunk_seconds),
        "-c", "copy", str(pattern),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise AudioProcessingError(f"Gagal memotong audio: {result.stderr[-2000:]}")
    chunks = sorted(out_dir.glob("chunk_*.wav"))
    if not chunks:
        raise AudioProcessingError("Tidak ada chunk audio yang dihasilkan.")
    return chunks
