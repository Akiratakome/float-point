#!/usr/bin/env python3
"""Kelvin--Helmholtz density morphology figure for Report 2, Chapter 4.

Renders the same field and contour convention as
scripts/regression/mhd_paper_style_mk2005.py:kh_paper_style, but without the
in-figure title, which the LaTeX caption already carries. Source data are the
retained week-13 HLL fp64 run at 256^2, CFL 0.4, t=1.0.
"""
from __future__ import annotations

import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from io_helper import read_binary  # noqa: E402

SOURCE = ROOT / "experiments" / "week13" / "kelvin_helmholtz" / "kh_256.bin"
TARGET_DIR = (
    ROOT / "dissertation" / "phd-thesis-template-2.4" / "Figs" / "report2"
)
STEM = "ch4_kelvin_helmholtz_morphology"
LEVELS = 24


def main() -> int:
    _, arr = read_binary(SOURCE)
    rho = np.asarray(arr[..., 0], dtype=np.float64)
    ny, nx = rho.shape
    xc = (np.arange(nx) + 0.5) / nx
    yc = (np.arange(ny) + 0.5) / ny
    levels = np.linspace(rho.min(), rho.max(), LEVELS)

    fig, ax = plt.subplots(figsize=(5.4, 4.6), constrained_layout=True)
    # The line contours alone carry no density scale, so the same 24 levels are
    # also shaded and a colour bar states what the contour spacing is worth.
    mesh = ax.pcolormesh(xc, yc, rho, cmap="gray", shading="nearest",
                         vmin=levels[0], vmax=levels[-1], rasterized=True)
    ax.contour(xc, yc, rho, levels=levels, colors="black", linewidths=0.5)
    ax.set_aspect("equal")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_xlabel("$x$")
    ax.set_ylabel("$y$")
    bar = fig.colorbar(mesh, ax=ax, fraction=0.046, pad=0.03)
    bar.set_label(r"density $\rho$")
    bar.add_lines(levels, ["black"] * LEVELS, 0.4)

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    for suffix in (".pdf", ".png"):
        target = TARGET_DIR / f"{STEM}{suffix}"
        fig.savefig(target, dpi=320)
        print("wrote", target.relative_to(ROOT))
    plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
