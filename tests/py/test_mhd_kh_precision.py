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


def test_plan_rows_mark_reference_variant():
    variant = BuildVariant("double", "O2", False, False)

    row = khp.plan_row(variant, "hll", smoke=False)

    assert row["variant"] == "cpu-double-O2-ieee-leq"
    assert row["is_reference"] is True
    assert row["case"] == "kelvin_helmholtz_2d"
