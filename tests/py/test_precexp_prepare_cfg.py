from pathlib import Path

from scripts.verificarlo.precexp_prepare_cfg import materialise_cfg


def test_materialise_cfg_overrides_output_without_editing_source(tmp_path: Path) -> None:
    source = tmp_path / "sod.cfg"
    source.write_text("test = sod\noutput_file = old.bin\n", encoding="utf-8")
    target = tmp_path / "run" / "config.cfg"
    grid = tmp_path / "run" / "grid.bin"

    materialise_cfg(source, target, grid)

    assert source.read_text(encoding="utf-8") == "test = sod\noutput_file = old.bin\n"
    text = target.read_text(encoding="utf-8")
    assert "output_format = binary" in text
    assert f"output_file = {grid}" in text
