"""
ui/views/manual_tab.py — Manual bot test tab
Single input → chat bubble history (user right, bot left).
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from ui.constants import BG, WIDGET, ACCENT, TEXT, SUBTEXT
from ui.api import call_bot_api


class ManualTab(ttk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent, padding=14)
        self._app = app
        self.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self._build()

    def _build(self):
        # ── Row 0: Input ────────────────────────────────────────────────────────
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

        # ── Row 1: Separator ────────────────────────────────────────────────────
        ttk.Separator(self, orient="horizontal").grid(
            row=1, column=0, columnspan=3, sticky="ew", pady=(14, 0))

        # ── Row 2: Chat area ────────────────────────────────────────────────────
        chat_outer = tk.Frame(self, bg=BG)
        chat_outer.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=(10, 0))
        chat_outer.columnconfigure(0, weight=1)
        chat_outer.rowconfigure(0, weight=1)

        self._canvas = tk.Canvas(chat_outer, bg=BG, highlightthickness=0,
                                 bd=0, relief="flat")
        self._canvas.grid(row=0, column=0, sticky="nsew")

        _sb = ttk.Scrollbar(chat_outer, orient="vertical",
                            command=self._canvas.yview)
        _sb.grid(row=0, column=1, sticky="ns")
        self._canvas.configure(yscrollcommand=_sb.set)

        self._chat_inner = tk.Frame(self._canvas, bg=BG)
        self._chat_win = self._canvas.create_window(
            (0, 0), window=self._chat_inner, anchor="nw")

        self._chat_inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._chat_inner.bind("<MouseWheel>", self._on_mousewheel)

    # ── Chat helpers ────────────────────────────────────────────────────────────

    def _on_inner_configure(self, *_):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, e):
        self._canvas.itemconfig(self._chat_win, width=e.width)

    def _on_mousewheel(self, e):
        self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def _add_user_bubble(self, text: str):
        """Right-aligned blue bubble for user message."""
        row = tk.Frame(self._chat_inner, bg=BG)
        row.pack(fill="x", pady=(6, 0), padx=8)

        bubble = tk.Label(row, text=text,
                          bg=ACCENT, fg="#ffffff",
                          font=("Segoe UI", 9),
                          wraplength=380, justify="left",
                          padx=12, pady=8, relief="flat",
                          cursor="arrow")
        bubble.pack(side="right")
        self._scroll_bottom()

    def _add_bot_bubble(self, dialog: str, score: str):
        """Left-aligned dark bubble for bot response."""
        row = tk.Frame(self._chat_inner, bg=BG)
        row.pack(fill="x", pady=(4, 0), padx=8)

        content = f"{dialog}\n\nScore: {score}" if score else dialog

        bubble = tk.Label(row, text=content,
                          bg=WIDGET, fg=TEXT,
                          font=("Segoe UI", 9),
                          wraplength=380, justify="left",
                          padx=12, pady=8, relief="flat",
                          cursor="arrow")
        bubble.pack(side="left")
        self._scroll_bottom()

    def _add_loading_bubble(self):
        """Temporary loading indicator — returns the frame so it can be removed."""
        row = tk.Frame(self._chat_inner, bg=BG)
        row.pack(fill="x", pady=(4, 0), padx=8)

        tk.Label(row, text="  ...  ",
                 bg=WIDGET, fg=SUBTEXT,
                 font=("Segoe UI", 9, "italic"),
                 padx=12, pady=8, relief="flat").pack(side="left")
        self._scroll_bottom()
        return row

    def _remove_widget(self, widget):
        widget.destroy()

    def _scroll_bottom(self):
        self._canvas.update_idletasks()
        self._canvas.yview_moveto(1.0)

    def _clear_chat(self):
        for w in self._chat_inner.winfo_children():
            w.destroy()

    # ── Actions ─────────────────────────────────────────────────────────────────

    def _send(self):
        app = self._app
        if not app.check_ready():
            return
        user_says = self._input.get().strip()
        if not user_says:
            messagebox.showwarning("Input Kosong", "Isi kolom User Says terlebih dahulu.")
            return

        self._input.delete(0, "end")
        self._send_btn.config(state="disabled")
        self._reset_btn.config(state="disabled")

        self._add_user_bubble(user_says)
        loading = self._add_loading_bubble()

        cookie_str = app._cookie_str
        view_state = app._view_state

        def _worker():
            result = call_bot_api(cookie_str, view_state, user_says)
            app.after(0, self._on_done, result, loading)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_done(self, result, loading):
        self._remove_widget(loading)
        self._add_bot_bubble(result["dialog"], result["score"])
        self._send_btn.config(state="normal")
        self._reset_btn.config(state="normal")
        self._input.focus_set()

    def _reset_session(self):
        app = self._app
        if not app.check_ready():
            return
        self._reset_btn.config(state="disabled")
        self._send_btn.config(state="disabled")
        app.session_bar.set_progress("Sesi sedang di Reset...")

        cookie_str = app._cookie_str
        view_state = app._view_state

        def _worker():
            for reset_word in ("menu", "batal"):
                call_bot_api(cookie_str, view_state, reset_word)
            app.after(0, _done)

        def _done():
            self._clear_chat()
            self._reset_btn.config(state="disabled")
            self._send_btn.config(state="normal")
            app.session_bar.set_progress("✓  Sesi berhasil direset. Chat baru telah terbuka.")

        threading.Thread(target=_worker, daemon=True).start()
