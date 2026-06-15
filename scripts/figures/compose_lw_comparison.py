#!/usr/bin/env python3
# scripts/figures/compose_lw_comparison.py
#
# Side-by-side comparison: LW2003 WAFT panel (left, supplied as PNG)
# vs this work (right, rendered from grid.bin in matching style).
# Both panels are drawn without axis ticks/labels to match the LW figure.
# One shared colorbar (from this work's pressure field) sits on the right.

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from io_helper import IDX_E, IDX_RHO, IDX_RHOU, IDX_RHOV, read_binary  # noqa: E402
from _style import apply, save_pair  # noqa: E402

apply()
GAMMA_DEFAULT = 1.4


def primitives(arr, gamma):
    rho = arr[..., IDX_RHO]
    u = arr[..., IDX_RHOU] / rho
    v = arr[..., IDX_RHOV] / rho
    E = arr[..., IDX_E]
    p = (gamma - 1.0) * (E - 0.5 * rho * (u * u + v * v))
    return rho, u, v, p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lw-image", type=Path, required=True,
                    help="LW2003 WAFT panel screenshot (PNG)")
    ap.add_argument("--grid-bin", type=Path, required=True)
    ap.add_argument("--out-stem", required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--p-range", type=float, nargs=2, required=True,
                    metavar=("PMIN", "PMAX"))
    ap.add_argument("--rho-levels", type=float, nargs=3, required=True,
                    metavar=("LO", "HI", "STEP"))
    ap.add_argument("--arrow-stride", type=int, default=22)
    ap.add_argument("--gamma", type=float, default=GAMMA_DEFAULT)
    ap.add_argument("--left-title", default="Liska--Wendroff (2003) WAFT")
    ap.add_argument("--right-title", default="This work (MUSCL--Hancock + HLLC)")
    args = ap.parse_args()

    # --- left panel: pre-rendered LW WAFT crop -------------------------------
    lw_img = mpimg.imread(args.lw_image)

    # --- right panel: render from grid.bin in matching style -----------------
    header, arr = read_binary(args.grid_bin)
    rho, u, v, p = primitives(arr, args.gamma)
    ny, nx = rho.shape
    Lx = nx * header.dx
    Ly = ny * header.dy
    extent = [0, Lx, 0, Ly]

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 5.4))

    axL.imshow(lw_img, aspect="equal")
    axL.set_title(args.left_title, fontsize=11)
    axL.set_xticks([])
    axL.set_yticks([])
    for s in axL.spines.values():
        s.set_visible(False)

    im = axR.imshow(p, origin="lower", extent=extent, cmap="jet",
                    vmin=args.p_range[0], vmax=args.p_range[1], aspect="equal")
    levels = np.arange(args.rho_levels[0],
                       args.rho_levels[1] + 0.5 * args.rho_levels[2],
                       args.rho_levels[2])
    xs = (np.arange(nx) + 0.5) * header.dx
    ys = (np.arange(ny) + 0.5) * header.dy
    X, Y = np.meshgrid(xs, ys)
    axR.contour(X, Y, rho, levels=levels, colors="black", linewidths=0.4)
    s = max(1, args.arrow_stride)
    axR.quiver(X[::s, ::s], Y[::s, ::s], u[::s, ::s], v[::s, ::s],
               color="black", scale=None, width=0.0018, alpha=0.7)
    axR.set_title(args.right_title, fontsize=11)
    axR.set_xticks([])
    axR.set_yticks([])
    for sp in axR.spines.values():
        sp.set_visible(False)

    fig.subplots_adjust(left=0.02, right=0.90, top=0.94, bottom=0.04, wspace=0.05)
    cax = fig.add_axes([0.91, 0.08, 0.018, 0.82])
    fig.colorbar(im, cax=cax, label="pressure")

    save_pair(fig, args.out_stem, str(args.outdir))
    plt.close(fig)
    print(f"wrote pair {args.outdir}/{args.out_stem}.{{pdf,png}}")


if __name__ == "__main__":
    main()
