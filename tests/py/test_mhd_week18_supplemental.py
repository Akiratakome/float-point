from scripts.regression import mhd_week18_supplemental as w18


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
