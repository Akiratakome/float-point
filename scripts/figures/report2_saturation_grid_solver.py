#!/usr/bin/env python3
"""Report-2 figure: does the temporal saturation survive grid and solver?

Report 2 measures the long-horizon fp32--fp64 discrepancy only at 128^2 with the
globally clamped HLL flux, the most dissipative configuration in the matrix, and
separately shows the same domain-mean level rising steeply under refinement.
This figure puts the two on one axis by repeating the identical Kelvin--Helmholtz
series over three one-factor comparisons:

    grid    at HLL,  CFL 0.4 : 128^2 -> 256^2
    solver  at 128^2, CFL 0.2: HLL   -> HLLD
    grid    at HLLD, CFL 0.2 : 128^2 -> 256^2
    CFL     at 128^2, HLL    : 0.4   -> 0.2   (control)

Normalisation follows scripts/figures/report2_temporal_saturation.py: the domain
mean is divided by the conserved reference density mean, which is 1 for
Kelvin--Helmholtz, and then by the binary32 unit roundoff.
"""
from __future__ import annotations

import glob
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
KH_REF_MEAN = 1.0
W22 = ROOT / "experiments" / "week22"
W15 = ROOT / "experiments" / "week15"
TARGET = (ROOT / "dissertation" / "phd-thesis-template-2.4" / "Figs" / "report2"
          / "ch5_saturation_grid_solver.pdf")
FIT_WINDOW = (0.2, 3.0)

# label, colour, linestyle, marker
SERIES = [
    ("baseline", "KH $128^2$, HLL, CFL 0.4", PALETTE["fp32"], "-", "o", 128),
    ("kh_n256_hll_cfl04", "KH $256^2$, HLL, CFL 0.4", PALETTE["accent"], "-", "s", 256),
    ("kh_n128_hll_cfl02", "KH $128^2$, HLL, CFL 0.2", PALETTE["gray"], "--", "^", 128),
    ("kh_n128_hlld_cfl02", "KH $128^2$, HLLD, CFL 0.2", PALETTE["gpu"], "-", "D", 128),
    ("kh_n256_hlld_cfl02", "KH $256^2$, HLLD, CFL 0.2", PALETTE["fp64"], "-", "v", 256),
]
B0_KH = 0.1  # uniform flow-aligned field strength of the Kelvin--Helmholtz data


def load_divb(case: str, n: int) -> tuple[np.ndarray, np.ndarray] | None:
    """Cell-width- and B0-scaled max |div B| of the fp64 member of each series."""
    if case == "baseline":
        root = W15 / "mhd_temporal_divergence_kelvin_helmholtz_2d" / "runs"
    else:
        root = W22 / f"mhd_saturation_grid_solver_{case}" / "runs"
    rows = []
    for f in glob.glob(str(root / "*" / "double" / "slice_*" / "metadata.json")):
        diag = json.loads(pathlib.Path(f).read_text(encoding="utf-8")).get(
            "stderr_diagnostics"
        )
        if isinstance(diag, dict) and "t" in diag and "divB_max" in diag:
            rows.append((float(diag["t"]), float(diag["divB_max"]) / n / B0_KH))
    if not rows:
        return None
    rows.sort()
    return np.asarray([r[0] for r in rows]), np.asarray([r[1] for r in rows])


def load(case: str) -> tuple[np.ndarray, np.ndarray] | None:
    if case == "baseline":
        path = W15 / "mhd_temporal_divergence_kelvin_helmholtz_2d" / "summary.json"
        want = "kelvin_helmholtz_2d"
    else:
        path = W22 / f"mhd_saturation_grid_solver_{case}" / "summary.json"
        want = case
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    for record in payload.get("records", []):
        if record["case"] == want:
            t = np.asarray(record["times"], dtype=float)
            y = np.asarray(record["l1"], dtype=float) / KH_REF_MEAN / U32
            return t, y
    return None


def power_law(t: np.ndarray, y: np.ndarray) -> dict[str, float]:
    mask = (t > 0) & (y > 0) & (t >= FIT_WINDOW[0]) & (t <= FIT_WINDOW[1])
    logt, logy = np.log(t[mask]), np.log(y[mask])
    design = np.vstack([np.ones_like(logt), logt]).T
    coeff, *_ = np.linalg.lstsq(design, logy, rcond=None)
    residual = logy - design @ coeff
    ss_tot = float(np.sum((logy - logy.mean()) ** 2))
    r2 = 1.0 - float(np.sum(residual ** 2)) / ss_tot if ss_tot > 0 else float("nan")
    # OLS standard error of the slope, so the exponent carries an uncertainty.
    dof = max(len(logt) - 2, 1)
    s2 = float(np.sum(residual ** 2)) / dof
    sxx = float(np.sum((logt - logt.mean()) ** 2))
    return {
        "k": float(coeff[1]),
        "k_se": float(np.sqrt(s2 / sxx)) if sxx > 0 else float("nan"),
        "r2": r2,
        "rmse_log": float(np.sqrt(np.mean(residual ** 2))),
        "n": int(mask.sum()),
    }


def main() -> int:
    apply()
    data: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    divb: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    stats: dict[str, dict[str, float]] = {}
    for case, _lbl, _col, _ls, _mk, ncell in SERIES:
        loaded = load(case)
        if loaded is None:
            print(f"[skip] {case}: summary not found")
            continue
        data[case] = loaded
        db = load_divb(case, ncell)
        if db is not None:
            divb[case] = db
        t, y = loaded
        fit = power_law(t, y)
        fit.update({
            "u32_first": float(y[0]),
            "u32_last": float(y[-1]),
            "endpoint_ratio": float(y[-1] / y[0]),
            "t_first": float(t[0]),
            "t_last": float(t[-1]),
        })
        stats[case] = fit

    if not data:
        print("no series available")
        return 1

    fig, (ax_a, ax_b, ax_c) = plt.subplots(
        1, 3, figsize=(13.2, 4.0), constrained_layout=True,
        gridspec_kw={"width_ratios": [1.25, 1.05, 0.95]},
    )

    ax_a.axhspan(2.0, 3.0, color=PALETTE["gray"], alpha=0.14)
    ax_a.axvline(1.0, color=PALETTE["gray"], lw=0.7, ls=":")
    for case, label, colour, ls, marker, _n in SERIES:
        if case not in data:
            continue
        t, y = data[case]
        ax_a.plot(t, y, ls, marker=marker, color=colour, label=label,
                  markersize=3.4, markerfacecolor="none")
    ax_a.set_xscale("log")
    ax_a.set_yscale("log")
    ax_a.set_xlim(0.18, 3.4)
    ax_a.set_xticks([0.2, 0.3, 0.5, 1.0, 2.0, 3.0])
    ax_a.set_xticklabels(["0.2", "0.3", "0.5", "1.0", "2.0", "3.0"])
    ax_a.set_yticks([2, 3, 5, 10, 20, 40])
    ax_a.set_yticklabels(["2", "3", "5", "10", "20", "40"])
    ax_a.minorticks_off()
    ax_a.text(0.19, 2.06, "reported saturation band, 2–3 roundings",
              fontsize=7.6, color=PALETTE["gray"], va="bottom")
    ax_a.text(1.05, 1.62, "roll-up", fontsize=7.6, color=PALETTE["gray"])
    ax_a.set_xlabel("Simulation time $t$")
    ax_a.set_ylabel(r"Density mean $L_1$ discrepancy $/\,u_{32}$")
    ax_a.set_title("(a) Long-horizon discrepancy by grid and solver", loc="left")
    ax_a.grid(True, which="major")
    ax_a.legend(loc="upper left", fontsize=7.8)

    order = [c for c, *_ in SERIES if c in stats]
    labels = [lbl for c, lbl, *_ in SERIES if c in stats]
    colours = [col for c, _lbl, col, *_ in SERIES if c in stats]
    ks = [stats[c]["k"] for c in order]
    ses = [stats[c]["k_se"] for c in order]
    pos = np.arange(len(order))[::-1]
    xmax = max(k + s for k, s in zip(ks, ses)) * 1.42
    ax_b.barh(pos, ks, xerr=ses, color=colours, alpha=0.85, height=0.58,
              error_kw={"ecolor": "#333333", "elinewidth": 0.9, "capsize": 2.5})
    ax_b.axvline(0.0, color=PALETTE["gray"], lw=0.9, ls="--")
    for p, case, k, se in zip(pos, order, ks, ses):
        ax_b.text(k + se + xmax * 0.025, p,
                  f"$\\times{stats[case]['endpoint_ratio']:.2f}$",
                  fontsize=8, va="center", color="#333333")
    ax_b.set_yticks(pos)
    ax_b.set_yticklabels(labels, fontsize=8)
    ax_b.set_ylim(pos.min() - 0.55, pos.max() + 0.55)
    ax_b.set_xlabel(r"Power-law exponent $k$ over $t\in[0.2,3.0]$")
    ax_b.set_xlim(0.0, xmax)
    ax_b.set_title(
        "(b) Fitted exponent, with endpoint ratio $e(3.0)/e(0.2)$", loc="left"
    )
    ax_b.grid(True, axis="x")

    # (c) The competing explanation: discrete divergence control over the same
    # window.  Read alongside (a), not as an independent result.
    ax_c.axvline(1.0, color=PALETTE["gray"], lw=0.7, ls=":")
    for case, label, colour, ls, marker, _n in SERIES:
        if case not in divb:
            continue
        t, y = divb[case]
        ax_c.plot(t, y, ls, marker=marker, color=colour, markersize=3.2,
                  markerfacecolor="none", label=label)
    ax_c.set_xscale("log")
    ax_c.set_yscale("log")
    ax_c.set_xlim(0.18, 3.4)
    ax_c.set_xticks([0.2, 0.3, 0.5, 1.0, 2.0, 3.0])
    ax_c.set_xticklabels(["0.2", "0.3", "0.5", "1.0", "2.0", "3.0"])
    ax_c.minorticks_off()
    ax_c.set_xlabel("Simulation time $t$")
    ax_c.set_ylabel(r"$\max|\nabla\!\cdot\!\mathbf{B}|\,\Delta x / B_0$ (fp64)")
    ax_c.set_title("(c) Discrete divergence over the same window", loc="left")
    ax_c.grid(True, which="major")

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(TARGET)
    fig.savefig(TARGET.with_suffix(".png"), dpi=160)
    plt.close(fig)
    print(f"wrote {TARGET.relative_to(ROOT)}")

    print(f"{'series':28s} {'n':>3s} {'u32@0.2':>9s} {'u32@3.0':>9s} "
          f"{'ratio':>7s} {'k':>8s} {'k_se':>7s} {'R2':>7s} {'rmse':>7s}")
    for case in order:
        s = stats[case]
        print(f"{case:28s} {s['n']:3d} {s['u32_first']:9.3f} {s['u32_last']:9.3f} "
              f"{s['endpoint_ratio']:7.3f} {s['k']:8.4f} {s['k_se']:7.4f} "
              f"{s['r2']:7.4f} {s['rmse_log']:7.4f}")

    (W22 / "saturation_grid_solver_stats.json").parent.mkdir(parents=True, exist_ok=True)
    (W22 / "saturation_grid_solver_stats.json").write_text(
        json.dumps({"fit_window": list(FIT_WINDOW), "stats": stats}, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
