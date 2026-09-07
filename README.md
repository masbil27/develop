# Transkrip Audio/Video ke Teks

Web app sederhana untuk mentranskripsi rekaman audio/video (rapat, wawancara,
kunjungan lapangan, dsb.) menjadi teks, termasuk dari link YouTube (video
maupun siaran live).

## PENTING: soal API key

Jangan pernah menaruh API key langsung di kode atau commit ke git. Semua key
disimpan di file `.env` (sudah masuk `.gitignore`, tidak ikut ter-commit).

> Jika kamu pernah menempel/mengetik API key di percakapan chat, media apa
> pun yang bisa ter-log, atau tempat lain yang bukan file `.env` lokal —
> anggap key itu bocor dan **segera revoke/rotate** di dashboard provider
> (OpenRouter: https://openrouter.ai/keys, OpenAI: https://platform.openai.com/api-keys),
> lalu generate key baru untuk dipakai di sini.

## Prasyarat

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) terpasang dan ada di PATH (`ffmpeg -version` harus jalan)
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`
- Akses internet ke provider transkripsi (OpenRouter dan/atau OpenAI)

## Instalasi

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# lalu edit .env: isi OPENROUTER_API_KEY (atau OPENAI_API_KEY kalau pakai provider openai)
```

## Menjalankan

```bash
python server.py
```

Buka `http://localhost:5000` di browser.

## Konfigurasi (`.env`)

| Variabel | Keterangan |
|---|---|
| `TRANSCRIPTION_PROVIDER` | `openrouter` (default) atau `openai` |
| `OPENROUTER_API_KEY` | Wajib kalau provider = openrouter |
| `OPENROUTER_MODEL` | Model audio-capable di OpenRouter, mis. `openai/gpt-4o-audio-preview`. Cek daftar model terbaru di https://openrouter.ai/models sebelum dipakai, karena dukungan audio tergantung model. |
| `OPENAI_API_KEY` | Wajib kalau provider = openai |
| `OPENAI_TRANSCRIBE_MODEL` | Default `whisper-1`, bisa diganti `gpt-4o-transcribe` |
| `TRANSCRIPTION_LANGUAGE_HINT` | `id`, `en`, atau `mixed` (default) untuk campuran Indonesia-Inggris |
| `CHUNK_SECONDS` | Panjang tiap potongan audio sebelum dikirim ke API (default 300 detik / 5 menit) — audio panjang otomatis dipecah |
| `MAX_CONTENT_LENGTH_MB` | Batas ukuran upload file (default 1024 MB) |
| `PORT` | Port web server (default 5000) |
| `APP_USERNAME` / `APP_PASSWORD` | Login (HTTP Basic Auth). Kosongkan dua-duanya untuk pemakaian lokal tanpa login. **Wajib diisi kalau di-deploy online.** |

## Cara pakai

1. **Unggah file** — pilih tab "Unggah File", pilih file audio (mp3, wav, m4a,
   aac, flac, ogg, opus) atau video (mp4, mov, mkv, webm, avi), klik "Mulai
   Transkripsi".
2. **Link YouTube** — pilih tab "Link YouTube", tempel URL video atau siaran
   live. Untuk siaran live, isi "Batas durasi rekam" (detik) supaya
   perekaman berhenti otomatis (mis. `3600` untuk 1 jam).
3. Tunggu proses selesai (rekaman panjang otomatis dipecah jadi beberapa
   bagian dan diproses berurutan — bisa memakan waktu untuk rekaman
   berjam-jam).
4. Hasil transkrip tampil di layar, bisa diunduh sebagai `.txt`.

Selalu periksa ulang hasil transkrip sebelum dipakai untuk dokumen resmi
(notulensi, laporan ke donor, dsb.) — transkripsi otomatis tetap bisa keliru,
terutama untuk istilah teknis, nama orang/lembaga, dan angka.

## Deploy online (Render.com)

Repo ini sudah punya `Dockerfile`, jadi bisa langsung dipakai untuk Web
Service di Render (atau platform lain yang support Docker seperti Railway,
Fly.io).

1. Buat akun di https://render.com (kalau belum punya), hubungkan akun
   GitHub-nya.
2. Di dashboard Render: **New +** → **Web Service** → pilih repo
   `masbil27/develop`.
3. Pastikan **Branch** yang dipilih: `claude/audio-video-transcription-tool-2bv7am`
   (atau branch tempat kode ini berada setelah di-merge).
4. **Runtime**: pilih **Docker** (Render otomatis mendeteksi `Dockerfile`).
5. Di bagian **Environment Variables**, isi minimal:
   - `TRANSCRIPTION_PROVIDER` = `openrouter`
   - `OPENROUTER_API_KEY` = kunci baru kamu (jangan yang lama/bocor)
   - `OPENROUTER_MODEL` = model audio-capable pilihanmu
   - `APP_USERNAME` = username login
   - `APP_PASSWORD` = password login
   - (opsional) `TRANSCRIPTION_LANGUAGE_HINT`, `CHUNK_SECONDS`, dll sesuai
     tabel konfigurasi di atas
6. Klik **Deploy**. Setelah build selesai, Render kasih link publik bentuk
   `https://<nama-service>.onrender.com` — itu link web app-nya. Buka,
   login pakai `APP_USERNAME`/`APP_PASSWORD` yang tadi diisi.

### Keterbatasan penting untuk deployment online

- **Request timeout**: transkripsi saat ini diproses **sinkron** dalam satu
  HTTP request (upload → tunggu semua chunk selesai → hasil tampil).
  Gunicorn di `Dockerfile` sudah diset timeout 30 menit, tapi platform
  hosting (Render, Railway, dll) biasanya punya batas timeout proxy
  sendiri di depan aplikasi yang **tidak bisa diubah dari kode ini** — cek
  dokumentasi/dashboard platform yang dipakai. Kalau rekaman rapat
  berjam-jam bikin request timeout, kabari saya — solusinya perlu diubah
  jadi proses background (job queue) + halaman status, bukan sekadar
  tunggu di satu request.
- **Penyimpanan sementara**: file upload & hasil transkrip disimpan di
  disk container. Di Render free/starter tier, disk ini **hilang setiap
  kali service di-restart/redeploy** — jadi jangan andalkan link `/download`
  untuk penyimpanan jangka panjang, langsung unduh & simpan hasilnya.
- **Biaya API**: tiap transkripsi memakai kuota API berbayar (OpenRouter/
  OpenAI) milik pemilik key. Login (`APP_USERNAME`/`APP_PASSWORD`)
  membantu membatasi siapa yang bisa memicu pemakaian ini.

## Catatan penggunaan link YouTube

Fitur unduh dari YouTube memakai `yt-dlp`. Gunakan hanya untuk keperluan
internal/dinas yang sah (mis. mengarsipkan webinar atau rapat daring yang
disiarkan lembaga sendiri atau donor), dan perhatikan hak cipta serta Terms
of Service YouTube untuk konten yang bukan milik sendiri.

## Struktur proyek

```
server.py                  # entry point Flask
app/
  audio.py                 # ekstraksi & pemotongan audio (ffmpeg)
  youtube.py                # unduh audio dari YouTube (yt-dlp)
  transcriber.py            # orkestrasi pipeline transkripsi
  providers/
    openrouter.py           # provider via OpenRouter chat completions (audio input)
    openai_provider.py      # provider via OpenAI audio transcriptions API
  templates/                # halaman HTML
  static/                   # CSS
```

## Mengganti provider

Karena dukungan audio di OpenRouter bergantung pada model yang tersedia saat
itu, kalau hasil dari `openrouter` kurang presisi atau modelnya error, ganti
di `.env`:

```
TRANSCRIPTION_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

`OpenAI Whisper`/`gpt-4o-transcribe` adalah endpoint transkripsi khusus
(bukan chat completions), jadi umumnya lebih stabil untuk akurasi.
