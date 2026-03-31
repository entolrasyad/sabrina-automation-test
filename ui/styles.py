"""
ui/styles.py — Theme configuration.
CTk handles UI styling; ttk styling kept only for Treeview (no CTk equivalent).
"""

import tkinter as tk
from tkinter import ttk

from .constants import (
    BG, PANEL, WIDGET, HOVER,
    TEXT, SUBTEXT, BORDER, SEL_BG,
)


def apply_theme(_root=None) -> None:
    """Apply ttk styling for Treeview + Scrollbar (CTk has no Treeview widget)."""
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(".",
        background=PANEL, foreground=TEXT,
        fieldbackground=WIDGET, bordercolor=BORDER,
        selectbackground=SEL_BG, selectforeground=TEXT,
        font=("Segoe UI", 9),
    )
    style.configure("Treeview",
        background=WIDGET, foreground=TEXT,
        fieldbackground=WIDGET, bordercolor=PANEL,
        borderwidth=0, relief="flat",
        rowheight=28, font=("Segoe UI", 9),
    )
    style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    style.configure("Treeview.Heading",
        background=BG, foreground=SUBTEXT,
        bordercolor=BORDER, relief="flat",
        font=("Segoe UI", 9, "bold"),
    )
    style.map("Treeview",
        background=[("selected", SEL_BG)],
        foreground=[("selected", TEXT)],
    )
    style.map("Treeview.Heading",
        background=[("active", HOVER)],
        foreground=[("active", TEXT)],
    )
    # Scrollbar — slim, borderless, matches light theme
    style.configure("TScrollbar",
        background=BORDER, troughcolor=BG,
        bordercolor=BG, arrowcolor=BG,
        relief="flat", width=8, arrowsize=0,
    )
    style.map("TScrollbar",
        background=[("active", SUBTEXT), ("disabled", BG)],
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
