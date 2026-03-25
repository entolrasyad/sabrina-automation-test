"""
ui/views/manual_tab.py — Manual bot test tab
Single input → Dialog + Score output with session reset button.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from ui.constants import PANEL, SUCCESS
from ui.api import call_bot_api


class ManualTab(ttk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent, padding=14)
        self._app = app
        self.columnconfigure(1, weight=1)
        self._build()

    def _build(self):
        ttk.Label(self, text="User Says").grid(row=0, column=0, sticky="w")

        input_frame = ttk.Frame(self)
        input_frame.grid(row=0, column=1, columnspan=2, sticky="ew", padx=(10, 0))
        input_frame.columnconfigure(0, weight=1)

        self._input = ttk.Entry(input_frame, font=("Segoe UI", 10))
        self._input.grid(row=0, column=0, sticky="ew", ipady=3)
        self._input.bind("<Return>", lambda *_: self._send())

        self._send_btn = ttk.Button(input_frame, text="▶  Send",
                                    command=self._send,
                                    style="Accent.TButton")
        self._send_btn.grid(row=0, column=1, padx=(8, 0))

        self._reset_btn = ttk.Button(input_frame, text="↩  BATAL (Sesi Chat Baru)",
                                     command=self._reset_session,
                                     style="Warning.TButton",
                                     state="disabled")
        self._reset_btn.grid(row=0, column=2, padx=(6, 0))

        ttk.Separator(self, orient="horizontal").grid(
            row=1, column=0, columnspan=3, sticky="ew", pady=(14, 0))

        _entry_kw = dict(
            font=("Segoe UI", 10),
            bg=PANEL, fg=SUCCESS,
            readonlybackground=PANEL,
            disabledforeground=SUCCESS,
            disabledbackground=PANEL,
            relief="flat", bd=0,
            highlightthickness=0,
            insertbackground=SUCCESS,
        )

        ttk.Label(self, text="Dialog").grid(row=2, column=0, sticky="w", pady=(12, 0))
        self._dialog_var = tk.StringVar()
        tk.Entry(self, textvariable=self._dialog_var, state="readonly",
                 **_entry_kw).grid(row=2, column=1, columnspan=2, sticky="ew",
                                   padx=(10, 0), pady=(12, 0), ipady=6)

        ttk.Label(self, text="Score").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self._score_var = tk.StringVar()
        tk.Entry(self, textvariable=self._score_var, state="readonly",
                 **_entry_kw).grid(row=3, column=1, columnspan=2, sticky="ew",
                                   padx=(10, 0), pady=(8, 0), ipady=6)

    # ── Actions ─────────────────────────────────────────────────────────────────

    def _send(self):
        app = self._app
        if not app.check_ready():
            return
        user_says = self._input.get().strip()
        if not user_says:
            messagebox.showwarning("Input Kosong", "Isi kolom User Says terlebih dahulu.")
            return

        self._send_btn.config(state="disabled")
        self._dialog_var.set("Loading...")
        self._score_var.set("...")

        cookie_str = app._cookie_str
        view_state = app._view_state

        def _worker():
            result = call_bot_api(cookie_str, view_state, user_says)
            app.after(0, self._on_done, result)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_done(self, result):
        self._dialog_var.set(result["dialog"])
        self._score_var.set(result["score"])
        self._send_btn.config(state="normal")

    def _reset_session(self):
        app = self._app
        if not app.check_ready():
            return
        self._reset_btn.config(state="disabled")
        app.session_bar.set_progress("Sesi sedang di Reset...")

        cookie_str = app._cookie_str
        view_state = app._view_state

        def _worker():
            for reset_word in ("menu", "batal"):
                call_bot_api(cookie_str, view_state, reset_word)
            app.after(0, _done)

        def _done():
            self._reset_btn.config(state="normal")
            app.session_bar.set_progress("✓  Sesi berhasil direset. Chat baru telah terbuka.")

        threading.Thread(target=_worker, daemon=True).start()
