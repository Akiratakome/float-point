import pathlib
import sys


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from scripts.regression.mhd_hlld_glm_sweep import (
    json_sanitise,
    make_run_cfg,
    replace_or_append_cfg,
    row_from_metadata,
    summarise_rows,
)


def test_replace_or_append_cfg_replaces_existing_key_and_preserves_comment():
    text = "nx = 256  # base grid\nriemann = hll\n"

    out = replace_or_append_cfg(text, "nx", "64")

    assert out == "nx = 64  # base grid\nriemann = hll\n"


def test_replace_or_append_cfg_appends_missing_key_with_trailing_newline():
    out = replace_or_append_cfg("nx = 64\n", "glm_cr", "0.18")

    assert out == "nx = 64\nglm_cr = 0.18\n"


def test_summarise_rows_selects_lowest_finite_hlld_divb_without_adoption():
    rows = [
        {"riemann": "hll", "glm_cr": 0.05, "divB_max": 1.0e-3, "returncode": 0},
        {"riemann": "hlld", "glm_cr": 0.05, "divB_max": float("nan"), "returncode": 0},
        {"riemann": "hlld", "glm_cr": 0.18, "divB_max": 4.0e-4, "returncode": 0},
        {"riemann": "hlld", "glm_cr": 0.3, "divB_max": 2.0e-4, "returncode": 0},
    ]

    summary = summarise_rows(rows)

    assert summary["best_finite_hlld"]["glm_cr"] == 0.3
    assert summary["best_finite_hlld"]["divB_max"] == 2.0e-4
    assert summary["hlld_adopted"] is False
    assert "diagnostic" in summary["decision"].lower()
    assert "not production adoption" in summary["decision"].lower()


def test_summarise_rows_excludes_failed_hlld_from_best_diagnostic():
    rows = [
        {"riemann": "hlld", "glm_cr": 0.05, "divB_max": 1.0e-6, "returncode": 1},
        {"riemann": "hlld", "glm_cr": 0.18, "divB_max": 4.0e-4, "returncode": 0},
    ]

    summary = summarise_rows(rows)

    assert summary["best_finite_hlld"]["glm_cr"] == 0.18
    assert summary["best_finite_hlld"]["returncode"] == 0


def test_make_run_cfg_applies_overrides_without_mutating_source_text():
    source = "nx = 256\nny = 256\nt_end = 0.5\nglm_cr = 0.18\n"

    out = make_run_cfg(
        source,
        grid_path=pathlib.Path("run") / "grid.bin",
        riemann="hlld",
        glm_cr=0.05,
        nx=64,
        t_end=0.05,
    )

    assert source == "nx = 256\nny = 256\nt_end = 0.5\nglm_cr = 0.18\n"
    assert "nx = 64\n" in out
    assert "ny = 64\n" in out
    assert "t_end = 0.05\n" in out
    assert "glm_cr = 0.05\n" in out
    assert "riemann = hlld\n" in out
    assert "output_format = binary\n" in out
    assert "output_file = run\\grid.bin\n" in out or "output_file = run/grid.bin\n" in out


def test_row_from_metadata_reuses_persisted_rho_metrics_without_grid_bin(tmp_path):
    run_dir = tmp_path / "hlld_glm0.18"
    meta = {
        "returncode": 0,
        "elapsed_wall_s": 1.25,
        "output_binary": str(run_dir / "grid.bin"),
        "stderr_diagnostics": {
            "t": 0.05,
            "steps": 19,
            "divB_mean": 0.04,
            "divB_max": 0.3,
            "line": "[mhd] t=0.050000 steps=19 divB_mean=4e-2 divB_max=3e-1",
        },
        "rho_metrics": {
            "grid_status": "read",
            "finite_rho": True,
            "rho_min": 2.4,
            "rho_max": 3.7,
        },
    }

    row = row_from_metadata(meta, run_dir, "hlld", 0.18, reused=True)

    assert row["reused"] is True
    assert row["finite_rho"] is True
    assert row["rho_min"] == 2.4
    assert row["rho_max"] == 3.7
    assert row["grid_status"] == "read"


def test_json_sanitise_replaces_non_finite_numbers():
    payload = {"ok": 1.0, "bad": float("nan"), "nested": [float("inf"), {"x": -float("inf")}]}

    assert json_sanitise(payload) == {"ok": 1.0, "bad": None, "nested": [None, {"x": None}]}
