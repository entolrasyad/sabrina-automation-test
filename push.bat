@echo off
echo [1/3] Bumping version...
python bump_version.py
if errorlevel 1 ( echo Gagal bump version & pause & exit /b 1 )

echo [2/3] Commit semua perubahan...
git add .
git commit -m "chore: bump version"
if errorlevel 1 ( echo Tidak ada perubahan untuk di-commit & )

echo [3/3] Push ke origin master...
git push origin master
if errorlevel 1 ( echo Push gagal & pause & exit /b 1 )

echo.
echo Done!
timeout /t 2 >nul
