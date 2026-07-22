from pathlib import Path

import pytest

from scripts.harness.contracts import (
    BuildSemantics,
    FailureCategory,
    RequiredArtifact,
    RunRecord,
    RunSpec,
)
from scripts.harness.metadata import (
    normalise_metadata,
    require_successful_metadata,
    serialise_record,
)


def test_legacy_aliases_normalise_without_rewrite():
    raw = {
        "name": "legacy",
        "returncode": 0,
        "output_binary": "grid.bin",
        "elapsed_wall_s": 1.25,
    }
    canonical = normalise_metadata(raw)
    assert canonical["schema"] == {"name": "hrsc.run-record", "version": 1}
    assert canonical["status"] == "success"
    assert canonical["artifacts"]["primary_output"] == "grid.bin"
    assert canonical["timing"]["elapsed_wall_s"] == 1.25


def test_failed_canonical_record_is_rejected():
    raw = {
        "schema": {"name": "hrsc.run-record", "version": 1},
        "status": "failed",
        "failure": {"category": "incomplete_run", "message": "stopped early"},
        "returncode": 2,
    }
    with pytest.raises(ValueError, match="incomplete_run"):
        require_successful_metadata(raw)


def test_normalise_rejects_unknown_schema_name_and_future_version():
    with pytest.raises(ValueError, match="schema name"):
        normalise_metadata({"schema": {"name": "other", "version": 1}})
    with pytest.raises(ValueError, match="version"):
        normalise_metadata(
            {"schema": {"name": "hrsc.run-record", "version": 2}}
        )


def test_normalise_prefers_canonical_aliases_and_does_not_mutate_input():
    raw = {
        "schema": {"name": "hrsc.run-record", "version": 1},
        "returncode": 0,
        "status": "success",
        "artifacts": {"primary_output": "canonical.bin"},
        "raw_output": "raw.bin",
        "output_binary": "legacy.bin",
        "timing": {"elapsed_wall_s": 2.5, "total_s": 3.5},
        "elapsed_wall_s": 4.5,
    }
    original = raw.copy()
    canonical = normalise_metadata(raw)
    assert canonical["artifacts"]["primary_output"] == "canonical.bin"
    assert canonical["timing"]["elapsed_wall_s"] == 2.5
    assert raw == original
    assert canonical is not raw


def test_normalise_uses_raw_output_and_total_time_fallbacks():
    canonical = normalise_metadata(
        {"returncode": 0, "raw_output": "raw.bin", "timing": {"total_s": 3.5}}
    )
    assert canonical["artifacts"]["primary_output"] == "raw.bin"
    assert canonical["timing"]["elapsed_wall_s"] == 3.5


def test_serialise_record_adds_canonical_fields_and_preserves_legacy_fields(tmp_path):
    spec = RunSpec(
        name="run-1",
        experiment="smoke",
        command=("hrsc", "config.cfg"),
        run_dir=tmp_path / "run-1",
        source_config=tmp_path / "source.cfg",
        run_config=tmp_path / "config.cfg",
        required_artifacts=(RequiredArtifact(tmp_path / "grid.bin"),),
        build_semantics=BuildSemantics(
            requested_opt_level="O2", effective_math_mode="strict-ieee"
        ),
    )
    record = RunRecord(
        spec=spec,
        returncode=0,
        elapsed_wall_s=1.25,
        stdout_path=tmp_path / "stdout.txt",
        stderr_path=tmp_path / "stderr.txt",
        status="success",
        completion={"reported": True, "steps": 4},
    )
    output = serialise_record(record, {"name": "legacy", "precision": "double"})
    assert output["name"] == "legacy"
    assert output["precision"] == "double"
    assert output["schema"] == {"name": "hrsc.run-record", "version": 1}
    assert output["status"] == "success"
    assert output["returncode"] == 0
    assert output["timing"]["elapsed_wall_s"] == 1.25
    assert output["completion"] == {"reported": True, "steps": 4}
    assert output["build_semantics"]["requested_opt_level"] == "O2"


def test_successful_metadata_is_returned_in_canonical_form():
    canonical = require_successful_metadata({"returncode": 0})
    assert canonical["status"] == "success"


def test_require_successful_metadata_names_failure_category():
    with pytest.raises(ValueError, match="numerical_failure"):
        require_successful_metadata(
            {
                "status": "failed",
                "failure": {
                    "category": FailureCategory.NUMERICAL.value,
                    "message": "nan",
                },
            }
        )

