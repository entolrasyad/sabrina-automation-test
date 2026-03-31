"""
ui/updater.py — Auto-update dari GitHub public repo.
"""

import os
import sys
import shutil
import zipfile
import tempfile
import subprocess
import requests

REPO_RAW   = "https://raw.githubusercontent.com/entolrasyad/sabrina-automation-test/master"
REPO_ZIP   = "https://github.com/entolrasyad/sabrina-automation-test/archive/refs/heads/master.zip"
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# File/folder yang tidak boleh ditimpa saat update
PROTECTED = {
    "config/credentials.json",
    "data.xlsx",
    "error.log",
    "version.txt",   # diupdate manual di akhir proses
}


def get_local_version() -> str:
    path = os.path.join(BASE_DIR, "version.txt")
    try:
        return open(path, encoding="utf-8").read().strip()
    except Exception:
        return "v0.0"


def get_remote_version() -> str:
    """Fetch version.txt dari GitHub. Raise jika gagal."""
    resp = requests.get(f"{REPO_RAW}/version.txt", timeout=10)
    resp.raise_for_status()
    return resp.text.strip()


def _parse_version(v: str) -> tuple:
    """Convert 'v1.2.3' → (1, 2, 3) untuk perbandingan numerik."""
    import re
    nums = re.findall(r"\d+", v)
    return tuple(int(n) for n in nums) if nums else (0,)


def is_update_available() -> tuple[bool, str, str]:
    """Return (ada_update, local_ver, remote_ver).
    Update dianggap tersedia hanya jika remote LEBIH BARU dari local.
    """
    local  = get_local_version()
    remote = get_remote_version()
    available = _parse_version(remote) > _parse_version(local)
    return available, local, remote


def download_and_apply(on_progress=None) -> None:
    """
    Download ZIP repo, extract, copy file baru ke BASE_DIR.
    on_progress(msg: str) dipanggil tiap tahap.
    """
    def _prog(msg):
        if on_progress:
            on_progress(msg)

    _prog("Mendownload versi terbaru...")
    resp = requests.get(REPO_ZIP, timeout=60, stream=True)
    resp.raise_for_status()

    tmp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(tmp_dir, "update.zip")

    with open(zip_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    _prog("Mengekstrak file...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(tmp_dir)

    # Folder hasil extract: sabrina-automation-test-master/
    extracted = next(
        os.path.join(tmp_dir, d)
        for d in os.listdir(tmp_dir)
        if os.path.isdir(os.path.join(tmp_dir, d))
    )

    _prog("Menerapkan update...")
    for root, dirs, files in os.walk(extracted):
        # Skip folder tersembunyi
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            src_abs = os.path.join(root, fname)
            rel     = os.path.relpath(src_abs, extracted).replace("\\", "/")

            if rel in PROTECTED:
                continue

            dst = os.path.join(BASE_DIR, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src_abs, dst)

    # Update version.txt setelah semua file berhasil dicopy
    remote_ver_path = os.path.join(extracted, "version.txt")
    if os.path.exists(remote_ver_path):
        shutil.copy2(remote_ver_path, os.path.join(BASE_DIR, "version.txt"))

    shutil.rmtree(tmp_dir, ignore_errors=True)
    _prog("Update selesai!")


def restart_app() -> None:
    """Install dependencies baru lalu restart gui.py dengan Python yang sama."""
    req = os.path.join(BASE_DIR, "requirements.txt")
    if os.path.exists(req):
        subprocess.call(
            [sys.executable, "-m", "pip", "install", "-r", req,
             "--disable-pip-version-check", "--quiet"],
        )
    gui = os.path.join(BASE_DIR, "gui.py")
    subprocess.Popen([sys.executable, gui])
    sys.exit(0)
