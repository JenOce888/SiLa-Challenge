"""
theme.py — Visual themes
Retro CRT (default) + Dark Modern.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    # backgrounds
    bg:         str
    bg_panel:   str
    bg_input:   str
    # text
    fg:         str
    fg_dim:     str
    fg_accent:  str
    fg_error:   str
    fg_success: str
    fg_warn:    str
    # buttons
    btn_bg:     str
    btn_fg:     str
    btn_active: str
    # canvas
    canvas_bg:  str
    scaffold:   str
    body:       str
    head:       str
    # fonts
    font_mono:  str
    font_title: str


# Retro arcade 80s — neon magenta/cyan/yellow on deep black
RETRO = Theme(
    name       = "retro",
    bg         = "#0a0010",
    bg_panel   = "#120020",
    bg_input   = "#120020",
    fg         = "#00f5ff",          # neon cyan
    fg_dim     = "#5a4080",
    fg_accent  = "#ff00cc",          # hot magenta
    fg_error   = "#ff3a3a",
    fg_success = "#00ff99",          # neon mint
    fg_warn    = "#ffe600",          # electric yellow
    btn_bg     = "#1a0035",
    btn_fg     = "#ff00cc",
    btn_active = "#2d0055",
    canvas_bg  = "#06000e",
    scaffold   = "#ff6600",          # orange neon scaffold
    body       = "#00f5ff",          # cyan body
    head       = "#ff00cc",          # magenta head
    font_mono  = "Courier",
    font_title = "Courier",
)

# Dark GitHub-style
DARK = Theme(
    name       = "dark",
    bg         = "#0d1117",
    bg_panel   = "#161b22",
    bg_input   = "#161b22",
    fg         = "#e6edf3",
    fg_dim     = "#8b949e",
    fg_accent  = "#58a6ff",
    fg_error   = "#f85149",
    fg_success = "#3fb950",
    fg_warn    = "#e6b450",
    btn_bg     = "#21262d",
    btn_fg     = "#c9d1d9",
    btn_active = "#30363d",
    canvas_bg  = "#0d1117",
    scaffold   = "#30363d",
    body       = "#79c0ff",
    head       = "#ff7b72",
    font_mono  = "Courier",
    font_title = "Courier",
)

# Phosphor green CRT terminal
CRT = Theme(
    name       = "crt",
    bg         = "#0a0f00",
    bg_panel   = "#0d1500",
    bg_input   = "#0d1500",
    fg         = "#a8ff3e",
    fg_dim     = "#4a7a1a",
    fg_accent  = "#c8ff6e",
    fg_error   = "#ff4444",
    fg_success = "#a8ff3e",
    fg_warn    = "#ffd700",
    btn_bg     = "#1a2e00",
    btn_fg     = "#a8ff3e",
    btn_active = "#2a4800",
    canvas_bg  = "#070c00",
    scaffold   = "#3a5a10",
    body       = "#a8ff3e",
    head       = "#c8ff6e",
    font_mono  = "Courier",
    font_title = "Courier",
)

ALL_THEMES: dict[str, Theme] = {
    "retro": RETRO,
    "dark":  DARK,
    "crt":   CRT,
}
