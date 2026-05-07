from __future__ import annotations

import os
import struct
import subprocess
from pathlib import Path

import pytest


def _hrsc_binary() -> Path:
    value = os.environ.get("HRSC_TEST_BINARY")
    if not value:
        pytest.skip("set HRSC_TEST_BINARY to run hrsc output_times smoke tests")
    path = Path(value)
    if not path.exists():
        pytest.skip(f"HRSC_TEST_BINARY does not exist: {path}")
    return path


def _write_cfg(path: Path, output_file: Path, *, output_times: str | None = None) -> None:
    lines = [
        "test = sod",
        "nx = 40",
        "xmin = 0.0",
        "xmax = 1.0",
        "gamma = 1.4",
        "cfl = 0.8",
        "t_end = 0.03",
        "bc = outflow",
        "solver = hllc",
        "mode = normal",
        "output_format = binary",
        f"output_file = {output_file}",
    ]
    if output_times is not None:
        lines.append(f"output_times = {output_times}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _header_time(path: Path) -> float:
    with path.open("rb") as f:
        header = f.read(64)
    assert header[:4] == b"HRSC"
    return struct.unpack("<d", header[20:28])[0]


def test_default_binary_output_writes_only_final_file(tmp_path: Path) -> None:
    binary = _hrsc_binary()
    output_file = tmp_path / "grid.bin"
    cfg = tmp_path / "default.cfg"
    _write_cfg(cfg, output_file)

    result = subprocess.run([str(binary), str(cfg)], capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr
    assert output_file.exists()
    assert sorted(path.name for path in tmp_path.glob("*.bin")) == ["grid.bin"]


def test_output_times_writes_checkpoint_files_with_monotonic_header_times(tmp_path: Path) -> None:
    binary = _hrsc_binary()
    output_file = tmp_path / "grid.bin"
    cfg = tmp_path / "checkpoints.cfg"
    _write_cfg(cfg, output_file, output_times="0.01,0.02")

    result = subprocess.run([str(binary), str(cfg)], capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr
    files = sorted(path.name for path in tmp_path.glob("*.bin"))
    assert files == ["grid.bin", "grid_t0000.bin", "grid_t0001.bin"]
    times = [
        _header_time(tmp_path / "grid_t0000.bin"),
        _header_time(tmp_path / "grid_t0001.bin"),
        _header_time(tmp_path / "grid.bin"),
    ]
    assert times == sorted(times)
    assert times[-1] == pytest.approx(0.03)
