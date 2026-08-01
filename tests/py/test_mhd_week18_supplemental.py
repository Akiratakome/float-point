import os
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from scripts.regression import mhd_week18_supplemental as w18


ROOT = Path(__file__).resolve().parents[2]


def test_hardware_plan_has_five_repeats_for_each_covered_pair():
    rows = w18.hardware_plan(repeats=5)

    assert len(rows) == 40
    assert {row["case"] for row in rows} == {"brio_wu_1d", "orszag_tang_2d"}
    assert {row["precision"] for row in rows} == {"float", "double"}
    assert {row["device"] for row in rows} == {"cpu", "gpu"}
    assert {row["repeat"] for row in rows} == {1, 2, 3, 4, 5}


def test_thread_plan_covers_two_2d_cases_both_precisions_and_four_threads():
    rows = w18.thread_plan(threads=(1, 2, 4, 8))

    assert len(rows) == 16
    assert {row["case"] for row in rows} == {
        "orszag_tang_2d",
        "kelvin_helmholtz_2d",
    }
    assert {row["precision"] for row in rows} == {"float", "double"}
    assert {row["omp_num_threads"] for row in rows} == {1, 2, 4, 8}


def test_cfl_plan_covers_hll_hlld_float_double_and_four_values():
    rows = w18.cfl_plan(cfl_values=(0.2, 0.4, 0.6, 0.8))

    assert len(rows) == 16
    assert {row["solver"] for row in rows} == {"hll", "hlld"}
    assert {row["precision"] for row in rows} == {"float", "double"}
    assert {row["cfl"] for row in rows} == {0.2, 0.4, 0.6, 0.8}


def test_generated_cfg_changes_only_requested_run_keys(tmp_path):
    text = "test = kelvin_helmholtz\ncfl = 0.4\nt_end = 1.0\n"

    result = w18.generated_cfg(
        text,
        {"cfl": 0.6, "riemann": "hlld"},
        tmp_path / "grid.bin",
        "cpu",
    )

    assert "cfl = 0.6\n" in result
    assert "riemann = hlld\n" in result
    assert "test = kelvin_helmholtz\n" in result
    assert "t_end = 1.0\n" in result
    assert "device = cpu\n" in result
    assert "output_format = binary\n" in result
    assert f"output_file = {tmp_path / 'grid.bin'}\n" in result


def test_hardware_gate_requires_repeat_count_and_bit_exact_pairs():
    rows = [
        {
            "case": "orszag_tang_2d",
            "precision": "double",
            "repeat": repeat,
            "device": device,
            "elapsed_wall_s": 10.0 if device == "cpu" else 2.0,
            "ulp_max": 0,
            "linf_abs": 0.0,
            "completed": True,
        }
        for repeat in range(1, 6)
        for device in ("cpu", "gpu")
    ]

    summary = w18.aggregate_hardware(rows, expected_repeats=5)

    assert summary["gate"]["pass"] is True
    assert summary["groups"][0]["speedup_median"] == 5.0
    assert summary["groups"][0]["cpu_time_iqr_s"] == 0.0

    incomplete = w18.aggregate_hardware(rows[:-1], expected_repeats=5)
    assert incomplete["gate"]["pass"] is False
    assert incomplete["gate"]["missing_pairs"]


def test_hardware_group_ulp_is_not_carried_between_cases():
    rows = [
        {
            "case": case,
            "precision": "double",
            "repeat": 1,
            "device": device,
            "elapsed_wall_s": 2.0 if device == "cpu" else 1.0,
            "ulp_max": 1 if case == "brio_wu_1d" else 0,
            "linf_abs": 1.0e-15 if case == "brio_wu_1d" else 0.0,
            "completed": True,
        }
        for case in ("brio_wu_1d", "orszag_tang_2d")
        for device in ("cpu", "gpu")
    ]

    summary = w18.aggregate_hardware(rows, expected_repeats=1)

    groups = {row["case"]: row for row in summary["groups"]}
    assert groups["brio_wu_1d"]["ulp_max"] == 1
    assert groups["orszag_tang_2d"]["ulp_max"] == 0


def test_hardware_gate_rejects_nonphysical_completed_rows():
    rows = [
        {
            "case": "brio_wu_1d",
            "precision": "double",
            "repeat": 1,
            "device": device,
            "elapsed_wall_s": 1.0,
            "ulp_max": 0,
            "linf_abs": 0.0,
            "completed": True,
            "finite_positive": device == "cpu",
        }
        for device in ("cpu", "gpu")
    ]

    assert w18.aggregate_hardware(rows, expected_repeats=1)["gate"]["pass"] is False


def test_thread_gate_compares_each_row_to_same_precision_one_thread():
    rows = [
        {
            "case": "kelvin_helmholtz_2d",
            "precision": "float",
            "omp_num_threads": thread,
            "completed": True,
            "ulp_max": 0,
            "linf_abs": 0.0,
        }
        for thread in (1, 2, 4, 8)
    ]

    summary = w18.aggregate_threads(rows)

    assert summary["gate"]["pass"] is True
    assert summary["gate"]["max_ulp"] == 0


def test_cfl_gate_reports_precision_effect_without_temporal_convergence_claim():
    rows = [
        {
            "solver": solver,
            "precision": precision,
            "cfl": cfl,
            "completed": True,
            "finite_positive": True,
            "steps": 100,
            "divB_max": 1.0e-3,
            "Linf_rho_vs_fp64": 0.0 if precision == "double" else 1.0e-6,
        }
        for solver in ("hll", "hlld")
        for precision in ("double", "float")
        for cfl in (0.2, 0.4, 0.6, 0.8)
    ]

    summary = w18.aggregate_cfl(rows)

    assert summary["gate"]["pass"] is True
    assert summary["claims"]["temporal_convergence"] is False


def test_run_name_contains_every_independent_axis():
    hardware = {
        "suite": "hardware_repeats",
        "case": "orszag_tang_2d",
        "precision": "float",
        "device": "gpu",
        "repeat": 3,
        "solver": "hll",
    }
    thread = {
        "suite": "thread_repro",
        "case": "kelvin_helmholtz_2d",
        "precision": "double",
        "device": "cpu",
        "solver": "hll",
        "omp_num_threads": 8,
    }

    assert w18.run_name(hardware) == "orszag_tang_2d-float-gpu-hll-r03"
    assert w18.run_name(thread) == "kelvin_helmholtz_2d-double-cpu-hll-t08"


def test_cleanup_refuses_non_grid_paths(tmp_path):
    path = tmp_path / "summary.json"
    path.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="non-grid"):
        w18.cleanup_grids([path])

    assert path.is_file()


def test_cli_defaults_to_week18_output():
    args = w18.parse_args(["hardware", "--repeats", "3"])

    assert args.suite == "hardware"
    assert args.repeats == 3
    assert "experiments" in str(args.out)
    assert "week18" in str(args.out)


def test_direct_cli_imports_metrics_without_pytest_path_injection():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "regression" / "mhd_week18_supplemental.py"),
            "--help",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_difference_metrics_use_ulp_only_for_same_dtype():
    reference = np.array([1.0, -1.0], dtype=np.float32)
    adjacent = np.nextafter(
        reference,
        np.array([2.0, -2.0], dtype=np.float32),
    )

    same_precision = w18.difference_metrics(adjacent, reference)
    cross_precision = w18.difference_metrics(
        adjacent.astype(np.float64),
        reference,
    )

    assert same_precision["ulp_max"] == 1
    assert same_precision["linf_abs"] > 0.0
    assert cross_precision["ulp_max"] is None


def test_physical_state_requires_finite_positive_density_and_pressure():
    valid = np.zeros((1, 1, 9), dtype=np.float64)
    valid[..., 0] = 1.0
    valid[..., 7] = 2.5

    assert w18.physical_state(valid, gamma=5.0 / 3.0)["finite_positive"] is True

    invalid = valid.copy()
    invalid[..., 0] = -1.0
    assert w18.physical_state(invalid, gamma=5.0 / 3.0)["finite_positive"] is False


def test_environment_override_restores_previous_value():
    key = "HRSC_WEEK18_TEST_ENV"
    original = os.environ.get(key)
    os.environ[key] = "before"
    try:
        with w18.environment_override({key: "during"}):
            assert os.environ[key] == "during"
        assert os.environ[key] == "before"
    finally:
        if original is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original


def test_write_hardware_outputs_creates_stable_packet(tmp_path):
    summary = w18.aggregate_hardware(
        [
            {
                "case": "orszag_tang_2d",
                "precision": "double",
                "repeat": 1,
                "device": device,
                "elapsed_wall_s": 4.0 if device == "cpu" else 1.0,
                "ulp_max": 0,
                "linf_abs": 0.0,
                "completed": True,
            }
            for device in ("cpu", "gpu")
        ],
        expected_repeats=1,
    )

    w18.write_suite_outputs(summary, tmp_path)

    saved = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert saved["gate"]["pass"] is True
    assert (tmp_path / "summary.csv").is_file()
    assert (tmp_path / "summary.md").is_file()
    assert (tmp_path / "figures" / "hardware_repeats.png").is_file()


def test_combined_summary_requires_all_three_suite_gates():
    summaries = {
        name: {"suite": name, "gate": {"pass": True}}
        for name in ("hardware_repeats", "thread_repro", "kh_cfl")
    }

    combined = w18.combine_summaries(summaries, commit="deadbeef")

    assert combined["gate"]["pass"] is True
    assert combined["git_commit"] == "deadbeef"
    assert combined["claim_boundaries"]["full_kh_mca_completed"] is False


def test_attach_hardware_metrics_pairs_same_repeat_and_precision():
    cpu = np.array([1.0, -1.0], dtype=np.float64)
    staged = [
        {
            "row": {
                "case": "brio_wu_1d",
                "precision": "double",
                "device": device,
                "repeat": 1,
            },
            "array": cpu.copy(),
        }
        for device in ("cpu", "gpu")
    ]

    rows = w18.attach_hardware_metrics(staged)

    assert all(row["ulp_max"] == 0 for row in rows)
    assert all(row["linf_abs"] == 0.0 for row in rows)


def test_attach_thread_metrics_uses_one_thread_reference():
    reference = np.array([1.0], dtype=np.float32)
    changed = np.nextafter(reference, np.array([2.0], dtype=np.float32))
    staged = [
        {
            "row": {
                "case": "kelvin_helmholtz_2d",
                "precision": "float",
                "omp_num_threads": thread,
            },
            "array": reference.copy() if thread == 1 else changed.copy(),
        }
        for thread in (1, 2)
    ]

    rows = w18.attach_thread_metrics(staged)
    indexed = {row["omp_num_threads"]: row for row in rows}

    assert indexed[1]["ulp_max"] == 0
    assert indexed[2]["ulp_max"] == 1


def test_attach_cfl_metrics_uses_same_solver_cfl_fp64_density_reference():
    double = np.zeros((1, 1, 9), dtype=np.float64)
    double[..., 0] = 1.0
    double[..., 7] = 2.5
    single = double.astype(np.float32)
    single[..., 0] = np.float32(1.000001)
    staged = [
        {
            "row": {"solver": "hll", "precision": precision, "cfl": 0.4},
            "array": array,
            "gamma": 5.0 / 3.0,
            "dx": 1.0,
        }
        for precision, array in (("double", double), ("float", single))
    ]

    rows = w18.attach_cfl_metrics(staged)
    indexed = {row["precision"]: row for row in rows}

    assert indexed["double"]["Linf_rho_vs_fp64"] == 0.0
    assert indexed["float"]["Linf_rho_vs_fp64"] > 0.0


def test_zero_ulp_axis_spec_makes_exact_agreement_visible():
    spec = w18.ulp_axis_spec([0, 0, 0])

    assert spec["ylim"] == (-0.1, 0.5)
    assert spec["annotations"] == ["0 ULP", "0 ULP", "0 ULP"]


def test_thread_runtime_ratios_use_same_group_one_thread_baseline():
    rows = [
        {
            "case": "orszag_tang_2d",
            "precision": "double",
            "omp_num_threads": thread,
            "elapsed_wall_s": elapsed,
        }
        for thread, elapsed in ((1, 10.0), (2, 5.0), (4, 2.5))
    ]

    ratios = w18.thread_runtime_ratios(rows)

    assert [row["runtime_vs_one_thread"] for row in ratios] == [1.0, 0.5, 0.25]
