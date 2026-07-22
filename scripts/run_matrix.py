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
    return MatrixRun(
        name=name,
        binary=Path(str(raw["binary"])),
        source_config=Path(str(raw["config"])),
        run_dir=run_dir,
        precision=raw.get("precision"),
        build=raw.get("build"),
        raw_output=(run_dir / str(raw_output)) if raw_output else None,
        extra_cfg={str(key): str(value) for key, value in raw_extra_cfg.items()},
    )


_replace_or_append_cfg_line = replace_or_append_cfg


def materialise_run_config(run: MatrixRun) -> Path:
    target = run.run_dir / "config.cfg"
    overrides = dict(run.extra_cfg or {})
    if run.raw_output is not None:
        overrides["output_format"] = "binary"
        overrides["output_file"] = str(run.raw_output)
    return materialise_config(run.source_config, target, overrides)


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
    return {
        "experiment": experiment,
        "name": run.name,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit,
        "binary": str(run.binary),
        "source_config": str(run.source_config),
        "run_config": str(run.run_dir / "config.cfg"),
        "precision": run.precision,
        "build": run.build,
        "raw_output": str(run.raw_output) if run.raw_output else None,
        "extra_cfg": run.extra_cfg or {},
        "command": command,
        "returncode": returncode,
    }


def run_one(run: MatrixRun, experiment: str, dry_run: bool = False) -> dict[str, Any]:
    config = materialise_run_config(run)
    command = [str(run.binary), str(config)]
    stdout_path = run.run_dir / "stdout.txt"
    stderr_path = run.run_dir / "stderr.txt"
    if dry_run:
        result_code = 0
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("dry-run\n", encoding="utf-8")
    else:
        with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
            result = subprocess.run(command, stdout=stdout, stderr=stderr, check=False)
        result_code = result.returncode

    metadata = build_metadata(run, experiment, command, git_commit(), result_code)
    if not dry_run:
        total_s = parse_timing_total_s(stderr_path.read_text(encoding="utf-8"))
        metadata["timing"] = {"total_s": total_s}
    metadata["stdout"] = str(stdout_path)
    metadata["stderr"] = str(stderr_path)
    (run.run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    if result_code != 0:
        raise RuntimeError(f"run failed: {run.name} exited {result_code}; see {stderr_path}")
    return metadata


def load_matrix(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
