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
