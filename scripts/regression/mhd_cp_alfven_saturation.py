#!/usr/bin/env python3
"""Circularly polarised Alfven wave: where fp32 round-off overtakes truncation.

mhd_cp_alfven_convergence.py verifies the observed order of accuracy on
N = 32..512, the range over which fp32 and fp64 are indistinguishable. That
range cannot answer the question the project is about: at which resolution does
the working precision, rather than the discretisation, set the error?

This driver extends the same exact-solution ladder to N = 8192. Because the
Alfven wave has an analytic final state, the error plotted here is true
discretisation error and not a self-refinement rate, so the fp32 curve leaving
the fp64 curve is a direct measurement of the round-off floor rather than an
inference from a discrepancy.

Reported per group and grid:
  * mean L1 error of the transverse field against the analytic solution;
  * the fp32-minus-fp64 error excess, and its size relative to the fp64 error;
  * the pairwise observed order, which decays towards zero once fp32 saturates.

The saturation grid is declared as the coarsest N at which the fp32 error
exceeds the matched fp64 error by more than SATURATION_TOL, held for every
finer grid, so a single noisy rung cannot trigger it.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from scripts.regression._mhd_harness import (  # noqa: E402
    ROOT,
    git_commit,
    replace_or_append_cfg,
    resolve_binary,
    run_case,
    sha256_file,
)
from scripts.regression.mhd_cp_alfven_convergence import (  # noqa: E402
    BINS,
    CFG,
    fit_order,
    measure,
)

DEFAULT_OUT = ROOT / "experiments" / "week21" / "cp_alfven_saturation"
EXPERIMENT = "week21-cp-alfven-saturation"
GRIDS = (32, 64, 128, 256, 512, 1024, 2048, 4096, 8192)
# Order-verification range: the published fit, kept unchanged for comparison.
ORDER_FIT_GRIDS = (32, 64, 128, 256, 512)
# 5 per cent excess over the matched fp64 error. Well above the ~0.3 per cent
# separation already visible at N=512 and well below a decade, so the declared
# grid is the onset of a real departure rather than of measurement noise.
SATURATION_TOL = 0.05
IMPLEMENTATION_SOURCES = (
    ROOT / "src" / "mhd" / "mhd_solver.cpp",
    ROOT / "src" / "mhd" / "mhd_config.hpp",
    ROOT / "src" / "mhd_main.cpp",
    pathlib.Path(__file__).resolve(),
)


def run_group(precision: str, device: str, out: pathlib.Path,
              commit: str, grids: tuple[int, ...]) -> dict | None:
    try:
        binary = resolve_binary(BINS[(precision, device)])
    except (FileNotFoundError, KeyError):
        return None
    binary_sha = sha256_file(binary)
    base = CFG.read_text(encoding="utf-8")
    rows: list[dict[str, float]] = []
    for nx in grids:
        label = f"cp_alfven-{precision}-{device}-n{nx}"
        run_dir = out / "runs" / label
        out_bin = run_dir / "grid.bin"
        text = replace_or_append_cfg(base, "nx", str(nx))
        text = replace_or_append_cfg(text, "device", device)
        text = replace_or_append_cfg(text, "riemann", "hll")
        text = replace_or_append_cfg(text, "output_format", "binary")
        text = replace_or_append_cfg(text, "output_file", str(out_bin).replace("\\", "/"))
        run_case(label, text, run_dir, binary, CFG, commit, binary_sha,
                 output_bin=out_bin, experiment=EXPERIMENT)
        row = measure(out_bin)
        meta = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
        diag = meta.get("stderr_diagnostics", {})
        row["steps"] = diag.get("steps")
        row["divB_max"] = diag.get("divB_max")
        row["elapsed_wall_s"] = meta.get("elapsed_wall_s")
        rows.append(row)
        out_bin.unlink(missing_ok=True)  # scalar summary retained; grid discarded
    subset = [r for r in rows if r["nx"] in ORDER_FIT_GRIDS]
    return {
        "precision": precision,
        "device": device,
        "binary": str(binary),
        "binary_sha256": binary_sha,
        "rows": rows,
        "fit_l1_order_range": fit_order(subset, "l1"),
        "fit_l1_full_range": fit_order(rows, "l1"),
    }


def pairwise(rows: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for a, b in zip(rows, rows[1:]):
        if a["l1"] > 0.0 and b["l1"] > 0.0:
            out.append({
                "coarse": a["nx"], "fine": b["nx"],
                "order": float(math.log2(a["l1"] / b["l1"])
                               / math.log2(b["nx"] / a["nx"])),
            })
    return out


def compare(fp64: dict, fp32: dict) -> dict:
    """fp32 error excess over the matched fp64 error, grid by grid."""
    by_n64 = {r["nx"]: r["l1"] for r in fp64["rows"]}
    table, saturation = [], None
    for r in fp32["rows"]:
        e64 = by_n64.get(r["nx"])
        if e64 is None or e64 <= 0.0:
            continue
        table.append({
            "nx": r["nx"],
            "l1_fp64": e64,
            "l1_fp32": r["l1"],
            "excess_abs": r["l1"] - e64,
            "excess_rel": (r["l1"] - e64) / e64,
            "steps": r["steps"],
        })
    for i, row in enumerate(table):
        if row["excess_rel"] > SATURATION_TOL and all(
                t["excess_rel"] > SATURATION_TOL for t in table[i:]):
            saturation = row["nx"]
            break
    return {
        "tolerance_rel": SATURATION_TOL,
        "rows": table,
        "saturation_grid": saturation,
        "pairwise_order_fp64": pairwise(fp64["rows"]),
        "pairwise_order_fp32": pairwise(fp32["rows"]),
    }


def plot(groups: list[dict], comparison: dict, out: pathlib.Path) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    styles = {
        ("double", "cpu"): ("#0072B2", "o", "fp64 CPU"),
        ("double", "gpu"): ("#56B4E9", "s", "fp64 GPU"),
        ("float", "cpu"): ("#D55E00", "^", "fp32 CPU"),
        ("float", "gpu"): ("#E69F00", "d", "fp32 GPU"),
    }
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(9.4, 3.9), constrained_layout=True)

    for g in groups:
        colour, marker, label = styles[(g["precision"], g["device"])]
        n = [r["nx"] for r in g["rows"]]
        e = [r["l1"] for r in g["rows"]]
        ax.loglog(n, e, color=colour, marker=marker, linewidth=1.3, markersize=4.2,
                  label=label, zorder=3)
    ref = np.array([32.0, 8192.0])
    anchor = groups[0]["rows"][0]["l1"]
    ax.loglog(ref, anchor * (ref / ref[0]) ** -2.0, color="#5F6368",
              linestyle="--", linewidth=1.0, label="second order", zorder=2)
    sat = comparison.get("saturation_grid")
    if sat:
        ax.axvline(sat, color="#B00020", linewidth=0.9, linestyle=":", zorder=1)
        ax.annotate(f"fp32 departs\nat $N={sat}$", xy=(sat, anchor * 0.02),
                    xytext=(4, 0), textcoords="offset points", fontsize=8,
                    color="#B00020", va="center")
    ax.set_xlabel("Grid cells $N$")
    ax.set_ylabel(r"Transverse field mean $L_1$ error")
    ax.set_title("(a) Error against the exact solution", loc="left", fontsize=10)
    ax.grid(True, which="major", color="#D9DEE5", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(fontsize=8)

    # Panel (b): the observed order between successive grids. fp64 climbs
    # towards two; fp32 tracks it and then collapses once rounding dominates.
    for key, colour, marker, label in (
            ("pairwise_order_fp64", "#0072B2", "o", "fp64"),
            ("pairwise_order_fp32", "#D55E00", "^", "fp32")):
        pairs = comparison[key]
        bx.semilogx([p["fine"] for p in pairs], [p["order"] for p in pairs],
                    color=colour, marker=marker, linewidth=1.3, markersize=4.2,
                    label=label, zorder=3)
    bx.axhline(2.0, color="#5F6368", linestyle="--", linewidth=1.0,
               label="second order", zorder=2)
    if sat:
        bx.axvline(sat, color="#B00020", linewidth=0.9, linestyle=":", zorder=1)
    bx.set_xlabel("Finer grid $N$ of the pair")
    bx.set_ylabel("Observed order between successive grids")
    bx.set_title("(b) Order retained under refinement", loc="left", fontsize=10)
    bx.set_ylim(0.0, 2.4)
    bx.grid(True, which="major", color="#D9DEE5", linewidth=0.6)
    bx.set_axisbelow(True)
    bx.legend(fontsize=8, loc="lower left")

    ax.set_xticks(list(GRIDS))
    ax.set_xticklabels([str(v) for v in GRIDS], fontsize=7.5)
    ax.set_xticks([], minor=True)
    fine = [p["fine"] for p in comparison["pairwise_order_fp64"]]
    bx.set_xticks(fine)
    bx.set_xticklabels([str(v) for v in fine], fontsize=7.5)
    bx.set_xticks([], minor=True)

    paths = []
    (out / "figures").mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "pdf"):
        p = out / "figures" / f"cp_alfven_saturation.{suffix}"
        fig.savefig(p, dpi=320)
        paths.append(str(p.relative_to(ROOT)))
    plt.close(fig)
    return paths


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    ap.add_argument("--grids", type=int, nargs="*", default=list(GRIDS))
    ap.add_argument("--devices", nargs="*", default=["cpu", "gpu"])
    ap.add_argument("--replot-only", action="store_true",
                    help="redraw from the retained summary without re-running")
    args = ap.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    commit = git_commit()
    grids = tuple(sorted(args.grids))

    if args.replot_only:
        payload = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        primary = (payload["comparisons"].get("cpu")
                   or next(iter(payload["comparisons"].values())))
        payload["figures"] = plot(payload["groups"], primary, out)
        (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n",
                                          encoding="utf-8")
        print("replotted:", ", ".join(payload["figures"]))
        return 0

    groups, skipped = [], []
    for precision in ("double", "float"):
        for device in args.devices:
            g = run_group(precision, device, out, commit, grids)
            if g is None:
                skipped.append(f"{precision}-{device}")
            else:
                groups.append(g)
    if not groups:
        raise SystemExit("no usable builds found")

    def pick(precision, device):
        return next((g for g in groups if g["precision"] == precision
                     and g["device"] == device), None)

    comparisons = {}
    for device in args.devices:
        f64, f32 = pick("double", device), pick("float", device)
        if f64 and f32:
            comparisons[device] = compare(f64, f32)
    primary = comparisons.get("cpu") or next(iter(comparisons.values()))
    figures = plot(groups, primary, out)

    payload = {
        "experiment": EXPERIMENT,
        "scope": ("Circularly polarised Alfven wave, exact solution. Locates the "
                  "grid at which fp32 round-off overtakes truncation error."),
        "git_commit": commit,
        "grids": list(grids),
        "order_fit_grids": list(ORDER_FIT_GRIDS),
        "saturation_tolerance_rel": SATURATION_TOL,
        "implementation_sources": {
            str(p.relative_to(ROOT)): sha256_file(p) for p in IMPLEMENTATION_SOURCES
        },
        "source_config": str(CFG.relative_to(ROOT)),
        "source_config_sha256": sha256_file(CFG),
        "groups": groups,
        "comparisons": comparisons,
        "skipped_builds": skipped,
        "figures": figures,
        "claim_boundary": [
            "True discretisation error: the exact final state is the initial condition.",
            "The saturation grid is specific to this case, CFL, solver and error norm.",
            "Beyond saturation the fp32 slope is not an order of accuracy.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    for g in groups:
        print(f"{g['precision']:6s} {g['device']:3s} "
              f"order[32-512]={g['fit_l1_order_range']['order']:.3f}  "
              + "  ".join(f"N{r['nx']}={r['l1']:.4e}" for r in g["rows"]))
    for device, c in comparisons.items():
        print(f"\n[{device}] saturation grid = {c['saturation_grid']} "
              f"(> {c['tolerance_rel']:.0%} excess, sustained)")
        for r in c["rows"]:
            print(f"   N={r['nx']:5d}  fp64={r['l1_fp64']:.4e}  fp32={r['l1_fp32']:.4e}  "
                  f"excess={r['excess_rel']:+.3%}")
        print("   pairwise order fp64: "
              + ", ".join(f"{p['coarse']}->{p['fine']}:{p['order']:.2f}"
                          for p in c["pairwise_order_fp64"]))
        print("   pairwise order fp32: "
              + ", ".join(f"{p['coarse']}->{p['fine']}:{p['order']:.2f}"
                          for p in c["pairwise_order_fp32"]))
    if skipped:
        print("skipped (build absent):", ", ".join(skipped))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
