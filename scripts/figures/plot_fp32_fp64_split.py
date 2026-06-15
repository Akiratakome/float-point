#!/usr/bin/env python3
"""Two separate figures for Ch5 precision panel:

  fig_a (2x3, 1D)  : top row Sod/Toro3/Toro5 rho(fp32) - rho(fp64).
                     bottom row Sod/Toro3/Toro5 rho(fp64) - rho(exact Riemann).
  fig_b (1x2, 2D)  : LW3 and LW12 cellwise rho(fp32) - rho(fp64) heatmaps,
                     percentile-clipped colour range and fp64 density contours
                     overlaid in faint black so the wave structure is visible
                     alongside the precision signal.

Outputs:
  fp32_fp64_density_differences_1d_triplet.{pdf,png}
  fp32_fp64_density_differences_2d_pair.{pdf,png}
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
sys.path.insert(0, str(ROOT / "scripts" / "regression"))

from scripts.io_helper import read_binary  # noqa: E402
from _style import apply, save_pair  # noqa: E402
from verify_toro import TESTS, exact_riemann  # noqa: E402

apply()
OUT = ROOT / "report1" / "phd-thesis-template-2.4" / "Figs" / "report1"


def density(path: Path):
    h, arr = read_binary(path)
    return h, arr[..., 0].astype(np.float64)


def fig_1d_triplet() -> None:
    runs = ROOT / "experiments" / "report1_fp32_fp64_time_drift" / "runs"
    cases = [
        ("Sod", "sod", "sod-cpu-double", "sod-cpu-float"),
        ("Toro3", "toro3", "toro3-cpu-double", "toro3-cpu-float"),
        ("Toro5", "toro5", "toro5-cpu-double", "toro5-cpu-float"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(10.5, 6.0),
                             constrained_layout=True)

    for col, (title, key, dname, fname) in enumerate(cases):
        h_d, rho_d = density(runs / dname / "grid.bin")
        _, rho_f = density(runs / fname / "grid.bin")
        diff_prec = rho_f - rho_d
        x = np.linspace(0.0, 1.0, h_d.nx, endpoint=False) + 0.5 / h_d.nx

        ax_top = axes[0, col]
        ax_top.plot(x, diff_prec[0], lw=1.2, color="#1F4E79")
        ax_top.axhline(0.0, lw=0.5, color="0.4")
        ax_top.set_xlabel("x")
        ax_top.set_ylabel(r"$\rho_{\mathrm{fp32}}-\rho_{\mathrm{fp64}}$")
        ax_top.ticklabel_format(axis="y", style="sci", scilimits=(-2, 2))
        ax_top.set_title(title, fontsize=11)
        ax_top.grid(True, linewidth=0.35, alpha=0.4)

        cfg = TESTS[key]
        rho_ex, _u_ex, _p_ex, _ = exact_riemann(
            x, cfg["t_end"], cfg["gamma"], cfg["x0"],
            cfg["rhoL"], cfg["uL"], cfg["pL"],
            cfg["rhoR"], cfg["uR"], cfg["pR"],
        )
        disc_err = rho_d[0] - rho_ex

        ax_bot = axes[1, col]
        ax_bot.plot(x, disc_err, lw=1.2, color="#9B2226")
        ax_bot.axhline(0.0, lw=0.5, color="0.4")
        ax_bot.set_xlabel("x")
        ax_bot.set_ylabel(r"$\rho_{\mathrm{fp64}}-\rho_{\mathrm{exact}}$")
        ax_bot.ticklabel_format(axis="y", style="sci", scilimits=(-2, 2))
        ax_bot.grid(True, linewidth=0.35, alpha=0.4)

    save_pair(fig, "fp32_fp64_density_differences_1d_triplet", str(OUT))
    plt.close(fig)
    print("wrote 1d triplet (2x3)")


def fig_2d_pair() -> None:
    from scipy.ndimage import gaussian_filter
    midtime = ROOT / "experiments" / "week9" / "cpu_gpu_midtime_n400" / "runs"
    lw12_dir = ROOT / "experiments" / "week8" / "report1_2d_config12_fill" / "runs"

    cases = [
        ("LW3 ($N=400$, $t=0.3$)",
         midtime / "lw3-n400-t4-cpu-double-strict-hllc" / "grid.bin",
         midtime / "lw3-n400-t4-cpu-float-strict-hllc" / "grid.bin"),
        ("LW12 ($N=400$, $t=0.25$)",
         lw12_dir / "lw12-n400-cpu-double-strict-hllc" / "grid.bin",
         lw12_dir / "lw12-n400-cpu-float-strict-hllc" / "grid.bin"),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2),
                             constrained_layout=True)
    for ax, (title, p64, p32) in zip(axes, cases):
        h, rho_d = density(p64)
        _, rho_f = density(p32)
        diff = rho_f - rho_d
        # Light 2-pixel Gaussian smoothing on |diff| to suppress pixel-level
        # round-off speckle while preserving wave-aligned structure.
        mag = gaussian_filter(np.abs(diff), sigma=1.5)
        vmax = float(np.nanpercentile(mag, 99.0))
        if vmax <= 0:
            vmax = float(np.nanmax(mag)) or 1e-12

        im = ax.imshow(
            mag, origin="lower", cmap="rocket_r" if "rocket_r" in
            plt.colormaps() else "magma_r",
            vmin=0.0, vmax=vmax,
            interpolation="nearest",
            extent=[0, h.nx * h.dx, 0, h.ny * h.dy], aspect="equal",
        )
        # density contours from fp64 reference, dark thin lines for context
        xs = (np.arange(h.nx) + 0.5) * h.dx
        ys = (np.arange(h.ny) + 0.5) * h.dy
        X, Y = np.meshgrid(xs, ys)
        rho_min, rho_max = float(np.nanmin(rho_d)), float(np.nanmax(rho_d))
        if rho_max > rho_min:
            levels = np.linspace(rho_min, rho_max, 12)
            ax.contour(X, Y, rho_d, levels=levels,
                       colors="#cfd8dc", linewidths=0.45, alpha=0.85)
        cbar = fig.colorbar(im, ax=ax, shrink=0.92, pad=0.025,
                            label=r"$|\rho_{\mathrm{fp32}}-\rho_{\mathrm{fp64}}|$ (smoothed)")
        cbar.ax.tick_params(labelsize=9)
        cbar.formatter.set_powerlimits((-3, 3))
        cbar.update_ticks()
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title(title, fontsize=11)

    save_pair(fig, "fp32_fp64_density_differences_2d_pair", str(OUT))
    plt.close(fig)
    print("wrote 2d pair (magnitude, gaussian smoothed, single-hue)")


if __name__ == "__main__":
    fig_1d_triplet()
    fig_2d_pair()
