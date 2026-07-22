from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
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
    effective_math_mode: str = "unknown"
    compiler_id: str | None = None
    compiler_version: str | None = None
    compiler_path: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)


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
    failure: dict[str, str] | None = None
    completion: dict[str, Any] | None = None
