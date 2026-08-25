from __future__ import annotations

import math
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from .contracts import FailureCategory, RunRecord, RunSpec
from .artifacts import ArtifactValidationError, get_artifact_validator, validate_artifact


_STATUS_RE = re.compile(r"^\[run-status\]\s+(?P<body>.+)$")


def _parse_solver_completion(
    parsed: dict[str, str],
) -> tuple[str | None, dict[str, Any] | None, dict[str, Any] | None]:
    try:
        final_time = float(parsed["final_time"])
        target_time = float(parsed["target_time"])
        steps = int(parsed["steps"])
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        return "failed", None, _failure("schema_error", f"invalid completion fields: {exc}")
    if not math.isfinite(final_time) or not math.isfinite(target_time):
        return "failed", None, _failure(
            "schema_error", "completion times must be finite"
        )
    if steps < 0:
        return "failed", None, _failure("schema_error", "completion steps must be non-negative")
    if final_time < target_time:
        return "failed", None, _failure(
            "schema_error", "completion final_time must reach target_time"
        )
    return "success", {
        "final_time": final_time,
        "target_time": target_time,
        "steps": steps,
    }, None


def _parse_workload_completion(
    parsed: dict[str, str],
) -> tuple[str | None, dict[str, Any] | None, dict[str, Any] | None]:
    try:
        completed = int(parsed["completed"])
        expected = int(parsed["expected"])
    except (KeyError, TypeError, ValueError) as exc:
        return "failed", None, _failure("schema_error", f"invalid workload fields: {exc}")
    if completed < 0 or expected <= 0:
        return "failed", None, _failure(
            "schema_error", "workload counts must be non-negative with a positive expected"
        )
    if completed != expected:
        return "failed", None, _failure(
            FailureCategory.INCOMPLETE.value,
            f"workload completed {completed} of {expected} units",
        )
    return "success", {
        "kind": "workload",
        "completed": completed,
        "expected": expected,
    }, None


def parse_run_status(
    stderr_text: str,
) -> tuple[str | None, dict[str, Any] | None, dict[str, Any] | None]:
    parsed = None
    parse_failure: dict[str, str] | None = None
    for line in stderr_text.splitlines():
        match = _STATUS_RE.match(line.strip())
        if match:
            try:
                tokens = []
                for token in match["body"].split():
                    if "=" not in token:
                        raise ValueError(f"token has no '=': {token!r}")
                    key, value = token.split("=", 1)
                    if not key:
                        raise ValueError("token key is empty")
                    tokens.append((key, value))
                parsed = dict(tokens)
                parse_failure = None
            except ValueError as exc:
                parsed = None
                parse_failure = _failure("schema_error", f"malformed status line: {exc}")
    if parse_failure is not None:
        return "failed", None, parse_failure
    if parsed is None:
        return None, None, None
    if parsed.get("status") == "success":
        kind = parsed.get("kind")
        if kind is None:
            return _parse_solver_completion(parsed)
        if kind == "workload":
            return _parse_workload_completion(parsed)
        return "failed", None, _failure(
            "schema_error", f"unknown run-status kind: {kind!r}"
        )
    category = parsed.get("reason", FailureCategory.INFRASTRUCTURE.value)
    if category not in {member.value for member in FailureCategory}:
        return "failed", None, _failure(
            "schema_error", f"unknown run-status reason: {category!r}"
        )
    return "failed", None, {"category": category, "message": category}


def git_provenance(repo_root: Path) -> dict[str, Any]:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        status = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return {"commit": "unknown", "dirty": None}
    return {"commit": commit, "dirty": bool(status.strip())}


def _failure(category: str, message: str) -> dict[str, Any]:
    return {"category": category, "message": message}


def _artifact_failure(spec: RunSpec, wall_start_s: float) -> dict[str, str] | None:
    for artifact in spec.required_artifacts:
        try:
            get_artifact_validator(artifact.kind)
            is_file = artifact.path.is_file()
            artifact_mtime = artifact.path.stat().st_mtime if is_file else None
        except (ArtifactValidationError, OSError) as exc:
            return _failure("artifact_error", str(exc))
        if not is_file:
            return _failure("artifact_error", f"missing required artifact: {artifact.path}")
        if artifact.must_be_fresh and artifact_mtime < wall_start_s:
            return _failure("artifact_error", f"stale required artifact: {artifact.path}")
        try:
            validate_artifact(artifact.path, artifact.kind)
        except ArtifactValidationError as exc:
            return _failure("artifact_error", str(exc))
    return None


def execute_run(spec: RunSpec, dry_run: bool = False) -> RunRecord:
    stdout_path = spec.run_dir / "stdout.txt"
    stderr_path = spec.run_dir / "stderr.txt"
    wall_start_s = time.time()
    perf_start = time.perf_counter()
    returncode = -1
    status = "failed"
    failure: dict[str, Any] | None = None
    completion: dict[str, Any] | None = None

    try:
        spec.run_dir.mkdir(parents=True, exist_ok=True)
        if dry_run:
            stdout_path.write_text("", encoding="utf-8")
            stderr_path.write_text("dry-run\n", encoding="utf-8")
            returncode = 0
            status = "success"
            completion = {"reported": False}
        else:
            with (
                stdout_path.open("w", encoding="utf-8") as stdout,
                stderr_path.open("w", encoding="utf-8") as stderr,
            ):
                result = subprocess.run(
                    spec.command,
                    cwd=spec.cwd,
                    timeout=spec.timeout_s,
                    stdout=stdout,
                    stderr=stderr,
                    check=False,
                )
            returncode = result.returncode
            stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
            parsed_status, parsed_completion, parsed_failure = parse_run_status(stderr_text)
            if returncode != 0:
                status = "failed"
                failure = parsed_failure or _failure(
                    "infrastructure_error", f"process exited with return code {returncode}"
                )
            elif parsed_status == "failed":
                status = "failed"
                failure = parsed_failure
            else:
                status = "success"
                completion = {"reported": parsed_status == "success"}
                if parsed_completion is not None:
                    completion.update(parsed_completion)
                failure = _artifact_failure(spec, wall_start_s)
                if failure is not None:
                    status = "failed"
                    completion = None
    except subprocess.TimeoutExpired as exc:
        failure = _failure("infrastructure_error", f"process timed out: {exc}")
    except Exception as exc:
        failure = _failure("infrastructure_error", str(exc))
        failure["exception_type"] = type(exc).__name__
        if isinstance(exc, FileNotFoundError):
            failure.update(
                errno=exc.errno,
                strerror=exc.strerror,
                filename=exc.filename or spec.command[0],
            )

    return RunRecord(
        spec=spec,
        returncode=returncode,
        elapsed_wall_s=time.perf_counter() - perf_start,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        status=status,
        failure=failure,
        completion=completion,
    )
