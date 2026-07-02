#!/usr/bin/env python3
"""Week-14 deterministic MHD precision-pilot driver."""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import pathlib
import subprocess
import sys
from typing import Any

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASE = ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg"
DEFAULT_OUT = ROOT / "experiments" / "week14" / "mhd_precision_pilot"
EXPERIMENT = "week14-mhd-precision-pilot"

for path in (
    ROOT,
    ROOT / "scripts",
    ROOT / "scripts" / "figures",
    ROOT / "scripts" / "metrics",
    ROOT / "scripts" / "regression",
    ROOT / "scripts" / "verificarlo",
):
    sys.path.insert(0, str(path))

from scripts.build_matrix import BuildVariant, generate_variants  # noqa: E402
from mhd_fields import field_norms  # noqa: E402
from io_helper import read_binary  # noqa: E402
from _mhd_harness import (  # noqa: E402
    git_commit,
    parse_mhd_diagnostics,
    replace_or_append_cfg,
    resolve_binary,
    run_case,
    sha256_file,
)
import mhd_precision_pilot_core as core  # noqa: E402
from mhd_precision_pilot_core import assemble_summary, write_summaries  # noqa: E402
from mhd_precision_pilot_plots import (  # noqa: E402
    plot_mca_noise_floor,
    plot_precision_variant_norms,
)


def p0_filter(v: BuildVariant) -> bool:
    """Select P0: O2/Ofast, IEEE math, both precisions, both Riemann flags."""
    return (
        v.hardware == "cpu"
        and v.opt_level in {"O2", "Ofast"}
        and v.fast_math is False
        and v.precision in {"double", "float"}
        and v.strict_riemann in {False, True}
    )


def select_variants(phase: str) -> list[BuildVariant]:
    """Return deterministic variants for the requested pilot phase."""
    if phase == "p0":
        return generate_variants(filter=p0_filter)
    if phase == "p1":
        return generate_variants()
    raise ValueError(f"unknown phase {phase!r}; expected 'p0' or 'p1'")


def ordered_variants_reference_first(variants: list[BuildVariant]) -> list[BuildVariant]:
    """Return variants with the deterministic reference variant first."""
    refs = [variant for variant in variants if variant.name == core.REFERENCE]
    if not refs:
        raise ValueError(f"selected variants do not include reference {core.REFERENCE}")
    return refs[:1] + [variant for variant in variants if variant.name != core.REFERENCE]


def build_variant(variant: BuildVariant) -> pathlib.Path:
    """Configure/build one build-matrix variant and return its hrsc_mhd binary."""
    build_dir = ROOT / variant.build_dir
    cmake_configure = [
        "cmake",
        "-S",
        str(ROOT),
        "-B",
        str(build_dir),
        "-G",
        "Ninja",
        *variant.cmake_args(),
    ]
    subprocess.run(cmake_configure, cwd=str(ROOT), check=True)
    subprocess.run(
        ["cmake", "--build", str(build_dir), "--target", "hrsc_mhd"],
        cwd=str(ROOT),
        check=True,
    )
    return resolve_binary(build_dir / "hrsc_mhd")


def write_matrix_json(variants: list[BuildVariant], out_dir: pathlib.Path) -> pathlib.Path:
    """Write a reproducible matrix manifest for the selected Brio-Wu runs."""
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    runs = []
    for variant in variants:
        runs.append(
            {
                "name": variant.name,
                "binary": str(_manifest_binary_path(variant)),
                "config": str(CASE.relative_to(ROOT)).replace("\\", "/"),
                "precision": variant.precision,
                "build": variant.name,
                "output_file": "grid.bin",
            }
        )
    path = out / "matrix.json"
    payload = {
        "experiment": EXPERIMENT,
        "output_root": str(out.relative_to(ROOT) if out.is_relative_to(ROOT) else out),
        "runs": runs,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def measure_run(
    variant: BuildVariant,
    arr: np.ndarray,
    ref_arr: np.ndarray,
    gamma: float,
    dx: float,
    diagnostics: dict[str, Any],
    walltime_s: float,
) -> dict[str, Any]:
    """Measure one deterministic row against the reference grid."""
    finite = bool(np.isfinite(arr).all() and np.isfinite(ref_arr).all())
    if finite:
        norms = field_norms(
            arr.astype(np.float64, copy=False),
            ref_arr.astype(np.float64, copy=False),
            gamma,
            dx,
        )
    else:
        norms = _zero_norms()
    row: dict[str, Any] = {
        "variant": variant.name,
        "precision": variant.precision,
        "opt": variant.opt_level,
        "fastmath": bool(variant.fast_math),
        "riemann": "strict" if variant.strict_riemann else "leq",
        "finite": finite,
        "rc": 0,
        "steps": int(diagnostics.get("steps", 0)),
        "divB_max": _finite_float(diagnostics.get("divB_max", 0.0)),
        "walltime_s": _finite_float(walltime_s),
        "is_reference": variant.name == core.REFERENCE,
    }
    row.update({key: _finite_float(value) for key, value in norms.items()})
    return row


def _manifest_binary_path(variant: BuildVariant) -> pathlib.Path:
    binary = variant.build_dir / "hrsc_mhd"
    if (ROOT / binary).is_file():
        return binary
    exe_binary = pathlib.Path(str(binary) + ".exe")
    if (ROOT / exe_binary).is_file() or os.name == "nt":
        return exe_binary
    return binary


def _zero_norms() -> dict[str, float]:
    return {
        f"{norm}_{field}": 0.0
        for field in ("rho", "By", "p", "vx")
        for norm in ("L1", "L2", "Linf")
    }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    out = _resolve_out(args.out)
    out.mkdir(parents=True, exist_ok=True)

    variants = select_variants(args.phase)
    write_matrix_json(variants, out)

    commit = git_commit()
    gamma = _cfg_float(CASE, "gamma", 2.0)
    rows = _run_deterministic(variants, out, gamma, commit, keep_grids=args.keep_grids)
    mca = _load_or_run_mca(args, out)

    summary = assemble_summary(rows, mca, commit)
    write_summaries(summary, out)
    plot_precision_variant_norms(summary, out / "figures" / "deterministic_norms.png")
    plot_mca_noise_floor(summary, out / "figures" / "mca_noise_floor.png")

    print((out / "summary.md").read_text(encoding="utf-8"), end="")
    return 0 if summary.get("gates", {}).get("G0", {}).get("pass") is True else 1


def _run_deterministic(
    variants: list[BuildVariant],
    out: pathlib.Path,
    gamma: float,
    commit: str,
    *,
    keep_grids: bool,
) -> list[dict[str, Any]]:
    ordered = ordered_variants_reference_first(variants)
    ref_arr = None
    rows = []
    for variant in ordered:
        binary = build_variant(variant)
        grid_path = out / "runs" / variant.name / "grid.bin"
        meta, arr, header = _run_one(variant, binary, out, commit, grid_path)
        if ref_arr is None:
            ref_arr = arr
        rows.append(
            measure_run(
                variant,
                arr,
                ref_arr,
                gamma,
                dx=float(header.dx),
                diagnostics=meta.get("stderr_diagnostics", {}),
                walltime_s=float(meta.get("elapsed_wall_s", 0.0)),
            )
        )
        if not keep_grids and grid_path.is_file() and grid_path.parent == out / "runs" / variant.name:
            grid_path.unlink()
    return rows


def _run_one(
    variant: BuildVariant,
    binary: pathlib.Path,
    out: pathlib.Path,
    commit: str,
    grid_path: pathlib.Path,
) -> tuple[dict[str, Any], np.ndarray, Any]:
    cfg_text = CASE.read_text(encoding="utf-8")
    cfg_text = replace_or_append_cfg(cfg_text, "output_format", "binary")
    cfg_text = replace_or_append_cfg(cfg_text, "output_file", str(grid_path))
    binary_sha = sha256_file(binary)
    _result, meta, stderr_text = run_case(
        variant.name,
        cfg_text,
        out / "runs" / variant.name,
        binary,
        CASE,
        commit,
        binary_sha,
        output_bin=grid_path,
        experiment=EXPERIMENT,
    )
    if "stderr_diagnostics" not in meta or not meta["stderr_diagnostics"]:
        meta["stderr_diagnostics"] = parse_mhd_diagnostics(stderr_text)
    header, arr = read_binary(grid_path)
    return meta, arr, header


def _load_or_run_mca(args: argparse.Namespace, out: pathlib.Path) -> dict[str, Any]:
    if args.skip_mca:
        return {
            "p53": core.blocked_mca_block("blocked_environment", "MCA skipped via --skip-mca"),
            "p24": core.blocked_mca_block("blocked_environment", "MCA skipped via --skip-mca"),
        }
    if args.mca_summary is not None:
        payload = json.loads(args.mca_summary.read_text(encoding="utf-8"))
        return payload.get("mca", payload)
    sampler = importlib.import_module("mhd_precision_sampling")
    mca_out = out / "mca"
    return {
            "p53": sampler.sample_precision(
                mca_out / "p53",
                precision=53,
                samples=args.samples,
                image=args.mca_image,
            ),
            "p24": sampler.sample_precision(
                mca_out / "p24",
                precision=24,
                samples=args.samples,
                image=args.mca_image,
            ),
        }


def _cfg_float(path: pathlib.Path, key: str, default: float) -> float:
    for line in path.read_text(encoding="utf-8").splitlines():
        content = line.split("#", 1)[0].strip()
        if not content or "=" not in content:
            continue
        lhs, rhs = [part.strip() for part in content.split("=", 1)]
        if lhs == key:
            return float(rhs)
    return default


def _finite_float(value: Any) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"expected finite numeric value, got {value!r}")
    return number


def _resolve_out(path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else ROOT / path


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--phase", choices=("p0", "p1"), default="p0")
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--keep-grids", action="store_true")
    parser.add_argument("--skip-mca", action="store_true")
    parser.add_argument("--mca-summary", type=pathlib.Path)
    parser.add_argument("--mca-image", default="verificarlo/verificarlo")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
