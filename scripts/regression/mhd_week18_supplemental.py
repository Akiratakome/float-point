#!/usr/bin/env python3
"""Week 18 MHD robustness experiments for the Report 2 evidence packet."""

from __future__ import annotations

import pathlib
import sys
from collections.abc import Iterable
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]

for path in (ROOT, ROOT / "scripts", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(path))

from _mhd_harness import replace_or_append_cfg  # noqa: E402


CASES_2D = ("orszag_tang_2d", "kelvin_helmholtz_2d")
PRECISIONS = ("double", "float")


def hardware_plan(repeats: int = 5) -> list[dict[str, Any]]:
    if repeats < 1:
        raise ValueError("repeats must be positive")
    return [
        {
            "suite": "hardware_repeats",
            "case": case,
            "precision": precision,
            "device": device,
            "repeat": repeat,
            "solver": "hll",
        }
        for case in ("brio_wu_1d", "orszag_tang_2d")
        for precision in PRECISIONS
        for repeat in range(1, repeats + 1)
        for device in ("cpu", "gpu")
    ]


def thread_plan(threads: Iterable[int] = (1, 2, 4, 8)) -> list[dict[str, Any]]:
    values = tuple(int(thread) for thread in threads)
    if not values or any(thread < 1 for thread in values):
        raise ValueError("thread counts must be positive")
    return [
        {
            "suite": "thread_repro",
            "case": case,
            "precision": precision,
            "device": "cpu",
            "solver": "hll",
            "omp_num_threads": thread,
        }
        for case in CASES_2D
        for precision in PRECISIONS
        for thread in values
    ]


def cfl_plan(
    cfl_values: Iterable[float] = (0.2, 0.4, 0.6, 0.8),
) -> list[dict[str, Any]]:
    values = tuple(float(cfl) for cfl in cfl_values)
    if not values or any(cfl <= 0.0 for cfl in values):
        raise ValueError("CFL values must be positive")
    return [
        {
            "suite": "kh_cfl",
            "case": "kelvin_helmholtz_2d",
            "precision": precision,
            "device": "cpu",
            "solver": solver,
            "cfl": cfl,
        }
        for solver in ("hll", "hlld")
        for precision in PRECISIONS
        for cfl in values
    ]


def generated_cfg(
    base_text: str,
    overrides: dict[str, Any],
    output_file: pathlib.Path,
    device: str,
) -> str:
    text = base_text
    for key, value in overrides.items():
        text = replace_or_append_cfg(text, key, str(value))
    for key, value in (
        ("device", device),
        ("output_format", "binary"),
        ("output_file", str(output_file)),
    ):
        text = replace_or_append_cfg(text, key, value)
    return text
