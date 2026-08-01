import math

import numpy as np

from scripts.regression import mhd_brio_build_semantics as build_semantics


def test_plan_covers_solvers_precisions_and_four_variants():
    rows = build_semantics.plan_rows()
    assert len(rows) == 16
    assert {row["solver"] for row in rows} == {"hll", "hlld"}
    assert {row["precision"] for row in rows} == {"double", "float"}
    assert {row["variant"] for row in rows} == {"o2", "ox", "fast", "strict"}


def test_density_norms_are_direct_same_grid_metrics():
    reference = np.zeros((1, 2, 9), dtype=np.float64)
    reference[..., 0] = [1.0, 3.0]
    candidate = reference.copy(); candidate[..., 0] += [1.0, -1.0]
    norms = build_semantics.density_norms(candidate, reference)
    assert norms["rho_l1_mean"] == 1.0
    assert norms["rho_l2_mean"] == 1.0
    assert norms["rho_linf"] == 1.0
    assert norms["rho_l1_relative"] == 0.5


def test_aggregate_requires_complete_matched_matrix():
    arrays = {}
    rows = []
    for item in build_semantics.plan_rows():
        key = (item["solver"], item["precision"], item["variant"])
        arr = np.ones((1, 2, 9), dtype=np.float64)
        if item["variant"] == "fast":
            arr[..., 0] += 1e-6
        arrays[key] = arr
        rows.append({**item, "status": "completed", "physical_state": True, "steps": 10, "final_time": 0.1})
    builds = [{} for _ in range(8)]
    summary = build_semantics.aggregate(rows, arrays, "deadbeef", builds)
    assert summary["gate"]["pass"] is True
    assert len(summary["comparisons"]) == 12
    assert math.isclose(
        max(row["rho_linf"] for row in summary["comparisons"] if row["axis"] == "fast_math"),
        1e-6,
    )
