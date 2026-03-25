@echo off
title Automation Bot Tester
color 0B

cd /d "%~dp0"

echo.
echo  ================================================
echo             Bot Tester  ^|  Sabrina BRI
echo  ================================================
echo.

:: ── Cek Python ────────────────────────────────────────────────────────────────
py --version >nul 2>&1
if %errorlevel% == 0 ( set PYTHON=py & goto :found_python )

python --version >nul 2>&1
if %errorlevel% == 0 ( set PYTHON=python & goto :found_python )

echo  [ERROR] Python tidak ditemukan.
echo  Install Python 3.x dari https://python.org
echo  Pastikan centang "Add Python to PATH" saat instalasi.
echo.
pause
exit /b 1

:found_python
for /f "tokens=*" %%v in ('%PYTHON% --version 2^>^&1') do set PY_VER=%%v
echo  [OK] %PY_VER% ditemukan.
echo.

:: ── Cek pip ────────────────────────────────────────────────────────────────────
%PYTHON% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [INFO] pip tidak ditemukan, mencoba install...
    %PYTHON% -m ensurepip --upgrade
    if %errorlevel% neq 0 (
        echo  [ERROR] Gagal mengaktifkan pip.
        pause
        exit /b 1
    )
)
echo  [OK] pip tersedia.
echo.

:: ── Install / Update Dependencies ─────────────────────────────────────────────
echo  [INFO] Menginstall dependencies dari requirements.txt...
%PYTHON% -m pip install -r requirements.txt --user --disable-pip-version-check
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Gagal install dependencies.
    echo  Pastikan koneksi internet aktif, lalu coba lagi.
    pause
    exit /b 1
)
echo.
echo  [OK] Semua dependencies terinstall.
echo.

:: ── Cek Google Chrome ─────────────────────────────────────────────────────────
set CHROME_FOUND=0
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe"      set CHROME_FOUND=1
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set CHROME_FOUND=1
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe"       set CHROME_FOUND=1
if "%CHROME_FOUND%"=="0" (
    echo  [WARNING] Google Chrome tidak ditemukan.
    echo  Pastikan Chrome sudah terinstall sebelum menekan Login.
    echo.
) else (
    echo  [OK] Google Chrome ditemukan.
    echo.
)

:: ── Hapus log error lama ───────────────────────────────────────────────────────
if exist error.log del error.log

:: ── Jalankan GUI ───────────────────────────────────────────────────────────────
echo  [INFO] Menjalankan GUI...
echo  ================================================
echo.
%PYTHON% gui.py

:: ── Selesai / Error ────────────────────────────────────────────────────────────
echo.
if exist error.log (
    echo  [ERROR] Aplikasi keluar dengan error:
    echo  ------------------------------------------------
    type error.log
    echo  ------------------------------------------------
) else (
    echo  [INFO] Aplikasi ditutup.
)
echo.
pause
