#!/usr/bin/env python3
"""Run a three-resolution OT/KH MHD self-convergence diagnostic."""

from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "experiments" / "week18" / "resolution_ladder"
for path in (ROOT, ROOT / "scripts", ROOT / "scripts" / "metrics", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(path))

from _mhd_harness import git_commit, replace_or_append_cfg, resolve_binary, run_case, sha256_file  # noqa: E402
from io_helper import read_binary  # noqa: E402
from mhd_fields import mhd_primitive_fields  # noqa: E402

EXPERIMENT = "week18-mhd-resolution-ladder"
CASES = ("orszag_tang_2d", "kelvin_helmholtz_2d")
SOLVERS = ("hll", "hlld")
PRECISIONS = ("double", "float")
RESOLUTIONS = (128, 256, 512)
CFL_BY_SOLVER = {"hll": 0.4, "hlld": 0.2}
CASE_LABELS = {"orszag_tang_2d": "Orszag-Tang", "kelvin_helmholtz_2d": "Kelvin-Helmholtz"}
CASE_CONFIGS = {
    "orszag_tang_2d": ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg",
    "kelvin_helmholtz_2d": ROOT / "tests" / "cases" / "kelvin_helmholtz_2d" / "kh.cfg",
}
BINARIES = {
    "double": ROOT / "build-matrix" / "cpu-double-O2-ieee-leq" / "hrsc_mhd",
    "float": ROOT / "build-matrix" / "cpu-float-O2-ieee-leq" / "hrsc_mhd",
}


def plan_rows() -> list[dict[str, Any]]:
    return [
        {"case": case, "solver": solver, "precision": precision, "resolution": resolution, "cfl": CFL_BY_SOLVER[solver]}
        for case in CASES
        for solver in SOLVERS
        for precision in PRECISIONS
        for resolution in RESOLUTIONS
    ]


def block_average_mhd(fine: np.ndarray, target_resolution: int) -> np.ndarray:
    arr = np.asarray(fine)
    if arr.ndim != 3 or arr.shape[-1] != 9:
        raise ValueError("fine must have shape (ny, nx, 9)")
    ny, nx, _ = arr.shape
    if target_resolution <= 0 or ny % target_resolution or nx % target_resolution:
        raise ValueError(f"non-integer downsample: {(ny, nx)} -> {target_resolution}")
    fy, fx = ny // target_resolution, nx // target_resolution
    return arr.reshape(target_resolution, fy, target_resolution, fx, 9).mean(axis=(1, 3))


def _norms(diff: np.ndarray) -> dict[str, float]:
    values = np.asarray(diff, dtype=np.float64)
    return {
        "l1": float(np.mean(np.abs(values))),
        "l2": float(np.sqrt(np.mean(values * values))),
        "linf": float(np.max(np.abs(values))),
    }


def density_pair_norms(coarse: np.ndarray, fine: np.ndarray) -> dict[str, float]:
    coarse_arr = np.asarray(coarse)
    reference = block_average_mhd(fine, coarse_arr.shape[0])
    if coarse_arr.shape != reference.shape:
        raise ValueError("coarse and downsampled fine arrays must match")
    return _norms(coarse_arr[..., 0] - reference[..., 0])


def same_grid_density_norms(candidate: np.ndarray, reference: np.ndarray) -> dict[str, float]:
    cand = np.asarray(candidate)
    ref = np.asarray(reference)
    if cand.shape != ref.shape:
        raise ValueError("same-grid arrays must match")
    return _norms(cand[..., 0] - ref[..., 0])


def observed_order(coarse_error: float, fine_error: float) -> float:
    coarse = float(coarse_error)
    fine = float(fine_error)
    if not math.isfinite(coarse) or not math.isfinite(fine) or coarse <= 0.0 or fine <= 0.0:
        return math.nan
    return math.log2(coarse / fine)


def _finite_positive_run(row: dict[str, Any]) -> bool:
    expected_precision = 4 if row.get("precision") == "float" else 8
    return (
        row.get("status") == "completed"
        and bool(row.get("physical_state"))
        and int(row.get("output_precision_bytes", -1)) == expected_precision
        and int(row.get("steps", 0)) > 0
        and math.isfinite(float(row.get("divB_mean", math.nan)))
        and math.isfinite(float(row.get("divB_max", math.nan)))
        and math.isfinite(float(row.get("wall_time_s", math.nan)))
        and float(row.get("wall_time_s", 0.0)) > 0.0
    )


def stored_completed_result_is_valid(summary: dict[str, Any]) -> bool:
    """Validate the repaired 24-success/eight-complete-group evidence state."""
    rows = summary.get("runs", [])
    expected = {
        (r["case"], r["solver"], r["precision"], r["resolution"])
        for r in plan_rows()
    }
    present = {
        (r.get("case"), r.get("solver"), r.get("precision"), r.get("resolution"))
        for r in rows
    }
    groups = summary.get("groups", [])
    complete_groups_valid = all(
        group.get("status") != "complete"
        or all(
            math.isfinite(float(group.get(metric, math.nan)))
            and float(group.get(metric, 0.0)) > 0.0
            for metric in (
                "rho_l1_128_256",
                "rho_l1_256_512",
                "observed_order_l1",
            )
        )
        for group in groups
    )
    precision_pair_cells = sum(
        row.get("precision") == "double"
        and row.get("rho_linf_fp32_vs_fp64") is not None
        and math.isfinite(float(row["rho_linf_fp32_vs_fp64"]))
        for row in rows
    )
    return (
        present == expected
        and len(rows) == len(expected)
        and sum(
            _finite_positive_run(row)
            and row.get("cfl") == CFL_BY_SOLVER.get(str(row.get("solver")))
            for row in rows
        ) == 24
        and not summary.get("gate", {}).get("failed_runs")
        and len(groups) == len(CASES) * len(SOLVERS) * len(PRECISIONS)
        and sum(group.get("status") == "complete" for group in groups) == 8
        and complete_groups_valid
        and precision_pair_cells == 12
        and summary.get("gate", {}).get("precision_pair_metrics_complete") is True
        and summary.get("gate", {}).get("pass") is True
    )


def assemble_summary(rows: list[dict[str, Any]], groups: list[dict[str, Any]], commit: str) -> dict[str, Any]:
    expected = {(r["case"], r["solver"], r["precision"], r["resolution"]) for r in plan_rows()}
    present = {(r.get("case"), r.get("solver"), r.get("precision"), r.get("resolution")) for r in rows}
    expected_groups = len(CASES) * len(SOLVERS) * len(PRECISIONS)
    complete = expected == present and len(rows) == len(expected) and all(_finite_positive_run(row) for row in rows)
    group_metrics = all(
        math.isfinite(float(group.get(metric, math.nan))) and float(group.get(metric, 0.0)) > 0.0
        for group in groups
        for metric in ("rho_l1_128_256", "rho_l1_256_512")
    ) if len(groups) == expected_groups else False
    orders = [float(group["observed_order_l1"]) for group in groups if math.isfinite(float(group.get("observed_order_l1", math.nan)))]
    failed_runs = [
        {
            "case": row.get("case"),
            "solver": row.get("solver"),
            "precision": row.get("precision"),
            "resolution": row.get("resolution"),
            "cfl": row.get("cfl"),
            "failure_category": row.get("failure_category"),
            "failure_message": row.get("failure_message"),
        }
        for row in rows
        if row.get("status") != "completed"
    ]
    complete_groups = sum(group.get("status") == "complete" for group in groups)
    return {
        "schema": {"name": "hrsc.week18-resolution-ladder", "version": 1},
        "experiment": EXPERIMENT,
        "git_commit": commit,
        "matrix": {"cases": list(CASES), "solvers": list(SOLVERS), "precisions": list(PRECISIONS), "resolutions": list(RESOLUTIONS), "cfl_by_solver": CFL_BY_SOLVER, "expected_runs": len(expected)},
        "gate": {
            "pass": complete and group_metrics,
            "complete_run_matrix": complete,
            "complete_group_metrics": group_metrics,
            "missing_runs": [list(key) for key in sorted(expected - present)],
            "failed_runs": failed_runs,
            "complete_groups": complete_groups,
            "expected_groups": expected_groups,
        },
        "claims": {
            "self_convergence_diagnostic": True,
            "complete_group_diagnostics": complete_groups,
            "positive_order_required": False,
            "positive_order_groups": sum(order > 0.0 for order in orders),
            "evaluated_order_groups": len(orders),
            "asymptotic_convergence": False,
            "claim_boundary": "Three resolutions expose the direction of self-convergence, but do not by themselves prove an asymptotic convergence regime for discontinuous MHD solutions.",
        },
        "groups": groups,
        "runs": rows,
    }


def _cfg_value(text: str, key: str, default: float) -> float:
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if "=" in line:
            lhs, rhs = (part.strip() for part in line.split("=", 1))
            if lhs == key:
                return float(rhs)
    return default


def _generated_config(base: str, resolution: int, solver: str, cfl: float, output: pathlib.Path) -> str:
    text = base
    for key, value in (
        ("nx", resolution), ("ny", resolution), ("riemann", solver), ("cfl", cfl),
        ("device", "cpu"), ("output_format", "binary"), ("output_file", str(output)),
    ):
        text = replace_or_append_cfg(text, key, str(value))
    return text


def _physical_state(arr: np.ndarray, gamma: float) -> dict[str, Any]:
    finite = bool(np.isfinite(arr).all())
    if not finite:
        return {"finite": False, "physical_state": False, "rho_min": None, "pressure_min": None}
    fields = mhd_primitive_fields(arr, gamma)
    rho_min = float(np.min(fields["rho"]))
    pressure_min = float(np.min(fields["p"]))
    return {"finite": True, "physical_state": rho_min > 0.0 and pressure_min > 0.0, "rho_min": rho_min, "pressure_min": pressure_min}


def _repair_artifact_tuple_failure(metadata: dict[str, Any], grid: pathlib.Path) -> bool:
    """Revalidate outputs affected by the former single-artifact tuple bug."""
    failure = metadata.get("failure") or {}
    completion = metadata.get("completion") or {}
    if not (
        metadata.get("status") == "success"
        and completion.get("reported") is True
        and failure.get("exception_type") == "TypeError"
        and failure.get("message") == "'RequiredArtifact' object is not iterable"
        and grid.is_file()
    ):
        return False
    metadata["failure"] = None
    metadata["artifact_revalidation"] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "reason": "Revalidated after fixing the single RequiredArtifact tuple construction.",
        "primary_output": str(grid),
        "primary_output_sha256": sha256_file(grid),
        "fresh_for_recorded_run": grid.stat().st_mtime >= pathlib.Path(metadata["run_config"]).stat().st_mtime,
    }
    return True


def _run_one(spec: dict[str, Any], out: pathlib.Path, commit: str) -> tuple[dict[str, Any], np.ndarray | None, pathlib.Path]:
    case = str(spec["case"])
    solver = str(spec["solver"])
    precision = str(spec["precision"])
    resolution = int(spec["resolution"])
    cfl = float(spec["cfl"])
    source_cfg = CASE_CONFIGS[case]
    base_text = source_cfg.read_text(encoding="utf-8")
    gamma = _cfg_value(base_text, "gamma", 5.0 / 3.0)
    binary = resolve_binary(BINARIES[precision])
    cfl_suffix = "" if cfl == 0.4 else f"-cfl{cfl:g}".replace(".", "p")
    run_id = f"{case}-{solver}-{precision}-n{resolution}{cfl_suffix}"
    run_dir = out / "runs" / run_id
    grid = run_dir / "grid.bin"
    cfg_text = _generated_config(base_text, resolution, solver, cfl, grid.resolve())
    metadata_path = run_dir / "metadata.json"
    metadata = None
    if metadata_path.is_file():
        candidate = json.loads(metadata_path.read_text(encoding="utf-8"))
        if (
            candidate.get("run_config_text") == cfg_text
            and candidate.get("binary_sha256") == sha256_file(binary)
        ):
            if candidate.get("status") == "success" and grid.is_file():
                if _repair_artifact_tuple_failure(candidate, grid):
                    metadata_path.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
                metadata = candidate
                print(f"[resolution-ladder] reuse {run_id}", flush=True)
            elif candidate.get("status") == "failed":
                metadata = candidate
                print(f"[resolution-ladder] retain documented failure {run_id}", flush=True)
    if metadata is None:
        try:
            _, metadata, _ = run_case(
                run_id, cfg_text, run_dir, binary, source_cfg, commit, sha256_file(binary),
                output_bin=grid.resolve(), experiment=EXPERIMENT,
            )
        except RuntimeError:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    diagnostics = metadata.get("stderr_diagnostics", {})
    common = {
        **spec,
        "gamma": gamma,
        "steps": int(diagnostics.get("steps", 0)),
        "divB_mean": float(diagnostics.get("divB_mean", math.nan)),
        "divB_max": float(diagnostics.get("divB_max", math.nan)),
        "wall_time_s": float(metadata["elapsed_wall_s"]),
        "binary": str(binary.relative_to(ROOT)),
        "binary_sha256": sha256_file(binary),
        "run_dir": str(run_dir.relative_to(ROOT)).replace("\\", "/"),
    }
    if metadata.get("status") != "success" or not grid.is_file():
        failure = metadata.get("failure") or {}
        return {
            **common,
            "status": "failed",
            "failure_category": failure.get("category", "unknown"),
            "failure_message": failure.get("message", ""),
            "output_precision_bytes": None,
            "finite": False,
            "physical_state": False,
            "rho_min": None,
            "pressure_min": None,
        }, None, grid
    header, arr_view = read_binary(grid)
    arr = np.array(arr_view, dtype=np.float64, copy=True)
    state = _physical_state(arr, gamma)
    row = {
        **common,
        "status": "completed",
        "failure_category": "",
        "failure_message": "",
        "output_precision_bytes": int(header.precision_tag),
        **state,
    }
    return row, arr, grid


def _group_metrics(arrays: dict[tuple[str, str, str, int], np.ndarray]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for case in CASES:
        for solver in SOLVERS:
            for precision in PRECISIONS:
                available = sorted(resolution for resolution in RESOLUTIONS if (case, solver, precision, resolution) in arrays)
                group: dict[str, Any] = {
                    "case": case,
                    "solver": solver,
                    "precision": precision,
                    "available_resolutions": available,
                    "status": "complete" if available == list(RESOLUTIONS) else "incomplete",
                }
                if 128 in available and 256 in available:
                    e1 = density_pair_norms(arrays[(case, solver, precision, 128)], arrays[(case, solver, precision, 256)])
                    group.update({f"rho_{name}_128_256": value for name, value in e1.items()})
                if 256 in available and 512 in available:
                    e2 = density_pair_norms(arrays[(case, solver, precision, 256)], arrays[(case, solver, precision, 512)])
                    group.update({f"rho_{name}_256_512": value for name, value in e2.items()})
                for name in ("l1", "l2", "linf"):
                    group[f"observed_order_{name}"] = observed_order(
                        group.get(f"rho_{name}_128_256", math.nan),
                        group.get(f"rho_{name}_256_512", math.nan),
                    )
                groups.append(group)
    return groups

def _attach_precision_separation(rows: list[dict[str, Any]], arrays: dict[tuple[str, str, str, int], np.ndarray]) -> None:
    indexed = {(row["case"], row["solver"], row["precision"], row["resolution"]): row for row in rows}
    for case in CASES:
        for solver in SOLVERS:
            for resolution in RESOLUTIONS:
                float_key = (case, solver, "float", resolution)
                double_key = (case, solver, "double", resolution)
                if float_key not in arrays or double_key not in arrays:
                    continue
                norms = same_grid_density_norms(arrays[float_key], arrays[double_key])
                for precision in PRECISIONS:
                    row = indexed[(case, solver, precision, resolution)]
                    for name, value in norms.items():
                        row[f"rho_{name}_fp32_vs_fp64"] = value


def _json_safe(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: _json_safe(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [_json_safe(value) for value in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def _write_outputs(summary: dict[str, Any], out: pathlib.Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    safe = _json_safe(summary)
    (out / "summary.json").write_text(json.dumps(safe, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    run_fields = list(summary["runs"][0].keys())
    with (out / "runs.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=run_fields)
        writer.writeheader(); writer.writerows(summary["runs"])
    group_fields = list(summary["groups"][0].keys())
    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=group_fields)
        writer.writeheader(); writer.writerows(summary["groups"])
    lines = [
        "# Week 18 OT/KH three-resolution diagnostic", "",
        f"Full-matrix gate pass: `{summary['gate']['pass']}`. Attempted runs: `{len(summary['runs'])}/24`; complete three-grid groups: `{summary['gate']['complete_groups']}/{summary['gate']['expected_groups']}`; same-grid fp32--fp64 cells: `{summary['gate']['precision_pair_cells_available']}/{summary['gate']['precision_pair_cells_expected']}`.", "",
        "HLL uses CFL=0.4 and HLLD uses CFL=0.2. Solver-to-solver timing or error comparisons are therefore excluded; each resolution ladder is interpreted only within a fixed solver, precision, and CFL.", "",
        "| case | solver | precision | L1 128-256 | L1 256-512 | observed p |", "|---|---|---|---:|---:|---:|",
    ]
    for group in summary["groups"]:
        e1 = group.get("rho_l1_128_256")
        e2 = group.get("rho_l1_256_512")
        order = group.get("observed_order_l1")
        lines.append(
            f"| {CASE_LABELS[group['case']]} | {group['solver'].upper()} | "
            f"{'FP64' if group['precision'] == 'double' else 'FP32'} | "
            f"{e1:.3e} | "
            f"{e2:.3e} | {order:.3f} |"
            if e1 is not None and e2 is not None and order is not None
            else f"| {CASE_LABELS[group['case']]} | {group['solver'].upper()} | "
                 f"{'FP64' if group['precision'] == 'double' else 'FP32'} | "
                 f"{e1:.3e} | -- | -- |"
        )
    lines += [
        "", "## Same-grid fp32--fp64 density separation", "",
        "These values compare matched outputs at one grid and are not discretisation errors or accuracy measures.", "",
        "| case | solver | N | mean L1 | mean L2 | Linf |", "|---|---|---:|---:|---:|---:|",
    ]
    for row in summary["runs"]:
        if row["precision"] != "double" or row.get("rho_l1_fp32_vs_fp64") is None:
            continue
        lines.append(
            f"| {CASE_LABELS[row['case']]} | {row['solver'].upper()} | {row['resolution']} | "
            f"{row['rho_l1_fp32_vs_fp64']:.3e} | {row['rho_l2_fp32_vs_fp64']:.3e} | "
            f"{row['rho_linf_fp32_vs_fp64']:.3e} |"
        )
    if summary["gate"]["failed_runs"]:
        lines += ["", "## Documented failed runs", "", "| case | solver | precision | N | CFL | category |", "|---|---|---|---:|---:|---|"]
        for failure in summary["gate"]["failed_runs"]:
            lines.append(
                f"| {CASE_LABELS[failure['case']]} | {failure['solver'].upper()} | "
                f"{'FP64' if failure['precision'] == 'double' else 'FP32'} | "
                f"{failure['resolution']} | {failure['cfl']} | `{failure['failure_category']}` |"
            )
    if summary["gate"]["failed_runs"]:
        matrix_boundary = "A failed endpoint prevents a full-matrix claim; the complete groups remain bounded subgroup diagnostics."
    else:
        matrix_boundary = "All eight groups are complete, but they remain bounded subgroup diagnostics rather than proof of an asymptotic regime."
    lines += ["", "## Claim boundary", "", summary["claims"]["claim_boundary"], "", f"Positive observed order is reported as evidence, not used as a pass/fail requirement. {matrix_boundary}", ""]
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def _plot(summary: dict[str, Any], out: pathlib.Path) -> pathlib.Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titleweight": "bold", "axes.linewidth": 0.8, "figure.dpi": 150, "savefig.dpi": 320})
    fig, axes = plt.subplots(2, 2, figsize=(11.8, 8.2), constrained_layout=True)
    colors = {("hll", "double"): "#1f4e79", ("hll", "float"): "#5b9bd5", ("hlld", "double"): "#8b1e3f", ("hlld", "float"): "#d96b7d"}
    markers = {"double": "o", "float": "s"}
    for ax, case, panel in zip(axes[0], CASES, ("a", "b")):
        for group in [g for g in summary["groups"] if g["case"] == case and g["status"] == "complete"]:
            key = (group["solver"], group["precision"])
            ax.plot([192, 384], [group["rho_l1_128_256"], group["rho_l1_256_512"]], color=colors[key], marker=markers[group["precision"]], linewidth=1.8, markersize=5.5, label=f"{group['solver'].upper()} / {'FP64' if group['precision']=='double' else 'FP32'}")
        ax.set_yscale("log"); ax.set_xticks([192, 384], ["128 vs 256", "256 vs 512"])
        ax.set_ylabel(r"Mean $L_1$ density difference"); ax.set_title(f"({panel}) {CASE_LABELS[case]}: adjacent-grid difference", loc="left")
        ax.grid(True, which="both", color="#d7dce2", linewidth=0.6, alpha=0.8)
        ax.legend(frameon=False, ncols=2, fontsize=8)
    ax = axes[1, 0]
    groups = [group for group in summary["groups"] if group["status"] == "complete"]
    labels = [f"{'OT' if g['case']==CASES[0] else 'KH'}\n{g['solver'].upper()}\n{'64' if g['precision']=='double' else '32'}" for g in groups]
    values = [g["observed_order_l1"] for g in groups]
    bar_colors = [colors[(g["solver"], g["precision"])] for g in groups]
    ax.bar(np.arange(len(groups)), values, color=bar_colors, width=0.72)
    ax.axhline(0.0, color="#30343b", linewidth=0.9); ax.axhline(1.0, color="#70757d", linestyle="--", linewidth=0.9, label="p = 1 reference")
    ax.set_xticks(np.arange(len(groups)), labels); ax.set_ylabel(r"Observed $p=\log_2(E_{128,256}/E_{256,512})$")
    ax.set_title("(c) Observed self-convergence order", loc="left"); ax.grid(True, axis="y", color="#d7dce2", linewidth=0.6); ax.legend(frameon=False)
    ax = axes[1, 1]
    rows = summary["runs"]
    for case in CASES:
        for solver in SOLVERS:
            selected = sorted([r for r in rows if r["case"] == case and r["solver"] == solver and r["precision"] == "float" and r.get("rho_linf_fp32_vs_fp64") is not None], key=lambda r: r["resolution"])
            ax.plot([r["resolution"] for r in selected], [r["rho_linf_fp32_vs_fp64"] for r in selected], marker="o" if solver == "hll" else "s", linewidth=1.8, label=f"{'OT' if case==CASES[0] else 'KH'} / {solver.upper()}")
    ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xticks(RESOLUTIONS, [str(n) for n in RESOLUTIONS]); ax.set_xlabel("Grid resolution N x N"); ax.set_ylabel(r"$L_\infty(\rho_{FP32}-\rho_{FP64})$")
    ax.set_title("(d) Precision separation with refinement", loc="left"); ax.grid(True, which="both", color="#d7dce2", linewidth=0.6); ax.legend(frameon=False, ncols=2, fontsize=8)
    fig.suptitle("MHD resolution ladder: self-convergence and precision separation", fontsize=14, fontweight="bold")
    fig.text(0.5, 0.005, "Three-grid diagnostic; positive order is descriptive and does not establish an asymptotic regime.", ha="center", fontsize=8, color="#4d535b")
    figure_dir = out / "figures"; figure_dir.mkdir(parents=True, exist_ok=True)
    target = figure_dir / "resolution_ladder.png"; fig.savefig(target, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return target


def run(out: pathlib.Path, keep_grids: bool = False) -> dict[str, Any]:
    commit = git_commit(); rows: list[dict[str, Any]] = []; arrays: dict[tuple[str, str, str, int], np.ndarray] = {}; grids: list[pathlib.Path] = []
    for spec in plan_rows():
        print(f"[resolution-ladder] {spec['case']} {spec['solver']} {spec['precision']} N={spec['resolution']} CFL={spec['cfl']}", flush=True)
        row, arr, grid = _run_one(spec, out, commit)
        rows.append(row)
        if arr is not None:
            arrays[(spec["case"], spec["solver"], spec["precision"], spec["resolution"])] = arr
        grids.append(grid)
    groups = _group_metrics(arrays); _attach_precision_separation(rows, arrays)
    summary = assemble_summary(rows, groups, commit); _write_outputs(summary, out); figure = _plot(summary, out)
    if not keep_grids:
        for grid in grids:
            if grid.name != "grid.bin":
                raise ValueError(f"refusing to remove non-grid artifact: {grid}")
            grid.unlink(missing_ok=True)
    print(f"summary: {out / 'summary.json'}"); print(f"figure: {figure}"); print(f"gate_pass: {summary['gate']['pass']}")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT); parser.add_argument("--keep-grids", action="store_true")
    args = parser.parse_args(argv); summary = run(args.out.resolve(), args.keep_grids); return 0 if summary["gate"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
