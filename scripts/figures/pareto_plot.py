"""Pareto frontier figure: σ_FP_L1 vs s_worst_q05 with s_req(N) target band.

x-axis: log10(σ_FP_L1)  — FP noise (smaller = quieter)
y-axis: s_worst_q05     — worst-5%-cell trustworthy digits (larger = better)
Each (solver, precision) is one labeled point; the s_req(N) horizontal
dashed line shows the truncation-anchored target a "well-matched" cell
should be at-or-above.

Reads the same three CSVs as tradeoff_summary_table; reports headline
values for the ρ variable.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_HEADLINE_VAR = "rho"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _pick(rows: list[dict], **filters) -> dict:
    for r in rows:
        if all(r.get(k) == v for k, v in filters.items()):
            return r
    raise KeyError(f"no row matches {filters}")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Pareto plot for LW Config 3 at N=200.")
    p.add_argument("--snr-csv", required=True, type=Path)
    p.add_argument("--losos-csv", required=True, type=Path)
    p.add_argument("--s-req-csv", required=True, type=Path)
    p.add_argument("--N", type=int, default=200)
    p.add_argument("--out", required=True, type=Path)
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    snr = _read_csv(args.snr_csv)
    losos = _read_csv(args.losos_csv)
    s_req_rows = _read_csv(args.s_req_csv)

    points = []
    for solver in ("hllc", "rusanov"):
        snr_row = _pick(snr, solver=solver, precision="p53", variable=_HEADLINE_VAR)
        losos_row = _pick(losos, solver=solver, precision="p53", variable=_HEADLINE_VAR)
        s_req_row = _pick(s_req_rows, solver=solver, variable=_HEADLINE_VAR)
        points.append({
            "label": f"{solver.upper()} double",
            "x": float(snr_row["sigma_fp_l1"]),
            "y": float(losos_row["s_worst_q05"]),
            "s_req": float(s_req_row["s_req"]),
        })

    s_req_target = max(p["s_req"] for p in points)  # use the larger as conservative target

    fig, ax = plt.subplots(figsize=(7, 5))
    for p in points:
        ax.scatter(p["x"], p["y"], s=80, label=p["label"])
        ax.annotate(p["label"], (p["x"], p["y"]),
                    xytext=(8, 4), textcoords="offset points", fontsize=9)

    ax.set_xscale("log")
    ax.axhline(s_req_target, linestyle="--", color="gray",
               label=f"s_req(N={args.N}) ≈ {s_req_target:.2f}")
    ax.set_xlabel(r"$\sigma_{FP,L1}$ (rho)")
    ax.set_ylabel(r"$s_{worst,q05}$ (rho)")
    ax.set_title(f"LW Config 3 tradeoff (N={args.N}², ρ)")
    ax.legend(loc="best", fontsize=9)
    ax.grid(True, which="both", linestyle=":", alpha=0.5)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(args.out, dpi=120)
    plt.close(fig)
    print(f"[pareto] wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
