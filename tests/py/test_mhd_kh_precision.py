import json
from pathlib import Path

from scripts.build_matrix import BuildVariant
from scripts.regression import mhd_kh_precision as khp


def test_kelvin_helmholtz_precision_cfg_sets_solver_and_output(tmp_path):
    cfg = tmp_path / "kh.cfg"
    cfg.write_text(
        "test = kelvin_helmholtz\n"
        "nx = 256\n"
        "ny = 256\n"
        "riemann = hll\n",
        encoding="utf-8",
    )

    text = khp.precision_cfg_text(
        cfg.read_text(encoding="utf-8"),
        solver="hlld",
        output_file=tmp_path / "grid.bin",
        smoke=True,
    )

    assert "test = kelvin_helmholtz\n" in text
    assert "riemann = hlld\n" in text
    assert "nx = 64\n" in text
    assert "ny = 64\n" in text
    assert "output_format = binary\n" in text
    assert f"output_file = {tmp_path / 'grid.bin'}\n" in text


def test_blocked_mca_summary_is_schema_complete():
    block = khp.blocked_mca("docker daemon unavailable")

    assert block["p53"]["status"] == "blocked_environment"
    assert block["p24"]["status"] == "blocked_environment"
    assert block["p53"]["n"] == 0
    assert "docker daemon unavailable" in block["p24"]["reason"]


def test_load_mca_summary_returns_embedded_blocks(tmp_path):
    summary = tmp_path / "mca_summary.json"
    summary.write_text(
        json.dumps(
            {
                "mca": {
                    "p53": {"status": "completed", "n": 30, "runner": "docker"},
                    "p24": {"status": "completed", "n": 30, "runner": "docker"},
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )

    block = khp.load_mca_summary(summary)

    assert block["p53"]["status"] == "completed"
    assert block["p24"]["n"] == 30


def test_completed_mca_promotes_report_grade_gate():
    rows = [
        {
            "variant": "cpu-double-O2-ieee-leq",
            "finite": True,
            "rc": 0,
            "is_reference": True,
        },
        {
            "variant": "cpu-float-O2-ieee-leq",
            "finite": True,
            "rc": 0,
            "is_reference": False,
        },
    ]
    mca = {
        "p53": {"status": "completed", "n": 30},
        "p24": {"status": "completed", "n": 30},
    }

    summary = khp.assemble_summary(
        rows,
        mca,
        "deadbeef",
        solver="hll",
        phase="p1",
        smoke=False,
    )

    assert summary["gates"]["mca"] == {"pass": True, "status": "completed"}
    assert summary["gates"]["report_grade"]["pass"] is True
    assert "completed" in summary["claims"]["mca"]


def test_plan_rows_mark_reference_variant():
    variant = BuildVariant("double", "O2", False, False)

    row = khp.plan_row(variant, "hll", smoke=False)

    assert row["variant"] == "cpu-double-O2-ieee-leq"
    assert row["is_reference"] is True
    assert row["case"] == "kelvin_helmholtz_2d"
