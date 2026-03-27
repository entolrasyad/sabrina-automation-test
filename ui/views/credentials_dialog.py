"""
ui/views/credentials_dialog.py
Dialog form untuk input / edit username & password.
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from config import credential_manager
from ui.constants import PANEL, WIDGET, TEXT, SUBTEXT, BORDER, ACCENT, ACCENT_D
from ui.constants import BTN_ACCENT, BTN_GHOST
from ui.constants import FONT, FONT_BOLD, FONT_SMALL, FONT_LABEL


class CredentialsDialog(ctk.CTkToplevel):
    """
    Modal dialog untuk mengisi atau mengedit credentials.
    force=True → tidak bisa ditutup tanpa mengisi (first-run).
    """

    def __init__(self, parent, on_save=None, force: bool = False):
        super().__init__(parent)
        self._on_save = on_save
        self._force   = force

        self.title("Edit Credentials")
        self.configure(fg_color=PANEL)
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()

        if force:
            self.protocol("WM_DELETE_WINDOW", lambda: None)
        else:
            self.protocol("WM_DELETE_WINDOW", self._cancel)

        self._build()
        self.update_idletasks()
        self._center(parent)

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build(self):
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=28, pady=20)

        # Header
        ctk.CTkLabel(root,
                     text="Login Credentials",
                     fg_color="transparent",
                     text_color=TEXT,
                     font=FONT_BOLD).pack(anchor="w")

        ctk.CTkLabel(root,
                     text="Masukkan username & password akun Sabrina Dev.",
                     fg_color="transparent",
                     text_color=SUBTEXT,
                     font=FONT_SMALL).pack(anchor="w", pady=(2, 14))

        # Username
        ctk.CTkLabel(root, text="Username",
                     fg_color="transparent",
                     text_color=SUBTEXT,
                     font=FONT_LABEL).pack(anchor="w")

        self._user_var = tk.StringVar()
        self._user_entry = ctk.CTkEntry(root,
                                        textvariable=self._user_var,
                                        font=FONT,
                                        fg_color=WIDGET,
                                        text_color=TEXT,
                                        border_color=BORDER)
        self._user_entry.pack(fill="x", pady=(2, 12))

        # Password
        ctk.CTkLabel(root, text="Password",
                     fg_color="transparent",
                     text_color=SUBTEXT,
                     font=FONT_LABEL).pack(anchor="w")

        self._pass_var = tk.StringVar()
        self._pass_entry = ctk.CTkEntry(root,
                                        textvariable=self._pass_var,
                                        show="●",
                                        font=FONT,
                                        fg_color=WIDGET,
                                        text_color=TEXT,
                                        border_color=BORDER)
        self._pass_entry.pack(fill="x", pady=(2, 6))

        # Show password
        self._show_pass = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(root,
                        text="Tampilkan password",
                        variable=self._show_pass,
                        command=self._toggle_password,
                        text_color=SUBTEXT,
                        fg_color=ACCENT,
                        hover_color=ACCENT_D,
                        border_color=BORDER,
                        checkmark_color="#ffffff",
                        font=FONT_SMALL).pack(anchor="w", pady=(0, 18))

        # Buttons
        btn_row = ctk.CTkFrame(root, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(btn_row, text="💾  Simpan",
                      command=self._save,
                      **BTN_ACCENT).pack(side="right", padx=(6, 0))

        if not self._force:
            ctk.CTkButton(btn_row, text="Batal",
                          command=self._cancel,
                          **BTN_GHOST).pack(side="right")

        # Pre-fill
        creds = credential_manager.load()
        if creds.get("username"):
            self._user_var.set(creds["username"])
        if creds.get("password"):
            self._pass_var.set(creds["password"])

        # Key bindings
        self._user_entry.bind("<Return>", lambda _: self._pass_entry.focus_set())
        self._pass_entry.bind("<Return>", lambda _: self._save())
        self._user_entry.focus_set()

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _toggle_password(self):
        self._pass_entry.configure(show="" if self._show_pass.get() else "●")

    def _center(self, parent):
        pw = parent.winfo_x() + parent.winfo_width()  // 2
        ph = parent.winfo_y() + parent.winfo_height() // 2
        w  = self.winfo_reqwidth()
        h  = self.winfo_reqheight()
        self.geometry(f"{w}x{h}+{pw - w // 2}+{ph - h // 2}")

    def _save(self):
        username = self._user_var.get().strip()
        password = self._pass_var.get().strip()

        if not username or not password:
            messagebox.showwarning("Form Tidak Lengkap",
                                   "Username dan Password wajib diisi.",
                                   parent=self)
            return

        credential_manager.save(username, password)
        if self._on_save:
            self._on_save(username, password)
        self.destroy()

    def _cancel(self):
        self.destroy()
