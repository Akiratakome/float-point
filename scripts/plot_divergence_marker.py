"""
plot_divergence_marker.py — HLLC vs Rusanov first-divergence marker.

Stage 1 (A2-S1): implements "visible" mode only.
Stage 2 (A2-S2): will fill in noise_floor and strict_fp modes.
"""

from __future__ import annotations

import argparse
import os
from typing import Literal, Optional

import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# Module-level constants — no magic numbers elsewhere
# ---------------------------------------------------------------------------
DEFAULT_SAFETY_SIGMA = 3.0       # reserved for noise_floor mode (not used in visible mode)
DEFAULT_K_GRAD = 1.0             # reserved for noise_floor mode
DEFAULT_K_EPS_FALLBACK = 10.0   # reserved for strict_fp mode
DEFAULT_VISIBLE_REL_TOL = 1e-3  # human-eye threshold, explicitly non-statistical

# Column mapping in data files: x  rho  u  v  p
COLUMN_MAP = {"rho": 1, "u": 2, "p": 4}

Mode = Literal["noise_floor", "strict_fp", "visible"]


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def first_divergence_index(
    a: np.ndarray,
    b: np.ndarray,
    mode: Mode = "noise_floor",
    # noise_floor mode:
    noise_floor_a: Optional[np.ndarray] = None,
    noise_floor_b: Optional[np.ndarray] = None,
    safety: float = DEFAULT_SAFETY_SIGMA,
    # shared:
    k_grad: float = DEFAULT_K_GRAD,
    abs_floor_frac: Optional[float] = None,
    # strict_fp fallback:
    source_precision: Literal["float32", "float64"] = "float64",
    k_eps: float = DEFAULT_K_EPS_FALLBACK,
    # visible mode:
    visible_rel_tol: float = DEFAULT_VISIBLE_REL_TOL,
) -> Optional[int]:
    """Return the first index i where |a - b| exceeds the per-mode tolerance envelope.

    Parameters
    ----------
    a, b : np.ndarray
        1-D arrays of equal length to compare.
    mode : {"visible", "noise_floor", "strict_fp"}
        "visible"     — presentation-level check; no statistical claim.
        "noise_floor" — Stage 2 (A2-S2); requires MCA noise_floor.npz.
        "strict_fp"   — Stage 2 (A2-S2); strict floating-point threshold.
    visible_rel_tol : float
        Relative tolerance for visible mode: tol = visible_rel_tol * max(|a|, |b|).

    Returns
    -------
    int or None
        Index of first divergence, or None if arrays agree everywhere within tolerance.
    """
    if mode == "visible":
        tol = visible_rel_tol * np.maximum(np.abs(a), np.abs(b))
        diff = np.abs(a - b)
        idx = np.where(diff > tol)[0]
        return int(idx[0]) if len(idx) else None

    elif mode in ("noise_floor", "strict_fp"):
        raise NotImplementedError(
            "Stage 2 (A2-S2): requires MCA noise_floor.npz; see plan §A2.1-§A2.5"
        )

    else:
        raise ValueError(f"Unknown mode: {mode!r}. Choose from 'visible', 'noise_floor', 'strict_fp'.")


# ---------------------------------------------------------------------------
# Single-panel plot helper
# ---------------------------------------------------------------------------

def plot_single_panel(
    ax: plt.Axes,
    x_a: np.ndarray,
    a: np.ndarray,
    x_b: np.ndarray,
    b: np.ndarray,
    label_a: str,
    label_b: str,
    variable: str,
    mode: Mode = "visible",
    visible_rel_tol: float = DEFAULT_VISIBLE_REL_TOL,
    title: Optional[str] = None,
) -> Optional[int]:
    """Plot two solver lines and annotate the first-divergence index.

    Returns the first-divergence index (or None).
    """
    ax.plot(x_a, a, color="tab:blue", linewidth=1.5, label=label_a)
    ax.plot(x_b, b, color="tab:red", linewidth=1.5, linestyle="--", label=label_b)

    div_idx = first_divergence_index(a, b, mode=mode, visible_rel_tol=visible_rel_tol)

    if div_idx is not None:
        xd = x_a[div_idx]
        yd = a[div_idx]
        ax.plot(xd, yd, "rx", markersize=10, markeredgewidth=2.5,
                label=f"First divergence i={div_idx}")
        ax.annotate(
            f"i={div_idx}\nx={xd:.3f}",
            xy=(xd, yd),
            xytext=(xd + 0.03 * (x_a[-1] - x_a[0]), yd),
            fontsize=7,
            color="darkred",
            arrowprops=dict(arrowstyle="->", color="darkred", lw=0.8),
        )
    else:
        ax.text(
            0.98, 0.98,
            f"No divergence detected\nat rel_tol={visible_rel_tol:.0e}",
            transform=ax.transAxes,
            ha="right", va="top",
            fontsize=7, color="gray",
        )

    if title:
        ax.set_title(title, fontsize=9)
    ax.set_xlabel("x", fontsize=8)
    ax.set_ylabel(variable, fontsize=8)
    ax.legend(fontsize=7)
    ax.tick_params(labelsize=7)

    return div_idx


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _load_column(path: str, variable: str) -> tuple[np.ndarray, np.ndarray]:
    """Load (x, var) arrays from a data file."""
    data = np.loadtxt(path)
    x = data[:, 0]
    col = COLUMN_MAP[variable]
    var = data[:, col]
    return x, var


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Plot HLLC vs Rusanov with first-divergence marker."
    )
    p.add_argument("--input-a", required=True, metavar="PATH", help="Path to solver A data file.")
    p.add_argument("--label-a", default="A", metavar="STR", help="Label for solver A.")
    p.add_argument("--input-b", required=True, metavar="PATH", help="Path to solver B data file.")
    p.add_argument("--label-b", default="B", metavar="STR", help="Label for solver B.")
    p.add_argument("--variable", choices=list(COLUMN_MAP.keys()), default="rho",
                   help="Variable to plot (rho=col 1, u=col 2, p=col 4).")
    p.add_argument("--mode", choices=["visible", "noise_floor", "strict_fp"], default="visible",
                   help="Divergence-detection mode (default: visible).")
    p.add_argument("--visible-rel-tol", type=float, default=DEFAULT_VISIBLE_REL_TOL,
                   metavar="FLOAT", help="Relative tolerance for visible mode.")
    p.add_argument("--output", required=True, metavar="PATH", help="Output PNG path.")
    p.add_argument("--title", default=None, metavar="STR", help="Optional figure title.")
    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    x_a, a = _load_column(args.input_a, args.variable)
    x_b, b = _load_column(args.input_b, args.variable)

    fig, ax = plt.subplots(figsize=(7, 4))
    div_idx = plot_single_panel(
        ax, x_a, a, x_b, b,
        label_a=args.label_a,
        label_b=args.label_b,
        variable=args.variable,
        mode=args.mode,
        visible_rel_tol=args.visible_rel_tol,
        title=args.title,
    )

    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    fig.savefig(args.output, dpi=150)
    plt.close(fig)

    if div_idx is not None:
        print(f"First divergence at index {div_idx}, x={x_a[div_idx]:.4f}")
    else:
        print(f"No divergence detected at rel_tol={args.visible_rel_tol:.0e}")


if __name__ == "__main__":
    main()
