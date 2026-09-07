import hmac
import logging
import os
import uuid
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, abort, redirect, render_template, request, send_file, url_for

load_dotenv()

from app import config_store  # noqa: E402
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

# Kalau ffmpeg.exe/ffprobe.exe ditaruh di folder ffmpeg_bin (misal di Windows,
# tanpa perlu edit PATH sistem), pakai itu secara otomatis.
FFMPEG_BIN_DIR = BASE_DIR / "ffmpeg_bin"
if FFMPEG_BIN_DIR.is_dir():
    os.environ["PATH"] = str(FFMPEG_BIN_DIR) + os.pathsep + os.environ.get("PATH", "")

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

APP_USERNAME = os.environ.get("APP_USERNAME", "")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")


def _auth_enabled() -> bool:
    return bool(APP_USERNAME and APP_PASSWORD)


def _check_credentials(username: str, password: str) -> bool:
    return hmac.compare_digest(username, APP_USERNAME) and hmac.compare_digest(password, APP_PASSWORD)


def requires_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not _auth_enabled():
            return view(*args, **kwargs)
        auth = request.authorization
        if not auth or not _check_credentials(auth.username or "", auth.password or ""):
            return Response(
                "Login diperlukan.",
                401,
                {"WWW-Authenticate": 'Basic realm="Transkrip Audio/Video"'},
            )
        return view(*args, **kwargs)

    return wrapped


@app.route("/")
@requires_auth
def index():
    config = config_store.load_config()
    if not config_store.is_configured(config) and not (
        os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    ):
        return redirect(url_for("settings"))
    return render_template("index.html")


@app.route("/settings", methods=["GET", "POST"])
@requires_auth
def settings():
    saved = False
    error = None
    if request.method == "POST":
        provider = request.form.get("provider", "openrouter").strip().lower()
        if provider not in ("openrouter", "openai"):
            error = "Provider tidak dikenal."
        else:
            config_store.save_config(
                {
                    "provider": provider,
                    "openrouter_api_key": (request.form.get("openrouter_api_key") or "").strip(),
                    "openrouter_model": (request.form.get("openrouter_model") or "").strip()
                    or "openai/gpt-4o-audio-preview",
                    "openai_api_key": (request.form.get("openai_api_key") or "").strip(),
                    "openai_model": "whisper-1",
                    "language_hint": request.form.get("language_hint", "mixed"),
                }
            )
            saved = True

    config = config_store.load_config()
    return render_template("settings.html", config=config, saved=saved, error=error)


@app.route("/transcribe", methods=["POST"])
@requires_auth
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
@requires_auth
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


def _open_browser_later(url: str, delay: float = 1.5) -> None:
    import threading
    import webbrowser

    def _open():
        webbrowser.open(url)

    threading.Timer(delay, _open).start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    if os.environ.get("AUTO_OPEN_BROWSER", "1") != "0":
        _open_browser_later(f"http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
