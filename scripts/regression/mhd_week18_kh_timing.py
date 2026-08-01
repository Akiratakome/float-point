#!/usr/bin/env python3
"""Five-repeat KH HLL/HLLD precision timing experiment for Report 2."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import pathlib
import platform
import sys
from contextlib import contextmanager
from typing import Any, Iterable

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "experiments" / "week18" / "kh_solver_timing"
CFG = ROOT / "tests" / "cases" / "kelvin_helmholtz_2d" / "kh.cfg"
for item in (ROOT, ROOT / "scripts", ROOT / "scripts" / "metrics", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(item))

from _mhd_harness import git_commit, replace_or_append_cfg, resolve_binary, run_case, sha256_file  # noqa: E402
from io_helper import read_binary  # noqa: E402
from mhd_fields import mhd_primitive_fields  # noqa: E402
from mhd_gpu_hardware_axis import max_ulp_distance  # noqa: E402

EXPERIMENT = "week18-kh-solver-timing"
SOLVERS = ("hll", "hlld")
PRECISIONS = ("double", "float")
BINARIES = {"double": ROOT / "build-double" / "hrsc_mhd", "float": ROOT / "build-float" / "hrsc_mhd"}


def plan_rows(repeats: int = 5) -> list[dict[str, Any]]:
    if repeats < 1:
        raise ValueError("repeats must be positive")
    return [{"solver": solver, "precision": precision, "repeat": repeat} for solver in SOLVERS for precision in PRECISIONS for repeat in range(1, repeats + 1)]


def median_iqr(values: Iterable[float]) -> tuple[float, float]:
    arr = np.asarray(tuple(values), dtype=np.float64)
    if not arr.size or not np.isfinite(arr).all():
        raise ValueError("finite timing values are required")
    return float(np.median(arr)), float(np.percentile(arr, 75) - np.percentile(arr, 25))


def aggregate(rows: list[dict[str, Any]], precision_error: dict[str, float], commit: str, repeats: int = 5) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    indexed: dict[tuple[str, str], dict[str, Any]] = {}
    missing: list[dict[str, Any]] = []
    for solver in SOLVERS:
        for precision in PRECISIONS:
            selected = sorted([row for row in rows if row["solver"] == solver and row["precision"] == precision], key=lambda row: row["repeat"])
            present = {int(row["repeat"]) for row in selected}
            for repeat in range(1, repeats + 1):
                if repeat not in present:
                    missing.append({"solver": solver, "precision": precision, "repeat": repeat})
            if len(selected) != repeats:
                continue
            times = np.asarray([float(row["elapsed_wall_s"]) for row in selected], dtype=np.float64)
            median, iqr = median_iqr(times)
            q25, q75 = float(np.percentile(times, 25)), float(np.percentile(times, 75))
            group = {"solver": solver, "precision": precision, "repeats": repeats, "wall_time_median_s": median, "wall_time_iqr_s": iqr, "wall_time_q25_s": q25, "wall_time_q75_s": q75, "wall_time_min_s": float(np.min(times)), "wall_time_max_s": float(np.max(times)), "max_ulp_vs_repeat1": max(int(row["ulp_vs_repeat1"]) for row in selected)}
            groups.append(group); indexed[(solver, precision)] = group
    complete = not missing and len(rows) == repeats * len(SOLVERS) * len(PRECISIONS) and all(row["status"] == "completed" and row["physical_state"] and int(row["ulp_vs_repeat1"]) == 0 for row in rows)
    comparisons = {
        "fp32_speedup": {solver: indexed[(solver, "double")]["wall_time_median_s"] / indexed[(solver, "float")]["wall_time_median_s"] for solver in SOLVERS} if len(indexed) == 4 else {},
        "hlld_over_hll_cost": {precision: indexed[("hlld", precision)]["wall_time_median_s"] / indexed[("hll", precision)]["wall_time_median_s"] for precision in PRECISIONS} if len(indexed) == 4 else {},
        "Linf_rho_fp32_vs_fp64": precision_error,
    }
    return {
        "schema": {"name": "hrsc.week18-kh-solver-timing", "version": 1}, "experiment": EXPERIMENT, "git_commit": commit,
        "configuration": {"case": "kelvin_helmholtz_2d", "nx": 256, "ny": 256, "t_end": 1.0, "cfl": 0.4, "omp_num_threads": 1, "warmups_per_group": 1, "measured_repeats": repeats, "timer_scope": "harness subprocess wall time including solver startup and binary output"},
        "environment": {"platform": platform.platform(), "processor": platform.processor(), "python": platform.python_version()},
        "gate": {"pass": complete and len(groups) == 4, "complete_matrix": complete, "missing_runs": missing, "repeat_outputs_bit_exact": complete},
        "groups": groups, "comparisons": comparisons, "runs": rows,
        "claims": {"timing_statistic": "median", "variability_statistic": "interquartile range (P75-P25)", "broad_performance_benchmark": False, "claim_boundary": "Five repeats on one workstation support a bounded KH CPU comparison; they do not establish cross-machine performance portability."},
    }


@contextmanager
def _environment(values: dict[str, str]):
    previous = {key: os.environ.get(key) for key in values}
    try:
        os.environ.update(values); yield
    finally:
        for key, value in previous.items():
            if value is None: os.environ.pop(key, None)
            else: os.environ[key] = value


def _cfg_text(solver: str, output: pathlib.Path) -> str:
    text = CFG.read_text(encoding="utf-8")
    for key, value in (("riemann", solver), ("device", "cpu"), ("output_format", "binary"), ("output_file", str(output))):
        text = replace_or_append_cfg(text, key, value)
    return text


def _physical(arr: np.ndarray) -> tuple[bool, float, float]:
    fields = mhd_primitive_fields(arr, 5.0 / 3.0)
    rho_min, p_min = float(np.min(fields["rho"])), float(np.min(fields["p"]))
    return bool(np.isfinite(arr).all() and rho_min > 0.0 and p_min > 0.0), rho_min, p_min


def _run_one(solver: str, precision: str, label: str, out: pathlib.Path, commit: str) -> tuple[dict[str, Any], np.ndarray, pathlib.Path]:
    binary = resolve_binary(BINARIES[precision]); run_dir = out / "runs" / label; grid = run_dir / "grid.bin"; text = _cfg_text(solver, grid.resolve())
    _, metadata, _ = run_case(label, text, run_dir, binary, CFG, commit, sha256_file(binary), output_bin=grid.resolve(), experiment=EXPERIMENT)
    header, view = read_binary(grid); arr = np.array(view, copy=True)
    physical, rho_min, p_min = _physical(arr); diag = metadata.get("stderr_diagnostics", {})
    row = {"solver": solver, "precision": precision, "status": "completed", "physical_state": physical, "steps": int(diag.get("steps", 0)), "divB_max": float(diag.get("divB_max", math.nan)), "elapsed_wall_s": float(metadata["elapsed_wall_s"]), "precision_bytes": int(header.precision_tag), "rho_min": rho_min, "pressure_min": p_min, "binary_sha256": sha256_file(binary), "run_dir": run_dir.relative_to(ROOT).as_posix()}
    return row, arr, grid


def _write(summary: dict[str, Any], out: pathlib.Path) -> None:
    out.mkdir(parents=True, exist_ok=True); (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    with (out / "runs.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary["runs"][0])); writer.writeheader(); writer.writerows(summary["runs"])
    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary["groups"][0])); writer.writeheader(); writer.writerows(summary["groups"])
    lines = ["# Week 18 KH solver and precision timing", "", f"Gate pass: `{summary['gate']['pass']}`.", "", "| solver | precision | median (s) | IQR (s) | min-max (s) | max ULP between repeats |", "|---|---|---:|---:|---:|---:|"]
    for group in summary["groups"]:
        lines.append(f"| {group['solver'].upper()} | {'FP64' if group['precision']=='double' else 'FP32'} | {group['wall_time_median_s']:.3f} | {group['wall_time_iqr_s']:.3f} | {group['wall_time_min_s']:.3f}-{group['wall_time_max_s']:.3f} | {group['max_ulp_vs_repeat1']} |")
    lines += ["", f"FP32 speed-up: HLL `{summary['comparisons']['fp32_speedup']['hll']:.3f}x`, HLLD `{summary['comparisons']['fp32_speedup']['hlld']:.3f}x`.", f"HLLD/HLL cost: FP64 `{summary['comparisons']['hlld_over_hll_cost']['double']:.3f}x`, FP32 `{summary['comparisons']['hlld_over_hll_cost']['float']:.3f}x`.", "", summary["claims"]["claim_boundary"], ""]
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def _plot(summary: dict[str, Any], out: pathlib.Path) -> pathlib.Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.linewidth": 0.8, "savefig.dpi": 320})
    groups = {(g["solver"], g["precision"]): g for g in summary["groups"]}; colors = {"double": "#24557a", "float": "#c5523c"}; x = np.arange(2); width = 0.34
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.2), constrained_layout=True)
    for offset, precision in ((-width / 2, "double"), (width / 2, "float")):
        vals = [groups[(solver, precision)]["wall_time_median_s"] for solver in SOLVERS]
        lower = [groups[(solver, precision)]["wall_time_median_s"] - groups[(solver, precision)]["wall_time_q25_s"] for solver in SOLVERS]
        upper = [groups[(solver, precision)]["wall_time_q75_s"] - groups[(solver, precision)]["wall_time_median_s"] for solver in SOLVERS]
        axes[0].bar(x + offset, vals, width, yerr=np.asarray([lower, upper]), capsize=4, color=colors[precision], label="FP64" if precision == "double" else "FP32")
    axes[0].set_xticks(x, [s.upper() for s in SOLVERS]); axes[0].set_ylabel("Wall time (s), median of five"); axes[0].set_title("(a) End-to-end KH runtime", loc="left", fontweight="bold"); axes[0].grid(axis="y", color="#d8dde3", linewidth=0.6); axes[0].legend(frameon=False)
    labels = ["FP32 speed-up (HLL)", "FP32 speed-up (HLLD)", "HLLD/HLL cost (FP64)", "HLLD/HLL cost (FP32)"]
    values = [summary["comparisons"]["fp32_speedup"]["hll"], summary["comparisons"]["fp32_speedup"]["hlld"], summary["comparisons"]["hlld_over_hll_cost"]["double"], summary["comparisons"]["hlld_over_hll_cost"]["float"]]
    ypos = np.arange(4); bars = axes[1].barh(ypos, values, color=["#c5523c", "#c5523c", "#6f5a8a", "#6f5a8a"]); axes[1].axvline(1.0, color="#33383e", linestyle="--", linewidth=0.9); axes[1].set_yticks(ypos, labels); axes[1].invert_yaxis(); axes[1].set_xlabel("Dimensionless ratio"); axes[1].set_title("(b) Precision gain and solver cost", loc="left", fontweight="bold"); axes[1].grid(axis="x", color="#d8dde3", linewidth=0.6); axes[1].bar_label(bars, fmt="%.2fx", padding=3, fontsize=8); axes[1].set_xlim(0.95, max(values) + 0.08)
    for solver, marker, color in (("hll", "o", "#24557a"), ("hlld", "s", "#8f2d35")):
        axes[2].scatter(groups[(solver, "float")]["wall_time_median_s"], summary["comparisons"]["Linf_rho_fp32_vs_fp64"][solver], s=72, marker=marker, color=color, label=solver.upper(), zorder=3)
    axes[2].set_yscale("log"); axes[2].set_xlabel("FP32 median wall time (s)"); axes[2].set_ylabel(r"$L_\infty(\rho_{FP32}-\rho_{FP64})$"); axes[2].set_title("(c) FP32 accuracy-cost position", loc="left", fontweight="bold"); axes[2].grid(which="both", color="#d8dde3", linewidth=0.6); axes[2].legend(frameon=False)
    fig.suptitle("Kelvin-Helmholtz 256 x 256 CPU timing: solver and precision", fontsize=13, fontweight="bold")
    fig_dir = out / "figures"; fig_dir.mkdir(parents=True, exist_ok=True); target = fig_dir / "kh_solver_precision_timing.png"; fig.savefig(target, bbox_inches="tight", facecolor="white"); plt.close(fig); return target


def run(out: pathlib.Path, repeats: int = 5) -> dict[str, Any]:
    commit = git_commit(); rows: list[dict[str, Any]] = []; references: dict[tuple[str, str], np.ndarray] = {}; first_arrays: dict[tuple[str, str], np.ndarray] = {}; grids: list[pathlib.Path] = []
    with _environment({"OMP_NUM_THREADS": "1"}):
        for solver in SOLVERS:
            for precision in PRECISIONS:
                warm_label = f"kh-{solver}-{precision}-warmup"
                print(f"[kh-timing] warm-up {solver} {precision}", flush=True)
                _, _, warm_grid = _run_one(solver, precision, warm_label, out, commit); grids.append(warm_grid)
                for repeat in range(1, repeats + 1):
                    label = f"kh-{solver}-{precision}-r{repeat:02d}"; print(f"[kh-timing] measured {solver} {precision} {repeat}/{repeats}", flush=True)
                    row, arr, grid = _run_one(solver, precision, label, out, commit); key = (solver, precision)
                    if key not in references: references[key] = arr; first_arrays[key] = arr
                    row["repeat"] = repeat; row["ulp_vs_repeat1"] = max_ulp_distance(arr, references[key]); rows.append(row); grids.append(grid)
    errors = {}
    for solver in SOLVERS:
        fp64 = mhd_primitive_fields(first_arrays[(solver, "double")].astype(np.float64), 5.0 / 3.0)["rho"]
        fp32 = mhd_primitive_fields(first_arrays[(solver, "float")].astype(np.float64), 5.0 / 3.0)["rho"]
        errors[solver] = float(np.max(np.abs(fp32 - fp64)))
    summary = aggregate(rows, errors, commit, repeats); _write(summary, out); figure = _plot(summary, out)
    for grid in grids:
        if grid.name != "grid.bin": raise ValueError(f"refusing to remove {grid}")
        grid.unlink(missing_ok=True)
    print(f"gate_pass: {summary['gate']['pass']}"); print(f"figure: {figure}"); return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT); parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args(argv); summary = run(args.out.resolve(), args.repeats); return 0 if summary["gate"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())