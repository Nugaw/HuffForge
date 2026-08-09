"""
Shared color palette and fonts for the dark "Huffman Studio" look. Every
page in gui.py and the tree-drawing code in tree_canvas.py import from
here, so the whole app stays visually consistent instead of each window
picking its own colors.
"""

import customtkinter as ctk

# -- backgrounds -------------------------------------------------------
BG = "#0b0f19"            # window background
CARD_BG = "#131826"       # card / panel background
CARD_BG_LIGHT = "#1a2033"  # slightly raised surface (e.g. plain tree nodes)
BORDER = "#232a3d"
BORDER_LIGHT = "#2e3650"

# -- accents -------------------------------------------------------------
CYAN = "#22d3ee"
CYAN_HOVER = "#0e9fb8"
CYAN_DIM = "#155e75"

GREEN = "#4ade80"
GREEN_HOVER = "#22c55e"

AMBER = "#f59e0b"
AMBER_DIM = "#92400e"

PURPLE = "#8b5cf6"

# -- text ---------------------------------------------------------------
TEXT_PRIMARY = "#f1f5f9"
TEXT_SECONDARY = "#94a3b8"
TEXT_MUTED = "#64748b"

# -- fonts ----------------------------------------------------------------
SANS = "Segoe UI"   # falls back to the platform default where unavailable
MONO = "Courier"    # one of Tk's built-in cross-platform generic families

# Everything below was originally sized for a denser, web-style layout and
# read as too small/cramped on a desktop app. This one multiplier scales
# every CTkFont produced by font()/mono_font() at once - bump it here
# instead of hunting down every call site.
FONT_SCALE = 1.3


def font(size, weight="normal", family=SANS):
    return ctk.CTkFont(family=family, size=round(size * FONT_SCALE), weight=weight)


def mono_font(size, weight="normal"):
    scaled = round(size * FONT_SCALE)
    return (MONO, scaled, weight) if weight != "normal" else (MONO, scaled)


def canvas_font(size, weight="normal", family=SANS):
    """For raw tkinter Canvas/Text widgets, which take a plain tuple
    instead of a CTkFont - scaled the same way so Canvas-drawn text
    (the tree nodes, the drop zone, the savings gauge) grows to match."""
    scaled = round(size * FONT_SCALE)
    return (family, scaled, weight) if weight != "normal" else (family, scaled)