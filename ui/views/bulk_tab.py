"""
ui/views/bulk_tab.py — Bulk Excel processing tab
Loads data.xlsx, runs bot API for each row, saves results back.
"""

import os
import threading
import openpyxl
import tkinter as tk
from tkinter import ttk, messagebox

from ui.constants import WIDGET, ROW_ALT, SUCCESS, SUBTEXT
from ui.api import call_bot_api

CHECKPOINT = 10   # save every N rows


class BulkTab(ttk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent, padding=14)
        self._app        = app
        self._excel_rows = []
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build()

    # ── UI Construction ─────────────────────────────────────────────────────────

    def _build(self):
        self._build_toolbar()
        self._build_treeview()

    def _build_toolbar(self):
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self._reload_btn = ttk.Button(toolbar, text="↺  Reload",
                                      command=self.load_excel,
                                      style="Ghost.TButton")
        self._reload_btn.pack(side="left", padx=(0, 6))

        self._run_btn = ttk.Button(toolbar, text="▶  Run All",
                                   command=self._run,
                                   style="Accent.TButton")
        self._run_btn.pack(side="left")

        self._stop_btn = ttk.Button(toolbar, text="⏹  Stop",
                                    command=self._stop,
                                    style="Danger.TButton",
                                    state="disabled")
        self._stop_btn.pack(side="left", padx=(6, 0))

        ttk.Label(toolbar, text="Optional - Mulai dari baris:",
                  foreground=SUBTEXT, font=("Segoe UI", 9)).pack(side="left", padx=(16, 4))
        self._start_from_var = tk.StringVar(value="1")
        self._start_from_cb  = ttk.Combobox(toolbar, textvariable=self._start_from_var,
                                             width=6, state="readonly")
        self._start_from_cb["values"] = ["1"]
        self._start_from_cb.pack(side="left")

        right = ttk.Frame(toolbar)
        right.pack(side="right", padx=(16, 0))

        self._progress = ttk.Progressbar(right, mode="determinate",
                                         length=160, style="TProgressbar")
        self._progress.pack(side="left", padx=(0, 8))

        self._status_var = tk.StringVar(value="Belum ada data.")
        ttk.Label(right, textvariable=self._status_var,
                  foreground=SUBTEXT, font=("Segoe UI", 9)).pack(side="left")

    def _build_treeview(self):
        frame = ttk.Frame(self)
        frame.grid(row=1, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        cols = ("no", "user_says", "dialog", "score")
        self._tree = ttk.Treeview(frame, columns=cols, show="headings", height=16)
        self._tree.heading("no",        text="#",         anchor="center")
        self._tree.heading("user_says", text="User Says", anchor="w")
        self._tree.heading("dialog",    text="Dialog",    anchor="w")
        self._tree.heading("score",     text="Score",     anchor="w")
        self._tree.column("no",        width=44,  stretch=False, anchor="center")
        self._tree.column("user_says", width=190, stretch=False)
        self._tree.column("dialog",    width=330, stretch=True)
        self._tree.column("score",     width=160, stretch=True, anchor="w")

        self._tree.tag_configure("odd",  background=WIDGET)
        self._tree.tag_configure("even", background=ROW_ALT)
        self._tree.tag_configure("done", foreground=SUCCESS)

        vsb = ttk.Scrollbar(frame, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

    # ── Excel Load ──────────────────────────────────────────────────────────────

    def load_excel(self):
        excel_path = self._app.EXCEL_PATH
        if not os.path.exists(excel_path):
            self._status_var.set("data.xlsx tidak ditemukan di direktori project.")
            return
        try:
            wb = openpyxl.load_workbook(excel_path)
            ws = wb.active
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
            self._status_var.set(f"{total} baris dimuat")
            self._progress["value"]   = 0
            self._progress["maximum"] = max(total, 1)
            self._start_from_cb["values"] = [str(i) for i in range(1, total + 1)]
            self._start_from_var.set("1")
        except Exception as exc:
            messagebox.showerror("Load Error", str(exc))

    # ── Bulk Run ────────────────────────────────────────────────────────────────

    def _run(self):
        app = self._app
        if not app.check_ready():
            return
        if not self._excel_rows:
            messagebox.showwarning("Kosong", "Tidak ada data. Klik 'Reload' terlebih dahulu.")
            return

        start_from = max(1, int(self._start_from_var.get() or "1"))
        app._cancel = False

        self._run_btn.config(state="disabled")
        self._reload_btn.config(state="disabled")
        self._start_from_cb.config(state="disabled")
        self._stop_btn.config(state="normal")

        excel_rows = list(self._excel_rows)[start_from - 1:]
        total      = len(excel_rows)
        self._progress["maximum"] = max(total, 1)
        self._progress["value"]   = 0
        self._status_var.set(f"0 / {total}")

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
                app.after(0, self._status_var.set, "Gagal menyimpan — file sedang terbuka.")
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
                        app.after(0, self._status_var.set,
                                  f"⏹  Stop di {stopped_at} / {total} — Saved.")
                    else:
                        app.after(0, self._status_var.set,
                                  f"✓  Selesai! {total} baris disimpan ke data.xlsx")
            except Exception as exc:
                app.after(0, self._status_var.set, f"⚠  Error: {exc}")
            finally:
                app.after(0, self._finish)

        threading.Thread(target=_worker, daemon=True).start()

    def _update_row(self, iid, dialog, score, i, total):
        try:
            vals = self._tree.item(iid, "values")
            self._tree.item(iid, values=(vals[0], vals[1], dialog, score), tags=("done",))
            self._tree.see(iid)
        except tk.TclError:
            pass
        self._progress["value"] = i
        self._status_var.set(f"{i} / {total}")

    def _stop(self):
        self._app._cancel = True
        self._stop_btn.config(state="disabled")

    def _finish(self):
        self._run_btn.config(state="normal")
        self._reload_btn.config(state="normal")
        self._start_from_cb.config(state="readonly")
        self._stop_btn.config(state="disabled")
