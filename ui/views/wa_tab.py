"""
ui/views/wa_tab.py — Tab WhatsApp
Kirim trigger dari Excel ke WhatsApp Web.
Chrome diembed langsung ke dalam GUI via Win32 window reparenting.
"""

import textwrap
import threading
import time
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

from ui.constants import WIDGET, ROW_ALT, SUBTEXT, PANEL, BG, TEXT, BORDER, SUCCESS, DANGER, ACCENT, ACCENT_D
from ui.constants import BTN_ACCENT, BTN_GHOST
from ui.constants import FONT, FONT_SMALL, FONT_BOLD, FONT_LABEL

BTN_WA = dict(fg_color="#D1FAE5", hover_color="#A7F3D0", text_color=ACCENT_D, font=FONT_BOLD)


class WATab(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self._app          = app
        self._connected    = False
        self._polling      = False
        self._chrome_hwnd  = None
        self._session_id   = 0   # naik setiap kali Buka WhatsApp diklik
        self._raw_triggers: list = []  # teks asli sebelum di-wrap (untuk editor)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build()

    # ── UI ───────────────────────────────────────────────────────────────────────

    def _build(self):
        self._build_toolbar()
        self._build_content()

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(10, 8), padx=14)

        self._wa_btn = ctk.CTkButton(toolbar, text="💬  Buka WhatsApp",
                                     command=self._open_whatsapp, **BTN_WA)
        self._wa_btn.pack(side="left", padx=(0, 6))

        self._status_dot = ctk.CTkLabel(toolbar, text="●",
                                        fg_color="transparent",
                                        text_color=DANGER,
                                        font=FONT_BOLD)
        self._status_dot.pack(side="left", padx=(0, 2))

        self._status_var = tk.StringVar(value="Belum terhubung, silahkan klik tombol 'Buka WhatsApp'")
        ctk.CTkLabel(toolbar, textvariable=self._status_var,
                     fg_color="transparent",
                     text_color=SUBTEXT,
                     font=FONT).pack(side="left", padx=(0, 14))

        # Environment selector — float kanan
        self._env = "dev"  # "dev" | "prod"

        self._env_prod_btn = ctk.CTkButton(toolbar, text="Prod",
                                           width=56, command=lambda: self._set_env("prod"),
                                           state="disabled", **BTN_GHOST)
        self._env_prod_btn.pack(side="right", padx=(4, 0))

        self._env_dev_btn = ctk.CTkButton(toolbar, text="Dev",
                                          width=56, command=lambda: self._set_env("dev"),
                                          state="disabled", **BTN_GHOST)
        self._env_dev_btn.pack(side="right", padx=(4, 0))

        ctk.CTkLabel(toolbar, text="Whatsapp Sabrina :",
                     fg_color="transparent",
                     text_color=SUBTEXT,
                     font=FONT).pack(side="right", padx=(0, 8))

        ctk.CTkFrame(toolbar, fg_color=BORDER, width=1,
                     height=24).pack(side="right", padx=(0, 14))


    # Nomor tujuan per environment (tanpa '+' atau '0' awal — format internasional)
    _ENV_PHONES = {
        "dev":  "8111440177",           # TODO: isi nomor Sabrina Dev
        "prod": "8121214017", # Sabrina Prod
    }

    _CSS_CHAT_NAV = 'button[aria-label="Chats"][data-navbar-item="true"]'
    _CSS_SEARCH = (
        'input[role="textbox"][data-tab="3"],'
        'input[aria-label="Search or start a new chat"],'
        'input[placeholder="Search or start a new chat"]'
    )

    def _set_env(self, env: str):
        """Toggle tampilan tombol Dev/Prod; buka room chat jika sudah connected."""
        self._env = env
        self._apply_env_visual(env)
        if self._connected:
            self._open_chat_room(env)

    def _apply_env_visual(self, env: str):
        """Hanya update tampilan tombol tanpa trigger room opening."""
        if env == "dev":
            self._env_dev_btn.configure(**BTN_ACCENT)
            self._env_prod_btn.configure(**BTN_GHOST)
        else:
            self._env_dev_btn.configure(**BTN_GHOST)
            self._env_prod_btn.configure(**BTN_ACCENT)

    def _open_chat_room(self, env: str):
        phone = self._ENV_PHONES.get(env, "")
        if not phone or not self._app._wa_driver:
            return
        self._status_dot.configure(text_color=SUBTEXT)
        self._status_var.set(f"Membuka chat Sabrina {env.upper()}...")
        self._env_dev_btn.configure(state="disabled", **BTN_GHOST)
        self._env_prod_btn.configure(state="disabled", **BTN_GHOST)
        self._send_btn.configure(state="disabled")
        threading.Thread(target=self._open_chat_worker,
                         args=(env, phone), daemon=True).start()

    def _open_chat_worker(self, env: str, phone: str):
        driver  = self._app._wa_driver
        wait    = WebDriverWait(driver, 15)
        success = False
        try:
            # Pastikan panel Chats aktif sebelum search
            try:
                chat_nav = driver.find_element(By.CSS_SELECTOR, self._CSS_CHAT_NAV)
                chat_nav.click()
                time.sleep(0.3)
            except Exception:
                pass
            search = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, self._CSS_SEARCH)))
            search.click()
            search.send_keys(Keys.CONTROL + "a")
            search.send_keys(phone)
            time.sleep(1.0)
            search.send_keys(Keys.ARROW_DOWN)
            time.sleep(0.5)
            focused = driver.find_element(
                By.CSS_SELECTOR, '[aria-selected="true"]')
            focused.click()
            # Validasi: tunggu input pesan muncul — tanda room chat sudah terbuka
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
                'div[aria-label="Type a message"],'
                'div[contenteditable="true"][data-tab="10"],'
                'footer div[contenteditable="true"]')))
            success = True
            # Sembunyikan panel kiri: klik New Chat → New Community
            try:
                driver.find_element(
                    By.CSS_SELECTOR, 'button[data-tab="2"][aria-label="New chat"]').click()
                time.sleep(0.4)
                driver.find_element(
                    By.CSS_SELECTOR, 'div[aria-label="New community"][role="button"]').click()
            except Exception:
                pass
            self._app.after(0, lambda: self._status_var.set(
                f"Chat Sabrina {env.capitalize()} Terbuka"))
        except TimeoutException:
            self._app.after(0, lambda: self._status_var.set(
                f"Kontak Sabrina {env.capitalize()} tidak ditemukan"))
        except Exception as e:
            msg = str(e)
            self._app.after(0, lambda: self._status_var.set(f"⚠  Gagal: {msg}"))
        finally:
            self._app.after(0, self._env_dev_btn.configure, {"state": "normal"})
            self._app.after(0, self._env_prod_btn.configure, {"state": "normal"})
            # Accent hanya muncul jika room benar-benar terbuka (validasi input pesan)
            if success:
                self._app.after(0, self._apply_env_visual, env)
            self._app.after(0, self._refresh_send_btn)

    # chars yg muat di kolom trigger (320px, Segoe UI 8pt ≈ 5.9px/char @ 100% DPI)
    _WRAP_CHARS = 54

    def _build_content(self):
        content = tk.Frame(self, bg=PANEL, highlightthickness=0, bd=0)
        content.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        content.columnconfigure(0, minsize=370)
        content.columnconfigure(2, weight=1)
        content.rowconfigure(0, weight=1)

        # Style khusus WA tab agar rowheight-nya bisa diubah tanpa
        # mempengaruhi treeview di tab Bulk
        _s = ttk.Style()
        _tree_opts    = dict(_s.configure("Treeview")         or {})
        _heading_opts = dict(_s.configure("Treeview.Heading") or {})
        _tree_opts["font"]    = ("Segoe UI", 8)
        _heading_opts["font"] = ("Segoe UI", 8, "bold")
        _s.configure("WA.Treeview",        **_tree_opts)
        _s.configure("WA.Treeview.Heading", **_heading_opts)
        _s.layout("WA.Treeview", _s.layout("Treeview"))
        _s.map("WA.Treeview",
               background=_s.map("Treeview", "background"),
               foreground=_s.map("Treeview", "foreground"))

        # ── Kiri: tombol edit + treeview + tombol kirim ──────────────────────
        left_col = tk.Frame(content, bg=PANEL, highlightthickness=0, bd=0)
        left_col.grid(row=0, column=0, sticky="nsew")
        left_col.columnconfigure(0, weight=1)
        left_col.rowconfigure(0, weight=0)   # tombol edit — tinggi tetap
        left_col.rowconfigure(1, weight=1)   # treeview mengisi sisa ruang
        left_col.rowconfigure(2, weight=0)   # tombol kirim — tinggi tetap

        # Tombol Edit List Trigger — lebar penuh, di atas treeview
        self._reload_btn = ctk.CTkButton(left_col, text="✏  Edit List Trigger",
                                         command=self._edit_triggers, **BTN_GHOST)
        self._reload_btn.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        tree_frame = tk.Frame(left_col, bg=PANEL, highlightthickness=0, bd=0)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        cols = ("no", "trigger")
        self._tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                  style="WA.Treeview")
        self._tree.heading("no",      text="#",       anchor="center")
        self._tree.heading("trigger", text="Trigger", anchor="w")
        self._tree.column("no",      width=40,  stretch=False, anchor="center")
        self._tree.column("trigger", width=320, stretch=True)
        self._tree.tag_configure("odd",    background=WIDGET)
        self._tree.tag_configure("even",   background=ROW_ALT)
        self._tree.tag_configure("spacer", background=PANEL)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<ButtonPress-1>",    self._on_tree_click)
        self._tree.bind("<Motion>",           self._on_tree_motion)
        self._spacer_iids: set = set()

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        # Tombol Kirim Trigger — lebar penuh, menempel di bawah treeview
        self._send_btn = ctk.CTkButton(left_col, text="▶  Kirim Chat/Trigger",
                                       command=self._send_trigger,
                                       state="disabled",
                                       **BTN_ACCENT)
        self._send_btn.grid(row=2, column=0, sticky="ew", pady=(3, 0))

        # ── Separator ────────────────────────────────────────────────────────
        tk.Frame(content, bg=BORDER, width=1).grid(row=0, column=1, sticky="ns", padx=4)

        # ── Kanan: area embed Chrome ──────────────────────────────────────────
        self._browser_frame = tk.Frame(content, bg=BG,
                                       highlightthickness=0, bd=0)
        self._browser_frame.grid(row=0, column=2, sticky="nsew")
        self._browser_frame.bind("<Configure>", lambda _: self._resize_chrome())

        self._placeholder = ctk.CTkLabel(
            self._browser_frame,
            text="Klik  💬 Buka WhatsApp  untuk memulai.\n\n"
                 "Chrome WhatsApp Web akan tampil di sini.",
            text_color=SUBTEXT,
            fg_color="transparent",
            font=FONT,
            justify="center",
        )
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")

    # ── Load Triggers ─────────────────────────────────────────────────────────────

    def load_triggers(self):
        """Isi awal treeview dengan placeholder saat startup."""
        self._apply_triggers([
            "Klik Tombol 'Edit List Trigger' diatas",
            "Untuk mengubah list Trigger disini",
            "*Hapus yang tidak digunakan*",
        ])

    def _edit_triggers(self):
        """Buka popup editor untuk menyunting daftar trigger secara manual."""
        TriggerEditDialog(self._app, self._raw_triggers, self._apply_triggers)

    def _apply_triggers(self, triggers: list):
        """Update treeview dari list trigger. Baris kosong ditampilkan sebagai jeda visual."""
        self._raw_triggers = list(triggers)   # simpan asli untuk editor
        self._tree.delete(*self._tree.get_children())
        self._spacer_iids = set()

        # Jumlah karakter per baris disesuaikan dengan DPI scale
        # (di 150% font lebih besar → lebih sedikit chars yang muat)
        scale     = self._app._get_dpi_scale()
        wrap_chars = max(22, round(self._WRAP_CHARS / scale))

        seq       = 0
        max_lines = 1
        for val in triggers:
            if not str(val).strip():
                iid = self._tree.insert("", "end", values=("", ""), tags=("spacer",))
                self._spacer_iids.add(iid)
            else:
                seq += 1
                wrapped  = "\n".join(textwrap.wrap(str(val), width=wrap_chars)) or str(val)
                n_lines  = wrapped.count("\n") + 1
                max_lines = max(max_lines, n_lines)
                tag = "even" if seq % 2 == 0 else "odd"
                self._tree.insert("", "end", values=(seq, wrapped), tags=(tag,))

        # rowheight = tinggi per baris × jumlah baris terbanyak + padding
        # Nilai 22px per baris cukup untuk Segoe UI 9pt di semua skala DPI
        row_h = max(28, max_lines * 22 + 6)
        ttk.Style().configure("WA.Treeview", rowheight=row_h)

    # ── WhatsApp Connection ────────────────────────────────────────────────────────

    def _open_whatsapp(self):
        # Naikkan session ID — semua callback lama (embed retry, poll) otomatis batal
        self._session_id += 1
        self._connected   = False
        self._polling     = False
        self._chrome_hwnd = None
        self._set_connected(False)
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")
        self._wa_btn.configure(state="disabled")
        self._status_var.set("Membuka WhatsApp...")
        sid = self._session_id
        threading.Thread(target=self._open_worker, args=(sid,), daemon=True).start()

    def _open_worker(self, sid: int):
        from utils.driver_factory import create_wa_driver
        try:
            if self._app._wa_driver:
                try:
                    self._app._wa_driver.quit()
                except Exception:
                    pass
            if sid != self._session_id:
                return  # session sudah diganti lagi sebelum ini selesai
            driver = create_wa_driver()
            self._app._wa_driver = driver
            driver.get("https://web.whatsapp.com")
            # Paksa WhatsApp Web render dalam light mode
            try:
                driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {
                    "media": "screen",
                    "features": [{"name": "prefers-color-scheme", "value": "light"}],
                })
            except Exception:
                pass
            # Zoom out sesuai DPI scale agar konten tidak terlalu besar
            scale = self._app._get_dpi_scale()
            zoom  = 0.4 if scale >= 1.45 else 0.5 if scale >= 1.20 else None
            if zoom:
                try:
                    driver.execute_cdp_cmd("Emulation.setPageScaleFactor",
                                           {"pageScaleFactor": zoom})
                except Exception:
                    pass
            self._app.after(800, lambda: self._embed_chrome(sid))
            self._app.after(0, lambda: self._start_polling(sid))
        except Exception as e:
            msg = str(e)
            if sid == self._session_id:
                self._app.after(0, lambda: self._status_var.set(f"⚠  Gagal: {msg}"))
                self._app.after(0, lambda: self._wa_btn.configure(state="normal"))

    # ── Embed Chrome ──────────────────────────────────────────────────────────────

    def _embed_chrome(self, sid: int, _retry: int = 0):
        if sid != self._session_id:
            return  # session sudah basi
        driver = self._app._wa_driver
        if not driver:
            return
        hwnd = self._find_chrome_hwnd(driver)
        if not hwnd:
            if _retry < 5:
                self._app.after(800, lambda: self._embed_chrome(sid, _retry + 1))
            else:
                self._app.after(0, lambda: self._status_var.set(
                    "Chrome terbuka di jendela terpisah"))
            return
        try:
            import win32gui
            import win32con
            frame_hwnd = self._browser_frame.winfo_id()
            win32gui.SetParent(hwnd, frame_hwnd)
            # Hapus title bar dan border Chrome
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            style &= ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME |
                       win32con.WS_SYSMENU | win32con.WS_MINIMIZEBOX |
                       win32con.WS_MAXIMIZEBOX)
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
            self._chrome_hwnd = hwnd
            self._placeholder.place_forget()
            self._app.after(0, self._resize_chrome)
            # Resize ulang setelah Chrome selesai reflow
            self._app.after(600, self._resize_chrome)
        except ImportError:
            pass  # pywin32 tidak terinstall — Chrome tetap di jendela terpisah
        except Exception:
            pass

    def _find_chrome_hwnd(self, driver) -> int | None:
        try:
            import psutil
            import win32gui
            import win32process
            service_pid = driver.service.process.pid
            chrome_pids: set[int] = set()
            try:
                for child in psutil.Process(service_pid).children(recursive=True):
                    if "chrome" in child.name().lower():
                        chrome_pids.add(child.pid)
            except Exception:
                pass
            if not chrome_pids:
                return None
            found: list[int] = []

            def _cb(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    if pid in chrome_pids and \
                            win32gui.GetClassName(hwnd) == "Chrome_WidgetWin_1":
                        found.append(hwnd)
                return True

            win32gui.EnumWindows(_cb, None)
            return found[0] if found else None
        except Exception:
            return None

    def _resize_chrome(self):
        if not self._chrome_hwnd:
            return
        try:
            import win32gui
            self._browser_frame.update_idletasks()
            w = self._browser_frame.winfo_width()
            h = self._browser_frame.winfo_height()
            if w < 2 or h < 2:
                return
            win32gui.MoveWindow(self._chrome_hwnd, 0, 0, w, h, True)
            # Paksa Chrome renderer update viewport agar konten tidak terpotong.
            # winfo_width/height = pixel fisik (proses DPI-aware).
            # CDP width/height = CSS pixel (logis) → bagi dengan scale agar tidak overflow.
            driver = self._app._wa_driver
            if driver:
                try:
                    scale = self._app._get_dpi_scale()
                    driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
                        "width":             round(w / scale),
                        "height":            round(h / scale),
                        "deviceScaleFactor": 0,
                        "mobile":            False,
                    })
                except Exception:
                    pass
        except Exception:
            pass

    # ── Status Polling ────────────────────────────────────────────────────────────

    def _start_polling(self, sid: int):
        if sid != self._session_id:
            return
        self._wa_btn.configure(state="normal")
        if not self._polling:
            self._polling = True
            self._poll_status(sid)

    def _poll_status(self, sid: int):
        if sid != self._session_id:
            self._polling = False
            return
        driver = self._app._wa_driver
        if not driver:
            self._polling = False
            return
        try:
            main = driver.find_elements(By.CSS_SELECTOR, '#pane-side')
            self._app.after(0, self._set_connected, bool(main))
        except Exception:
            self._polling = False
            return
        self._app.after(2000, lambda: self._poll_status(sid))

    def _set_connected(self, connected: bool):
        was_connected = self._connected
        self._connected = connected
        if connected:
            self._status_dot.configure(text_color=SUCCESS)
            self._env_dev_btn.configure(state="normal")
            self._env_prod_btn.configure(state="normal")
            if not was_connected:
                # Transisi pertama kali: tulis status + buka room
                self._status_var.set("Terhubung")
                self._set_env(self._env)
            else:
                # Sudah terhubung — jangan overwrite status yang mungkin sedang tampil
                self._apply_env_visual(self._env)
        else:
            self._status_dot.configure(text_color=DANGER)
            self._status_var.set("Scan QR untuk Login Whatsapp")
            # Nonaktifkan tombol env, kembalikan keduanya ke ghost
            self._env_dev_btn.configure(state="disabled", **BTN_GHOST)
            self._env_prod_btn.configure(state="disabled", **BTN_GHOST)
        self._refresh_send_btn()

    # ── Send ──────────────────────────────────────────────────────────────────────

    def _on_tree_click(self, event):
        iid = self._tree.identify_row(event.y)
        if iid in self._spacer_iids:
            return "break"  # blokir klik — tidak bisa dipilih

    def _on_tree_motion(self, event):
        iid = self._tree.identify_row(event.y)
        if iid in self._spacer_iids:
            self._tree.config(cursor="arrow")
            self._tree.focus("")   # hapus active-highlight dari baris spacer
        else:
            self._tree.config(cursor="")

    def _on_select(self, _event=None):
        # Backup: hapus spacer dari selection jika entah bagaimana terpilih
        for iid in list(self._tree.selection()):
            if iid in self._spacer_iids:
                self._tree.selection_remove(iid)
        self._refresh_send_btn()

    def _refresh_send_btn(self):
        ready = self._connected and bool(self._tree.selection())
        self._send_btn.configure(state="normal" if ready else "disabled")

    _CSS_MSG_INPUT = (
        'div[aria-label="Type a message"],'
        'div[contenteditable="true"][data-tab="10"],'
        'footer div[contenteditable="true"]'
    )
    _CSS_SEND_BTN = 'button[aria-label="Send"]'

    def _send_trigger(self):
        sel = self._tree.selection()
        if not sel:
            return
        idx     = self._tree.get_children().index(sel[0])
        trigger = self._raw_triggers[idx] if idx < len(self._raw_triggers) else \
                  self._tree.item(sel[0], "values")[1]
        self._send_btn.configure(state="disabled")
        self._status_var.set("Mengirim Trigger...")
        threading.Thread(target=self._send_worker,
                         args=(trigger,), daemon=True).start()

    def _send_worker(self, text: str):
        driver = self._app._wa_driver
        wait   = WebDriverWait(driver, 10)
        try:
            # Ketik trigger ke message input yang sudah terbuka
            inp = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, self._CSS_MSG_INPUT)))
            inp.click()
            inp.send_keys(text)
            # Klik tombol Send sebagai validasi pengiriman
            send_btn = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, self._CSS_SEND_BTN)))
            send_btn.click()
            self._app.after(0, lambda: self._status_var.set(f"Trigger Terkirim: {text}"))
        except TimeoutException:
            self._app.after(0, lambda: self._status_var.set(
                "⚠  Timeout — pastikan room chat sudah terbuka"))
        except Exception as e:
            msg = str(e)
            self._app.after(0, lambda: self._status_var.set(f"Gagal Mengirim: {msg}"))
        finally:
            self._app.after(0, self._refresh_send_btn)


# ── Trigger Editor Dialog ─────────────────────────────────────────────────────

class TriggerEditDialog(ctk.CTkToplevel):
    """
    Popup modal untuk menyunting daftar trigger secara bebas.
    Satu trigger per baris; baris kosong diabaikan saat disimpan ke treeview.
    """

    def __init__(self, parent, triggers: list, on_save):
        super().__init__(parent)
        self._on_save = on_save
        self.title("Edit Daftar Trigger")
        self.configure(fg_color=PANEL)
        self.resizable(True, True)
        self.grab_set()
        self.focus_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._build(triggers)
        self.update_idletasks()
        self._center(parent)

    def _build(self, triggers: list):
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=28, pady=20)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        # Header
        ctk.CTkLabel(root, text="Edit Daftar Trigger",
                     fg_color="transparent", text_color=TEXT,
                     font=FONT_BOLD).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(root,
                     text="Satu trigger per baris. Baris kosong tampil sebagai jeda di preview.",
                     fg_color="transparent", text_color=SUBTEXT,
                     font=FONT_SMALL).grid(row=1, column=0, sticky="w", pady=(2, 10))

        # Text area
        text_frame = tk.Frame(root, bg=WIDGET,
                              highlightthickness=1, highlightbackground=BORDER)
        text_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 14))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self._text = tk.Text(text_frame,
                             font=("Segoe UI", 9),
                             bg=WIDGET, fg=TEXT,
                             insertbackground=TEXT,
                             selectbackground="#C6F6D5",
                             relief="flat", wrap="word", undo=True,
                             padx=10, pady=8)
        vsb = ttk.Scrollbar(text_frame, orient="vertical",
                            command=self._text.yview)
        self._text.configure(yscrollcommand=vsb.set)
        self._text.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        # Pre-fill
        self._text.insert("1.0", "\n".join(triggers))

        # Footer — count label + buttons
        footer = ctk.CTkFrame(root, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)

        self._count_var = tk.StringVar()
        ctk.CTkLabel(footer, textvariable=self._count_var,
                     fg_color="transparent", text_color=SUBTEXT,
                     font=FONT_LABEL).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(footer, text="💾  Simpan",
                      command=self._save,
                      **BTN_ACCENT).grid(row=0, column=2, padx=(6, 0))
        ctk.CTkButton(footer, text="Batal",
                      command=self.destroy,
                      **BTN_GHOST).grid(row=0, column=1)

        # Update count setiap kali teks berubah
        self._text.bind("<<Modified>>", self._update_count)
        self._update_count()
        self._text.focus_set()

    def _update_count(self, *_):
        raw   = self._text.get("1.0", "end-1c")
        total = sum(1 for ln in raw.splitlines() if ln.strip())
        self._count_var.set(f"{total} trigger")
        self._text.edit_modified(False)  # reset flag agar event terpicu lagi

    def _save(self):
        raw      = self._text.get("1.0", "end-1c")
        # Kirim semua baris termasuk kosong — treeview yang tampilkan sebagai jeda
        triggers = raw.splitlines()
        self._on_save(triggers)
        self.destroy()

    def _center(self, parent):
        w, h = 520, 500
        pw = parent.winfo_x() + parent.winfo_width()  // 2
        ph = parent.winfo_y() + parent.winfo_height() // 2
        self.geometry(f"{w}x{h}+{pw - w // 2}+{ph - h // 2}")
