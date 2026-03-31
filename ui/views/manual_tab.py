"""
ui/views/manual_tab.py — Manual bot test tab
Single input → chat bubble history (user right, bot left).
"""

import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from ui.constants import PANEL, WIDGET, TEXT, SUBTEXT, BORDER
from ui.constants import BTN_ACCENT, BTN_WARNING
from ui.constants import FONT, FONT_SMALL

BUBBLE_USER = "#03AC0E"   # Tokopedia green — pesan terkirim
BUBBLE_BOT  = "#EEF1F8"   # soft blue-gray — balasan bot
FONT_CHAT   = ("Segoe UI", 10)


class ManualTab(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self._app = app
        self.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self._build()

    def _build(self):
        # ── Row 0: Input ──────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Kirim Chat/Trigger",
                     fg_color="transparent",
                     text_color=TEXT,
                     font=FONT).grid(row=0, column=0, sticky="w",
                                     padx=(14, 0), pady=(14, 0))

        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=0, column=1, columnspan=2, sticky="ew",
                         padx=(10, 14), pady=(14, 0))
        input_frame.columnconfigure(0, weight=1)

        self._input = ctk.CTkEntry(input_frame, font=FONT,
                                   fg_color=WIDGET, text_color=TEXT,
                                   border_color=BORDER, border_width=1)
        self._input.grid(row=0, column=0, sticky="ew", ipady=2)
        self._input.bind("<Return>", lambda *_: self._send())

        self._send_btn = ctk.CTkButton(input_frame, text="▶  Send",
                                       command=self._send, **BTN_ACCENT)
        self._send_btn.grid(row=0, column=1, padx=(8, 0))

        self._reset_btn = ctk.CTkButton(input_frame, text="↩  BATAL (Sesi Chat Baru)",
                                        command=self._reset_session,
                                        state="disabled",
                                        **BTN_WARNING)
        self._reset_btn.grid(row=0, column=2, padx=(6, 0))

        # ── Row 1: Separator ──────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=BORDER,
                     corner_radius=0).grid(row=1, column=0, columnspan=3,
                                           sticky="ew", pady=(14, 0), padx=14)

        # ── Row 2: Chat area ──────────────────────────────────────────────────
        chat_outer = tk.Frame(self, bg=PANEL)
        chat_outer.grid(row=2, column=0, columnspan=3, sticky="nsew",
                        pady=(10, 10), padx=14)
        chat_outer.columnconfigure(0, weight=1)
        chat_outer.rowconfigure(0, weight=1)

        self._canvas = tk.Canvas(chat_outer, bg=PANEL, highlightthickness=0,
                                 bd=0, relief="flat")
        self._canvas.grid(row=0, column=0, sticky="nsew")

        _sb = ctk.CTkScrollbar(chat_outer, command=self._canvas.yview,
                                fg_color=PANEL, button_color=WIDGET,
                                button_hover_color=BORDER)
        _sb.grid(row=0, column=1, sticky="ns")
        self._canvas.configure(yscrollcommand=_sb.set)

        self._chat_inner = tk.Frame(self._canvas, bg=PANEL)
        self._chat_win = self._canvas.create_window(
            (0, 0), window=self._chat_inner, anchor="nw")

        self._chat_inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._chat_inner.bind("<MouseWheel>", self._on_mousewheel)

    # ── Chat helpers ─────────────────────────────────────────────────────────────

    def _on_inner_configure(self, *_):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, e):
        self._canvas.itemconfig(self._chat_win, width=e.width)

    def _on_mousewheel(self, e):
        self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def _bind_scroll(self, widget):
        """Bind mousewheel recursively to all children so scroll works anywhere."""
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        for child in widget.winfo_children():
            self._bind_scroll(child)

    def _add_user_bubble(self, text: str):
        row = tk.Frame(self._chat_inner, bg=PANEL)
        row.pack(fill="x", pady=(6, 0), padx=8)

        tk.Label(row, text=text,
                 bg=BUBBLE_USER, fg="#ffffff",
                 font=FONT_CHAT,
                 wraplength=380, justify="left",
                 padx=12, pady=8, relief="flat").pack(side="right")
        self._bind_scroll(row)
        self._scroll_bottom()

    def _add_bot_bubble(self, dialog: str, score: str):
        row = tk.Frame(self._chat_inner, bg=PANEL)
        row.pack(fill="x", pady=(4, 0), padx=8)

        bubble = tk.Frame(row, bg=BUBBLE_BOT, padx=12, pady=8)
        bubble.pack(side="left")

        tk.Label(bubble, text="Dialog:", bg=BUBBLE_BOT, fg=TEXT,
                 font=(*FONT_CHAT, "bold"), justify="left").pack(anchor="w")
        tk.Label(bubble, text=dialog, bg=BUBBLE_BOT, fg=TEXT,
                 font=FONT_CHAT, justify="left", wraplength=380).pack(anchor="w")

        if score:
            tk.Label(bubble, text="Score:", bg=BUBBLE_BOT, fg=TEXT,
                     font=(*FONT_CHAT, "bold"), justify="left").pack(anchor="w", pady=(8, 0))
            tk.Label(bubble, text=score, bg=BUBBLE_BOT, fg=TEXT,
                     font=FONT_CHAT, justify="left", wraplength=380).pack(anchor="w")

        self._bind_scroll(row)
        self._scroll_bottom()

    def _add_loading_bubble(self):
        row = tk.Frame(self._chat_inner, bg=PANEL)
        row.pack(fill="x", pady=(4, 0), padx=8)

        tk.Label(row, text="  ...  ",
                 bg=WIDGET, fg=SUBTEXT,
                 font=(*FONT_CHAT, "italic"),
                 padx=12, pady=8, relief="flat").pack(side="left")
        self._bind_scroll(row)
        self._scroll_bottom()
        return row

    def _scroll_bottom(self):
        self._canvas.update_idletasks()
        self._canvas.yview_moveto(1.0)

    def _clear_chat(self):
        for w in self._chat_inner.winfo_children():
            w.destroy()

    # ── Actions ──────────────────────────────────────────────────────────────────

    def _send(self):
        app = self._app
        if not app.check_ready():
            return
        user_says = self._input.get().strip()
        if not user_says:
            messagebox.showwarning("Input Kosong", "Isi kolom Chat/Trigger terlebih dahulu.")
            return

        self._input.delete(0, "end")
        self._send_btn.configure(state="disabled")
        self._reset_btn.configure(state="disabled")

        self._add_user_bubble(user_says)
        loading = self._add_loading_bubble()

        cookie_str = app._cookie_str
        view_state = app._view_state

        def _worker():
            result = call_bot_api(cookie_str, view_state, user_says)
            app.after(0, self._on_done, result, loading)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_done(self, result, loading):
        loading.destroy()
        self._add_bot_bubble(result["dialog"], result["score"])
        self._send_btn.configure(state="normal")
        self._reset_btn.configure(state="normal")
        self._input.focus_set()

    def _reset_session(self):
        app = self._app
        if not app.check_ready():
            return
        self._reset_btn.configure(state="disabled")
        self._send_btn.configure(state="disabled")
        app.session_bar.set_progress("Sesi sedang di Reset...")

        cookie_str = app._cookie_str
        view_state = app._view_state

        def _worker():
            for reset_word in ("menu", "batal"):
                call_bot_api(cookie_str, view_state, reset_word)
            app.after(0, _done)

        def _done():
            self._reset_btn.configure(state="normal")
            self._send_btn.configure(state="normal")
            self._clear_chat()
            app.session_bar.set_progress("✓  Sesi berhasil direset. Chat baru telah terbuka.")

        threading.Thread(target=_worker, daemon=True).start()


from ui.api import call_bot_api  # noqa: E402 — avoid circular at module level
