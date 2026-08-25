"""Loading and fail-closed validation of aiinfra workload configurations."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CONFIG_SCHEMA = {"name": "aiinfra.workload-config", "version": 1}
PINS_SCHEMA = {"name": "aiinfra.model-pins", "version": 1}
CONFIG_FIELDS = {
    "schema",
    "workload",
    "backend",
    "model",
    "dtype",
    "prompt",
    "max_new_tokens",
    "repeats",
    "batch_sizes",
    "seed",
    "decode",
    "options",
}
PIN_FIELDS = {"id", "revision", "source", "approx_weight_bytes"}
SUPPORTED_DECODES = {"greedy"}
SUPPORTED_DTYPES = {"float32", "float16", "bfloat16"}


@dataclass(frozen=True)
class WorkloadConfig:
    """The schema-v1 workload settings required for one aiinfra run."""

    workload: str
    backend: str
    model_key: str
    dtype: str
    prompt: str
    max_new_tokens: int
    repeats: int
    batch_sizes: tuple[int, ...]
    seed: int
    decode: str
    options: dict[str, Any] = field(default_factory=dict)


def _reject_non_standard_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _read_json(path: Path) -> Any:
    try:
        return json.loads(
            Path(path).read_text(encoding="utf-8-sig"),
            parse_constant=_reject_non_standard_json_constant,
        )
    except (OSError, UnicodeError, ValueError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc


def _exact_fields(value: Any, fields: set[str], where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{where} must be an object")
    missing = sorted(fields - value.keys())
    unexpected = sorted(value.keys() - fields)
    if missing:
        raise ValueError(f"{where} is missing {', '.join(missing)}")
    if unexpected:
        raise ValueError(f"{where} has unexpected {', '.join(unexpected)}")
    return value


def _check_schema(value: Any, expected: Mapping[str, Any], where: str) -> None:
    schema = _exact_fields(value, set(expected), where)
    if schema != expected:
        raise ValueError(f"{where} is unsupported: {schema}")


def _nonempty_string(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{where} must be a non-empty string")
    return value


def _positive_int(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{where} must be a positive integer")
    return value


def _nonnegative_int(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{where} must be a non-negative integer")
    return value


def load_workload_config(path: Path) -> WorkloadConfig:
    """Load *path* as a schema-v1 workload configuration or raise ValueError."""
    document = _read_json(path)
    _exact_fields(document, CONFIG_FIELDS, "workload config")
    _check_schema(document["schema"], CONFIG_SCHEMA, "workload config schema")

    workload = _nonempty_string(document["workload"], "workload config workload")
    backend = _nonempty_string(document["backend"], "workload config backend")
    model_key = _nonempty_string(document["model"], "workload config model")
    prompt = _nonempty_string(document["prompt"], "workload config prompt")
    dtype = document["dtype"]
    if not isinstance(dtype, str) or dtype not in SUPPORTED_DTYPES:
        raise ValueError(f"workload config dtype must be one of {sorted(SUPPORTED_DTYPES)}")
    decode = document["decode"]
    if not isinstance(decode, str) or decode not in SUPPORTED_DECODES:
        raise ValueError(f"workload config decode must be one of {sorted(SUPPORTED_DECODES)}")

    batch_sizes = document["batch_sizes"]
    if not isinstance(batch_sizes, list) or not batch_sizes:
        raise ValueError("workload config batch_sizes must be a non-empty array")
    for index, size in enumerate(batch_sizes):
        _positive_int(size, f"workload config batch_sizes[{index}]")
    options = document["options"]
    if not isinstance(options, Mapping):
        raise ValueError("workload config options must be an object")

    return WorkloadConfig(
        workload=workload,
        backend=backend,
        model_key=model_key,
        dtype=dtype,
        prompt=prompt,
        max_new_tokens=_positive_int(document["max_new_tokens"], "workload config max_new_tokens"),
        repeats=_positive_int(document["repeats"], "workload config repeats"),
        batch_sizes=tuple(batch_sizes),
        seed=_nonnegative_int(document["seed"], "workload config seed"),
        decode=decode,
        options=dict(options),
    )


def load_model_pins(path: Path) -> dict[str, dict[str, Any]]:
    """Load a schema-v1 model pin table or raise ValueError."""
    document = _read_json(path)
    _exact_fields(document, {"schema", "models"}, "model pins")
    _check_schema(document["schema"], PINS_SCHEMA, "model pins schema")
    models = document["models"]
    if not isinstance(models, Mapping) or not models:
        raise ValueError("model pins models must be a non-empty object")

    resolved: dict[str, dict[str, Any]] = {}
    for key, pin in models.items():
        model_key = _nonempty_string(key, "model pins model key")
        pin = _exact_fields(pin, PIN_FIELDS, f"model pins models[{model_key!r}]")
        resolved[model_key] = {
            "id": _nonempty_string(pin["id"], f"model pins models[{model_key!r}].id"),
            "revision": _nonempty_string(
                pin["revision"], f"model pins models[{model_key!r}].revision"
            ),
            "source": _nonempty_string(pin["source"], f"model pins models[{model_key!r}].source"),
            "approx_weight_bytes": _nonnegative_int(
                pin["approx_weight_bytes"],
                f"model pins models[{model_key!r}].approx_weight_bytes",
            ),
        }
    return resolved


def resolve_model(
    config: WorkloadConfig, pins: Mapping[str, Mapping[str, Any]]
) -> dict[str, str]:
    """Return the run-record model block for *config*, or raise on an unpinned key."""
    try:
        pin = pins[config.model_key]
    except (KeyError, TypeError) as exc:
        raise ValueError(
            f"workload config model {config.model_key!r} is not pinned in models.json"
        ) from exc
    if not isinstance(pin, Mapping):
        raise ValueError(f"model pin for {config.model_key!r} must be an object")
    try:
        model_id = _nonempty_string(pin["id"], f"model pin {config.model_key!r}.id")
        revision = _nonempty_string(
            pin["revision"], f"model pin {config.model_key!r}.revision"
        )
    except KeyError as exc:
        raise ValueError(f"model pin for {config.model_key!r} is incomplete") from exc
    return {"id": model_id, "revision": revision, "dtype": config.dtype}
