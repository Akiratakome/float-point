#!/usr/bin/env python3
"""Week 18 MHD robustness experiments for the Report 2 evidence packet."""

from __future__ import annotations

import pathlib
import sys
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]

for path in (ROOT, ROOT / "scripts", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(path))

from _mhd_harness import replace_or_append_cfg  # noqa: E402


CASES_2D = ("orszag_tang_2d", "kelvin_helmholtz_2d")
PRECISIONS = ("double", "float")


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
            all_completed = all_completed and bool(cpu.get("completed")) and bool(
                gpu.get("completed")
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
    completed = bool(rows) and all(bool(row.get("completed")) for row in rows)
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
