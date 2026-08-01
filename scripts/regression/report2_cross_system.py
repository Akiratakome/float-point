#!/usr/bin/env python3
"""Aggregate a bounded Euler--MHD precision/math-mode comparison."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pathlib
import sys
from typing import Any

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_ROOT = ROOT / "experiments" / "week18" / "euler_mhd_cross_system"
sys.path.insert(0, str(ROOT / "scripts"))
from io_helper import read_binary  # noqa: E402

CASES = {
    "sod": {"label": "Sod", "system": "Euler", "dimension": "1D", "solver": "HLLC", "shape": [1, 200, 4], "t_end": 0.25},
    "lw3": {"label": "LW3", "system": "Euler", "dimension": "2D", "solver": "HLLC", "shape": [200, 200, 4], "t_end": 0.3},
    "brio-wu": {"label": "Brio-Wu", "system": "ideal MHD", "dimension": "1D", "solver": "HLL", "shape": [1, 800, 9], "t_end": 0.1},
    "orszag-tang": {"label": "Orszag-Tang", "system": "ideal MHD", "dimension": "2D", "solver": "HLL", "shape": [128, 128, 9], "t_end": 0.5},
}
VARIANTS = ("double-o2", "float-o2", "double-fast", "float-fast")
COMPARISONS = {
    "precision_o2": ("float-o2", "double-o2", "FP32 vs FP64 / O2-default"),
    "precision_fast": ("float-fast", "double-fast", "FP32 vs FP64 / Ofast-fast"),
    "math_fp64": ("double-fast", "double-o2", "Ofast-fast vs O2-default / FP64"),
    "math_fp32": ("float-fast", "float-o2", "Ofast-fast vs O2-default / FP32"),
}


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def density_norms(candidate: np.ndarray, reference: np.ndarray) -> dict[str, float]:
    cand = np.asarray(candidate, dtype=np.float64)
    ref = np.asarray(reference, dtype=np.float64)
    if cand.shape != ref.shape:
        raise ValueError(f"shape mismatch: {cand.shape} != {ref.shape}")
    diff = cand[..., 0] - ref[..., 0]
    scale = float(np.mean(np.abs(ref[..., 0])))
    if not math.isfinite(scale) or scale <= 0.0:
        raise ValueError("density normalization scale must be finite and positive")
    return {
        "rho_l1": float(np.mean(np.abs(diff))),
        "rho_l2": float(np.sqrt(np.mean(diff * diff))),
        "rho_linf": float(np.max(np.abs(diff))),
        "rho_l1_relative": float(np.mean(np.abs(diff)) / scale),
    }


def expected_run_ids() -> list[str]:
    return [f"{case}-{variant}" for case in CASES for variant in VARIANTS]


def run_row_is_valid(row: dict[str, Any]) -> bool:
    run_id = str(row.get("run_id", ""))
    matched = next(
        (
            (case, variant)
            for case in CASES
            for variant in VARIANTS
            if run_id == f"{case}-{variant}"
        ),
        None,
    )
    if matched is None:
        return False
    case, variant = matched
    expected_precision = "float" if variant.startswith("float-") else "double"
    expected_tag = 4 if expected_precision == "float" else 8
    expected_mode = "fast" if variant.endswith("-fast") else "compiler-default"
    final_time = float(row.get("final_time", math.nan))
    t_end = float(CASES[case]["t_end"])
    time_ok = math.isfinite(final_time) and abs(final_time - t_end) <= max(
        1e-7, 1e-6 * t_end
    )
    return (
        row.get("status") == "success"
        and row.get("completion_reported") is True
        and row.get("precision") == expected_precision
        and int(row.get("precision_tag", -1)) == expected_tag
        and int(row.get("expected_precision_tag", -1)) == expected_tag
        and row.get("shape") == CASES[case]["shape"]
        and row.get("effective_math_mode") == expected_mode
        and time_ok
    )


def stored_summary_is_valid(summary: dict[str, Any]) -> bool:
    runs = summary.get("runs", [])
    comparisons = summary.get("comparisons", [])
    expected_comparisons = [
        (case, comparison) for case in CASES for comparison in COMPARISONS
    ]
    comparison_plan_ok = [
        (row.get("case"), row.get("comparison")) for row in comparisons
    ] == expected_comparisons and all(
        row.get("comparison") in COMPARISONS
        and row.get("candidate") == COMPARISONS[row["comparison"]][0]
        and row.get("reference") == COMPARISONS[row["comparison"]][1]
        for row in comparisons
    )
    return (
        [row.get("run_id") for row in runs] == expected_run_ids()
        and all(run_row_is_valid(row) for row in runs)
        and len(comparisons) == len(CASES) * len(COMPARISONS)
        and comparison_plan_ok
        and all(
            math.isfinite(float(row.get(key, math.nan)))
            and float(row.get(key, -1.0)) >= 0.0
            for row in comparisons
            for key in ("rho_l1", "rho_l2", "rho_linf", "rho_l1_relative")
        )
        and summary.get("gate", {}).get("pass") is True
    )


def load_runs(root: pathlib.Path) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    arrays: dict[str, np.ndarray] = {}
    rows: list[dict[str, Any]] = []
    for run_id in expected_run_ids():
        run_dir = root / "runs" / run_id
        metadata_path = run_dir / "metadata.json"
        grid_path = run_dir / "grid.bin"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        header, view = read_binary(grid_path)
        precision = "float" if "-float-" in run_id else "double"
        expected_tag = 4 if precision == "float" else 8
        binary = ROOT / pathlib.Path(metadata["binary"])
        row = {
            "run_id": run_id,
            "status": metadata.get("status"),
            "completion_reported": bool((metadata.get("completion") or {}).get("reported")),
            "precision": precision,
            "precision_tag": int(header.precision_tag),
            "expected_precision_tag": expected_tag,
            "shape": [int(header.ny), int(header.nx), int(header.nvars)],
            "final_time": float(header.t),
            "binary": str(binary.relative_to(ROOT)).replace("\\", "/"),
            "binary_sha256": sha256_file(binary),
            "config_sha256": sha256_file(run_dir / "config.cfg"),
            "effective_math_mode": (metadata.get("build_semantics") or {}).get("effective_math_mode"),
        }
        rows.append(row)
        arrays[run_id] = np.array(view, dtype=np.float64, copy=True)
    return arrays, rows


def assemble(root: pathlib.Path) -> dict[str, Any]:
    arrays, runs = load_runs(root)
    comparisons: list[dict[str, Any]] = []
    for case, case_meta in CASES.items():
        for comparison, (candidate_variant, reference_variant, label) in COMPARISONS.items():
            metrics = density_norms(arrays[f"{case}-{candidate_variant}"], arrays[f"{case}-{reference_variant}"])
            comparisons.append({
                "case": case,
                **case_meta,
                "comparison": comparison,
                "comparison_label": label,
                "candidate": candidate_variant,
                "reference": reference_variant,
                **metrics,
            })
    run_gate = (
        [row["run_id"] for row in runs] == expected_run_ids()
        and all(run_row_is_valid(row) for row in runs)
    )
    metric_gate = len(comparisons) == len(CASES) * len(COMPARISONS) and all(
        math.isfinite(float(row[key])) and float(row[key]) >= 0.0
        for row in comparisons
        for key in ("rho_l1", "rho_l2", "rho_linf", "rho_l1_relative")
    )
    return {
        "schema": {"name": "hrsc.week18-cross-system", "version": 1},
        "experiment": "week18-euler-mhd-cross-system",
        "matrix": {
            "systems": ["Euler", "ideal MHD"],
            "dimensions": ["1D", "2D"],
            "cases": list(CASES),
            "precisions": ["FP64", "FP32"],
            "math_modes": ["O2-default", "Ofast-fast"],
            "device": "CPU",
            "branch_rule": "<=",
            "expected_runs": len(expected_run_ids()),
        },
        "gate": {"pass": run_gate and metric_gate, "runs": run_gate, "metrics": metric_gate},
        "claim_boundary": "This packet compares bounded density-discrepancy sensitivity across selected Euler/HLLC and ideal-MHD/HLL cases. Different physical systems and Riemann solvers prevent a universal method ranking, and no cross-system accuracy claim is made.",
        "runs": runs,
        "comparisons": comparisons,
    }


def write_outputs(summary: dict[str, Any], root: pathlib.Path) -> None:
    (root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    fields = list(summary["comparisons"][0])
    with (root / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary["comparisons"])
    lines = [
        "# Week 18 Euler--MHD cross-system sensitivity", "",
        f"Gate pass: `{summary['gate']['pass']}`. Completed runs: `{len(summary['runs'])}/{summary['matrix']['expected_runs']}`.", "",
        "| system | dimension | case | comparison | relative L1(rho) | Linf(rho) |", "|---|---|---|---|---:|---:|",
    ]
    for row in summary["comparisons"]:
        lines.append(f"| {row['system']} | {row['dimension']} | {row['label']} | {row['comparison_label']} | {row['rho_l1_relative']:.3e} | {row['rho_linf']:.3e} |")
    lines += ["", "## Claim boundary", "", summary["claim_boundary"], ""]
    (root / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def plot(summary: dict[str, Any], root: pathlib.Path) -> pathlib.Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = [CASES[case]["label"] for case in CASES]
    x = np.arange(len(labels))
    width = 0.34
    precision = [next(row["rho_l1_relative"] for row in summary["comparisons"] if row["case"] == case and row["comparison"] == "precision_o2") for case in CASES]
    math_mode = [next(row["rho_l1_relative"] for row in summary["comparisons"] if row["case"] == case and row["comparison"] == "math_fp32") for case in CASES]
    positive = [value for value in precision + math_mode if value > 0.0]
    floor = min(positive) / 3.0
    plotted_math = [value if value > 0.0 else floor for value in math_mode]
    fig, ax = plt.subplots(figsize=(9.2, 5.2), constrained_layout=True)
    ax.bar(x - width / 2, precision, width, label="FP32 vs FP64 / O2-default", color="#2f6da1")
    bars = ax.bar(x + width / 2, plotted_math, width, label="Ofast-fast vs O2-default / FP32", color="#d55e00")
    for index, value in enumerate(math_mode):
        if value == 0.0:
            bars[index].set_facecolor("white")
            bars[index].set_edgecolor("#d55e00")
            bars[index].set_hatch("///")
            ax.annotate("0 (bit-identical)", (x[index] + width / 2, floor),
                        xytext=(0, 5), textcoords="offset points", ha="center",
                        va="bottom", fontsize=8, color="#d55e00")
    ax.set_yscale("log")
    ax.set_xticks(x, [f"{labels[i]}\n{CASES[case]['system']}, {CASES[case]['dimension']}" for i, case in enumerate(CASES)])
    ax.set_ylabel("Relative L1 density discrepancy")
    ax.set_title("Within-case precision and math-mode sensitivity")
    ax.grid(True, axis="y", which="both", linewidth=0.6, alpha=0.45)
    ax.legend(frameon=False)
    ax.text(0.5, -0.2, "Within-case discrepancies; bars are not cross-system accuracy errors.", transform=ax.transAxes, ha="center", fontsize=8)
    target_dir = root / "figures"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "cross_system_sensitivity.png"
    fig.savefig(target, dpi=320, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return target


def remove_grids(root: pathlib.Path) -> None:
    for run_id in expected_run_ids():
        grid = root / "runs" / run_id / "grid.bin"
        if grid.name != "grid.bin" or root not in grid.parents:
            raise ValueError(f"refusing to remove unexpected path: {grid}")
        grid.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, default=DEFAULT_ROOT)
    parser.add_argument("--keep-grids", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    summary = assemble(root)
    write_outputs(summary, root)
    figure = plot(summary, root)
    if not args.keep_grids:
        remove_grids(root)
    print(f"summary: {root / 'summary.json'}")
    print(f"figure: {figure}")
    print(f"gate_pass: {summary['gate']['pass']}")
    return 0 if summary["gate"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
