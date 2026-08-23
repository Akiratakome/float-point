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
    # Report-2 addition: carries the temporal axis past the linear stage, which
    # the t=1.0 stopping time of the validation ladder does not reach.
    "kelvin_helmholtz_2d": {
        "cfg": ROOT / "tests" / "cases" / "kelvin_helmholtz_2d" / "kh.cfg",
        "nx": 128,
        "ny": 128,
        "t_start": 0.2,
        "t_end_max": 3.0,
        "n_slices": 20,
        "fit_window": [0.2, 3.0],
    },
    # Early-time companions: resolve the approach to the saturation level that
    # the windows above already sit on at their first sample.
    "kelvin_helmholtz_2d_early": {
        "cfg": ROOT / "tests" / "cases" / "kelvin_helmholtz_2d" / "kh.cfg",
        "nx": 128,
        "ny": 128,
        "t_start": 0.01,
        "t_end_max": 0.19,
        "n_slices": 10,
        "fit_window": [0.01, 0.19],
    },
    "orszag_tang_2d_early": {
        "cfg": ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg",
        "nx": 128,
        "ny": 128,
        "t_start": 0.005,
        "t_end_max": 0.045,
        "n_slices": 10,
        "fit_window": [0.005, 0.045],
    },
}
EXPECTED_SAMPLE_COUNTS = {
    case: int(spec["n_slices"]) for case, spec in CASES.items()
}
EXPECTED_REPORT_RUNS = 2 * sum(EXPECTED_SAMPLE_COUNTS.values())
REQUIRED_RUN_PROVENANCE = (
    "git_commit",
    "binary_sha256",
    "run_config_sha256",
    "source_config_sha256",
    "source_config",
    "run_config",
    "run_config_text",
)


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


def route_output_dir(
    requested_out: pathlib.Path,
    *,
    case: str,
    smoke: bool,
) -> pathlib.Path:
    out = requested_out if requested_out.is_absolute() else ROOT / requested_out
    if out.resolve() != DEFAULT_OUT.resolve():
        return out
    suffixes = []
    if case != "all":
        suffixes.append(case)
    if smoke:
        suffixes.append("smoke")
    if not suffixes:
        return DEFAULT_OUT
    return DEFAULT_OUT.with_name("_".join((DEFAULT_OUT.name, *suffixes)))


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


def record_series_aligned(record: Mapping[str, Any]) -> bool:
    try:
        lengths = {len(record[key]) for key in ("times", "l1", "linf")}
    except (KeyError, TypeError):
        return False
    return len(lengths) == 1


def validate_record_alignment(records: Sequence[Mapping[str, Any]]) -> None:
    for record in records:
        if not record_series_aligned(record):
            case = record.get("case", "<unknown>")
            lengths = {
                key: len(record.get(key, ())) for key in ("times", "l1", "linf")
            }
            raise ValueError(f"{case} series length mismatch: {lengths}")


def quantify_fit_quality(records: Sequence[dict[str, Any]]) -> None:
    """Attach fixed-window log-fit residual diagnostics without changing slopes."""
    for record in records:
        times = np.asarray(record["times"], dtype=np.float64)
        for metric, fit_key in (("l1", "fit_l1"), ("linf", "fit_linf")):
            values = np.asarray(record[metric], dtype=np.float64)
            fit = record[fit_key]
            slope = fit.get("slope")
            intercept = fit.get("intercept")
            used = np.asarray(fit.get("times_used", ()), dtype=np.float64)
            mask = np.isfinite(times) & np.isfinite(values) & (values > 0.0)
            if used.size:
                mask &= np.any(
                    np.isclose(times[:, None], used[None, :], rtol=0.0, atol=1.0e-12),
                    axis=1,
                )
            else:
                window = fit.get("fit_window") or record.get("fit_window")
                if window is not None:
                    mask &= (times >= float(window[0])) & (times <= float(window[1]))
            fit_t = times[mask]
            fit_values = values[mask]
            if slope is None or intercept is None or fit_t.size < 2:
                fit.update({
                    "r2_log": None,
                    "rmse_log": None,
                    "max_abs_residual_log": None,
                })
                continue
            log_values = np.log(fit_values)
            fitted = float(slope) * fit_t + float(intercept)
            residual = log_values - fitted
            ss_res = float(np.sum(residual * residual))
            centred = log_values - float(np.mean(log_values))
            ss_tot = float(np.sum(centred * centred))
            r2 = 1.0 if ss_tot == 0.0 and ss_res == 0.0 else (
                None if ss_tot == 0.0 else 1.0 - ss_res / ss_tot
            )
            fit.update({
                "r2_log": None if r2 is None else float(r2),
                "rmse_log": float(np.sqrt(np.mean(residual * residual))),
                "max_abs_residual_log": float(np.max(np.abs(residual))),
            })


def evaluate_gates(
    records: Sequence[dict[str, Any]],
    runs: Sequence[dict[str, Any]],
    *,
    mode: str,
    selected_cases: Sequence[str],
) -> dict[str, Any]:
    quantify_fit_quality(records)
    by_case = {record["case"]: record for record in records}
    try:
        finite_nonnegative = all(
            math.isfinite(float(value)) and float(value) >= 0.0
            for record in records
            for key in ("l1", "linf")
            for value in record[key]
        )
    except (KeyError, TypeError, ValueError):
        finite_nonnegative = False
    ot_lambda = by_case.get("orszag_tang_2d", {}).get("lambda_l1")
    ot_positive = ot_lambda is not None and math.isfinite(float(ot_lambda)) and float(ot_lambda) > 0.0
    complete = len(records) == len(CASES) and set(by_case) == set(CASES)
    selected_complete = (
        len(selected_cases) == len(CASES) and set(selected_cases) == set(CASES)
    )
    aligned = all(record_series_aligned(record) for record in records)
    sample_counts_exact = complete and all(
        len(by_case[case].get("times", ())) == expected
        for case, expected in EXPECTED_SAMPLE_COUNTS.items()
    )
    try:
        lambdas_finite = complete and all(
            math.isfinite(float(by_case[case][key]))
            for case in CASES
            for key in ("lambda_l1", "lambda_linf")
        )
    except (KeyError, TypeError, ValueError):
        lambdas_finite = False
    try:
        fits_sufficient = complete and all(
            int(by_case[case][fit]["n_fit"]) >= 2
            for case in CASES
            for fit in ("fit_l1", "fit_linf")
        )
    except (KeyError, TypeError, ValueError):
        fits_sufficient = False
    try:
        fit_quality_quantified = complete and all(
            math.isfinite(float(by_case[case][fit][metric]))
            for case in CASES
            for fit in ("fit_l1", "fit_linf")
            for metric in ("r2_log", "rmse_log", "max_abs_residual_log")
        )
    except (KeyError, TypeError, ValueError):
        fit_quality_quantified = False
    run_count_exact = len(runs) == EXPECTED_REPORT_RUNS
    runs_successful = run_count_exact and all(run.get("returncode") == 0 for run in runs)
    provenance_complete = run_count_exact and all(
        all(run.get(field) not in (None, "") for field in REQUIRED_RUN_PROVENANCE)
        for run in runs
    )
    technical_pass = bool(complete and finite_nonnegative and ot_positive)
    report_grade_pass = bool(
        mode == "report-grade"
        and selected_complete
        and technical_pass
        and aligned
        and sample_counts_exact
        and lambdas_finite
        and fits_sufficient
        and fit_quality_quantified
        and run_count_exact
        and runs_successful
        and provenance_complete
    )
    return {
        "pass": report_grade_pass,
        "technical_pass": technical_pass,
        "report_grade_pass": report_grade_pass,
        "mode_is_report_grade": mode == "report-grade",
        "cases_complete": complete,
        "selected_cases_complete": selected_complete,
        "all_drift_finite_nonnegative": finite_nonnegative,
        "orszag_tang_positive_lambda": ot_positive,
        "series_aligned": aligned,
        "sample_counts_exact": sample_counts_exact,
        "required_lambdas_finite": lambdas_finite,
        "fit_counts_sufficient": fits_sufficient,
        "fit_quality_quantified": fit_quality_quantified,
        "run_count_exact": run_count_exact,
        "runs_successful": runs_successful,
        "run_provenance_complete": provenance_complete,
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
                    fit_t[-1], fit_log10[-1],
                    f"lambda={float(fit['slope']):.3g}; R2={float(fit['r2_log']):.3f}",
                    color=line.get_color(), fontsize=8, ha="right", va="bottom",
                )
        ax.set_xlabel("time")
        ax.set_ylabel("log10 L1 density drift")
        ax.legend(frameon=False)
        fig.savefig(figure)
        plt.close(fig)
    return figure


def ordering_statement(
    planned_contrast: bool | None,
    *,
    ot_l1: Any,
    brio_l1: Any,
) -> str:
    prefix = "Bounded result: the planned OT>Brio-Wu L1 contrast"
    if planned_contrast is None:
        return f"{prefix} is unavailable/not comparable because both case fits are required."
    result = "is observed" if planned_contrast else "is not observed"
    return (
        f"{prefix} {result} under the fixed fit windows "
        f"(OT {float(ot_l1):.6g} vs Brio-Wu {float(brio_l1):.6g})."
    )


def write_outputs(
    out_dir: pathlib.Path,
    records: Sequence[dict[str, Any]],
    runs: Sequence[dict[str, Any]],
    *,
    mode: str = "diagnostic",
    selected_cases: Sequence[str] | None = None,
) -> dict[str, Any]:
    if mode not in ("diagnostic", "report-grade"):
        raise ValueError(f"unknown mode {mode!r}")
    selected = list(selected_cases) if selected_cases is not None else [
        str(record["case"]) for record in records
    ]
    validate_record_alignment(records)
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    gates = evaluate_gates(records, runs, mode=mode, selected_cases=selected)
    figure = plot_records(out, records)
    by_case = {record["case"]: record for record in records}
    brio_l1 = by_case.get("brio_wu_1d", {}).get("lambda_l1")
    ot_l1 = by_case.get("orszag_tang_2d", {}).get("lambda_l1")
    ot_linf = by_case.get("orszag_tang_2d", {}).get("lambda_linf")
    planned_contrast = (
        None if brio_l1 is None or ot_l1 is None
        else bool(float(ot_l1) > float(brio_l1))
    )
    ot_linf_positive = None if ot_linf is None else bool(float(ot_linf) > 0.0)
    generation_commit = git_commit()
    generator = pathlib.Path(__file__).resolve()
    run_commits = sorted({
        str(run["git_commit"]) for run in runs if run.get("git_commit") is not None
    })
    payload = {
        "experiment": "week15-mhd-temporal-divergence",
        "mode": mode,
        "selected_cases": selected,
        "git_commit": generation_commit,
        "git_commit_semantics": "summary-generation checkout",
        "analysis_generator": {
            "path": generator.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(generator),
            "identity": "exact script content used to generate this summary",
        },
        "run_provenance": {
            "git_commit_field": "runs[].git_commit",
            "git_commits": run_commits,
            "semantics": "checkout recorded when each solver run was executed",
        },
        "gates": gates,
        "records": list(records),
        "runs": list(runs),
        "figure": figure.relative_to(out).as_posix(),
        "interpretation": {
            "formal_maximal_lyapunov": False,
            "statement": "lambda is a Lyapunov-like growth rate of an fp32-vs-fp64 perturbation.",
            "fixed_fit_windows": {
                case: record.get("fit_window") for case, record in by_case.items()
            },
            "planned_ot_exceeds_brio_l1": planned_contrast,
            "orszag_tang_linf_positive": ot_linf_positive,
            "gate_scope": (
                "technical_pass checks case presence, finite nonnegative drift samples, and "
                "a positive Orszag-Tang L1 fit. gates.pass is report_grade_pass and also "
                "requires exact samples, aligned series, finite fits, quantified residual "
                "diagnostics, sufficient fit counts, and 80 successful provenance-complete "
                "runs; neither gate requires "
                "OT>Brio-Wu ordering or a positive Orszag-Tang Linf fit."
            ),
            "fit_quality": (
                "Fixed-window log-linear fit quality is quantified by R2 and log-residual "
                "diagnostics. No minimum R2 is required for the negative-result gate; low R2 "
                "limits interpretation of the fitted slope."
            ),
            "fit_quality_by_case": {
                case: {
                    "l1_r2_log": record["fit_l1"]["r2_log"],
                    "l1_rmse_log": record["fit_l1"]["rmse_log"],
                    "linf_r2_log": record["fit_linf"]["r2_log"],
                    "linf_rmse_log": record["fit_linf"]["rmse_log"],
                }
                for case, record in by_case.items()
            },
        },
    }
    json_path = out / "summary.json"
    csv_path = out / "summary.csv"
    md_path = out / "summary.md"
    json_path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        columns = (
            "case", "pair", "variable", "time", "l1", "linf",
            "lambda_l1", "lambda_linf", "r2_l1", "r2_linf", "rmse_log_l1",
            "rmse_log_linf", "n_fit_l1", "n_fit_linf",
        )
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
                    "r2_l1": record["fit_l1"]["r2_log"],
                    "r2_linf": record["fit_linf"]["r2_log"],
                    "rmse_log_l1": record["fit_l1"]["rmse_log"],
                    "rmse_log_linf": record["fit_linf"]["rmse_log"],
                    "n_fit_l1": record["fit_l1"]["n_fit"],
                    "n_fit_linf": record["fit_linf"]["n_fit"],
                })

    def fmt_lambda(value: Any) -> str:
        return "n/a" if value is None else f"{float(value):.6g}"

    lines = [
        "# MHD Temporal Divergence", "",
        "| case | samples | lambda L1 | R2 L1 | lambda Linf | R2 Linf | n_fit L1 | n_fit Linf | fit window |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for record in records:
        lines.append(
            f"| {record['case']} | {len(record['times'])} | {fmt_lambda(record['lambda_l1'])} | "
            f"{float(record['fit_l1']['r2_log']):.4f} | {fmt_lambda(record['lambda_linf'])} | "
            f"{float(record['fit_linf']['r2_log']):.4f} | {record['fit_l1']['n_fit']} | "
            f"{record['fit_linf']['n_fit']} | {record['fit_window']} |"
        )
    lines.extend([
        "", f"- Mode: {mode}",
        f"- Technical pass: {gates['technical_pass']}",
        f"- Report-grade pass: {gates['report_grade_pass']}",
        f"- Gate pass: {gates['pass']}",
        f"- Figure: `{payload['figure']}`", "",
        "Technical pass checks case presence, finite nonnegative drift samples, and a "
        "positive Orszag-Tang L1 fit. Report-grade pass additionally requires exact samples, "
        "aligned series, finite fits, quantified residual diagnostics, sufficient fit counts, and 80 successful "
        "provenance-complete runs. Neither gate requires OT>Brio-Wu ordering or a positive "
        "Orszag-Tang Linf fit.", "",
        ordering_statement(planned_contrast, ot_l1=ot_l1, brio_l1=brio_l1),
        f"The OT Linf fit is {fmt_lambda(ot_linf)}. Fixed-window log-linear R2 values are "
        + ", ".join(
            f"{by_case[case]['fit_l1']['r2_log']:.4f}/"
            f"{by_case[case]['fit_linf']['r2_log']:.4f} for {case} L1/Linf"
            for case in sorted(by_case)
        )
        + ". Where an OT series is present its near-zero "
        "values limit slope interpretation; no minimum R2 is required for the negative-result gate.", "",
        "The fitted lambda is a Lyapunov-like engineering growth rate of an "
        "fp32-vs-fp64 perturbation, not a formal maximal Lyapunov exponent.", "",
    ])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "json": json_path, "csv": csv_path, "markdown": md_path,
        "figure": figure, "payload": payload,
    }


def refresh_outputs_from_summary(out_dir: pathlib.Path) -> dict[str, Any]:
    """Rebuild analysis products from retained records/runs without solver reruns."""
    summary_path = pathlib.Path(out_dir) / "summary.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    return write_outputs(
        out_dir,
        payload["records"],
        payload["runs"],
        mode=str(payload.get("mode", "report-grade")),
        selected_cases=payload.get("selected_cases", list(CASES)),
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--case", choices=("all", *CASES), default="all")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--keep-grids", action="store_true")
    parser.add_argument(
        "--refresh-summary",
        action="store_true",
        help="Recompute fit diagnostics and outputs from retained summary records; run no solver jobs.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    out = route_output_dir(args.out, case=args.case, smoke=args.smoke)
    if args.refresh_summary:
        if args.case != "all" or args.smoke or args.keep_grids:
            raise ValueError("--refresh-summary cannot be combined with --case, --smoke, or --keep-grids")
        paths = refresh_outputs_from_summary(out)
        print(paths["markdown"])
        return 0 if paths["payload"]["gates"]["pass"] else 1
    binaries = resolve_binaries()
    names = list(CASES) if args.case == "all" else [args.case]
    mode = "report-grade" if args.case == "all" and not args.smoke else "diagnostic"
    records, runs = [], []
    for name in names:
        result = run_case_series(
            name, out, binaries, smoke=args.smoke, keep_grids=args.keep_grids,
        )
        records.append(result["record"])
        runs.extend(result["runs"])
    paths = write_outputs(out, records, runs, mode=mode, selected_cases=names)
    print(paths["markdown"])
    return 0 if paths["payload"]["gates"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
