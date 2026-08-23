#!/usr/bin/env python3
"""Report-2 temporal saturation figure.

Combines the week-15 Brio--Wu and Orszag--Tang temporal series with the
Report-2 additions -- an early-time Orszag--Tang window, and a Kelvin--Helmholtz
series carried from t=0.01 to t=3.0, past the roll-up -- on the common
binary32-unit-roundoff scale.

The domain mean is normalised by the conserved reference density mean of each
case, which is the same normalisation the chapter-5 u32 axis uses:
Brio--Wu 0.5625, Orszag--Tang 25/9, Kelvin--Helmholtz 1.
"""
from __future__ import annotations

import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "figures"))
from _style import apply, PALETTE  # noqa: E402

U32 = 2.0 ** -24
EXP = ROOT / "experiments" / "week15"
TARGET = (ROOT / "dissertation" / "phd-thesis-template-2.4" / "Figs" / "report2"
          / "ch5_temporal_saturation.pdf")

# Conserved density domain mean of each initial condition.
REF_MEAN = {
    "brio_wu_1d": 0.5625,
    "orszag_tang_2d": 25.0 / 9.0,
    "kelvin_helmholtz_2d": 1.0,
}


def series(directory: str, case: str) -> tuple[np.ndarray, np.ndarray]:
    payload = json.loads((EXP / directory / "summary.json").read_text(encoding="utf-8"))
    for record in payload["records"]:
        if record["case"].startswith(case):
            t = np.asarray(record["times"], dtype=float)
            l1 = np.asarray(record["l1"], dtype=float) / REF_MEAN[case] / U32
            return t, l1
    raise KeyError(f"{case} not in {directory}")


def merge(*parts: tuple[np.ndarray, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    t = np.concatenate([p[0] for p in parts])
    y = np.concatenate([p[1] for p in parts])
    order = np.argsort(t)
    return t[order], y[order]


def power_law(t: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    mask = (t > 0) & (y > 0)
    logt, logy = np.log(t[mask]), np.log(y[mask])
    design = np.vstack([np.ones_like(logt), logt]).T
    coeff, *_ = np.linalg.lstsq(design, logy, rcond=None)
    residual = logy - design @ coeff
    r2 = 1.0 - np.sum(residual ** 2) / np.sum((logy - logy.mean()) ** 2)
    return float(coeff[1]), float(r2)


def main() -> int:
    apply()
    brio = series("mhd_temporal_divergence", "brio_wu_1d")
    ot = merge(series("mhd_temporal_divergence_orszag_tang_2d_early", "orszag_tang_2d"),
               series("mhd_temporal_divergence", "orszag_tang_2d"))
    kh = merge(series("mhd_temporal_divergence_kelvin_helmholtz_2d_early",
                      "kelvin_helmholtz_2d"),
               series("mhd_temporal_divergence_kelvin_helmholtz_2d",
                      "kelvin_helmholtz_2d"))

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(9.4, 4.0), constrained_layout=True)

    # (a) Kelvin--Helmholtz across the roll-up, growth phase against plateau.
    t, y = kh
    grow = t <= 0.2
    plateau = t >= 1.0
    k_grow, r2_grow = power_law(t[grow], y[grow])
    k_plateau, r2_plateau = power_law(t[plateau], y[plateau])
    ax_a.plot(t, y, "o-", color=PALETTE["fp32"], label="KH $128^2$, HLL")
    fit_t = np.linspace(t[grow].min(), t[grow].max(), 50)
    scale = y[grow][0] / t[grow][0] ** k_grow
    ax_a.plot(fit_t, scale * fit_t ** k_grow, ":", color=PALETTE["gray"],
              label=f"growth fit $k={k_grow:.2f}$")
    ax_a.axhspan(y[plateau].min(), y[plateau].max(), color=PALETTE["gpu"], alpha=0.15)
    ax_a.text(0.085, y[plateau].max() * 0.955,
              f"plateau, $k={k_plateau:.2f}$ ($R^2={r2_plateau:.2f}$)",
              fontsize=8, color=PALETTE["gray"], va="top")
    ax_a.axvline(1.0, color=PALETTE["gray"], lw=0.7, ls="--")
    ax_a.text(1.08, 1.02, "roll-up", fontsize=8.5, color=PALETTE["gray"])
    ax_a.set_xscale("log")
    ax_a.set_yscale("log")
    ax_a.set_xlabel("Simulation time $t$")
    ax_a.set_ylabel(r"Density mean $L_1$ discrepancy $/\,u_{32}$")
    ax_a.set_title("(a) Kelvin–Helmholtz through roll-up", loc="left")
    ax_a.grid(True, which="both")
    ax_a.legend(loc="lower right")

    # (b) All three cases approach one saturation level.
    for (t, y), label, colour in (
        (brio, "Brio–Wu $N=800$", PALETTE["fp64"]),
        (ot, "Orszag–Tang $128^2$", PALETTE["gpu"]),
        (kh, "Kelvin–Helmholtz $128^2$", PALETTE["fp32"]),
    ):
        ax_b.plot(t, y, "o-", color=colour, label=label, markersize=3)
    ax_b.axhspan(2.0, 3.0, color=PALETTE["gray"], alpha=0.16)
    ax_b.text(0.0058, 2.38, "saturation band, 2–3 roundings",
              fontsize=8.5, color=PALETTE["gray"])
    ax_b.set_xscale("log")
    ax_b.set_yscale("log")
    ax_b.set_xlabel("Simulation time $t$")
    ax_b.set_ylabel(r"Density mean $L_1$ discrepancy $/\,u_{32}$")
    ax_b.set_title("(b) Common saturation level across cases", loc="left")
    ax_b.grid(True, which="both")
    ax_b.legend(loc="lower right")

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(TARGET)
    fig.savefig(TARGET.with_suffix(".png"), dpi=160)
    plt.close(fig)

    print(f"wrote {TARGET.relative_to(ROOT)}")
    print(f"KH growth   t<=0.2 : k={k_grow:.4f} R2={r2_grow:.4f}")
    print(f"KH plateau  t>=1.0 : k={k_plateau:.4f} R2={r2_plateau:.4f}")
    for (t, y), name in ((brio, "brio_wu"), (ot, "orszag_tang"), (kh, "kelvin_helmholtz")):
        k, r2 = power_law(t, y)
        print(f"{name:16s} n={len(t):3d} t={t[0]:.4g}..{t[-1]:.4g} "
              f"u32={y[0]:.3f}..{y[-1]:.3f} full k={k:.4f} R2={r2:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
