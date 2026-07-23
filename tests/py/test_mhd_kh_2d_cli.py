from pathlib import Path

from scripts.regression import mhd_kh_2d


def test_resolve_output_dir_maps_relative_path_under_repo():
    out = mhd_kh_2d.resolve_output_dir(Path("experiments/week16/kh"))

    assert out == mhd_kh_2d.ROOT / "experiments" / "week16" / "kh"


def test_validation_cfg_overrides_harness_keys_only(tmp_path):
    cfg = tmp_path / "kh.cfg"
    cfg.write_text(
        "test = kelvin_helmholtz\n"
        "nx = 256\n"
        "ny = 256\n"
        "t_end = 1.0\n"
        "bc = periodic\n",
        encoding="utf-8",
    )

    text = mhd_kh_2d.validation_cfg_text(
        cfg,
        tmp_path / "grid.bin",
        {"nx": 64, "ny": 64, "t_end": 0.05},
    )

    assert "test = kelvin_helmholtz\n" in text
    assert "bc = periodic\n" in text
    assert "nx = 64\n" in text
    assert "ny = 64\n" in text
    assert "t_end = 0.05\n" in text
    assert "output_format = binary\n" in text
    assert f"output_file = {tmp_path / 'grid.bin'}\n" in text
