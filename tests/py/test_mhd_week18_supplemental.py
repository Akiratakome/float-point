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
