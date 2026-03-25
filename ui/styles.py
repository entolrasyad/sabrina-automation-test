"""
ui/styles.py — TTK dark theme configuration
"""

import tkinter as tk
from tkinter import ttk
from .constants import (
    BG, PANEL, WIDGET, HOVER, ACCENT, ACCENT2, ACCENT_D,
    SUCCESS, DANGER, WARNING, TEXT, SUBTEXT, BORDER, SEL_BG,
)


def apply_dark_theme(root: tk.Tk) -> None:
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".",
        background=BG, foreground=TEXT,
        fieldbackground=WIDGET, bordercolor=BORDER,
        darkcolor=PANEL, lightcolor=PANEL,
        troughcolor=PANEL, selectbackground=SEL_BG,
        selectforeground=TEXT, insertcolor=TEXT,
        font=("Segoe UI", 9),
    )

    # Frames & Labels
    style.configure("TFrame",      background=BG)
    style.configure("TLabel",      background=BG, foreground=TEXT)
    style.configure("Sub.TLabel",  background=BG, foreground=SUBTEXT, font=("Segoe UI", 9))
    style.configure("TLabelframe", background=PANEL, bordercolor=BORDER, relief="flat")
    style.configure("TLabelframe.Label",
        background=PANEL, foreground=SUBTEXT, font=("Segoe UI", 9, "bold"))
    style.configure("Panel.TFrame",     background=PANEL)
    style.configure("Panel.TLabel",     background=PANEL, foreground=TEXT)
    style.configure("Panel.Sub.TLabel", background=PANEL, foreground=SUBTEXT,
                    font=("Segoe UI", 9))

    # Notebook / Tabs
    style.configure("TNotebook",
        background=BG, bordercolor=BORDER, tabmargins=[0, 4, 0, 0])
    style.configure("TNotebook.Tab",
        background=PANEL, foreground=SUBTEXT,
        padding=[14, 7], bordercolor=BORDER, font=("Segoe UI", 9))
    style.map("TNotebook.Tab",
        background=[("selected", WIDGET), ("active", HOVER)],
        foreground=[("selected", TEXT),   ("active", TEXT)],
    )

    # Separator
    style.configure("TSeparator", background=BORDER)

    # Buttons — default
    style.configure("TButton",
        background=WIDGET, foreground=TEXT,
        bordercolor=BORDER, focuscolor=ACCENT,
        padding=[10, 5], relief="flat", font=("Segoe UI", 9),
    )
    style.map("TButton",
        background=[("active", HOVER), ("disabled", PANEL)],
        foreground=[("disabled", SUBTEXT)],
        bordercolor=[("active", ACCENT)],
    )

    # Accent button (primary action)
    style.configure("Accent.TButton",
        background=ACCENT, foreground="#ffffff",
        bordercolor=ACCENT, padding=[12, 6],
        font=("Segoe UI", 9, "bold"),
    )
    style.map("Accent.TButton",
        background=[("active", ACCENT_D), ("disabled", PANEL)],
        foreground=[("disabled", SUBTEXT)],
        bordercolor=[("active", ACCENT_D)],
    )

    # Danger button (Stop / Logout)
    style.configure("Danger.TButton",
        background="#3d2233", foreground=DANGER,
        bordercolor=DANGER, padding=[10, 5],
        font=("Segoe UI", 9),
    )
    style.map("Danger.TButton",
        background=[("active", "#502a3e"), ("disabled", PANEL)],
        foreground=[("disabled", SUBTEXT)],
    )

    # Warning button (reset / caution actions)
    style.configure("Warning.TButton",
        background="#3d3010", foreground=WARNING,
        bordercolor=WARNING, padding=[10, 5],
        font=("Segoe UI", 9),
    )
    style.map("Warning.TButton",
        background=[("active", "#524018"), ("disabled", PANEL)],
        foreground=[("disabled", SUBTEXT)],
    )

    # Ghost button (secondary actions)
    style.configure("Ghost.TButton",
        background=PANEL, foreground=SUBTEXT,
        bordercolor=BORDER, padding=[10, 5],
    )
    style.map("Ghost.TButton",
        background=[("active", HOVER), ("disabled", PANEL)],
        foreground=[("active", TEXT), ("disabled", SUBTEXT)],
    )

    # Entry
    style.configure("TEntry",
        fieldbackground=WIDGET, foreground=TEXT,
        bordercolor=BORDER, insertcolor=TEXT,
        padding=[6, 4],
    )
    style.map("TEntry",
        bordercolor=[("focus", ACCENT)],
        fieldbackground=[("readonly", PANEL), ("disabled", PANEL)],
        foreground=[("readonly", SUBTEXT)],
    )

    # Progressbar
    style.configure("TProgressbar",
        troughcolor=WIDGET, background=ACCENT,
        bordercolor=BORDER, darkcolor=ACCENT, lightcolor=ACCENT2,
    )

    # Scrollbar
    style.configure("TScrollbar",
        background=PANEL, troughcolor=WIDGET,
        bordercolor=BORDER, arrowcolor=SUBTEXT,
        relief="flat",
    )
    style.map("TScrollbar",
        background=[("active", HOVER)],
    )

    # Treeview
    style.configure("Treeview",
        background=WIDGET, foreground=TEXT,
        fieldbackground=WIDGET, bordercolor=BORDER,
        rowheight=28, font=("Segoe UI", 9),
    )
    style.configure("Treeview.Heading",
        background=PANEL, foreground=SUBTEXT,
        bordercolor=BORDER, relief="flat",
        font=("Segoe UI", 9, "bold"),
    )
    style.map("Treeview",
        background=[("selected", SEL_BG)],
        foreground=[("selected", "#ffffff")],
    )
    style.map("Treeview.Heading",
        background=[("active", HOVER)],
        foreground=[("active", TEXT)],
    )


def draw_gradient(canvas: tk.Canvas, w: int, h: int,
                  color1: str, color2: str) -> None:
    """Draw a horizontal gradient on a Canvas widget."""
    r1, g1, b1 = canvas.winfo_rgb(color1)
    r2, g2, b2 = canvas.winfo_rgb(color2)
    for i in range(w):
        r = int(r1 + (r2 - r1) * i / w) >> 8
        g = int(g1 + (g2 - g1) * i / w) >> 8
        b = int(b1 + (b2 - b1) * i / w) >> 8
        canvas.create_line(i, 0, i, h, fill=f"#{r:02x}{g:02x}{b:02x}")
