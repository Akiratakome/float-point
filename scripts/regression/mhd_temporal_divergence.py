#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys
from typing import Any, Callable, Mapping, Sequence

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "scripts", ROOT / "scripts" / "metrics", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(path))

from _mhd_harness import (
    git_commit,
    replace_or_append_cfg,
    resolve_binary,
    run_case,
    sha256_file,
)
from scripts.metrics.drift_timeseries import analyse_pair

DEFAULT_GAMMA = 5.0 / 3.0
DEFAULT_OUT = ROOT / "experiments" / "week15" / "mhd_temporal_divergence"
BINARY_PATHS = {
    "double": ROOT / "build-matrix" / "cpu-double-O2-ieee-leq" / "hrsc_mhd",
    "float": ROOT / "build-matrix" / "cpu-float-O2-ieee-leq" / "hrsc_mhd",
}
CASES = {
    "brio_wu_1d": {
        "cfg": ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg",
        "nx": 800,
        "ny": 1,
        "t_start": 0.01,
        "t_end_max": 0.1,
        "n_slices": 15,
        "fit_window": [0.01, 0.1],
    },
    "orszag_tang_2d": {
        "cfg": ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg",
        "nx": 128,
        "ny": 128,
        "t_start": 0.05,
        "t_end_max": 1.0,
        "n_slices": 25,
        "fit_window": [0.1, 0.5],
    },
}


def slice_plan(case_name: str, smoke: bool = False) -> list[float]:
    spec = CASES[case_name]
    count = 3 if smoke else int(spec["n_slices"])
    return np.linspace(float(spec["t_start"]), float(spec["t_end_max"]), count).tolist()


def case_gamma(cfg_text: str) -> float:
    for line in cfg_text.splitlines():
        content = line.split("#", 1)[0].strip()
        if content and "=" in content:
            key, value = (part.strip() for part in content.split("=", 1))
            if key == "gamma":
                return float(value)
    return DEFAULT_GAMMA


def temporal_cfg(
    base_text: str,
    *,
    nx: int,
    ny: int,
    t_end: float,
    solver: str,
    output_file: pathlib.Path,
) -> str:
    text = base_text
    for key, value in (
        ("nx", str(nx)),
        ("ny", str(ny)),
        ("t_end", f"{t_end:.17g}"),
        ("riemann", solver),
        ("output_format", "binary"),
        ("output_file", output_file.as_posix()),
    ):
        text = replace_or_append_cfg(text, key, value)
    return text


def pair_entry(
    case_name: str,
    *,
    gamma: float,
    double_grids: Sequence[pathlib.Path],
    float_grids: Sequence[pathlib.Path],
) -> dict[str, Any]:
    return {
        "case": case_name,
        "pair": "fp32-vs-fp64",
        "variable": "rho",
        "gamma": gamma,
        "a": list(double_grids),
        "b": list(float_grids),
        "time_tolerance": 2.0e-3,
        "spatial_tolerance": 1.0e-5,
        "notes": ["Lyapunov-like precision-perturbation growth rate; not a formal maximal exponent."],
    }


def resolve_binaries() -> dict[str, pathlib.Path]:
    return {precision: resolve_binary(path) for precision, path in BINARY_PATHS.items()}


def run_case_series(
    case_name: str,
    out_dir: pathlib.Path,
    binaries: Mapping[str, pathlib.Path],
    *,
    smoke: bool = False,
    keep_grids: bool = False,
    runner: Callable[..., Any] = run_case,
    analyser: Callable[..., dict[str, Any]] = analyse_pair,
) -> dict[str, Any]:
    spec = CASES[case_name]
    source_cfg = pathlib.Path(spec["cfg"])
    base_text = source_cfg.read_text(encoding="utf-8")
    gamma = case_gamma(base_text)
    commit = git_commit()
    grids: dict[str, list[pathlib.Path]] = {"double": [], "float": []}
    runs: list[dict[str, Any]] = []
    for precision in ("double", "float"):
        binary = pathlib.Path(binaries[precision])
        sha = sha256_file(binary) if binary.is_file() else "test-double"
        for index, target in enumerate(slice_plan(case_name, smoke=smoke)):
            run_dir = pathlib.Path(out_dir) / "runs" / case_name / precision / f"slice_{index:02d}"
            grid = run_dir / "grid.bin"
            cfg_text = temporal_cfg(
                base_text,
                nx=int(spec["nx"]),
                ny=int(spec["ny"]),
                t_end=target,
                solver="hll",
                output_file=grid,
            )
            _, meta, _ = runner(
                f"{case_name}-{precision}-{index:02d}",
                cfg_text,
                run_dir,
                binary,
                source_cfg,
                commit,
                sha,
                output_bin=grid,
                experiment="week15-mhd-temporal-divergence",
            )
            grids[precision].append(grid)
            runs.append(meta)
    entry = pair_entry(
        case_name,
        gamma=gamma,
        double_grids=grids["double"],
        float_grids=grids["float"],
    )
    record = analyser(entry, fit_window=spec["fit_window"])
    if not keep_grids:
        for grid in grids["double"] + grids["float"]:
            if grid.is_file():
                grid.unlink()
    return {"record": record, "runs": runs}


def evaluate_gates(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    by_case = {record["case"]: record for record in records}
    finite_nonnegative = all(
        math.isfinite(float(value)) and float(value) >= 0.0
        for record in records
        for key in ("l1", "linf")
        for value in record[key]
    )
    ot_lambda = by_case.get("orszag_tang_2d", {}).get("lambda_l1")
    ot_positive = ot_lambda is not None and math.isfinite(float(ot_lambda)) and float(ot_lambda) > 0.0
    complete = set(by_case) == set(CASES)
    return {
        "pass": bool(complete and finite_nonnegative and ot_positive),
        "cases_complete": complete,
        "all_drift_finite_nonnegative": finite_nonnegative,
        "orszag_tang_positive_lambda": ot_positive,
    }


def plot_records(out_dir: pathlib.Path, records: Sequence[dict[str, Any]]) -> pathlib.Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure = pathlib.Path(out_dir) / "figures" / "temporal_divergence.png"
    figure.parent.mkdir(parents=True, exist_ok=True)
    with plt.rc_context({
        "font.family": "serif", "font.size": 9,
        "axes.grid": True, "grid.alpha": 0.25,
        "figure.dpi": 120, "savefig.dpi": 300,
    }):
        fig, ax = plt.subplots(figsize=(6.6, 3.8), constrained_layout=True)
        for record in records:
            times = np.asarray(record["times"], dtype=np.float64)
            l1 = np.asarray(record["l1"], dtype=np.float64)
            log_l1 = np.full(l1.shape, np.nan, dtype=np.float64)
            positive = np.isfinite(l1) & (l1 > 0.0)
            log_l1[positive] = np.log10(l1[positive])
            label = str(record["case"]).replace("_", " ")
            line, = ax.plot(times, log_l1, marker="o", ms=3, lw=1.2, label=label)
            fit = record["fit_l1"]
            window = record["fit_window"]
            if fit["slope"] is not None and window is not None:
                fit_t = np.linspace(float(window[0]), float(window[1]), 100)
                fit_log10 = (float(fit["slope"]) * fit_t + float(fit["intercept"])) / math.log(10.0)
                ax.plot(fit_t, fit_log10, ls="--", lw=1.0, color=line.get_color())
                ax.text(
                    fit_t[-1], fit_log10[-1], f"lambda={float(fit['slope']):.3g}",
                    color=line.get_color(), fontsize=8, ha="right", va="bottom",
                )
        ax.set_xlabel("time")
        ax.set_ylabel("log10 L1 density drift")
        ax.legend(frameon=False)
        fig.savefig(figure)
        plt.close(fig)
    return figure


def write_outputs(
    out_dir: pathlib.Path,
    records: Sequence[dict[str, Any]],
    runs: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    gates = evaluate_gates(records)
    figure = plot_records(out, records)
    payload = {
        "experiment": "week15-mhd-temporal-divergence",
        "git_commit": git_commit(),
        "gates": gates,
        "records": list(records),
        "runs": list(runs),
        "figure": figure.relative_to(out).as_posix(),
        "interpretation": {
            "formal_maximal_lyapunov": False,
            "statement": "lambda is a Lyapunov-like growth rate of an fp32-vs-fp64 perturbation.",
        },
    }
    json_path = out / "summary.json"
    csv_path = out / "summary.csv"
    md_path = out / "summary.md"
    json_path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        columns = ("case", "pair", "variable", "time", "l1", "linf", "lambda_l1", "lambda_linf")
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in records:
            for time_value, l1, linf in zip(record["times"], record["l1"], record["linf"]):
                writer.writerow({
                    "case": record["case"], "pair": record["pair"],
                    "variable": record["variable"], "time": time_value,
                    "l1": l1, "linf": linf,
                    "lambda_l1": record["lambda_l1"],
                    "lambda_linf": record["lambda_linf"],
                })

    def fmt_lambda(value: Any) -> str:
        return "n/a" if value is None else f"{float(value):.6g}"

    lines = [
        "# MHD Temporal Divergence", "",
        "| case | samples | lambda L1 | lambda Linf | fit window |",
        "|---|---:|---:|---:|---|",
    ]
    for record in records:
        lines.append(
            f"| {record['case']} | {len(record['times'])} | {fmt_lambda(record['lambda_l1'])} | "
            f"{fmt_lambda(record['lambda_linf'])} | {record['fit_window']} |"
        )
    lines.extend([
        "", f"- Gate pass: {gates['pass']}",
        f"- Figure: `{payload['figure']}`", "",
        "The fitted lambda is a Lyapunov-like engineering growth rate of an "
        "fp32-vs-fp64 perturbation, not a formal maximal Lyapunov exponent.", "",
    ])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "json": json_path, "csv": csv_path, "markdown": md_path,
        "figure": figure, "payload": payload,
    }
