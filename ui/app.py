"""
ui/app.py — Main application window
Owns session state and composes all views.
"""

import os
import threading
import tkinter as tk
import customtkinter as ctk

from pages.dashboard_page import DashboardPage
from ui.constants import BG, PANEL, WIDGET, HOVER, TEXT, BORDER, FONT_BOLD
from ui.styles import apply_theme
from ui.views.session_bar import SessionBar
from ui.views.manual_tab import ManualTab
from ui.views.bulk_tab import BulkTab
from ui.views.update_bar import UpdateBar


class App(ctk.CTk):

    EXCEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data.xlsx")

    def __init__(self):
        super().__init__()
        self.title("Dolphin Bot Tester")
        self.resizable(True, True)
        self.configure(fg_color=BG)
        tk.Tk.configure(self, bg=BG)  # sync OS-level window bg agar tidak tembus warna lain
        self._center_window(1150, 720)

        apply_theme()

        # ── Session state ────────────────────────────────────────────────────────
        self._driver     = None
        self._cookie_str = ""
        self._view_state = ""
        self._cancel     = False

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(50, lambda: self.bulk_tab.load_excel())

    # ── Public Helpers ───────────────────────────────────────────────────────────

    def check_ready(self) -> bool:
        from tkinter import messagebox
        if not self._cookie_str or not self._view_state:
            messagebox.showwarning(
                "Credential Belum Siap",
                "Klik Login terlebih dahulu.",
            )
            return False
        return True

    @staticmethod
    def _get_dpi_scale() -> float:
        try:
            import ctypes
            dpi = ctypes.windll.user32.GetDpiForSystem()
            return dpi / 96.0
        except Exception:
            return 1.0

    def _center_window(self, w: int, h: int):
        self.update_idletasks()
        scale = self._get_dpi_scale()
        sw    = self.winfo_screenwidth()
        sh    = self.winfo_screenheight()
        # Kurangi ukuran sesuai scale level
        y_offset = 0
        if scale >= 1.45:    # 150% → langsung fullscreen
            self.after(0, lambda: self.state("zoomed"))
            return
        elif scale >= 1.20:  # 125%
            h = round(h * 0.80)
            y_offset = -80
        x = (sw - round(w * scale)) // 2
        y = max(0, (sh - round(h * scale)) // 2 + y_offset)
        self.minsize(1000, 680)
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── UI Construction ──────────────────────────────────────────────────────────

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)


        # Session bar (row 1)
        self.session_bar = SessionBar(self, self)
        self.session_bar.grid(row=1, column=0, sticky="ew", padx=12, pady=(10, 4))

        # Tabview (row 2)
        tabview = ctk.CTkTabview(
            self,
            fg_color=PANEL,
            border_width=1,
            border_color=BORDER,
            segmented_button_fg_color=BG,
            segmented_button_selected_color=WIDGET,
            segmented_button_selected_hover_color=HOVER,
            segmented_button_unselected_color=BG,
            segmented_button_unselected_hover_color=PANEL,
            text_color=TEXT,
            text_color_disabled=TEXT,
            anchor="w",
        )
        tabview.grid(row=2, column=0, sticky="nsew", padx=12, pady=(4, 4))

        tabview.add("  ✏  Manual  ")
        tabview.add("  📋  Bulk Excel  ")
        tabview._segmented_button.configure(font=FONT_BOLD, height=38)

        self.manual_tab = ManualTab(tabview.tab("  ✏  Manual  "), self)
        self.manual_tab.pack(fill="both", expand=True)

        self.bulk_tab = BulkTab(tabview.tab("  📋  Bulk Excel  "), self)
        self.bulk_tab.pack(fill="both", expand=True)

        # Update bar (row 3 — bottom)
        self.update_bar = UpdateBar(self, self)
        self.update_bar.grid(row=3, column=0, sticky="ew", padx=12, pady=(2, 8))

    # ── Window Close ─────────────────────────────────────────────────────────────

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
        overlay = ctk.CTkToplevel(self)
        overlay.title(title)
        overlay.resizable(False, False)
        overlay.configure(fg_color=PANEL)
        overlay.grab_set()
        overlay.protocol("WM_DELETE_WINDOW", lambda: None)

        ctk.CTkLabel(overlay,
                     text="⏏  Sedang logout dari sesi aktif...\n\nMohon tunggu.",
                     text_color=TEXT,
                     fg_color="transparent",
                     font=("Segoe UI", 10)).pack(padx=28, pady=(20, 8))

        pb = ctk.CTkProgressBar(overlay, mode="indeterminate", width=240)
        pb.pack(padx=28, pady=(0, 24))
        pb.start()

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
