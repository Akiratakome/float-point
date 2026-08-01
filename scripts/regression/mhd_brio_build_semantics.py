#!/usr/bin/env python3
"""Direct Brio--Wu comparisons for optimisation, fast-math, and branch semantics.

The driver can build from a clean source snapshot while writing run artefacts to
the active repository.  This keeps the numerical source commit explicit even
when the active worktree contains unrelated changes.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import pathlib
import shutil
import subprocess
import sys
from contextlib import contextmanager
from typing import Any

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "experiments" / "week20" / "brio_wu_build_semantics"
for item in (ROOT, ROOT / "scripts", ROOT / "scripts" / "metrics", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(item))

from _mhd_harness import replace_or_append_cfg, resolve_binary, run_case, sha256_file  # noqa: E402
from io_helper import read_binary  # noqa: E402
from mhd_fields import mhd_primitive_fields  # noqa: E402

EXPERIMENT = "week20-brio-wu-build-semantics"
SOLVERS = ("hll", "hlld")
PRECISIONS = ("double", "float")
VARIANTS: dict[str, dict[str, Any]] = {
    "o2": {"opt_level": "O2", "fast_math": False, "strict_branch": False},
    "ox": {"opt_level": "O3", "fast_math": False, "strict_branch": False},
    "fast": {"opt_level": "O2", "fast_math": True, "strict_branch": False},
    "strict": {"opt_level": "O2", "fast_math": False, "strict_branch": True},
}
COMPARISONS = {
    "optimisation": {"candidate": "ox", "reference": "o2", "changed_axis": "/Ox versus /O2"},
    "fast_math": {"candidate": "fast", "reference": "o2", "changed_axis": "/fp:fast versus compiler default"},
    "branch_rule": {"candidate": "strict", "reference": "o2", "changed_axis": "< versus <= in the Riemann branch"},
}


def plan_rows() -> list[dict[str, str]]:
    return [
        {"solver": solver, "precision": precision, "variant": variant}
        for solver in SOLVERS
        for precision in PRECISIONS
        for variant in VARIANTS
    ]


def density_norms(candidate: np.ndarray, reference: np.ndarray) -> dict[str, float]:
    cand = np.asarray(candidate, dtype=np.float64)[..., 0]
    ref = np.asarray(reference, dtype=np.float64)[..., 0]
    if cand.shape != ref.shape:
        raise ValueError(f"shape mismatch: {cand.shape} != {ref.shape}")
    diff = cand - ref
    scale = float(np.mean(np.abs(ref)))
    if not math.isfinite(scale) or scale <= 0.0:
        raise ValueError("density reference scale must be finite and positive")
    return {
        "rho_l1_mean": float(np.mean(np.abs(diff))),
        "rho_l2_mean": float(np.sqrt(np.mean(diff * diff))),
        "rho_linf": float(np.max(np.abs(diff))),
        "rho_l1_relative": float(np.mean(np.abs(diff)) / scale),
    }


def _build_name(precision: str, variant: str) -> str:
    spec = VARIANTS[variant]
    math_name = "fastmath" if spec["fast_math"] else "ieee"
    branch_name = "strict" if spec["strict_branch"] else "leq"
    return f"cpu-{precision}-{spec['opt_level']}-{math_name}-{branch_name}"


def _run_logged(command: list[str], cwd: pathlib.Path, log: pathlib.Path) -> None:
    result = subprocess.run(
        command, cwd=cwd, text=True, encoding="utf-8", errors="replace",
        capture_output=True, check=False,
    )
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"command failed ({result.returncode}); see {log}")


def build_matrix(source_root: pathlib.Path, build_root: pathlib.Path, out: pathlib.Path) -> dict[tuple[str, str], pathlib.Path]:
    binaries: dict[tuple[str, str], pathlib.Path] = {}
    for precision in PRECISIONS:
        for variant, spec in VARIANTS.items():
            name = _build_name(precision, variant)
            build_dir = build_root / name
            configure = [
                "cmake", "-S", str(source_root), "-B", str(build_dir), "-G", "Ninja",
                "-DCMAKE_BUILD_TYPE=Release", f"-DFLOAT_PRECISION={precision}",
                f"-DOPT_LEVEL={spec['opt_level']}",
                f"-DFAST_MATH={'ON' if spec['fast_math'] else 'OFF'}",
                f"-DRIEMANN_STRICT_INEQUALITY={'ON' if spec['strict_branch'] else 'OFF'}",
                "-DENABLE_OPENMP=ON", "-DENABLE_CUDA=OFF",
            ]
            print(f"[build-semantics] configure {name}", flush=True)
            _run_logged(configure, source_root, out / "build_logs" / f"{name}-configure.txt")
            print(f"[build-semantics] build {name}", flush=True)
            _run_logged(
                ["cmake", "--build", str(build_dir), "--target", "hrsc_mhd"],
                source_root,
                out / "build_logs" / f"{name}-build.txt",
            )
            binary = resolve_binary(build_dir / "hrsc_mhd")
            semantics = build_dir / "build_semantics.json"
            if not semantics.is_file():
                raise FileNotFoundError(f"missing build semantics: {semantics}")
            retained = out / "build_semantics" / f"{name}.json"
            retained.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(semantics, retained)
            binaries[(precision, variant)] = binary
    return binaries


def load_binaries(build_root: pathlib.Path) -> dict[tuple[str, str], pathlib.Path]:
    return {
        (precision, variant): resolve_binary(build_root / _build_name(precision, variant) / "hrsc_mhd")
        for precision in PRECISIONS
        for variant in VARIANTS
    }


@contextmanager
def _one_thread():
    previous = os.environ.get("OMP_NUM_THREADS")
    os.environ["OMP_NUM_THREADS"] = "1"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("OMP_NUM_THREADS", None)
        else:
            os.environ["OMP_NUM_THREADS"] = previous


def _config_text(source_cfg: pathlib.Path, solver: str, output: pathlib.Path) -> str:
    text = source_cfg.read_text(encoding="utf-8")
    for key, value in (
        ("riemann", solver), ("device", "cpu"), ("output_format", "binary"),
        ("output_file", str(output.resolve())),
    ):
        text = replace_or_append_cfg(text, key, value)
    return text


def _physical(arr: np.ndarray) -> tuple[bool, float, float]:
    fields = mhd_primitive_fields(arr, 2.0)
    rho_min = float(np.min(fields["rho"]))
    pressure_min = float(np.min(fields["p"]))
    ok = bool(np.isfinite(arr).all() and rho_min > 0.0 and pressure_min > 0.0)
    return ok, rho_min, pressure_min


def execute_matrix(
    binaries: dict[tuple[str, str], pathlib.Path], source_cfg: pathlib.Path,
    source_commit: str, out: pathlib.Path,
) -> tuple[list[dict[str, Any]], dict[tuple[str, str, str], np.ndarray], list[pathlib.Path]]:
    rows: list[dict[str, Any]] = []
    arrays: dict[tuple[str, str, str], np.ndarray] = {}
    grids: list[pathlib.Path] = []
    with _one_thread():
        for item in plan_rows():
            solver, precision, variant = item["solver"], item["precision"], item["variant"]
            label = f"brio-{solver}-{precision}-{variant}"
            run_dir = out / "runs" / label
            grid = run_dir / "grid.bin"
            binary = binaries[(precision, variant)]
            print(f"[build-semantics] run {label}", flush=True)
            _, metadata, _ = run_case(
                label, _config_text(source_cfg, solver, grid), run_dir, binary,
                source_cfg, source_commit, sha256_file(binary), output_bin=grid.resolve(),
                experiment=EXPERIMENT,
            )
            header, view = read_binary(grid)
            arr = np.array(view, dtype=np.float64, copy=True)
            physical, rho_min, pressure_min = _physical(arr)
            diag = metadata.get("stderr_diagnostics", {})
            rows.append({
                **item, "status": "completed", "physical_state": physical,
                "steps": int(diag.get("steps", 0)), "final_time": float(header.t),
                "precision_bytes": int(header.precision_tag), "rho_min": rho_min,
                "pressure_min": pressure_min, "divB_max": float(diag.get("divB_max", math.nan)),
                "binary_sha256": sha256_file(binary),
                "build_name": binary.parent.name,
                "run_dir": run_dir.relative_to(ROOT).as_posix(),
            })
            arrays[(solver, precision, variant)] = arr
            grids.append(grid)
    return rows, arrays, grids


def aggregate(
    rows: list[dict[str, Any]], arrays: dict[tuple[str, str, str], np.ndarray],
    source_commit: str, build_semantics: list[dict[str, Any]],
) -> dict[str, Any]:
    comparisons: list[dict[str, Any]] = []
    for solver in SOLVERS:
        for precision in PRECISIONS:
            for axis, spec in COMPARISONS.items():
                metrics = density_norms(
                    arrays[(solver, precision, spec["candidate"])],
                    arrays[(solver, precision, spec["reference"])],
                )
                comparisons.append({
                    "solver": solver, "precision": precision, "axis": axis,
                    "candidate": spec["candidate"], "reference": spec["reference"],
                    "changed_axis": spec["changed_axis"], **metrics,
                })
    expected_rows = len(SOLVERS) * len(PRECISIONS) * len(VARIANTS)
    expected_comparisons = len(SOLVERS) * len(PRECISIONS) * len(COMPARISONS)
    steps_ok = all(
        len({row["steps"] for row in rows if row["solver"] == solver and row["precision"] == precision}) == 1
        for solver in SOLVERS for precision in PRECISIONS
    )
    runs_ok = (
        len(rows) == expected_rows
        and all(row["status"] == "completed" and row["physical_state"] for row in rows)
        and all(abs(float(row["final_time"]) - 0.1) <= 1e-6 for row in rows)
        and steps_ok
    )
    metrics_ok = len(comparisons) == expected_comparisons and all(
        math.isfinite(float(row[key])) and float(row[key]) >= 0.0
        for row in comparisons
        for key in ("rho_l1_mean", "rho_l2_mean", "rho_linf", "rho_l1_relative")
    )
    return {
        "schema": {"name": "hrsc.week20-brio-build-semantics", "version": 1},
        "experiment": EXPERIMENT,
        "source_commit": source_commit,
        "configuration": {
            "case": "brio_wu_1d", "nx": 800, "ny": 1, "t_end": 0.1,
            "cfl": 0.4, "gamma": 2.0, "device": "cpu", "omp_num_threads": 1,
            "solvers": list(SOLVERS), "precisions": list(PRECISIONS),
        },
        "builds": build_semantics,
        "gate": {
            "pass": runs_ok and metrics_ok and len(build_semantics) == len(PRECISIONS) * len(VARIANTS),
            "complete_runs": runs_ok, "complete_metrics": metrics_ok,
            "same_steps_within_solver_precision": steps_ok,
        },
        "runs": rows,
        "comparisons": comparisons,
        "claim_boundary": (
            "Each comparison changes one recorded build axis on MSVC for one Brio--Wu CPU configuration. "
            "The deterministic output result is not a compiler-wide, performance, accuracy, or portability claim."
        ),
    }


def _build_rows(binaries: dict[tuple[str, str], pathlib.Path], out: pathlib.Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for precision in PRECISIONS:
        for variant, requested in VARIANTS.items():
            name = _build_name(precision, variant)
            semantics_path = out / "build_semantics" / f"{name}.json"
            if not semantics_path.is_file():
                source = binaries[(precision, variant)].parent / "build_semantics.json"
                semantics_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, semantics_path)
            semantics = json.loads(semantics_path.read_text(encoding="utf-8"))
            rows.append({
                "precision": precision, "variant": variant, "build_name": name,
                "requested_branch_rule": "<" if requested["strict_branch"] else "<=",
                "binary_sha256": sha256_file(binaries[(precision, variant)]),
                "semantics_sha256": sha256_file(semantics_path),
                "compiler": semantics.get("compiler"),
                "requested": semantics.get("requested"),
                "effective_math_mode": semantics.get("effective_math_mode"),
                "flag_evidence": semantics.get("flag_evidence"),
            })
    return rows


def write_outputs(summary: dict[str, Any], out: pathlib.Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary["comparisons"][0]))
        writer.writeheader(); writer.writerows(summary["comparisons"])
    lines = [
        "# Brio--Wu direct build-semantics comparison", "",
        f"Gate pass: `{summary['gate']['pass']}`. Source commit: `{summary['source_commit']}`.", "",
        "| solver | precision | isolated axis | mean L1(rho) | Linf(rho) |", "|---|---|---|---:|---:|",
    ]
    for row in summary["comparisons"]:
        lines.append(
            f"| {row['solver'].upper()} | {'FP64' if row['precision']=='double' else 'FP32'} | "
            f"{row['changed_axis']} | {row['rho_l1_mean']:.3e} | {row['rho_linf']:.3e} |"
        )
    lines += ["", "## Claim boundary", "", summary["claim_boundary"], ""]
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def plot(summary: dict[str, Any], out: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = summary["comparisons"]
    labels = [f"{solver.upper()}\n{'FP64' if precision == 'double' else 'FP32'}" for solver in SOLVERS for precision in PRECISIONS]
    x = np.arange(len(labels), dtype=np.float64)
    width = 0.24
    positive = [float(row["rho_linf"]) for row in rows if float(row["rho_linf"]) > 0.0]
    floor = min(positive) / 5.0 if positive else 1e-18
    fig, ax = plt.subplots(figsize=(9.4, 4.9), constrained_layout=True)
    colors = {"optimisation": "#0072B2", "fast_math": "#D55E00", "branch_rule": "#009E73"}
    for offset_index, axis in enumerate(COMPARISONS):
        values = []
        exact = []
        for solver in SOLVERS:
            for precision in PRECISIONS:
                value = next(float(row["rho_linf"]) for row in rows if row["solver"] == solver and row["precision"] == precision and row["axis"] == axis)
                exact.append(value); values.append(value if value > 0.0 else floor)
        bars = ax.bar(x + (offset_index - 1) * width, values, width, label=axis.replace("_", " "), color=colors[axis])
        for bar, value in zip(bars, exact):
            if value == 0.0:
                bar.set_facecolor("white"); bar.set_edgecolor(colors[axis]); bar.set_hatch("///")
                ax.annotate(
                    "0",
                    (bar.get_x() + bar.get_width() / 2.0, floor),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    color=colors[axis],
                )
    ax.set_yscale("log"); ax.set_xticks(x, labels)
    ax.set_ylabel(r"Direct density $L_\infty$ discrepancy")
    ax.set_title("Brio--Wu: isolated build-semantics response")
    ax.grid(axis="y", which="both", color="#d8dde3", linewidth=0.6)
    ax.legend(frameon=False, ncol=3)
    target_dir = out / "figures"; target_dir.mkdir(parents=True, exist_ok=True)
    png, pdf = target_dir / "brio_build_semantics.png", target_dir / "brio_build_semantics.pdf"
    fig.savefig(png, dpi=320, facecolor="white"); fig.savefig(pdf, facecolor="white"); plt.close(fig)
    return png, pdf


def run(source_root: pathlib.Path, build_root: pathlib.Path, source_commit: str, out: pathlib.Path, skip_build: bool) -> dict[str, Any]:
    source_cfg = source_root / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg"
    if not source_cfg.is_file():
        raise FileNotFoundError(f"missing clean source config: {source_cfg}")
    binaries = load_binaries(build_root) if skip_build else build_matrix(source_root, build_root, out)
    build_rows = _build_rows(binaries, out)
    rows, arrays, grids = execute_matrix(binaries, source_cfg, source_commit, out)
    summary = aggregate(rows, arrays, source_commit, build_rows)
    write_outputs(summary, out); png, pdf = plot(summary, out)
    for grid in grids:
        if grid.name != "grid.bin" or out not in grid.parents:
            raise ValueError(f"refusing to remove unexpected grid: {grid}")
        grid.unlink(missing_ok=True)
    print(f"gate_pass: {summary['gate']['pass']}")
    print(f"summary: {out / 'summary.json'}")
    print(f"figure: {png}")
    print(f"figure_pdf: {pdf}")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=pathlib.Path, required=True)
    parser.add_argument("--build-root", type=pathlib.Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args(argv)
    summary = run(
        args.source_root.resolve(), args.build_root.resolve(), args.source_commit,
        args.out.resolve(), args.skip_build,
    )
    return 0 if summary["gate"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
