import numpy as np
import json

from scripts.regression import report2_cross_system as cross


def test_expected_matrix_covers_two_systems_and_dimensions():
    assert len(cross.expected_run_ids()) == 16
    assert {meta["system"] for meta in cross.CASES.values()} == {"Euler", "ideal MHD"}
    assert {meta["dimension"] for meta in cross.CASES.values()} == {"1D", "2D"}


def test_density_norms_are_relative_to_reference_scale():
    reference = np.zeros((1, 2, 4), dtype=np.float64)
    candidate = np.zeros_like(reference)
    reference[..., 0] = 2.0
    candidate[..., 0] = 3.0
    result = cross.density_norms(candidate, reference)
    assert result == {"rho_l1": 1.0, "rho_l2": 1.0, "rho_linf": 1.0, "rho_l1_relative": 0.5}


def test_comparison_plan_separates_precision_and_math_mode():
    assert set(cross.COMPARISONS) == {"precision_o2", "precision_fast", "math_fp64", "math_fp32"}
    assert cross.COMPARISONS["precision_o2"][:2] == ("float-o2", "double-o2")
    assert cross.COMPARISONS["math_fp64"][:2] == ("double-fast", "double-o2")


def test_committed_cross_system_summary_passes_strict_contract():
    path = cross.DEFAULT_ROOT / "summary.json"
    summary = json.loads(path.read_text(encoding="utf-8"))
    assert cross.stored_summary_is_valid(summary)


def test_run_contract_rejects_wrong_math_mode():
    case = "sod"
    row = {
        "run_id": "sod-float-o2",
        "status": "success",
        "completion_reported": True,
        "precision": "float",
        "precision_tag": 4,
        "expected_precision_tag": 4,
        "shape": cross.CASES[case]["shape"],
        "final_time": cross.CASES[case]["t_end"],
        "effective_math_mode": "fast",
    }
    assert not cross.run_row_is_valid(row)
