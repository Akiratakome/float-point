import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "regression"))
sys.path.insert(0, str(ROOT))

from mhd_precision_pilot_core import REFERENCE
import mhd_orszag_tang_precision_smoke as ot


def _cell(rho, vx, By, p, gamma):
    energy = p / (gamma - 1.0) + 0.5 * rho * vx * vx + 0.5 * By * By
    return [rho, rho * vx, 0.0, 0.0, 0.0, By, 0.0, energy, 0.0]


def _grid(gamma):
    return np.array(
        [
            [_cell(1.0, 0.1, 0.2, 1.0, gamma), _cell(1.2, -0.1, -0.2, 1.1, gamma)],
            [_cell(0.9, 0.2, 0.4, 0.8, gamma), _cell(1.1, -0.2, -0.4, 0.9, gamma)],
        ],
        dtype=np.float64,
    )


def _row(*, solver="hll", profile="gate", steps=None, divb=None, finite=True, variant=REFERENCE):
    anchor_steps, anchor_divb = ot.OT_ANCHORS[(solver, profile)]
    if steps is None:
        steps = anchor_steps
    if divb is None:
        divb = anchor_divb
    return {
        "variant": variant,
        "precision": "double",
        "opt": "O2",
        "fastmath": False,
        "riemann": "leq",
        "solver": solver,
        "profile": profile,
        "case": ot.CASE.name,
        "finite": finite,
        "rc": 0,
        "steps": steps,
        "divB_mean": divb / 10.0,
        "divB_max": divb,
        "walltime_s": np.float64(0.25),
        "dx": np.float64(1.0 / 128.0),
        "dy": np.float64(1.0 / 128.0),
        "symmetry_residual_rho": np.float64(0.0),
        "is_reference": variant == REFERENCE,
        "L1_rho": np.float64(0.0),
        "L2_rho": np.float64(0.0),
        "Linf_rho": np.float64(0.0),
        "L1_By": np.float64(0.0),
        "L2_By": np.float64(0.0),
        "Linf_By": np.float64(0.0),
        "L1_p": np.float64(0.0),
        "L2_p": np.float64(0.0),
        "Linf_p": np.float64(0.0),
        "L1_vx": np.float64(0.0),
        "L2_vx": np.float64(0.0),
        "Linf_vx": np.float64(0.0),
    }


def test_default_plan_uses_eight_p0_variants_reference_first_and_stamps_profile():
    rows = ot.deterministic_plan()

    assert len(rows) == 8
    assert rows[0]["variant"] == "cpu-double-O2-ieee-leq"
    assert rows[0]["variant"] == REFERENCE
    assert all(row["solver"] == "hll" for row in rows)
    assert all(row["profile"] == "gate" for row in rows)
    assert all(row["case"] == ot.CASE.name for row in rows)
    assert all(row["subdir"] == "gate128" and row["nx"] == 128 for row in rows)

    headline = ot.plan_row(rows[0]["build_variant"], "hlld", "headline")
    assert headline["solver"] == "hlld"
    assert headline["profile"] == "headline"
    assert headline["subdir"] == "headline256"
    assert headline["nx"] == 256
    assert headline["ny"] == 256
    assert headline["t_end"] == 0.5

    with pytest.raises(ValueError):
        ot.deterministic_plan(solver="roe")
    with pytest.raises(ValueError):
        ot.deterministic_plan(profile="preview")


def test_cfg_override_preserves_physics_and_sets_smoke_controls():
    base = """
case = orszag_tang_2d
gamma = 1.4
cfl = 0.3
nx = 64
ny = 64
t_end = 0.05
riemann = hll
output_format = text
"""

    cfg = ot.orszag_tang_cfg(base, solver="hlld", profile="headline", output_file="runs/grid.bin")

    assert "case = orszag_tang_2d" in cfg
    assert "gamma = 1.4" in cfg
    assert "cfl = 0.3" in cfg
    assert "nx = 256" in cfg
    assert "ny = 256" in cfg
    assert "t_end = 0.5" in cfg
    assert "riemann = hlld" in cfg
    assert "output_format = binary" in cfg
    assert "output_file = runs/grid.bin" in cfg
    assert ot.case_gamma(cfg) == 1.4
    assert ot.case_gamma("case = orszag_tang_2d\n") == pytest.approx(5.0 / 3.0)


def test_measure_pair_reports_core_metrics_and_symmetry_residual():
    gamma = 5.0 / 3.0
    ref = _grid(gamma)
    arr = ref.copy()
    arr[0, 0, 0] += 0.125
    arr[1, 0, 5] -= 0.5
    plan = ot.deterministic_plan()[0]

    row = ot.measure_pair(
        plan,
        arr,
        ref,
        gamma=gamma,
        dx=0.25,
        dy=0.5,
        diagnostics={"steps": 76, "divB_mean": 0.25, "divB_max": 1.173},
        walltime_s=0.01,
    )

    assert row["case"] == ot.CASE.name
    assert row["finite"] is True
    assert row["steps"] == 76
    assert row["divB_mean"] == 0.25
    assert row["divB_max"] == 1.173
    assert row["walltime_s"] == 0.01
    assert row["dx"] == 0.25 and row["dy"] == 0.5
    assert row["Linf_rho"] == pytest.approx(0.125)
    assert row["Linf_By"] == pytest.approx(0.5)
    assert math.isfinite(row["symmetry_residual_rho"])
    assert row["symmetry_residual_rho"] > 0.0


def test_measure_pair_nonfinite_norms_are_json_safe_na_values(tmp_path):
    gamma = 5.0 / 3.0
    ref = _grid(gamma)
    arr = ref.copy()
    arr[0, 0, 0] = np.nan

    row = ot.measure_pair(
        ot.deterministic_plan()[0],
        arr,
        ref,
        gamma=gamma,
        dx=0.25,
        dy=0.5,
        diagnostics={"steps": 76, "divB_mean": 0.25, "divB_max": 1.173},
        walltime_s=0.01,
    )

    assert row["finite"] is False
    for field in ("rho", "By", "p", "vx"):
        for norm in ("L1", "L2", "Linf"):
            assert row[f"{norm}_{field}"] is None

    ot.write_outputs(tmp_path, [row], solver="hll", profile="gate", git_commit="deadbeef", figures=[])
    payload = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert payload["rows"][0]["Linf_rho"] is None
    csv_row = next(csv.DictReader((tmp_path / "summary.csv").read_text(encoding="utf-8").splitlines()))
    assert csv_row["Linf_rho"] == ""


def test_measure_pair_preserves_diagnostics_return_code():
    gamma = 5.0 / 3.0
    ref = _grid(gamma)

    row = ot.measure_pair(
        ot.deterministic_plan()[0],
        ref,
        ref,
        gamma=gamma,
        dx=0.25,
        dy=0.5,
        diagnostics={"rc": 7, "steps": 76, "divB_mean": 0.25, "divB_max": 1.173},
        walltime_s=0.01,
    )

    assert row["rc"] == 7


def test_anchor_gate_checks_exact_steps_and_five_percent_divb_tolerance():
    for solver in ot.SUPPORTED_SOLVERS:
        for profile in ot.PROFILES:
            gate = ot.anchor_gate([_row(solver=solver, profile=profile)], solver, profile)
            assert gate["pass"] is True
            assert gate["steps_exact"] is True
            assert gate["divB_within_rtol"] is True

            steps, divb = ot.OT_ANCHORS[(solver, profile)]
            assert ot.anchor_gate([_row(solver=solver, profile=profile, steps=steps + 1)], solver, profile)["pass"] is False
            assert ot.anchor_gate([_row(solver=solver, profile=profile, divb=divb * 1.049)], solver, profile)["pass"] is True
            assert ot.anchor_gate([_row(solver=solver, profile=profile, divb=divb * 1.051)], solver, profile)["pass"] is False
            assert ot.anchor_gate([_row(solver=solver, profile=profile, finite=False)], solver, profile)["pass"] is False


def test_write_outputs_emits_json_csv_markdown_with_gates_and_figures(tmp_path):
    figures = ["figures/reference_fields.png", "figures/drift_fields.png"]
    written = ot.write_outputs(
        tmp_path,
        [_row(), _row(variant="cpu-float-O2-ieee-leq")],
        solver="hll",
        profile="gate",
        git_commit=np.str_("deadbeef"),
        figures=figures,
    )

    assert written["json"] == str(tmp_path / "summary.json")
    assert written["csv"] == str(tmp_path / "summary.csv")
    assert written["markdown"] == str(tmp_path / "summary.md")

    payload = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert payload["experiment"] == ot.EXPERIMENT
    assert payload["case"] == ot.CASE.name
    assert payload["solver"] == "hll"
    assert payload["profile"] == "gate"
    assert payload["git_commit"] == "deadbeef"
    assert payload["reference_variant"] == REFERENCE
    assert payload["gates"]["G0"]["pass"] is True
    assert payload["figures"] == figures
    assert isinstance(payload["rows"][0]["walltime_s"], float)

    csv_rows = list(csv.DictReader((tmp_path / "summary.csv").read_text(encoding="utf-8").splitlines()))
    assert [row["variant"] for row in csv_rows] == [REFERENCE, "cpu-float-O2-ieee-leq"]

    md = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "# Orszag-Tang Precision Smoke Summary" in md
    assert "Profile: gate" in md
    assert "Docker Verificarlo" in md
    assert "Linf(By)" in md and "Linf(rho)" in md


def test_write_figures_creates_nonempty_pngs(tmp_path):
    gamma = 5.0 / 3.0
    ref = _grid(gamma)
    arr = ref.copy()
    arr[..., 0] += np.array([[0.0, 0.1], [0.2, 0.3]])
    arr[..., 5] -= np.array([[0.0, 0.2], [0.1, 0.4]])

    figures = ot.write_figures(tmp_path, arr, ref, gamma=gamma, dx=0.25, dy=0.5)

    assert figures == ["figures/reference_fields.png", "figures/drift_fields.png"]
    for rel in figures:
        path = tmp_path / rel
        assert path.is_file()
        assert path.stat().st_size > 100
