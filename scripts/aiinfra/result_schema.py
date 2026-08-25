"""Single source of truth for the `aiinfra.workload-result` document."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any


SCHEMA = {"name": "aiinfra.workload-result", "version": 1}

TOP_LEVEL_FIELDS = {
    "schema",
    "workload",
    "backend",
    "model",
    "environment",
    "cells",
    "completion",
}
BACKEND_FIELDS = {"name", "version", "requested_path", "effective_path"}
MODEL_FIELDS = {"id", "revision", "dtype"}
CELL_FIELDS = {
    "cell_id",
    "axes",
    "repeats",
    "unique_output_count",
    "reproduction_rate",
    "output_digests",
    "latency_median_s",
    "latency_iqr_s",
}


def _exact_fields(value: Any, fields: set[str], where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"workload result {where} must be an object")
    missing = sorted(fields - value.keys())
    unexpected = sorted(value.keys() - fields)
    if missing:
        raise ValueError(f"workload result {where} is missing {', '.join(missing)}")
    if unexpected:
        raise ValueError(f"workload result {where} has unexpected {', '.join(unexpected)}")
    return value


def _finite(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"workload result {where} must be a number")
    if not math.isfinite(float(value)):
        raise ValueError(f"workload result {where} must be finite")
    return float(value)


def _nonneg_int(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"workload result {where} must be a non-negative integer")
    return value


def _nonempty_string(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"workload result {where} must be a non-empty string")
    return value


def validate_workload_result(document: Any) -> None:
    """Raise ValueError with one readable reason if *document* is not schema v1."""
    _exact_fields(document, TOP_LEVEL_FIELDS, "document")

    schema = _exact_fields(document["schema"], set(SCHEMA), "schema")
    if schema["name"] != SCHEMA["name"]:
        raise ValueError("workload result schema.name is unsupported")
    if type(schema["version"]) is not int or schema["version"] != SCHEMA["version"]:
        raise ValueError("workload result schema.version is unsupported")

    _nonempty_string(document["workload"], "workload")

    backend = _exact_fields(document["backend"], BACKEND_FIELDS, "backend")
    for field in sorted(BACKEND_FIELDS):
        _nonempty_string(backend[field], f"backend.{field}")

    model = _exact_fields(document["model"], MODEL_FIELDS, "model")
    for field in sorted(MODEL_FIELDS):
        _nonempty_string(model[field], f"model.{field}")

    if not isinstance(document["environment"], Mapping):
        raise ValueError("workload result environment must be an object")

    cells = document["cells"]
    if not isinstance(cells, Sequence) or isinstance(cells, str) or not cells:
        raise ValueError("workload result cells must be a non-empty array")
    for index, cell in enumerate(cells):
        where = f"cells[{index}]"
        _exact_fields(cell, CELL_FIELDS, where)
        _nonempty_string(cell["cell_id"], f"{where}.cell_id")
        if not isinstance(cell["axes"], Mapping):
            raise ValueError(f"workload result {where}.axes must be an object")
        repeats = _nonneg_int(cell["repeats"], f"{where}.repeats")
        if repeats == 0:
            raise ValueError(f"workload result {where}.repeats must be positive")
        unique = _nonneg_int(cell["unique_output_count"], f"{where}.unique_output_count")
        digests = cell["output_digests"]
        if not isinstance(digests, Sequence) or isinstance(digests, str):
            raise ValueError(f"workload result {where}.output_digests must be an array")
        if len(digests) != repeats:
            raise ValueError(
                f"workload result {where}.output_digests must hold one digest per repeat"
            )
        if any(not isinstance(digest, str) for digest in digests):
            raise ValueError(
                f"workload result {where}.output_digests must contain only strings"
            )
        if len(set(digests)) != unique:
            raise ValueError(
                f"workload result {where}.unique_output_count disagrees with output_digests"
            )
        rate = _finite(cell["reproduction_rate"], f"{where}.reproduction_rate")
        if not 0.0 <= rate <= 1.0:
            raise ValueError(f"workload result {where}.reproduction_rate must lie in [0, 1]")
        expected_rate = max(Counter(digests).values()) / repeats
        # Permit only a few ULPs for a decimal serialization of the exact ratio.
        if not math.isclose(
            rate,
            expected_rate,
            rel_tol=0.0,
            abs_tol=8 * math.ulp(expected_rate),
        ):
            raise ValueError(
                f"workload result {where}.reproduction_rate disagrees with "
                "output_digests"
            )
        _finite(cell["latency_median_s"], f"{where}.latency_median_s")
        _finite(cell["latency_iqr_s"], f"{where}.latency_iqr_s")

    completion = _exact_fields(
        document["completion"], {"completed", "expected"}, "completion"
    )
    completed = _nonneg_int(completion["completed"], "completion.completed")
    expected = _nonneg_int(completion["expected"], "completion.expected")
    if expected == 0:
        raise ValueError("workload result completion.expected must be positive")
    if completed != expected:
        raise ValueError(
            f"workload result completion is partial: {completed} of {expected}"
        )


def build_workload_result(
    *,
    workload: str,
    backend: Mapping[str, str],
    model: Mapping[str, str],
    environment: Mapping[str, Any],
    cells: Sequence[Mapping[str, Any]],
    completed: int,
    expected: int,
) -> dict[str, Any]:
    """Assemble a schema-v1 document; the caller validates before writing."""
    return {
        "schema": dict(SCHEMA),
        "workload": workload,
        "backend": dict(backend),
        "model": dict(model),
        "environment": dict(environment),
        "cells": [dict(cell) for cell in cells],
        "completion": {"completed": completed, "expected": expected},
    }
