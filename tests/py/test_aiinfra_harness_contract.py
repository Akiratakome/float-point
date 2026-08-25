from __future__ import annotations

import json
from pathlib import Path
import sys

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


def _workload_config(tmp_path: Path, **overrides) -> Path:
    """Create a complete workload config; each test varies one real input."""
    document = {
        "schema": {"name": "aiinfra.workload-config", "version": 1},
        "workload": "determinism",
        "backend": "fake",
        "model": "fake-tiny",
        "dtype": "float32",
        "prompt": "hello",
        "max_new_tokens": 8,
        "repeats": 3,
        "batch_sizes": [1, 4],
        "seed": 0,
        "decode": "greedy",
        "options": {},
    }
    document.update(overrides)
    path = tmp_path / "workload.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def _workload_matrix(source_config: Path) -> dict:
    return {
        "experiment": "pytest-aiinfra",
        "runs": [
            {
                "name": "fake-workload",
                "binary": sys.executable,
                "arguments": ["scripts/aiinfra/run_workload.py"],
                "config": str(source_config),
                "config_filename": "config.json",
                "output_file": "workload_result.json",
                "artifact_kind": "workload_result",
            }
        ],
    }


def test_fake_workload_runs_end_to_end_through_run_matrix(tmp_path: Path) -> None:
    """A missing workload entry point would leave no valid result or completion."""
    from scripts import run_matrix

    source = _workload_config(tmp_path)
    run = run_matrix.normalise_run(
        _workload_matrix(source)["runs"][0], output_root=tmp_path / "out"
    )
    metadata = run_matrix.run_one(run, experiment="pytest-aiinfra")

    assert metadata["status"] == "success"
    assert metadata["completion"] == {
        "kind": "workload",
        "completed": 2,
        "expected": 2,
        "reported": True,
    }
    assert metadata["failure"] is None
    assert (
        Path(metadata["stderr"]).read_text(encoding="utf-8").splitlines()[0]
        == "[run-status] status=success kind=workload completed=2 expected=2"
    )

    result_path = run.run_dir / "workload_result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["schema"] == {"name": "aiinfra.workload-result", "version": 1}
    assert [cell["cell_id"] for cell in result["cells"]] == [
        "batch_size=1",
        "batch_size=4",
    ]


@pytest.mark.parametrize(
    ("fault", "category"),
    (
        ("resource_exhausted", "resource_exhausted"),
        ("unsupported_capability", "unsupported_capability"),
    ),
)
def test_injected_backend_faults_reach_the_run_record(
    tmp_path: Path, fault: str, category: str
) -> None:
    """A backend's declared failure must survive process and harness boundaries."""
    from scripts import run_matrix

    source = _workload_config(tmp_path, options={"fault": fault})
    run = run_matrix.normalise_run(
        _workload_matrix(source)["runs"][0], output_root=tmp_path / "out"
    )

    with pytest.raises(RuntimeError, match=category):
        run_matrix.run_one(run, experiment="pytest-aiinfra")

    metadata = json.loads((run.run_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "failed"
    assert metadata["failure"]["category"] == category
    assert metadata["completion"] is None
    assert (
        Path(metadata["stderr"]).read_text(encoding="utf-8").splitlines()[0]
        == f"[run-status] status=failed reason={category}"
    )


def test_unknown_workload_is_a_configuration_error_in_the_run_record(tmp_path: Path) -> None:
    """Accepting an unimplemented workload would misrepresent a completed run."""
    from scripts import run_matrix

    source = _workload_config(tmp_path, workload="unimplemented")
    run = run_matrix.normalise_run(
        _workload_matrix(source)["runs"][0], output_root=tmp_path / "out"
    )

    with pytest.raises(RuntimeError, match="configuration_error"):
        run_matrix.run_one(run, experiment="pytest-aiinfra")

    metadata = json.loads((run.run_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "failed"
    assert metadata["failure"]["category"] == "configuration_error"
    assert metadata["completion"] is None


def test_invalid_workload_config_is_a_configuration_error_in_the_run_record(
    tmp_path: Path,
) -> None:
    """A malformed config must fail before any result can be accepted."""
    from scripts import run_matrix

    source = _workload_config(tmp_path, repeats=0)
    run = run_matrix.normalise_run(
        _workload_matrix(source)["runs"][0], output_root=tmp_path / "out"
    )

    with pytest.raises(RuntimeError, match="configuration_error"):
        run_matrix.run_one(run, experiment="pytest-aiinfra")

    metadata = json.loads((run.run_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "failed"
    assert metadata["failure"]["category"] == "configuration_error"
    assert metadata["completion"] is None


def test_committed_smoke_matrix_agrees_with_the_result_filename() -> None:
    """The committed smoke matrix must contain only runnable success cells."""
    from scripts import run_matrix
    from scripts.aiinfra import run_workload

    repo_root = Path(__file__).resolve().parents[2]
    matrix = run_matrix.load_matrix(
        repo_root / "configs" / "aiinfra" / "smoke" / "fake_workload.json"
    )
    assert len(matrix["runs"]) == 1
    for raw in matrix["runs"]:
        assert raw["output_file"] == run_workload.RESULT_FILENAME
        assert raw["artifact_kind"] == "workload_result"
        assert (repo_root / raw["config"]).is_file()
