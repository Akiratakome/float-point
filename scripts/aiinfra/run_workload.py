#!/usr/bin/env python3
"""Matrix entry point for aiinfra workloads."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.aiinfra import determinism, environment, result_schema
from scripts.aiinfra.backends.base import WorkloadFailure, get_backend
from scripts.aiinfra.config import load_model_pins, load_workload_config, resolve_model
from scripts.harness.contracts import FailureCategory


REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_PINS = REPO_ROOT / "configs" / "aiinfra" / "models.json"
RESULT_FILENAME = "workload_result.json"
WORKLOADS = {"determinism"}


def _fail(category: str, message: str) -> int:
    print(f"[run-status] status=failed reason={category}", file=sys.stderr)
    print(f"[error] {message}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Materialised workload configuration")
    args = parser.parse_args(argv)

    run_dir = args.config.resolve().parent
    try:
        config = load_workload_config(args.config)
        if config.workload not in WORKLOADS:
            raise WorkloadFailure(
                FailureCategory.CONFIGURATION.value,
                f"unknown workload {config.workload!r}; known: {sorted(WORKLOADS)}",
            )
        model = resolve_model(config, load_model_pins(MODEL_PINS))
    except WorkloadFailure as exc:
        return _fail(exc.category, str(exc))
    except ValueError as exc:
        return _fail(FailureCategory.CONFIGURATION.value, str(exc))

    try:
        backend = get_backend(config.backend, model=model, options=config.options)
        cells = determinism.measure_cells(backend, config)
    except WorkloadFailure as exc:
        return _fail(exc.category, str(exc))
    except MemoryError as exc:
        return _fail(FailureCategory.RESOURCE_EXHAUSTED.value, f"MemoryError: {exc}")

    document = result_schema.build_workload_result(
        workload=config.workload,
        backend=backend.describe(),
        model=model,
        environment=environment.probe(),
        cells=cells,
        completed=len(cells),
        expected=len(config.batch_sizes),
    )
    try:
        result_schema.validate_workload_result(document)
    except ValueError as exc:
        return _fail(FailureCategory.SCHEMA.value, str(exc))

    (run_dir / RESULT_FILENAME).write_text(
        json.dumps(document, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"[run-status] status=success kind=workload "
        f"completed={len(cells)} expected={len(config.batch_sizes)}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
