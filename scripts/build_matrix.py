#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Callable, Optional


@dataclass(frozen=True)
class BuildVariant:
    precision: str
    opt_level: str
    fast_math: bool
    strict_riemann: bool
    hardware: str = "cpu"

    @property
    def name(self) -> str:
        math = "fastmath" if self.fast_math else "ieee"
        riemann = "strict" if self.strict_riemann else "leq"
        return f"{self.hardware}-{self.precision}-{self.opt_level}-{math}-{riemann}"

    @property
    def build_dir(self) -> Path:
        return Path("build-matrix") / self.name

    @property
    def effective_math_mode(self) -> str:
        if self.opt_level == "Ofast" or self.fast_math:
            return "fast"
        return "compiler-default"

    def cmake_args(self) -> list[str]:
        return [
            f"-DFLOAT_PRECISION={self.precision}",
            f"-DOPT_LEVEL={self.opt_level}",
            f"-DFAST_MATH={'ON' if self.fast_math else 'OFF'}",
            f"-DRIEMANN_STRICT_INEQUALITY={'ON' if self.strict_riemann else 'OFF'}",
            "-DENABLE_OPENMP=ON",
        ]


def generate_variants(
    precisions: tuple[str, ...] = ("double", "float"),
    opt_levels: tuple[str, ...] = ("O2", "O3", "Ofast"),
    fast_math_values: tuple[bool, ...] = (False, True),
    strict_values: tuple[bool, ...] = (False, True),
    filter: Optional[Callable[[BuildVariant], bool]] = None,
) -> list[BuildVariant]:
    variants = [
        BuildVariant(
            precision=precision,
            opt_level=opt_level,
            fast_math=fast_math,
            strict_riemann=strict,
        )
        for precision, opt_level, fast_math, strict in product(
            precisions, opt_levels, fast_math_values, strict_values
        )
    ]
    if filter is not None:
        variants = [variant for variant in variants if filter(variant)]
    return variants
