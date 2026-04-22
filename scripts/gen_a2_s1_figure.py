"""
gen_a2_s1_figure.py — Build the 2x2 supervisor-facing figure for A2-S1.

Reproducibly regenerates the Stage-1 figure (visible-mode divergence markers)
from Week-3 HLLC and Rusanov sample outputs. Stage 2 (A2-S2) should swap the
mode from "visible" to "noise_floor" and pass the MCA noise_floor.npz paths;
this script's structure stays the same.

Usage:
    python scripts/gen_a2_s1_figure.py
"""

from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt
import numpy as np

# Import the divergence helpers from the sibling script.
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS_DIR)

from plot_divergence_marker import (  # noqa: E402
    COLUMN_MAP,
    DEFAULT_VISIBLE_REL_TOL,
    plot_single_panel,
)

# Week-3 sample outputs live under a legacy directory containing a space.
REPO_ROOT = os.path.abspath(os.path.join(_SCRIPTS_DIR, ".."))
DATA_DIR = os.path.join(REPO_ROOT, "experiments", "week 3", "week4_rusanov", "data")
OUT_PATH = os.path.join(
    REPO_ROOT,
    "experiments", "week4_vfc", "divergence_marker", "visible",
    "hllc_vs_rusanov_sod_statcontact.png",
)

PANELS = [
    # (row, col, test_name, variable_name)
    (0, 0, "sod",                "rho"),
    (0, 1, "sod",                "p"),
    (1, 0, "stationary_contact", "rho"),
    (1, 1, "stationary_contact", "p"),
]

TITLES = {
    "sod":                "Sod shock tube",
    "stationary_contact": "Stationary contact",
}


def _load(test: str, solver: str, variable: str) -> tuple[np.ndarray, np.ndarray]:
    path = os.path.join(DATA_DIR, f"{test}_{solver}.txt")
    data = np.loadtxt(path)
    return data[:, 0], data[:, COLUMN_MAP[variable]]


def main() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(
        f"HLLC vs Rusanov — divergence markers "
        f"(visible mode, rel_tol={DEFAULT_VISIBLE_REL_TOL:.0e})",
        fontsize=13, fontweight="bold",
    )

    for row, col, test, variable in PANELS:
        ax = axes[row, col]
        xa, a = _load(test, "hllc", variable)
        xb, b = _load(test, "rusanov", variable)
        plot_single_panel(
            ax, xa, a, xb, b,
            label_a="HLLC",
            label_b="Rusanov",
            variable=variable,
            mode="visible",
            visible_rel_tol=DEFAULT_VISIBLE_REL_TOL,
            title=f"{TITLES[test]} — {variable}",
        )

    fig.text(
        0.5, 0.01,
        f"Stage 1 visible threshold: |a-b| > "
        f"{DEFAULT_VISIBLE_REL_TOL:.0e} * max(|a|,|b|). "
        f"MCA noise-floor calibration (Stage 2) follows within 1-2 days.",
        ha="center", va="bottom", fontsize=9, color="gray", style="italic",
    )

    fig.tight_layout(rect=[0, 0.03, 1, 0.96])
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    fig.savefig(OUT_PATH, dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
