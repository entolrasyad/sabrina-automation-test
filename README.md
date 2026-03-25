# Sabrina BOT Tester

Aplikasi GUI untuk menguji bot Sabrina BRI secara manual maupun bulk melalui file Excel.

---

## Prasyarat

### 1. Install Python 3.x

1. Buka [https://www.python.org/downloads](https://www.python.org/downloads)
2. Download versi terbaru Python 3.x untuk Windows
3. Jalankan installer
4. **Penting:** centang opsi **"Add Python to PATH"** sebelum klik Install

   ![Add to PATH](https://www.python.org/static/img/python-logo.png)

5. Klik **Install Now** dan tunggu hingga selesai

Untuk memverifikasi instalasi, buka Command Prompt dan ketik:
```
python --version
```
Atau:
```
py --version
```
Jika muncul versi Python, instalasi berhasil.

---

### 2. Install Google Chrome

Aplikasi menggunakan Selenium dengan browser Chrome (headless).
Download di: [https://www.google.com/chrome](https://www.google.com/chrome)

---

## Cara Menjalankan

1. Extract file project ke folder mana saja (misal: `C:\Users\nama\Downloads\dolphin`)
2. Pastikan koneksi internet aktif (untuk install dependencies pertama kali)
3. Double-click file **`automationTest.bat`**

   Script akan otomatis:
   - Mengecek instalasi Python
   - Menginstall semua library yang dibutuhkan
   - Membuka aplikasi GUI

---

## Penggunaan Pertama

Saat pertama kali dibuka, akan muncul form untuk mengisi credentials:

- **Username** — email akun Sabrina BOT
- **Password** — password akun Sabrina BOT

Credentials disimpan di `config/credentials.json` secara lokal dan tidak dikirim ke mana pun.

Setelah credentials tersimpan, klik tombol **⚡ Login & Get Credentials** untuk memulai sesi.

---

## Fitur

| Fitur | Keterangan |
|---|---|
| **Manual** | Kirim satu pertanyaan dan lihat Dialog + Score secara langsung |
| **Bulk Excel** | Proses ratusan baris dari `data.xlsx` secara otomatis |
| **Start From** | Pilih baris awal untuk melanjutkan proses yang terhenti |
| **Stop** | Hentikan proses bulk di tengah jalan, progress tetap tersimpan |
| **Edit Credentials** | Ubah username/password kapan saja tanpa restart |
| **Auto Update** | Cek dan download versi terbaru dari GitHub otomatis |

---

## Struktur File

```
dolphin/
├── automationTest.bat       ← Jalankan ini
├── gui.py                   ← Entry point aplikasi
├── data.xlsx                ← File input/output Excel
├── version.txt              ← Versi aplikasi saat ini
├── requirements.txt         ← Daftar library Python
├── config/
│   ├── settings.py          ← Konfigurasi URL & timeout
│   └── credentials.json     ← Credentials (dibuat otomatis, tidak di-share)
├── pages/
│   └── dashboard_page.py    ← Selenium page object
├── utils/
│   └── driver_factory.py    ← Setup Chrome WebDriver
└── ui/
    ├── app.py               ← Main window
    ├── api.py               ← API calls & Selenium login
    ├── updater.py           ← Auto-update dari GitHub
    ├── constants.py         ← Warna & tema
    ├── styles.py            ← TTK dark theme
    └── views/
        ├── session_bar.py   ← Status bar & tombol login
        ├── manual_tab.py    ← Tab manual input
        ├── bulk_tab.py      ← Tab bulk Excel
        └── credentials_dialog.py ← Form credentials
```

---

## Troubleshooting

**Python tidak ditemukan**
→ Pastikan saat install Python, opsi "Add Python to PATH" sudah dicentang. Jika tidak, uninstall dan install ulang.

**Gagal install dependencies**
→ Pastikan koneksi internet aktif. Coba jalankan ulang `automationTest.bat`.

**Login gagal / User has active session**
→ Klik tombol **Logout** terlebih dahulu, tunggu beberapa saat, lalu coba Login kembali.

**Chrome tidak ditemukan**
→ Install Google Chrome dari [https://www.google.com/chrome](https://www.google.com/chrome).

---

## Versi

Lihat file `version.txt` untuk versi yang sedang berjalan.
Update otomatis tersedia melalui tombol **⬆ Update Tersedia** di aplikasi.
