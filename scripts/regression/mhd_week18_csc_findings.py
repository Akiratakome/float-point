#!/usr/bin/env python3
"""Synthesize CSC KH MCA findings and run a matched local deterministic check."""

from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys
from typing import Any

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments" / "report2_w16_verificarlo_findings"
DEFAULT_OUT = ROOT / "experiments" / "week18" / "csc_findings_synthesis"
CFG = ROOT / "scripts" / "cluster" / "report2_w16_w17_slurm" / "cfg" / "kh_64_t005.cfg"
for item in (ROOT, ROOT / "scripts", ROOT / "scripts" / "metrics", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(item))

from _mhd_harness import git_commit, replace_or_append_cfg, resolve_binary, run_case, sha256_file  # noqa: E402
from io_helper import read_binary  # noqa: E402
from mhd_fields import mhd_primitive_fields  # noqa: E402

FIELDS = ("rho", "vx", "By", "p")
SOLVERS = ("hll", "hlld")
PRECISIONS = ("double", "float")
BINARIES = {"double": ROOT / "build-double" / "hrsc_mhd", "float": ROOT / "build-float" / "hrsc_mhd"}
EXPERIMENT = "week18-csc-kh-mca-synthesis"


def local_plan() -> list[dict[str, str]]:
    return [{"solver": solver, "precision": precision} for solver in SOLVERS for precision in PRECISIONS]


def load_csc_summaries(source: pathlib.Path = SOURCE) -> dict[str, dict[str, Any]]:
    return {
        solver: json.loads((source / "smoke_validation_64sq" / solver / "summary.json").read_text(encoding="utf-8"))
        for solver in SOLVERS
    }


def derive_csc_metrics(summaries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    complete = True
    amplification: dict[str, dict[str, Any]] = {}
    for solver in SOLVERS:
        blocks = summaries[solver]["mca"]
        complete = complete and all(blocks[p]["status"] == "completed" and int(blocks[p]["n"]) == 4 for p in ("p24", "p53"))
        amplification[solver] = {}
        for field in FIELDS:
            p24 = float(blocks["p24"][f"spread_{field}"])
            p53 = float(blocks["p53"][f"spread_{field}"])
            ratio = p24 / p53
            amplification[solver][field] = {"p24": p24, "p53": p53, "ratio": ratio, "decades": math.log10(ratio)}
    solver_ratio = {
        field: float(summaries["hlld"]["mca"]["p24"][f"spread_{field}"]) / float(summaries["hll"]["mca"]["p24"][f"spread_{field}"])
        for field in FIELDS
    }
    all_large = all(amplification[s][f]["ratio"] > 1.0e6 for s in SOLVERS for f in FIELDS)
    return {
        "gate": {"pass": complete, "completed_blocks": 4 if complete else sum(summaries[s]["mca"][p]["status"] == "completed" for s in SOLVERS for p in ("p24", "p53")), "expected_blocks": 4},
        "precision_amplification": amplification,
        "solver_ratio_p24": solver_ratio,
        "claims": {
            "reduced_pipeline_validated": complete,
            "p24_p53_separation_over_six_decades_all_fields": complete and all_large,
            "hlld_p24_spread_exceeds_hll_all_fields": complete and all(value > 1.0 for value in solver_ratio.values()),
            "full_resolution_mca_completed": False,
            "small_sample_exploratory": True,
        },
    }


def _config_text(solver: str, output: pathlib.Path) -> str:
    text = CFG.read_text(encoding="utf-8")
    for key, value in (("riemann", solver), ("device", "cpu"), ("output_format", "binary"), ("output_file", str(output))):
        text = replace_or_append_cfg(text, key, value)
    return text


def _run_local(spec: dict[str, str], out: pathlib.Path, commit: str) -> tuple[dict[str, Any], np.ndarray, pathlib.Path]:
    solver, precision = spec["solver"], spec["precision"]
    binary = resolve_binary(BINARIES[precision])
    run_id = f"kh64-{solver}-{precision}"
    run_dir = out / "runs" / run_id
    grid = run_dir / "grid.bin"
    cfg_text = _config_text(solver, grid.resolve())
    _, metadata, _ = run_case(run_id, cfg_text, run_dir, binary, CFG, commit, sha256_file(binary), output_bin=grid.resolve(), experiment=EXPERIMENT)
    header, view = read_binary(grid)
    arr = np.array(view, dtype=np.float64, copy=True)
    fields = mhd_primitive_fields(arr, 5.0 / 3.0)
    physical = bool(np.isfinite(arr).all() and np.min(fields["rho"]) > 0.0 and np.min(fields["p"]) > 0.0)
    diagnostics = metadata.get("stderr_diagnostics", {})
    row = {
        **spec, "status": "completed", "physical_state": physical,
        "steps": int(diagnostics.get("steps", 0)), "divB_max": float(diagnostics.get("divB_max", math.nan)),
        "wall_time_s": float(metadata["elapsed_wall_s"]), "precision_bytes": int(header.precision_tag),
        "rho_min": float(np.min(fields["rho"])), "pressure_min": float(np.min(fields["p"])),
        "binary_sha256": sha256_file(binary), "run_dir": run_dir.relative_to(ROOT).as_posix(),
    }
    return row, arr, grid


def deterministic_metrics(arrays: dict[tuple[str, str], np.ndarray]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for solver in SOLVERS:
        fp64 = mhd_primitive_fields(arrays[(solver, "double")], 5.0 / 3.0)
        fp32 = mhd_primitive_fields(arrays[(solver, "float")], 5.0 / 3.0)
        result[solver] = {field: float(np.max(np.abs(fp32[field] - fp64[field]))) for field in FIELDS}
    return result


def assemble_summary(csc: dict[str, dict[str, Any]], derived: dict[str, Any], rows: list[dict[str, Any]], deterministic: dict[str, dict[str, float]], commit: str) -> dict[str, Any]:
    local_pass = len(rows) == 4 and all(row["status"] == "completed" and row["physical_state"] and row["steps"] > 0 for row in rows)
    triangulation = {
        solver: {
            field: {
                "deterministic_linf_fp32_vs_fp64": deterministic[solver][field],
                "csc_p24_mca_spread": derived["precision_amplification"][solver][field]["p24"],
                "deterministic_to_mca_ratio": deterministic[solver][field] / derived["precision_amplification"][solver][field]["p24"],
            }
            for field in FIELDS
        }
        for solver in SOLVERS
    }
    return {
        "schema": {"name": "hrsc.week18-csc-findings-synthesis", "version": 1},
        "experiment": EXPERIMENT, "git_commit": commit,
        "sources": {"csc_bundle": SOURCE.relative_to(ROOT).as_posix(), "csc_config": CFG.relative_to(ROOT).as_posix(), "csc_host": "phy-cerberus6", "verificarlo": "2.4.0 native", "clang": "18.1.3"},
        "scope": {"case": "kelvin_helmholtz_2d", "nx": 64, "ny": 64, "t_end": 0.05, "cfl": 0.4, "mca_samples": 4},
        "gate": {"pass": bool(derived["gate"]["pass"] and local_pass), "csc_smoke_pass": derived["gate"]["pass"], "local_deterministic_pass": local_pass},
        "claims": {
            **derived["claims"],
            "matched_deterministic_triangulation": local_pass,
            "claim_boundary": "The 64^2, t=0.05, N=4 result validates the pipeline and provides reduced-case directional evidence only; it does not promote the full 256^2, t=1.0, N=30 KH MCA claim.",
        },
        "csc_derived": derived, "local_runs": rows, "deterministic_linf": deterministic, "triangulation": triangulation,
        "cost": {
            "source": "CSC README_findings.md and raw timing logs; t=0.02, 23 steps on athena unless noted",
            "seconds_per_step": {"native": 0.0575, "mca_quad": 24.0, "mca_int_mca": 11.43, "mca_int_rr": 6.25},
            "quad_overhead_vs_native": 24.0 / 0.0575,
            "mca_int_reduced_precision_supported": False,
            "dedicated_quad_sample_hours_observed_range": [2.5, 3.0],
            "csc_partition_limit_hours": 6.0, "samples_per_block": 30, "parallel_workers": 32,
        },
        "csc_raw": csc,
    }


def _write(summary: dict[str, Any], out: pathlib.Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["solver", "field", "p53_spread", "p24_spread", "p24_p53_ratio", "amplification_decades", "deterministic_linf", "deterministic_to_p24_ratio"]
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for solver in SOLVERS:
            for field in FIELDS:
                amp = summary["csc_derived"]["precision_amplification"][solver][field]
                tri = summary["triangulation"][solver][field]
                writer.writerow({"solver": solver, "field": field, "p53_spread": amp["p53"], "p24_spread": amp["p24"], "p24_p53_ratio": amp["ratio"], "amplification_decades": amp["decades"], "deterministic_linf": tri["deterministic_linf_fp32_vs_fp64"], "deterministic_to_p24_ratio": tri["deterministic_to_mca_ratio"]})
    lines = ["# CSC KH MCA findings synthesis", "", f"Combined gate: `{summary['gate']['pass']}`.", "", "| solver | field | p53 spread | p24 spread | p24/p53 | deterministic Linf | det./p24 |", "|---|---|---:|---:|---:|---:|---:|"]
    for solver in SOLVERS:
        for field in FIELDS:
            amp = summary["csc_derived"]["precision_amplification"][solver][field]; tri = summary["triangulation"][solver][field]
            lines.append(f"| {solver.upper()} | {field} | {amp['p53']:.3e} | {amp['p24']:.3e} | {amp['ratio']:.3e} | {tri['deterministic_linf_fp32_vs_fp64']:.3e} | {tri['deterministic_to_mca_ratio']:.2f} |")
    lines += ["", "## Claim boundary", "", summary["claims"]["claim_boundary"], ""]
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def _plots(summary: dict[str, Any], out: pathlib.Path) -> list[pathlib.Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.linewidth": 0.8, "savefig.dpi": 320})
    figure_dir = out / "figures"; figure_dir.mkdir(parents=True, exist_ok=True)
    colors = {"hll": "#1f5a7a", "hlld": "#a33b3b"}

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.2), constrained_layout=True)
    x = np.arange(len(FIELDS)); width = 0.34
    for offset, solver in ((-width / 2, "hll"), (width / 2, "hlld")):
        p24 = [summary["csc_derived"]["precision_amplification"][solver][f]["p24"] for f in FIELDS]
        axes[0].bar(x + offset, p24, width, color=colors[solver], label=solver.upper())
    axes[0].set_yscale("log"); axes[0].set_xticks(x, FIELDS); axes[0].set_ylabel("Maximum MCA field spread"); axes[0].set_title("(a) p24 reduced-precision spread", loc="left", fontweight="bold"); axes[0].legend(frameon=False); axes[0].grid(axis="y", which="both", color="#d8dde3", linewidth=0.6)
    for offset, solver in ((-width / 2, "hll"), (width / 2, "hlld")):
        vals = [summary["csc_derived"]["precision_amplification"][solver][f]["decades"] for f in FIELDS]
        axes[1].bar(x + offset, vals, width, color=colors[solver], label=solver.upper())
    axes[1].axhline(7, color="#555b63", linestyle="--", linewidth=0.9, label="7 decades"); axes[1].set_xticks(x, FIELDS); axes[1].set_ylabel(r"$\log_{10}$(p24 spread / p53 spread)"); axes[1].set_title("(b) precision-noise amplification", loc="left", fontweight="bold"); axes[1].grid(axis="y", color="#d8dde3", linewidth=0.6)
    for solver, marker in (("hll", "o"), ("hlld", "s")):
        xv = [summary["triangulation"][solver][f]["csc_p24_mca_spread"] for f in FIELDS]
        yv = [summary["triangulation"][solver][f]["deterministic_linf_fp32_vs_fp64"] for f in FIELDS]
        axes[2].scatter(xv, yv, s=52, marker=marker, color=colors[solver], label=solver.upper(), zorder=3)
        for field, xx, yy in zip(FIELDS, xv, yv): axes[2].annotate(field, (xx, yy), xytext=(4, 4), textcoords="offset points", fontsize=8)
    values = [summary["triangulation"][s][f][k] for s in SOLVERS for f in FIELDS for k in ("csc_p24_mca_spread", "deterministic_linf_fp32_vs_fp64")]
    lo, hi = min(values) / 2, max(values) * 2; axes[2].plot([lo, hi], [lo, hi], color="#555b63", linestyle="--", linewidth=0.9, label="equal magnitude")
    axes[2].set_xscale("log"); axes[2].set_yscale("log"); axes[2].set_xlim(lo, hi); axes[2].set_ylim(lo, hi); axes[2].set_xlabel("CSC p24 MCA spread"); axes[2].set_ylabel(r"Local $L_\infty$(FP32 - FP64)"); axes[2].set_title("(c) matched deterministic triangulation", loc="left", fontweight="bold"); axes[2].grid(which="both", color="#d8dde3", linewidth=0.6); axes[2].legend(frameon=False, fontsize=8)
    fig.suptitle("Kelvin-Helmholtz 64 x 64 precision sensitivity: CSC MCA and matched local evidence", fontsize=13, fontweight="bold")
    target1 = figure_dir / "csc_mca_precision_triangulation.png"; fig.savefig(target1, bbox_inches="tight", facecolor="white"); plt.close(fig)

    cost = summary["cost"]; names = ["Native IEEE", "MCA quad", "MCA-int MCA", "MCA-int RR"]; keys = ["native", "mca_quad", "mca_int_mca", "mca_int_rr"]
    seconds = [cost["seconds_per_step"][key] for key in keys]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
    palette = ["#4f6d7a", "#9c2f2f", "#d17b0f", "#4e8b57"]
    axes[0].bar(names, seconds, color=palette); axes[0].set_yscale("log"); axes[0].set_ylabel("Seconds per timestep (log scale)"); axes[0].set_title("(a) Measured instrumentation cost", loc="left", fontweight="bold"); axes[0].tick_params(axis="x", rotation=18); axes[0].grid(axis="y", which="both", color="#d8dde3", linewidth=0.6)
    task_names = ["One p53 block", "One p24 block", "p53 + p24\nsequential"]
    task_hours = [2.75, 2.75, 5.5]
    task_error = np.array([[0.25, 0.25, 0.5], [0.25, 0.25, 0.5]])
    axes[1].bar(task_names, task_hours, yerr=task_error, capsize=4, color=["#9c2f2f", "#9c2f2f", "#6c4b7d"])
    axes[1].axhline(6.0, color="#22272e", linestyle="--", linewidth=1.1)
    axes[1].text(0.98, 0.97, "CSC 6 h task limit", transform=axes[1].transAxes, ha="right", va="top", fontsize=8, bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5})
    axes[1].set_ylabel("Estimated task makespan (hours)"); axes[1].set_title("(b) Split precision blocks preserve margin", loc="left", fontweight="bold"); axes[1].grid(axis="y", color="#d8dde3", linewidth=0.6)
    axes[1].text(0.02, 0.88, "30 samples run concurrently with 32 workers", transform=axes[1].transAxes, va="top", fontsize=8, color="#4d535b", bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5})
    fig.suptitle("Verificarlo cost on CSC: correct progress, high arithmetic overhead", fontsize=13, fontweight="bold")
    target2 = figure_dir / "csc_mca_cost_feasibility.png"; fig.savefig(target2, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return [target1, target2]


def run(source: pathlib.Path, out: pathlib.Path) -> dict[str, Any]:
    csc = load_csc_summaries(source); derived = derive_csc_metrics(csc); commit = git_commit()
    rows: list[dict[str, Any]] = []; arrays: dict[tuple[str, str], np.ndarray] = {}; grids: list[pathlib.Path] = []
    for spec in local_plan():
        print(f"[csc-findings] local {spec['solver']} {spec['precision']}", flush=True)
        row, arr, grid = _run_local(spec, out, commit); rows.append(row); arrays[(spec["solver"], spec["precision"])] = arr; grids.append(grid)
    deterministic = deterministic_metrics(arrays); summary = assemble_summary(csc, derived, rows, deterministic, commit); _write(summary, out); figures = _plots(summary, out)
    for grid in grids:
        if grid.name != "grid.bin": raise ValueError(f"refusing to remove {grid}")
        grid.unlink(missing_ok=True)
    print(f"gate_pass: {summary['gate']['pass']}"); [print(f"figure: {figure}") for figure in figures]
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--source", type=pathlib.Path, default=SOURCE); parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv); summary = run(args.source.resolve(), args.out.resolve()); return 0 if summary["gate"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())