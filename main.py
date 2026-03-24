"""
main.py
DAY 16 | Linear Algebra & Advanced Statistics
=============================================
Orchestrates all five modules:
  1. decompositions  — SVD, QR, Cholesky
  2. regression      — Least squares (Fourier basis)
  3. statistics      — t-test, ANOVA, Chi-squared
  4. compression     — SVD image compression
  5. visualization   — 3-D linear transformation

Run:
    python main.py
"""

import sys
import time
from pathlib import Path

# Allow sibling-module imports when run from repo root
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np

from config import RANDOM_SEED, OUTPUT_DIR, apply_theme

from decompositions.matrix_decompositions import run as run_decompositions
from regression.least_squares            import run as run_regression
from statistics.inferential_stats        import run as run_statistics
from compression.svd_compression         import run as run_compression
from visualization.linear_transform_3d   import run as run_visualization



# Dashboard — combined figure

def build_dashboard() -> None:
    """
    Assemble a single summary dashboard from all saved sub-figures
    (a lightweight reference sheet).
    """
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    import matplotlib.gridspec as gridspec
    from config import DARK_BG, TEAL, YELLOW

    apply_theme()

    images = {
        "Decompositions":      OUTPUT_DIR / "decompositions.png",
        "Regression":          OUTPUT_DIR / "regression.png",
        "Statistics":          OUTPUT_DIR / "statistics.png",
        "SVD Compression":     OUTPUT_DIR / "compression.png",
        "3-D Transform":       OUTPUT_DIR / "linear_transform_3d.png",
    }

    fig = plt.figure(figsize=(22, 18), facecolor=DARK_BG)
    fig.suptitle(
        "DAY 16  |  Linear Algebra & Advanced Statistics — Dashboard",
        color=TEAL, fontsize=14, fontweight="bold", y=0.99
    )

    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.08, wspace=0.04)
    positions = [
        gs[0, 0], gs[0, 1],
        gs[1, 0], gs[1, 1],
        gs[2, :],
    ]

    for (title, path), pos in zip(images.items(), positions):
        ax = fig.add_subplot(pos)
        if path.exists():
            img = mpimg.imread(path)
            ax.imshow(img)
        ax.set_title(title, color=YELLOW, fontsize=9, pad=4)
        ax.axis("off")

    out = OUTPUT_DIR / "day16_dashboard.png"
    fig.savefig(out, dpi=130, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"\n  [dashboard saved] {out}")


# Main

def main() -> None:
    print("=" * 60)
    print("  DAY 16 — LINEAR ALGEBRA & ADVANCED STATISTICS")
    print("=" * 60)

    t0 = time.perf_counter()

    run_decompositions(seed=RANDOM_SEED)
    run_regression(seed=RANDOM_SEED)
    run_statistics(seed=RANDOM_SEED)
    run_compression()
    run_visualization()

    build_dashboard()

    elapsed = time.perf_counter() - t0
    print(f"\n{'=' * 60}")
    print(f"  All modules completed in {elapsed:.2f}s")
    print(f"  Outputs → {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
