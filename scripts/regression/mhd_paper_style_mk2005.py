#!/usr/bin/env python3
"""Render our Orszag-Tang results in the visual format of Miyoshi & Kusano 2005.

Reproduces the layout of two figures from
  T. Miyoshi & K. Kusano, J. Comput. Phys. 208 (2005) 315-344,
so our HLL / HLLD solvers can be compared side-by-side against the paper:

  Fig. 12  -> gray-scale temperature (T = p/rho) of the OT vortex, LEFT HALF of
              the domain, panels: HLL | HLLD | high-res reference.
  Fig. 13  -> 1D temperature cuts along two horizontal lines; the paper uses
              y = 0.64*pi and y = pi on a [0, 2*pi]^2 domain. Our run is in the
              Toth-2000 convention ([0,1]^2, t=0.5), so the same normalised
              positions are y = 0.32 and y = 0.50.

The reference is our 512^2 HLL run (same role the paper's high-res solution
plays). Units are rationalised (rho0=gamma^2, p0=gamma, B0=1), so the
comparison is of solver-to-solver structure, not absolute paper values.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from io_helper import read_binary  # noqa: E402

GAMMA = 5.0 / 3.0
# Conserved-variable indices for ideal MHD (see mhd_paper_figures.py).
RHO, MX, MY, MZ, BX, BY, BZ, E = range(8)

W13 = ROOT / "experiments" / "week13"
HLL_BIN = W13 / "solver_compare" / "ot_256_hll.bin"
HLLD_BIN = W13 / "solver_compare" / "ot_256_hlld.bin"
REF_BIN = W13 / "orszag_tang" / "ot_512_ref.bin"
OUT_DIR = W13 / "solver_compare" / "figures"

# Production single-result runs whose paper-style figures we overwrite in place.
OT_BIN = W13 / "orszag_tang" / "ot_256.bin"
OT_FIG_DIR = W13 / "orszag_tang" / "figures"
KH_BIN = W13 / "kelvin_helmholtz" / "kh_256.bin"
KH_FIG_DIR = W13 / "kelvin_helmholtz" / "figures"


def temperature(path: pathlib.Path) -> tuple[np.ndarray, float, float]:
    """Return (T[ny,nx], dx, dy) with T = p/rho for an ideal-MHD grid.bin."""
    h, arr = read_binary(path)
    a = arr.astype(np.float64)
    rho = a[..., RHO]
    vx = a[..., MX] / rho
    vy = a[..., MY] / rho
    vz = a[..., MZ] / rho
    Bx, By, Bz = a[..., BX], a[..., BY], a[..., BZ]
    kinetic = 0.5 * rho * (vx * vx + vy * vy + vz * vz)
    magnetic = 0.5 * (Bx * Bx + By * By + Bz * Bz)
    p = (GAMMA - 1.0) * (a[..., E] - kinetic - magnetic)
    return p / rho, h.dx, h.dy


def density(path: pathlib.Path) -> np.ndarray:
    """Return rho[ny, nx] from an ideal-MHD grid.bin."""
    _, arr = read_binary(path)
    return arr.astype(np.float64)[..., RHO]


def row_at(field: np.ndarray, y_frac: float) -> tuple[np.ndarray, np.ndarray]:
    """Nearest cell-centred row at y = y_frac (domain length 1); returns (x, T)."""
    ny, nx = field.shape
    j = int(round(y_frac * ny - 0.5))
    j = max(0, min(ny - 1, j))
    x = (np.arange(nx) + 0.5) / nx
    return x, field[j]


def fig12(t_hll, t_hlld, t_ref) -> pathlib.Path:
    """Gray-scale temperature, left half of domain: HLL | HLLD | reference."""
    panels = [
        ("HLL solver (256$^2$)", t_hll),
        ("HLLD solver (256$^2$)", t_hlld),
        ("reference (HLL 512$^2$)", t_ref),
    ]
    # Shared gray scale across panels for a fair visual comparison.
    vmin = min(float(t.min()) for _, t in panels)
    vmax = max(float(t.max()) for _, t in panels)

    fig, axes = plt.subplots(1, 3, figsize=(9.0, 6.2), constrained_layout=True)
    im = None
    for ax, (title, t) in zip(axes, panels):
        ny, nx = t.shape
        half = t[:, : nx // 2]  # left half of the domain, as in the paper
        im = ax.imshow(
            half,
            origin="lower",
            cmap="gray",
            vmin=vmin,
            vmax=vmax,
            extent=(0.0, 0.5, 0.0, 1.0),
            aspect="equal",
            interpolation="bilinear",
        )
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("x")
        ax.set_xticks([0.0, 0.25, 0.5])
    axes[0].set_ylabel("y")
    fig.colorbar(im, ax=axes, shrink=0.62, label="temperature  $T = p/\\rho$", pad=0.02)
    fig.suptitle(
        "Orszag-Tang temperature at $t=0.5$ (left half) "
        "— layout after Miyoshi & Kusano 2005, Fig. 12",
        fontsize=10.5,
    )
    out = OUT_DIR / "ot_temperature_mk_fig12.png"
    fig.savefig(out, dpi=170)
    plt.close(fig)
    return out


def fig13(t_hll, t_hlld, t_ref) -> pathlib.Path:
    """1D temperature cuts at y=0.32 (~0.64*pi) and y=0.50 (~pi)."""
    cuts = [(0.32, "y = 0.32  (paper $y = 0.64\\pi$)"),
            (0.50, "y = 0.50  (paper $y = \\pi$)")]
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4), constrained_layout=True)
    for ax, (yf, label) in zip(axes, cuts):
        xr, tr = row_at(t_ref, yf)
        ax.plot(xr, tr, "-", color="black", lw=1.1, label="reference (512$^2$)", zorder=1)
        xh, th = row_at(t_hll, yf)
        ax.plot(xh, th, "o", color="tab:blue", ms=2.6, mfc="none", mew=0.7,
                label="HLL solver", zorder=2)
        xd, td = row_at(t_hlld, yf)
        ax.plot(xd, td, "x", color="tab:red", ms=3.0, mew=0.7,
                label="HLLD solver", zorder=3)
        ax.set_title(label, fontsize=10)
        ax.set_xlabel("x")
        ax.set_xlim(0.0, 1.0)
        ax.grid(True, color="0.85", lw=0.5)
    axes[0].set_ylabel("temperature  $T = p/\\rho$")
    axes[0].legend(loc="best", fontsize=8, framealpha=0.9)
    fig.suptitle(
        "Orszag-Tang 1D temperature at $t=0.5$ "
        "— layout after Miyoshi & Kusano 2005, Fig. 13",
        fontsize=10.5,
    )
    out = OUT_DIR / "ot_temperature_mk_fig13.png"
    fig.savefig(out, dpi=170)
    plt.close(fig)
    return out


def ot_paper_style() -> pathlib.Path:
    """Overwrite ot_paper_style.png: gray-scale temperature, full domain.

    Two panels (256^2 production run | 512^2 reference) in the Toth-2000 /
    Miyoshi-Kusano-2005 gray-scale temperature layout, replacing the old
    colour density/mag-pressure heatmap.
    """
    t256, _, _ = temperature(OT_BIN)
    tref, _, _ = temperature(REF_BIN)
    vmin = min(float(t256.min()), float(tref.min()))
    vmax = max(float(t256.max()), float(tref.max()))

    fig, axes = plt.subplots(1, 2, figsize=(7.4, 4.2), constrained_layout=True)
    im = None
    for ax, (title, t) in zip(axes, (("HLL (256$^2$)", t256),
                                     ("reference (HLL 512$^2$)", tref))):
        im = ax.imshow(t, origin="lower", cmap="gray", vmin=vmin, vmax=vmax,
                       extent=(0.0, 1.0, 0.0, 1.0), aspect="equal",
                       interpolation="bilinear")
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("x")
    axes[0].set_ylabel("y")
    fig.colorbar(im, ax=axes, shrink=0.78, label="temperature  $T = p/\\rho$", pad=0.02)
    fig.suptitle("Orszag-Tang temperature at $t=0.5$ "
                 "— layout after Toth 2000 / Miyoshi & Kusano 2005", fontsize=10)
    out = OT_FIG_DIR / "ot_paper_style.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=170)
    plt.close(fig)
    return out


def kh_paper_style() -> pathlib.Path:
    """Overwrite kh_paper_style.png: density isolines, Dedner 2002 Fig. 8 style."""
    rho = density(KH_BIN)
    ny, nx = rho.shape
    xc = (np.arange(nx) + 0.5) / nx
    yc = (np.arange(ny) + 0.5) / ny
    levels = np.linspace(float(rho.min()), float(rho.max()), 24)

    fig, ax = plt.subplots(figsize=(5.2, 5.2), constrained_layout=True)
    ax.contour(xc, yc, rho, levels=levels, colors="black", linewidths=0.6)
    ax.set_aspect("equal")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Kelvin-Helmholtz: isolines of $\\rho$ at $t=1.0$\n"
                 "— layout after Dedner et al. 2002, Fig. 8", fontsize=9.5)
    out = KH_FIG_DIR / "kh_paper_style.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=170)
    plt.close(fig)
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t_hll, _, _ = temperature(HLL_BIN)
    t_hlld, _, _ = temperature(HLLD_BIN)
    t_ref, _, _ = temperature(REF_BIN)
    for name, t in (("HLL", t_hll), ("HLLD", t_hlld), ("ref", t_ref)):
        print(f"[mk2005] {name:5s} T: shape={t.shape} "
              f"min={t.min():.4g} max={t.max():.4g} mean={t.mean():.4g}")
    p12 = fig12(t_hll, t_hlld, t_ref)
    p13 = fig13(t_hll, t_hlld, t_ref)
    p_ot = ot_paper_style()
    p_kh = kh_paper_style()
    for p in (p12, p13, p_ot, p_kh):
        print(f"[mk2005] wrote {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
