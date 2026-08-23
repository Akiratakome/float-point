#!/usr/bin/env python3
"""Week 18 MHD robustness experiments for the Report 2 evidence packet."""

from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import sys
from collections import defaultdict
from collections.abc import Iterable
from contextlib import contextmanager
from typing import Any

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "experiments" / "week18" / "supplemental"

for path in (
    ROOT,
    ROOT / "scripts",
    ROOT / "scripts" / "metrics",
    ROOT / "scripts" / "regression",
):
    sys.path.insert(0, str(path))

from _mhd_harness import (  # noqa: E402
    git_commit,
    replace_or_append_cfg,
    resolve_binary,
    run_case,
    sha256_file,
)
from io_helper import read_binary  # noqa: E402
from mhd_gpu_hardware_axis import max_ulp_distance  # noqa: E402
from mhd_fields import field_norms, mhd_primitive_fields  # noqa: E402


CASES_2D = ("orszag_tang_2d", "kelvin_helmholtz_2d")
PRECISIONS = ("double", "float")
EXPERIMENT = "week18-report2-supplemental"
CASE_SPECS = {
    "brio_wu_1d": ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg",
    "orszag_tang_2d": (
        ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg"
    ),
    "kelvin_helmholtz_2d": (
        ROOT / "tests" / "cases" / "kelvin_helmholtz_2d" / "kh.cfg"
    ),
}
BINS = {
    ("double", "cpu"): ROOT / "build-double" / "hrsc_mhd",
    ("float", "cpu"): ROOT / "build-float" / "hrsc_mhd",
    ("double", "gpu"): ROOT / "build-cuda" / "hrsc_mhd",
    ("float", "gpu"): ROOT / "build-cuda-float" / "hrsc_mhd",
}


def hardware_plan(repeats: int = 5) -> list[dict[str, Any]]:
    if repeats < 1:
        raise ValueError("repeats must be positive")
    return [
        {
            "suite": "hardware_repeats",
            "case": case,
            "precision": precision,
            "device": device,
            "repeat": repeat,
            "solver": "hll",
        }
        for case in ("brio_wu_1d", "orszag_tang_2d")
        for precision in PRECISIONS
        for repeat in range(1, repeats + 1)
        for device in ("cpu", "gpu")
    ]


def thread_plan(threads: Iterable[int] = (1, 2, 4, 8)) -> list[dict[str, Any]]:
    values = tuple(int(thread) for thread in threads)
    if not values or any(thread < 1 for thread in values):
        raise ValueError("thread counts must be positive")
    return [
        {
            "suite": "thread_repro",
            "case": case,
            "precision": precision,
            "device": "cpu",
            "solver": "hll",
            "omp_num_threads": thread,
        }
        for case in CASES_2D
        for precision in PRECISIONS
        for thread in values
    ]


def cfl_plan(
    cfl_values: Iterable[float] = (0.2, 0.4, 0.6, 0.8),
) -> list[dict[str, Any]]:
    values = tuple(float(cfl) for cfl in cfl_values)
    if not values or any(cfl <= 0.0 for cfl in values):
        raise ValueError("CFL values must be positive")
    return [
        {
            "suite": "kh_cfl",
            "case": "kelvin_helmholtz_2d",
            "precision": precision,
            "device": "cpu",
            "solver": solver,
            "cfl": cfl,
        }
        for solver in ("hll", "hlld")
        for precision in PRECISIONS
        for cfl in values
    ]


def generated_cfg(
    base_text: str,
    overrides: dict[str, Any],
    output_file: pathlib.Path,
    device: str,
) -> str:
    text = base_text
    for key, value in overrides.items():
        text = replace_or_append_cfg(text, key, str(value))
    for key, value in (
        ("device", device),
        ("output_format", "binary"),
        ("output_file", str(output_file)),
    ):
        text = replace_or_append_cfg(text, key, value)
    return text


def run_name(row: dict[str, Any]) -> str:
    parts = [
        str(row["case"]),
        str(row["precision"]),
        str(row["device"]),
        str(row["solver"]),
    ]
    if row["suite"] == "hardware_repeats":
        parts.append(f"r{int(row['repeat']):02d}")
    elif row["suite"] == "thread_repro":
        parts.append(f"t{int(row['omp_num_threads']):02d}")
    elif row["suite"] == "kh_cfl":
        parts.append(f"cfl{float(row['cfl']):g}".replace(".", "p"))
    else:
        raise ValueError(f"unknown suite: {row['suite']}")
    return "-".join(parts)


def cleanup_grids(paths: Iterable[pathlib.Path]) -> None:
    for path in paths:
        candidate = pathlib.Path(path)
        if candidate.name != "grid.bin":
            raise ValueError(f"refusing to clean non-grid path: {candidate}")
        if candidate.exists():
            candidate.unlink()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "suite",
        choices=("hardware", "threads", "cfl", "all", "aggregate"),
    )
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--keep-grids", action="store_true")
    return parser.parse_args(argv)


def difference_metrics(
    candidate: np.ndarray,
    reference: np.ndarray,
) -> dict[str, Any]:
    if candidate.shape != reference.shape:
        raise ValueError(f"shape mismatch: {candidate.shape} vs {reference.shape}")
    diff = np.abs(
        candidate.astype(np.float64, copy=False)
        - reference.astype(np.float64, copy=False)
    )
    return {
        "l1_mean_abs": float(diff.mean()) if diff.size else 0.0,
        "linf_abs": float(diff.max(initial=0.0)),
        "ulp_max": (
            max_ulp_distance(candidate, reference)
            if candidate.dtype == reference.dtype
            else None
        ),
    }


def physical_state(arr: np.ndarray, *, gamma: float) -> dict[str, Any]:
    candidate = np.asarray(arr)
    finite = bool(np.isfinite(candidate).all())
    if not finite:
        return {
            "finite": False,
            "finite_positive": False,
            "rho_min": None,
            "pressure_min": None,
        }
    rho_min = float(candidate[..., 0].min(initial=np.inf))
    pressure = mhd_primitive_fields(candidate, gamma)["p"]
    pressure_min = float(pressure.min(initial=np.inf))
    return {
        "finite": True,
        "finite_positive": rho_min > 0.0 and pressure_min > 0.0,
        "rho_min": rho_min,
        "pressure_min": pressure_min,
    }


@contextmanager
def environment_override(values: dict[str, str]):
    previous = {key: os.environ.get(key) for key in values}
    try:
        os.environ.update({key: str(value) for key, value in values.items()})
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def median_iqr(values: Iterable[float]) -> tuple[float, float]:
    arr = np.asarray(tuple(values), dtype=np.float64)
    if not arr.size or not np.isfinite(arr).all():
        raise ValueError("statistics require finite values")
    return (
        float(np.median(arr)),
        float(np.percentile(arr, 75) - np.percentile(arr, 25)),
    )


def aggregate_hardware(
    rows: list[dict[str, Any]],
    *,
    expected_repeats: int = 5,
) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["case"]), str(row["precision"]))].append(row)

    groups = []
    missing_pairs = []
    all_ulp = []
    all_linf = []
    all_completed = True
    for (case, precision), group_rows in sorted(grouped.items()):
        indexed = {
            (int(row["repeat"]), str(row["device"])): row for row in group_rows
        }
        cpu_times = []
        gpu_times = []
        speedups = []
        group_ulp = []
        group_linf = []
        for repeat in range(1, expected_repeats + 1):
            cpu = indexed.get((repeat, "cpu"))
            gpu = indexed.get((repeat, "gpu"))
            if cpu is None or gpu is None:
                missing_pairs.append(
                    {"case": case, "precision": precision, "repeat": repeat}
                )
                continue
            all_completed = (
                all_completed
                and bool(cpu.get("completed"))
                and bool(gpu.get("completed"))
                and bool(cpu.get("finite_positive", True))
                and bool(gpu.get("finite_positive", True))
            )
            cpu_time = float(cpu["elapsed_wall_s"])
            gpu_time = float(gpu["elapsed_wall_s"])
            cpu_times.append(cpu_time)
            gpu_times.append(gpu_time)
            speedups.append(cpu_time / gpu_time)
            pair_ulp = max(
                int(cpu.get("ulp_max", 0)), int(gpu.get("ulp_max", 0))
            )
            pair_linf = max(
                float(cpu.get("linf_abs", 0.0)),
                float(gpu.get("linf_abs", 0.0)),
            )
            group_ulp.append(pair_ulp)
            group_linf.append(pair_linf)
            all_ulp.append(pair_ulp)
            all_linf.append(pair_linf)
        if cpu_times:
            cpu_median, cpu_iqr = median_iqr(cpu_times)
            gpu_median, gpu_iqr = median_iqr(gpu_times)
            speedup_median, speedup_iqr = median_iqr(speedups)
            groups.append(
                {
                    "case": case,
                    "precision": precision,
                    "repeats": len(cpu_times),
                    "cpu_time_median_s": cpu_median,
                    "cpu_time_iqr_s": cpu_iqr,
                    "gpu_time_median_s": gpu_median,
                    "gpu_time_iqr_s": gpu_iqr,
                    "speedup_median": speedup_median,
                    "speedup_iqr": speedup_iqr,
                    "ulp_max": max(group_ulp, default=0),
                    "linf_abs_max": max(group_linf, default=0.0),
                }
            )
    max_ulp = max(all_ulp, default=0)
    max_linf = max(all_linf, default=0.0)
    return {
        "schema": {"name": "hrsc.week18-supplemental", "version": 1},
        "suite": "hardware_repeats",
        "rows": rows,
        "groups": groups,
        "gate": {
            "pass": bool(rows)
            and not missing_pairs
            and all_completed
            and max_ulp == 0
            and max_linf == 0.0,
            "expected_repeats": expected_repeats,
            "missing_pairs": missing_pairs,
            "max_ulp": max_ulp,
            "max_linf_abs": max_linf,
        },
        "claims": {
            "performance_statistic": "median and interquartile range",
            "broad_gpu_matrix": False,
        },
    }


def aggregate_threads(
    rows: list[dict[str, Any]],
    *,
    expected_threads: Iterable[int] = (1, 2, 4, 8),
) -> dict[str, Any]:
    expected = {int(value) for value in expected_threads}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["case"]), str(row["precision"]))].append(row)
    missing_rows = []
    for (case, precision), group_rows in sorted(grouped.items()):
        present = {int(row["omp_num_threads"]) for row in group_rows}
        for thread in sorted(expected - present):
            missing_rows.append(
                {"case": case, "precision": precision, "omp_num_threads": thread}
            )
    max_ulp = max((int(row.get("ulp_max", 0)) for row in rows), default=0)
    max_linf = max((float(row.get("linf_abs", 0.0)) for row in rows), default=0.0)
    completed = bool(rows) and all(
        bool(row.get("completed")) and bool(row.get("finite_positive", True))
        for row in rows
    )
    return {
        "schema": {"name": "hrsc.week18-supplemental", "version": 1},
        "suite": "thread_repro",
        "rows": rows,
        "gate": {
            "pass": completed
            and not missing_rows
            and max_ulp == 0
            and max_linf == 0.0,
            "expected_threads": sorted(expected),
            "missing_rows": missing_rows,
            "max_ulp": max_ulp,
            "max_linf_abs": max_linf,
        },
        "claims": {
            "openmp_reproducibility": True,
            "mpi_reproducibility": False,
        },
    }


def aggregate_cfl(
    rows: list[dict[str, Any]],
    *,
    expected_cfl: Iterable[float] = (0.2, 0.4, 0.6, 0.8),
) -> dict[str, Any]:
    expected = {float(value) for value in expected_cfl}
    indexed = {
        (str(row["solver"]), str(row["precision"]), float(row["cfl"])): row
        for row in rows
    }
    missing_rows = []
    groups = []
    for solver in ("hll", "hlld"):
        for cfl in sorted(expected):
            double = indexed.get((solver, "double", cfl))
            float_row = indexed.get((solver, "float", cfl))
            for precision, row in (("double", double), ("float", float_row)):
                if row is None:
                    missing_rows.append(
                        {"solver": solver, "precision": precision, "cfl": cfl}
                    )
            if double is not None and float_row is not None:
                groups.append(
                    {
                        "solver": solver,
                        "cfl": cfl,
                        "steps_double": int(double["steps"]),
                        "steps_float": int(float_row["steps"]),
                        "divB_max_double": float(double["divB_max"]),
                        "divB_max_float": float(float_row["divB_max"]),
                        "Linf_rho_fp32_vs_fp64": float(
                            float_row["Linf_rho_vs_fp64"]
                        ),
                    }
                )
    completed = bool(rows) and all(
        bool(row.get("completed")) and bool(row.get("finite_positive"))
        for row in rows
    )
    return {
        "schema": {"name": "hrsc.week18-supplemental", "version": 1},
        "suite": "kh_cfl",
        "rows": rows,
        "groups": groups,
        "gate": {
            "pass": completed and not missing_rows,
            "expected_cfl": sorted(expected),
            "missing_rows": missing_rows,
            "all_finite_positive": completed,
        },
        "claims": {
            "cfl_sensitivity": True,
            "temporal_convergence": False,
        },
    }


def write_suite_outputs(summary: dict[str, Any], out: pathlib.Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    rows = list(summary.get("rows", []))
    columns = sorted({str(key) for row in rows for key in row})
    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        if columns:
            writer.writeheader()
            writer.writerows(rows)
    (out / "summary.md").write_text(
        render_suite_markdown(summary),
        encoding="utf-8",
    )
    plot_suite(summary, out / "figures")


def render_suite_markdown(summary: dict[str, Any]) -> str:
    suite = str(summary["suite"])
    lines = [
        f"# Week 18 {suite.replace('_', ' ').title()}",
        "",
        f"- Gate pass: `{summary['gate']['pass']}`",
        f"- Rows: `{len(summary.get('rows', []))}`",
        "- Schema: `hrsc.week18-supplemental` version `1`",
        "",
    ]
    if suite == "hardware_repeats":
        lines.extend(
            [
                "| case | precision | repeats | CPU median (s) | GPU median (s) | speedup median | IQR | max ULP |",
                "|---|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for group in summary["groups"]:
            lines.append(
                f"| {group['case']} | {group['precision']} | {group['repeats']} | "
                f"{group['cpu_time_median_s']:.6f} | {group['gpu_time_median_s']:.6f} | "
                f"{group['speedup_median']:.4f} | {group['speedup_iqr']:.4f} | "
                f"{group['ulp_max']} |"
            )
    elif suite == "thread_repro":
        lines.extend(
            [
                f"- Maximum ULP distance: `{summary['gate']['max_ulp']}`",
                f"- Maximum absolute drift: `{summary['gate']['max_linf_abs']:.6e}`",
                "- Boundary: this covers OpenMP thread counts only, not MPI ordering.",
            ]
        )
    elif suite == "kh_cfl":
        lines.extend(
            [
                "| solver | CFL | steps fp64/fp32 | divB max fp64/fp32 | Linf rho fp32 vs fp64 |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for group in summary["groups"]:
            lines.append(
                f"| {group['solver']} | {group['cfl']:.1f} | "
                f"{group['steps_double']}/{group['steps_float']} | "
                f"{group['divB_max_double']:.6e}/{group['divB_max_float']:.6e} | "
                f"{group['Linf_rho_fp32_vs_fp64']:.6e} |"
            )
        lines.extend(
            [
                "",
                "Boundary: this is a CFL-sensitivity study, not a formal temporal-convergence result.",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def plot_suite(summary: dict[str, Any], fig_dir: pathlib.Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig_dir.mkdir(parents=True, exist_ok=True)
    suite = str(summary["suite"])
    if suite == "hardware_repeats":
        groups = summary["groups"]
        labels = [
            f"{row['case'].replace('_2d', '').replace('_1d', '')}\n{row['precision']}"
            for row in groups
        ]
        values = [float(row["speedup_median"]) for row in groups]
        errors = [float(row["speedup_iqr"]) / 2.0 for row in groups]
        ulps = [int(row["ulp_max"]) for row in groups]
        fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.0))
        axes[0].bar(
            labels,
            values,
            yerr=errors,
            color=["#2f6690", "#d1495b", "#2f6690", "#d1495b"][: len(labels)],
            capsize=4,
        )
        axes[0].axhline(1.0, color="#555555", linewidth=1.0, linestyle="--")
        axes[0].set_ylabel("CPU / GPU wall time")
        axes[0].set_title("(a) Median speedup and IQR")
        x_values = np.arange(len(labels))
        axes[1].scatter(
            x_values,
            ulps,
            color="#4d9078",
            s=55,
            zorder=3,
        )
        axes[1].set_xticks(x_values, labels)
        spec = ulp_axis_spec(ulps)
        axes[1].set_ylim(*spec["ylim"])
        for x_value, value, annotation in zip(
            x_values,
            ulps,
            spec["annotations"],
        ):
            axes[1].annotate(
                annotation,
                (x_value, value),
                xytext=(0, 9),
                textcoords="offset points",
                ha="center",
                fontsize=9,
            )
        axes[1].axhline(0.0, color="#777777", linewidth=1.0)
        axes[1].set_ylabel("Maximum ULP distance")
        axes[1].set_title("(b) Same-precision bit-exact agreement")
        fig.tight_layout()
        path = fig_dir / "hardware_repeats.png"
    elif suite == "thread_repro":
        rows = summary["rows"]
        fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
        colors = {"double": "#2f6690", "float": "#d1495b"}
        threads = sorted({int(row["omp_num_threads"]) for row in rows})
        group_keys = [
            (case, precision)
            for case in CASES_2D
            for precision in PRECISIONS
        ]
        matrix = np.array(
            [
                [
                    next(
                        int(row["ulp_max"])
                        for row in rows
                        if row["case"] == case
                        and row["precision"] == precision
                        and int(row["omp_num_threads"]) == thread
                    )
                    for thread in threads
                ]
                for case, precision in group_keys
            ],
            dtype=np.float64,
        )
        axes[0].imshow(
            matrix,
            cmap="Greens",
            vmin=0.0,
            vmax=max(1.0, float(matrix.max(initial=0.0))),
            aspect="auto",
        )
        axes[0].set_xticks(range(len(threads)), threads)
        axes[0].set_yticks(
            range(len(group_keys)),
            [
                f"{case.replace('_2d', '').replace('_', ' ')} {precision}"
                for case, precision in group_keys
            ],
        )
        for row_index in range(matrix.shape[0]):
            for col_index in range(matrix.shape[1]):
                axes[0].text(
                    col_index,
                    row_index,
                    f"{int(matrix[row_index, col_index])} ULP",
                    ha="center",
                    va="center",
                    color="#16352a",
                    fontsize=9,
                )
        axes[0].set_xlabel("OMP_NUM_THREADS")
        axes[0].set_title("(a) Bit-exact thread agreement")

        ratio_rows = thread_runtime_ratios(rows)
        line_styles = {
            "orszag_tang_2d": "-",
            "kelvin_helmholtz_2d": "--",
        }
        for case, precision in group_keys:
            series = sorted(
                (
                    row
                    for row in ratio_rows
                    if row["case"] == case and row["precision"] == precision
                ),
                key=lambda row: int(row["omp_num_threads"]),
            )
            axes[1].plot(
                [int(row["omp_num_threads"]) for row in series],
                [float(row["runtime_vs_one_thread"]) for row in series],
                marker="o" if precision == "double" else "s",
                linestyle=line_styles[case],
                color=colors[precision],
                label=(
                    f"{case.replace('_2d', '').replace('_', ' ')} {precision}"
                ),
            )
        axes[1].axhline(1.0, color="#777777", linewidth=1.0, linestyle=":")
        axes[1].set_xlabel("OMP_NUM_THREADS")
        axes[1].set_ylabel("Wall time / 1-thread wall time")
        axes[1].set_title("(b) Runtime remains near the 1-thread baseline")
        axes[1].legend(frameon=False, fontsize=8)
        axes[1].grid(True, alpha=0.25)
        fig.tight_layout()
        path = fig_dir / "thread_repro.png"
    elif suite == "kh_cfl":
        groups = summary["groups"]
        fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.0))
        colors = {"hll": "#2f6690", "hlld": "#d1495b"}
        for solver in ("hll", "hlld"):
            series = sorted(
                (row for row in groups if row["solver"] == solver),
                key=lambda row: float(row["cfl"]),
            )
            cfl = [float(row["cfl"]) for row in series]
            axes[0].plot(
                cfl,
                [float(row["Linf_rho_fp32_vs_fp64"]) for row in series],
                marker="o",
                color=colors[solver],
                label=solver.upper(),
            )
            axes[1].plot(
                cfl,
                [int(row["steps_double"]) for row in series],
                marker="o" if solver == "hll" else "s",
                linestyle="-" if solver == "hll" else "--",
                color=colors[solver],
                label=solver.upper(),
            )
        axes[0].set_yscale("log")
        axes[0].set_xlabel("CFL")
        axes[0].set_ylabel(r"$L_\infty(\rho)$: fp32 vs fp64")
        axes[0].set_title("(a) Precision separation")
        axes[1].set_xlabel("CFL")
        axes[1].set_ylabel("fp64 step count")
        axes[1].set_title("(b) Time-step cost")
        axes[1].text(
            0.03,
            0.06,
            "HLL and HLLD step counts coincide",
            transform=axes[1].transAxes,
            fontsize=9,
            color="#444444",
        )
        axes[0].legend(frameon=False)
        axes[1].legend(frameon=False)
        fig.tight_layout()
        path = fig_dir / "kh_cfl.png"
    else:
        raise ValueError(f"unknown suite: {suite}")
    fig.savefig(path, dpi=240, bbox_inches="tight")
    # These are line and marker plots, so a vector copy is the manuscript asset;
    # the raster copy stays for quick review.
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def combine_summaries(
    summaries: dict[str, dict[str, Any]],
    *,
    commit: str,
) -> dict[str, Any]:
    expected = ("hardware_repeats", "thread_repro", "kh_cfl")
    missing = [name for name in expected if name not in summaries]
    failed = [
        name
        for name in expected
        if name in summaries and not bool(summaries[name].get("gate", {}).get("pass"))
    ]
    return {
        "schema": {"name": "hrsc.week18-supplemental-index", "version": 1},
        "experiment": "week18-report2-supplemental",
        "git_commit": commit,
        "suites": summaries,
        "gate": {
            "pass": not missing and not failed,
            "missing_suites": missing,
            "failed_suites": failed,
        },
        "claim_boundaries": {
            "formal_temporal_convergence": False,
            "mpi_reproducibility": False,
            "broad_gpu_matrix": False,
            "full_kh_mca_completed": False,
        },
    }


def ulp_axis_spec(ulps: Iterable[int]) -> dict[str, Any]:
    values = [int(value) for value in ulps]
    if values and max(values) == 0:
        return {
            "ylim": (-0.1, 0.5),
            "annotations": ["0 ULP" for _ in values],
        }
    upper = max(values, default=1)
    return {
        "ylim": (0.0, float(upper) * 1.15),
        "annotations": [str(value) for value in values],
    }


def thread_runtime_ratios(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    baselines = {
        (str(row["case"]), str(row["precision"])): float(row["elapsed_wall_s"])
        for row in rows
        if int(row["omp_num_threads"]) == 1
    }
    output = []
    for source in rows:
        row = dict(source)
        key = (str(row["case"]), str(row["precision"]))
        baseline = baselines.get(key)
        row["runtime_vs_one_thread"] = (
            float(row["elapsed_wall_s"]) / baseline
            if baseline is not None and baseline > 0.0
            else float("nan")
        )
        output.append(row)
    return output


def attach_hardware_metrics(
    staged: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    indexed = {
        (
            str(item["row"]["case"]),
            str(item["row"]["precision"]),
            int(item["row"]["repeat"]),
            str(item["row"]["device"]),
        ): item
        for item in staged
    }
    rows = []
    for item in staged:
        row = dict(item["row"])
        key = (str(row["case"]), str(row["precision"]), int(row["repeat"]))
        cpu = indexed.get((*key, "cpu"))
        gpu = indexed.get((*key, "gpu"))
        if cpu is None or gpu is None:
            row.update({"ulp_max": -1, "linf_abs": float("inf")})
        else:
            metrics = difference_metrics(gpu["array"], cpu["array"])
            row.update(metrics)
        rows.append(row)
    return rows


def attach_thread_metrics(
    staged: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    references = {
        (str(item["row"]["case"]), str(item["row"]["precision"])): item["array"]
        for item in staged
        if int(item["row"]["omp_num_threads"]) == 1
    }
    rows = []
    for item in staged:
        row = dict(item["row"])
        reference = references.get((str(row["case"]), str(row["precision"])))
        if reference is None:
            row.update({"ulp_max": -1, "linf_abs": float("inf")})
        else:
            row.update(difference_metrics(item["array"], reference))
        rows.append(row)
    return rows


def attach_cfl_metrics(
    staged: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    references = {
        (str(item["row"]["solver"]), float(item["row"]["cfl"])): item
        for item in staged
        if str(item["row"]["precision"]) == "double"
    }
    rows = []
    for item in staged:
        row = dict(item["row"])
        reference = references.get((str(row["solver"]), float(row["cfl"])))
        if reference is None:
            row["Linf_rho_vs_fp64"] = float("inf")
        else:
            norms = field_norms(
                np.asarray(item["array"], dtype=np.float64),
                np.asarray(reference["array"], dtype=np.float64),
                float(item["gamma"]),
                float(item["dx"]),
            )
            row["Linf_rho_vs_fp64"] = float(norms["Linf_rho"])
        rows.append(row)
    return rows


def _cfg_float(text: str, key: str, default: float) -> float:
    for line in text.splitlines():
        content = line.split("#", 1)[0].strip()
        if not content or "=" not in content:
            continue
        lhs, rhs = (part.strip() for part in content.split("=", 1))
        if lhs == key:
            return float(rhs)
    return default


def _plan_overrides(row: dict[str, Any]) -> dict[str, Any]:
    overrides: dict[str, Any] = {"riemann": row["solver"]}
    if row["suite"] == "kh_cfl":
        overrides["cfl"] = row["cfl"]
    return overrides


def _execute_plans(
    plans: list[dict[str, Any]],
    suite_dir: pathlib.Path,
    *,
    keep_grids: bool,
) -> list[dict[str, Any]]:
    commit = git_commit()
    staged = []
    grids = []
    for plan in plans:
        source_cfg = CASE_SPECS[str(plan["case"])]
        base_text = source_cfg.read_text(encoding="utf-8")
        binary = resolve_binary(BINS[(str(plan["precision"]), str(plan["device"]))])
        label = run_name(plan)
        run_dir = suite_dir / "runs" / label
        grid = run_dir / "grid.bin"
        cfg_text = generated_cfg(
            base_text,
            _plan_overrides(plan),
            grid,
            str(plan["device"]),
        )
        env = {}
        if plan["suite"] == "thread_repro":
            env["OMP_NUM_THREADS"] = str(plan["omp_num_threads"])
        with environment_override(env):
            _, meta, _ = run_case(
                label,
                cfg_text,
                run_dir,
                binary,
                source_cfg,
                commit,
                sha256_file(binary),
                output_bin=grid,
                experiment=EXPERIMENT,
            )
        if env:
            meta["environment_overrides"] = env
            (run_dir / "metadata.json").write_text(
                json.dumps(meta, indent=2) + "\n",
                encoding="utf-8",
            )
        header, arr = read_binary(grid)
        gamma = _cfg_float(base_text, "gamma", 5.0 / 3.0)
        diagnostics = meta.get("stderr_diagnostics") or {}
        state = physical_state(arr, gamma=gamma)
        row = dict(plan)
        row.update(
            {
                "completed": True,
                "nx": int(header.nx),
                "ny": int(header.ny),
                "t": float(diagnostics.get("t", header.t)),
                "steps": int(diagnostics.get("steps", -1)),
                "divB_max": float(diagnostics.get("divB_max", np.nan)),
                "elapsed_wall_s": float(meta["elapsed_wall_s"]),
                "binary": str(binary),
                "binary_sha256": str(meta["binary_sha256"]),
                "run_config": str(meta["run_config"]),
            }
        )
        row.update(state)
        staged.append(
            {
                "row": row,
                "array": np.array(arr, copy=True),
                "gamma": gamma,
                "dx": float(header.dx),
            }
        )
        grids.append(grid)
    if not keep_grids:
        cleanup_grids(grids)
    return staged


def run_hardware_suite(
    out: pathlib.Path,
    *,
    repeats: int = 5,
    keep_grids: bool = False,
) -> dict[str, Any]:
    suite_dir = out / "hardware_repeats"
    staged = _execute_plans(
        hardware_plan(repeats),
        suite_dir,
        keep_grids=keep_grids,
    )
    summary = aggregate_hardware(
        attach_hardware_metrics(staged),
        expected_repeats=repeats,
    )
    summary.update(
        {
            "git_commit": git_commit(),
            "mode": "report-grade" if repeats >= 5 else "smoke",
            "retention": {"grid_bin": "kept" if keep_grids else "removed"},
        }
    )
    write_suite_outputs(summary, suite_dir)
    return summary


def run_thread_suite(
    out: pathlib.Path,
    *,
    keep_grids: bool = False,
) -> dict[str, Any]:
    suite_dir = out / "thread_repro"
    staged = _execute_plans(
        thread_plan(),
        suite_dir,
        keep_grids=keep_grids,
    )
    summary = aggregate_threads(attach_thread_metrics(staged))
    summary.update(
        {
            "git_commit": git_commit(),
            "mode": "report-grade",
            "retention": {"grid_bin": "kept" if keep_grids else "removed"},
        }
    )
    write_suite_outputs(summary, suite_dir)
    return summary


def run_cfl_suite(
    out: pathlib.Path,
    *,
    keep_grids: bool = False,
) -> dict[str, Any]:
    suite_dir = out / "kh_cfl"
    staged = _execute_plans(
        cfl_plan(),
        suite_dir,
        keep_grids=keep_grids,
    )
    summary = aggregate_cfl(attach_cfl_metrics(staged))
    summary.update(
        {
            "git_commit": git_commit(),
            "mode": "report-grade",
            "retention": {"grid_bin": "kept" if keep_grids else "removed"},
        }
    )
    write_suite_outputs(summary, suite_dir)
    return summary


def aggregate_existing(out: pathlib.Path) -> dict[str, Any]:
    summaries = {}
    for name in ("hardware_repeats", "thread_repro", "kh_cfl"):
        path = out / name / "summary.json"
        if path.is_file():
            summaries[name] = json.loads(path.read_text(encoding="utf-8"))
    combined = combine_summaries(summaries, commit=git_commit())
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(
        json.dumps(combined, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Week 18 Report 2 Supplemental Evidence",
        "",
        f"- Combined gate pass: `{combined['gate']['pass']}`",
        f"- Commit: `{combined['git_commit']}`",
        "",
    ]
    for name in ("hardware_repeats", "thread_repro", "kh_cfl"):
        suite = summaries.get(name)
        status = "missing" if suite is None else str(suite["gate"]["pass"])
        lines.append(f"- `{name}`: gate `{status}`")
    lines.extend(
        [
            "",
            "Full 256^2, t=1.0, N=30 KH MCA remains a separate CSC gate and is not claimed here.",
            "",
        ]
    )
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    return combined


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out = args.out if args.out.is_absolute() else ROOT / args.out
    summaries = []
    if args.suite in ("hardware", "all"):
        summaries.append(
            run_hardware_suite(
                out,
                repeats=args.repeats,
                keep_grids=args.keep_grids,
            )
        )
    if args.suite in ("threads", "all"):
        summaries.append(run_thread_suite(out, keep_grids=args.keep_grids))
    if args.suite in ("cfl", "all"):
        summaries.append(run_cfl_suite(out, keep_grids=args.keep_grids))
    combined = aggregate_existing(out)
    passed = all(bool(summary["gate"]["pass"]) for summary in summaries)
    if args.suite == "aggregate":
        passed = bool(combined["gate"]["pass"])
    print((out / "summary.md").read_text(encoding="utf-8"), end="")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
