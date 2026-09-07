@echo off
setlocal enabledelayedexpansion
title Transkrip Audio/Video
cd /d "%~dp0"

echo ============================================
echo   Transkrip Audio/Video ke Teks
echo ============================================
echo.

rem --- Cek Python terpasang ---
set PYTHON_CMD=
where py >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_CMD=py
) else (
    where python >nul 2>nul
    if !errorlevel!==0 (
        set PYTHON_CMD=python
    )
)

if "!PYTHON_CMD!"=="" (
    echo [ERROR] Python belum terpasang di komputer ini.
    echo.
    echo Silakan install Python dulu dari https://www.python.org/downloads/
    echo PENTING: saat instalasi, centang kotak "Add Python to PATH".
    echo Setelah selesai install, tutup jendela ini lalu klik dua kali file ini lagi.
    echo.
    pause
    exit /b 1
)

rem --- Setup venv (hanya sekali, saat pertama kali dijalankan) ---
if not exist "venv\Scripts\python.exe" (
    echo Menyiapkan aplikasi untuk pertama kali, mohon tunggu ^(cuma sekali^)...
    !PYTHON_CMD! -m venv venv
    if not exist "venv\Scripts\python.exe" (
        echo [ERROR] Gagal membuat lingkungan Python ^(venv^).
        pause
        exit /b 1
    )
)

if not exist "venv\.setup_done" (
    echo Menginstall komponen yang dibutuhkan, mohon tunggu ^(cuma sekali, butuh internet^)...
    "venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
    "venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
    if !errorlevel! neq 0 (
        echo [ERROR] Gagal menginstall komponen aplikasi. Pastikan komputer terhubung internet, lalu coba lagi.
        pause
        exit /b 1
    )
    echo done > "venv\.setup_done"
)

rem --- Pengecekan ffmpeg (opsional, aplikasi tetap jalan tapi transkripsi akan gagal tanpa ini) ---
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    if not exist "ffmpeg_bin\ffmpeg.exe" (
        echo [PERINGATAN] ffmpeg belum ditemukan.
        echo Transkripsi TIDAK akan berhasil sampai ffmpeg terpasang.
        echo Lihat panduan di PANDUAN_WINDOWS.md untuk cara memasangnya.
        echo Aplikasi tetap akan dibuka, tapi proses transkripsi akan gagal sampai ffmpeg tersedia.
        echo.
    )
)

echo Menjalankan aplikasi... browser akan terbuka otomatis sebentar lagi.
echo Biarkan jendela hitam ini tetap terbuka selama aplikasi dipakai.
echo Tutup jendela ini untuk menghentikan aplikasi.
echo.

"venv\Scripts\python.exe" server.py

pause
