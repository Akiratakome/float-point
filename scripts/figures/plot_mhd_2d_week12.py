#!/usr/bin/env python3
"""Week 12 Part 2 (2D MHD + GLM) supervisor figures.

Reads the validation artefacts under experiments/week12/mhd_2d/ and produces:

  1. divb_cleaning_decay.png -- max|div(B)| vs time for glm_cr in {0, 0.18, 0.36}
     on the doubly-periodic Gaussian-Bx-bump test. Shows GLM cleaning vs the
     no-damping control.
  2. divb_cleaning_heatmap.png -- the div(B) field at t=0.5 for the control
     (cr=0) vs the cleaned run (cr=0.18), side by side on a shared scale.

Run:  python scripts/figures/plot_mhd_2d_week12.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from io_helper import read_binary  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
DIVB = ROOT / "experiments" / "week12" / "mhd_2d" / "divb_clean"
OUT = ROOT / "experiments" / "week12" / "mhd_2d" / "figures"
BX, BY = 4, 5


def divergence(arr: np.ndarray, dx: float, dy: float) -> np.ndarray:
    """Periodic central-difference div(B) for a (ny, nx, nvars) field."""
    Bx = arr[:, :, BX].astype(np.float64)
    By = arr[:, :, BY].astype(np.float64)
    dBxdx = (np.roll(Bx, -1, axis=1) - np.roll(Bx, 1, axis=1)) / (2 * dx)
    dBydy = (np.roll(By, -1, axis=0) - np.roll(By, 1, axis=0)) / (2 * dy)
    return dBxdx + dBydy


def plot_decay(summary: dict) -> pathlib.Path:
    table = summary["decay_table"]
    styles = {"0.0": ("C3", "o", "c_r = 0 (no damping, control)"),
              "0.18": ("C0", "s", "c_r = 0.18"),
              "0.36": ("C2", "^", "c_r = 0.36")}
    fig, ax = plt.subplots(figsize=(7, 5))
    for cr, (color, marker, label) in styles.items():
        if cr not in table:
            continue
        rows = sorted(table[cr], key=lambda r: r["t_end"])
        t = [r["t_end"] for r in rows]
        dmax = [r["divB_max"] for r in rows]
        ax.plot(t, dmax, color=color, marker=marker, label=label)
    ax.set_xlabel("time")
    ax.set_ylabel(r"max $|\nabla\cdot B|$")
    ax.set_title("GLM divergence cleaning — Gaussian $B_x$ bump (128$^2$, doubly periodic)")
    ax.grid(alpha=0.3)
    ax.legend()
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "divb_cleaning_decay.png"
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_heatmaps(summary: dict) -> pathlib.Path:
    grids = summary["figure_grids"]
    h_ctrl, a_ctrl = read_binary(grids["cr0.0_t0.5"])
    h_clean, a_clean = read_binary(grids["cr0.18_t0.5"])
    dx = 1.0 / h_ctrl.nx
    dy = 1.0 / h_ctrl.ny
    div_ctrl = divergence(a_ctrl, dx, dy)
    div_clean = divergence(a_clean, dx, dy)
    vmax = float(np.abs(div_ctrl).max())

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), constrained_layout=True)
    for ax, field, title in (
        (axes[0], div_ctrl, f"control  c_r=0   max|div B|={np.abs(div_ctrl).max():.2f}"),
        (axes[1], div_clean, f"cleaned  c_r=0.18   max|div B|={np.abs(div_clean).max():.2f}"),
    ):
        im = ax.imshow(field, origin="lower", extent=(0, 1, 0, 1),
                       cmap="RdBu_r", vmin=-vmax, vmax=vmax)
        ax.set_title(title)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle(r"$\nabla\cdot B$ at t=0.5 (shared scale): GLM cleaning suppresses the divergence",
                 fontweight="bold")
    out = OUT / "divb_cleaning_heatmap.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def main():
    summary = json.loads((DIVB / "summary.json").read_text(encoding="utf-8"))
    p1 = plot_decay(summary)
    p2 = plot_heatmaps(summary)
    print(f"wrote {p1}")
    print(f"wrote {p2}")


if __name__ == "__main__":
    main()
