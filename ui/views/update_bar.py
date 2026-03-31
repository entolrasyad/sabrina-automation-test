"""
ui/views/update_bar.py — Compact update bar (bottom section)
Shows version info, Check Update and Apply buttons.
"""

import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from ui import updater
from ui.constants import SUBTEXT, BORDER
from ui.constants import BTN_GHOST, BTN_WARNING  # dipakai oleh _BTN_MINI_*
from ui.constants import FONT_SMALL, FONT_LABEL

_BTN_MINI_GHOST   = {**BTN_GHOST,   "font": FONT_LABEL, "height": 24}
_BTN_MINI_WARNING = {**BTN_WARNING, "font": FONT_LABEL, "height": 24}


class UpdateBar(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self._app = app
        self._has_update = False
        self.columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        # Separator
        ctk.CTkFrame(self, height=1, fg_color=BORDER,
                     corner_radius=0).grid(row=0, column=0, sticky="ew", pady=(0, 6))

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.grid(row=1, column=0, sticky="ew")
        inner.columnconfigure(0, weight=1)

        # Left: version + status
        self._status_var = tk.StringVar(value=f"By: Entol Rasyad | App Version: {updater.get_local_version()}")
        ctk.CTkLabel(inner, textvariable=self._status_var,
                     fg_color="transparent",
                     text_color=SUBTEXT,
                     font=FONT_SMALL).grid(row=0, column=0, sticky="w")

        # Right: buttons
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        self._check_btn = ctk.CTkButton(btn_frame,
                                        text="🔍  Check Update",
                                        command=self._check_update,
                                        **_BTN_MINI_GHOST)
        self._check_btn.pack(side="left", padx=(0, 6))

        self._apply_btn = ctk.CTkButton(btn_frame,
                                        text="⬆  Download & Apply",
                                        command=self._apply_update,
                                        state="disabled",
                                        **_BTN_MINI_GHOST)
        self._apply_btn.pack(side="left")

    # ── Check ────────────────────────────────────────────────────────────────────

    def _check_update(self):
        self._check_btn.configure(state="disabled", text="🔍  Memeriksa...")
        self._apply_btn.configure(state="disabled")
        self._status_var.set("By: Entol Rasyad | Mengecek versi terbaru...")

        def _worker():
            try:
                available, local, remote = updater.is_update_available()
                self._app.after(0, self._on_check_done, available, local, remote)
            except Exception as e:
                self._app.after(0, self._on_check_error, str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_check_done(self, available: bool, local: str, remote: str):
        self._check_btn.configure(state="normal", text="🔍  Check Update")
        self._has_update = available
        if available:
            self._apply_btn.configure(state="normal", **_BTN_MINI_WARNING)
            self._status_var.set(f"✦  Update tersedia! {local} → {remote}")
        else:
            self._apply_btn.configure(state="disabled", **_BTN_MINI_GHOST)
            self._status_var.set(f"By: Entol Rasyad | ✓  Sudah versi terbaru ({local})")

    def _on_check_error(self, msg: str):
        self._check_btn.configure(state="normal", text="🔍  Check Update")
        self._status_var.set(f"By: Entol Rasyad | Gagal cek update: {msg}")

    # ── Apply ────────────────────────────────────────────────────────────────────

    def _apply_update(self):
        if not messagebox.askyesno(
                "Konfirmasi Update",
                "Download dan terapkan versi terbaru?\n\n"
                "Aplikasi akan restart otomatis setelah selesai.",
                parent=self._app):
            return

        self._check_btn.configure(state="disabled")
        self._apply_btn.configure(state="disabled")
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
        self._status_var.set("✓  Update selesai! Logout & restart dalam 2 detik...")
        self._app.after(2000, self._app.logout_then_restart)

    def _on_apply_error(self, msg: str):
        self._check_btn.configure(state="normal")
        self._apply_btn.configure(state="normal" if self._has_update else "disabled")
        self._status_var.set(f"Update gagal: {msg}")
        messagebox.showerror("Update Error", msg, parent=self._app)
