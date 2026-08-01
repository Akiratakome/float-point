import math

from scripts.regression import mhd_week18_kh_timing as timing


def test_plan_has_twenty_measured_runs():
    rows = timing.plan_rows(5)
    assert len(rows) == 20
    assert {row["solver"] for row in rows} == {"hll", "hlld"}
    assert {row["precision"] for row in rows} == {"double", "float"}
    assert {row["repeat"] for row in rows} == {1, 2, 3, 4, 5}


def test_median_iqr_uses_robust_statistics():
    median, iqr = timing.median_iqr([1.0, 2.0, 3.0, 4.0, 100.0])
    assert median == 3.0
    assert iqr == 2.0


def test_aggregate_reports_precision_speedup_and_solver_cost():
    rows = []
    values = {
        ("hll", "double"): [10, 10, 10, 10, 10],
        ("hll", "float"): [5, 5, 5, 5, 5],
        ("hlld", "double"): [15, 15, 15, 15, 15],
        ("hlld", "float"): [10, 10, 10, 10, 10],
    }
    for (solver, precision), times in values.items():
        for repeat, elapsed in enumerate(times, 1):
            rows.append({"solver": solver, "precision": precision, "repeat": repeat, "status": "completed", "physical_state": True, "elapsed_wall_s": elapsed, "ulp_vs_repeat1": 0})
    summary = timing.aggregate(rows, {"hll": 1e-6, "hlld": 2e-6}, "deadbeef", 5)
    assert summary["gate"]["pass"] is True
    assert summary["comparisons"]["fp32_speedup"]["hll"] == 2.0
    assert summary["comparisons"]["hlld_over_hll_cost"]["double"] == 1.5
    assert math.isclose(summary["comparisons"]["hlld_over_hll_cost"]["float"], 2.0)