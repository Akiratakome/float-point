#!/usr/bin/env python3
# scripts/figures/plot_lw_style.py
#
# Liska-Wendroff 2003 style 2D visualisation:
#   - jet colormap of pressure
#   - density iso-contours overlaid in black
#   - sparse velocity quiver
#
# This matches Fig. 4.1 (LW3 / Case 3) and Fig. 4.4 (LW12 / Case 12) in
# Liska & Wendroff (2003), SIAM J. Sci. Comput. 25(3):995-1017.
#
# Usage:
#   python scripts/figures/plot_lw_style.py path/to/grid.bin \
#       --p-range 0.0 1.7 --rho-levels 0.16 1.71 0.05 \
#       --out report1/phd-thesis-template-2.4/Figs/report1/lw3_n400_lw_style.png

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from io_helper import IDX_E, IDX_RHO, IDX_RHOU, IDX_RHOV, read_binary  # noqa: E402
from _style import apply, save_pair  # noqa: E402

apply()
GAMMA_DEFAULT = 1.4


def compute_primitives(arr, gamma):
    rho = arr[..., IDX_RHO]
    u = arr[..., IDX_RHOU] / rho
    v = arr[..., IDX_RHOV] / rho
    energy = arr[..., IDX_E]
    p = (gamma - 1.0) * (energy - 0.5 * rho * (u * u + v * v))
    return rho, u, v, p


def render_lw_style(arr, header, *, gamma, out_stem, outdir,
                    p_vmin, p_vmax, rho_lo, rho_hi, rho_step, arrow_stride):
    rho, u, v, p = compute_primitives(arr, gamma)
    ny, nx = rho.shape
    Lx = nx * header.dx
    Ly = ny * header.dy
    extent = [0, Lx, 0, Ly]

    if p_vmin is None:
        p_vmin = float(np.nanmin(p))
    if p_vmax is None:
        p_vmax = float(np.nanmax(p))

    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    im = ax.imshow(
        p, origin="lower", extent=extent, cmap="jet",
        vmin=p_vmin, vmax=p_vmax, aspect="equal",
    )

    levels = np.arange(rho_lo, rho_hi + 0.5 * rho_step, rho_step)
    xs = (np.arange(nx) + 0.5) * header.dx
    ys = (np.arange(ny) + 0.5) * header.dy
    X, Y = np.meshgrid(xs, ys)
    ax.contour(X, Y, rho, levels=levels, colors="black", linewidths=0.4)

    s = max(1, arrow_stride)
    ax.quiver(
        X[::s, ::s], Y[::s, ::s], u[::s, ::s], v[::s, ::s],
        color="black", scale=None, width=0.0018, alpha=0.7,
    )

    ax.set_xlabel("x")
    ax.set_ylabel("y")
    fig.colorbar(im, ax=ax, label="pressure", fraction=0.046, pad=0.03)
    fig.tight_layout()
    save_pair(fig, out_stem, outdir)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(
        description="Liska-Wendroff style: pressure colormap + density contours + velocity arrows.",
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--out-stem", required=True,
                        help="Output filename stem (no extension); pair written as <stem>.{pdf,png}.")
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--p-range", type=float, nargs=2, default=(None, None),
                        metavar=("PMIN", "PMAX"))
    parser.add_argument("--rho-levels", type=float, nargs=3, required=True,
                        metavar=("LO", "HI", "STEP"))
    parser.add_argument("--arrow-stride", type=int, default=20,
                        help="Stride for velocity quiver downsampling")
    parser.add_argument("--gamma", type=float, default=GAMMA_DEFAULT)
    args = parser.parse_args()

    header, arr = read_binary(args.input)
    render_lw_style(
        arr, header,
        gamma=args.gamma,
        out_stem=args.out_stem,
        outdir=str(args.outdir),
        p_vmin=args.p_range[0],
        p_vmax=args.p_range[1],
        rho_lo=args.rho_levels[0],
        rho_hi=args.rho_levels[1],
        rho_step=args.rho_levels[2],
        arrow_stride=args.arrow_stride,
    )
    print(f"wrote pair {args.outdir}/{args.out_stem}.{{pdf,png}}")


if __name__ == "__main__":
    main()
