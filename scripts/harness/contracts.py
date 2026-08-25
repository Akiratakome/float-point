from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from typing import Any


class FailureCategory(str, Enum):
    CONFIGURATION = "configuration_error"
    UNSUPPORTED = "unsupported_capability"
    NUMERICAL = "numerical_failure"
    INCOMPLETE = "incomplete_run"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    INFRASTRUCTURE = "infrastructure_error"
    ARTIFACT = "artifact_error"
    SCHEMA = "schema_error"


@dataclass(frozen=True)
class RequiredArtifact:
    path: Path
    must_be_fresh: bool = True
    kind: str = "file"


@dataclass(frozen=True)
class BuildSemantics:
    requested_opt_level: str | None = None
    requested_fast_math: bool | None = None
    requested_strict_ieee: bool | None = None
    effective_math_mode: str = "unknown"
    compiler_id: str | None = None
    compiler_version: str | None = None
    compiler_path: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)


_BUILD_SEMANTICS_SCHEMA = {"name": "hrsc.build-semantics", "version": 1}
_OPT_LEVELS = {"", "O2", "O3", "Ofast"}
_EFFECTIVE_MATH_MODES = {"compiler-default", "fast", "strict"}
_EVIDENCE_FIELDS = {"optimization", "fast_math", "strict_ieee"}


def _require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"build semantics {field} must be an object")
    return value


def _require_exact_fields(value: dict[str, Any], fields: set[str], field: str) -> None:
    missing = fields - value.keys()
    unexpected = value.keys() - fields
    if missing or unexpected:
        details = []
        if missing:
            details.append(
                f"missing {', '.join(f'{field}.{name}' for name in sorted(missing))}"
            )
        if unexpected:
            details.append(
                f"unexpected {', '.join(f'{field}.{name}' for name in sorted(unexpected))}"
            )
        raise ValueError(f"build semantics {field} has {'; '.join(details)} fields")


def _require_string(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not value and not allow_empty):
        requirement = "a string" if allow_empty else "a non-empty string"
        raise ValueError(f"build semantics {field} must be {requirement}")
    return value


def _require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"build semantics {field} must be a boolean")
    return value


def _fallback_build_semantics(label: str | None) -> BuildSemantics:
    parts = label.split("-") if label else []
    opt_level = next((part for part in parts if part in {"O2", "O3", "Ofast"}), None)
    fast_math = "fastmath" in parts if opt_level is not None else None
    effective_math_mode = (
        "fast"
        if opt_level == "Ofast" or fast_math is True
        else "compiler-default"
        if opt_level is not None
        else "unknown"
    )
    return BuildSemantics(
        requested_opt_level=opt_level,
        requested_fast_math=fast_math,
        effective_math_mode=effective_math_mode,
    )


def load_build_semantics(path: Path, fallback_label: str | None = None) -> BuildSemantics:
    """Load CMake build semantics, or derive only safe facts from a legacy label."""
    if not path.exists():
        return _fallback_build_semantics(fallback_label)
    if not path.is_file():
        raise ValueError(f"build semantics path is not a file: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid build semantics JSON: {path}") from exc

    raw = _require_object(raw, "document")
    _require_exact_fields(
        raw,
        {"schema", "compiler", "requested", "effective_math_mode", "flag_evidence"},
        "document",
    )
    schema = _require_object(raw["schema"], "schema")
    _require_exact_fields(schema, {"name", "version"}, "schema")
    if schema["name"] != _BUILD_SEMANTICS_SCHEMA["name"]:
        raise ValueError("unsupported build semantics schema name")
    if (
        type(schema["version"]) is not int
        or schema["version"] != _BUILD_SEMANTICS_SCHEMA["version"]
    ):
        raise ValueError("unsupported build semantics schema version")

    compiler = _require_object(raw["compiler"], "compiler")
    _require_exact_fields(compiler, {"id", "version", "path"}, "compiler")
    requested = _require_object(raw["requested"], "requested")
    _require_exact_fields(
        requested, {"opt_level", "fast_math", "strict_ieee"}, "requested"
    )
    opt_level = _require_string(
        requested["opt_level"], "requested.opt_level", allow_empty=True
    )
    if opt_level not in _OPT_LEVELS:
        raise ValueError("build semantics requested.opt_level is unsupported")
    fast_math = _require_bool(requested["fast_math"], "requested.fast_math")
    strict_ieee = _require_bool(requested["strict_ieee"], "requested.strict_ieee")
    effective_math_mode = _require_string(
        raw["effective_math_mode"], "effective_math_mode"
    )
    if effective_math_mode not in _EFFECTIVE_MATH_MODES:
        raise ValueError("build semantics effective_math_mode is unsupported")
    expected_mode = (
        "strict"
        if strict_ieee
        else "fast"
        if fast_math or opt_level == "Ofast"
        else "compiler-default"
    )
    if effective_math_mode != expected_mode:
        raise ValueError("build semantics effective_math_mode conflicts with requested axes")

    evidence = _require_object(raw["flag_evidence"], "flag_evidence")
    _require_exact_fields(evidence, _EVIDENCE_FIELDS, "flag_evidence")

    return BuildSemantics(
        requested_opt_level=opt_level,
        requested_fast_math=fast_math,
        requested_strict_ieee=strict_ieee,
        effective_math_mode=effective_math_mode,
        compiler_id=_require_string(compiler["id"], "compiler.id"),
        compiler_version=_require_string(compiler["version"], "compiler.version"),
        compiler_path=_require_string(compiler["path"], "compiler.path"),
        evidence={
            field: _require_string(
                evidence[field], f"flag_evidence.{field}", allow_empty=True
            )
            for field in _EVIDENCE_FIELDS
        },
    )


@dataclass(frozen=True)
class RunSpec:
    name: str
    experiment: str
    command: tuple[str, ...]
    run_dir: Path
    source_config: Path
    run_config: Path
    cwd: Path | None = None
    timeout_s: float | None = None
    required_artifacts: tuple[RequiredArtifact, ...] = ()
    build_semantics: BuildSemantics | None = None


@dataclass(frozen=True)
class RunRecord:
    spec: RunSpec
    returncode: int
    elapsed_wall_s: float
    stdout_path: Path
    stderr_path: Path
    status: str
    failure: dict[str, Any] | None = None
    completion: dict[str, Any] | None = None
