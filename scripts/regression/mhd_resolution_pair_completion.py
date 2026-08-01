#!/usr/bin/env python3
"""Complete the corrected OT/HLLD/512 FP32--FP64 density pairing."""

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
for path in (ROOT, ROOT / "scripts", ROOT / "scripts" / "metrics", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(path))

from _mhd_harness import git_commit, sha256_file  # noqa: E402
from io_helper import read_binary  # noqa: E402
from scripts.regression import mhd_week18_resolution_ladder as ladder  # noqa: E402

EXPERIMENT = "report2-ot-hlld-512-precision-pair-completion"
DEFAULT_OUT = ROOT / "experiments" / "week18" / "resolution_ladder_pair_completion"
REFERENCE_DIR = (
    ROOT / "experiments" / "diagnostics" / "hlld_positivity_guard"
    / "runs" / "orszag-tang-hlld-double-n512-cfl0p2"
)
REFERENCE_GRID = REFERENCE_DIR / "grid.bin"
REFERENCE_METADATA = REFERENCE_DIR / "metadata.json"
REFERENCE_SUMMARY = (
    ROOT / "experiments" / "diagnostics" / "hlld_positivity_guard" / "summary.json"
)
PRIMARY_SUMMARY = ladder.DEFAULT_OUT / "summary.json"
SPEC = {
    "case": "orszag_tang_2d",
    "solver": "hlld",
    "precision": "float",
    "resolution": 512,
    "cfl": 0.2,
}
RUN_NAME = "orszag_tang_2d-hlld-float-n512-cfl0p2"
PAIR_RUN_DIR = DEFAULT_OUT / "runs" / RUN_NAME
PAIR_RUN_METADATA = PAIR_RUN_DIR / "metadata.json"
REPLAY_ATTEMPT_METADATA = PAIR_RUN_DIR / "replay_attempt_metadata.json"
ARTIFACT_REVALIDATION = PAIR_RUN_DIR / "artifact_revalidation.json"


def _json_safe(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: _json_safe(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [_json_safe(value) for value in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def validate_reference_semantics() -> dict[str, Any]:
    reference = json.loads(REFERENCE_SUMMARY.read_text(encoding="utf-8"))
    metadata = json.loads(REFERENCE_METADATA.read_text(encoding="utf-8"))
    expected_binary = reference["provenance"]["binary_sha256"]
    expected_grid = reference["provenance"]["grid_512_sha256"]
    current_double = ladder.resolve_binary(ladder.BINARIES["double"])
    checks = {
        "reference_status_success": metadata.get("status") == "success",
        "reference_completion_reported": metadata.get("completion", {}).get("reported") is True,
        "reference_final_time_matches": math.isclose(
            float(metadata.get("completion", {}).get("final_time", math.nan)), 0.5,
            rel_tol=0.0, abs_tol=1.0e-12,
        ),
        "reference_steps_match": int(metadata.get("completion", {}).get("steps", 0)) == 3277,
        "reference_grid_hash_matches": sha256_file(REFERENCE_GRID) == expected_grid,
        "current_double_binary_matches_reference": sha256_file(current_double) == expected_binary,
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "binary_sha256": expected_binary,
        "grid_sha256": expected_grid,
        "metadata": str(REFERENCE_METADATA.relative_to(ROOT)).replace("\\", "/"),
    }


def build_payload(float_row: dict[str, Any], float_grid: pathlib.Path) -> dict[str, Any]:
    reference = validate_reference_semantics()
    double_header, double_view = read_binary(REFERENCE_GRID)
    float_header, float_view = read_binary(float_grid)
    double_arr = np.array(double_view, dtype=np.float64, copy=True)
    float_arr = np.array(float_view, dtype=np.float64, copy=True)
    shape_match = double_arr.shape == float_arr.shape == (512, 512, 9)
    time_match = math.isclose(float(double_header.t), float(float_header.t), rel_tol=0.0, abs_tol=1.0e-6)
    precision_tags_match = int(double_header.precision_tag) == 8 and int(float_header.precision_tag) == 4
    norms = ladder.same_grid_density_norms(float_arr, double_arr) if shape_match else {
        "l1": math.nan, "l2": math.nan, "linf": math.nan,
    }
    checks = {
        "reference_semantics": reference["pass"],
        "float_run_completed": float_row.get("status") == "completed",
        "shape_match": shape_match,
        "time_match": time_match,
        "precision_tags_match": precision_tags_match,
        "steps_match": int(float_row.get("steps", 0)) == 3277,
        "float_state_finite_positive": bool(float_row.get("finite") and float_row.get("physical_state")),
        "metrics_finite_nonnegative": all(math.isfinite(value) and value >= 0.0 for value in norms.values()),
    }
    return {
        "schema": {"name": "hrsc.resolution-pair-completion", "version": 1},
        "experiment": EXPERIMENT,
        "git_commit": git_commit(),
        "scope": {**SPEC, "reference_precision": "double", "target_time": 0.5},
        "gate": {"pass": all(checks.values()), **checks},
        "metrics": {
            "rho_l1_fp32_vs_fp64": norms["l1"],
            "rho_l2_fp32_vs_fp64": norms["l2"],
            "rho_linf_fp32_vs_fp64": norms["linf"],
        },
        "float_run": float_row,
        "provenance": {
            "reference": reference,
            "float_grid": str(float_grid.relative_to(ROOT)).replace("\\", "/"),
            "float_grid_sha256": sha256_file(float_grid),
            "float_binary_sha256": float_row["binary_sha256"],
            "primary_resolution_summary": str(PRIMARY_SUMMARY.relative_to(ROOT)).replace("\\", "/"),
        },
        "claim_boundary": (
            "This packet completes one same-grid density-discrepancy cell for corrected "
            "OT/HLLD at 512^2. It does not establish accuracy, convergence, or solver ranking."
        ),
    }


def write_outputs(payload: dict[str, Any], out: pathlib.Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    safe = _json_safe(payload)
    (out / "summary.json").write_text(
        json.dumps(safe, indent=2, allow_nan=False) + "\n", encoding="utf-8",
    )
    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=(
            "case", "solver", "resolution", "cfl", "rho_l1_fp32_vs_fp64",
            "rho_l2_fp32_vs_fp64", "rho_linf_fp32_vs_fp64", "gate_pass",
        ))
        writer.writeheader()
        writer.writerow({
            "case": SPEC["case"], "solver": SPEC["solver"],
            "resolution": SPEC["resolution"], "cfl": SPEC["cfl"],
            **payload["metrics"], "gate_pass": payload["gate"]["pass"],
        })
    metrics = payload["metrics"]
    lines = [
        "# Corrected OT/HLLD/512 precision-pair completion", "",
        f"Gate pass: `{payload['gate']['pass']}`.", "",
        "| metric | value |", "|---|---:|",
        f"| density mean L1 | {metrics['rho_l1_fp32_vs_fp64']:.6e} |",
        f"| density mean L2 | {metrics['rho_l2_fp32_vs_fp64']:.6e} |",
        f"| density Linf | {metrics['rho_linf_fp32_vs_fp64']:.6e} |", "",
        payload["claim_boundary"], "",
    ]
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def merge_primary_summary(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("gate", {}).get("pass") is not True:
        raise ValueError("refusing to merge a failed pair-completion packet")
    summary = json.loads(PRIMARY_SUMMARY.read_text(encoding="utf-8"))
    metrics = payload["metrics"]
    float_row = payload["float_run"]
    matched = []
    for row in summary["runs"]:
        if (
            row.get("case") == SPEC["case"]
            and row.get("solver") == SPEC["solver"]
            and int(row.get("resolution", 0)) == SPEC["resolution"]
        ):
            row.update(metrics)
            matched.append(row)
            if row.get("precision") == "float":
                for key in (
                    "gamma", "steps", "divB_mean", "divB_max", "wall_time_s", "binary",
                    "binary_sha256", "run_dir", "status", "failure_category", "failure_message",
                    "output_precision_bytes", "finite", "physical_state", "rho_min", "pressure_min",
                ):
                    row[key] = float_row[key]
    if len(matched) != 2:
        raise ValueError(f"expected two primary OT/HLLD/512 rows, found {len(matched)}")
    available = sum(
        row.get("precision") == "double"
        and row.get("rho_linf_fp32_vs_fp64") is not None
        for row in summary["runs"]
    )
    summary["gate"]["precision_pair_metrics_complete"] = available == 12
    summary["gate"]["precision_pair_cells_available"] = available
    summary["gate"]["precision_pair_cells_expected"] = 12
    summary["claims"]["resolution_dependent_precision_separation"] = available == 12
    summary["claims"]["precision_separation_boundary"] = (
        "All 12 same-grid case/solver/resolution cells are available. These are cross-precision "
        "density discrepancies, not discretisation errors or accuracy measures."
    )
    summary["precision_pair_completion"] = {
        "source": str((DEFAULT_OUT / "summary.json").relative_to(ROOT)).replace("\\", "/"),
        "git_commit": payload["git_commit"],
        "gate": payload["gate"],
        "metrics": metrics,
        "provenance": payload["provenance"],
    }
    ladder._write_outputs(summary, ladder.DEFAULT_OUT)
    ladder._plot(summary, ladder.DEFAULT_OUT)
    return summary


def run(out: pathlib.Path = DEFAULT_OUT) -> dict[str, Any]:
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "matrix.json").write_text(
        json.dumps({
            "experiment": EXPERIMENT,
            "run": SPEC,
            "reference_grid": str(REFERENCE_GRID.relative_to(ROOT)).replace("\\", "/"),
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    float_row, float_arr, float_grid = ladder._run_one(SPEC, out, git_commit())
    if float_arr is None:
        raise RuntimeError("corrected fp32 endpoint did not produce a readable grid")
    payload = build_payload(float_row, float_grid)
    write_outputs(payload, out)
    merge_primary_summary(payload)
    return payload


def refresh_from_retained(out: pathlib.Path = DEFAULT_OUT) -> dict[str, Any]:
    """Rebuild derived outputs from the already gated pair without rerunning the solver."""
    out = out.resolve()
    prior = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    if prior.get("gate", {}).get("pass") is not True:
        raise ValueError("retained pair-completion summary is not gated")
    float_grid = ROOT / prior["provenance"]["float_grid"]
    if sha256_file(float_grid) != prior["provenance"]["float_grid_sha256"]:
        raise ValueError("retained fp32 grid hash does not match the gated summary")
    current_float = ladder.resolve_binary(ladder.BINARIES["float"])
    if sha256_file(current_float) != prior["provenance"]["float_binary_sha256"]:
        raise ValueError("current fp32 binary does not match the gated summary")
    payload = build_payload(prior["float_run"], float_grid)
    for name, value in prior["metrics"].items():
        if not math.isclose(float(payload["metrics"][name]), float(value), rel_tol=0.0, abs_tol=0.0):
            raise ValueError(f"retained metric changed during refresh: {name}")
    run_dir = float_grid.parent
    metadata_path = run_dir / "metadata.json"
    replay_path = run_dir / "replay_attempt_metadata.json"
    if metadata_path.is_file():
        replay = json.loads(metadata_path.read_text(encoding="utf-8"))
        if replay.get("status") == "failed":
            if not replay_path.exists():
                metadata_path.replace(replay_path)
            else:
                metadata_path.unlink()
    revalidation_path = run_dir / "artifact_revalidation.json"
    revalidation = {
        "schema": {"name": "hrsc.retained-artifact-revalidation", "version": 1},
        "status": "revalidated",
        "authority": str((out / "summary.json").relative_to(ROOT)).replace("\\", "/"),
        "original_execution_record": prior["float_run"],
        "checks": {
            "prior_gate_pass": True,
            "grid_hash_matches": True,
            "binary_hash_matches": True,
            "metrics_reproduced_exactly": True,
        },
        "grid": str(float_grid.relative_to(ROOT)).replace("\\", "/"),
        "grid_sha256": sha256_file(float_grid),
        "binary_sha256": sha256_file(current_float),
        "non_authoritative_replay_attempt": (
            str(replay_path.relative_to(ROOT)).replace("\\", "/") if replay_path.is_file() else None
        ),
        "note": (
            "The retained grid and original successful row are authoritative. A later WSL replay "
            "could not open the Windows-generated config and is retained separately as a failed, "
            "non-authoritative attempt."
        ),
    }
    revalidation_path.write_text(json.dumps(revalidation, indent=2) + "\n", encoding="utf-8")
    payload["provenance"]["artifact_revalidation"] = (
        str(revalidation_path.relative_to(ROOT)).replace("\\", "/")
    )
    payload["provenance"]["non_authoritative_replay_attempt"] = (
        str(replay_path.relative_to(ROOT)).replace("\\", "/") if replay_path.is_file() else None
    )
    write_outputs(payload, out)
    merge_primary_summary(payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--refresh-summary", action="store_true",
        help="rebuild summaries/figures from retained gated grids without rerunning the solver",
    )
    parser.add_argument(
        "--rerun", action="store_true",
        help="explicitly rerun the expensive corrected fp32 endpoint instead of revalidating it",
    )
    args = parser.parse_args(argv)
    if args.rerun:
        payload = run(args.out)
    elif (args.out / "summary.json").is_file():
        payload = refresh_from_retained(args.out)
    else:
        parser.error("no retained gated summary exists; pass --rerun to execute the solver")
    print(args.out / "summary.json")
    return 0 if payload["gate"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
