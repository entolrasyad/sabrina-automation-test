"""
gui.py — Entry point for Dolphin Bot Tester
"""

import sys
import os
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "error.log")

sys.path.insert(0, BASE_DIR)

import customtkinter as ctk
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

# Beritahu Windows bahwa app ini DPI-aware agar tidak di-scale paksa
# Harus dipanggil SEBELUM tkinter window dibuat
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()   # Fallback: system DPI aware
        except Exception:
            pass

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    import atexit
    from pages.dashboard_page import DashboardPage
    from ui.app import App

    if __name__ == "__main__":
        # Hapus log lama jika ada
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
        app = App()

        # Safety net: logout + kill driver jika app crash / close tidak normal
        def _emergency_cleanup():
            driver = app._driver
            if not driver:
                return
            try:
                DashboardPage(driver).logout()
            except Exception:
                pass
            finally:
                try:
                    driver.quit()
                except Exception:
                    pass

        atexit.register(_emergency_cleanup)
        app.mainloop()

except Exception:
    # Tulis error ke file agar bisa dilihat walau pakai pythonw
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        traceback.print_exc(file=f)
    # Tampilkan popup error (tkinter minimal, tidak butuh App)
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Startup Error",
            f"Aplikasi gagal dijalankan.\n\nDetail error tersimpan di:\n{LOG_FILE}"
        )
        root.destroy()
    except Exception:
        pass
