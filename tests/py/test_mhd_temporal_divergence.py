import csv
import hashlib
import json
import math
import sys
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "regression"))
sys.path.insert(0, str(ROOT))

import mhd_temporal_divergence as td


def test_ordering_statement_reports_observed():
    text = td.ordering_statement(True, ot_l1=31.0, brio_l1=30.0)
    assert "OT>Brio-Wu L1 contrast is observed" in text


def test_ordering_statement_reports_not_observed():
    text = td.ordering_statement(False, ot_l1=0.03, brio_l1=30.0)
    assert "OT>Brio-Wu L1 contrast is not observed" in text


def test_ordering_statement_reports_unavailable_when_not_comparable():
    text = td.ordering_statement(None, ot_l1=None, brio_l1=30.0)
    assert "OT>Brio-Wu L1 contrast is unavailable/not comparable" in text


def test_parse_args_defaults_to_all_full_runs():
    args = td.parse_args([])
    assert args.out == td.DEFAULT_OUT
    assert args.case == "all"
    assert args.smoke is False
    assert args.keep_grids is False


def test_route_output_keeps_full_default_canonical():
    assert td.route_output_dir(td.DEFAULT_OUT, case="all", smoke=False) == td.DEFAULT_OUT


def test_route_output_sends_smoke_to_dedicated_directory():
    expected = td.DEFAULT_OUT.with_name(f"{td.DEFAULT_OUT.name}_smoke")
    assert td.route_output_dir(td.DEFAULT_OUT, case="all", smoke=True) == expected


def test_route_output_includes_single_case():
    expected = td.DEFAULT_OUT.with_name(f"{td.DEFAULT_OUT.name}_brio_wu_1d")
    assert td.route_output_dir(td.DEFAULT_OUT, case="brio_wu_1d", smoke=False) == expected


def test_route_output_includes_single_case_and_smoke_suffix():
    expected = td.DEFAULT_OUT.with_name(f"{td.DEFAULT_OUT.name}_orszag_tang_2d_smoke")
    assert td.route_output_dir(td.DEFAULT_OUT, case="orszag_tang_2d", smoke=True) == expected


def test_route_output_honors_explicit_noncanonical_output():
    custom = ROOT / "experiments" / "custom-temporal-output"
    assert td.route_output_dir(custom, case="brio_wu_1d", smoke=True) == custom


def test_slice_plan_is_monotone_and_within_bounds():
    ts = td.slice_plan("orszag_tang_2d")
    assert ts == sorted(ts)
    assert len(ts) >= 10
    assert ts[0] > 0.0
    assert ts[-1] == td.CASES["orszag_tang_2d"]["t_end_max"]
    assert all(b > a for a, b in zip(ts, ts[1:]))  # strictly increasing


def test_temporal_cfg_overrides_only_harness_keys():
    base = "test = orszag_tang\nnx = 256\nny = 256\nt_end = 0.5\ngamma = 1.6666666666666667\nriemann = hll\n"
    text = td.temporal_cfg(base, nx=128, ny=128, t_end=0.25, solver="hll",
                           output_file=Path("runs/g.bin"))
    assert "test = orszag_tang" in text
    assert "gamma = 1.6666666666666667" in text
    assert "nx = 128" in text
    assert "ny = 128" in text
    assert "t_end = 0.25" in text
    assert "riemann = hll" in text
    assert "output_format = binary" in text
    assert "output_file = runs/g.bin" in text.replace("\\", "/")


def test_pair_entry_uses_loose_tolerances_and_pairs_paths_in_order():
    a = [Path("d/g_00.bin"), Path("d/g_01.bin")]
    b = [Path("f/g_00.bin"), Path("f/g_01.bin")]
    entry = td.pair_entry("orszag_tang_2d", gamma=5.0 / 3.0, double_grids=a, float_grids=b)
    assert entry["case"] == "orszag_tang_2d"
    assert entry["variable"] == "rho"
    assert entry["gamma"] == 5.0 / 3.0
    assert [str(p) for p in entry["a"]] == [str(p) for p in a]
    assert [str(p) for p in entry["b"]] == [str(p) for p in b]
    # fp32-vs-fp64 header time / dx differences must not trip the strict 1e-12 checks
    assert entry["time_tolerance"] >= 1e-3
    assert entry["spatial_tolerance"] >= 1e-6


def test_case_gamma_reads_value_or_defaults():
    assert td.case_gamma("gamma = 1.4\n") == 1.4
    assert td.case_gamma("nx = 8\n") == td.DEFAULT_GAMMA


def test_run_case_series_records_both_precisions_and_cleans_grids(tmp_path):
    calls = []

    def fake_runner(label, cfg_text, run_dir, bin_path, source_cfg, commit, sha, **kwargs):
        grid = Path(kwargs["output_bin"])
        grid.parent.mkdir(parents=True, exist_ok=True)
        grid.write_bytes(b"grid")
        calls.append((label, cfg_text, Path(bin_path), grid))
        return None, {
            "returncode": 0,
            "elapsed_wall_s": 0.01,
            "stderr_diagnostics": {"steps": 1, "divB_max": 0.0},
        }, ""

    def fake_analyser(entry, fit_window):
        assert len(entry["a"]) == len(entry["b"]) == 3
        return {
            "case": entry["case"], "pair": entry["pair"], "variable": "rho",
            "times": [0.01, 0.055, 0.1], "l1": [1e-8, 2e-8, 3e-8],
            "linf": [2e-8, 4e-8, 6e-8], "lambda_l1": 1.0,
            "lambda_linf": 1.0, "fit_l1": {"slope": 1.0, "intercept": -18.0},
            "fit_linf": {"slope": 1.0, "intercept": -17.0},
            "fit_window": fit_window, "notes": entry["notes"], "samples": [],
        }

    result = td.run_case_series(
        "brio_wu_1d", tmp_path,
        {"double": tmp_path / "double.exe", "float": tmp_path / "float.exe"},
        smoke=True, runner=fake_runner, analyser=fake_analyser,
    )
    assert len(calls) == 6
    assert result["record"]["lambda_l1"] == 1.0
    assert not list(tmp_path.rglob("*.bin"))


def test_run_case_series_keep_grids_preserves_successful_outputs(tmp_path):
    def fake_runner(label, cfg_text, run_dir, bin_path, source_cfg, commit, sha, **kwargs):
        grid = Path(kwargs["output_bin"])
        grid.parent.mkdir(parents=True, exist_ok=True)
        grid.write_bytes(b"grid")
        return None, {"returncode": 0}, ""

    def fake_analyser(entry, fit_window):
        return _record(entry["case"], 1.0, sample_count=3, n_fit=3)

    td.run_case_series(
        "brio_wu_1d", tmp_path,
        {"double": tmp_path / "double.exe", "float": tmp_path / "float.exe"},
        smoke=True, keep_grids=True, runner=fake_runner, analyser=fake_analyser,
    )
    assert len(list(tmp_path.rglob("*.bin"))) == 6


def test_run_case_series_analyser_exception_preserves_grids(tmp_path):
    def fake_runner(label, cfg_text, run_dir, bin_path, source_cfg, commit, sha, **kwargs):
        grid = Path(kwargs["output_bin"])
        grid.parent.mkdir(parents=True, exist_ok=True)
        grid.write_bytes(b"grid")
        return None, {"returncode": 0}, ""

    def failing_analyser(entry, fit_window):
        raise RuntimeError("analysis failed")

    with pytest.raises(RuntimeError, match="analysis failed"):
        td.run_case_series(
            "brio_wu_1d", tmp_path,
            {"double": tmp_path / "double.exe", "float": tmp_path / "float.exe"},
            smoke=True, runner=fake_runner, analyser=failing_analyser,
        )
    assert len(list(tmp_path.rglob("*.bin"))) == 6


def _record(case, lam, scale=1.0, *, sample_count=3, n_fit=3):
    times = [0.1 + 0.01 * index for index in range(sample_count)]
    l1 = [scale * (index + 1) for index in range(sample_count)]
    linf = [2.0 * value for value in l1]
    return {
        "case": case, "pair": "fp32-vs-fp64", "variable": "rho",
        "times": times, "l1": l1, "linf": linf, "lambda_l1": lam,
        "lambda_linf": lam,
        "fit_l1": {"slope": lam, "intercept": math.log(scale), "n_fit": n_fit},
        "fit_linf": {"slope": lam, "intercept": math.log(2 * scale), "n_fit": n_fit},
        "fit_window": [0.1, 0.3], "notes": [], "samples": [],
    }


def _full_records():
    brio = _record("brio_wu_1d", 30.0, sample_count=15, n_fit=13)
    ot = _record("orszag_tang_2d", 0.03, 1e-6, sample_count=25, n_fit=10)
    ot["lambda_linf"] = -0.04
    ot["fit_linf"]["slope"] = -0.04
    return [brio, ot]


def _full_runs():
    return [
        {
            "name": f"run-{index:02d}",
            "returncode": 0,
            "git_commit": "abc123",
            "binary_sha256": "b" * 64,
            "run_config_sha256": "c" * 64,
            "source_config_sha256": "d" * 64,
            "source_config": "tests/cases/source.cfg",
            "run_config": f"runs/{index:02d}/config.cfg",
            "run_config_text": "nx = 8\n",
        }
        for index in range(80)
    ]


def test_report_grade_rejects_smoke_length_records_even_when_technical_passes():
    records = [_record("brio_wu_1d", 1.0), _record("orszag_tang_2d", 1.0)]
    gates = td.evaluate_gates(
        records, _full_runs(), mode="diagnostic", selected_cases=list(td.CASES),
    )
    assert gates["technical_pass"] is True
    assert gates["sample_counts_exact"] is False
    assert gates["report_grade_pass"] is False
    assert gates["pass"] is False


def test_write_outputs_rejects_mismatched_record_series_before_csv(tmp_path):
    records = _full_records()
    records[0]["linf"] = records[0]["linf"][:-1]
    with pytest.raises(ValueError, match="series length mismatch"):
        td.write_outputs(
            tmp_path, records, _full_runs(),
            mode="report-grade", selected_cases=list(td.CASES),
        )


def test_report_grade_rejects_failed_and_missing_run_provenance():
    runs = _full_runs()
    runs[0]["returncode"] = 1
    del runs[1]["binary_sha256"]
    gates = td.evaluate_gates(
        _full_records(), runs, mode="report-grade", selected_cases=list(td.CASES),
    )
    assert gates["runs_successful"] is False
    assert gates["run_provenance_complete"] is False
    assert gates["report_grade_pass"] is False
    assert gates["pass"] is False


def test_full_synthetic_report_grade_packet_passes():
    gates = td.evaluate_gates(
        _full_records(), _full_runs(),
        mode="report-grade", selected_cases=list(td.CASES),
    )
    assert gates["technical_pass"] is True
    assert gates["sample_counts_exact"] is True
    assert gates["series_aligned"] is True
    assert gates["required_lambdas_finite"] is True
    assert gates["fit_counts_sufficient"] is True
    assert gates["run_count_exact"] is True
    assert gates["runs_successful"] is True
    assert gates["run_provenance_complete"] is True
    assert gates["report_grade_pass"] is True
    assert gates["pass"] is True


def test_outputs_are_strict_json_and_register_figure(tmp_path):
    records = _full_records()
    paths = td.write_outputs(
        tmp_path, records, _full_runs(),
        mode="report-grade", selected_cases=list(td.CASES),
    )
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["gates"]["pass"] is True
    assert payload["gates"]["technical_pass"] is True
    assert payload["mode"] == "report-grade"
    assert payload["selected_cases"] == list(td.CASES)
    assert payload["gates"]["orszag_tang_positive_lambda"] is True
    assert payload["interpretation"]["formal_maximal_lyapunov"] is False
    assert payload["interpretation"]["planned_ot_exceeds_brio_l1"] is False
    assert payload["interpretation"]["orszag_tang_linf_positive"] is False
    assert "gates.pass is report_grade_pass" in payload["interpretation"]["gate_scope"]
    generator = ROOT / payload["analysis_generator"]["path"]
    expected_hash = hashlib.sha256(generator.read_bytes()).hexdigest()
    assert payload["analysis_generator"]["sha256"] == expected_hash
    assert payload["git_commit_semantics"] == "summary-generation checkout"
    assert payload["run_provenance"]["git_commit_field"] == "runs[].git_commit"
    markdown = paths["markdown"].read_text(encoding="utf-8")
    assert "OT>Brio-Wu L1 contrast is not observed" in markdown
    assert "fixed fit windows" in markdown
    assert "| n_fit L1 | n_fit Linf |" in markdown
    assert "| 13 | 13 |" in markdown
    assert "| 10 | 10 |" in markdown
    rows = list(csv.DictReader(paths["csv"].open(encoding="utf-8")))
    assert rows[0]["n_fit_l1"] == "13"
    assert rows[-1]["n_fit_linf"] == "10"
    assert paths["figure"].is_file()


def test_plot_records_masks_zero_drift_without_runtime_warnings(tmp_path):
    record = _record("brio_wu_1d", 0.1)
    record["l1"] = [0.0, 0.0, 0.0]
    record["linf"] = [0.0, 0.0, 0.0]
    record["fit_l1"] = {"slope": None, "intercept": None}
    record["fit_window"] = None
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        figure = td.plot_records(tmp_path, [record])
    assert figure.is_file()
