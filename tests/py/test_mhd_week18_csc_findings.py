import copy

from scripts.regression import mhd_week18_csc_findings as findings


BASE = {
    "mca": {
        "p24": {
            "status": "completed", "n": 4,
            "spread_rho": 1.0e-7, "spread_vx": 2.0e-7,
            "spread_By": 3.0e-8, "spread_p": 4.0e-7,
            "snr_rho": 1.0e7, "snr_By": 1.0e4, "snr_p": 2.0e7,
        },
        "p53": {
            "status": "completed", "n": 4,
            "spread_rho": 1.0e-15, "spread_vx": 2.0e-15,
            "spread_By": 3.0e-16, "spread_p": 4.0e-15,
            "snr_rho": 1.0e15, "snr_By": 1.0e12, "snr_p": 2.0e15,
        },
    }
}


def test_derive_metrics_reports_decades_and_solver_ratio():
    hll = copy.deepcopy(BASE)
    hlld = copy.deepcopy(BASE)
    for precision in ("p24", "p53"):
        for field in findings.FIELDS:
            hlld["mca"][precision][f"spread_{field}"] *= 3.0
    derived = findings.derive_csc_metrics({"hll": hll, "hlld": hlld})
    assert derived["gate"]["pass"] is True
    assert derived["precision_amplification"]["hll"]["rho"]["decades"] == 8.0
    assert derived["solver_ratio_p24"]["rho"] == 3.0
    assert derived["claims"]["full_resolution_mca_completed"] is False


def test_gate_rejects_incomplete_precision_block():
    payload = {"hll": copy.deepcopy(BASE), "hlld": copy.deepcopy(BASE)}
    payload["hlld"]["mca"]["p24"]["status"] = "blocked"
    assert findings.derive_csc_metrics(payload)["gate"]["pass"] is False


def test_local_plan_is_exact_four_run_matrix():
    plan = findings.local_plan()
    assert len(plan) == 4
    assert {row["solver"] for row in plan} == {"hll", "hlld"}
    assert {row["precision"] for row in plan} == {"double", "float"}