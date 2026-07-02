import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "regression"))
sys.path.insert(0, str(ROOT))

from scripts.build_matrix import BuildVariant
import mhd_precision_pilot as drv


def _cell(rho, vx, By, p, gamma):
    E = p / (gamma - 1.0) + 0.5 * rho * vx * vx + 0.5 * By * By
    return [rho, rho * vx, 0.0, 0.0, 0.0, By, 0.0, E, 0.0]


def test_p0_filter_picks_eight():
    from scripts.build_matrix import generate_variants
    assert len(generate_variants(filter=drv.p0_filter)) == 8


def test_select_variants_by_phase():
    assert len(drv.select_variants("p0")) == 8
    assert len(drv.select_variants("p1")) == 24
    with pytest.raises(ValueError):
        drv.select_variants("p2")


def test_ordered_variants_reference_first():
    variants = list(reversed(drv.select_variants("p0")))
    ordered = drv.ordered_variants_reference_first(variants)
    assert ordered[0].name == drv.core.REFERENCE
    assert sorted(v.name for v in ordered) == sorted(v.name for v in variants)
    assert len({v.name for v in ordered}) == len(ordered)


def test_measure_run_reference_is_zero_delta():
    gamma = 5.0 / 3.0
    ref = np.array([[_cell(1.0, 0.1, 0.2, 1.0, gamma)]], dtype=np.float64)
    v = BuildVariant("double", "O2", False, False)
    row = drv.measure_run(v, ref, ref, gamma, dx=0.5,
                          diagnostics={"steps": 759, "divB_max": 4.441e-14},
                          walltime_s=0.02)
    assert row["variant"] == "cpu-double-O2-ieee-leq"
    assert row["is_reference"] is True
    assert row["Linf_rho"] == 0.0
    assert row["steps"] == 759 and row["finite"] is True
    assert row["rc"] == 0 and row["walltime_s"] == 0.02


def test_measure_run_uses_shared_field_norms(monkeypatch):
    gamma = 5.0 / 3.0
    ref = np.array([[_cell(1.0, 0.1, 0.2, 1.0, gamma)]], dtype=np.float64)
    sentinel = {
        "L1_rho": 11.0, "L2_rho": 12.0, "Linf_rho": 13.0,
        "L1_By": 21.0, "L2_By": 22.0, "Linf_By": 23.0,
        "L1_p": 31.0, "L2_p": 32.0, "Linf_p": 33.0,
        "L1_vx": 41.0, "L2_vx": 42.0, "Linf_vx": 43.0,
    }
    calls = []

    def fake_field_norms(arr, ref_arr, got_gamma, dx):
        calls.append((arr, ref_arr, got_gamma, dx))
        return sentinel

    monkeypatch.setattr(drv, "field_norms", fake_field_norms)
    row = drv.measure_run(
        BuildVariant("float", "Ofast", False, True),
        ref,
        ref,
        gamma,
        dx=0.25,
        diagnostics={"steps": 759, "divB_max": 4.441e-14},
        walltime_s=0.02,
    )

    assert calls and calls[0][2:] == (gamma, 0.25)
    for key, value in sentinel.items():
        assert row[key] == value


def test_write_matrix_json(tmp_path):
    from scripts.build_matrix import generate_variants
    variants = generate_variants(filter=drv.p0_filter)
    path = drv.write_matrix_json(variants, tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["experiment"] == "week14-mhd-precision-pilot"
    assert len(data["runs"]) == 8
    assert all(r["config"].endswith("brio_wu.cfg") for r in data["runs"])
    expected_binary = "hrsc_mhd.exe" if sys.platform.startswith("win") else "hrsc_mhd"
    assert all(Path(r["binary"]).name == expected_binary for r in data["runs"])


def test_measure_run_nonfinite_array_returns_failing_row():
    gamma = 5.0 / 3.0
    ref = np.array([[_cell(1.0, 0.1, 0.2, 1.0, gamma)]], dtype=np.float64)
    candidate = ref.copy()
    candidate[0, 0, 0] = np.nan

    row = drv.measure_run(
        BuildVariant("float", "O2", False, False),
        candidate,
        ref,
        gamma,
        dx=0.5,
        diagnostics={"steps": 759, "divB_max": 4.441e-14},
        walltime_s=0.02,
    )

    assert row["finite"] is False
    assert row["rc"] == 0
    for field in ("rho", "By", "p", "vx"):
        for norm in ("L1", "L2", "Linf"):
            value = row[f"{norm}_{field}"]
            assert isinstance(value, float)
            assert math.isfinite(value)
    mca = {
        "p53": drv.core.blocked_mca_block("blocked_environment", "test"),
        "p24": drv.core.blocked_mca_block("blocked_environment", "test"),
    }
    assert drv.core.schema_valid([row], mca) is True


def test_measure_run_nonfinite_reference_returns_failing_row():
    gamma = 5.0 / 3.0
    candidate = np.array([[_cell(1.0, 0.1, 0.2, 1.0, gamma)]], dtype=np.float64)
    ref = candidate.copy()
    ref[0, 0, 0] = np.nan

    row = drv.measure_run(
        BuildVariant("float", "O2", False, False),
        candidate,
        ref,
        gamma,
        dx=0.5,
        diagnostics={"steps": 759, "divB_max": 4.441e-14},
        walltime_s=0.02,
    )

    assert row["finite"] is False
    for field in ("rho", "By", "p", "vx"):
        for norm in ("L1", "L2", "Linf"):
            assert math.isfinite(row[f"{norm}_{field}"])
    mca = {
        "p53": drv.core.blocked_mca_block("blocked_environment", "test"),
        "p24": drv.core.blocked_mca_block("blocked_environment", "test"),
    }
    assert drv.core.schema_valid([row], mca) is True
