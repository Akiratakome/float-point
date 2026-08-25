"""Validation for versioned Report 2 experiment lifecycle manifests."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


SCHEMA = {"name": "hrsc.experiment-manifest", "version": 1}
REPORTS = {"report2", "aiinfra"}
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
RETENTION_FIELDS = {"keep", "transient"}
PROVENANCE_FIELDS = {"notes"}


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_existing_path(
    value: Any, field: str, repo_root: Path, errors: list[str]
) -> Path | None:
    if not _nonempty_string(value):
        errors.append(f"{field} must be a nonempty repository-relative path")
        return None
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        errors.append(f"{field} must not contain control characters")
        return None

    posix_path = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    if posix_path.is_absolute():
        errors.append(f"{field} must not use a POSIX absolute path: {value!r}")
        return None
    if windows_path.drive or windows_path.root:
        errors.append(
            f"{field} must not use a Windows absolute or drive-relative path: {value!r}"
        )
        return None
    if ".." in posix_path.parts or ".." in windows_path.parts:
        errors.append(f"{field} must not contain traversal '..': {value!r}")
        return None

    candidate = (repo_root / Path(value)).resolve()
    try:
        candidate.relative_to(repo_root)
    except ValueError:
        errors.append(f"{field} escapes the repository: {value!r}")
        return None
    if not candidate.is_file():
        errors.append(f"{field} must resolve to an existing regular file: {value!r}")
        return None
    return candidate


def _validate_manifest(
    path: Path, repo_root: Path, replacement_stack: set[Path]
) -> list[str]:
    errors: list[str] = []
    manifest_path = path.resolve()
    try:
        manifest_path.relative_to(repo_root)
    except ValueError:
        return [f"manifest is outside repo_root: {path}"]
    if manifest_path in replacement_stack:
        return [f"replacement cycle includes {path}"]
    if not manifest_path.is_file():
        return [f"manifest must be an existing regular file: {path}"]

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
        if type(schema.get("version")) is not int or schema["version"] != SCHEMA["version"]:
            errors.append("schema.version must equal 1")
        unknown_schema_fields = sorted(set(schema) - set(SCHEMA))
        if unknown_schema_fields:
            errors.append(f"schema has unknown fields: {', '.join(unknown_schema_fields)}")
    if not _nonempty_string(data.get("id")):
        errors.append("id must be a nonempty string")
    if data.get("report") not in REPORTS:
        errors.append(f"report must be one of {sorted(REPORTS)}")
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
        unknown_retention_fields = sorted(set(retention) - RETENTION_FIELDS)
        if unknown_retention_fields:
            errors.append(
                f"retention has unknown fields: {', '.join(unknown_retention_fields)}"
            )
        for field in RETENTION_FIELDS:
            values = retention.get(field)
            if not isinstance(values, list) or not values or not all(
                _nonempty_string(value) for value in values
            ):
                errors.append(f"retention.{field} must be a nonempty list of strings")

    provenance = data.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance must be an object")
    else:
        unknown_provenance_fields = sorted(set(provenance) - PROVENANCE_FIELDS)
        if unknown_provenance_fields:
            errors.append(
                f"provenance has unknown fields: {', '.join(unknown_provenance_fields)}"
            )
        if not _nonempty_string(provenance.get("notes")):
            errors.append("provenance.notes must be a nonempty string")

    exclusion_reason = data.get("exclusion_reason")
    if "exclusion_reason" in data and not _nonempty_string(exclusion_reason):
        errors.append("exclusion_reason must be a nonempty string")
    if lifecycle == "invalid" and not _nonempty_string(exclusion_reason):
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

    resolved_root = repo_root.resolve()
    if not resolved_root.is_dir():
        return [f"repo_root must be an existing directory: {repo_root}"]
    return _validate_manifest(path, resolved_root, set())


def load_valid_manifest(path: Path, repo_root: Path) -> dict[str, Any]:
    """Load *path* after validation, raising one readable error for invalid input."""

    errors = validate_manifest(path, repo_root)
    if errors:
        details = "\n".join(f"- {error}" for error in errors)
        raise ValueError(f"Invalid experiment manifest {path}:\n{details}")
    return json.loads(path.read_text(encoding="utf-8"))
