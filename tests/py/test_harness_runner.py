import sys
import time
from pathlib import Path

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
