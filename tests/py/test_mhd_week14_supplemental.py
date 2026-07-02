import json
from pathlib import Path

import numpy as np

from scripts.regression import mhd_week14_supplemental as supp


def test_resolution_ladder_plan_defaults_are_brio_wu_cpu_hll():
    rows = supp.resolution_ladder_plan()

    assert len(rows) == 8
    assert rows[0] == {
        "suite": "resolution_ladder",
        "case": "brio_wu_1d",
        "nx": 200,
        "precision": "double",
        "variant": "cpu-double-O2-ieee-leq",
        "opt": "O2",
        "fast_math": False,
        "riemann": "leq",
        "hardware": "cpu",
        "solver": "HLL",
    }
    assert rows[-1]["nx"] == 1600
    assert rows[-1]["variant"] == "cpu-float-O2-ieee-leq"
    assert {row["fast_math"] for row in rows} == {False}


def test_time_slice_and_thread_plans_keep_required_axes():
    time_rows = supp.time_slice_plan(times=(0.02, 0.10))
    thread_rows = supp.thread_repro_plan(threads=(1, 4))

    assert [row["variant"] for row in time_rows[:4]] == [
        "cpu-double-O2-ieee-leq",
        "cpu-float-O2-ieee-leq",
        "cpu-double-Ofast-ieee-leq",
        "cpu-float-Ofast-ieee-leq",
    ]
    assert [row["t_end"] for row in time_rows] == [0.02] * 4 + [0.10] * 4
    assert {row["fast_math"] for row in time_rows} == {False}
    assert [row["omp_num_threads"] for row in thread_rows] == [1, 4]
    assert {row["variant"] for row in thread_rows} == {"cpu-double-O2-ieee-leq"}


def test_variant_label_matches_build_variant_fastmath_name():
    row = supp.time_slice_plan(
        times=(0.02,),
        variants=({"precision": "float", "opt": "O3", "fast_math": True, "riemann": "strict"},),
    )[0]

    assert row["fast_math"] is True
    assert row["variant"] == "cpu-float-O3-fastmath-strict"


def test_brio_wu_cfg_only_updates_requested_keys_and_binary_output():
    base = "nx = 400\nt_end = 0.1\n# output_file = old.bin\n"

    text = supp.brio_wu_cfg(base, nx=800, t_end=0.06, output_file=Path("runs/a/grid.bin"))

    assert "nx = 800" in text
    assert "t_end = 0.06" in text
    assert "output_format = binary" in text
    assert "output_file = runs/a/grid.bin" in text.replace("\\", "/")
    assert "# output_file = old.bin" in text


def test_measure_array_returns_week14_row_schema_and_field_norms():
    ref = np.zeros((1, 2, 9), dtype=np.float64)
    ref[..., 0] = 1.0
    ref[..., 4] = 0.75
    ref[..., 5] = 1.0
    ref[..., 7] = 2.0
    arr = ref.copy()
    arr[0, 1, 0] = 1.5
    arr[0, 1, 1] = 0.3
    arr[0, 1, 5] = 1.25
    arr[0, 1, 7] = 2.6
    plan = {
        "suite": "resolution_ladder",
        "variant": "cpu-float-O2-ieee-leq",
        "precision": "float",
        "opt": "O2",
        "fast_math": False,
        "riemann": "leq",
        "nx": 2,
        "t_end": 0.1,
        "omp_num_threads": 4,
    }

    row = supp.measure_array(
        plan,
        arr,
        ref,
        gamma=2.0,
        dx=0.5,
        diagnostics={"steps": 17, "divB_max": 3.25e-12},
        walltime_s=0.125,
    )

    assert row["suite"] == "resolution_ladder"
    assert row["variant"] == "cpu-float-O2-ieee-leq"
    assert row["fast_math"] is False
    assert row["nx"] == 2
    assert row["t_end"] == 0.1
    assert row["omp_num_threads"] == 4
    assert row["finite"] is True
    assert row["steps"] == 17
    assert row["divB_max"] == 3.25e-12
    assert row["walltime_s"] == 0.125
    assert set(row) >= {
        "L1_rho",
        "L2_rho",
        "Linf_rho",
        "L1_By",
        "L2_By",
        "Linf_By",
        "L1_p",
        "L2_p",
        "Linf_p",
        "L1_vx",
        "L2_vx",
        "Linf_vx",
    }
    assert row["L1_rho"] == 0.25
    assert row["Linf_By"] == 0.25


def test_run_planned_case_uses_injected_runner_reader_and_removes_grid(tmp_path):
    seen = {}

    def fake_runner(label, cfg_text, run_dir, bin_path, source_cfg, commit, binary_sha256, **kwargs):
        seen["label"] = label
        seen["cfg_text"] = cfg_text
        seen["run_dir"] = run_dir
        seen["kwargs"] = kwargs
        output_bin = Path(kwargs["output_bin"])
        output_bin.parent.mkdir(parents=True, exist_ok=True)
        output_bin.write_bytes(b"fake-grid")
        meta = {
            "elapsed_wall_s": 1.5,
            "stderr_diagnostics": {"steps": 3, "divB_max": 0.0},
        }
        return object(), meta, "[mhd] t=0.02 steps=3 divB_mean=0 divB_max=0"

    class Header:
        nx = 4
        ny = 1
        dx = 0.25

    ref = np.zeros((1, 4, 9), dtype=np.float64)
    ref[..., 0] = 1.0
    ref[..., 7] = 2.0

    def fake_reader(path):
        seen["reader_path"] = Path(path)
        return Header(), ref.copy()

    plan = {
        "suite": "time_sliced_drift",
        "variant": "cpu-double-O2-ieee-leq",
        "precision": "double",
        "opt": "O2",
        "fast_math": False,
        "riemann": "leq",
        "nx": 4,
        "t_end": 0.02,
        "env": {"OMP_NUM_THREADS": "2"},
    }

    row, arr, header = supp.run_planned_case(
        plan,
        out=tmp_path,
        binary=tmp_path / "hrsc_mhd",
        base_cfg_text="gamma = 2\nnx = 2\nt_end = 0.1\n",
        runner=fake_runner,
        reader=fake_reader,
        commit="abc123",
        binary_sha="sha",
    )

    assert row["variant"] == "cpu-double-O2-ieee-leq"
    assert row["steps"] == 3
    assert row["walltime_s"] == 1.5
    assert header.nx == 4
    assert arr.shape == (1, 4, 9)
    assert "nx = 4" in seen["cfg_text"]
    assert "t_end = 0.02" in seen["cfg_text"]
    assert "output_format = binary" in seen["cfg_text"]
    assert "OMP_NUM_THREADS" in seen["kwargs"]["env"]
    assert seen["reader_path"].name == "grid.bin"
    assert not seen["reader_path"].exists()


def test_relative_rows_adds_errors_against_selected_reference():
    rows = [
        {"variant": "ref", "L1_rho": 0.0, "Linf_By": 0.0, "walltime_s": 2.0},
        {"variant": "cand", "L1_rho": 0.5, "Linf_By": 2.0, "walltime_s": 3.0},
    ]

    out = supp.relative_rows(rows, lambda row: row["variant"] == "ref")

    assert out[0]["is_relative_reference"] is True
    assert out[1]["is_relative_reference"] is False
    assert out[1]["rel_L1_rho"] == 0.5
    assert out[1]["rel_Linf_By"] == 2.0
    assert "rel_walltime_s" not in out[1]


def test_write_summary_sanitizes_numpy_scalars(tmp_path):
    path = tmp_path / "summary.json"

    supp.write_summary(path, {"rows": [{"value": np.float64(1.25), "count": np.int64(3)}]})

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload == {"rows": [{"value": 1.25, "count": 3}]}


def test_plot_helpers_create_nonempty_pngs(tmp_path):
    resolution = {
        "rows": [
            {"nx": 200, "precision": "double", "L1_rho": 0.2},
            {"nx": 400, "precision": "double", "L1_rho": 0.1},
            {"nx": 200, "precision": "float", "L1_rho": 0.3},
        ]
    }
    drift = {
        "rows": [
            {"t_end": 0.02, "variant": "cpu-double-O2-ieee-leq", "Linf_By": 0.1},
            {"t_end": 0.04, "variant": "cpu-double-O2-ieee-leq", "Linf_By": 0.2},
        ]
    }
    threads = {
        "rows": [
            {"omp_num_threads": 1, "Linf_rho": 0.0},
            {"omp_num_threads": 4, "Linf_rho": 1.0e-12},
        ]
    }

    outputs = [
        tmp_path / "resolution.png",
        tmp_path / "drift.png",
        tmp_path / "threads.png",
    ]
    supp.plot_resolution_ladder(resolution, outputs[0])
    supp.plot_time_sliced_drift(drift, outputs[1])
    supp.plot_thread_repro(threads, outputs[2])

    assert all(path.is_file() and path.stat().st_size > 0 for path in outputs)


def test_summary_rows_rejects_bare_mapping_without_rows():
    try:
        list(supp._summary_rows({"variant": "cpu-double-O2-ieee-leq"}))
    except ValueError as exc:
        assert "rows" in str(exc)
    else:
        raise AssertionError("bare mapping without rows should be rejected")


def test_metric_does_not_plot_nonfinite_rows_as_zero_drift():
    value = supp._metric({"finite": False, "Linf_rho": 0.0}, "Linf_rho")

    assert np.isnan(value)
    assert supp._metric({"finite": True, "Linf_rho": 0.0}, "Linf_rho") == np.finfo(np.float64).tiny


def test_preserve_run_provenance_carries_metadata_after_remeasurement():
    measured = {"variant": "cpu-double-O2-ieee-leq", "L1_rho": 0.0}
    run_row = {
        "variant": "cpu-double-O2-ieee-leq",
        "run_dir": "runs/cpu-double-O2-ieee-leq",
        "metadata_path": "runs/cpu-double-O2-ieee-leq/metadata.json",
    }

    out = supp._preserve_run_provenance(measured, run_row)

    assert out["run_dir"] == "runs/cpu-double-O2-ieee-leq"
    assert out["metadata_path"].endswith("metadata.json")


def test_suite_headlines_report_finitemax_and_thread_result():
    summary = {
        "rows": [
            {
                "variant": "cpu-double-O2-ieee-leq",
                "finite": True,
                "divB_max": 4.441e-14,
                "Linf_By": 0.0,
                "Linf_rho": 0.0,
                "omp_num_threads": 1,
            },
            {
                "variant": "cpu-float-O2-ieee-leq",
                "finite": True,
                "divB_max": 2.384e-5,
                "Linf_By": 0.125,
                "Linf_rho": 0.25,
                "omp_num_threads": 4,
            },
        ]
    }

    stats = supp.suite_headlines(summary)

    assert stats["finite_rows"] == 2
    assert stats["total_rows"] == 2
    assert stats["max_divB_abs"] == 2.384e-5
    assert stats["max_Linf_By"] == 0.125
    assert stats["max_thread_Linf_rho"] == 0.25


def test_render_report_maps_experiments_and_keeps_verificarlo_required():
    report = supp.render_report(
        {
            "git_commit": "abc123",
            "suites": {
                "resolution_ladder": {
                    "summary_path": "resolution_ladder/summary.json",
                    "figure_path": "resolution_ladder/figure.png",
                    "rows": 8,
                    "headlines": {"finite_rows": 8, "total_rows": 8, "max_divB_abs": 8.882e-14},
                },
                "time_sliced_drift": {
                    "summary_path": "time_sliced_drift/summary.json",
                    "figure_path": "time_sliced_drift/figure.png",
                    "rows": 20,
                    "headlines": {"finite_rows": 20, "total_rows": 20, "max_Linf_By": 0.5},
                },
                "thread_repro": {
                    "summary_path": "thread_repro/summary.json",
                    "figure_path": "thread_repro/figure.png",
                    "rows": 4,
                    "headlines": {"finite_rows": 4, "total_rows": 4, "max_thread_Linf_rho": 0.0},
                },
            },
        }
    )

    assert "resolution ladder" in report
    assert "time-sliced drift" in report
    assert "thread reproducibility" in report
    assert "Report 2" in report
    assert "Docker Verificarlo MCA remains formal evidence" in report
    assert "Week14 summary" in report
    assert "How To Read The Figures" in report
    assert "resolution_ladder/figure.png" in report
    assert "(20 rows)" in report
    assert "They do not broaden the Week-14 claim" in report
    assert "Headline Checks" in report
    assert "finite 20/20" in report
    assert "Binary grids are transient" in report
