"""
statistics/inferential_stats.py
Inferential statistics: Student t-test, one-way ANOVA, Chi-squared test.
Each test returns a structured result with the statistic, p-value and verdict.
"""

import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
from dataclasses import dataclass

from config import DARK_BG, TEAL, YELLOW, PINK, CYAN_DIM, OUTPUT_DIR, apply_theme


# Data classes 

@dataclass
class TTestResult:
    group_a: np.ndarray
    group_b: np.ndarray
    statistic: float
    p_value: float
    significant: bool          # at α = 0.05


@dataclass
class AnovaResult:
    groups: list[np.ndarray]
    group_labels: list[str]
    f_statistic: float
    p_value: float
    significant: bool


@dataclass
class ChiSquaredResult:
    observed: np.ndarray
    expected: np.ndarray
    statistic: float
    p_value: float
    degrees_of_freedom: int
    significant: bool


# Core functions

def student_t_test(a: np.ndarray,
                   b: np.ndarray,
                   alpha: float = 0.05) -> TTestResult:
    """Two-sample independent Student t-test."""
    t, p = stats.ttest_ind(a, b)
    return TTestResult(group_a=a, group_b=b,
                       statistic=float(t), p_value=float(p),
                       significant=p < alpha)


def one_way_anova(*groups: np.ndarray,
                  labels: list[str] | None = None,
                  alpha: float = 0.05) -> AnovaResult:
    """One-way ANOVA across an arbitrary number of groups."""
    f, p = stats.f_oneway(*groups)
    if labels is None:
        labels = [f"G{i+1}" for i in range(len(groups))]
    return AnovaResult(groups=list(groups), group_labels=labels,
                       f_statistic=float(f), p_value=float(p),
                       significant=p < alpha)


def chi_squared_test(observed: np.ndarray,
                     alpha: float = 0.05) -> ChiSquaredResult:
    """Chi-squared test of independence on a contingency table."""
    chi2, p, dof, expected = stats.chi2_contingency(observed)
    return ChiSquaredResult(observed=observed, expected=expected,
                            statistic=float(chi2), p_value=float(p),
                            degrees_of_freedom=int(dof),
                            significant=p < alpha)


# Printing

def _verdict(sig: bool) -> str:
    return "Significant ✓" if sig else "Not significant"


def print_results(t_res: TTestResult,
                  anova_res: AnovaResult,
                  chi_res: ChiSquaredResult) -> None:
    print("\n[3] INFERENTIAL STATISTICS")
    print("-" * 45)
    print(f"t-test    |  t = {t_res.statistic:+.3f}  "
          f"p = {t_res.p_value:.4f}  →  {_verdict(t_res.significant)}")
    print(f"ANOVA     |  F = {anova_res.f_statistic:.3f}  "
          f"p = {anova_res.p_value:.4f}  →  {_verdict(anova_res.significant)}")
    print(f"Chi²      |  χ² = {chi_res.statistic:.3f}  "
          f"p = {chi_res.p_value:.4f}  "
          f"df = {chi_res.degrees_of_freedom}  →  {_verdict(chi_res.significant)}")


# Visualisation 

def plot_statistics(t_res: TTestResult,
                    anova_res: AnovaResult,
                    chi_res: ChiSquaredResult,
                    save: bool = True) -> plt.Figure:
    apply_theme()

    fig, axes = plt.subplots(1, 3, figsize=(15, 4), facecolor=DARK_BG)
    fig.suptitle("Inferential Statistics — t-test | ANOVA | Chi-squared",
                 color=YELLOW, fontsize=11, fontweight="bold")

    # t-test: overlapping histograms 
    ax = axes[0]
    ax.hist(t_res.group_a, bins=12, color=TEAL, alpha=0.6, label="Group A")
    ax.hist(t_res.group_b, bins=12, color=PINK, alpha=0.6, label="Group B")
    ax.set_title(f"Student t-test\nt={t_res.statistic:+.3f}  p={t_res.p_value:.3f}",
                 color=YELLOW, fontsize=9)
    ax.legend(fontsize=7, facecolor=DARK_BG, edgecolor=TEAL, labelcolor=TEAL)
    ax.grid(True, alpha=0.3)

    # ANOVA: overlapping histograms
    ax = axes[1]
    colors = [TEAL, PINK, YELLOW]
    for g, c, lbl in zip(anova_res.groups,
                         colors[:len(anova_res.groups)],
                         anova_res.group_labels):
        ax.hist(g, bins=12, color=c, alpha=0.5, label=lbl)
    ax.set_title(f"One-way ANOVA\nF={anova_res.f_statistic:.2f}  p={anova_res.p_value:.4f}",
                 color=YELLOW, fontsize=9)
    ax.legend(fontsize=7, facecolor=DARK_BG, edgecolor=TEAL, labelcolor=TEAL)
    ax.grid(True, alpha=0.3)

    # Chi-squared: contingency table heatmap
    ax = axes[2]
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("cyber", [DARK_BG, CYAN_DIM, YELLOW])
    ax.imshow(chi_res.observed, cmap=cmap, aspect="auto")
    for (i, j), val in np.ndenumerate(chi_res.observed):
        ax.text(j, i, str(val), ha="center", va="center",
                color="white", fontsize=12, fontweight="bold")
    n_rows, n_cols = chi_res.observed.shape
    ax.set_xticks(range(n_cols))
    ax.set_yticks(range(n_rows))
    ax.set_xticklabels([f"Col {i+1}" for i in range(n_cols)])
    ax.set_yticklabels([f"Row {i+1}" for i in range(n_rows)])
    ax.set_title(f"Chi-squared\nχ²={chi_res.statistic:.2f}  p={chi_res.p_value:.4f}",
                 color=YELLOW, fontsize=9)

    plt.tight_layout()
    if save:
        path = OUTPUT_DIR / "statistics.png"
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
        print(f"  [saved] {path}")
    return fig


# Entry point 

def run(seed: int = 42) -> tuple[TTestResult, AnovaResult, ChiSquaredResult]:
    rng = np.random.default_rng(seed)

    # t-test data
    group_a = rng.normal(loc=5.0, scale=1.5, size=30)
    group_b = rng.normal(loc=5.8, scale=1.5, size=30)

    # ANOVA data
    g1 = rng.normal(10,   2, 25)
    g2 = rng.normal(12,   2, 25)
    g3 = rng.normal(10.5, 2, 25)

    # Chi-squared contingency table
    observed = np.array([[30, 10], [15, 45]])

    t_res    = student_t_test(group_a, group_b)
    anova_res = one_way_anova(g1, g2, g3, labels=["G1", "G2", "G3"])
    chi_res  = chi_squared_test(observed)

    print_results(t_res, anova_res, chi_res)
    plot_statistics(t_res, anova_res, chi_res)

    return t_res, anova_res, chi_res


if __name__ == "__main__":
    run()
