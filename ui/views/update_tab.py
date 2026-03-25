"""
ui/views/update_tab.py — Tab untuk check & apply update dari GitHub.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from ui import updater
from ui.constants import PANEL, TEXT, SUBTEXT, SUCCESS, DANGER, WARNING, WIDGET, BORDER


class UpdateTab(ttk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent, padding=24)
        self._app = app
        self._has_update = False
        self._build()

    def _build(self):
        self.columnconfigure(1, weight=1)

        # ── Versi Lokal ─────────────────────────────────────────────────────────
        ttk.Label(self, text="Versi saat ini",
                  foreground=SUBTEXT, font=("Segoe UI", 9)).grid(
            row=0, column=0, sticky="w", pady=(0, 4))

        self._local_var = tk.StringVar(value=updater.get_local_version())
        ttk.Label(self, textvariable=self._local_var,
                  font=("Segoe UI", 13, "bold")).grid(
            row=0, column=1, sticky="w", padx=(16, 0), pady=(0, 4))

        # ── Versi Remote ────────────────────────────────────────────────────────
        ttk.Label(self, text="Versi terbaru",
                  foreground=SUBTEXT, font=("Segoe UI", 9)).grid(
            row=1, column=0, sticky="w", pady=(0, 4))

        self._remote_var = tk.StringVar(value="— belum dicek —")
        self._remote_label = ttk.Label(self, textvariable=self._remote_var,
                                       font=("Segoe UI", 13, "bold"),
                                       foreground=SUBTEXT)
        self._remote_label.grid(row=1, column=1, sticky="w", padx=(16, 0), pady=(0, 4))

        ttk.Separator(self, orient="horizontal").grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=16)

        # ── Tombol ──────────────────────────────────────────────────────────────
        btn_row = ttk.Frame(self)
        btn_row.grid(row=3, column=0, columnspan=2, sticky="w")

        self._check_btn = ttk.Button(btn_row,
                                     text="🔍  Check Update",
                                     command=self._check_update,
                                     style="Accent.TButton")
        self._check_btn.pack(side="left", padx=(0, 10))

        self._apply_btn = ttk.Button(btn_row,
                                     text="⬆  Download & Apply Update",
                                     command=self._apply_update,
                                     style="Warning.TButton",
                                     state="disabled")
        self._apply_btn.pack(side="left")

        # ── Status ──────────────────────────────────────────────────────────────
        self._status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self._status_var,
                  foreground=SUBTEXT, font=("Segoe UI", 9),
                  wraplength=500).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(14, 0))

        # ── Progress ────────────────────────────────────────────────────────────
        self._progress = ttk.Progressbar(self, mode="indeterminate", length=300)
        self._progress.grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self._progress.grid_remove()

    # ── Check ──────────────────────────────────────────────────────────────────

    def _check_update(self):
        self._check_btn.config(state="disabled", text="🔍  Memeriksa...")
        self._apply_btn.config(state="disabled")
        self._status_var.set("Mengecek versi terbaru dari GitHub...")
        self._progress.grid()
        self._progress.start(10)

        def _worker():
            try:
                available, local, remote = updater.is_update_available()
                self._app.after(0, self._on_check_done, available, local, remote)
            except Exception as e:
                self._app.after(0, self._on_check_error, str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_check_done(self, available: bool, local: str, remote: str):
        self._progress.stop()
        self._progress.grid_remove()
        self._check_btn.config(state="normal", text="🔍  Check Update")
        self._local_var.set(local)
        self._remote_var.set(remote)
        self._has_update = available

        if available:
            self._remote_label.config(foreground=WARNING)
            self._apply_btn.config(state="normal")
            self._status_var.set(f"✦  Update tersedia! {local} → {remote}. Klik 'Download & Apply' untuk update.")
        else:
            self._remote_label.config(foreground=SUCCESS)
            self._apply_btn.config(state="disabled")
            self._status_var.set(f"✓  Aplikasi sudah versi terbaru ({local}).")

    def _on_check_error(self, msg: str):
        self._progress.stop()
        self._progress.grid_remove()
        self._check_btn.config(state="normal", text="🔍  Check Update")
        self._status_var.set(f"Gagal cek update: {msg}")

    # ── Apply ──────────────────────────────────────────────────────────────────

    def _apply_update(self):
        if not messagebox.askyesno(
                "Konfirmasi Update",
                "Download dan terapkan versi terbaru dari GitHub?\n\n"
                "Aplikasi akan restart otomatis setelah selesai.",
                parent=self._app):
            return

        self._check_btn.config(state="disabled")
        self._apply_btn.config(state="disabled")
        self._progress.grid()
        self._progress.start(10)

        def _worker():
            try:
                updater.download_and_apply(
                    on_progress=lambda m: self._app.after(0, self._status_var.set, m))
                self._app.after(0, self._on_apply_done)
            except Exception as e:
                self._app.after(0, self._on_apply_error, str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_apply_done(self):
        self._progress.stop()
        self._progress.grid_remove()
        self._status_var.set("✓  Update selesai! Restart dalam 2 detik...")
        self._app.after(2000, updater.restart_app)

    def _on_apply_error(self, msg: str):
        self._progress.stop()
        self._progress.grid_remove()
        self._check_btn.config(state="normal")
        self._apply_btn.config(state="normal" if self._has_update else "disabled")
        self._status_var.set(f"Update gagal: {msg}")
        messagebox.showerror("Update Error", msg, parent=self._app)
