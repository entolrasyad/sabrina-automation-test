"""
ui/constants.py — Color palette & dimension constants
Light mode — Tokopedia-inspired green accent palette
"""

# ── Background hierarchy ───────────────────────────────────────────────────────
BG       = "#EEF1F8"   # main window bg — soft blue-gray
PANEL    = "#FFFFFF"   # card / panel — pure white
WIDGET   = "#F4F6FB"   # input / treeview cell bg
HOVER    = "#E4E9F5"   # hover state

# ── Accent — Tokopedia green ───────────────────────────────────────────────────
ACCENT   = "#03AC0E"   # Tokopedia primary green
ACCENT2  = "#05C910"   # lighter green (gradient)
ACCENT_D = "#028A0B"   # deep green — pressed / hover

# ── Status ─────────────────────────────────────────────────────────────────────
SUCCESS  = "#03AC0E"   # green — ready
DANGER   = "#E53E3E"   # red — error / stop
WARNING  = "#D97706"   # amber — caution

# ── Text ───────────────────────────────────────────────────────────────────────
TEXT     = "#1A202C"   # near-black
SUBTEXT  = "#718096"   # slate gray — secondary / placeholder

# ── Border & Selection ─────────────────────────────────────────────────────────
BORDER   = "#CBD5E0"   # light border
SEL_BG   = "#C6F6D5"   # mint green — treeview selection
ROW_ALT  = "#F7FAFC"   # alternate treeview row

# ── Font scale ────────────────────────────────────────────────────────────────
FONT         = ("Segoe UI", 13)
FONT_BOLD    = ("Segoe UI", 13, "bold")
FONT_SMALL   = ("Segoe UI", 11)
FONT_LABEL   = ("Segoe UI", 10)

# ── CTkButton presets ─────────────────────────────────────────────────────────
BTN_ACCENT  = dict(fg_color=ACCENT,    hover_color=ACCENT_D,  text_color="#ffffff",  font=FONT_BOLD)
BTN_DANGER  = dict(fg_color="#FFF5F5", hover_color="#FED7D7", text_color=DANGER,     font=FONT)
BTN_WARNING = dict(fg_color="#FFFBEB", hover_color="#FEF3C7", text_color=WARNING,    font=FONT)
BTN_GHOST   = dict(fg_color=PANEL,     hover_color=HOVER,     text_color=SUBTEXT,    font=FONT,
                   border_width=1, border_color=BORDER)
BTN_DEFAULT = dict(fg_color=WIDGET,    hover_color=HOVER,     text_color=TEXT,       font=FONT)
BTN_BLUE    = dict(fg_color="#EBF4FF", hover_color="#BEE3F8", text_color="#2B6CB0",  font=FONT,
                   border_width=1, border_color="#90CDF4")
BTN_SUBTLE  = dict(fg_color="#EDF2F7", hover_color="#E2E8F0", text_color="#4A5568",  font=FONT,
                   border_width=1, border_color="#CBD5E0")
