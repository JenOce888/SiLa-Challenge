"""
config.py
Shared constants: plot theme, random seed, output path.
"""

import matplotlib.pyplot as plt
from pathlib import Path

# Paths 
OUTPUT_DIR = Path("/mnt/user-data/outputs/day16_lab")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Reproducibility 
RANDOM_SEED = 42

# Cyberpunk colour palette
DARK_BG  = "#0a0f1e"
TEAL     = "#00e5d4"
CYAN_DIM = "#00b4a0"
YELLOW   = "#f0e040"
PINK     = "#ff4daa"
GRID_COL = "#1a2a3a"

def apply_theme() -> None:
    """Apply the global matplotlib dark-cyberpunk theme."""
    plt.rcParams.update({
        "figure.facecolor": DARK_BG,
        "axes.facecolor":   DARK_BG,
        "axes.edgecolor":   TEAL,
        "axes.labelcolor":  TEAL,
        "xtick.color":      TEAL,
        "ytick.color":      TEAL,
        "text.color":       TEAL,
        "grid.color":       GRID_COL,
        "grid.linestyle":   "--",
        "font.family":      "monospace",
    })
