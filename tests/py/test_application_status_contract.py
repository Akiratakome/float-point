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


def _function_body(source: str, name: str) -> str:
    match = re.search(rf"static void {name}\(const Config& cfg\) \{{", source)
    assert match, f"missing {name}"
    start = match.start()
    next_function = source.find("\nstatic void ", start + 1)
    if next_function < 0:
        next_function = len(source)
    return source[start:next_function]


def test_cpu_euler_run_emits_success_status(tmp_path: Path) -> None:
    binary = _hrsc_binary()
    cfg = tmp_path / "sod-zero-time.cfg"
    cfg.write_text(
        "\n".join(
            (
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
                "output_format = table",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(binary), str(cfg)], capture_output=True, text=True, check=False
    )

    assert result.returncode == 0, result.stderr
    assert "[run-status] status=success final_time=0 target_time=0 steps=0" in result.stderr


def test_final_euler_binary_outputs_follow_completion_gate() -> None:
    source = (ROOT / "src" / "main.cpp").read_text(encoding="utf-8")
    for name in ("run_normal", "run_normal_gpu"):
        body = _function_body(source, name)
        binary_writes = list(re.finditer(r"write_binary<Real, EulerNVars>", body))
        assert binary_writes, f"{name} has no final binary output"
        for write in binary_writes:
            assert body.rfind("require_run_complete", 0, write.start()) >= 0, (
                f"{name} writes a final binary before proving completion"
            )
