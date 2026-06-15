#!/usr/bin/env python3
"""Five-case cellwise fp32-fp64 density-difference figure.

Replaces the previous Fig 5.7 (Sod/Toro3/Toro5/LW3) and Fig 5.8 (LW12) by
one combined figure: 1D lineouts on top (Sod, Toro3, Toro5) and 2D heatmaps
on the bottom (LW3, LW12). Fonts and style follow scripts/figures/_style.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from scripts.io_helper import read_binary  # noqa: E402
from _style import apply, save_pair  # noqa: E402

apply()

OUT = ROOT / "report1" / "phd-thesis-template-2.4" / "Figs" / "report1"


def density(path: Path) -> tuple[object, np.ndarray]:
    header, arr = read_binary(path)
    return header, arr[..., 0].astype(np.float64)


def main() -> None:
    runs_1d = ROOT / "experiments" / "report1_fp32_fp64_time_drift" / "runs"
    cases_1d = [
        ("Sod", "sod-cpu-double", "sod-cpu-float"),
        ("Toro3", "toro3-cpu-double", "toro3-cpu-float"),
        ("Toro5", "toro5-cpu-double", "toro5-cpu-float"),
    ]
    lw3_dir = runs_1d
    lw12_base = ROOT / "experiments" / "week8" / "report1_2d_config12_fill" / "runs"

    cases_2d = [
        ("LW3", lw3_dir / "lw3-n200-cpu-double" / "grid.bin",
         lw3_dir / "lw3-n200-cpu-float" / "grid.bin"),
        ("LW12", lw12_base / "lw12-n400-cpu-double-strict-hllc" / "grid.bin",
         lw12_base / "lw12-n400-cpu-float-strict-hllc" / "grid.bin"),
    ]

    fig = plt.figure(figsize=(9.5, 6.4))
    gs = fig.add_gridspec(
        nrows=2, ncols=6,
        height_ratios=[1.0, 1.45],
        hspace=0.42, wspace=0.55,
        left=0.07, right=0.97, top=0.95, bottom=0.08,
    )
    axes_top = [fig.add_subplot(gs[0, i:i + 2]) for i in (0, 2, 4)]
    ax_lw3 = fig.add_subplot(gs[1, 0:3])
    ax_lw12 = fig.add_subplot(gs[1, 3:6])

    for ax, (title, dname, fname) in zip(axes_top, cases_1d):
        h_d, rho_d = density(runs_1d / dname / "grid.bin")
        _, rho_f = density(runs_1d / fname / "grid.bin")
        diff = rho_f - rho_d
        x = np.linspace(0.0, 1.0, h_d.nx, endpoint=False) + 0.5 / h_d.nx
        ax.plot(x, diff[0], lw=1.1, color="#1F4E79")
        ax.axhline(0.0, lw=0.5, color="0.4")
        ax.set_xlabel("x")
        ax.set_ylabel(r"$\rho_{\mathrm{fp32}}-\rho_{\mathrm{fp64}}$")
        ax.ticklabel_format(axis="y", style="sci", scilimits=(-2, 2))
        ax.set_title(title, fontsize=10)

    for ax, (title, p64, p32) in zip([ax_lw3, ax_lw12], cases_2d):
        h, rho_d = density(p64)
        _, rho_f = density(p32)
        diff = rho_f - rho_d
        vmax = float(np.nanmax(np.abs(diff)))
        im = ax.imshow(
            diff, origin="lower", cmap="RdBu_r",
            vmin=-vmax, vmax=vmax, interpolation="nearest",
            extent=[0, h.nx * h.dx, 0, h.ny * h.dy], aspect="equal",
        )
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.025,
                            label=r"$\rho_{\mathrm{fp32}}-\rho_{\mathrm{fp64}}$")
        cbar.ax.tick_params(labelsize=8)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title(title, fontsize=10)

    save_pair(fig, "fp32_fp64_density_differences_all5", str(OUT))
    plt.close(fig)
    print(f"wrote {OUT}/fp32_fp64_density_differences_all5.{{pdf,png}}")


if __name__ == "__main__":
    main()
