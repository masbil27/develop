"""Unduh audio dari link YouTube (video biasa maupun live) memakai yt-dlp.

Catatan pemakaian: hanya untuk keperluan internal/dinas (mis. mengarsipkan
webinar atau rapat daring yang disiarkan lewat YouTube). Pastikan penggunaan
mengikuti Terms of Service YouTube dan hak cipta konten yang diunduh.
"""
from pathlib import Path
from typing import Optional

from yt_dlp import YoutubeDL


class YoutubeDownloadError(RuntimeError):
    pass


def download_audio(url: str, out_dir: Path, max_duration_seconds: Optional[int] = None) -> Path:
    """Unduh trek audio terbaik dari URL YouTube. Mengembalikan path file hasil unduhan.

    Untuk siaran live, `max_duration_seconds` (opsional) membatasi berapa lama
    stream direkam sebelum berhenti otomatis (best-effort, tergantung dukungan
    yt-dlp/ffmpeg untuk stream yang bersangkutan).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    outtmpl = str(out_dir / "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
    }
    if max_duration_seconds:
        # Best-effort: minta ffmpeg (kalau dipakai sebagai downloader HLS/live) berhenti setelah durasi ini.
        ydl_opts["downloader_args"] = {"ffmpeg_i": ["-t", str(max_duration_seconds)]}

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
    except Exception as exc:  # yt-dlp melempar banyak jenis exception berbeda
        raise YoutubeDownloadError(f"Gagal mengunduh audio dari '{url}': {exc}") from exc

    result_path = Path(filename)
    if not result_path.exists():
        raise YoutubeDownloadError(
            f"yt-dlp melaporkan sukses tapi file hasil tidak ditemukan: {filename}"
        )
    return result_path
