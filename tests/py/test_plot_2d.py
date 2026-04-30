from __future__ import annotations

import struct
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE = REPO_ROOT / "experiments/week5/baselines/lw_config6_n200/grid.bin"
PLOT_SCRIPT = REPO_ROOT / "scripts/figures/plot_2d.py"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data.startswith(PNG_SIGNATURE)
    assert data[12:16] == b"IHDR"
    return struct.unpack(">II", data[16:24])


@pytest.mark.parametrize("field", ["rho", "p", "vmag", "schlieren"])
def test_plot_2d_writes_valid_png_for_field(tmp_path: Path, field: str) -> None:
    if not BASELINE.exists():
        pytest.skip(f"missing baseline binary: {BASELINE}")

    out_png = tmp_path / f"{field}.png"
    result = subprocess.run(
        [
            sys.executable,
            str(PLOT_SCRIPT),
            str(BASELINE),
            "--field",
            field,
            "--out",
            str(out_png),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert out_png.exists()
    assert out_png.stat().st_size > 1024

    width, height = _png_dimensions(out_png)
    assert width >= 100
    assert height >= 100
