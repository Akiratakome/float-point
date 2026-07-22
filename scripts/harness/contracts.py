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
    INFRASTRUCTURE = "infrastructure_error"
    ARTIFACT = "artifact_error"
    SCHEMA = "schema_error"


@dataclass(frozen=True)
class RequiredArtifact:
    path: Path
    must_be_fresh: bool = True


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


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _optional_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


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
    if not path.is_file():
        return _fallback_build_semantics(fallback_label)

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"build semantics must be an object: {path}")
    compiler = raw.get("compiler")
    requested = raw.get("requested")
    evidence = raw.get("flag_evidence")
    compiler = compiler if isinstance(compiler, dict) else {}
    requested = requested if isinstance(requested, dict) else {}
    return BuildSemantics(
        requested_opt_level=_optional_string(requested.get("opt_level")),
        requested_fast_math=_optional_bool(requested.get("fast_math")),
        requested_strict_ieee=_optional_bool(requested.get("strict_ieee")),
        effective_math_mode=_optional_string(raw.get("effective_math_mode")) or "unknown",
        compiler_id=_optional_string(compiler.get("id")),
        compiler_version=_optional_string(compiler.get("version")),
        compiler_path=_optional_string(compiler.get("path")),
        evidence=dict(evidence) if isinstance(evidence, dict) else {},
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
