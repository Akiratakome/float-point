"""Validation for versioned Report 2 experiment lifecycle manifests."""

from __future__ import annotations

import json
from pathlib import Path, PureWindowsPath
from typing import Any


SCHEMA = {"name": "hrsc.experiment-manifest", "version": 1}
PIPELINE_STAGES = ("config", "build", "run", "measure", "aggregate", "plot")
LIFECYCLES = {"canonical", "provenance", "superseded", "invalid", "generated"}
TOP_LEVEL_FIELDS = {
    "schema",
    "id",
    "report",
    "lifecycle",
    "purpose",
    "pipeline",
    "evidence",
    "retention",
    "provenance",
    "replacement",
    "exclusion_reason",
}


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_existing_path(
    value: Any, field: str, repo_root: Path, errors: list[str]
) -> Path | None:
    if not _nonempty_string(value):
        errors.append(f"{field} must be a nonempty repository-relative path")
        return None

    raw_path = Path(value)
    windows_path = PureWindowsPath(value)
    if raw_path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        errors.append(f"{field} must be repository-relative: {value!r}")
        return None

    candidate = (repo_root / raw_path).resolve()
    try:
        candidate.relative_to(repo_root)
    except ValueError:
        errors.append(f"{field} escapes the repository: {value!r}")
        return None
    if not candidate.exists():
        errors.append(f"{field} does not exist: {value!r}")
        return None
    return candidate


def _validate_manifest(
    path: Path, repo_root: Path, replacement_stack: set[Path]
) -> list[str]:
    errors: list[str] = []
    manifest_path = path.resolve()
    if manifest_path in replacement_stack:
        return [f"replacement cycle includes {path}"]
    if not manifest_path.is_file():
        return [f"manifest does not exist: {path}"]

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"manifest is not valid JSON: {exc}"]
    if not isinstance(data, dict):
        return ["manifest root must be an object"]

    unknown_fields = sorted(set(data) - TOP_LEVEL_FIELDS)
    if unknown_fields:
        errors.append(f"unknown top-level fields: {', '.join(unknown_fields)}")
    schema = data.get("schema")
    if not isinstance(schema, dict):
        errors.append("schema must be an object")
    else:
        if schema.get("name") != SCHEMA["name"]:
            errors.append("schema.name must equal 'hrsc.experiment-manifest'")
        if schema.get("version") != SCHEMA["version"]:
            errors.append("schema.version must equal 1")
        unknown_schema_fields = sorted(set(schema) - set(SCHEMA))
        if unknown_schema_fields:
            errors.append(f"schema has unknown fields: {', '.join(unknown_schema_fields)}")
    if not _nonempty_string(data.get("id")):
        errors.append("id must be a nonempty string")
    if data.get("report") != "report2":
        errors.append("report must equal 'report2'")
    if not _nonempty_string(data.get("purpose")):
        errors.append("purpose must be a nonempty string")

    lifecycle = data.get("lifecycle")
    if not isinstance(lifecycle, str) or lifecycle not in LIFECYCLES:
        errors.append(f"lifecycle must be one of {sorted(LIFECYCLES)}")

    pipeline = data.get("pipeline")
    if not isinstance(pipeline, dict):
        errors.append("pipeline must be an object")
    else:
        missing_stages = [stage for stage in PIPELINE_STAGES if stage not in pipeline]
        if missing_stages:
            errors.append(f"pipeline is missing required stages: {', '.join(missing_stages)}")
        unknown_stages = sorted(set(pipeline) - set(PIPELINE_STAGES))
        if unknown_stages:
            errors.append(f"pipeline has unknown stages: {', '.join(unknown_stages)}")
        for stage in PIPELINE_STAGES:
            values = pipeline.get(stage)
            if not isinstance(values, list) or not values:
                errors.append(f"pipeline.{stage} must be a nonempty list")
                continue
            for index, value in enumerate(values):
                _validate_existing_path(value, f"pipeline.{stage}[{index}]", repo_root, errors)

    evidence = data.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("evidence must be a nonempty list")
    else:
        for index, value in enumerate(evidence):
            _validate_existing_path(value, f"evidence[{index}]", repo_root, errors)

    retention = data.get("retention")
    if not isinstance(retention, dict):
        errors.append("retention must be an object")
    else:
        for field in ("keep", "transient"):
            values = retention.get(field)
            if not isinstance(values, list) or not values or not all(
                _nonempty_string(value) for value in values
            ):
                errors.append(f"retention.{field} must be a nonempty list of strings")

    provenance = data.get("provenance")
    if not isinstance(provenance, dict) or not _nonempty_string(provenance.get("notes")):
        errors.append("provenance.notes must be a nonempty string")

    if lifecycle == "invalid" and not _nonempty_string(data.get("exclusion_reason")):
        errors.append("invalid lifecycle requires a nonempty exclusion_reason")

    replacement = data.get("replacement")
    if lifecycle == "superseded" and not _nonempty_string(replacement):
        errors.append("superseded lifecycle requires a valid replacement")
    if replacement is not None:
        replacement_path = _validate_existing_path(replacement, "replacement", repo_root, errors)
        if replacement_path is not None:
            replacement_errors = _validate_manifest(
                replacement_path, repo_root, replacement_stack | {manifest_path}
            )
            if replacement_errors:
                errors.append("replacement is not a valid manifest: " + "; ".join(replacement_errors))

    return errors


def validate_manifest(path: Path, repo_root: Path) -> list[str]:
    """Return every schema, lifecycle, path, and evidence validation error."""

    return _validate_manifest(path, repo_root.resolve(), set())


def load_valid_manifest(path: Path, repo_root: Path) -> dict[str, Any]:
    """Load *path* after validation, raising one readable error for invalid input."""

    errors = validate_manifest(path, repo_root)
    if errors:
        details = "\n".join(f"- {error}" for error in errors)
        raise ValueError(f"Invalid experiment manifest {path}:\n{details}")
    return json.loads(path.read_text(encoding="utf-8"))
