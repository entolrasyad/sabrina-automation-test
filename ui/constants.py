"""
ui/constants.py — Color palette & dimension constants
"""

BG       = "#0e0e14"   # main window background — rich near-black
PANEL    = "#141420"   # frame / labelframe background
WIDGET   = "#1c1c2c"   # entry / treeview / text widget bg
HOVER    = "#252538"   # hover state bg
ACCENT   = "#7c6af7"   # primary indigo-violet (Linear-style)
ACCENT2  = "#c084fc"   # purple gradient end
ACCENT_D = "#5b4fd4"   # deeper indigo for pressed state
SUCCESS  = "#34d399"   # emerald — credential ready
DANGER   = "#f87171"   # red — credential not ready / stop
WARNING  = "#fb923c"   # warm orange
TEXT     = "#ededf0"   # primary text — warm near-white
SUBTEXT  = "#6b7280"   # secondary / placeholder text
BORDER   = "#232336"   # border / separator
SEL_BG   = "#4338ca"   # treeview selection bg
ROW_ALT  = "#111120"   # alternate treeview row

# ── Font scale ────────────────────────────────────────────────────────────────
FONT         = ("Segoe UI", 13)
FONT_BOLD    = ("Segoe UI", 13, "bold")
FONT_SMALL   = ("Segoe UI", 11)
FONT_LABEL   = ("Segoe UI", 10)   # field labels (Username, Password, dll)

# ── CTkButton presets ──────────────────────────────────────────────────────────
BTN_ACCENT  = dict(fg_color=ACCENT,    hover_color=ACCENT_D,  text_color="#ffffff",  font=FONT_BOLD)
BTN_DANGER  = dict(fg_color="#3d2233", hover_color="#502a3e", text_color=DANGER,     font=FONT)
BTN_WARNING = dict(fg_color="#3d3010", hover_color="#524018", text_color=WARNING,    font=FONT)
BTN_GHOST   = dict(fg_color=PANEL,     hover_color=HOVER,     text_color=SUBTEXT,    font=FONT,
                   border_width=1, border_color=BORDER)
BTN_DEFAULT = dict(fg_color=WIDGET,    hover_color=HOVER,     text_color=TEXT,       font=FONT)
