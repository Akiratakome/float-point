import math
import json

import numpy as np

from scripts.regression import mhd_week18_resolution_ladder as ladder


def test_plan_covers_full_resolution_ladder():
    rows = ladder.plan_rows()
    assert len(rows) == 24
    assert {row["case"] for row in rows} == {"orszag_tang_2d", "kelvin_helmholtz_2d"}
    assert {row["solver"] for row in rows} == {"hll", "hlld"}
    assert {row["precision"] for row in rows} == {"double", "float"}
    assert {row["resolution"] for row in rows} == {128, 256, 512}


def test_block_average_mhd_preserves_constant_state():
    fine = np.ones((4, 4, 9), dtype=np.float64)
    fine[..., 0] = 2.5
    coarse = ladder.block_average_mhd(fine, 2)
    assert coarse.shape == (2, 2, 9)
    np.testing.assert_allclose(coarse[..., 0], 2.5)
    np.testing.assert_allclose(coarse[..., 1:], 1.0)


def test_density_pair_norms_are_mean_based():
    coarse = np.zeros((2, 2, 9), dtype=np.float64)
    fine = np.zeros((4, 4, 9), dtype=np.float64)
    coarse[..., 0] = 2.0
    fine[..., 0] = 1.0
    norms = ladder.density_pair_norms(coarse, fine)
    assert norms == {"l1": 1.0, "l2": 1.0, "linf": 1.0}


def test_observed_order_handles_regular_and_degenerate_errors():
    assert ladder.observed_order(0.04, 0.01) == 2.0
    assert math.isnan(ladder.observed_order(0.0, 0.01))
    assert math.isnan(ladder.observed_order(0.01, 0.0))


def test_summary_requires_complete_matrix_but_not_positive_order():
    rows = []
    for planned in ladder.plan_rows():
        rows.append(
            {
                **planned,
                "status": "completed",
                "physical_state": True,
                "output_precision_bytes": 4 if planned["precision"] == "float" else 8,
                "steps": 10,
                "divB_mean": 0.0,
                "divB_max": 0.0,
                "wall_time_s": 1.0,
            }
        )

    groups = []
    for case in ladder.CASES:
        for solver in ladder.SOLVERS:
            for precision in ladder.PRECISIONS:
                groups.append(
                    {
                        "case": case,
                        "solver": solver,
                        "precision": precision,
                        "rho_l1_128_256": 0.02,
                        "rho_l1_256_512": 0.03,
                        "observed_order_l1": math.log2(0.02 / 0.03),
                    }
                )

    summary = ladder.assemble_summary(rows, groups, "deadbeef")
    assert summary["gate"]["pass"] is True
    assert summary["claims"]["self_convergence_diagnostic"] is True
    assert summary["claims"]["positive_order_required"] is False
    assert summary["claims"]["asymptotic_convergence"] is False


def test_committed_resolution_result_has_all_expected_completions():
    path = ladder.DEFAULT_OUT / "summary.json"
    summary = json.loads(path.read_text(encoding="utf-8"))
    assert ladder.stored_completed_result_is_valid(summary)
    assert summary["gate"]["precision_pair_metrics_complete"] is True
    assert summary["gate"]["precision_pair_cells_available"] == 12
    report = (ladder.DEFAULT_OUT / "summary.md").read_text(encoding="utf-8")
    assert "same-grid fp32--fp64 cells: `12/12`" in report
    assert "Same-grid fp32--fp64 density separation" in report
