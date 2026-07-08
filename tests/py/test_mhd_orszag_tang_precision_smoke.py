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
    assert payload["gates"]["G0_anchor"]["pass"] is True
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


def test_run_deterministic_uses_injected_hooks_and_deletes_grids(tmp_path):
    base = "test = orszag_tang\nnx = 256\nny = 256\nt_end = 0.5\ngamma = 1.6666666666666667\n"

    class Header:
        nx = 4
        ny = 4
        dx = 0.25
        dy = 0.25

    arr = np.zeros((4, 4, 9), dtype=np.float64)
    arr[..., 0] = 1.0
    arr[..., 4] = 0.5
    arr[..., 5] = 0.25
    arr[..., 7] = 3.0

    built = []

    def fake_builder(variant):
        built.append(variant.name)
        binary = tmp_path / "hrsc_mhd.exe"
        binary.write_bytes(b"exe")
        return binary

    def fake_runner(label, cfg_text, run_dir, bin_path, source_cfg, commit, binary_sha256, **kwargs):
        assert "riemann = hlld" in cfg_text
        assert "nx = 128" in cfg_text
        grid = Path(kwargs["output_bin"])
        grid.parent.mkdir(parents=True, exist_ok=True)
        grid.write_bytes(b"grid")
        meta = {
            "elapsed_wall_s": 0.1,
            "stderr_diagnostics": {"steps": 76, "divB_mean": 0.2, "divB_max": 1.085},
        }
        return object(), meta, "stderr"

    def fake_reader(path):
        return Header(), arr.copy()

    payload = ot.run_deterministic(
        tmp_path / "out",
        solver="hlld",
        profile="gate",
        base_cfg_text=base,
        builder=fake_builder,
        runner=fake_runner,
        reader=fake_reader,
        keep_grids=False,
    )

    assert len(payload["rows"]) == 8
    assert len(built) == 8
    assert built[0] == "cpu-double-O2-ieee-leq"
    assert payload["rows"][0]["is_reference"] is True
    assert payload["rows"][1]["metadata_path"].endswith("metadata.json")
    assert payload["gates"]["G0_anchor"]["pass"] is True
    assert payload["figures"]
    assert not list((tmp_path / "out").glob("**/grid.bin"))


def test_run_deterministic_skips_drift_figures_when_drift_grid_is_nonfinite(tmp_path):
    base = "test = orszag_tang\nnx = 256\nny = 256\nt_end = 0.5\ngamma = 1.6666666666666667\n"

    class Header:
        nx = 4
        ny = 4
        dx = 0.25
        dy = 0.25

    finite = np.zeros((4, 4, 9), dtype=np.float64)
    finite[..., 0] = 1.0
    finite[..., 4] = 0.5
    finite[..., 5] = 0.25
    finite[..., 7] = 3.0
    nan_grid = np.full((4, 4, 9), np.nan, dtype=np.float64)

    def fake_builder(variant):
        binary = tmp_path / "hrsc_mhd.exe"
        binary.write_bytes(b"exe")
        return binary

    def fake_runner(label, cfg_text, run_dir, bin_path, source_cfg, commit, binary_sha256, **kwargs):
        grid = Path(kwargs["output_bin"])
        grid.parent.mkdir(parents=True, exist_ok=True)
        grid.write_bytes(b"grid")
        meta = {
            "elapsed_wall_s": 0.1,
            "stderr_diagnostics": {"steps": 76, "divB_mean": 0.2, "divB_max": 1.085},
        }
        return object(), meta, "stderr"

    def fake_reader(path):
        if "cpu-float-O2-ieee-leq" in str(path):
            return Header(), nan_grid.copy()
        return Header(), finite.copy()

    payload = ot.run_deterministic(
        tmp_path / "out",
        solver="hlld",
        profile="gate",
        base_cfg_text=base,
        builder=fake_builder,
        runner=fake_runner,
        reader=fake_reader,
        keep_grids=False,
    )

    assert payload["gates"]["G0_anchor"]["pass"] is False
    assert payload["figures"] == []
    assert (tmp_path / "out" / "summary.json").is_file()
    assert (tmp_path / "out" / "summary.csv").is_file()
    assert (tmp_path / "out" / "summary.md").is_file()
    assert next(row for row in payload["rows"] if row["variant"] == "cpu-float-O2-ieee-leq")["finite"] is False


def test_run_deterministic_rejects_empty_or_missing_reference_variants(tmp_path):
    def fail_builder(variant):
        pytest.fail("explicit variants=[] must not default to the full P0 plan")

    with pytest.raises(ValueError, match="variants.*empty"):
        ot.run_deterministic(tmp_path / "empty", variants=[], builder=fail_builder)

    non_reference = next(variant for variant in ot.select_variants("p0") if variant.name != REFERENCE)

    with pytest.raises(ValueError, match="reference variant"):
        ot.run_deterministic(tmp_path / "missing-reference", variants=[non_reference], builder=fail_builder)


def test_resolve_output_dir_and_profile_subdirs():
    assert ot.DEFAULT_OUT == ot.ROOT / "experiments" / "week15" / "orszag_tang_precision_smoke"
    assert ot.resolve_output_dir(None, "hll") == ot.DEFAULT_OUT
    assert ot.resolve_output_dir(None, "hlld").name == f"{ot.DEFAULT_OUT.name}_hlld"
    explicit = ot.resolve_output_dir(Path("experiments/x"), "hlld")
    assert explicit.is_absolute()
    assert ot.PROFILES["gate"]["subdir"] == "gate128"
    assert ot.PROFILES["headline"]["subdir"] == "headline256"


def test_main_prints_packet_summary_and_returns_anchor_gate_status(tmp_path, monkeypatch, capsys):
    calls = []

    def fake_run_deterministic(packet, *, solver, profile, keep_grids):
        calls.append((packet, solver, profile, keep_grids))
        return {"gates": {"G0_anchor": {"pass": True}}}

    monkeypatch.setattr(ot, "run_deterministic", fake_run_deterministic)

    rc = ot.main([
        "--out",
        str(tmp_path),
        "--solver",
        "hlld",
        "--profile",
        "headline",
        "--keep-grids",
    ])

    packet = tmp_path / "headline256"
    assert rc == 0
    assert calls == [(packet, "hlld", "headline", True)]
    assert capsys.readouterr().out.strip() == str(packet / "summary.md")


def test_main_returns_one_when_anchor_gate_fails(tmp_path, monkeypatch):
    def fake_run_deterministic(packet, *, solver, profile, keep_grids):
        return {"gates": {"G0_anchor": {"pass": False}}}

    monkeypatch.setattr(ot, "run_deterministic", fake_run_deterministic)

    assert ot.main(["--out", str(tmp_path), "--solver", "hll", "--profile", "gate"]) == 1
