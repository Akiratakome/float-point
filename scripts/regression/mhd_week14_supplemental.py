#!/usr/bin/env python3
"""Week-14 supplemental MHD experiment planning and plotting helpers.

The default CLI writes manifests/summaries only. Solver execution remains an
explicit follow-up step so Report 2 supplemental planning can be reviewed before
any long Brio-Wu runs are launched.
"""

from __future__ import annotations

import argparse
import inspect
import json
import math
import os
import pathlib
import subprocess
import sys
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASE = ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg"
DEFAULT_OUT = ROOT / "experiments" / "week14" / "mhd_supplemental"
EXPERIMENT = "week14-mhd-supplemental"
REFERENCE_VARIANT = "cpu-double-O2-ieee-leq"

for path in (ROOT, ROOT / "scripts", ROOT / "scripts" / "metrics", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(path))

from _mhd_harness import (  # noqa: E402
    git_commit,
    parse_mhd_diagnostics,
    replace_or_append_cfg,
    run_case,
    sha256_file,
)
from io_helper import read_binary  # noqa: E402
from mhd_fields import field_norms  # noqa: E402


DEFAULT_TIME_VARIANTS = (
    {"precision": "double", "opt": "O2", "fast_math": False, "riemann": "leq"},
    {"precision": "float", "opt": "O2", "fast_math": False, "riemann": "leq"},
    {"precision": "double", "opt": "Ofast", "fast_math": False, "riemann": "leq"},
    {"precision": "float", "opt": "Ofast", "fast_math": False, "riemann": "leq"},
)

_NORM_PREFIXES = ("L1_", "L2_", "Linf_")


def resolution_ladder_plan(
    resolutions: Sequence[int] = (200, 400, 800, 1600),
    precisions: Sequence[str] = ("double", "float"),
) -> list[dict[str, Any]]:
    """Plan Brio-Wu HLL rows for a same-time resolution ladder."""

    rows = []
    for nx in resolutions:
        for precision in precisions:
            rows.append(
                _plan_row(
                    suite="resolution_ladder",
                    precision=precision,
                    opt="O2",
                    fast_math=False,
                    riemann="leq",
                    nx=int(nx),
                )
            )
    return rows


def time_slice_plan(
    times: Sequence[float] = (0.02, 0.04, 0.06, 0.08, 0.10),
    variants: Sequence[Mapping[str, Any] | str] = DEFAULT_TIME_VARIANTS,
) -> list[dict[str, Any]]:
    """Plan fixed-resolution Brio-Wu rows at multiple output times."""

    rows = []
    for t_end in times:
        for variant in variants:
            spec = _variant_spec(variant)
            rows.append(
                _plan_row(
                    suite="time_sliced_drift",
                    precision=spec["precision"],
                    opt=spec["opt"],
                    fast_math=spec["fast_math"],
                    riemann=spec["riemann"],
                    t_end=float(t_end),
                )
            )
    return rows


def thread_repro_plan(threads: Sequence[int] = (1, 2, 4, 8)) -> list[dict[str, Any]]:
    """Plan OpenMP thread reproducibility rows for the strict reference variant."""

    return [
        _plan_row(
            suite="thread_repro",
            precision="double",
            opt="O2",
            fast_math=False,
            riemann="leq",
            omp_num_threads=int(thread_count),
        )
        for thread_count in threads
    ]


def brio_wu_cfg(
    base_text: str,
    *,
    nx: int | None = None,
    t_end: float | None = None,
    output_file: str | pathlib.Path | None = None,
) -> str:
    """Return Brio-Wu cfg text with only supplied run keys changed."""

    text = base_text
    if nx is not None:
        text = replace_or_append_cfg(text, "nx", str(int(nx)))
    if t_end is not None:
        text = replace_or_append_cfg(text, "t_end", f"{float(t_end):g}")
    if output_file is not None:
        text = replace_or_append_cfg(text, "output_format", "binary")
        text = replace_or_append_cfg(
            text,
            "output_file",
            pathlib.PurePath(output_file).as_posix(),
        )
    return text


def measure_array(
    variant_row: Mapping[str, Any],
    arr: np.ndarray,
    ref_arr: np.ndarray,
    gamma: float,
    dx: float,
    diagnostics: Mapping[str, Any],
    walltime_s: float,
) -> dict[str, Any]:
    """Measure one Week-14 supplemental row against a same-grid reference."""

    finite = bool(np.isfinite(arr).all() and np.isfinite(ref_arr).all())
    norms = (
        field_norms(
            arr.astype(np.float64, copy=False),
            ref_arr.astype(np.float64, copy=False),
            gamma,
            dx,
        )
        if finite
        else _zero_norms()
    )
    row: dict[str, Any] = {
        "suite": str(variant_row.get("suite", "")),
        "variant": str(variant_row.get("variant", "")),
        "precision": str(variant_row.get("precision", "")),
        "opt": str(variant_row.get("opt", "")),
        "fast_math": bool(variant_row.get("fast_math", False)),
        "riemann": str(variant_row.get("riemann", "")),
        "finite": finite,
        "steps": int(diagnostics.get("steps", 0) or 0),
        "divB_max": _finite_float(diagnostics.get("divB_max", 0.0)),
        "walltime_s": _finite_float(walltime_s),
    }
    for key in ("nx", "t_end", "omp_num_threads"):
        if key in variant_row:
            row[key] = variant_row[key]
    row.update({key: _finite_float(value) for key, value in norms.items()})
    return row


def run_case_with_env(
    label: str,
    cfg_text: str,
    run_dir: str | pathlib.Path,
    bin_path: str | pathlib.Path,
    source_cfg: str | pathlib.Path,
    commit: str,
    binary_sha256: str,
    *,
    output_bin: str | pathlib.Path | None = None,
    experiment: str = EXPERIMENT,
    env: Mapping[str, str] | None = None,
):
    """Run one solver case with optional environment overrides and metadata."""

    run_path = pathlib.Path(run_dir)
    run_path.mkdir(parents=True, exist_ok=True)
    cfg_path = run_path / "config.cfg"
    cfg_path.write_text(cfg_text, encoding="utf-8")
    stdout_path = run_path / "stdout.txt"
    stderr_path = run_path / "stderr.txt"
    command = [str(bin_path), str(cfg_path)]
    output_bin_path = pathlib.Path(output_bin) if output_bin is not None else None
    merged_env = os.environ.copy()
    if env:
        merged_env.update({str(key): str(value) for key, value in env.items()})
    start = time.time()
    t0 = time.perf_counter()
    with stdout_path.open("w", encoding="utf-8") as fo, stderr_path.open("w", encoding="utf-8") as fe:
        result = subprocess.run(
            command,
            cwd=str(ROOT),
            stdout=fo,
            stderr=fe,
            check=False,
            env=merged_env,
        )
    elapsed = time.perf_counter() - t0
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
    source_path = pathlib.Path(source_cfg)
    meta = {
        "experiment": experiment,
        "name": label,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": commit,
        "binary": str(bin_path),
        "binary_sha256": binary_sha256,
        "source_config": str(source_path),
        "source_config_sha256": sha256_file(source_path) if source_path.is_file() else "unknown",
        "run_config": str(cfg_path),
        "run_config_sha256": sha256_file(cfg_path),
        "run_config_text": cfg_text,
        "command": command,
        "env": dict(env or {}),
        "returncode": result.returncode,
        "elapsed_wall_s": elapsed,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "stderr_diagnostics": parse_mhd_diagnostics(stderr_text),
    }
    if output_bin_path is not None:
        meta["output_binary"] = str(output_bin_path)
    (run_path / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"run '{label}' failed (rc={result.returncode}); see {stderr_path}")
    if output_bin_path is not None and (
        not output_bin_path.is_file() or output_bin_path.stat().st_mtime < start
    ):
        raise RuntimeError(f"run '{label}' did not (re)produce {output_bin_path}; see {stderr_path}")
    return result, meta, stderr_text


def run_planned_case(
    plan_row: Mapping[str, Any],
    *,
    out: str | pathlib.Path,
    binary: str | pathlib.Path,
    base_cfg_text: str | None = None,
    runner: Callable[..., Any] = run_case,
    reader: Callable[[str | pathlib.Path], tuple[Any, np.ndarray]] = read_binary,
    commit: str | None = None,
    binary_sha: str | None = None,
    ref_arr: np.ndarray | None = None,
    gamma: float | None = None,
    keep_grid: bool = False,
) -> tuple[dict[str, Any], np.ndarray, Any]:
    """Generate cfg, run one planned case, read the grid, measure, then clean up."""

    out_dir = pathlib.Path(out)
    label = _run_label(plan_row)
    run_dir = out_dir / "runs" / label
    grid_path = run_dir / "grid.bin"
    cfg_text = brio_wu_cfg(
        base_cfg_text if base_cfg_text is not None else CASE.read_text(encoding="utf-8"),
        nx=int(plan_row["nx"]) if "nx" in plan_row else None,
        t_end=float(plan_row["t_end"]) if "t_end" in plan_row else None,
        output_file=grid_path,
    )
    binary_path = pathlib.Path(binary)
    if binary_sha is None:
        binary_sha = sha256_file(binary_path) if binary_path.is_file() else "unknown"
    if commit is None:
        commit = git_commit()
    _result, meta, stderr_text = _call_runner(
        runner,
        str(plan_row.get("variant", label)),
        cfg_text,
        run_dir,
        binary_path,
        CASE,
        commit,
        binary_sha,
        output_bin=grid_path,
        experiment=EXPERIMENT,
        env=plan_row.get("env", {}),
    )
    diagnostics = meta.get("stderr_diagnostics") or parse_mhd_diagnostics(stderr_text)
    header, arr = reader(grid_path)
    reference = arr if ref_arr is None else ref_arr
    row = measure_array(
        plan_row,
        arr,
        reference,
        _cfg_float_from_text(cfg_text, "gamma", 2.0) if gamma is None else gamma,
        float(getattr(header, "dx")),
        diagnostics,
        float(meta.get("elapsed_wall_s", 0.0)),
    )
    row["run_dir"] = str(run_dir)
    row["metadata_path"] = str(run_dir / "metadata.json")
    if not keep_grid and grid_path.is_file():
        grid_path.unlink()
    return row, arr, header


def run_resolution_ladder(
    out: str | pathlib.Path,
    binary_for_precision: Mapping[str, str | pathlib.Path],
    *,
    keep_grids: bool = False,
    resolutions: Sequence[int] = (200, 400, 800, 1600),
    reference_nx: int | None = 1600,
    base_cfg_text: str | None = None,
    runner: Callable[..., Any] = run_case,
    reader: Callable[[str | pathlib.Path], tuple[Any, np.ndarray]] = read_binary,
) -> dict[str, Any]:
    """Run the resolution ladder suite and write summary plus figure."""

    suite_dir = pathlib.Path(out) / "resolution_ladder"
    plans = resolution_ladder_plan(resolutions=resolutions)
    commit = git_commit()
    gamma = _cfg_float_from_text(base_cfg_text or CASE.read_text(encoding="utf-8"), "gamma", 2.0)
    rows: list[dict[str, Any]] = []
    arrays: dict[tuple[str, int], np.ndarray] = {}
    headers: dict[tuple[str, int], Any] = {}

    for plan in plans:
        binary = binary_for_precision[str(plan["precision"])]
        row, arr, header = run_planned_case(
            plan,
            out=suite_dir,
            binary=binary,
            base_cfg_text=base_cfg_text,
            runner=runner,
            reader=reader,
            commit=commit,
            gamma=gamma,
            keep_grid=keep_grids,
        )
        rows.append(row)
        arrays[(str(plan["precision"]), int(plan["nx"]))] = arr
        headers[(str(plan["precision"]), int(plan["nx"]))] = header

    ref_nx = int(reference_nx or max(resolutions))
    ref_arr = arrays.get(("double", ref_nx))
    if ref_arr is not None:
        measured = []
        for plan, row in zip(plans, rows, strict=True):
            nx = int(plan["nx"])
            header = headers[(str(plan["precision"]), nx)]
            ref_same_grid = ref_arr if nx == ref_nx else _downsample_x(ref_arr, nx)
            measured.append(
                _preserve_run_provenance(
                    measure_array(
                        plan,
                        arrays[(str(plan["precision"]), nx)],
                        ref_same_grid,
                        gamma,
                        float(getattr(header, "dx")),
                        {"steps": row["steps"], "divB_max": row["divB_max"]},
                        float(row["walltime_s"]),
                    ),
                    row,
                )
            )
        rows = measured
    payload = _suite_payload("resolution_ladder", rows, commit)
    _write_suite_outputs(payload, suite_dir, plot_resolution_ladder)
    return payload


def run_time_sliced_drift(
    out: str | pathlib.Path,
    binary_for_variant: Mapping[str, str | pathlib.Path],
    *,
    keep_grids: bool = False,
    times: Sequence[float] = (0.02, 0.04, 0.06, 0.08, 0.10),
    variants: Sequence[Mapping[str, Any] | str] = DEFAULT_TIME_VARIANTS,
    base_cfg_text: str | None = None,
    runner: Callable[..., Any] = run_case,
    reader: Callable[[str | pathlib.Path], tuple[Any, np.ndarray]] = read_binary,
) -> dict[str, Any]:
    """Run time-sliced drift, comparing each time to double-O2-leq."""

    suite_dir = pathlib.Path(out) / "time_sliced_drift"
    plans = time_slice_plan(times=times, variants=variants)
    commit = git_commit()
    gamma = _cfg_float_from_text(base_cfg_text or CASE.read_text(encoding="utf-8"), "gamma", 2.0)
    rows = []
    refs: dict[float, np.ndarray] = {}
    pending: list[tuple[Mapping[str, Any], np.ndarray, Any, dict[str, Any]]] = []
    for plan in plans:
        row, arr, header = run_planned_case(
            plan,
            out=suite_dir,
            binary=binary_for_variant[str(plan["variant"])],
            base_cfg_text=base_cfg_text,
            runner=runner,
            reader=reader,
            commit=commit,
            gamma=gamma,
            keep_grid=keep_grids,
        )
        if str(plan["variant"]) == REFERENCE_VARIANT:
            refs[float(plan["t_end"])] = arr
        pending.append((plan, arr, header, row))
    for plan, arr, header, run_row in pending:
        ref = refs[float(plan["t_end"])]
        rows.append(
            _preserve_run_provenance(
                measure_array(
                    plan,
                    arr,
                    ref,
                    gamma,
                    float(getattr(header, "dx")),
                    {"steps": run_row["steps"], "divB_max": run_row["divB_max"]},
                    float(run_row["walltime_s"]),
                ),
                run_row,
            )
        )
    payload = _suite_payload("time_sliced_drift", rows, commit)
    _write_suite_outputs(payload, suite_dir, plot_time_sliced_drift)
    return payload


def run_thread_repro(
    out: str | pathlib.Path,
    binary: str | pathlib.Path,
    *,
    keep_grids: bool = False,
    threads: Sequence[int] = (1, 2, 4, 8),
    base_cfg_text: str | None = None,
    runner: Callable[..., Any] = run_case,
    reader: Callable[[str | pathlib.Path], tuple[Any, np.ndarray]] = read_binary,
) -> dict[str, Any]:
    """Run OpenMP thread reproducibility rows, comparing all to 1 thread."""

    suite_dir = pathlib.Path(out) / "thread_repro"
    plans = thread_repro_plan(threads=threads)
    commit = git_commit()
    gamma = _cfg_float_from_text(base_cfg_text or CASE.read_text(encoding="utf-8"), "gamma", 2.0)
    pending = []
    ref_arr = None
    for plan in plans:
        row, arr, header = run_planned_case(
            plan,
            out=suite_dir,
            binary=binary,
            base_cfg_text=base_cfg_text,
            runner=runner,
            reader=reader,
            commit=commit,
            gamma=gamma,
            keep_grid=keep_grids,
        )
        if int(plan["omp_num_threads"]) == 1:
            ref_arr = arr
        pending.append((plan, arr, header, row))
    if ref_arr is None:
        raise ValueError("thread reproducibility suite requires omp_num_threads=1 reference")
    rows = [
        _preserve_run_provenance(
            measure_array(
                plan,
                arr,
                ref_arr,
                gamma,
                float(getattr(header, "dx")),
                {"steps": run_row["steps"], "divB_max": run_row["divB_max"]},
                float(run_row["walltime_s"]),
            ),
            run_row,
        )
        for plan, arr, header, run_row in pending
    ]
    payload = _suite_payload("thread_repro", rows, commit)
    _write_suite_outputs(payload, suite_dir, plot_thread_repro)
    return payload


def render_report(payload: Mapping[str, Any]) -> str:
    """Render a markdown report for the Week-14 supplemental evidence packet."""

    suites = payload.get("suites", {})
    lines = [
        "# Week 14 Supplemental MHD Evidence",
        "",
        f"- Git commit: `{payload.get('git_commit', 'unknown')}`",
        "- Report 2 requirement mapping:",
        "  - resolution ladder: grid-convergence context for Brio-Wu MHD precision comparisons.",
        "  - time-sliced drift: temporal growth of deterministic fp32/fp64 and build-flag drift.",
        "  - thread reproducibility: OpenMP reproducibility check against the one-thread reference.",
        "- Docker Verificarlo MCA remains formal evidence from the Week14 summary; these deterministic supplemental runs do not replace it.",
    ]
    if suites:
        lines.extend(["", "## Suite Outputs"])
        for name in ("resolution_ladder", "time_sliced_drift", "thread_repro"):
            if name in suites:
                label = name.replace("_", " ")
                suite = suites[name]
                line = f"- {label}: `{suite.get('summary_path', 'summary.json')}`"
                if "figure_path" in suite:
                    line += f", `{suite['figure_path']}`"
                if "rows" in suite:
                    line += f" ({suite['rows']} rows)"
                lines.append(line)
        if any("headlines" in suite for suite in suites.values()):
            lines.extend(["", "## Headline Checks"])
            for name in ("resolution_ladder", "time_sliced_drift", "thread_repro"):
                suite = suites.get(name)
                if not suite or "headlines" not in suite:
                    continue
                label = name.replace("_", " ")
                lines.append(f"- {label}: {_format_headlines(suite['headlines'])}")
        lines.extend(
            [
                "",
                "## How To Read The Figures",
                "- `resolution_ladder/figure.png`: x-axis is grid resolution; y-axis is density L1 error against the nx=1600 fp64 reference projected to the same grid. A downward trend indicates the measured precision effect is not just a coarse-grid artifact.",
                "- `time_sliced_drift/figure.png`: x-axis is t_end; y-axis is By Linf drift against the fp64 O2 reference at the same time. Growth with time shows how deterministic precision/build choices separate as the shock tube evolves.",
                "- `thread_repro/figure.png`: x-axis is OMP_NUM_THREADS; y-axis is rho Linf drift against the one-thread fp64 O2 reference. Near-zero values support CPU-thread reproducibility for this Week-14 pilot case.",
                "",
                "## Interpretation Boundary",
                "- These plots are supplemental deterministic evidence for Report 2 discussion: they explain grid sensitivity, temporal drift, and CPU threading effects on the Brio-Wu HLL pilot.",
                "- They do not broaden the Week-14 claim to 2D, GPU, HLLD, or Lyapunov behavior.",
                "- Stochastic precision evidence remains the Docker Verificarlo MCA packet recorded by the Week-14 main summary.",
                "- Binary grids are transient: each grid is measured, summarized, and then deleted unless an explicit keep-grids run is requested.",
            ]
        )
    return "\n".join(lines) + "\n"


def suite_headlines(summary: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Return compact supervisor-facing checks for one supplemental suite."""

    rows = list(_summary_rows(summary))
    finite_rows = [row for row in rows if bool(row.get("finite", False))]
    return {
        "finite_rows": len(finite_rows),
        "total_rows": len(rows),
        "max_divB_abs": _max_abs(finite_rows, "divB_max"),
        "max_Linf_By": _max_abs(finite_rows, "Linf_By"),
        "max_Linf_rho": _max_abs(finite_rows, "Linf_rho"),
        "max_thread_Linf_rho": _max_abs(
            [row for row in finite_rows if "omp_num_threads" in row],
            "Linf_rho",
        ),
    }


def relative_rows(
    rows: Sequence[Mapping[str, Any]],
    reference_selector: Callable[[Mapping[str, Any]], bool],
) -> list[dict[str, Any]]:
    """Copy rows and add relative norm columns against one selected reference row."""

    refs = [row for row in rows if reference_selector(row)]
    if len(refs) != 1:
        raise ValueError(f"expected exactly one reference row, found {len(refs)}")
    reference = refs[0]

    out = []
    for row in rows:
        copied = dict(row)
        copied["is_relative_reference"] = row is reference
        for key, value in row.items():
            if key.startswith(_NORM_PREFIXES) and key in reference:
                copied[f"rel_{key}"] = float(value) - float(reference[key])
        out.append(copied)
    return out


def write_summary(path: str | pathlib.Path, payload: Mapping[str, Any]) -> None:
    """Write JSON summary with numpy scalar/array values converted to plain JSON."""

    out = pathlib.Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(_jsonable(payload), indent=2) + "\n", encoding="utf-8")


def plot_resolution_ladder(summary: Mapping[str, Any], path: str | pathlib.Path) -> None:
    """Plot resolution ladder norm trends from an already-computed summary."""

    plt = _pyplot()
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    rows = list(_summary_rows(summary))
    plotted_values: list[float] = []
    dropped_reference: list[tuple[str, int]] = []
    for precision in sorted({str(row.get("precision", "unknown")) for row in rows}):
        series = sorted(
            (row for row in rows if str(row.get("precision", "unknown")) == precision),
            key=lambda row: float(row.get("nx", 0)),
        )
        xs: list[float] = []
        ys: list[float] = []
        for row in series:
            value = _positive_metric(row, "L1_rho")
            if value is None:
                # An identically-zero error is the self-reference point (the
                # fp64 finest-grid run compared to itself). It cannot appear on
                # a log axis; recording it for annotation avoids clamping it to
                # the float64 tiny floor, which otherwise stretched the y-axis
                # down to ~1e-300 and hid the real convergence trend.
                dropped_reference.append((precision, int(float(row.get("nx", 0)))))
                continue
            xs.append(float(row["nx"]))
            ys.append(value)
            plotted_values.append(value)
        if xs:
            ax.plot(xs, ys, marker="o", label=precision)
    ax.set_xlabel("nx")
    ax.set_ylabel("L1 rho vs reference")
    ax.set_title("Brio-Wu resolution ladder")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    if plotted_values:
        lo = 10.0 ** math.floor(math.log10(min(plotted_values)))
        hi = 10.0 ** math.ceil(math.log10(max(plotted_values)))
        ax.set_ylim(lo, hi)
    ax.grid(True, which="both", alpha=0.3)
    if dropped_reference:
        note = ", ".join(f"{prec} nx={nx}" for prec, nx in dropped_reference)
        ax.text(
            0.02,
            0.02,
            f"reference (error=0, off log axis): {note}",
            transform=ax.transAxes,
            fontsize=7,
            va="bottom",
            alpha=0.7,
        )
    ax.legend()
    _savefig(fig, path)


def plot_time_sliced_drift(summary: Mapping[str, Any], path: str | pathlib.Path) -> None:
    """Plot time-sliced drift from an already-computed summary."""

    plt = _pyplot()
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    rows = list(_summary_rows(summary))
    for variant in sorted({str(row.get("variant", "unknown")) for row in rows}):
        series = sorted(
            (row for row in rows if str(row.get("variant", "unknown")) == variant),
            key=lambda row: float(row.get("t_end", 0.0)),
        )
        ax.plot(
            [float(row["t_end"]) for row in series],
            [_metric(row, "Linf_By") for row in series],
            marker="o",
            label=variant,
        )
    ax.set_xlabel("t_end")
    ax.set_ylabel("Linf By vs reference")
    ax.set_title("Brio-Wu time-sliced drift")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize="small")
    _savefig(fig, path)


def plot_thread_repro(summary: Mapping[str, Any], path: str | pathlib.Path) -> None:
    """Plot thread reproducibility drift from an already-computed summary."""

    plt = _pyplot()
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    rows = sorted(_summary_rows(summary), key=lambda row: int(row.get("omp_num_threads", 0)))
    ax.plot(
        [int(row["omp_num_threads"]) for row in rows],
        [_metric(row, "Linf_rho") for row in rows],
        marker="o",
    )
    ax.set_xlabel("OMP_NUM_THREADS")
    ax.set_ylabel("Linf rho vs 1-thread reference")
    ax.set_title("Brio-Wu thread reproducibility")
    ax.grid(True, alpha=0.3)
    _savefig(fig, path)


def write_plan_manifest(path: str | pathlib.Path) -> dict[str, Any]:
    """Write the supplemental plan manifest without executing solver runs."""

    payload = {
        "experiment": EXPERIMENT,
        "case": str(CASE.relative_to(ROOT)).replace("\\", "/"),
        "git_commit": git_commit(),
        "verificarlo_required": True,
        "mca_skip_allowed": False,
        "notes": [
            "Scope is Brio-Wu 1D, HLL, CPU only.",
            "Verificarlo/MCA remains required evidence and is not replaced here.",
        ],
        "plans": {
            "resolution_ladder": resolution_ladder_plan(),
            "time_sliced_drift": time_slice_plan(),
            "thread_repro": thread_repro_plan(),
        },
    }
    write_summary(path, payload)
    return payload


def _plan_row(
    *,
    suite: str,
    precision: str,
    opt: str,
    fast_math: bool,
    riemann: str,
    nx: int | None = None,
    t_end: float | None = None,
    omp_num_threads: int | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "suite": suite,
        "case": "brio_wu_1d",
        "precision": precision,
        "variant": _variant_label(precision, opt, fast_math, riemann),
        "opt": opt,
        "fast_math": bool(fast_math),
        "riemann": riemann,
        "hardware": "cpu",
        "solver": "HLL",
    }
    if nx is not None:
        row["nx"] = nx
    if t_end is not None:
        row["t_end"] = t_end
    if omp_num_threads is not None:
        row["omp_num_threads"] = omp_num_threads
        row["env"] = {"OMP_NUM_THREADS": str(omp_num_threads)}
    return row


def _variant_label(precision: str, opt: str, fast_math: bool, riemann: str) -> str:
    math_label = "fastmath" if fast_math else "ieee"
    return f"cpu-{precision}-{opt}-{math_label}-{riemann}"


def _variant_spec(variant: Mapping[str, Any] | str) -> dict[str, Any]:
    if isinstance(variant, str):
        parts = variant.split("-")
        if len(parts) != 5 or parts[0] != "cpu":
            raise ValueError(f"unsupported variant label {variant!r}")
        return {
            "precision": parts[1],
            "opt": parts[2],
            "fast_math": parts[3] in {"fast", "fastmath"},
            "riemann": parts[4],
        }
    return {
        "precision": str(variant["precision"]),
        "opt": str(variant["opt"]),
        "fast_math": bool(variant.get("fast_math", False)),
        "riemann": str(variant.get("riemann", "leq")),
    }


def _jsonable(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _summary_rows(summary: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> Iterable[Mapping[str, Any]]:
    if isinstance(summary, Mapping):
        if "rows" not in summary:
            raise ValueError("summary mapping must contain a 'rows' sequence")
        rows = summary["rows"]
    else:
        rows = summary
    if isinstance(rows, Mapping) or not isinstance(rows, Iterable):
        raise ValueError("summary must be a row sequence or contain a 'rows' sequence")
    return rows


def _run_label(row: Mapping[str, Any]) -> str:
    parts = [str(row.get("variant", "run"))]
    for key in ("nx", "t_end", "omp_num_threads"):
        if key in row:
            parts.append(f"{key}-{row[key]}")
    return "_".join(parts).replace(".", "p")


def _call_runner(runner: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    if kwargs.get("env") and runner is run_case:
        return run_case_with_env(*args, **kwargs)
    try:
        params = inspect.signature(runner).parameters
    except (TypeError, ValueError):
        params = {}
    accepts_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in params.values())
    if "env" not in params and not accepts_kwargs:
        kwargs.pop("env", None)
    return runner(*args, **kwargs)


def _cfg_float_from_text(text: str, key: str, default: float) -> float:
    for line in text.splitlines():
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


def _zero_norms() -> dict[str, float]:
    return {
        f"{norm}_{field}": 0.0
        for field in ("rho", "By", "p", "vx")
        for norm in ("L1", "L2", "Linf")
    }


def _downsample_x(arr: np.ndarray, nx: int) -> np.ndarray:
    if arr.shape[1] == nx:
        return arr
    if arr.shape[1] % nx != 0:
        raise ValueError(f"cannot downsample reference nx={arr.shape[1]} to nx={nx}")
    factor = arr.shape[1] // nx
    return arr.reshape(arr.shape[0], nx, factor, arr.shape[2]).mean(axis=2)


def _suite_payload(suite: str, rows: Sequence[Mapping[str, Any]], commit: str) -> dict[str, Any]:
    return {
        "experiment": EXPERIMENT,
        "suite": suite,
        "case": str(CASE.relative_to(ROOT)).replace("\\", "/"),
        "git_commit": commit,
        "rows": [dict(row) for row in rows],
    }


def _write_suite_outputs(
    payload: Mapping[str, Any],
    suite_dir: pathlib.Path,
    plotter: Callable[[Mapping[str, Any], str | pathlib.Path], None],
) -> None:
    write_summary(suite_dir / "summary.json", payload)
    plotter(payload, suite_dir / "figure.png")


def _preserve_run_provenance(
    measured: Mapping[str, Any],
    run_row: Mapping[str, Any],
) -> dict[str, Any]:
    out = dict(measured)
    for key in ("run_dir", "metadata_path"):
        if key in run_row:
            out[key] = run_row[key]
    return out


def _max_abs(rows: Sequence[Mapping[str, Any]], key: str) -> float:
    values = [abs(float(row[key])) for row in rows if key in row and math.isfinite(float(row[key]))]
    return max(values) if values else 0.0


def _format_headlines(headlines: Mapping[str, Any]) -> str:
    parts = [
        f"finite {int(headlines.get('finite_rows', 0))}/{int(headlines.get('total_rows', 0))}",
        f"max |divB| {_finite_float(headlines.get('max_divB_abs', 0.0)):.3e}",
    ]
    if "max_Linf_By" in headlines:
        parts.append(f"max Linf(By) {_finite_float(headlines['max_Linf_By']):.3e}")
    if "max_thread_Linf_rho" in headlines:
        parts.append(f"max thread Linf(rho) {_finite_float(headlines['max_thread_Linf_rho']):.3e}")
    return "; ".join(parts)


def _metric(row: Mapping[str, Any], key: str) -> float:
    if row.get("finite") is False:
        return float("nan")
    value = float(row.get(key, 0.0))
    return max(value, np.finfo(np.float64).tiny)


def _positive_metric(row: Mapping[str, Any], key: str) -> float | None:
    """Return the raw finite metric for log plotting, or None if non-plottable.

    A zero (self-reference) or non-finite value has no place on a log axis, so
    callers can skip/annotate it rather than clamp it to the float64 tiny floor.
    """
    if row.get("finite") is False:
        return None
    value = float(row.get(key, 0.0))
    if not math.isfinite(value) or value <= 0.0:
        return None
    return value


def _pyplot():
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    return plt


def _savefig(fig: Any, path: str | pathlib.Path) -> None:
    out = pathlib.Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    fig.clf()


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--write-plan",
        action="store_true",
        help="write manifest.json only; no solver or Verificarlo execution is launched",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    manifest = out / "manifest.json"
    write_plan_manifest(manifest)
    print(f"wrote {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
