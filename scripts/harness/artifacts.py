from __future__ import annotations

import json
import math
import struct
from collections.abc import Callable
from pathlib import Path


class ArtifactValidationError(ValueError):
    """Raised when an artifact kind is unknown or its contents are invalid."""


ArtifactValidator = Callable[[Path], None]


def _validate_file(path: Path) -> None:
    if not path.is_file():
        raise ArtifactValidationError(f"missing required artifact: {path}")


def _validate_hrsc_binary(path: Path) -> None:
    try:
        size = path.stat().st_size
        with path.open("rb") as stream:
            header = stream.read(64)
    except OSError as exc:
        raise ArtifactValidationError(f"cannot read HRSC binary: {path}: {exc}") from exc

    if len(header) != 64:
        raise ArtifactValidationError(f"HRSC binary header is truncated: {path}")
    if header[:4] != b"HRSC":
        raise ArtifactValidationError(f"HRSC binary has invalid magic: {path}")

    try:
        nx, ny, nvars, precision = struct.unpack("<iiii", header[4:20])
        time_value, dx, dy = struct.unpack("<ddd", header[20:44])
    except struct.error as exc:
        raise ArtifactValidationError(f"HRSC binary header is malformed: {path}") from exc

    if nx <= 0 or ny <= 0:
        raise ArtifactValidationError(
            f"HRSC binary dimensions must be positive: nx={nx}, ny={ny}"
        )
    if nvars <= 0:
        raise ArtifactValidationError(f"HRSC binary variable count must be positive: {nvars}")
    if precision not in (4, 8):
        raise ArtifactValidationError(
            f"HRSC binary precision must be 4 or 8 bytes: {precision}"
        )
    if not all(math.isfinite(value) for value in (time_value, dx, dy)):
        raise ArtifactValidationError("HRSC binary time and spacing must be finite")
    if dx <= 0 or dy <= 0:
        raise ArtifactValidationError(
            f"HRSC binary spacing must be positive: dx={dx}, dy={dy}"
        )

    expected_size = 64 + nx * ny * nvars * precision
    if size != expected_size:
        raise ArtifactValidationError(
            f"HRSC binary size {size}B != expected {expected_size}B: {path}"
        )


def _validate_workload_result(path: Path) -> None:
    from scripts.aiinfra.result_schema import validate_workload_result

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactValidationError(f"cannot read workload result: {path}: {exc}") from exc
    try:
        validate_workload_result(document)
    except ValueError as exc:
        raise ArtifactValidationError(f"{path}: {exc}") from exc


_ARTIFACT_VALIDATORS: dict[str, ArtifactValidator] = {
    "file": _validate_file,
    "hrsc_binary": _validate_hrsc_binary,
    "workload_result": _validate_workload_result,
}


def get_artifact_validator(kind: str) -> ArtifactValidator:
    try:
        return _ARTIFACT_VALIDATORS[kind]
    except KeyError as exc:
        raise ArtifactValidationError(f"unknown artifact kind: {kind}") from exc


def validate_artifact(path: Path, kind: str) -> None:
    validator = get_artifact_validator(kind)
    try:
        validator(path)
    except ArtifactValidationError:
        raise
    except OSError as exc:
        raise ArtifactValidationError(f"cannot validate artifact {path}: {exc}") from exc
