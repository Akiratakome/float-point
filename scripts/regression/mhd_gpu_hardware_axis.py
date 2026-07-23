#!/usr/bin/env python3
"""Week 16 MHD HLL CPU/GPU hardware-axis evidence driver.

Runs the validated `hrsc_mhd` HLL path for Brio-Wu 1D and Orszag-Tang 2D on
CPU and GPU in float and double. Outputs stable summaries and figures while
deleting measured grid binaries after aggregation.
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
DEFAULT_OUT = ROOT / "experiments" / "week16" / "cpu_gpu_hardware_axis"
EXPERIMENT = "week16-cpu-gpu-hardware-axis"

for path in (ROOT, ROOT / "scripts", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(path))

from io_helper import read_binary  # noqa: E402
from _mhd_harness import (  # noqa: E402
    git_commit,
    replace_or_append_cfg,
    resolve_binary,
    run_case,
    sha256_file,
)


CASES = {
    "brio_wu_1d": {
        "cfg": ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg",
        "smoke_overrides": {"nx": 64, "t_end": 0.01},
    },
    "orszag_tang_2d": {
        "cfg": ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg",
        "smoke_overrides": {"nx": 64, "ny": 64, "t_end": 0.05},
    },
}

BINS = {
    ("double", "cpu"): ROOT / "build-double" / "hrsc_mhd",
    ("float", "cpu"): ROOT / "build-float" / "hrsc_mhd",
    ("double", "gpu"): ROOT / "build-cuda" / "hrsc_mhd",
    ("float", "gpu"): ROOT / "build-cuda-float" / "hrsc_mhd",
}

ROW_FIELDS = [
    "case",
    "precision",
    "nx",
    "ny",
    "steps_cpu",
    "steps_gpu",
    "t_cpu",
    "t_gpu",
    "elapsed_cpu_s",
    "elapsed_gpu_s",
    "speedup_cpu_over_gpu",
    "l1_mean_abs",
    "linf_abs",
    "ulp_max",
    "divB_max_cpu",
    "divB_max_gpu",
    "gate_passed",
]


def max_ulp_distance(a: np.ndarray, b: np.ndarray) -> int:
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {b.shape}")
    if a.dtype != b.dtype:
        raise ValueError(f"dtype mismatch: {a.dtype} vs {b.dtype}")
    if a.dtype == np.dtype("float32"):
        ua = a.view(np.uint32)
        ub = b.view(np.uint32)
        sign = np.uint32(1 << 31)
    elif a.dtype == np.dtype("float64"):
        ua = a.view(np.uint64)
        ub = b.view(np.uint64)
        sign = np.uint64(1 << 63)
    else:
        raise ValueError(f"unsupported dtype for ULP distance: {a.dtype}")
    oa = np.where((ua & sign) != 0, ~ua, ua ^ sign)
    ob = np.where((ub & sign) != 0, ~ub, ub ^ sign)
    diff = np.maximum(oa, ob) - np.minimum(oa, ob)
    return int(diff.max(initial=0))


def compute_pair_metrics(
    case: str,
    precision: str,
    cpu: np.ndarray,
    gpu: np.ndarray,
    elapsed_cpu_s: float,
    elapsed_gpu_s: float,
) -> dict[str, Any]:
    if cpu.shape != gpu.shape:
        raise ValueError(f"{case}/{precision}: shape mismatch {cpu.shape} vs {gpu.shape}")
    if cpu.dtype != gpu.dtype:
        raise ValueError(f"{case}/{precision}: dtype mismatch {cpu.dtype} vs {gpu.dtype}")
    diff = np.abs(cpu.astype(np.float64) - gpu.astype(np.float64))
    linf = float(diff.max(initial=0.0))
    return {
        "case": case,
        "precision": precision,
        "elapsed_cpu_s": float(elapsed_cpu_s),
        "elapsed_gpu_s": float(elapsed_gpu_s),
        "speedup_cpu_over_gpu": (
            float(elapsed_cpu_s) / float(elapsed_gpu_s)
            if float(elapsed_gpu_s) > 0.0 else math.inf
        ),
        "l1_mean_abs": float(diff.mean()) if diff.size else 0.0,
        "linf_abs": linf,
        "ulp_max": max_ulp_distance(cpu, gpu),
        "gate_passed": linf == 0.0 and max_ulp_distance(cpu, gpu) == 0,
    }


def cleanup_transient_grids(paths: list[pathlib.Path]) -> None:
    for path in paths:
        if path.name != "grid.bin":
            raise ValueError(f"refusing to clean non-grid path: {path}")
        resolved = path.resolve()
        if resolved.exists():
            resolved.unlink()


def _cfg_with_overrides(source_cfg: pathlib.Path, output_bin: pathlib.Path,
                        device: str, smoke: bool) -> str:
    text = source_cfg.read_text(encoding="utf-8")
    text = replace_or_append_cfg(text, "riemann", "hll")
    text = replace_or_append_cfg(text, "device", device)
    text = replace_or_append_cfg(text, "output_format", "binary")
    text = replace_or_append_cfg(text, "output_file", str(output_bin))
    if smoke:
        case_spec = next(spec for spec in CASES.values() if spec["cfg"] == source_cfg)
        for key, value in case_spec["smoke_overrides"].items():
            text = replace_or_append_cfg(text, key, str(value))
    return text


def _run_one(case: str, precision: str, device: str, out: pathlib.Path,
             smoke: bool, commit: str) -> tuple[Any, np.ndarray, dict[str, Any], pathlib.Path]:
    source_cfg = CASES[case]["cfg"]
    binary = resolve_binary(BINS[(precision, device)])
    run_dir = out / "runs" / f"{case}-{precision}-{device}"
    grid_path = run_dir / "grid.bin"
    cfg_text = _cfg_with_overrides(source_cfg, grid_path, device, smoke)
    _, meta, _stderr = run_case(
        f"{case}-{precision}-{device}",
        cfg_text,
        run_dir,
        binary,
        source_cfg,
        commit,
        sha256_file(binary),
        output_bin=grid_path,
        experiment=EXPERIMENT,
    )
    header, arr = read_binary(grid_path)
    return header, np.array(arr, copy=True), meta, grid_path


def _headers_match(case: str, precision: str, cpu_h: Any, gpu_h: Any) -> None:
    for field in ("nx", "ny", "nvars", "precision_tag"):
        if getattr(cpu_h, field) != getattr(gpu_h, field):
            raise ValueError(
                f"{case}/{precision}: header {field} mismatch "
                f"{getattr(cpu_h, field)} vs {getattr(gpu_h, field)}"
            )
    for field in ("t", "dx", "dy"):
        if float(getattr(cpu_h, field)) != float(getattr(gpu_h, field)):
            raise ValueError(
                f"{case}/{precision}: header {field} mismatch "
                f"{getattr(cpu_h, field)} vs {getattr(gpu_h, field)}"
            )


def run_matrix(out: pathlib.Path, smoke: bool) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    commit = git_commit()
    rows = []
    grid_paths: list[pathlib.Path] = []
    for case in CASES:
        for precision in ("double", "float"):
            cpu_h, cpu, meta_cpu, cpu_grid = _run_one(case, precision, "cpu", out, smoke, commit)
            gpu_h, gpu, meta_gpu, gpu_grid = _run_one(case, precision, "gpu", out, smoke, commit)
            grid_paths.extend([cpu_grid, gpu_grid])
            _headers_match(case, precision, cpu_h, gpu_h)
            row = compute_pair_metrics(
                case,
                precision,
                cpu,
                gpu,
                float(meta_cpu["elapsed_wall_s"]),
                float(meta_gpu["elapsed_wall_s"]),
            )
            diag_cpu = meta_cpu.get("stderr_diagnostics") or {}
            diag_gpu = meta_gpu.get("stderr_diagnostics") or {}
            row.update({
                "nx": int(cpu_h.nx),
                "ny": int(cpu_h.ny),
                "steps_cpu": int(diag_cpu.get("steps", -1)),
                "steps_gpu": int(diag_gpu.get("steps", -1)),
                "t_cpu": float(diag_cpu.get("t", cpu_h.t)),
                "t_gpu": float(diag_gpu.get("t", gpu_h.t)),
                "divB_max_cpu": float(diag_cpu.get("divB_max", math.nan)),
                "divB_max_gpu": float(diag_gpu.get("divB_max", math.nan)),
            })
            row["gate_passed"] = bool(
                row["gate_passed"]
                and row["steps_cpu"] == row["steps_gpu"]
                and row["t_cpu"] == row["t_gpu"]
            )
            rows.append(row)
    cleanup_transient_grids(grid_paths)
    summary = {
        "experiment": EXPERIMENT,
        "mode": "smoke" if smoke else "report-grade",
        "git_commit": commit,
        "gate": {
            "name": "G-GPU",
            "target": "same-precision CPU-vs-GPU bit-exact output",
            "ulp_max_required": 0,
            "pass": all(row["gate_passed"] for row in rows),
        },
        "rows": rows,
        "retention": {
            "kept": ["config.cfg", "stdout.txt", "stderr.txt", "metadata.json", "summary.*", "figures/*"],
            "transient_removed": "runs/*/grid.bin",
        },
    }
    write_outputs(summary, out)
    return summary


def write_outputs(summary: dict[str, Any], out: pathlib.Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ROW_FIELDS)
        writer.writeheader()
        writer.writerows(summary["rows"])
    lines = [
        "# Week 16 MHD CPU/GPU Hardware Axis",
        "",
        f"- Mode: `{summary['mode']}`",
        f"- Commit: `{summary['git_commit']}`",
        f"- Gate: `{summary['gate']['name']}` pass = `{summary['gate']['pass']}`",
        f"- ULP target: `{summary['gate']['ulp_max_required']}`",
        "",
        "| case | precision | grid | steps cpu/gpu | ulp_max | linf_abs | speedup cpu/gpu | divB_max cpu/gpu | pass |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in summary["rows"]:
        lines.append(
            f"| {row['case']} | {row['precision']} | {row['nx']}x{row['ny']} | "
            f"{row['steps_cpu']}/{row['steps_gpu']} | {row['ulp_max']} | "
            f"{row['linf_abs']:.6e} | {row['speedup_cpu_over_gpu']:.3f} | "
            f"{row['divB_max_cpu']:.6e}/{row['divB_max_gpu']:.6e} | {row['gate_passed']} |"
        )
    lines.extend([
        "",
        "The gate is a same-precision correctness check for the validated HLL GPU path. "
        "It does not cover HLLD, KH-on-GPU, GPU MCA, or a broad performance study.",
        "",
        "Generated `grid.bin` files are removed after measurement; run metadata, generated "
        "configs, stdout/stderr logs, summaries, and figures are retained.",
        "",
    ])
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    _write_figures(summary, out)


def _write_figures(summary: dict[str, Any], out: pathlib.Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    labels = [f"{row['case']}\n{row['precision']}" for row in summary["rows"]]
    speedups = [float(row["speedup_cpu_over_gpu"]) for row in summary["rows"]]
    ulps = [int(row["ulp_max"]) for row in summary["rows"]]

    plt.figure(figsize=(7.0, 3.6))
    plt.bar(labels, speedups, color="#4f7cac")
    plt.ylabel("CPU wall time / GPU wall time")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(fig_dir / "speedup.png", dpi=180)
    plt.close()

    plt.figure(figsize=(7.0, 3.6))
    plt.bar(labels, ulps, color="#6b8f71")
    plt.ylabel("max ULP distance")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(fig_dir / "ulp_max.png", dpi=180)
    plt.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out = args.out if args.out.is_absolute() else ROOT / args.out
    summary = run_matrix(out, smoke=args.smoke)
    print((out / "summary.md").read_text(encoding="utf-8"), end="")
    return 0 if summary["gate"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
