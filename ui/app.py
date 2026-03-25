"""
ui/app.py — Main application window
Owns session state and composes all views.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk

from pages.dashboard_page import DashboardPage
from ui.constants import BG, PANEL, TEXT, ACCENT, ACCENT2
from ui.styles import apply_dark_theme, draw_gradient
from ui.views.session_bar import SessionBar
from ui.views.manual_tab import ManualTab
from ui.views.bulk_tab import BulkTab
from ui.views.update_bar import UpdateBar


class App(tk.Tk):

    EXCEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data.xlsx")

    def __init__(self):
        super().__init__()
        self.title("Dolphin Bot Tester")
        self.resizable(True, True)
        self.configure(bg=BG)
        self.minsize(1150, 680)
        self._center_window(1150, 680)

        apply_dark_theme(self)

        # ── Session state ───────────────────────────────────────────────────────
        self._driver     = None
        self._cookie_str = ""
        self._view_state = ""
        self._cancel     = False

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(50,  lambda: self.bulk_tab.load_excel())
        self.after(100, self._draw_accent_bar)

    # ── Public Helpers ──────────────────────────────────────────────────────────

    def check_ready(self) -> bool:
        """Returns True if credentials are available; shows warning otherwise."""
        from tkinter import messagebox
        if not self._cookie_str or not self._view_state:
            messagebox.showwarning(
                "Credential Belum Siap",
                "Klik Login terlebih dahulu.",
            )
            return False
        return True

    def _center_window(self, w: int, h: int):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - w) // 2
        y  = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── UI Construction ─────────────────────────────────────────────────────────

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # Accent gradient strip
        self._accent_canvas = tk.Canvas(self, height=4, highlightthickness=0, bg=ACCENT)
        self._accent_canvas.grid(row=0, column=0, sticky="ew")
        self._accent_canvas.bind("<Configure>", lambda _e: self._draw_accent_bar())

        # Session bar (row 1)
        self.session_bar = SessionBar(self, self)
        self.session_bar.grid(row=1, column=0, sticky="ew", padx=12, pady=(10, 4))

        # Notebook (row 2)
        nb = ttk.Notebook(self)
        nb.grid(row=2, column=0, sticky="nsew", padx=12, pady=(4, 4))

        self.manual_tab = ManualTab(nb, self)
        nb.add(self.manual_tab, text="  ✏  Manual  ")

        self.bulk_tab = BulkTab(nb, self)
        nb.add(self.bulk_tab, text="  📋  Bulk Excel  ")

        # Update bar (row 3 — bottom)
        self.update_bar = UpdateBar(self, self)
        self.update_bar.grid(row=3, column=0, sticky="ew", padx=12, pady=(2, 8))

    def _draw_accent_bar(self):
        c = self._accent_canvas
        w = c.winfo_width() or 800
        c.delete("all")
        draw_gradient(c, w, 4, ACCENT, ACCENT2)

    # ── Window Close ────────────────────────────────────────────────────────────

    def _on_close(self):
        self._cancel = True
        if self._driver and self._cookie_str:
            self._logout_then_close()
        else:
            if self._driver:
                try:
                    self._driver.quit()
                except Exception:
                    pass
            self.destroy()

    def _logout_then_close(self):
        self._logout_with_overlay(title="Menutup...", on_finish=self.destroy)

    def logout_then_restart(self):
        from ui import updater
        self._logout_with_overlay(title="Update — Restart...", on_finish=updater.restart_app)

    def _logout_with_overlay(self, title: str, on_finish):
        overlay = tk.Toplevel(self)
        overlay.title(title)
        overlay.resizable(False, False)
        overlay.configure(bg=PANEL)
        overlay.grab_set()
        overlay.protocol("WM_DELETE_WINDOW", lambda: None)

        tk.Label(overlay,
                 text="⏏  Sedang logout dari sesi aktif...\n\nMohon tunggu.",
                 bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10),
                 padx=28, pady=20).pack()

        pb = ttk.Progressbar(overlay, mode="indeterminate", length=240)
        pb.pack(padx=28, pady=(0, 24))
        pb.start(10)

        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - overlay.winfo_reqwidth())  // 2
        y = self.winfo_y() + (self.winfo_height() - overlay.winfo_reqheight()) // 2
        overlay.geometry(f"+{x}+{y}")

        driver           = self._driver
        self._driver     = None
        self._cookie_str = ""
        self._view_state = ""

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
            self.after(0, _finish)

        def _finish():
            try:
                overlay.destroy()
            except Exception:
                pass
            on_finish()

        threading.Thread(target=_worker, daemon=True).start()
