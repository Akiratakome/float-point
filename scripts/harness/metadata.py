from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from .contracts import RunRecord


SCHEMA = {"name": "hrsc.run-record", "version": 1}


def _schema(raw: Mapping[str, Any]) -> dict[str, int | str]:
    supplied = raw.get("schema")
    if supplied is None:
        return dict(SCHEMA)
    if not isinstance(supplied, Mapping):
        raise ValueError("schema must be a mapping")
    name = supplied.get("name")
    if name != SCHEMA["name"]:
        raise ValueError(f"unsupported schema name: {name!r}")
    version = supplied.get("version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise ValueError("schema version must be an integer")
    if version > SCHEMA["version"]:
        raise ValueError(f"unsupported schema version: {version}")
    return dict(SCHEMA)


def _mapping_copy(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def normalise_metadata(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Return schema-v1 metadata while retaining legacy fields verbatim."""
    if not isinstance(raw, Mapping):
        raise TypeError("metadata must be a mapping")

    canonical = dict(raw)
    canonical["schema"] = _schema(raw)

    status = raw.get("status")
    if status is None:
        status = "success" if raw.get("returncode") == 0 else "failed"
    canonical["status"] = status

    artifacts = _mapping_copy(raw.get("artifacts"))
    primary_output = _first_present(
        artifacts.get("primary_output"), raw.get("raw_output"), raw.get("output_binary")
    )
    if primary_output is not None:
        artifacts["primary_output"] = primary_output
    canonical["artifacts"] = artifacts

    timing = _mapping_copy(raw.get("timing"))
    elapsed_wall_s = _first_present(
        timing.get("elapsed_wall_s"), raw.get("elapsed_wall_s"), timing.get("total_s")
    )
    if elapsed_wall_s is not None:
        timing["elapsed_wall_s"] = elapsed_wall_s
    canonical["timing"] = timing
    return canonical


def _build_semantics(record: RunRecord) -> dict[str, Any] | None:
    if record.spec.build_semantics is None:
        return None
    return asdict(record.spec.build_semantics)


def serialise_record(
    record: RunRecord, legacy: Mapping[str, Any]
) -> dict[str, Any]:
    """Combine a run record with legacy metadata and add canonical fields."""
    output = dict(legacy)
    output["schema"] = dict(SCHEMA)
    output["status"] = record.status
    output["returncode"] = record.returncode

    artifacts = _mapping_copy(legacy.get("artifacts"))
    primary_output = _first_present(
        artifacts.get("primary_output"), legacy.get("raw_output"), legacy.get("output_binary")
    )
    if primary_output is not None:
        artifacts["primary_output"] = primary_output
    output["artifacts"] = artifacts

    timing = _mapping_copy(legacy.get("timing"))
    timing["elapsed_wall_s"] = record.elapsed_wall_s
    output["timing"] = timing
    output["failure"] = dict(record.failure) if record.failure is not None else None
    output["completion"] = (
        dict(record.completion) if record.completion is not None else None
    )
    output["build_semantics"] = _build_semantics(record)
    return output


def require_successful_metadata(raw: Mapping[str, Any]) -> dict[str, Any]:
    canonical = normalise_metadata(raw)
    if canonical.get("status") != "success":
        failure = canonical.get("failure")
        category = failure.get("category") if isinstance(failure, Mapping) else None
        detail = category or canonical.get("status") or "unknown"
        raise ValueError(f"run metadata is not successful: {detail}")
    return canonical
