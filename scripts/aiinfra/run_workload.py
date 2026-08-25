#!/usr/bin/env python3
"""Matrix entry point for aiinfra workloads."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

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


def _unexpected_failure(exc: Exception) -> int:
    return _fail(FailureCategory.INFRASTRUCTURE.value, f"{type(exc).__name__}: {exc}")


def _clear_canonical_result(result_path: Path) -> None:
    """Remove a prior attempt's canonical result before starting this attempt."""
    try:
        result_path.unlink()
    except FileNotFoundError:
        pass


def _write_result_atomically(result_path: Path, document: dict[str, Any]) -> None:
    """Publish a validated document without exposing a partial canonical result."""
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=result_path.parent,
            prefix=f".{result_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(document, temporary, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        temporary_path.replace(result_path)
    except Exception:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except (FileNotFoundError, OSError):
                pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Materialised workload configuration")
    args = parser.parse_args(argv)

    requested_result_path = args.config.parent / RESULT_FILENAME
    try:
        _clear_canonical_result(requested_result_path)
    except Exception as exc:
        return _fail(
            FailureCategory.ARTIFACT.value,
            f"cannot clear {requested_result_path}: {exc}",
        )

    try:
        resolved_config = args.config.resolve()
    except WorkloadFailure as exc:
        return _fail(exc.category, str(exc))
    except ValueError as exc:
        return _fail(FailureCategory.CONFIGURATION.value, str(exc))
    except MemoryError as exc:
        return _fail(FailureCategory.RESOURCE_EXHAUSTED.value, f"MemoryError: {exc}")
    except Exception as exc:
        return _unexpected_failure(exc)

    result_path = resolved_config.parent / RESULT_FILENAME
    if result_path != requested_result_path:
        try:
            _clear_canonical_result(result_path)
        except Exception as exc:
            return _fail(
                FailureCategory.ARTIFACT.value,
                f"cannot clear {result_path}: {exc}",
            )

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
    except MemoryError as exc:
        return _fail(FailureCategory.RESOURCE_EXHAUSTED.value, f"MemoryError: {exc}")
    except Exception as exc:
        return _unexpected_failure(exc)

    try:
        backend = get_backend(config.backend, model=model, options=config.options)
        cells = determinism.measure_cells(backend, config)
    except WorkloadFailure as exc:
        return _fail(exc.category, str(exc))
    except MemoryError as exc:
        return _fail(FailureCategory.RESOURCE_EXHAUSTED.value, f"MemoryError: {exc}")
    except Exception as exc:
        return _unexpected_failure(exc)

    try:
        document = result_schema.build_workload_result(
            workload=config.workload,
            backend=backend.describe(),
            model=model,
            environment=environment.probe(),
            cells=cells,
            completed=len(cells),
            expected=len(config.batch_sizes),
        )
        result_schema.validate_workload_result(document)
    except WorkloadFailure as exc:
        return _fail(exc.category, str(exc))
    except MemoryError as exc:
        return _fail(FailureCategory.RESOURCE_EXHAUSTED.value, f"MemoryError: {exc}")
    except Exception as exc:
        return _unexpected_failure(exc)

    try:
        _write_result_atomically(result_path, document)
    except OSError as exc:
        return _fail(FailureCategory.ARTIFACT.value, f"cannot write {result_path}: {exc}")
    except Exception as exc:
        return _unexpected_failure(exc)
    print(
        f"[run-status] status=success kind=workload "
        f"completed={len(cells)} expected={len(config.batch_sizes)}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
