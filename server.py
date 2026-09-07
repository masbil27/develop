import logging
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, render_template, request, send_file

load_dotenv()

from app.providers import TranscriptionError, get_provider  # noqa: E402
from app.transcriber import transcribe_file  # noqa: E402
from app.youtube import YoutubeDownloadError, download_audio  # noqa: E402
from app.audio import AudioProcessingError, FfmpegNotFoundError  # noqa: E402

logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
WORK_DIR = BASE_DIR / "uploads" / "_work"
RESULT_DIR = BASE_DIR / "uploads" / "_results"
for d in (UPLOAD_DIR, WORK_DIR, RESULT_DIR):
    d.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus",
    ".mp4", ".mov", ".mkv", ".webm", ".avi",
}
MAX_CONTENT_LENGTH_MB = int(os.environ.get("MAX_CONTENT_LENGTH_MB", "1024"))

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "app" / "templates"),
    static_folder=str(BASE_DIR / "app" / "static"),
)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH_MB * 1024 * 1024


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/transcribe", methods=["POST"])
def transcribe():
    source = request.form.get("source", "file")
    job_id = uuid.uuid4().hex
    input_path = None

    try:
        if source == "youtube":
            youtube_url = (request.form.get("youtube_url") or "").strip()
            if not youtube_url:
                return render_template("index.html", error="Link YouTube belum diisi.")
            max_duration = request.form.get("max_duration_seconds", "").strip()
            max_duration_seconds = int(max_duration) if max_duration.isdigit() else None
            try:
                input_path = download_audio(
                    youtube_url, WORK_DIR / f"yt_{job_id}", max_duration_seconds
                )
            except YoutubeDownloadError as exc:
                return render_template("index.html", error=str(exc))
        else:
            uploaded = request.files.get("media_file")
            if not uploaded or uploaded.filename == "":
                return render_template("index.html", error="Belum ada file yang dipilih.")
            ext = Path(uploaded.filename).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                return render_template(
                    "index.html",
                    error=f"Format '{ext}' belum didukung. Format yang didukung: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
                )
            dest_dir = WORK_DIR / f"upload_{job_id}"
            dest_dir.mkdir(parents=True, exist_ok=True)
            input_path = dest_dir / uploaded.filename
            uploaded.save(input_path)

        provider = get_provider()
        transcript = transcribe_file(input_path, provider, WORK_DIR)

        result_path = RESULT_DIR / f"{job_id}.txt"
        result_path.write_text(transcript, encoding="utf-8")

        return render_template("result.html", transcript=transcript, job_id=job_id)

    except (TranscriptionError, AudioProcessingError, FfmpegNotFoundError) as exc:
        return render_template("index.html", error=str(exc))
    finally:
        # Bersihkan file sumber (upload/unduhan) yang tidak lagi diperlukan.
        if input_path is not None:
            parent = input_path.parent
            if parent.exists() and parent != WORK_DIR:
                import shutil
                shutil.rmtree(parent, ignore_errors=True)


@app.route("/download/<job_id>")
def download(job_id):
    if not job_id.isalnum():
        abort(404)
    result_path = RESULT_DIR / f"{job_id}.txt"
    if not result_path.exists():
        abort(404)
    return send_file(
        result_path,
        as_attachment=True,
        download_name=f"transkrip_{job_id}.txt",
        mimetype="text/plain",
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
