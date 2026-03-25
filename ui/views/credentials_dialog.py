"""
ui/views/credentials_dialog.py
Dialog form untuk input / edit username & password.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from config import credential_manager
from ui.constants import PANEL, WIDGET, TEXT, SUBTEXT, BORDER


class CredentialsDialog(tk.Toplevel):
    """
    Modal dialog untuk mengisi atau mengedit credentials.
    force=True → tidak bisa ditutup tanpa mengisi (first-run).
    """

    def __init__(self, parent, on_save=None, force: bool = False):
        super().__init__(parent)
        self._on_save = on_save
        self._force   = force

        self.title("Edit Credentials")
        self.configure(bg=PANEL)
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
        root = tk.Frame(self, bg=PANEL, padx=28, pady=20)
        root.pack(fill="both", expand=True)

        # ── Header ─────────────────────────────────────────────────────────────
        tk.Label(root,
                 text="Login Credentials",
                 bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")

        tk.Label(root,
                 text="Masukkan username & password akun Sabrina Dev.",
                 bg=PANEL, fg=SUBTEXT,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 14))

        # ── Username ───────────────────────────────────────────────────────────
        tk.Label(root, text="Username",
                 bg=PANEL, fg=SUBTEXT,
                 font=("Segoe UI", 8)).pack(anchor="w")

        self._user_var = tk.StringVar()
        self._user_entry = tk.Entry(root,
                                    textvariable=self._user_var,
                                    font=("Segoe UI", 10),
                                    bg=WIDGET, fg=TEXT,
                                    insertbackground=TEXT,
                                    relief="flat", bd=6,
                                    width=36)
        self._user_entry.pack(fill="x", pady=(2, 12))

        # ── Password ───────────────────────────────────────────────────────────
        tk.Label(root, text="Password",
                 bg=PANEL, fg=SUBTEXT,
                 font=("Segoe UI", 8)).pack(anchor="w")

        self._pass_var = tk.StringVar()
        self._pass_entry = tk.Entry(root,
                                    textvariable=self._pass_var,
                                    show="●",
                                    font=("Segoe UI", 10),
                                    bg=WIDGET, fg=TEXT,
                                    insertbackground=TEXT,
                                    relief="flat", bd=6,
                                    width=36)
        self._pass_entry.pack(fill="x", pady=(2, 6))

        # ── Show password ──────────────────────────────────────────────────────
        self._show_pass = tk.BooleanVar(value=False)
        tk.Checkbutton(root,
                       text="Tampilkan password",
                       variable=self._show_pass,
                       command=self._toggle_password,
                       bg=PANEL, fg=SUBTEXT,
                       activebackground=PANEL, activeforeground=TEXT,
                       selectcolor=WIDGET,
                       font=("Segoe UI", 8),
                       relief="flat", bd=0).pack(anchor="w", pady=(0, 18))

        # ── Buttons ────────────────────────────────────────────────────────────
        btn_row = tk.Frame(root, bg=PANEL)
        btn_row.pack(fill="x")

        ttk.Button(btn_row, text="💾  Simpan",
                   command=self._save,
                   style="Accent.TButton").pack(side="right", padx=(6, 0))

        if not self._force:
            ttk.Button(btn_row, text="Batal",
                       command=self._cancel,
                       style="Ghost.TButton").pack(side="right")

        # ── Pre-fill ───────────────────────────────────────────────────────────
        creds = credential_manager.load()
        if creds.get("username"):
            self._user_var.set(creds["username"])
        if creds.get("password"):
            self._pass_var.set(creds["password"])

        # ── Key bindings ───────────────────────────────────────────────────────
        self._user_entry.bind("<Return>", lambda _: self._pass_entry.focus_set())
        self._pass_entry.bind("<Return>", lambda _: self._save())
        self._user_entry.focus_set()

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _toggle_password(self):
        self._pass_entry.config(show="" if self._show_pass.get() else "●")

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
