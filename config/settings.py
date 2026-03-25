"""
Konfigurasi global untuk test suite Dolphin.
Ubah nilai di bawah sesuai environment yang digunakan.
"""

# ─── URL ──────────────────────────────────────────────────────────────────────
BASE_URL   = "https://sabrina.dev.bri.co.id:1443"
LOGIN_URL  = f"{BASE_URL}/dolphin/login"

# ─── KREDENSIAL ───────────────────────────────────────────────────────────────
# Disimpan di config/credentials.json (tidak di-hardcode di sini)
USERNAME = ""
PASSWORD = ""

# ─── TIMEOUT (detik) ──────────────────────────────────────────────────────────
PAGE_LOAD_TIMEOUT = 30   # Tunggu halaman load
ACTION_TIMEOUT    = 15   # Tunggu elemen muncul / bisa diklik

# ─── BROWSER ──────────────────────────────────────────────────────────────────
HEADLESS       = True    # True = tanpa tampilan browser
WINDOW_SIZE    = (1366, 768)
SESSION_DIR    = ""      # kosong = tidak simpan session (fresh tiap run)
