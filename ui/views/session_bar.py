"""
ui/views/session_bar.py — Credential status bar (top section)
Shows credential state, login/logout buttons, and progress messages.
"""

import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from pages.dashboard_page import DashboardPage
from ui.constants import PANEL, WIDGET, SUBTEXT, SUCCESS, DANGER, BORDER
from ui.constants import BTN_ACCENT, BTN_DANGER, BTN_GHOST
from ui.constants import FONT, FONT_BOLD, FONT_SMALL
from ui.api import selenium_login
from config import credential_manager
from ui.views.credentials_dialog import CredentialsDialog


class SessionBar(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=PANEL, corner_radius=10,
                         border_width=1, border_color=BORDER)
        self._app = app
        self.columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(10, 4))
        inner.columnconfigure(0, weight=1)

        self._cred_label = ctk.CTkLabel(inner, text="",
                                        fg_color="transparent",
                                        font=FONT_BOLD)
        self._cred_label.grid(row=0, column=0, sticky="w")

        # Buttons: Login | Logout | Edit Credentials
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        self._login_btn = ctk.CTkButton(btn_frame,
                                        text="⚡  Login",
                                        command=self._start_login,
                                        **BTN_ACCENT)
        self._login_btn.pack(side="left", padx=(0, 6))

        self._logout_btn = ctk.CTkButton(btn_frame,
                                         text="⏏  Logout",
                                         command=self._start_logout,
                                         state="disabled",
                                         **BTN_DANGER)
        self._logout_btn.pack(side="left", padx=(0, 6))

        ctk.CTkButton(btn_frame,
                      text="✏  Edit Credentials",
                      command=self._open_credentials_dialog,
                      **BTN_GHOST).pack(side="left")

        # Row 1: login progress (left) + bulk progress (right)
        self._progress_var = tk.StringVar(value="Belum ada credentials. Klik Login.")
        ctk.CTkLabel(self, textvariable=self._progress_var,
                     fg_color="transparent",
                     text_color=SUBTEXT,
                     font=FONT_SMALL).grid(row=1, column=0, sticky="w",
                                           padx=12, pady=(0, 10))

        bulk_row = ctk.CTkFrame(self, fg_color="transparent")
        bulk_row.grid(row=1, column=1, sticky="e", padx=(0, 12), pady=(0, 10))

        self._bulk_status_var = tk.StringVar(value="")
        ctk.CTkLabel(bulk_row, textvariable=self._bulk_status_var,
                     fg_color="transparent",
                     text_color=SUBTEXT,
                     font=FONT_SMALL).pack(side="left", padx=(0, 8))

        self._bulk_progress = ctk.CTkProgressBar(bulk_row, mode="determinate",
                                                  width=135, height=7,
                                                  fg_color=WIDGET,
                                                  progress_color=SUCCESS)
        self._bulk_progress.set(0)
        self._bulk_progress.pack(side="left")

        self.refresh()
        if not credential_manager.exists():
            self._app.after(300, self._open_credentials_dialog_firstrun)

    # ── Public Interface ─────────────────────────────────────────────────────────

    def refresh(self):
        app = self._app
        ready = bool(app._cookie_str and app._view_state)
        if ready:
            self._cred_label.configure(text="●  Credential READY", text_color=SUCCESS)
            self._login_btn.configure(text="↺  Refresh Credentials")
            self._logout_btn.configure(state="normal")
        else:
            self._cred_label.configure(text="●  Credential NOT READY", text_color=DANGER)
            self._login_btn.configure(text="⚡  Login")
            self._logout_btn.configure(state="disabled")

        if hasattr(app, "manual_tab") and hasattr(app.manual_tab, "_reset_btn"):
            state = "normal" if ready else "disabled"
            app.manual_tab._reset_btn.configure(state=state)

    def set_progress(self, msg: str):
        self._progress_var.set(f"›  {msg}")

    def update_bulk(self, fraction: float, msg: str = ""):
        self._bulk_progress.set(fraction)
        self._bulk_status_var.set(msg)

    # ── Login ────────────────────────────────────────────────────────────────────

    def _start_login(self):
        app = self._app
        self._login_btn.configure(state="disabled")
        self._logout_btn.configure(state="disabled")

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
        self._login_btn.configure(state="normal")

    def _on_login_error(self, msg):
        self.set_progress(f"Login gagal: {msg}")
        self._login_btn.configure(state="normal")
        self.refresh()
        messagebox.showerror("Login Error", msg)

    # ── Logout ───────────────────────────────────────────────────────────────────

    def _start_logout(self):
        app = self._app
        if not app._driver:
            return
        self._logout_btn.configure(state="disabled")
        self._login_btn.configure(state="disabled")
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
        self._login_btn.configure(state="normal")

    # ── Credentials Dialog ────────────────────────────────────────────────────────

    def _open_credentials_dialog(self):
        def _on_save(username, _password):
            self.set_progress(f"✓  Credentials disimpan untuk: {username}")
        CredentialsDialog(self._app, on_save=_on_save, force=False)

    def _open_credentials_dialog_firstrun(self):
        def _on_save(_username, _password):
            self.set_progress("✓  Credentials disimpan. Silakan klik Login.")
        CredentialsDialog(self._app, on_save=_on_save, force=True)
