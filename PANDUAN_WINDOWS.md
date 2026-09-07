# Panduan Pakai (Windows) — Tanpa Perlu Coding

Panduan ini untuk yang belum pernah pakai terminal/command line. Cukup ikuti
langkah di bawah, sekali saja di awal.

## Langkah 1: Download aplikasinya

1. Buka halaman repo di GitHub: `masbil27/develop`, branch
   `claude/audio-video-transcription-tool-2bv7am`.
2. Klik tombol hijau **Code** → **Download ZIP**.
3. Extract (klik kanan → *Extract All*) ke folder mana saja di komputer,
   misalnya `D:\TranskripApp`.

## Langkah 2: Install Python (sekali saja)

1. Buka https://www.python.org/downloads/ lalu klik tombol download versi
   terbaru.
2. Jalankan installer-nya. **PENTING**: di layar pertama installer, centang
   kotak **"Add Python to PATH"** sebelum klik Install.
3. Tunggu sampai selesai, lalu klik Close.

## Langkah 3: Install ffmpeg (sekali saja)

Ini komponen untuk membaca file audio/video.

1. Buka https://ffmpeg.org/download.html, klik ikon Windows, ikuti link ke
   halaman build Windows (mis. gyan.dev) dan unduh paket **"release
   essentials"** (format .zip).
2. Extract file zip tersebut. Di dalamnya ada folder `bin` berisi 3 file:
   `ffmpeg.exe`, `ffplay.exe`, `ffprobe.exe`.
3. Di folder aplikasi yang sudah kamu extract di Langkah 1 (mis.
   `D:\TranskripApp`), buka folder `ffmpeg_bin`.
4. Copy `ffmpeg.exe` dan `ffprobe.exe` (dari folder `bin` hasil extract tadi)
   ke dalam folder `ffmpeg_bin` itu.

Tidak perlu edit PATH sistem atau pengaturan Windows lain — aplikasi akan
otomatis menemukan ffmpeg dari folder ini.

## Langkah 4: Siapkan API key

1. Buka https://openrouter.ai/keys, login/daftar, buat API key baru.
2. Simpan key itu (jangan dibagikan/ditempel di chat manapun).

## Langkah 5: Jalankan aplikasinya

1. Di folder aplikasi (mis. `D:\TranskripApp`), cari file **"Jalankan
   Aplikasi.bat"**.
2. Klik dua kali file itu.
3. Jendela hitam (command prompt) akan muncul. Saat pertama kali dijalankan,
   akan ada tulisan "Menyiapkan aplikasi untuk pertama kali..." — ini normal,
   tunggu sampai selesai (butuh koneksi internet, sekali saja, beberapa
   menit). Kalau Windows menampilkan peringatan keamanan ("Windows protected
   your PC"), klik **More info** lalu **Run anyway**.
4. Browser akan otomatis terbuka ke halaman aplikasi. Kalau belum ada
   pengaturan API key, kamu akan diarahkan ke halaman **Pengaturan** —
   tempel API key dari Langkah 4 di situ, klik **Simpan Pengaturan**.
5. Selesai. Sekarang bisa mulai upload file audio/video atau tempel link
   YouTube untuk ditranskripsi.

Untuk pemakaian berikutnya, tinggal klik dua kali **"Jalankan Aplikasi.bat"**
lagi — tidak perlu ulangi Langkah 2-4 (kecuali kalau mau ganti API key, bisa
lewat halaman Pengaturan kapan saja).

## Kalau ada masalah

- **Jendela hitam langsung tertutup / muncul tulisan error Python** →
  ulangi Langkah 2, pastikan centang "Add Python to PATH", lalu restart
  komputer sekali.
- **Transkripsi gagal, pesan menyebut ffmpeg** → cek lagi Langkah 3, pastikan
  `ffmpeg.exe` dan `ffprobe.exe` benar-benar ada di dalam folder
  `ffmpeg_bin`.
- **Pesan error dari OpenRouter/API key** → cek lagi API key di halaman
  Pengaturan, atau key mungkin sudah kedaluwarsa/di-revoke — buat yang baru
  di openrouter.ai/keys.
- Kalau masih bermasalah, kirim screenshot pesan error yang muncul di
  jendela hitam tadi.
