from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _hrsc_binary() -> Path:
    candidates = (
        ROOT / "build-double" / "hrsc.exe",
        ROOT / "build-double" / "hrsc",
        ROOT / "build-double" / "Release" / "hrsc.exe",
        ROOT / "build-double" / "Release" / "hrsc",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    pytest.skip("no built hrsc executable in build-double or build-double/Release")


def _hrsc_mhd_binary() -> Path:
    candidates = (
        ROOT / "build-double" / "hrsc_mhd.exe",
        ROOT / "build-double" / "hrsc_mhd",
        ROOT / "build-double" / "Release" / "hrsc_mhd.exe",
        ROOT / "build-double" / "Release" / "hrsc_mhd",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    pytest.skip("no built hrsc_mhd executable in build-double or build-double/Release")


def _braced_block(source: str, start: int) -> tuple[str, int]:
    opening = source.find("{", start)
    assert opening >= 0, "missing opening brace"
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1], index + 1
    raise AssertionError("missing closing brace")


def _function_body(source: str, name: str) -> str:
    match = re.search(rf"static void {name}\(const Config& cfg\) \{{", source)
    assert match, f"missing {name}"
    body, _ = _braced_block(source, match.start())
    return body


def _zero_time_sod_cfg(*, output_format: str, output_file: Path | None = None) -> str:
    lines = [
        "test = sod",
        "nx = 8",
        "xmin = 0.0",
        "xmax = 1.0",
        "gamma = 1.4",
        "cfl = 0.8",
        "t_end = 0",
        "bc = outflow",
        "solver = hllc",
        "mode = normal",
        f"output_format = {output_format}",
    ]
    if output_file is not None:
        lines.append(f"output_file = {output_file}")
    return "\n".join(lines) + "\n"


def _zero_time_mhd_cfg(*, output_file: Path, device: str = "cpu") -> str:
    return "\n".join(
        (
            "test = brio_wu",
            "nx = 8",
            "ny = 1",
            "xmin = 0.0",
            "xmax = 1.0",
            "gamma = 2.0",
            "cfl = 0.4",
            "t_end = 0",
            "x0 = 0.5",
            "glm_cr = 0",
            "riemann = hll",
            "bc = outflow",
            f"device = {device}",
            f"output_file = {output_file}",
        )
    ) + "\n"


def _assert_path_local_output_order(path: str, output_marker: str, label: str) -> None:
    output = path.find(output_marker)
    assert output >= 0, f"{label} is missing {output_marker}"
    assert path.count(output_marker) == 1, f"{label} has an unexpected {output_marker} count"

    success = path.rfind("write_run_success", 0, output)
    completion = path.rfind("require_run_complete", 0, success)
    advance = path.rfind("advance_solver", 0, completion)

    assert advance >= 0, f"{label} has no solver advance before final output"
    assert completion >= 0, f"{label} has no completion gate before final output"
    assert success >= 0, f"{label} has no success status before final output"
    assert advance < completion < success < output, f"{label} final output ordering changed"


def test_cpu_euler_run_emits_success_status(tmp_path: Path) -> None:
    binary = _hrsc_binary()
    cfg = tmp_path / "sod-zero-time.cfg"
    cfg.write_text(_zero_time_sod_cfg(output_format="table"), encoding="utf-8")

    result = subprocess.run(
        [str(binary), str(cfg)], capture_output=True, text=True, check=False
    )

    assert result.returncode == 0, result.stderr
    assert "[run-status] status=success final_time=0 target_time=0 steps=0" in result.stderr


def test_cpu_euler_binary_run_writes_artifact_after_success(tmp_path: Path) -> None:
    binary = _hrsc_binary()
    output_file = tmp_path / "sod-zero-time.bin"
    cfg = tmp_path / "sod-zero-time-binary.cfg"
    cfg.write_text(
        _zero_time_sod_cfg(output_format="binary", output_file=output_file),
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(binary), str(cfg)], capture_output=True, text=True, check=False
    )

    assert result.returncode == 0, result.stderr
    assert "[run-status] status=success final_time=0 target_time=0 steps=0" in result.stderr
    assert output_file.is_file()


def test_cpu_mhd_run_emits_success_status_and_legacy_binary(tmp_path: Path) -> None:
    binary = _hrsc_mhd_binary()
    output_file = tmp_path / "mhd-zero-time.bin"
    cfg = tmp_path / "mhd-zero-time.cfg"
    cfg.write_text(_zero_time_mhd_cfg(output_file=output_file), encoding="utf-8")

    result = subprocess.run(
        [str(binary), str(cfg)], capture_output=True, text=True, check=False
    )

    assert result.returncode == 0, result.stderr
    assert "[run-status] status=success final_time=0 target_time=0 steps=0" in result.stderr
    assert output_file.is_file()


def test_mhd_gpu_rejection_is_structured_and_writes_no_binary(tmp_path: Path) -> None:
    binary = _hrsc_mhd_binary()
    output_file = tmp_path / "mhd-gpu-rejected.bin"
    cfg = tmp_path / "mhd-gpu-rejected.cfg"
    cfg.write_text(
        _zero_time_mhd_cfg(output_file=output_file, device="gpu"), encoding="utf-8"
    )

    result = subprocess.run(
        [str(binary), str(cfg)], capture_output=True, text=True, check=False
    )

    assert result.returncode == 2, result.stderr
    assert "[run-status] status=failed reason=unsupported_capability" in result.stderr
    assert not output_file.exists()


def test_every_final_euler_output_path_follows_completion_contract() -> None:
    source = (ROOT / "src" / "main.cpp").read_text(encoding="utf-8")
    cpu = _function_body(source, "run_normal")
    cpu_2d, cpu_2d_end = _braced_block(cpu, cpu.index("if (ny > 1) {"))
    cpu_1d = cpu[cpu_2d_end:]
    gpu = _function_body(source, "run_normal_gpu")

    paths = (
        ("CPU 2D", cpu_2d, 3),
        ("CPU 1D", cpu_1d, 3),
        ("GPU", gpu, 1),
    )
    for label, path, expected_advances in paths:
        assert path.count("advance_solver") == expected_advances, (
            f"{label} solver-advance paths changed unexpectedly"
        )
        assert path.count("require_run_complete") == 1, (
            f"{label} must have exactly one completion gate"
        )
        assert path.count("write_run_success") == 1, (
            f"{label} must have exactly one success status writer"
        )
        _assert_path_local_output_order(
            path, "write_binary<Real, EulerNVars>", f"{label} binary output"
        )
        _assert_path_local_output_order(
            path, "std::cout << std::setprecision(out_prec);", f"{label} table output"
        )

    # Checkpoint and diagnostic dumps are delegated to their dedicated helpers,
    # so their writes are deliberately excluded from authoritative final paths.
    assert "run_with_binary_checkpoints" in cpu_2d
    assert "run_with_binary_checkpoints" in cpu_1d
    assert "run_with_diagnostics" in cpu_2d
    assert "run_with_diagnostics" in cpu_1d
    assert "checkpoint_output_file" not in source
    assert "write_diagnostic_dump" not in source


def test_mhd_result_follows_completion_contract() -> None:
    source = (ROOT / "src" / "mhd_main.cpp").read_text(encoding="utf-8")
    start = source.index("int run_mhd(")
    run_mhd, _ = _braced_block(source, start)

    advance = run_mhd.index("advance_solver")
    completion = run_mhd.index("require_run_complete")
    result = run_mhd.index("write_mhd_result")
    success = run_mhd.index("write_run_success")

    assert run_mhd.count("require_run_complete") == 1
    assert run_mhd.count("write_run_success") == 1
    assert advance < completion < result < success
