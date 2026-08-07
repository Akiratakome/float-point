#!/usr/bin/env python3
"""Where the fp32-fp64 discrepancy lives: localisation of the L-infinity response.

Report 2 twice explains a large L-infinity against a small domain mean by saying
that shocks, current sheets and shear layers occupy few cells. That is an
inference from the ratio of two norms, not a measurement. This driver maps the
cellwise |rho32 - rho64| field, marks the cell attaining L-infinity, and reports
the concentration curve: the share of the total absolute difference carried by
the largest-difference fraction of cells.

Matched pairs only: same case, grid, solver, CFL and stopping time, differing in
the build precision alone.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments" / "week21" / "precision_localisation"
EXPERIMENT = "week21-precision-localisation"

for path in (ROOT, ROOT / "scripts", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(path))

from io_helper import read_binary  # noqa: E402
from _mhd_harness import (  # noqa: E402
    git_commit,
    replace_or_append_cfg,
    resolve_binary,
    run_case,
    sha256_file,
)

CFG = ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg"
BINS = {
    "double": ROOT / "build-matrix" / "cpu-double-O2-ieee-leq" / "hrsc_mhd",
    "float": ROOT / "build-matrix" / "cpu-float-O2-ieee-leq" / "hrsc_mhd",
}
GRID = 256
SOLVERS = ("hll", "hlld")
CFL = {"hll": 0.4, "hlld": 0.2}
SHARE_FRACTIONS = (0.001, 0.005, 0.01, 0.05, 0.10)


def run(solver: str, precision: str, commit: str) -> np.ndarray:
    name = f"orszag_tang-{solver}-{precision}-n{GRID}"
    run_dir = OUT / "runs" / name
    run_dir.mkdir(parents=True, exist_ok=True)
    out_bin = run_dir / "grid.bin"
    binary = resolve_binary(BINS[precision])
    text = CFG.read_text(encoding="utf-8")
    for key, value in (("nx", GRID), ("ny", GRID), ("riemann", solver),
                       ("cfl", CFL[solver]), ("device", "cpu"),
                       ("output_format", "binary"),
                       ("output_file", str(out_bin).replace("\\", "/"))):
        text = replace_or_append_cfg(text, key, str(value))
    run_case(name, text, run_dir, binary, CFG, commit, sha256_file(binary),
             output_bin=out_bin, experiment=EXPERIMENT)
    _header, data = read_binary(out_bin)
    return np.asarray(data, dtype=np.float64)


def concentration(diff: np.ndarray) -> dict[str, float]:
    flat = np.sort(diff.ravel())[::-1]
    total = float(flat.sum())
    out = {}
    if total <= 0.0:
        return {f"share_top_{f:g}": float("nan") for f in SHARE_FRACTIONS}
    csum = np.cumsum(flat)
    for frac in SHARE_FRACTIONS:
        k = max(1, int(round(frac * flat.size)))
        out[f"share_top_{frac:g}"] = float(csum[k - 1] / total)
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    commit = git_commit()
    rows = []
    fields = {}
    for solver in SOLVERS:
        f64 = run(solver, "double", commit)
        f32 = run(solver, "float", commit)
        rho64, rho32 = f64[..., 0], f32[..., 0]
        diff = np.abs(rho32 - rho64)
        j, i = np.unravel_index(int(np.argmax(diff)), diff.shape)
        row = {
            "case": "orszag_tang_2d", "solver": solver, "grid": GRID,
            "cfl": CFL[solver],
            "linf": float(diff.max()),
            "l1_mean": float(diff.mean()),
            "linf_over_mean": float(diff.max() / diff.mean()),
            "argmax_ij": [int(i), int(j)],
            "argmax_xy": [float((i + 0.5) / GRID), float((j + 0.5) / GRID)],
            "rho64_at_argmax": float(rho64[j, i]),
        }
        row.update(concentration(diff))
        rows.append(row)
        fields[solver] = (rho64, diff, (i, j))
        print(f"{solver}: Linf={row['linf']:.4e} mean={row['l1_mean']:.4e} "
              f"ratio={row['linf_over_mean']:.1f} argmax=({i},{j}) "
              f"top1%share={row['share_top_0.01']:.3f}")

    figures = plot(fields, rows)
    payload = {
        "schema": {"name": "hrsc.week21-precision-localisation", "version": 1},
        "experiment": EXPERIMENT, "git_commit": commit,
        "grid": GRID, "rows": rows, "figures": figures,
        "claim_boundary": [
            "Density only, one grid, one case, matched CPU pairs.",
            "Concentration shares describe where the difference sits, not its cause.",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for path in (OUT / "runs").rglob("grid.bin"):
        path.unlink()
    print(f"\nwrote {OUT / 'summary.json'}")
    return 0


def plot(fields, rows) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.5), constrained_layout=True)
    solver = "hlld"
    rho64, diff, (i, j) = fields[solver]
    extent = (0.0, 1.0, 0.0, 1.0)

    ax = axes[0]
    ax.imshow(rho64, origin="lower", extent=extent, cmap="gray")
    ax.plot((i + 0.5) / GRID, (j + 0.5) / GRID, "o", markersize=9,
            markerfacecolor="none", markeredgecolor="#D55E00", markeredgewidth=1.6)
    ax.set_title("(a) fp64 density, HLLD $256^2$", loc="left", fontsize=9)
    ax.set_xlabel("x"); ax.set_ylabel("y")

    ax = axes[1]
    floor = max(diff[diff > 0].min(), diff.max() * 1e-6) if (diff > 0).any() else 1e-30
    im = ax.imshow(np.maximum(diff, floor), origin="lower", extent=extent,
                   cmap="magma", norm=LogNorm(vmin=floor, vmax=diff.max()))
    ax.plot((i + 0.5) / GRID, (j + 0.5) / GRID, "o", markersize=9,
            markerfacecolor="none", markeredgecolor="#00A0FF", markeredgewidth=1.6)
    ax.set_title(r"(b) $|\rho_{32}-\rho_{64}|$", loc="left", fontsize=9)
    ax.set_xlabel("x")
    fig.colorbar(im, ax=ax, fraction=0.046)

    ax = axes[2]
    for row, colour in zip(rows, ("#0072B2", "#D55E00")):
        d = fields[row["solver"]][1]
        flat = np.sort(d.ravel())[::-1]
        csum = np.cumsum(flat) / flat.sum()
        frac = np.arange(1, flat.size + 1) / flat.size
        ax.semilogx(frac, csum, color=colour, linewidth=1.4,
                    label=f"{row['solver'].upper()} (top 1%: {row['share_top_0.01']*100:.0f}%)")
    ax.set_xlabel("Fraction of cells, largest difference first")
    ax.set_ylabel("Share of total $|\\Delta\\rho|$")
    ax.set_title("(c) concentration", loc="left", fontsize=9)
    ax.grid(True, which="both", color="#D9DEE5", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_ylim(0, 1.02)
    ax.legend(fontsize=8, loc="upper left")

    (OUT / "figures").mkdir(parents=True, exist_ok=True)
    paths = []
    for suffix in ("png", "pdf"):
        p = OUT / "figures" / f"precision_localisation.{suffix}"
        fig.savefig(p, dpi=320)
        paths.append(str(p.relative_to(ROOT)))
    plt.close(fig)
    return paths


if __name__ == "__main__":
    raise SystemExit(main())
