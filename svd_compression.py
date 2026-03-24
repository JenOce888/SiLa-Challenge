"""
compression/svd_compression.py
Image compression via truncated SVD.
Generates a synthetic test image and compresses it at multiple ranks.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from dataclasses import dataclass, field

from config import DARK_BG, TEAL, YELLOW, CYAN_DIM, PINK, OUTPUT_DIR, apply_theme


# Data classes

@dataclass
class CompressionResult:
    rank: int
    image: np.ndarray
    storage_ratio: float       # fraction of original pixel count
    frobenius_error: float     # relative Frobenius norm error


@dataclass
class SVDCompressionReport:
    original: np.ndarray
    size: int                              # image is size × size
    singular_values: np.ndarray
    results: list[CompressionResult] = field(default_factory=list)


# Image generator 

def make_test_image(size: int = 128) -> np.ndarray:
    """
    Generate a deterministic synthetic grayscale image using
    superimposed sinusoidal patterns.
    """
    i = np.arange(size).reshape(-1, 1)
    j = np.arange(size).reshape(1, -1)
    img = (np.sin(i * 0.15) * np.cos(j * 0.10)
           + 0.4 * np.sin(i * 0.05 + j * 0.08)
           + 0.3 * np.cos(i * 0.20 - j * 0.15))
    return img


# Core functions 

def compress_at_rank(U: np.ndarray,
                     s: np.ndarray,
                     Vt: np.ndarray,
                     rank: int,
                     img_size: int) -> CompressionResult:
    """Reconstruct image from top-`rank` singular triplets."""
    img_r = U[:, :rank] @ np.diag(s[:rank]) @ Vt[:rank, :]

    # Ratio of stored values vs full pixel matrix
    stored = rank * (img_size + img_size + 1)
    ratio  = stored / img_size ** 2

    # Relative Frobenius error
    original = U @ np.diag(s) @ Vt
    fro_err  = np.linalg.norm(original - img_r, "fro") / np.linalg.norm(original, "fro")

    return CompressionResult(rank=rank, image=img_r,
                             storage_ratio=float(ratio),
                             frobenius_error=float(fro_err))


def run_compression(img: np.ndarray,
                    ranks: list[int]) -> SVDCompressionReport:
    """Perform full SVD and compress at every requested rank."""
    U, s, Vt = np.linalg.svd(img, full_matrices=False)
    report = SVDCompressionReport(original=img,
                                  size=img.shape[0],
                                  singular_values=s)
    for r in ranks:
        report.results.append(compress_at_rank(U, s, Vt, r, img.shape[0]))
    return report


# Printing 

def print_results(report: SVDCompressionReport) -> None:
    print("\n[4] SVD IMAGE COMPRESSION")
    print("-" * 45)
    for r in report.results:
        print(f"  rank {r.rank:4d}  →  {r.storage_ratio*100:5.1f}% storage  "
              f"|  error = {r.frobenius_error:.4f}")


# Visualisation

def plot_compression(report: SVDCompressionReport,
                     save: bool = True) -> plt.Figure:
    apply_theme()
    cmap = LinearSegmentedColormap.from_list("cyber", [DARK_BG, CYAN_DIM, YELLOW])
    n = len(report.results)

    fig, axes = plt.subplots(2, n // 2 + 1, figsize=(16, 7), facecolor=DARK_BG)
    fig.suptitle("SVD Image Compression — Rank Approximations",
                 color=YELLOW, fontsize=11, fontweight="bold")

    # Row 0, col 0: singular value spectrum + cumulative energy
    ax = axes[0, 0]
    s = report.singular_values
    energy = np.cumsum(s ** 2) / np.sum(s ** 2)
    ax.plot(energy[:80], color=TEAL, lw=2)
    ax.fill_between(range(80), energy[:80], alpha=0.2, color=TEAL)
    for r in report.results:
        ax.axvline(r.rank, color=PINK, linewidth=0.9, linestyle=":")
        ax.text(r.rank + 0.5, 0.02, f"r={r.rank}",
                color=PINK, fontsize=6, rotation=90)
    ax.set_title("Cumulative Energy", color=YELLOW, fontsize=9)
    ax.set_xlabel("Rank"); ax.set_ylabel("Energy (%)"); ax.grid(True, alpha=0.3)

    # Row 0, col 1: original image
    ax = axes[0, 1]
    ax.imshow(report.original, cmap=cmap, aspect="auto")
    ax.set_title("Original", color=YELLOW, fontsize=9)
    ax.axis("off")

    # Remaining axes: compressed versions
    flat_axes = [axes[r][c] for r in range(2) for c in range(n // 2 + 1)]
    used = {(0, 0), (0, 1)}
    unused_axes = [ax for i, ax in enumerate(flat_axes)
                   if (i // (n // 2 + 1), i % (n // 2 + 1)) not in used]

    for ax, res in zip(unused_axes, report.results):
        ax.imshow(res.image, cmap=cmap, aspect="auto")
        ax.set_title(f"Rank {res.rank}  "
                     f"({res.storage_ratio*100:.0f}% storage  "
                     f"ε={res.frobenius_error:.3f})",
                     color=YELLOW, fontsize=8)
        ax.axis("off")

    # Hide leftover axes
    for ax in unused_axes[len(report.results):]:
        ax.set_visible(False)

    plt.tight_layout()
    if save:
        path = OUTPUT_DIR / "compression.png"
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
        print(f"  [saved] {path}")
    return fig


# Entry point 

def run() -> SVDCompressionReport:
    img    = make_test_image(size=128)
    report = run_compression(img, ranks=[1, 5, 15, 40])
    print_results(report)
    plot_compression(report)
    return report


if __name__ == "__main__":
    run()
