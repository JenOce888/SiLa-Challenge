"""
visualization/linear_transform_3d.py
3-D visualisation of a linear transformation applied to
the unit sphere using mpl_toolkits.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D          # noqa: F401 (registers 3-D projection)
from dataclasses import dataclass

from config import DARK_BG, TEAL, CYAN_DIM, YELLOW, PINK, OUTPUT_DIR, apply_theme


# Data class

@dataclass
class TransformResult:
    matrix: np.ndarray
    eigenvalues: np.ndarray
    eigenvectors: np.ndarray
    determinant: float
    condition_number: float


# Core function

def analyse_transform(M: np.ndarray) -> TransformResult:
    """Return eigendecomposition and key scalar properties of M."""
    eigenvalues, eigenvectors = np.linalg.eig(M)
    return TransformResult(
        matrix=M,
        eigenvalues=eigenvalues,
        eigenvectors=eigenvectors,
        determinant=float(np.linalg.det(M)),
        condition_number=float(np.linalg.cond(M)),
    )


def _unit_sphere(resolution: int = 40) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (x, y, z) grids for the unit sphere."""
    theta = np.linspace(0, 2 * np.pi, resolution)
    phi   = np.linspace(0, np.pi,     resolution)
    T, P  = np.meshgrid(theta, phi)
    xs = np.sin(P) * np.cos(T)
    ys = np.sin(P) * np.sin(T)
    zs = np.cos(P)
    return xs, ys, zs


def apply_transform(M: np.ndarray,
                    xs: np.ndarray,
                    ys: np.ndarray,
                    zs: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Apply matrix M to every point on the sphere grids."""
    pts   = np.stack([xs.ravel(), ys.ravel(), zs.ravel()])
    pts_t = M @ pts
    shape = xs.shape
    return pts_t[0].reshape(shape), pts_t[1].reshape(shape), pts_t[2].reshape(shape)


# Printing

def print_results(res: TransformResult) -> None:
    print("\n[5] 3-D LINEAR TRANSFORMATION")
    print("-" * 45)
    print(f"  Matrix M:\n{np.round(res.matrix, 3)}")
    print(f"  Eigenvalues   : {np.round(np.real(res.eigenvalues), 3)}")
    print(f"  Determinant   : {res.determinant:.4f}")
    print(f"  Condition no. : {res.condition_number:.4f}")


# Visualisation

def plot_transform(res: TransformResult, save: bool = True) -> plt.Figure:
    apply_theme()

    fig = plt.figure(figsize=(13, 5), facecolor=DARK_BG)
    fig.suptitle("3-D Linear Transformation of the Unit Sphere",
                 color=YELLOW, fontsize=11, fontweight="bold")

    xs, ys, zs = _unit_sphere(resolution=50)
    xt, yt, zt = apply_transform(res.matrix, xs, ys, zs)

    def _style_3d(ax: plt.Axes) -> None:
        ax.set_facecolor(DARK_BG)
        ax.tick_params(colors=TEAL, labelsize=7)
        for pane in [ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane]:
            pane.fill = False
            pane.set_edgecolor(TEAL + "44")

    # Left: unit sphere
    ax1 = fig.add_subplot(121, projection="3d")
    ax1.plot_surface(xs, ys, zs, color=CYAN_DIM, alpha=0.55, linewidth=0)
    ax1.set_title("Unit Sphere  S²", color=YELLOW, fontsize=9)
    _style_3d(ax1)

    # Right: transformed ellipsoid 
    ax2 = fig.add_subplot(122, projection="3d")
    ax2.plot_surface(xt, yt, zt, color=PINK, alpha=0.55, linewidth=0)

    # Draw eigenvectors as arrows
    origin = np.zeros(3)
    for vec in res.eigenvectors.T:
        real_vec = np.real(vec)
        ax2.quiver(*origin, *real_vec,
                   color=YELLOW, linewidth=1.5, arrow_length_ratio=0.2)

    ax2.set_title(
        f"M · S²   (det={res.determinant:.2f}  κ={res.condition_number:.2f})",
        color=YELLOW, fontsize=9)
    _style_3d(ax2)

    plt.tight_layout()
    if save:
        path = OUTPUT_DIR / "linear_transform_3d.png"
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
        print(f"  [saved] {path}")
    return fig


# Entry point

DEFAULT_MATRIX = np.array([
    [1.2, 0.3, 0.1],
    [0.0, 0.9, 0.4],
    [0.1, 0.2, 1.5],
])


def run(M: np.ndarray = DEFAULT_MATRIX) -> TransformResult:
    result = analyse_transform(M)
    print_results(result)
    plot_transform(result)
    return result


if __name__ == "__main__":
    run()
