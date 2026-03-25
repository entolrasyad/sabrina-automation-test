"""
ui/views/session_bar.py — Credential status bar (top section)
Shows credential state, login/logout buttons, and progress messages.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from pages.dashboard_page import DashboardPage
from ui.constants import PANEL, TEXT, SUBTEXT, SUCCESS, DANGER
from ui.api import selenium_login
from config import credential_manager
from ui.views.credentials_dialog import CredentialsDialog


class SessionBar(ttk.LabelFrame):

    def __init__(self, parent, app):
        super().__init__(parent, text="  ⚙  Sabrina BOT Tester",
                         padding=(13, 8), style="TLabelframe")
        self._app = app
        self.columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        inner = ttk.Frame(self, style="Panel.TFrame")
        inner.grid(row=0, column=0, sticky="ew")
        inner.columnconfigure(0, weight=1)

        self._cred_label = ttk.Label(inner, text="",
                                     font=("Segoe UI", 10, "bold"),
                                     style="Panel.TLabel")
        self._cred_label.grid(row=0, column=0, sticky="w")

        # ── Kanan: credential buttons (kiri→kanan: Login, Logout, Edit) ──────────
        btn_frame = ttk.Frame(inner, style="Panel.TFrame")
        btn_frame.grid(row=0, column=1, sticky="e")

        self._login_btn = ttk.Button(btn_frame,
                                     text="⚡  Login & Get Credentials",
                                     command=self._start_login,
                                     style="Accent.TButton")
        self._login_btn.pack(side="left", padx=(0, 6))

        self._logout_btn = ttk.Button(btn_frame,
                                      text="⏏  Logout",
                                      command=self._start_logout,
                                      style="Danger.TButton",
                                      state="disabled")
        self._logout_btn.pack(side="left", padx=(0, 6))

        ttk.Button(btn_frame,
                   text="✏  Edit Credentials",
                   command=self._open_credentials_dialog,
                   style="Ghost.TButton").pack(side="left")

        # ── Row 1: progress ─────────────────────────────────────────────────────
        self._progress_var = tk.StringVar(value="Belum ada credentials. Klik Login.")
        ttk.Label(self, textvariable=self._progress_var,
                  style="Panel.Sub.TLabel").grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.refresh()
        if not credential_manager.exists():
            self._app.after(300, self._open_credentials_dialog_firstrun)

    # ── Public Interface ────────────────────────────────────────────────────────

    def refresh(self):
        """Update credential status indicator and button states."""
        app = self._app
        ready = bool(app._cookie_str and app._view_state)
        if ready:
            self._cred_label.config(text="  ●  Credential READY", foreground=SUCCESS)
            self._login_btn.config(text="↺  Refresh Credentials")
            self._logout_btn.config(state="normal")
        else:
            self._cred_label.config(text="  ●  Credential NOT READY", foreground=DANGER)
            self._login_btn.config(text="⚡  Login & Get Credentials")
            self._logout_btn.config(state="disabled")

        # Propagate to views that have reset buttons
        if hasattr(app, "manual_tab") and hasattr(app.manual_tab, "_reset_btn"):
            state = "normal" if ready else "disabled"
            app.manual_tab._reset_btn.config(state=state)

    def set_progress(self, msg: str):
        self._progress_var.set(f"›  {msg}")

    # ── Login ───────────────────────────────────────────────────────────────────

    def _start_login(self):
        app = self._app
        self._login_btn.config(state="disabled")
        self._logout_btn.config(state="disabled")

        old_driver       = app._driver
        app._driver      = None
        app._cookie_str  = ""
        app._view_state  = ""
        self.refresh()

        def _progress(msg):
            app.after(0, self.set_progress, msg)

        def _done(driver, cookie_str, view_state):
            app.after(0, self._on_login_done, driver, cookie_str, view_state)

        def _error(msg):
            app.after(0, self._on_login_error, msg)

        def _worker():
            if old_driver:
                _progress("Logout sesi sebelumnya...")
                try:
                    DashboardPage(old_driver).logout()
                except Exception:
                    pass
                finally:
                    try:
                        old_driver.quit()
                    except Exception:
                        pass
            selenium_login(_progress, _done, _error)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_login_done(self, driver, cookie_str, view_state):
        app = self._app
        app._driver      = driver
        app._cookie_str  = cookie_str
        app._view_state  = view_state
        self.refresh()
        self.set_progress("Login berhasil. Credentials siap dipakai.")
        self._login_btn.config(state="normal")

    def _on_login_error(self, msg):
        self.set_progress(f"Login gagal: {msg}")
        self._login_btn.config(state="normal")
        self.refresh()
        messagebox.showerror("Login Error", msg)

    # ── Logout ──────────────────────────────────────────────────────────────────

    def _start_logout(self):
        app = self._app
        if not app._driver:
            return
        self._logout_btn.config(state="disabled")
        self._login_btn.config(state="disabled")
        self.set_progress("Logout...")

        driver          = app._driver
        app._driver     = None
        app._cookie_str = ""
        app._view_state = ""
        self.refresh()

        def _worker():
            try:
                DashboardPage(driver).logout()
            except Exception:
                pass
            finally:
                try:
                    driver.quit()
                except Exception:
                    pass
            app.after(0, self._on_logout_done)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_logout_done(self):
        self.set_progress("Logout berhasil.")
        self._login_btn.config(state="normal")

    # ── Credentials Dialog ───────────────────────────────────────────────────

    def _open_credentials_dialog(self):
        def _on_save(username, password):
            self.set_progress(f"✓  Credentials disimpan untuk: {username}")

        CredentialsDialog(self._app, on_save=_on_save, force=False)

    def _open_credentials_dialog_firstrun(self):
        def _on_save(username, password):
            self.set_progress(f"✓  Credentials disimpan. Silakan klik Login.")

        CredentialsDialog(self._app, on_save=_on_save, force=True)

