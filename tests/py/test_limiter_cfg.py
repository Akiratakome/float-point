from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


def _hrsc_binary() -> Path:
    value = os.environ.get("HRSC_TEST_BINARY")
    if not value:
        pytest.skip("set HRSC_TEST_BINARY to run hrsc limiter cfg smoke tests")
    path = Path(value)
    if not path.exists():
        pytest.skip(f"HRSC_TEST_BINARY does not exist: {path}")
    return path


def _write_cfg(path: Path, output_file: Path, *, limiter: str | None = None) -> None:
    lines = [
        "test = sod",
        "nx = 80",
        "xmin = 0.0",
        "xmax = 1.0",
        "gamma = 1.4",
        "cfl = 0.8",
        "t_end = 0.04",
        "bc = outflow",
        "solver = hllc",
        "mode = normal",
        "output_format = binary",
        f"output_file = {output_file}",
    ]
    if limiter is not None:
        lines.append(f"limiter = {limiter}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_cfg_text(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run(binary: Path, cfg: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(binary), str(cfg)], capture_output=True, text=True, check=False)


def test_missing_limiter_matches_explicit_minbee(tmp_path: Path) -> None:
    binary = _hrsc_binary()
    default_out = tmp_path / "default.bin"
    minbee_out = tmp_path / "minbee.bin"
    default_cfg = tmp_path / "default.cfg"
    minbee_cfg = tmp_path / "minbee.cfg"
    _write_cfg(default_cfg, default_out)
    _write_cfg(minbee_cfg, minbee_out, limiter="minbee")

    default_result = _run(binary, default_cfg)
    minbee_result = _run(binary, minbee_cfg)

    assert default_result.returncode == 0, default_result.stderr
    assert minbee_result.returncode == 0, minbee_result.stderr
    assert default_out.read_bytes() == minbee_out.read_bytes()


def test_vanleer_limiter_changes_output(tmp_path: Path) -> None:
    binary = _hrsc_binary()
    minbee_out = tmp_path / "minbee.bin"
    vanleer_out = tmp_path / "vanleer.bin"
    minbee_cfg = tmp_path / "minbee.cfg"
    vanleer_cfg = tmp_path / "vanleer.cfg"
    _write_cfg(minbee_cfg, minbee_out, limiter="minbee")
    _write_cfg(vanleer_cfg, vanleer_out, limiter="vanleer")

    minbee_result = _run(binary, minbee_cfg)
    vanleer_result = _run(binary, vanleer_cfg)

    assert minbee_result.returncode == 0, minbee_result.stderr
    assert vanleer_result.returncode == 0, vanleer_result.stderr
    assert minbee_out.read_bytes() != vanleer_out.read_bytes()


def test_invalid_limiter_fails_with_useful_message(tmp_path: Path) -> None:
    binary = _hrsc_binary()
    cfg = tmp_path / "bad.cfg"
    _write_cfg(cfg, tmp_path / "bad.bin", limiter="typo")

    result = _run(binary, cfg)

    assert result.returncode != 0
    assert "Unknown limiter" in result.stderr


def test_gpu_non_minbee_limiter_fails_before_cuda_run(tmp_path: Path) -> None:
    binary = _hrsc_binary()
    cfg = tmp_path / "gpu_vanleer.cfg"
    _write_cfg_text(
        cfg,
        [
            "test = sod",
            "nx = 40",
            "xmin = 0.0",
            "xmax = 1.0",
            "gamma = 1.4",
            "cfl = 0.8",
            "t_end = 0.03",
            "bc = outflow",
            "solver = hllc",
            "limiter = vanleer",
            "device = gpu",
            "mode = normal",
            "output_format = binary",
            f"output_file = {tmp_path / 'gpu.bin'}",
        ],
    )

    result = _run(binary, cfg)

    if (
        "Unknown device: gpu" in result.stderr
        or "device=gpu requires building with -DENABLE_CUDA=ON" in result.stderr
    ):
        pytest.skip("binary was built without CUDA device dispatch")
    assert result.returncode != 0
    assert "limiter selection is currently supported only for device=cpu" in result.stderr
