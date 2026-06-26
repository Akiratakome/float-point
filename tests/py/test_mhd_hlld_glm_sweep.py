import pathlib
import sys


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from scripts.regression.mhd_hlld_glm_sweep import replace_or_append_cfg, summarise_rows


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
