from __future__ import annotations

import struct
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "regression"))

import float_regression_report as frr  # noqa: E402
from io_helper import IDX_E, IDX_RHO, IDX_RHOU, IDX_RHOV  # noqa: E402


def _write_convergence_csv(path: Path, nx_last: int, l1_rho: float) -> None:
    header = (
        "# N        dx            L1_rho        L2_rho        Linf_rho      "
        "L1_u          L2_u          Linf_u        L1_p          L2_p          Linf_p\n"
    )
    body = (
        f"{nx_last}  1e-3  {l1_rho:.15e}  2e-3  3e-3  "
        f"4e-3  5e-3  6e-3  7e-3  8e-3  9e-3\n"
    )
    path.write_text(header + body, encoding="utf-8")


def _write_grid_bin(
    path: Path,
    nx: int,
    dtype: np.dtype,
    rho_value: float,
    gamma: float = 1.4,
) -> None:
    p = 1.0
    e_internal = p / (gamma - 1.0)
    cons = np.zeros((1, nx, 4), dtype=dtype)
    cons[..., IDX_RHO] = rho_value
    cons[..., IDX_RHOU] = 0.0
    cons[..., IDX_RHOV] = 0.0
    cons[..., IDX_E] = e_internal
    _write_binary(path, cons, 1.0 / nx, 1.0 / nx)


def _write_2d_grid_bin(
    path: Path,
    nx: int,
    ny: int,
    dtype: np.dtype,
    rho_value: float,
    gamma: float = 1.4,
) -> None:
    p = 1.0
    e_internal = p / (gamma - 1.0)
    cons = np.zeros((ny, nx, 4), dtype=dtype)
    cons[..., IDX_RHO] = rho_value
    cons[..., IDX_E] = e_internal
    _write_binary(path, cons, 1.0 / nx, 1.0 / ny)


def _write_binary(path: Path, cons: np.ndarray, dx: float, dy: float) -> None:
    ny, nx, nvars = cons.shape
    precision_tag = cons.dtype.itemsize
    header = struct.pack(
        "<4siiiiddd20s",
        b"HRSC",
        nx,
        ny,
        nvars,
        precision_tag,
        0.0,
        dx,
        dy,
        b"\x00" * 20,
    )
    assert len(header) == 64
    with open(path, "wb") as f:
        f.write(header)
        f.write(cons.tobytes(order="C"))


def _populate_1d_case_set(tmp_path: Path, nx: int, float_rho: float = 1.0) -> None:
    for test in frr.TESTS_1D:
        _write_convergence_csv(tmp_path / f"{test}_double.csv", nx, 1.0e-3)
        _write_convergence_csv(tmp_path / f"{test}_float.csv", nx, 1.0e-3)
        _write_grid_bin(tmp_path / f"{test}_double_grid.bin", nx, np.dtype(np.float64), 1.0)
        _write_grid_bin(tmp_path / f"{test}_float_grid.bin", nx, np.dtype(np.float32), float_rho)


def test_1d_report_pipeline_runs(tmp_path: Path) -> None:
    _populate_1d_case_set(tmp_path, nx=800)

    summary = frr._report_1d(tmp_path)

    assert summary["mode"] == "1d"
    assert (tmp_path / "summary.md").is_file()
    assert (tmp_path / "summary.json").is_file()


def test_1d_report_emits_philip_metric(tmp_path: Path) -> None:
    nx = 800
    _populate_1d_case_set(tmp_path, nx=nx)
    _write_grid_bin(tmp_path / "sod_float_grid.bin", nx, np.dtype(np.float32), 1.0 + 1.0e-7)

    summary = frr._report_1d(tmp_path)
    sod = summary["tests"]["sod"]

    expected = float(np.float32(1.0 + 1.0e-7) - np.float32(1.0))
    assert sod["philip"]["L1_rho_fmd"] == pytest.approx(expected, rel=1e-12)
    assert sod["philip"]["L1_rho_ratio"] == pytest.approx(expected / 1.0e-3, rel=1e-12)


def test_1d_summary_md_renders_high_precision_and_philip(tmp_path: Path) -> None:
    _populate_1d_case_set(tmp_path, nx=800, float_rho=1.0 + 1.0e-7)

    frr._report_1d(tmp_path)
    md = (tmp_path / "summary.md").read_text(encoding="utf-8")

    assert "L1_rho d/f" in md
    assert "L1_rho fmd/d_err" in md
    sod_line = next(line for line in md.splitlines() if line.startswith("| sod "))
    assert "1.192093e-04" in sod_line


def test_2d_report_emits_philip_metric(tmp_path: Path) -> None:
    _write_2d_grid_bin(tmp_path / "reference_800.bin", 800, 800, np.dtype(np.float64), 1.0)
    _write_2d_grid_bin(tmp_path / "double_200.bin", 200, 200, np.dtype(np.float64), 1.0)
    _write_2d_grid_bin(tmp_path / "float_200.bin", 200, 200, np.dtype(np.float32), 1.0 + 1.0e-6)
    _write_2d_grid_bin(tmp_path / "double_400.bin", 400, 400, np.dtype(np.float64), 1.0)
    _write_2d_grid_bin(tmp_path / "float_400.bin", 400, 400, np.dtype(np.float32), 1.0 + 1.0e-6)

    summary = frr._report_2d(
        tmp_path,
        gamma=1.4,
        smooth_sigma=0.5,
        allow_ssim_fallback=True,
    )

    fvd_200 = summary["cases"]["float_200"]["philip"]
    expected = float(np.float32(1.0 + 1.0e-6) - np.float32(1.0))
    assert fvd_200["L1_rho_fmd"] == pytest.approx(expected, rel=1e-12)
    assert fvd_200["L1_rho_ratio"] == float("inf")
