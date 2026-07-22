from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from typing import Any

from .contracts import RunRecord, RunSpec


_STATUS_RE = re.compile(r"^\[run-status\]\s+(?P<body>.+)$")


def parse_run_status(
    stderr_text: str,
) -> tuple[str | None, dict[str, Any] | None, dict[str, str] | None]:
    parsed = None
    for line in stderr_text.splitlines():
        match = _STATUS_RE.match(line.strip())
        if match:
            parsed = dict(token.split("=", 1) for token in match["body"].split())
    if parsed is None:
        return None, None, None
    if parsed.get("status") == "success":
        return "success", {
            "final_time": float(parsed["final_time"]),
            "target_time": float(parsed["target_time"]),
            "steps": int(parsed["steps"]),
        }, None
    category = parsed.get("reason", "infrastructure_error")
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


def _failure(category: str, message: str) -> dict[str, str]:
    return {"category": category, "message": message}


def _artifact_failure(spec: RunSpec, wall_start_s: float) -> dict[str, str] | None:
    for artifact in spec.required_artifacts:
        if not artifact.path.is_file():
            return _failure("artifact_error", f"missing required artifact: {artifact.path}")
        if artifact.must_be_fresh and artifact.path.stat().st_mtime < wall_start_s:
            return _failure("artifact_error", f"stale required artifact: {artifact.path}")
    return None


def execute_run(spec: RunSpec, dry_run: bool = False) -> RunRecord:
    stdout_path = spec.run_dir / "stdout.txt"
    stderr_path = spec.run_dir / "stderr.txt"
    wall_start_s = time.time()
    perf_start = time.perf_counter()
    returncode = -1
    status = "failed"
    failure: dict[str, str] | None = None
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
            stderr_text = stderr_path.read_text(encoding="utf-8")
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
