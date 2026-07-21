import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "regression"))
sys.path.insert(0, str(ROOT))

import mhd_temporal_divergence as td


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
