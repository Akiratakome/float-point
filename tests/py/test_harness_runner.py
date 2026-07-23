import base64
import math
import struct
import sys
import time
from errno import ENOENT
from pathlib import Path

import pytest

from scripts.harness.contracts import RequiredArtifact, RunSpec
from scripts.harness.runner import execute_run, parse_run_status


def test_status_parser_reads_last_structured_line():
    status, completion, failure = parse_run_status(
        "[run-status] status=failed reason=incomplete_run\n"
        "[run-status] status=success final_time=0.1 target_time=0.1 steps=4\n"
    )
    assert status == "success"
    assert completion == {"final_time": 0.1, "target_time": 0.1, "steps": 4}
    assert failure is None


def test_malformed_structured_status_token_is_schema_error():
    status, completion, failure = parse_run_status(
        "[run-status] status=success final_time=0.1 malformed steps=1\n"
    )

    assert status == "failed"
    assert completion is None
    assert failure["category"] == "schema_error"


def test_missing_required_artifact_marks_record_failed(tmp_path: Path):
    cfg = tmp_path / "config.cfg"
    cfg.write_text("x = 1\n", encoding="utf-8")
    spec = RunSpec(
        name="missing-output",
        experiment="pytest",
        command=(sys.executable, "-c", "print('ok')"),
        run_dir=tmp_path / "run",
        source_config=cfg,
        run_config=cfg,
        required_artifacts=(RequiredArtifact(tmp_path / "missing.bin"),),
    )
    record = execute_run(spec)
    assert record.status == "failed"
    assert record.failure["category"] == "artifact_error"


def test_timeout_becomes_infrastructure_failure(tmp_path: Path):
    cfg = tmp_path / "config.cfg"
    cfg.write_text("x = 1\n", encoding="utf-8")
    spec = RunSpec(
        name="timeout",
        experiment="pytest",
        command=(sys.executable, "-c", "import time; time.sleep(1)"),
        run_dir=tmp_path / "run",
        source_config=cfg,
        run_config=cfg,
        timeout_s=0.01,
    )

    record = execute_run(spec)

    assert record.status == "failed"
    assert record.failure["category"] == "infrastructure_error"


def test_stale_required_artifact_marks_record_failed(tmp_path: Path):
    cfg = tmp_path / "config.cfg"
    artifact = tmp_path / "output.bin"
    cfg.write_text("x = 1\n", encoding="utf-8")
    artifact.write_bytes(b"old")
    time.sleep(0.01)
    spec = RunSpec(
        name="stale-output",
        experiment="pytest",
        command=(sys.executable, "-c", "print('ok')"),
        run_dir=tmp_path / "run",
        source_config=cfg,
        run_config=cfg,
        required_artifacts=(RequiredArtifact(artifact),),
    )

    record = execute_run(spec)

    assert record.status == "failed"
    assert record.failure["category"] == "artifact_error"


def test_nonzero_returncode_overrides_structured_success(tmp_path: Path):
    cfg = tmp_path / "config.cfg"
    cfg.write_text("x = 1\n", encoding="utf-8")
    spec = RunSpec(
        name="nonzero-success",
        experiment="pytest",
        command=(
            sys.executable,
            "-c",
            "import sys; print('[run-status] status=success final_time=0.1 target_time=0.1 steps=1', file=sys.stderr); sys.exit(3)",
        ),
        run_dir=tmp_path / "run",
        source_config=cfg,
        run_config=cfg,
    )

    record = execute_run(spec)

    assert record.returncode == 3
    assert record.status == "failed"
    assert record.failure["category"] == "infrastructure_error"


def test_missing_executable_records_structured_launch_failure(tmp_path: Path):
    cfg = tmp_path / "config.cfg"
    missing_binary = tmp_path / "missing-hrsc"
    cfg.write_text("x = 1\n", encoding="utf-8")
    spec = RunSpec(
        name="missing-executable",
        experiment="pytest",
        command=(str(missing_binary),),
        run_dir=tmp_path / "run",
        source_config=cfg,
        run_config=cfg,
    )

    record = execute_run(spec)

    assert record.returncode == -1
    assert record.status == "failed"
    assert record.failure["category"] == "infrastructure_error"
    assert record.failure["exception_type"] == "FileNotFoundError"
    assert record.failure["errno"] == ENOENT
    assert record.failure["strerror"]
    assert record.failure["filename"] == str(missing_binary)


@pytest.mark.parametrize(
    "completion",
    (
        "final_time=nan target_time=1 steps=1",
        "final_time=inf target_time=1 steps=1",
        "final_time=1 target_time=nan steps=1",
        "final_time=1 target_time=inf steps=1",
        "final_time=1 target_time=2 steps=1",
        "final_time=1 target_time=1 steps=-1",
    ),
)
def test_invalid_structured_success_is_schema_error(
    tmp_path: Path, completion: str
):
    cfg = tmp_path / "config.cfg"
    cfg.write_text("x = 1\n", encoding="utf-8")
    status_line = f"[run-status] status=success {completion}"
    spec = RunSpec(
        name="invalid-completion",
        experiment="pytest",
        command=(
            sys.executable,
            "-c",
            "import sys; print(sys.argv[1], file=sys.stderr)",
            status_line,
        ),
        run_dir=tmp_path / "run",
        source_config=cfg,
        run_config=cfg,
    )

    record = execute_run(spec)

    assert record.status == "failed"
    assert record.failure["category"] == "schema_error"


def _hrsc_binary_bytes(
    *, nx: int = 2, ny: int = 1, nvars: int = 4, precision: int = 8,
    time_value: float = 0.0, dx: float = 0.5, dy: float = 1.0,
) -> bytes:
    header = struct.pack(
        "<4siiiiddd20s",
        b"HRSC", nx, ny, nvars, precision, time_value, dx, dy, b"\0" * 20
    )
    return header + b"\0" * (nx * ny * nvars * precision)


def _artifact_writer(path: Path, payload: bytes) -> tuple[str, ...]:
    encoded = base64.b64encode(payload).decode("ascii")
    return (
        sys.executable,
        "-c",
        "import base64, pathlib, sys; pathlib.Path(sys.argv[1]).write_bytes(base64.b64decode(sys.argv[2]))",
        str(path),
        encoded,
    )


def test_valid_hrsc_binary_artifact_passes_parseability_validation(tmp_path: Path):
    cfg = tmp_path / "config.cfg"
    artifact = tmp_path / "grid.bin"
    cfg.write_text("x = 1\n", encoding="utf-8")
    spec = RunSpec(
        name="valid-binary",
        experiment="pytest",
        command=_artifact_writer(artifact, _hrsc_binary_bytes()),
        run_dir=tmp_path / "run",
        source_config=cfg,
        run_config=cfg,
        required_artifacts=(RequiredArtifact(artifact, kind="hrsc_binary"),),
    )

    record = execute_run(spec)

    assert record.status == "success"


def test_truncated_hrsc_binary_is_artifact_error(tmp_path: Path):
    cfg = tmp_path / "config.cfg"
    artifact = tmp_path / "grid.bin"
    cfg.write_text("x = 1\n", encoding="utf-8")
    spec = RunSpec(
        name="truncated-binary",
        experiment="pytest",
        command=_artifact_writer(artifact, _hrsc_binary_bytes()[:-1]),
        run_dir=tmp_path / "run",
        source_config=cfg,
        run_config=cfg,
        required_artifacts=(RequiredArtifact(artifact, kind="hrsc_binary"),),
    )

    record = execute_run(spec)

    assert record.status == "failed"
    assert record.failure["category"] == "artifact_error"


@pytest.mark.parametrize(
    "mutation",
    (
        "magic",
        "dimensions",
        "variables",
        "precision",
        "time",
        "dx_nonfinite",
        "dy_nonfinite",
        "dx_nonpositive",
        "dy_nonpositive",
    ),
)
def test_hrsc_binary_artifact_rejects_invalid_header(tmp_path: Path, mutation: str):
    cfg = tmp_path / "config.cfg"
    artifact = tmp_path / "grid.bin"
    cfg.write_text("x = 1\n", encoding="utf-8")
    payload = bytearray(_hrsc_binary_bytes())
    if mutation == "magic":
        payload[:4] = b"NOPE"
    elif mutation == "dimensions":
        payload = bytearray(_hrsc_binary_bytes(nx=0))
    elif mutation == "variables":
        payload = bytearray(_hrsc_binary_bytes(nvars=0))
    elif mutation == "precision":
        payload = bytearray(_hrsc_binary_bytes(precision=2))
    elif mutation == "time":
        payload = bytearray(_hrsc_binary_bytes(time_value=math.inf))
    elif mutation == "dx_nonfinite":
        payload = bytearray(_hrsc_binary_bytes(dx=math.nan))
    elif mutation == "dy_nonfinite":
        payload = bytearray(_hrsc_binary_bytes(dy=math.inf))
    elif mutation == "dx_nonpositive":
        payload = bytearray(_hrsc_binary_bytes(dx=0.0))
    elif mutation == "dy_nonpositive":
        payload = bytearray(_hrsc_binary_bytes(dy=-1.0))

    spec = RunSpec(
        name=f"invalid-{mutation}",
        experiment="pytest",
        command=_artifact_writer(artifact, bytes(payload)),
        run_dir=tmp_path / "run",
        source_config=cfg,
        run_config=cfg,
        required_artifacts=(RequiredArtifact(artifact, kind="hrsc_binary"),),
    )

    record = execute_run(spec)

    assert record.status == "failed"
    assert record.failure["category"] == "artifact_error"


def test_unknown_artifact_kind_fails_closed(tmp_path: Path):
    cfg = tmp_path / "config.cfg"
    cfg.write_text("x = 1\n", encoding="utf-8")
    spec = RunSpec(
        name="unknown-artifact",
        experiment="pytest",
        command=(sys.executable, "-c", "print('ok')"),
        run_dir=tmp_path / "run",
        source_config=cfg,
        run_config=cfg,
        required_artifacts=(RequiredArtifact(tmp_path / "output", kind="unknown"),),
    )

    record = execute_run(spec)

    assert record.status == "failed"
    assert record.failure["category"] == "artifact_error"
    assert "unknown artifact kind" in record.failure["message"]


def test_artifact_filesystem_error_is_artifact_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    cfg = tmp_path / "config.cfg"
    artifact = tmp_path / "grid.bin"
    cfg.write_text("x = 1\n", encoding="utf-8")
    original_is_file = Path.is_file

    def raise_for_artifact(path: Path) -> bool:
        if path == artifact:
            raise OSError("simulated artifact filesystem failure")
        return original_is_file(path)

    monkeypatch.setattr(Path, "is_file", raise_for_artifact)
    spec = RunSpec(
        name="artifact-filesystem-error",
        experiment="pytest",
        command=(sys.executable, "-c", "print('ok')"),
        run_dir=tmp_path / "run",
        source_config=cfg,
        run_config=cfg,
        required_artifacts=(RequiredArtifact(artifact, kind="hrsc_binary"),),
    )

    record = execute_run(spec)

    assert record.status == "failed"
    assert record.failure["category"] == "artifact_error"
