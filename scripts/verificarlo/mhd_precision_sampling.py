#!/usr/bin/env python3
"""Week-14 field-specific MHD Verificarlo MCA sampler.

This harness wrapper reuses the Week-13 Verificarlo smoke runner machinery and
turns its sample grids into the schema-complete MCA blocks consumed by the
Week-14 precision pilot. Environments without a supported runner produce a
blocked MCA block rather than failing the experiment.
"""
from __future__ import annotations

import argparse
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


def _sample_args(out_dir: pathlib.Path, precision: int, samples: int, image: str) -> argparse.Namespace:
    return argparse.Namespace(
        case=DEFAULT_CASE,
        out=pathlib.Path(out_dir),
        samples=int(samples),
        precision=int(precision),
        image=image,
        probe_only=False,
    )


def _blocked(status: str, reason: str, *, runner: str | None = None) -> dict[str, Any]:
    block = blocked_mca_block(status, reason)
    block["runner"] = runner
    return block


def _base_environment_with_experiment_label(
    args: argparse.Namespace,
    probes: list[dict[str, Any]],
    runner: str | None,
) -> dict[str, Any]:
    previous = smoke.EXPERIMENT
    smoke.EXPERIMENT = WEEK14_MCA_EXPERIMENT
    try:
        return base_environment(args, probes, runner)
    finally:
        smoke.EXPERIMENT = previous


def _run_with_experiment_label(
    args: argparse.Namespace,
    probes: list[dict[str, Any]],
    runner: str,
) -> tuple[str, list[dict[str, Any]], str, dict[str, Any]]:
    previous = smoke.EXPERIMENT
    smoke.EXPERIMENT = WEEK14_MCA_EXPERIMENT
    try:
        status, sample_rows, reason = run_samples(args, probes, runner)
        environment = base_environment(args, probes, runner)
        return status, sample_rows, reason, environment
    finally:
        smoke.EXPERIMENT = previous


def sample_precision(
    out_dir: pathlib.Path,
    precision: int,
    samples: int = DEFAULT_SAMPLES,
    image: str = DEFAULT_IMAGE,
) -> dict[str, Any]:
    """Run one MCA precision block and return schema-complete field metrics."""
    probes = probe_runners(image)
    runner = choose_runner(probes)
    args = _sample_args(pathlib.Path(out_dir), precision, samples, image)
    args.out.mkdir(parents=True, exist_ok=True)
    if runner is None:
        environment = _base_environment_with_experiment_label(args, probes, None)
        environment["status"] = "blocked_environment"
        write_json(args.out / "environment.json", environment)
        return _blocked(
            "blocked_environment",
            "No supported native, WSL, or Docker Verificarlo runner was found.",
        )

    status, sample_rows, reason, environment = _run_with_experiment_label(args, probes, runner)
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
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    mca = {
        "p53": sample_precision(out / "p53", precision=53, samples=args.samples, image=args.image),
        "p24": sample_precision(out / "p24", precision=24, samples=args.samples, image=args.image),
    }
    summary = {"experiment": EXPERIMENT, "samples": args.samples, "mca": mca}
    write_json(out / "summary.json", summary)
    print(out / "summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
