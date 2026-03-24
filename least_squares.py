"""
regression/least_squares.py
Over-determined system solved via least squares (SVD pseudo-inverse).
Uses a truncated Fourier basis as the design matrix.
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass

from config import DARK_BG, TEAL, YELLOW, PINK, OUTPUT_DIR, apply_theme


# Data class 

@dataclass
class RegressionResult:
    x: np.ndarray
    y_noisy: np.ndarray
    y_true: np.ndarray
    y_fit: np.ndarray
    coefficients: np.ndarray
    r_squared: float
    rank: int


# Design matrix builders 

def fourier_design_matrix(x: np.ndarray, order: int = 3) -> np.ndarray:
    """
    Build a Fourier regression design matrix of given harmonic order.

    Columns: [1, sin(x), cos(x), sin(2x), cos(2x), ..., sin(Nx), cos(Nx)]
    """
    cols = [np.ones_like(x)]
    for k in range(1, order + 1):
        cols.append(np.sin(k * x))
        cols.append(np.cos(k * x))
    return np.column_stack(cols)


# Core function

def fit_least_squares(x: np.ndarray,
                      y: np.ndarray,
                      y_true: np.ndarray,
                      order: int = 3) -> RegressionResult:
    """
    Fit an over-determined system with numpy's lstsq (SVD internally).

    Parameters
    ----------
    x      : 1-D array of sample points
    y      : noisy observations
    y_true : ground-truth signal (for comparison only)
    order  : harmonic order of the Fourier basis
    """
    X = fourier_design_matrix(x, order=order)
    coeffs, _, rank, _ = np.linalg.lstsq(X, y, rcond=None)
    y_fit = X @ coeffs

    ss_res = np.sum((y - y_fit) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = float(1 - ss_res / ss_tot)

    return RegressionResult(
        x=x, y_noisy=y, y_true=y_true, y_fit=y_fit,
        coefficients=coeffs, r_squared=r2, rank=int(rank)
    )


# Printing

def print_results(res: RegressionResult) -> None:
    print("\n[2] LEAST SQUARES (over-determined system)")
    print("-" * 45)
    print(f"  Coefficients : {np.round(res.coefficients, 3)}")
    print(f"  R²           : {res.r_squared:.4f}")
    print(f"  Matrix rank  : {res.rank}")


# Visualisation 

def plot_regression(res: RegressionResult, save: bool = True) -> plt.Figure:
    apply_theme()

    fig, axes = plt.subplots(1, 2, figsize=(12, 4), facecolor=DARK_BG)
    fig.suptitle("Least Squares — Fourier Basis Regression",
                 color=YELLOW, fontsize=11, fontweight="bold")

    # Fit vs ground truth
    ax = axes[0]
    ax.scatter(res.x, res.y_noisy, color=PINK, s=18, alpha=0.7,
               label="Noisy data", zorder=3)
    ax.plot(res.x, res.y_true, color=YELLOW, lw=1.5,
            linestyle="--", label="True signal", zorder=4)
    ax.plot(res.x, res.y_fit, color=TEAL, lw=2,
            label=f"Fitted  (R²={res.r_squared:.3f})", zorder=5)
    ax.set_title("Fit vs True Signal", color=YELLOW, fontsize=9)
    ax.legend(fontsize=7, facecolor=DARK_BG, edgecolor=TEAL, labelcolor=TEAL)
    ax.grid(True, alpha=0.3)

    # Residuals
    ax = axes[1]
    residuals = res.y_noisy - res.y_fit
    ax.scatter(res.x, residuals, color=PINK, s=14, alpha=0.8)
    ax.axhline(0, color=TEAL, lw=1.2, linestyle="--")
    ax.fill_between(res.x, residuals, alpha=0.15, color=PINK)
    ax.set_title("Residuals", color=YELLOW, fontsize=9)
    ax.set_xlabel("x"); ax.set_ylabel("y − ŷ")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    if save:
        path = OUTPUT_DIR / "regression.png"
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
        print(f"  [saved] {path}")
    return fig


#  Entry point 

def run(seed: int = 42) -> RegressionResult:
    rng   = np.random.default_rng(seed)
    x     = np.linspace(0, 2 * np.pi, 40)
    y_true = 2.5 * np.sin(x) + 1.2 * np.cos(x)
    y_noisy = y_true + rng.standard_normal(len(x)) * 0.4

    result = fit_least_squares(x, y_noisy, y_true, order=3)
    print_results(result)
    plot_regression(result)
    return result


if __name__ == "__main__":
    run()
