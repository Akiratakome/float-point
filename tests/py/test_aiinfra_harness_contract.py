from __future__ import annotations

import json
from pathlib import Path

import pytest


def _cfg(tmp_path: Path) -> Path:
    path = tmp_path / "case.cfg"
    path.write_text("test = sod\nnx = 4\n", encoding="utf-8")
    return path


def test_run_without_arguments_builds_the_legacy_two_token_command(tmp_path: Path) -> None:
    """The HRSC path must stay byte-identical: (binary, config), nothing else."""
    from scripts import run_matrix

    run = run_matrix.normalise_run(
        {"name": "sod", "binary": "build-double/hrsc", "config": str(_cfg(tmp_path))},
        output_root=tmp_path / "out",
    )
    config = run_matrix.materialise_run_config(run)

    assert run.arguments == ()
    assert run_matrix.build_command(run, config) == (str(run.binary), str(config))


def test_arguments_are_inserted_between_binary_and_config(tmp_path: Path) -> None:
    from scripts import run_matrix

    run = run_matrix.normalise_run(
        {
            "name": "workload",
            "binary": "python",
            "arguments": ["scripts/aiinfra/run_workload.py", "--strict"],
            "config": str(_cfg(tmp_path)),
        },
        output_root=tmp_path / "out",
    )
    config = run_matrix.materialise_run_config(run)

    assert run_matrix.build_command(run, config) == (
        "python",
        "scripts/aiinfra/run_workload.py",
        "--strict",
        str(config),
    )


@pytest.mark.parametrize("bad", ("not-a-list", [1, 2], [None]))
def test_non_string_arguments_are_rejected(tmp_path: Path, bad) -> None:
    from scripts import run_matrix

    with pytest.raises(ValueError, match="arguments"):
        run_matrix.normalise_run(
            {"name": "bad", "binary": "b", "config": str(_cfg(tmp_path)), "arguments": bad},
            output_root=tmp_path / "out",
        )


def test_default_config_filename_is_config_cfg(tmp_path: Path) -> None:
    from scripts import run_matrix

    run = run_matrix.normalise_run(
        {"name": "sod", "binary": "b", "config": str(_cfg(tmp_path))},
        output_root=tmp_path / "out",
    )
    assert run_matrix.materialise_run_config(run).name == "config.cfg"


def test_json_config_is_copied_verbatim_under_its_own_name(tmp_path: Path) -> None:
    from scripts import run_matrix

    source = tmp_path / "workload.json"
    source.write_text('{"backend": "fake"}\n', encoding="utf-8")

    run = run_matrix.normalise_run(
        {
            "name": "workload",
            "binary": "python",
            "config": str(source),
            "config_filename": "config.json",
        },
        output_root=tmp_path / "out",
    )
    target = run_matrix.materialise_run_config(run)

    assert target.name == "config.json"
    assert target.read_text(encoding="utf-8") == '{"backend": "fake"}\n'
    assert json.loads(target.read_text(encoding="utf-8")) == {"backend": "fake"}


def test_cfg_overrides_on_a_json_config_fail_closed(tmp_path: Path) -> None:
    from scripts import run_matrix

    source = tmp_path / "workload.json"
    source.write_text('{"backend": "fake"}\n', encoding="utf-8")

    run = run_matrix.normalise_run(
        {
            "name": "workload",
            "binary": "python",
            "config": str(source),
            "config_filename": "config.json",
            "extra_cfg": {"nx": "8"},
        },
        output_root=tmp_path / "out",
    )
    with pytest.raises(ValueError, match="config_filename"):
        run_matrix.materialise_run_config(run)


@pytest.mark.parametrize("bad", ("", ".", "..", "sub/config.cfg", "..\\escape.cfg"))
def test_config_filename_must_be_a_bare_file_name(tmp_path: Path, bad: str) -> None:
    from scripts import run_matrix

    with pytest.raises(ValueError, match="config_filename"):
        run_matrix.normalise_run(
            {
                "name": "bad",
                "binary": "b",
                "config": str(_cfg(tmp_path)),
                "config_filename": bad,
            },
            output_root=tmp_path / "out",
        )


def test_artifact_kind_defaults_to_the_hrsc_binary(tmp_path: Path) -> None:
    from scripts import run_matrix

    run = run_matrix.normalise_run(
        {
            "name": "sod",
            "binary": "b",
            "config": str(_cfg(tmp_path)),
            "output_file": "grid.bin",
        },
        output_root=tmp_path / "out",
    )

    assert run.artifact_kind == "hrsc_binary"


def test_unknown_artifact_kind_is_rejected_at_normalise_time(tmp_path: Path) -> None:
    from scripts import run_matrix

    with pytest.raises(ValueError, match="unknown artifact kind"):
        run_matrix.normalise_run(
            {
                "name": "bad",
                "binary": "b",
                "config": str(_cfg(tmp_path)),
                "output_file": "out.json",
                "artifact_kind": "does_not_exist",
            },
            output_root=tmp_path / "out",
        )


def test_legacy_success_line_still_requires_the_solver_fields() -> None:
    from scripts.harness.runner import parse_run_status

    status, completion, failure = parse_run_status(
        "[run-status] status=success final_time=0.1 target_time=0.1 steps=4\n"
    )
    assert (status, failure) == ("success", None)
    assert completion == {"final_time": 0.1, "target_time": 0.1, "steps": 4}


def test_workload_success_line_reports_completed_and_expected() -> None:
    from scripts.harness.runner import parse_run_status

    status, completion, failure = parse_run_status(
        "[run-status] status=success kind=workload completed=50 expected=50\n"
    )
    assert (status, failure) == ("success", None)
    assert completion == {"kind": "workload", "completed": 50, "expected": 50}


def test_workload_line_with_fewer_completed_than_expected_is_incomplete() -> None:
    from scripts.harness.runner import parse_run_status

    status, completion, failure = parse_run_status(
        "[run-status] status=success kind=workload completed=49 expected=50\n"
    )
    assert status == "failed"
    assert completion is None
    assert failure["category"] == "incomplete_run"


def test_unknown_status_kind_is_a_schema_error() -> None:
    from scripts.harness.runner import parse_run_status

    status, _completion, failure = parse_run_status(
        "[run-status] status=success kind=telepathy completed=1 expected=1\n"
    )
    assert status == "failed"
    assert failure["category"] == "schema_error"


def test_resource_exhausted_is_a_recognised_failure_category() -> None:
    from scripts.harness.contracts import FailureCategory
    from scripts.harness.runner import parse_run_status

    assert FailureCategory.RESOURCE_EXHAUSTED.value == "resource_exhausted"

    status, _completion, failure = parse_run_status(
        "[run-status] status=failed reason=resource_exhausted\n"
    )
    assert status == "failed"
    assert failure["category"] == "resource_exhausted"


def test_unknown_failure_reason_is_a_schema_error() -> None:
    from scripts.harness.runner import parse_run_status

    status, _completion, failure = parse_run_status(
        "[run-status] status=failed reason=made_up_category\n"
    )
    assert status == "failed"
    assert failure["category"] == "schema_error"
