"""
ui/views/manual_tab.py — Manual bot test tab
Single input → chat bubble history (user right, bot left).
"""

import math
import re
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox
import customtkinter as ctk

from ui.constants import PANEL, WIDGET, TEXT, SUBTEXT, BORDER
from ui.constants import ACCENT, ACCENT_D
from ui.constants import BTN_ACCENT, BTN_WARNING
from ui.constants import FONT

BUBBLE_USER   = "#03AC0E"   # green — pesan user
BUBBLE_BOT    = "#EEF1F8"   # soft blue-gray — balasan bot
BUBBLE_FOOTER = "#F5F5F5"   # abu lebih terang — footer score
BUBBLE_RADIUS  = 14
BUBBLE_MAX_W   = 460         # pixel maks lebar bubble
FONT_CHAT      = ("SF Pro", 10)
FONT_CHAT_FOOTER = ("Segoe UI", 10)


_PLACEHOLDER_RE = re.compile(r'\{[^{}]+\}')

def _fill_placeholders(text: str) -> str:
    """Ganti semua {placeholder} dengan 'Bot Tester'."""
    return _PLACEHOLDER_RE.sub("Bot Tester", text)


def _parse_replies(text: str):
    """
    Parse {replies:title=...,button=...,Name@===@payload@===@desc,...}
    Returns dict {title, button, options: [(name, desc), ...]} or None.
    """
    t = text.strip()
    if not (t.startswith("{replies:") and t.endswith("}")):
        return None
    body = t[9:-1]   # strip {replies: … }

    title_m  = re.search(r"title=([^,]*)", body)
    button_m = re.search(r"button=([^,]*)", body)
    title        = title_m.group(1).strip()  if title_m  else ""
    button_label = button_m.group(1).strip() if button_m else ""

    options = []
    for m in re.finditer(r"([^,@\n]+)@===@[^@]*@===@([^,}]*)", body):
        name = m.group(1).strip()
        desc = m.group(2).strip()
        if name:
            options.append((name, desc))

    return {"title": title, "button": button_label, "options": options}


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

        self._send_btn = ctk.CTkButton(input_frame, text="▷ Kirim",
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

    # ── Canvas / scroll helpers ───────────────────────────────────────────────────

    def _on_inner_configure(self, *_):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, e):
        self._canvas.itemconfig(self._chat_win, width=e.width)

    def _on_mousewheel(self, e):
        self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def _bind_scroll(self, widget):
        """Bind mousewheel ke semua children. tk.Text di-override agar tidak scroll sendiri."""
        if isinstance(widget, tk.Text):
            widget.bind("<MouseWheel>",
                        lambda e: self._canvas.yview_scroll(
                            int(-1 * (e.delta / 120)), "units"),
                        add="+")
        else:
            widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        for child in widget.winfo_children():
            self._bind_scroll(child)

    # ── Bubble helpers ────────────────────────────────────────────────────────────

    _BPADX = 10   # padding horizontal teks dalam bubble
    _BPADY = 7    # padding vertikal teks dalam bubble

    def _make_bubble(self, parent, text: str, bg: str, fg: str, side: str):
        """
        tk.Frame (auto-size persis mengikuti konten) + tk.Text (selectable).
        Ukuran dihitung sebelum render — tidak bergantung pada timing layout.
        """
        f       = tkfont.Font(family=FONT_CHAT[0], size=FONT_CHAT[1])
        char0_w = max(1, f.measure("0"))

        # ── Lebar bubble: shrink ke konten, maks BUBBLE_MAX_W ────────────
        max_line_px = max((f.measure(ln) for ln in text.split("\n")), default=40)
        bubble_px   = min(BUBBLE_MAX_W, max_line_px + self._BPADX * 2 + 8)
        inner_px    = max(40, bubble_px - self._BPADX * 2)
        width_chars = max(4, inner_px // char0_w)

        # ── Tinggi: hitung baris yang akan terbungkus ─────────────────────
        total_lines = 0
        for line in text.split("\n"):
            line_px = f.measure(line) if line else 0
            total_lines += max(1, math.ceil(line_px / inner_px))

        # ── Widget ────────────────────────────────────────────────────────
        # tk.Frame (bukan CTkFrame) agar auto-size tepat — tidak ada default 200px
        outer = tk.Frame(parent, bg=bg)
        outer.pack(side=side, padx=4, pady=2)

        t = tk.Text(
            outer,
            bg=bg, fg=fg, font=FONT_CHAT,
            relief="flat", bd=0, highlightthickness=0,
            wrap="word", cursor="xterm",
            width=width_chars, height=total_lines,
            padx=self._BPADX, pady=self._BPADY,
            spacing1=2, spacing2=2,
            selectbackground="#B2D8FF", selectforeground=fg,
            insertwidth=0,
        )
        if side == "right":
            t.tag_configure("r", justify="right")
            t.insert("1.0", text, "r")
        else:
            t.insert("1.0", text)
        t.configure(state="disabled")
        t.pack()

        self._bind_scroll(outer)
        return outer

    # ── Replies popup bubble ──────────────────────────────────────────────────────

    def _add_replies_bubbles(self, title: str, button_label: str, options: list):
        """Bubble toggle: compact ↔ expanded list, inline di chat, lebar sama."""
        f       = tkfont.Font(family=FONT_CHAT[0], size=FONT_CHAT[1])
        char0_w = max(1, f.measure("0"))
        btn_full = f"≡  {button_label}"

        def _bubble_px(text):
            max_lx = max((f.measure(ln) for ln in text.split("\n")), default=40)
            return min(BUBBLE_MAX_W, max(80, max_lx + self._BPADX * 2 + 8))

        # Lebar bubble disamakan antara title dan button (sama seperti _make_bubble)
        shared_px   = max(_bubble_px(title), _bubble_px(btn_full)) if title else _bubble_px(btn_full)
        inner_px    = max(40, shared_px - self._BPADX * 2)
        width_chars = max(4, inner_px // char0_w)

        FONT_ITEM_NAME = (FONT_CHAT[0], FONT_CHAT[1] - 1, "bold")
        FONT_ITEM_DESC = (FONT_CHAT[0], FONT_CHAT[1] - 1)

        # ── Bubble 1: teks judul ──────────────────────────────────────────────
        if title:
            row = tk.Frame(self._chat_inner, bg=PANEL)
            row.pack(fill="x", pady=(4, 0), padx=12)
            self._make_bubble(row, title, BUBBLE_BOT, TEXT, "left")
            self._bind_scroll(row)

        # ── Row untuk kedua state ─────────────────────────────────────────────
        row_btn = tk.Frame(self._chat_inner, bg=PANEL)
        row_btn.pack(fill="x", pady=(0, 0), padx=12)

        # ── State COMPACT — tk.Text sama seperti bubble biasa ─────────────────
        compact = tk.Frame(row_btn, bg=BUBBLE_BOT)
        compact.pack(side="left", padx=4, pady=2)

        t_c = tk.Text(compact, bg=BUBBLE_BOT, fg=BUBBLE_USER,
                      font=(*FONT_CHAT, "bold"),
                      relief="flat", bd=0, highlightthickness=0,
                      wrap="word", cursor="hand2",
                      width=width_chars, height=1,
                      padx=self._BPADX, pady=self._BPADY,
                      selectbackground="#B2D8FF", selectforeground=BUBBLE_USER,
                      insertwidth=0)
        t_c.tag_configure("c", justify="center")
        t_c.insert("1.0", btn_full, "c")
        t_c.configure(state="disabled")
        t_c.pack()

        # ── State EXPANDED — lebar tepat = compact_px, belum di-pack ──────────
        # compact_px = lebar persis widget tk.Text di compact state
        compact_px = width_chars * char0_w + 2 * self._BPADX
        expanded   = tk.Frame(row_btn, bg=BUBBLE_BOT)

        # Spacer tersembunyi: paksa expanded frame selebar persis compact bubble
        spacer = tk.Frame(expanded, bg=BUBBLE_BOT, width=compact_px, height=0)
        spacer.pack_propagate(False)
        spacer.pack(anchor="w")

        # Header — label fill="x" saja; ✕ di-place agar tidak memperlebar frame
        hdr = tk.Frame(expanded, bg=ACCENT)
        hdr.pack(fill="x")
        tk.Label(hdr, text=btn_full, bg=ACCENT, fg="#ffffff",
                 font=FONT_CHAT, anchor="w",
                 padx=self._BPADX,
                 pady=self._BPADY).pack(fill="x")

        def _collapse(*_):
            expanded.pack_forget()
            compact.pack(side="left", padx=4, pady=2)
            self._bind_scroll(row_btn)
            self._canvas.update_idletasks()

        close_btn = tk.Button(hdr, text="✕", bg=ACCENT, fg="#ffffff",
                              bd=0, relief="flat", cursor="hand2",
                              activebackground=ACCENT_D, activeforeground="#ffffff",
                              font=FONT_CHAT, command=_collapse)
        # place() tidak mempengaruhi ukuran frame induk
        close_btn.place(relx=1.0, rely=0.5, anchor="e", x=-6)

        # Opsi — fill="x" mengikuti lebar spacer, wraplength untuk teks panjang
        for i, (name, desc) in enumerate(options):
            ibg  = WIDGET if i % 2 == 0 else PANEL
            item = tk.Frame(expanded, bg=ibg)
            item.pack(fill="x")
            tk.Label(item, text=name, bg=ibg, fg=TEXT,
                     font=FONT_ITEM_NAME, anchor="w",
                     wraplength=inner_px).pack(anchor="w", fill="x",
                                               padx=self._BPADX, pady=(5, 0))
            if desc:
                tk.Label(item, text=desc, bg=ibg, fg=SUBTEXT,
                         font=FONT_ITEM_DESC, anchor="w",
                         wraplength=inner_px, justify="left").pack(
                             anchor="w", fill="x",
                             padx=self._BPADX, pady=(0, 5))
            else:
                item.pack_configure(pady=3)

        def _expand(*_):
            compact.pack_forget()
            expanded.pack(side="left", padx=4, pady=2)
            self._bind_scroll(row_btn)
            self._canvas.update_idletasks()

        t_c.bind("<Button-1>", _expand)
        compact.bind("<Button-1>", _expand)

        self._bind_scroll(row_btn)
        self._scroll_bottom()

    # ── Bubble builders ───────────────────────────────────────────────────────────

    def _add_user_bubble(self, text: str):
        row = tk.Frame(self._chat_inner, bg=PANEL)
        row.pack(fill="x", pady=(6, 0), padx=12)
        self._make_bubble(row, text, BUBBLE_USER, "#ffffff", "right")
        self._bind_scroll(row)
        self._scroll_bottom()

    def _add_bot_bubble(self, messages: list, dialog: str, score: str):
        for msg in messages:
            replies = _parse_replies(msg)
            if replies:
                # Terapkan placeholder replacement pada bagian teks yang tampil
                self._add_replies_bubbles(
                    _fill_placeholders(replies["title"]),
                    _fill_placeholders(replies["button"]),
                    [(_fill_placeholders(n), _fill_placeholders(d))
                     for n, d in replies["options"]])
            else:
                row = tk.Frame(self._chat_inner, bg=PANEL)
                row.pack(fill="x", pady=(4, 0), padx=12)
                self._make_bubble(row, _fill_placeholders(msg), BUBBLE_BOT, TEXT, "left")
                self._bind_scroll(row)

        # ── Footer satu baris: Dialog | Score ──────────────────────────────
        parts = []
        if dialog:
            parts.append(f"  {dialog}")
        if score:
            parts.append(f"{score}")
        footer_text = "    |    ".join(parts) if parts else "(tidak ada balasan)"

        row_f = tk.Frame(self._chat_inner, bg=PANEL)
        row_f.pack(fill="x", pady=(2, 8), padx=12)
        ctk.CTkLabel(
            row_f, text=footer_text,
            fg_color=BUBBLE_FOOTER, text_color=SUBTEXT,
            font=FONT_CHAT_FOOTER, corner_radius=8, anchor="w",
        ).pack(side="left", padx=4, ipadx=8, ipady=4)
        self._bind_scroll(row_f)
        self._scroll_bottom()

    def _add_loading_bubble(self):
        row = tk.Frame(self._chat_inner, bg=PANEL)
        row.pack(fill="x", pady=(4, 0), padx=12)
        ctk.CTkLabel(row, text="  ✵ Loading...  ",
                     fg_color=WIDGET, text_color=SUBTEXT,
                     font=(*FONT_CHAT, "italic"),
                     corner_radius=BUBBLE_RADIUS).pack(side="left", padx=4, pady=2)
        self._bind_scroll(row)
        self._scroll_bottom()
        return row

    def _scroll_bottom(self):
        self._canvas.update_idletasks()
        self._canvas.yview_moveto(1.0)

    def _clear_chat(self):
        for w in self._chat_inner.winfo_children():
            w.destroy()
        self._canvas.update_idletasks()
        self._canvas.yview_moveto(0.0)

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
        self._add_bot_bubble(
            result.get("messages", []),
            result["dialog"],
            result["score"],
        )
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
