from __future__ import annotations

import csv
import json
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "regression"))

import float_regression_report as frr  # noqa: E402


DEVICE_COLUMNS = [
    "pair_a",
    "pair_b",
    "precision",
    "l1_a_minus_b",
    "linf_a_minus_b",
    "philip_ratio",
    "ulp_max",
    "gate_passed",
    "notes",
]


def _write_binary(path: Path, cons: np.ndarray, dx: float = 1.0, dy: float = 1.0) -> None:
    ny, nx, nvars = cons.shape
    header = struct.pack(
        "<4siiiiddd20s",
        b"HRSC",
        nx,
        ny,
        nvars,
        cons.dtype.itemsize,
        0.0,
        dx,
        dy,
        b"\x00" * 20,
    )
    assert len(header) == 64
    with open(path, "wb") as f:
        f.write(header)
        f.write(cons.tobytes(order="C"))


def _conserved_payload(nx: int, dtype: np.dtype) -> np.ndarray:
    base = np.linspace(0.5, 1.5, nx * 4, dtype=np.float64).reshape(1, nx, 4)
    return base.astype(dtype)


def test_device_mode_passes_when_diff_is_8_eps(tmp_path: Path) -> None:
    cpu = _conserved_payload(64, np.dtype(np.float64))
    eps = np.finfo(np.float64).eps
    gpu = cpu + 8.0 * eps * np.abs(cpu)
    cpu_path = tmp_path / "sod_cpu.bin"
    gpu_path = tmp_path / "sod_gpu.bin"
    _write_binary(cpu_path, cpu)
    _write_binary(gpu_path, gpu)

    result = frr._report_device_pair(cpu_path, gpu_path, precision="double")

    assert result["gate_passed"] is True
    assert result["ulp_max"] <= 16.0
    assert result["pair_a"] == str(cpu_path)
    assert result["pair_b"] == str(gpu_path)


def test_device_mode_fails_when_diff_is_64_eps(tmp_path: Path) -> None:
    cpu = _conserved_payload(64, np.dtype(np.float64))
    eps = np.finfo(np.float64).eps
    gpu = cpu + 64.0 * eps * np.abs(cpu)
    cpu_path = tmp_path / "case_cpu.bin"
    gpu_path = tmp_path / "case_gpu.bin"
    _write_binary(cpu_path, cpu)
    _write_binary(gpu_path, gpu)

    result = frr._report_device_pair(cpu_path, gpu_path, precision="double")

    assert result["gate_passed"] is False
    assert result["ulp_max"] > 16.0


def test_device_mode_cli_writes_complete_csv_columns(tmp_path: Path) -> None:
    cpu = _conserved_payload(16, np.dtype(np.float32))
    eps = np.finfo(np.float32).eps
    gpu = cpu + 8.0 * eps * np.abs(cpu)
    cpu_path = tmp_path / "sod_cpu.bin"
    gpu_path = tmp_path / "sod_gpu.bin"
    output_prefix = tmp_path / "summary"
    _write_binary(cpu_path, cpu)
    _write_binary(gpu_path, gpu.astype(np.float32))

    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "regression" / "float_regression_report.py"),
            "--mode",
            "device",
            "--inputs",
            str(cpu_path),
            str(gpu_path),
            "--precision",
            "float",
            "--output",
            str(output_prefix),
        ],
        check=True,
        cwd=REPO_ROOT,
    )

    csv_path = output_prefix.with_suffix(".csv")
    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    assert csv_path.is_file()
    assert json_path.is_file()
    assert md_path.is_file()

    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows
    assert rows[0].keys() == set(DEVICE_COLUMNS)
    for column in DEVICE_COLUMNS:
        assert rows[0][column] not in ("", "None", "nan")

    summary = json.loads(json_path.read_text(encoding="utf-8"))
    assert summary["mode"] == "device"
    assert summary["rows"][0]["gate_passed"] is True


def test_device_mode_pairs_week6_run_directory_layout(tmp_path: Path) -> None:
    cpu = _conserved_payload(8, np.dtype(np.float64))
    gpu = cpu + 4.0 * np.finfo(np.float64).eps * np.abs(cpu)
    cpu_path = tmp_path / "runs" / "sod-cpu-strict-d" / "sod.bin"
    gpu_path = tmp_path / "runs" / "sod-gpu-strict-d" / "sod.bin"
    cpu_path.parent.mkdir(parents=True)
    gpu_path.parent.mkdir(parents=True)
    _write_binary(cpu_path, cpu)
    _write_binary(gpu_path, gpu)

    rows = frr._report_device(
        [cpu_path, gpu_path],
        tmp_path / "summary",
        precision="double",
        reference_path=None,
    )["rows"]

    assert len(rows) == 1
    assert rows[0]["pair_a"] == str(cpu_path)
    assert rows[0]["pair_b"] == str(gpu_path)
    assert rows[0]["gate_passed"] is True


def test_device_mode_exact_reference_marks_ratio_not_applicable(tmp_path: Path) -> None:
    cpu = _conserved_payload(8, np.dtype(np.float64))
    gpu = cpu + 4.0 * np.finfo(np.float64).eps * np.abs(cpu)
    cpu_path = tmp_path / "sod_cpu.bin"
    gpu_path = tmp_path / "sod_gpu.bin"
    _write_binary(cpu_path, cpu)
    _write_binary(gpu_path, gpu)

    row = frr._report_device(
        [cpu_path, gpu_path],
        tmp_path / "summary",
        precision="double",
        reference_path=Path("exact"),
    )["rows"][0]

    assert row["philip_ratio"] is None
    assert row["notes"] == "reference_exact_not_available"


def test_device_mode_stationary_contact_uses_four_ulp_gate(tmp_path: Path) -> None:
    cpu = _conserved_payload(8, np.dtype(np.float64))
    gpu = cpu + 8.0 * np.finfo(np.float64).eps * np.abs(cpu)
    cpu_path = tmp_path / "stationary_contact_cpu.bin"
    gpu_path = tmp_path / "stationary_contact_gpu.bin"
    _write_binary(cpu_path, cpu)
    _write_binary(gpu_path, gpu)

    row = frr._report_device_pair(cpu_path, gpu_path, precision="double")

    assert row["ulp_max"] > 4.0
    assert row["gate_passed"] is False
    assert "gate_ulp=4" in row["notes"]


def test_device_mode_infers_precision_per_pair_from_binary_headers(tmp_path: Path) -> None:
    cpu_double = _conserved_payload(8, np.dtype(np.float64))
    gpu_double = cpu_double.copy()
    cpu_float = _conserved_payload(8, np.dtype(np.float32))
    gpu_float = cpu_float.copy()
    paths = [
        tmp_path / "runs" / "sod-cpu-strict-d" / "sod.bin",
        tmp_path / "runs" / "sod-gpu-strict-d" / "sod.bin",
        tmp_path / "runs" / "sod-cpu-strict-f" / "sod.bin",
        tmp_path / "runs" / "sod-gpu-strict-f" / "sod.bin",
    ]
    for path, payload in zip(paths, (cpu_double, gpu_double, cpu_float, gpu_float)):
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_binary(path, payload)

    rows = frr._report_device(
        paths,
        tmp_path / "summary",
        precision=None,
        reference_path=None,
    )["rows"]

    assert [row["precision"] for row in rows] == ["double", "float"]
