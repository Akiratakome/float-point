import sys
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
