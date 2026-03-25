"""
ui/views/update_bar.py — Compact update bar (bottom section)
Shows version info, Check Update and Apply buttons.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from ui import updater
from ui.constants import PANEL, SUBTEXT, SUCCESS, WARNING


class UpdateBar(ttk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame")
        self._app = app
        self._has_update = False
        self.columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        ttk.Separator(self, orient="horizontal").grid(
            row=0, column=0, sticky="ew", pady=(0, 6))

        inner = ttk.Frame(self, style="TFrame")
        inner.grid(row=1, column=0, sticky="ew")
        inner.columnconfigure(0, weight=1)

        # Left: version + status
        self._status_var = tk.StringVar(value=f"App Version: {updater.get_local_version()}")
        ttk.Label(inner, textvariable=self._status_var,
                  style="Sub.TLabel").grid(row=0, column=0, sticky="w")

        # Right: buttons
        btn_frame = ttk.Frame(inner, style="TFrame")
        btn_frame.grid(row=0, column=1, sticky="e")

        self._check_btn = ttk.Button(btn_frame,
                                     text="🔍  Check Update",
                                     command=self._check_update,
                                     style="Ghost.TButton")
        self._check_btn.pack(side="left", padx=(0, 6))

        self._apply_btn = ttk.Button(btn_frame,
                                     text="⬆  Download & Apply",
                                     command=self._apply_update,
                                     style="Warning.TButton",
                                     state="disabled")
        self._apply_btn.pack(side="left")

    # ── Check ──────────────────────────────────────────────────────────────────

    def _check_update(self):
        self._check_btn.config(state="disabled", text="🔍  Memeriksa...")
        self._apply_btn.config(state="disabled")
        self._status_var.set("Mengecek versi terbaru dari GitHub...")

        def _worker():
            try:
                available, local, remote = updater.is_update_available()
                self._app.after(0, self._on_check_done, available, local, remote)
            except Exception as e:
                self._app.after(0, self._on_check_error, str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_check_done(self, available: bool, local: str, remote: str):
        self._check_btn.config(state="normal", text="🔍  Check Update")
        self._has_update = available
        if available:
            self._apply_btn.config(state="normal")
            self._status_var.set(f"✦  Update tersedia! {local} → {remote}")
        else:
            self._apply_btn.config(state="disabled")
            self._status_var.set(f"✓  Sudah versi terbaru ({local})")

    def _on_check_error(self, msg: str):
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
        self._status_var.set("Mengunduh update...")

        def _worker():
            try:
                updater.download_and_apply(
                    on_progress=lambda m: self._app.after(0, self._status_var.set, m))
                self._app.after(0, self._on_apply_done)
            except Exception as e:
                self._app.after(0, self._on_apply_error, str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_apply_done(self):
        self._status_var.set("✓  Update selesai! Restart dalam 2 detik...")
        self._app.after(2000, updater.restart_app)

    def _on_apply_error(self, msg: str):
        self._check_btn.config(state="normal")
        self._apply_btn.config(state="normal" if self._has_update else "disabled")
        self._status_var.set(f"Update gagal: {msg}")
        messagebox.showerror("Update Error", msg, parent=self._app)
