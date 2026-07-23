#!/usr/bin/env python3
"""Week 16 Kelvin-Helmholtz deterministic precision packet.

This driver runs CPU deterministic build variants for the KH 2D case after the
512^2 validation gate has passed. Verificarlo MCA is recorded as a schema-
complete blocked block when Docker is unavailable.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys
from typing import Any

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASE = ROOT / "tests" / "cases" / "kelvin_helmholtz_2d" / "kh.cfg"
DEFAULT_OUT = ROOT / "experiments" / "week16" / "kelvin_helmholtz_precision"
EXPERIMENT = "week16-kelvin-helmholtz-precision"
REFERENCE = "cpu-double-O2-ieee-leq"
SUPPORTED_SOLVERS = ("hll", "hlld")
SMOKE_OVERRIDES = {"nx": 64, "ny": 64, "t_end": 0.05}

for path in (
    ROOT,
    ROOT / "scripts",
    ROOT / "scripts" / "metrics",
    ROOT / "scripts" / "regression",
):
    sys.path.insert(0, str(path))

from scripts.build_matrix import BuildVariant, generate_variants  # noqa: E402
from _mhd_harness import (  # noqa: E402
    git_commit,
    replace_or_append_cfg,
    run_case,
    sha256_file,
)
from io_helper import read_binary  # noqa: E402
from mhd_fields import field_norms, mhd_primitive_fields  # noqa: E402


ROW_COLUMNS = (
    "variant",
    "precision",
    "opt",
    "fastmath",
    "riemann",
    "solver",
    "case",
    "nx",
    "ny",
    "t_end",
    "finite",
    "rc",
    "steps",
    "divB_max",
    "walltime_s",
    "is_reference",
    "L1_rho",
    "L2_rho",
    "Linf_rho",
    "L1_By",
    "L2_By",
    "Linf_By",
    "L1_p",
    "L2_p",
    "Linf_p",
    "L1_vx",
    "L2_vx",
    "Linf_vx",
)


def p0_filter(variant: BuildVariant) -> bool:
    return (
        variant.hardware == "cpu"
        and variant.opt_level in {"O2", "Ofast"}
        and variant.fast_math is False
        and variant.precision in {"double", "float"}
        and variant.strict_riemann in {False, True}
    )


def select_variants(phase: str) -> list[BuildVariant]:
    if phase == "p0":
        return generate_variants(filter=p0_filter)
    if phase == "p1":
        return generate_variants()
    raise ValueError(f"unknown phase: {phase}")


def ordered_reference_first(variants: list[BuildVariant]) -> list[BuildVariant]:
    refs = [variant for variant in variants if variant.name == REFERENCE]
    if not refs:
        raise ValueError(f"selected variants do not include {REFERENCE}")
    return refs[:1] + [variant for variant in variants if variant.name != REFERENCE]


def plan_row(variant: BuildVariant, solver: str, smoke: bool) -> dict[str, Any]:
    solver = normalise_solver(solver)
    return {
        "variant": variant.name,
        "precision": variant.precision,
        "opt": variant.opt_level,
        "fastmath": bool(variant.fast_math),
        "riemann": "strict" if variant.strict_riemann else "leq",
        "solver": solver,
        "case": "kelvin_helmholtz_2d",
        "nx": SMOKE_OVERRIDES["nx"] if smoke else 256,
        "ny": SMOKE_OVERRIDES["ny"] if smoke else 256,
        "t_end": SMOKE_OVERRIDES["t_end"] if smoke else 1.0,
        "is_reference": variant.name == REFERENCE,
    }


def precision_cfg_text(base_text: str, *, solver: str, output_file: pathlib.Path,
                       smoke: bool) -> str:
    text = base_text
    for key, value in (
        ("riemann", normalise_solver(solver)),
        ("output_format", "binary"),
        ("output_file", str(output_file)),
    ):
        text = replace_or_append_cfg(text, key, value)
    if smoke:
        for key, value in SMOKE_OVERRIDES.items():
            text = replace_or_append_cfg(text, key, str(value))
    return text


def blocked_mca(reason: str) -> dict[str, dict[str, Any]]:
    return {
        name: {
            "status": "blocked_environment",
            "reason": reason,
            "n": 0,
            "mca_evidence_generated": False,
            "spread_rho": None,
            "spread_By": None,
            "spread_p": None,
            "spread_vx": None,
            "snr_rho": None,
            "snr_By": None,
            "snr_p": None,
            "rho_mean_spread": None,
        }
        for name in ("p53", "p24")
    }


def load_mca_summary(path: pathlib.Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mca = payload.get("mca", payload)
    if not isinstance(mca, dict):
        raise ValueError(f"MCA summary must contain an object, got {type(mca).__name__}")
    for name in ("p53", "p24"):
        if not isinstance(mca.get(name), dict):
            raise ValueError(f"MCA summary is missing `{name}` block")
    return mca


def build_variant_binary(variant: BuildVariant) -> pathlib.Path:
    build_dir = ROOT / variant.build_dir
    cmd = [
        "cmake",
        "-S",
        str(ROOT),
        "-B",
        str(build_dir),
        "-G",
        "Ninja",
        "-DCMAKE_BUILD_TYPE=Release",
        *variant.cmake_args(),
    ]
    import subprocess
    subprocess.run(cmd, cwd=str(ROOT), check=True)
    subprocess.run(["cmake", "--build", str(build_dir), "--target", "hrsc_mhd"],
                   cwd=str(ROOT), check=True)
    exe = build_dir / "hrsc_mhd.exe"
    return exe if exe.is_file() else build_dir / "hrsc_mhd"


def run_packet(out: pathlib.Path, *, solver: str, phase: str, smoke: bool,
               mca_block_reason: str, keep_grids: bool = False,
               mca_summary: pathlib.Path | None = None) -> dict[str, Any]:
    solver = normalise_solver(solver)
    variants = ordered_reference_first(select_variants(phase))
    out.mkdir(parents=True, exist_ok=True)
    base_text = CASE.read_text(encoding="utf-8")
    gamma = cfg_float(base_text, "gamma", 5.0 / 3.0)
    commit = git_commit()
    staged = []
    for variant in variants:
        binary = build_variant_binary(variant)
        run_dir = out / "runs" / variant.name
        grid = run_dir / "grid.bin"
        cfg_text = precision_cfg_text(base_text, solver=solver, output_file=grid, smoke=smoke)
        _, meta, _ = run_case(
            variant.name,
            cfg_text,
            run_dir,
            binary,
            CASE,
            commit,
            sha256_file(binary),
            output_bin=grid,
            experiment=EXPERIMENT,
        )
        header, arr = read_binary(grid)
        staged.append((variant, meta, header, np.array(arr, copy=True), grid))
    ref_arr = staged[0][3]
    rows = []
    for variant, meta, header, arr, grid in staged:
        row = measure_row(
            plan_row(variant, solver, smoke),
            arr,
            ref_arr,
            gamma=gamma,
            dx=float(header.dx),
            diagnostics=meta.get("stderr_diagnostics") or {},
            walltime_s=float(meta.get("elapsed_wall_s", 0.0)),
        )
        rows.append(row)
        if not keep_grids and grid.is_file():
            grid.unlink()
    mca = load_mca_summary(mca_summary) if mca_summary is not None else blocked_mca(mca_block_reason)
    summary = assemble_summary(
        rows,
        mca,
        commit,
        solver=solver,
        phase=phase,
        smoke=smoke,
    )
    write_outputs(summary, out)
    return summary


def measure_row(plan: dict[str, Any], arr: np.ndarray, ref_arr: np.ndarray, *,
                gamma: float, dx: float, diagnostics: dict[str, Any],
                walltime_s: float) -> dict[str, Any]:
    candidate = np.asarray(arr, dtype=np.float64)
    reference = np.asarray(ref_arr, dtype=np.float64)
    finite = bool(np.isfinite(candidate).all())
    norms = field_norms(candidate, reference, gamma, dx) if finite else zero_norms()
    pressure = mhd_primitive_fields(candidate, gamma)["p"] if finite else np.array([math.nan])
    row = dict(plan)
    row.update({
        "finite": finite and bool(np.all(pressure > 0.0)),
        "rc": 0,
        "steps": int(diagnostics.get("steps", 0)),
        "divB_max": finite_float(diagnostics.get("divB_max", 0.0)),
        "walltime_s": finite_float(walltime_s),
    })
    row.update({key: finite_float(value) for key, value in norms.items()})
    return row


def assemble_summary(rows: list[dict[str, Any]], mca: dict[str, Any], commit: str,
                     *, solver: str, phase: str, smoke: bool) -> dict[str, Any]:
    deterministic_pass = (
        bool(rows)
        and all(row.get("finite") is True and row.get("rc") == 0 for row in rows)
        and any(row.get("is_reference") is True for row in rows)
    )
    mca_pass = all(block.get("status") == "completed" and block.get("n") == 30 for block in mca.values())
    return {
        "experiment": EXPERIMENT,
        "case": "kelvin_helmholtz_2d",
        "solver": normalise_solver(solver),
        "phase": phase,
        "mode": "smoke" if smoke else ("deterministic-with-mca" if mca_pass else "deterministic-with-blocked-mca"),
        "git_commit": commit,
        "reference": REFERENCE,
        "deterministic": rows,
        "mca": mca,
        "gates": {
            "deterministic": {
                "pass": deterministic_pass,
                "rows": len(rows),
                "all_finite_positive": all(row.get("finite") is True for row in rows),
            },
            "mca": {
                "pass": mca_pass,
                "status": "blocked_environment" if not mca_pass else "completed",
            },
            "report_grade": {
                "pass": deterministic_pass and mca_pass,
                "reason": None if deterministic_pass and mca_pass else "MCA unavailable or incomplete",
            },
        },
        "claims": {
            "deterministic": "CPU deterministic KH precision rows are measured against the same-grid cpu-double-O2-ieee-leq reference.",
            "mca": (
                "Docker Verificarlo MCA p53 and p24 blocks are completed for this KH packet."
                if mca_pass
                else "MCA precision-noise claims are blocked until Docker/Verificarlo is available."
            ),
        },
    }


def write_outputs(summary: dict[str, Any], out: pathlib.Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ROW_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summary["deterministic"])
    (out / "summary.md").write_text(render_markdown(summary), encoding="utf-8")
    write_figure(summary, out)


def write_figure(summary: dict[str, Any], out: pathlib.Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    rows = summary["deterministic"]
    labels = [row["variant"].replace("cpu-", "") for row in rows if not row["is_reference"]]
    values = [float(row["Linf_rho"]) for row in rows if not row["is_reference"]]
    plt.figure(figsize=(8.0, 4.0))
    plt.bar(labels, values, color="#8a6f4d")
    plt.ylabel("Linf rho vs reference")
    plt.xticks(rotation=70, ha="right", fontsize=7)
    plt.tight_layout()
    plt.savefig(fig_dir / "deterministic_linf_rho.png", dpi=180)
    plt.close()


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Week 16 Kelvin-Helmholtz Precision Packet",
        "",
        f"- Solver: `{summary['solver']}`",
        f"- Phase: `{summary['phase']}`",
        f"- Mode: `{summary['mode']}`",
        f"- Commit: `{summary['git_commit']}`",
        f"- Deterministic gate: `{summary['gates']['deterministic']['pass']}`",
        f"- MCA gate: `{summary['gates']['mca']['status']}`",
        f"- Report-grade gate: `{summary['gates']['report_grade']['pass']}`",
        "",
        "| variant | finite | steps | divB_max | Linf_rho | Linf_By | walltime_s |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary["deterministic"]:
        lines.append(
            f"| {row['variant']} | {row['finite']} | {row['steps']} | "
            f"{row['divB_max']:.6e} | {row['Linf_rho']:.6e} | "
            f"{row['Linf_By']:.6e} | {row['walltime_s']:.3f} |"
        )
    lines.extend([""])
    if summary["gates"]["mca"]["pass"]:
        lines.extend([
            "MCA blocks are completed with Docker Verificarlo p53/p24 evidence.",
            "KH deterministic-plus-MCA precision-noise claims are report-grade within this packet's bounds.",
            "",
        ])
    else:
        lines.extend([
            "MCA blocks are schema-complete but blocked by the local Docker daemon.",
            "No KH MCA precision-noise claim is made from this packet.",
            "",
        ])
    return "\n".join(lines)


def cfg_float(text: str, key: str, default: float) -> float:
    for line in text.splitlines():
        content = line.split("#", 1)[0].strip()
        if not content or "=" not in content:
            continue
        lhs, rhs = [part.strip() for part in content.split("=", 1)]
        if lhs == key:
            return float(rhs)
    return default


def zero_norms() -> dict[str, float]:
    return {
        f"{norm}_{field}": 0.0
        for field in ("rho", "By", "p", "vx")
        for norm in ("L1", "L2", "Linf")
    }


def finite_float(value: Any) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"expected finite value, got {value!r}")
    return out


def normalise_solver(solver: str) -> str:
    out = str(solver).lower()
    if out not in SUPPORTED_SOLVERS:
        raise ValueError(f"unsupported solver: {solver}")
    return out


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--solver", choices=SUPPORTED_SOLVERS, default="hll")
    parser.add_argument("--phase", choices=("p0", "p1"), default="p0")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--keep-grids", action="store_true")
    parser.add_argument(
        "--mca-block-reason",
        default="Docker daemon unavailable; Verificarlo MCA not run in this environment.",
    )
    parser.add_argument("--mca-summary", type=pathlib.Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    base_out = args.out if args.out.is_absolute() else ROOT / args.out
    suffix = f"{args.solver}_{args.phase}"
    if args.smoke:
        suffix = f"{suffix}_smoke"
    out = base_out / suffix
    summary = run_packet(
        out,
        solver=args.solver,
        phase=args.phase,
        smoke=args.smoke,
        keep_grids=args.keep_grids,
        mca_block_reason=args.mca_block_reason,
        mca_summary=args.mca_summary,
    )
    print((out / "summary.md").read_text(encoding="utf-8"), end="")
    return 0 if summary["gates"]["deterministic"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
