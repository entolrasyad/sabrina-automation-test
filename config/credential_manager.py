"""
config/credential_manager.py
Baca & tulis credentials dari file JSON lokal.
"""

import json
import os

_CRED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")


def load() -> dict:
    """Return {"username": ..., "password": ...} atau dict kosong jika belum ada."""
    if not os.path.exists(_CRED_FILE):
        return {"username": "", "password": ""}
    try:
        with open(_CRED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"username": "", "password": ""}


def save(username: str, password: str) -> None:
    """Simpan credentials ke file JSON."""
    with open(_CRED_FILE, "w", encoding="utf-8") as f:
        json.dump({"username": username, "password": password}, f, indent=2)


def exists() -> bool:
    """True jika credentials sudah pernah disimpan dan tidak kosong."""
    creds = load()
    return bool(creds.get("username") and creds.get("password"))
