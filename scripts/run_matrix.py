#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.harness.config import materialise_config, replace_or_append_cfg
from scripts.harness.artifacts import ArtifactValidationError, get_artifact_validator
from scripts.harness.contracts import (
    BuildSemantics,
    RequiredArtifact,
    RunRecord,
    RunSpec,
    load_build_semantics,
)
from scripts.harness.metadata import serialise_record
from scripts.harness.runner import execute_run, git_provenance


REQUIRED_RUN_FIELDS = ("name", "binary", "config")


@dataclass(frozen=True)
class MatrixRun:
    name: str
    binary: Path
    source_config: Path
    run_dir: Path
    precision: str | None = None
    build: str | None = None
    raw_output: Path | None = None
    extra_cfg: dict[str, str] | None = None
    arguments: tuple[str, ...] = ()
    config_filename: str = "config.cfg"
    artifact_kind: str = "hrsc_binary"
    build_semantics: BuildSemantics | None = None


def _require_field(raw: dict[str, Any], field: str) -> Any:
    if field not in raw or raw[field] in (None, ""):
        raise ValueError(f"run '{raw.get('name', '<unnamed>')}' missing required field '{field}'")
    return raw[field]


def normalise_run(raw: dict[str, Any], output_root: Path) -> MatrixRun:
    for field in REQUIRED_RUN_FIELDS:
        _require_field(raw, field)

    name = str(raw["name"])
    run_dir = output_root / "runs" / name
    raw_output = raw.get("output_file")
    raw_extra_cfg = raw.get("extra_cfg", {})
    if not isinstance(raw_extra_cfg, dict):
        raise ValueError(f"run '{name}' field 'extra_cfg' must be an object")
    binary = Path(str(raw["binary"]))
    raw_arguments = raw.get("arguments", [])
    if not isinstance(raw_arguments, list) or not all(
        isinstance(argument, str) for argument in raw_arguments
    ):
        raise ValueError(f"run '{name}' field 'arguments' must be an array of strings")
    config_filename = str(raw.get("config_filename", "config.cfg"))
    if (
        config_filename in ("", ".", "..")
        or "/" in config_filename
        or "\\" in config_filename
    ):
        raise ValueError(
            f"run '{name}' field 'config_filename' must be a bare file name"
        )
    artifact_kind = str(raw.get("artifact_kind", "hrsc_binary"))
    try:
        get_artifact_validator(artifact_kind)
    except ArtifactValidationError as exc:
        raise ValueError(f"run '{name}' has an {exc}") from exc
    build = raw.get("build")
    return MatrixRun(
        name=name,
        binary=binary,
        source_config=Path(str(raw["config"])),
        run_dir=run_dir,
        precision=raw.get("precision"),
        build=build,
        raw_output=(run_dir / str(raw_output)) if raw_output else None,
        extra_cfg={str(key): str(value) for key, value in raw_extra_cfg.items()},
        arguments=tuple(raw_arguments),
        config_filename=config_filename,
        artifact_kind=artifact_kind,
        build_semantics=load_build_semantics(
            binary.parent / "build_semantics.json",
            fallback_label=str(build) if build is not None else None,
        ),
    )


_replace_or_append_cfg_line = replace_or_append_cfg


def materialise_run_config(run: MatrixRun) -> Path:
    target = run.run_dir / run.config_filename
    overrides = dict(run.extra_cfg or {})
    is_cfg = Path(run.config_filename).suffix.lower() == ".cfg"
    if run.raw_output is not None and is_cfg:
        overrides["output_format"] = "binary"
        overrides["output_file"] = str(run.raw_output)
    if overrides and not is_cfg:
        raise ValueError(
            f"run '{run.name}' sets cfg overrides but config_filename "
            f"'{run.config_filename}' is not a '.cfg' file"
        )
    return materialise_config(run.source_config, target, overrides)


def build_command(run: MatrixRun, config: Path) -> tuple[str, ...]:
    """Binary, then optional workload arguments, then the materialised config."""
    return (str(run.binary), *run.arguments, str(config))


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def parse_timing_total_s(stderr_text: str) -> float | None:
    """Parse '[timing] total_s=<value>' from solver stderr.

    Returns the LAST occurrence's value (convergence mode emits one line
    per resolution; the last is the largest grid). Returns None if absent.
    """
    last_value: float | None = None
    for line in stderr_text.splitlines():
        s = line.strip()
        if not s.startswith("[timing]"):
            continue
        for tok in s.split():
            if tok.startswith("total_s="):
                try:
                    last_value = float(tok.split("=", 1)[1])
                except ValueError:
                    pass
    return last_value


def build_metadata(
    run: MatrixRun,
    experiment: str,
    command: list[str],
    git_commit: str,
    returncode: int,
) -> dict[str, Any]:
    legacy = _legacy_metadata(run, experiment, command, git_commit, returncode)
    spec = RunSpec(
        name=run.name,
        experiment=experiment,
        command=tuple(command),
        run_dir=run.run_dir,
        source_config=run.source_config,
        run_config=run.run_dir / run.config_filename,
        build_semantics=run.build_semantics,
    )
    record = RunRecord(
        spec=spec,
        returncode=returncode,
        elapsed_wall_s=0.0,
        stdout_path=run.run_dir / "stdout.txt",
        stderr_path=run.run_dir / "stderr.txt",
        status="success" if returncode == 0 else "failed",
    )
    return serialise_record(record, legacy)


def _legacy_metadata(
    run: MatrixRun,
    experiment: str,
    command: list[str],
    commit: str,
    returncode: int,
) -> dict[str, Any]:
    return {
        "experiment": experiment,
        "name": run.name,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": commit,
        "binary": str(run.binary),
        "source_config": str(run.source_config),
        "run_config": str(run.run_dir / run.config_filename),
        "precision": run.precision,
        "build": run.build,
        "raw_output": str(run.raw_output) if run.raw_output else None,
        "extra_cfg": run.extra_cfg or {},
        "command": command,
        "returncode": returncode,
        "provenance": {
            "git": git_provenance(Path(__file__).resolve().parents[1])
        },
    }


def run_one(run: MatrixRun, experiment: str, dry_run: bool = False) -> dict[str, Any]:
    config = materialise_run_config(run)
    spec = RunSpec(
        name=run.name,
        experiment=experiment,
        command=build_command(run, config),
        run_dir=run.run_dir,
        source_config=run.source_config,
        run_config=config,
        required_artifacts=(
            (RequiredArtifact(run.raw_output, kind=run.artifact_kind),)
            if run.raw_output
            else ()
        ),
        build_semantics=run.build_semantics,
    )
    record = execute_run(spec, dry_run=dry_run)
    stderr_text = (
        record.stderr_path.read_text(encoding="utf-8")
        if record.stderr_path.exists()
        else ""
    )
    legacy = _legacy_metadata(
        run,
        experiment,
        list(spec.command),
        git_commit(),
        record.returncode,
    )
    legacy.update(
        {
            "timing": {"total_s": parse_timing_total_s(stderr_text)},
            "stdout": str(record.stdout_path),
            "stderr": str(record.stderr_path),
        }
    )
    metadata = serialise_record(record, legacy)
    (run.run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    if record.status != "success":
        category = (record.failure or {}).get("category", "infrastructure_error")
        raise RuntimeError(
            f"run failed: {run.name} ({category}); see {record.stderr_path}"
        )
    return metadata


def load_matrix(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_matrix(path: Path, dry_run: bool = False) -> dict[str, Any]:
    matrix = load_matrix(path)
    experiment = str(matrix.get("experiment", path.stem))
    output_root = Path(str(matrix.get("output_root", Path("experiments") / experiment)))
    runs = [normalise_run(raw, output_root) for raw in matrix.get("runs", [])]
    if not runs:
        raise ValueError("matrix contains no runs")
    results = [run_one(run, experiment, dry_run=dry_run) for run in runs]
    summary = {
        "experiment": experiment,
        "output_root": str(output_root),
        "run_count": len(results),
        "runs": results,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "matrix_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a reproducible HRSC experiment matrix.")
    parser.add_argument("matrix", type=Path, help="JSON matrix file")
    parser.add_argument("--dry-run", action="store_true", help="Write configs and metadata without executing binaries")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    json.dump(run_matrix(args.matrix, dry_run=args.dry_run), sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
