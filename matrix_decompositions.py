"""
decompositions/matrix_decompositions.py
SVD, QR and Cholesky decompositions with error verification
and individual visualisations.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.linalg import svd, qr, cholesky
from dataclasses import dataclass

from config import DARK_BG, TEAL, YELLOW, CYAN_DIM, OUTPUT_DIR, apply_theme


# Data classes

@dataclass
class SVDResult:
    U: np.ndarray
    singular_values: np.ndarray
    Vt: np.ndarray
    reconstruction_error: float

    def reconstruct(self) -> np.ndarray:
        S = np.diag(self.singular_values)
        return self.U @ S @ self.Vt


@dataclass
class QRResult:
    Q: np.ndarray
    R: np.ndarray
    reconstruction_error: float
    orthogonality_error: float


@dataclass
class CholeskyResult:
    L: np.ndarray
    reconstruction_error: float


# Core functions

def compute_svd(A: np.ndarray) -> SVDResult:
    """Compute SVD of A and return structured results."""
    U, s, Vt = svd(A)
    S = np.diag(s)
    error = float(np.linalg.norm(A - U @ S @ Vt))
    return SVDResult(U=U, singular_values=s, Vt=Vt, reconstruction_error=error)


def compute_qr(A: np.ndarray) -> QRResult:
    """Compute QR decomposition of A."""
    Q, R = qr(A)
    recon_err  = float(np.linalg.norm(A - Q @ R))
    ortho_err  = float(np.linalg.norm(Q @ Q.T - np.eye(Q.shape[0])))
    return QRResult(Q=Q, R=R,
                    reconstruction_error=recon_err,
                    orthogonality_error=ortho_err)


def compute_cholesky(A: np.ndarray) -> CholeskyResult:
    """
    Compute Cholesky decomposition of A.
    A must be symmetric positive-definite.
    """
    L = cholesky(A, lower=True)
    error = float(np.linalg.norm(A - L @ L.T))
    return CholeskyResult(L=L, reconstruction_error=error)


def make_spd(A: np.ndarray, offset: float = 4.0) -> np.ndarray:
    """Turn any square matrix into a symmetric positive-definite one."""
    return A @ A.T + offset * np.eye(A.shape[0])


# Printing 

def print_results(svd_res: SVDResult,
                  qr_res: QRResult,
                  chol_res: CholeskyResult) -> None:
    print("\n[1] MATRIX DECOMPOSITIONS")
    print("-" * 45)
    print(f"SVD   →  A ≈ U·Σ·Vᵀ")
    print(f"         singular values  : {np.round(svd_res.singular_values, 3)}")
    print(f"         reconstruction ε : {svd_res.reconstruction_error:.2e}")

    print(f"\nQR    →  A = Q·R")
    print(f"         orthogonality ε  : {qr_res.orthogonality_error:.2e}")
    print(f"         reconstruction ε : {qr_res.reconstruction_error:.2e}")

    print(f"\nChol  →  B = L·Lᵀ  (B = AᵀA + 4I)")
    print(f"         reconstruction ε : {chol_res.reconstruction_error:.2e}")


# Visualisation 

def plot_decompositions(A: np.ndarray,
                        svd_res: SVDResult,
                        qr_res: QRResult,
                        save: bool = True) -> plt.Figure:
    apply_theme()
    cmap = LinearSegmentedColormap.from_list("cyber", [DARK_BG, CYAN_DIM, YELLOW])

    fig, axes = plt.subplots(1, 3, figsize=(14, 4), facecolor=DARK_BG)
    fig.suptitle("Matrix Decompositions — SVD | QR | Cholesky",
                 color=YELLOW, fontsize=11, fontweight="bold")

    # Singular values bar chart
    ax = axes[0]
    ax.bar(range(1, len(svd_res.singular_values) + 1),
           svd_res.singular_values, color=TEAL, edgecolor=DARK_BG)
    ax.set_title("SVD — Singular Values", color=YELLOW, fontsize=9)
    ax.set_xlabel("Index"); ax.set_ylabel("σᵢ"); ax.grid(True, alpha=0.3)

    # SVD reconstruction error heatmap
    ax = axes[1]
    err_mat = np.abs(A - svd_res.reconstruct())
    im = ax.imshow(err_mat, cmap=cmap, aspect="auto")
    ax.set_title(f"SVD Reconstruction Error\n(ε = {svd_res.reconstruction_error:.2e})",
                 color=YELLOW, fontsize=9)
    plt.colorbar(im, ax=ax, fraction=0.046)

    # Q matrix heatmap (should look like identity after QᵀQ)
    ax = axes[2]
    QtQ = qr_res.Q @ qr_res.Q.T
    im2 = ax.imshow(QtQ, cmap=cmap, aspect="auto")
    ax.set_title(f"QR — QᵀQ ≈ I\n(ortho ε = {qr_res.orthogonality_error:.2e})",
                 color=YELLOW, fontsize=9)
    plt.colorbar(im2, ax=ax, fraction=0.046)

    plt.tight_layout()
    if save:
        path = OUTPUT_DIR / "decompositions.png"
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
        print(f"  [saved] {path}")
    return fig


# Entry point 

def run(seed: int = 42) -> tuple[SVDResult, QRResult, CholeskyResult]:
    rng = np.random.default_rng(seed)
    A   = rng.standard_normal((4, 4))
    B   = make_spd(A)

    svd_res  = compute_svd(A)
    qr_res   = compute_qr(A)
    chol_res = compute_cholesky(B)

    print_results(svd_res, qr_res, chol_res)
    plot_decompositions(A, svd_res, qr_res)

    return svd_res, qr_res, chol_res


if __name__ == "__main__":
    run()
