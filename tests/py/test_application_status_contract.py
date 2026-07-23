from __future__ import annotations

import re
import subprocess
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _application_source_dependencies(
    root: Path, *, target: str
) -> tuple[Path, ...]:
    dependencies = {root / "CMakeLists.txt"}
    dependencies.update(path for path in (root / "cmake").rglob("*") if path.is_file())
    target_roots = {
        "hrsc": ((root / "src" / "app"), (root / "src" / "core"),
                 (root / "src" / "euler"), (root / "src" / "utils")),
        "hrsc_mhd": ((root / "src" / "app"), (root / "src" / "core"),
                     (root / "src" / "mhd")),
    }
    if target not in target_roots:
        raise ValueError(f"unknown application target: {target}")
    source_suffixes = {".c", ".cc", ".cpp", ".cu", ".cuh", ".h", ".hpp"}
    dependencies.update(
        path
        for source_root in target_roots[target]
        for path in source_root.rglob("*")
        if path.is_file() and path.suffix.lower() in source_suffixes
    )
    entrypoint = root / "src" / ("main.cpp" if target == "hrsc" else "mhd_main.cpp")
    if entrypoint.is_file():
        dependencies.add(entrypoint)
    return tuple(sorted(dependencies, key=lambda path: path.as_posix()))


def _select_binary(
    *, env_name: str, candidates: tuple[Path, ...], sources: tuple[Path, ...]
) -> Path:
    override = os.environ.get(env_name)
    if override:
        selected = Path(override)
        if not selected.is_file():
            pytest.fail(f"{env_name} does not name a file: {selected}")
    else:
        available = [candidate for candidate in candidates if candidate.is_file()]
        if not available:
            pytest.skip(f"no built executable found for {env_name}")
        selected = max(available, key=lambda candidate: candidate.stat().st_mtime)

    newest_source = max(source.stat().st_mtime for source in sources)
    if selected.stat().st_mtime < newest_source:
        pytest.fail(
            f"stale executable for {env_name}: {selected}; rebuild it because it predates "
            "the reviewed application sources"
        )
    return selected


def _hrsc_binary() -> Path:
    return _select_binary(
        env_name="HRSC_TEST_HRSC_BINARY",
        candidates=(
            ROOT / "build-double" / "Release" / "hrsc.exe",
            ROOT / "build-double" / "Release" / "hrsc",
            ROOT / "build-double" / "hrsc.exe",
            ROOT / "build-double" / "hrsc",
        ),
        sources=_application_source_dependencies(ROOT, target="hrsc"),
    )


def _hrsc_mhd_binary() -> Path:
    return _select_binary(
        env_name="HRSC_TEST_HRSC_MHD_BINARY",
        candidates=(
            ROOT / "build-double" / "Release" / "hrsc_mhd.exe",
            ROOT / "build-double" / "Release" / "hrsc_mhd",
            ROOT / "build-double" / "hrsc_mhd.exe",
            ROOT / "build-double" / "hrsc_mhd",
        ),
        sources=_application_source_dependencies(ROOT, target="hrsc_mhd"),
    )


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

    success = path.find("write_run_success", output)
    completion = path.rfind("require_run_complete", 0, output)
    advance = path.rfind("advance_solver", 0, completion)

    assert advance >= 0, f"{label} has no solver advance before final output"
    assert completion >= 0, f"{label} has no completion gate before final output"
    assert success >= 0, f"{label} has no success status after final output"
    assert advance < completion < output < success, f"{label} final output ordering changed"


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


def test_cpu_euler_binary_write_failure_is_an_artifact_error(tmp_path: Path) -> None:
    binary = _hrsc_binary()
    output_directory = tmp_path / "euler-output-directory"
    output_directory.mkdir()
    cfg = tmp_path / "euler-artifact-error.cfg"
    cfg.write_text(
        _zero_time_sod_cfg(output_format="binary", output_file=output_directory),
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(binary), str(cfg)], capture_output=True, text=True, check=False
    )

    assert result.returncode == 2, result.stderr
    assert "[run-status] status=failed reason=artifact_error" in result.stderr
    assert "status=success" not in result.stderr
    assert output_directory.is_dir()


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


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("xmin", "nan"),
        ("xmax", "inf"),
        ("ymin", "-inf"),
        ("ymax", "inf"),
        ("x0", "nan"),
        ("glm_cr", "inf"),
    ),
)
def test_mhd_non_finite_config_is_a_structured_configuration_error(
    tmp_path: Path, key: str, value: str
) -> None:
    binary = _hrsc_mhd_binary()
    output_file = tmp_path / f"mhd-nonfinite-{key}.bin"
    cfg = tmp_path / f"mhd-nonfinite-{key}.cfg"
    cfg.write_text(
        _zero_time_mhd_cfg(output_file=output_file) + f"{key} = {value}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(binary), str(cfg)], capture_output=True, text=True, check=False
    )

    assert result.returncode == 2, result.stderr
    assert "[run-status] status=failed reason=configuration_error" in result.stderr
    assert "reason=numerical_failure" not in result.stderr
    assert "status=success" not in result.stderr
    assert not output_file.exists()


def test_mhd_binary_write_failure_is_an_artifact_error(tmp_path: Path) -> None:
    binary = _hrsc_mhd_binary()
    output_directory = tmp_path / "mhd-output-directory"
    output_directory.mkdir()
    cfg = tmp_path / "mhd-artifact-error.cfg"
    cfg.write_text(
        _zero_time_mhd_cfg(output_file=output_directory), encoding="utf-8"
    )

    result = subprocess.run(
        [str(binary), str(cfg)], capture_output=True, text=True, check=False
    )

    assert result.returncode == 2, result.stderr
    assert "[run-status] status=failed reason=artifact_error" in result.stderr
    assert "status=success" not in result.stderr
    assert output_directory.is_dir()


def test_binary_locator_prefers_newest_fresh_candidate_and_honors_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.cpp"
    root_candidate = tmp_path / "root.exe"
    release_candidate = tmp_path / "Release" / "app.exe"
    release_candidate.parent.mkdir()
    source.write_text("source", encoding="utf-8")
    root_candidate.write_text("root", encoding="utf-8")
    release_candidate.write_text("release", encoding="utf-8")

    now = source.stat().st_mtime
    os.utime(root_candidate, (now + 1, now + 1))
    os.utime(release_candidate, (now + 2, now + 2))
    selected = _select_binary(
        env_name="HRSC_TEST_LOCATOR_BINARY",
        candidates=(release_candidate, root_candidate),
        sources=(source,),
    )
    assert selected == release_candidate

    monkeypatch.setenv("HRSC_TEST_LOCATOR_BINARY", str(root_candidate))
    assert _select_binary(
        env_name="HRSC_TEST_LOCATOR_BINARY",
        candidates=(release_candidate, root_candidate),
        sources=(source,),
    ) == root_candidate


def test_binary_locator_rejects_stale_candidate(tmp_path: Path) -> None:
    candidate = tmp_path / "old.exe"
    source = tmp_path / "new.cpp"
    candidate.write_text("candidate", encoding="utf-8")
    source.write_text("source", encoding="utf-8")
    old = source.stat().st_mtime - 10
    os.utime(candidate, (old, old))

    with pytest.raises(pytest.fail.Exception, match="stale executable"):
        _select_binary(
            env_name="HRSC_TEST_STALE_BINARY",
            candidates=(candidate,),
            sources=(source,),
        )


def test_application_source_dependencies_are_dynamic_and_include_cmake_inputs(
    tmp_path: Path,
) -> None:
    (tmp_path / "src" / "app").mkdir(parents=True)
    (tmp_path / "cmake").mkdir()
    (tmp_path / "src" / "app" / "new_source.cpp").write_text("source", encoding="utf-8")
    (tmp_path / "src" / "app" / "new_header.hpp").write_text("header", encoding="utf-8")
    (tmp_path / "cmake" / "new_flags.cmake").write_text("flags", encoding="utf-8")
    (tmp_path / "CMakeLists.txt").write_text("cmake", encoding="utf-8")

    dependencies = _application_source_dependencies(tmp_path, target="hrsc")

    assert tmp_path / "src" / "app" / "new_source.cpp" in dependencies
    assert tmp_path / "src" / "app" / "new_header.hpp" in dependencies
    assert tmp_path / "cmake" / "new_flags.cmake" in dependencies
    assert tmp_path / "CMakeLists.txt" in dependencies


def test_binary_locator_rejects_new_dynamic_application_source(tmp_path: Path) -> None:
    candidate = tmp_path / "app.exe"
    candidate.write_text("candidate", encoding="utf-8")
    (tmp_path / "src" / "app").mkdir(parents=True)
    (tmp_path / "cmake").mkdir()
    (tmp_path / "CMakeLists.txt").write_text("cmake", encoding="utf-8")
    source = tmp_path / "src" / "app" / "new_source.cpp"
    source.write_text("source", encoding="utf-8")
    old = source.stat().st_mtime - 10
    os.utime(candidate, (old, old))

    with pytest.raises(pytest.fail.Exception, match="stale executable"):
        _select_binary(
            env_name="HRSC_TEST_DYNAMIC_STALE_BINARY",
            candidates=(candidate,),
            sources=_application_source_dependencies(tmp_path, target="hrsc"),
        )


def test_binary_locator_rejects_binary_older_than_a_touched_header(
    tmp_path: Path
) -> None:
    candidate = tmp_path / "hrsc_mhd.exe"
    header = tmp_path / "mhd_result.hpp"
    candidate.write_text("candidate", encoding="utf-8")
    header.write_text("header", encoding="utf-8")
    old = header.stat().st_mtime - 10
    os.utime(candidate, (old, old))
    header.touch()

    with pytest.raises(pytest.fail.Exception, match="stale executable"):
        _select_binary(
            env_name="HRSC_TEST_STALE_HEADER_BINARY",
            candidates=(candidate,),
            sources=(header,),
        )


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


def test_cuda_guard_closes_run_normal_gpu_once() -> None:
    source = (ROOT / "src" / "main.cpp").read_text(encoding="utf-8")
    start = source.index("static void run_normal_gpu")
    _, end = _braced_block(source, start)
    guard_end = source.index("#endif // HRSC_HAS_CUDA", end)

    assert source[end:guard_end].strip() == ""


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
