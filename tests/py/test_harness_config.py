from pathlib import Path

from scripts.harness.config import materialise_config, replace_or_append_cfg


def test_replace_preserves_inline_comment_and_trailing_newline():
    text = "nx = 128  # validation grid\n# ny = 64\n"
    assert replace_or_append_cfg(text, "nx", "256") == (
        "nx = 256  # validation grid\n# ny = 64\n"
    )


def test_materialise_does_not_modify_source(tmp_path: Path):
    source = tmp_path / "source.cfg"
    target = tmp_path / "run" / "config.cfg"
    source.write_text("solver = hllc\n", encoding="utf-8")
    materialise_config(source, target, {"solver": "rusanov", "device": "gpu"})
    assert source.read_text(encoding="utf-8") == "solver = hllc\n"
    assert target.read_text(encoding="utf-8") == "solver = rusanov\ndevice = gpu\n"
