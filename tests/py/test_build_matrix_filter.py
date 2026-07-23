import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.build_matrix import BuildVariant, generate_variants


def test_default_output_unchanged():
    variants = generate_variants()
    names = [v.name for v in variants]
    assert names == [
        "cpu-double-O2-ieee-leq",
        "cpu-double-O2-ieee-strict",
        "cpu-double-O2-fastmath-leq",
        "cpu-double-O2-fastmath-strict",
        "cpu-double-O3-ieee-leq",
        "cpu-double-O3-ieee-strict",
        "cpu-double-O3-fastmath-leq",
        "cpu-double-O3-fastmath-strict",
        "cpu-double-Ofast-ieee-leq",
        "cpu-double-Ofast-ieee-strict",
        "cpu-double-Ofast-fastmath-leq",
        "cpu-double-Ofast-fastmath-strict",
        "cpu-float-O2-ieee-leq",
        "cpu-float-O2-ieee-strict",
        "cpu-float-O2-fastmath-leq",
        "cpu-float-O2-fastmath-strict",
        "cpu-float-O3-ieee-leq",
        "cpu-float-O3-ieee-strict",
        "cpu-float-O3-fastmath-leq",
        "cpu-float-O3-fastmath-strict",
        "cpu-float-Ofast-ieee-leq",
        "cpu-float-Ofast-ieee-strict",
        "cpu-float-Ofast-fastmath-leq",
        "cpu-float-Ofast-fastmath-strict",
    ]


def _p0(v: BuildVariant) -> bool:
    return v.opt_level in ("O2", "Ofast") and v.fast_math is False


def test_filter_selects_exactly_p0_eight():
    variants = generate_variants(filter=_p0)
    names = [v.name for v in variants]
    assert names == [
        "cpu-double-O2-ieee-leq",
        "cpu-double-O2-ieee-strict",
        "cpu-double-Ofast-ieee-leq",
        "cpu-double-Ofast-ieee-strict",
        "cpu-float-O2-ieee-leq",
        "cpu-float-O2-ieee-strict",
        "cpu-float-Ofast-ieee-leq",
        "cpu-float-Ofast-ieee-strict",
    ]


def test_ofast_is_recorded_as_effective_fast_without_renaming():
    variant = BuildVariant("double", "Ofast", False, False)

    assert variant.name == "cpu-double-Ofast-ieee-leq"
    assert variant.build_dir == Path("build-matrix/cpu-double-Ofast-ieee-leq")
    assert variant.effective_math_mode == "fast"


def test_o2_without_fast_math_is_compiler_default_not_claimed_ieee():
    variant = BuildVariant("double", "O2", False, False)

    assert variant.name == "cpu-double-O2-ieee-leq"
    assert variant.effective_math_mode == "compiler-default"
