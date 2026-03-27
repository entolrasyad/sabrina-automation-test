"""
ui/views/bulk_tab.py — Bulk Excel processing tab
Loads data.xlsx, runs bot API for each row, saves results back.
"""

import os
import threading
import openpyxl
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

from ui.constants import WIDGET, ROW_ALT, SUCCESS, SUBTEXT, PANEL, TEXT, BORDER
from ui.constants import BTN_ACCENT, BTN_DANGER, BTN_GHOST
from ui.constants import FONT
from ui.api import call_bot_api

CHECKPOINT = 10


class BulkTab(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self._app          = app
        self._excel_rows   = []
        self._progress_max = 1
        self._last_frac    = 0.0
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build()

    # ── UI Construction ──────────────────────────────────────────────────────────

    def _build(self):
        self._build_toolbar()
        self._build_treeview()

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(10, 8), padx=14)

        # Search
        ctk.CTkLabel(toolbar, text="Search:",
                     fg_color="transparent",
                     text_color=SUBTEXT,
                     font=FONT).pack(side="left", padx=(0, 4))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search())
        ctk.CTkEntry(toolbar,
                     textvariable=self._search_var,
                     width=200,
                     fg_color=WIDGET,
                     border_color=BORDER,
                     border_width=1,
                     text_color=TEXT,
                     font=FONT,
                     placeholder_text="ketik untuk filter...").pack(side="left", padx=(0, 14))

        self._reload_btn = ctk.CTkButton(toolbar, text="↺  Refresh Data",
                                         command=self.load_excel, **BTN_GHOST)
        self._reload_btn.pack(side="left", padx=(0, 6))

        self._run_btn = ctk.CTkButton(toolbar, text="▶  Mulai",
                                      command=self._run, **BTN_ACCENT)
        self._run_btn.pack(side="left")

        self._stop_btn = ctk.CTkButton(toolbar, text="⏹  Stop",
                                       command=self._stop,
                                       state="disabled",
                                       **BTN_DANGER)
        self._stop_btn.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(toolbar, text="Mulai dari baris:",
                     fg_color="transparent",
                     text_color=SUBTEXT,
                     font=FONT).pack(side="left", padx=(16, 4))

        self._start_from_var = tk.StringVar(value="1")
        self._start_from_cb  = ctk.CTkEntry(toolbar,
                                             textvariable=self._start_from_var,
                                             width=64,
                                             fg_color=WIDGET,
                                             border_color=BORDER,
                                             border_width=1,
                                             text_color=TEXT,
                                             font=FONT,
                                             justify="center")
        self._start_from_cb.pack(side="left")

    def _build_treeview(self):
        frame = tk.Frame(self, bg=PANEL, highlightthickness=0, bd=0)
        frame.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        cols = ("no", "user_says", "dialog", "score")
        self._tree = ttk.Treeview(frame, columns=cols, show="headings", height=16)
        self._tree.heading("no",        text="#",         anchor="center")
        self._tree.heading("user_says", text="Trigger", anchor="w")
        self._tree.heading("dialog",    text="Dialog",    anchor="w")
        self._tree.heading("score",     text="Score",     anchor="w")
        self._tree.column("no",        width=44,  stretch=False, anchor="center")
        self._tree.column("user_says", width=190, stretch=False)
        self._tree.column("dialog",    width=330, stretch=True)
        self._tree.column("score",     width=160, stretch=True, anchor="w")

        self._tree.tag_configure("odd",       background=WIDGET)
        self._tree.tag_configure("even",      background=ROW_ALT)
        self._tree.tag_configure("done_odd",  background=WIDGET,  foreground=SUCCESS)
        self._tree.tag_configure("done_even", background=ROW_ALT, foreground=SUCCESS)

        vsb = ttk.Scrollbar(frame, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

    # ── Excel Load ───────────────────────────────────────────────────────────────

    def load_excel(self):
        excel_path = self._app.EXCEL_PATH
        if not os.path.exists(excel_path):
            self._app.session_bar.update_bulk(0, "data.xlsx tidak ditemukan di direktori project.")
            return
        try:
            wb = openpyxl.load_workbook(excel_path)
            ws = wb.active
            self._search_var.set("")
            self._tree.delete(*self._tree.get_children())
            self._excel_rows.clear()
            seq = 0
            for row in range(2, ws.max_row + 1):
                val = ws.cell(row=row, column=1).value
                if not val:
                    continue
                seq += 1
                dialog = ws.cell(row=row, column=2).value or ""
                score  = ws.cell(row=row, column=3).value or ""
                tag    = "even" if seq % 2 == 0 else "odd"
                iid = self._tree.insert("", "end",
                                        values=(seq, str(val), str(dialog), str(score)),
                                        tags=(tag,))
                self._excel_rows.append((row, str(val), iid))

            total = len(self._excel_rows)
            self._app.session_bar.update_bulk(0, f"Berhasil Memuat {total} Baris Trigger")
            self._start_from_var.set("1")
        except Exception as exc:
            messagebox.showerror("Load Error", str(exc))

    # ── Bulk Run ─────────────────────────────────────────────────────────────────

    def _run(self):
        app = self._app
        if not app.check_ready():
            return
        if not self._excel_rows:
            messagebox.showwarning("Kosong", "Tidak ada data. Klik 'Reload' terlebih dahulu.")
            return

        try:
            start_from = max(1, int(self._start_from_var.get() or "1"))
        except ValueError:
            start_from = 1
        app._cancel = False

        self._run_btn.configure(state="disabled")
        self._reload_btn.configure(state="disabled")
        self._start_from_cb.configure(state="disabled")
        self._stop_btn.configure(state="normal")

        excel_rows = list(self._excel_rows)[start_from - 1:]
        total      = len(excel_rows)
        self._progress_max = max(total, 1)
        self._last_frac    = 0.0
        self._app.session_bar.update_bulk(0, f"0 / {total}")

        cookie_str = app._cookie_str
        view_state = app._view_state
        excel_path = app.EXCEL_PATH

        def _save(wb, label):
            try:
                wb.save(excel_path)
                return True
            except PermissionError:
                app.after(0, messagebox.showerror, "Simpan Gagal",
                          f"Tutup file data.xlsx di Excel terlebih dahulu.\n({label})")
                app.after(0, app.session_bar.update_bulk, self._last_frac,
                          "Gagal menyimpan — file sedang terbuka.")
                return False

        def _worker():
            try:
                wb = openpyxl.load_workbook(excel_path)
                ws = wb.active
                ws["B1"] = "Dialog"
                ws["C1"] = "Confident Score"
            except Exception as exc:
                app.after(0, messagebox.showerror, "Load Error", str(exc))
                app.after(0, self._finish)
                return

            stopped_at = total
            try:
                for i, (row_num, user_says, iid) in enumerate(excel_rows, 1):
                    if app._cancel:
                        stopped_at = i - 1
                        break
                    try:
                        for reset_word in ("menu", "batal"):
                            call_bot_api(cookie_str, view_state, reset_word)
                        result = call_bot_api(cookie_str, view_state, user_says)
                    except Exception as e:
                        result = {"dialog": f"[ERROR] {e}", "score": ""}
                    ws.cell(row=row_num, column=2).value = result["dialog"]
                    ws.cell(row=row_num, column=3).value = result["score"]
                    app.after(0, self._update_row, iid, result["dialog"], result["score"], i, total)
                    if i % CHECKPOINT == 0:
                        _save(wb, f"checkpoint baris {i}")

                saved = _save(wb, "simpan akhir")
                if saved:
                    if stopped_at < total:
                        app.after(0, app.session_bar.update_bulk,
                                  stopped_at / self._progress_max,
                                  f"⏹  Stop di {stopped_at} / {total} — Tersimpan.")
                    else:
                        app.after(0, app.session_bar.update_bulk, 1.0,
                                  f"✓  Selesai! {total} baris disimpan ke data.xlsx")
            except Exception as exc:
                app.after(0, app.session_bar.update_bulk, self._last_frac, f"⚠  Error: {exc}")
            finally:
                app.after(0, self._finish)

        threading.Thread(target=_worker, daemon=True).start()

    def _update_row(self, iid, dialog, score, i, total):
        try:
            vals     = self._tree.item(iid, "values")
            old_tags = self._tree.item(iid, "tags")
            done_tag = "done_even" if "even" in old_tags else "done_odd"
            self._tree.item(iid, values=(vals[0], vals[1], dialog, score), tags=(done_tag,))
            self._tree.see(iid)
        except tk.TclError:
            pass
        self._last_frac = i / self._progress_max
        self._app.session_bar.update_bulk(self._last_frac, f"{i} / {total}")

    def _on_search(self):
        q = self._search_var.get().lower().strip()
        if not q:
            self._tree.selection_set([])
            return
        matches = [
            iid for iid in self._tree.get_children()
            if any(q in str(v).lower() for v in self._tree.item(iid, "values")[1:])
        ]
        self._tree.selection_set(matches)
        if matches:
            self._tree.see(matches[0])

    def _stop(self):
        self._app._cancel = True
        self._stop_btn.configure(state="disabled")

    def _finish(self):
        self._run_btn.configure(state="normal")
        self._reload_btn.configure(state="normal")
        self._start_from_cb.configure(state="normal")
        self._stop_btn.configure(state="disabled")
