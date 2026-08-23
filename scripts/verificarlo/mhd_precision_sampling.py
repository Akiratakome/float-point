#!/usr/bin/env python3
"""Week-14 field-specific MHD Verificarlo MCA sampler.

This harness wrapper reuses the Week-13 Verificarlo smoke runner machinery and
turns its sample grids into the schema-complete MCA blocks consumed by the
Week-14 precision pilot. Environments without a supported runner produce a
blocked MCA block rather than failing the experiment.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "experiments" / "week14" / "mhd_precision_pilot" / "mca"
WEEK14_MCA_EXPERIMENT = "week14-mhd-mca"
EXPERIMENT = WEEK14_MCA_EXPERIMENT

for path in (
    ROOT / "scripts",
    ROOT / "scripts" / "metrics",
    ROOT / "scripts" / "regression",
    ROOT / "scripts" / "verificarlo",
):
    sys.path.insert(0, str(path))

import mhd_verificarlo_smoke as smoke  # noqa: E402
from io_helper import stack_samples  # noqa: E402
from mhd_fields import mca_field_spread  # noqa: E402
from mhd_precision_pilot_core import blocked_mca_block  # noqa: E402
from mhd_verificarlo_smoke import (  # noqa: E402
    DEFAULT_CASE,
    DEFAULT_IMAGE,
    base_environment,
    choose_runner,
    probe_runners,
    run_samples,
    write_json,
)


DEFAULT_SAMPLES = 8
DEFAULT_GAMMA = 2.0


def _normalise_solver(solver: str) -> str:
    solver = str(solver).lower()
    if solver not in {"hll", "hlld"}:
        raise ValueError(f"unsupported MHD MCA solver: {solver}")
    return solver


def _case_gamma(case: pathlib.Path = DEFAULT_CASE) -> float:
    """Read gamma from the cfg, matching the Brio-Wu default if absent."""
    if not case.is_file():
        return DEFAULT_GAMMA
    for line in case.read_text(encoding="utf-8").splitlines():
        content = line.split("#", 1)[0].strip()
        if not content or "=" not in content:
            continue
        key, value = [part.strip() for part in content.split("=", 1)]
        if key == "gamma":
            return float(value)
    return DEFAULT_GAMMA


def _sample_args(
    out_dir: pathlib.Path,
    precision: int,
    samples: int,
    image: str,
    solver: str,
    case: pathlib.Path = DEFAULT_CASE,
    jobs: int = 1,
    sample_timeout_s: int = smoke.SAMPLE_TIMEOUT_S,
    backend_lib: str = smoke.DEFAULT_VFC_BACKEND_LIB,
) -> argparse.Namespace:
    return argparse.Namespace(
        case=pathlib.Path(case),
        out=pathlib.Path(out_dir),
        samples=int(samples),
        precision=int(precision),
        image=image,
        probe_only=False,
        solver=_normalise_solver(solver),
        jobs=max(1, int(jobs)),
        sample_timeout_s=int(sample_timeout_s),
        backend_lib=str(backend_lib),
    )


def _blocked(status: str, reason: str, *, runner: str | None = None) -> dict[str, Any]:
    block = blocked_mca_block(status, reason)
    block["runner"] = runner
    return block


def _base_environment_with_experiment_label(
    args: argparse.Namespace,
    probes: list[dict[str, Any]],
    runner: str | None,
    experiment: str = WEEK14_MCA_EXPERIMENT,
) -> dict[str, Any]:
    previous = smoke.EXPERIMENT
    smoke.EXPERIMENT = experiment
    try:
        environment = base_environment(args, probes, runner)
        environment["solver"] = args.solver
        return environment
    finally:
        smoke.EXPERIMENT = previous


def _run_with_experiment_label(
    args: argparse.Namespace,
    probes: list[dict[str, Any]],
    runner: str,
    experiment: str = WEEK14_MCA_EXPERIMENT,
) -> tuple[str, list[dict[str, Any]], str, dict[str, Any]]:
    previous = smoke.EXPERIMENT
    smoke.EXPERIMENT = experiment
    try:
        status, sample_rows, reason = run_samples(args, probes, runner)
        environment = base_environment(args, probes, runner)
        environment["solver"] = args.solver
        return status, sample_rows, reason, environment
    finally:
        smoke.EXPERIMENT = previous


def sample_precision(
    out_dir: pathlib.Path,
    precision: int,
    samples: int = DEFAULT_SAMPLES,
    image: str = DEFAULT_IMAGE,
    solver: str = "hll",
    case: pathlib.Path = DEFAULT_CASE,
    experiment: str = WEEK14_MCA_EXPERIMENT,
    jobs: int = 1,
    sample_timeout_s: int = smoke.SAMPLE_TIMEOUT_S,
    backend_lib: str = smoke.DEFAULT_VFC_BACKEND_LIB,
) -> dict[str, Any]:
    """Run one MCA precision block and return schema-complete field metrics.

    ``jobs`` sets how many independent MCA sample containers run concurrently
    (default 1 = sequential, historical behaviour). ``sample_timeout_s`` sets
    the per-attempt timeout, and ``backend_lib`` selects the interflop backend.
    """
    solver = _normalise_solver(solver)
    probes = probe_runners(image)
    runner = choose_runner(probes)
    args = _sample_args(
        pathlib.Path(out_dir), precision, samples, image, solver,
        pathlib.Path(case), jobs=jobs, sample_timeout_s=sample_timeout_s,
        backend_lib=backend_lib,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    if runner is None:
        environment = _base_environment_with_experiment_label(args, probes, None, experiment)
        environment["status"] = "blocked_environment"
        write_json(args.out / "environment.json", environment)
        return _blocked(
            "blocked_environment",
            "No supported native, Apptainer, WSL, or Docker Verificarlo runner was found.",
        )

    status, sample_rows, reason, environment = _run_with_experiment_label(args, probes, runner, experiment)
    if status != "completed":
        environment["status"] = status
        write_json(args.out / "environment.json", environment)
        block = _blocked(status, reason, runner=runner)
        block["n"] = len([row for row in sample_rows if row.get("grid_status") == "read"])
        return block

    try:
        _, stacked, paths = stack_samples(args.out / "runs")
        metrics = mca_field_spread(stacked, _case_gamma(args.case))
    except Exception as exc:
        environment["status"] = "blocked_run"
        write_json(args.out / "environment.json", environment)
        return _blocked(
            "blocked_run",
            f"Completed samples could not be aggregated: {type(exc).__name__}: {exc}",
            runner=runner,
        )

    block: dict[str, Any] = {
        "status": "completed",
        "reason": reason,
        "n": len(paths),
        "runner": runner,
        "mca_evidence_generated": True,
    }
    block.update(metrics)
    environment["status"] = block["status"]
    write_json(args.out / "environment.json", environment)
    return block


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=None)
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--solver", choices=("hll", "hlld"), default="hll")
    parser.add_argument("--case", type=pathlib.Path, default=DEFAULT_CASE)
    parser.add_argument("--experiment", default=WEEK14_MCA_EXPERIMENT)
    parser.add_argument(
        "--jobs", type=int, default=1,
        help="Number of MCA sample containers to run concurrently (default 1).")
    parser.add_argument(
        "--sample-timeout-s", type=int, default=smoke.SAMPLE_TIMEOUT_S,
        help="Per-attempt wall-clock timeout in seconds (default 300).")
    parser.add_argument(
        "--backend-lib", default=smoke.DEFAULT_VFC_BACKEND_LIB,
        help="Interflop backend library (default libinterflop_mca.so).")
    parser.add_argument(
        "--precisions", default="53,24",
        help="Comma-separated subset of MCA precisions {53,24} (default both).")
    parser.add_argument(
        "--merge-only", action="store_true",
        help="Merge existing summary_p*.json partials without sampling.")
    return parser.parse_args(argv)


PRECISION_LABELS = {53: "p53", 24: "p24"}


def _parse_precisions(spec: str) -> list[int]:
    precisions: list[int] = []
    for token in str(spec).split(","):
        token = token.strip().lstrip("p")
        if not token:
            continue
        precision = int(token)
        if precision not in PRECISION_LABELS:
            allowed = sorted(PRECISION_LABELS)
            raise ValueError(f"unsupported precision: {precision} (allowed: {allowed})")
        if precision not in precisions:
            precisions.append(precision)
    if not precisions:
        raise ValueError("no precisions requested")
    return precisions


def resolve_output_dir(path: pathlib.Path | None, solver: str) -> pathlib.Path:
    solver = _normalise_solver(solver)
    if path is None:
        if solver == "hll":
            return DEFAULT_OUT
        return DEFAULT_OUT.parent.with_name(f"{DEFAULT_OUT.parent.name}_{solver}") / DEFAULT_OUT.name
    return path if path.is_absolute() else ROOT / path


def merge_partials(out: pathlib.Path) -> pathlib.Path:
    """Merge per-precision summaries into the combined sampler schema."""
    partials = sorted(out.glob("summary_p*.json"))
    if not partials:
        raise FileNotFoundError(f"no summary_p*.json partials found in {out}")

    merged: dict[str, Any] = {}
    mca: dict[str, Any] = {}
    for path in partials:
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in ("experiment", "case", "samples", "solver"):
            if key in data:
                if key in merged and merged[key] != data[key]:
                    raise ValueError(f"partial summaries disagree on {key}")
                merged[key] = data[key]
        mca.update(data.get("mca", {}))

    missing = set(PRECISION_LABELS.values()) - set(mca)
    if missing:
        raise ValueError(f"partial summaries are incomplete: missing {sorted(missing)}")
    merged["mca"] = mca
    target = out / "summary.json"
    write_json(target, merged)
    return target


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out = resolve_output_dir(args.out, args.solver)
    out.mkdir(parents=True, exist_ok=True)

    if args.merge_only:
        summary_path = merge_partials(out)
        print(summary_path)
        return 0

    case = args.case if args.case.is_absolute() else ROOT / args.case
    precisions = _parse_precisions(args.precisions)
    mca = {
        PRECISION_LABELS[precision]: sample_precision(
            out / PRECISION_LABELS[precision], precision=precision,
            samples=args.samples, image=args.image, solver=args.solver,
            case=case, experiment=args.experiment, jobs=args.jobs,
            sample_timeout_s=args.sample_timeout_s,
            backend_lib=args.backend_lib,
        )
        for precision in precisions
    }
    summary = {
        "experiment": args.experiment,
        "case": str(case),
        "samples": args.samples,
        "solver": args.solver,
        "mca": mca,
    }
    if set(precisions) == set(PRECISION_LABELS):
        summary_path = out / "summary.json"
    else:
        summary_path = out / f"summary_{PRECISION_LABELS[precisions[0]]}.json"
    write_json(summary_path, summary)
    print(summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
