#!/usr/bin/env python3
"""Week 12 Brio-Wu 1D MHD progress figures.

Reads the committed-discipline Brio-Wu outputs under
experiments/week12/brio_wu_1d/ and produces two supervisor-facing figures:

  1. brio_wu_profiles.png  -- rho / vx / By / p at t=0.1, N=800 vs the
                              N=8000 self-converged double reference.
  2. brio_wu_convergence.png -- L1/L2 density error vs N (log-log) from
                                summary.json, with a first-order guide line.

1D ideal MHD, gamma = 2. Conserved layout (MhdNVars=9):
  [rho, mx, my, mz, Bx, By, Bz, E, psi].

Run:  python scripts/figures/plot_brio_wu_1d.py
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
DATA = ROOT / "experiments" / "week12" / "brio_wu_1d"
OUT = DATA / "figures"
GAMMA = 2.0

# MhdIdx
RHO, MX, MY, MZ, BX, BY, BZ, E, PSI = range(9)


def primitives(path: pathlib.Path):
    """Return (x, rho, vx, By, p) for a 1D MHD binary."""
    h, arr = read_binary(path)
    if h.nvars != 9:
        raise ValueError(f"{path} is not a 9-var MHD field (nvars={h.nvars})")
    a = arr[0].astype(np.float64)  # (nx, 9)
    rho = a[:, RHO]
    vx = a[:, MX] / rho
    By = a[:, BY]
    v2 = (a[:, MX] ** 2 + a[:, MY] ** 2 + a[:, MZ] ** 2) / (rho ** 2)
    b2 = a[:, BX] ** 2 + a[:, BY] ** 2 + a[:, BZ] ** 2
    p = (GAMMA - 1.0) * (a[:, E] - 0.5 * rho * v2 - 0.5 * b2)
    x = (np.arange(h.nx) + 0.5) / h.nx
    return x, rho, vx, By, p


def plot_profiles():
    xr, rr, vr, br, pr = primitives(DATA / "bw_8000.bin")
    x8, r8, v8, b8, p8 = primitives(DATA / "bw_800.bin")
    panels = [
        ("Density  rho", rr, r8),
        ("Velocity  v_x", vr, v8),
        ("Transverse field  B_y", br, b8),
        ("Pressure  p", pr, p8),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5), sharex=True)
    for ax, (title, ref, num) in zip(axes.flat, panels):
        ax.plot(xr, ref, color="0.6", lw=2.2, label="N=8000 reference (double)")
        ax.plot(x8, num, color="C3", lw=0.0, marker=".", ms=2.5,
                label="N=800 (double)")
        ax.set_title(title)
        ax.grid(alpha=0.3)
    for ax in axes[1]:
        ax.set_xlabel("x")
    axes[0, 0].legend(loc="upper right", fontsize=8)
    fig.suptitle("Brio-Wu 1D MHD shock tube at t = 0.1  (gamma = 2, HLL, MUSCL-Hancock)",
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    out = OUT / "brio_wu_profiles.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_convergence():
    summary = json.loads((DATA / "summary.json").read_text(encoding="utf-8"))
    rows = sorted(summary["rows"], key=lambda r: r["nx"])
    N = np.array([r["nx"] for r in rows], dtype=float)
    L1 = np.array([r["L1"] for r in rows])
    L2 = np.array([r["L2"] for r in rows])

    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.loglog(N, L1, "o-", color="C0", label="L1 (density)")
    ax.loglog(N, L2, "s-", color="C1", label="L2 (density)")
    guide = L1[0] * (N[0] / N)  # first-order reference through the first point
    ax.loglog(N, guide, "k--", lw=1, label="first-order slope")
    # observed order between coarsest and finest
    order_L1 = np.log(L1[0] / L1[-1]) / np.log(N[-1] / N[0])
    ax.set_xlabel("grid resolution N")
    ax.set_ylabel("error vs N=8000 reference")
    ax.set_title(f"Brio-Wu self-convergence  (observed L1 order ~ {order_L1:.2f})")
    ax.grid(which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    out = OUT / "brio_wu_convergence.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out, order_L1


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    p1 = plot_profiles()
    p2, order = plot_convergence()
    print(f"wrote {p1}")
    print(f"wrote {p2}  (observed L1 order ~ {order:.2f})")


if __name__ == "__main__":
    main()
