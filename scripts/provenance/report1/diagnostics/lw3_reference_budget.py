#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "metrics"))

from io_helper import cons_to_prim, read_binary  # noqa: E402
from downsample_2d import downsample_conserved, primitive_error_norms  # noqa: E402


VAR_NAMES = ("rho", "u", "v", "p")

DEFAULT_PATHS = {
    "double_200": Path("experiments/week4/float_regression/2d/double_200.bin"),
    "float_200": Path("experiments/week4/float_regression/2d/float_200.bin"),
    "double_400": Path("experiments/week4/float_regression/2d/double_400.bin"),
    "float_400": Path("experiments/week4/float_regression/2d/float_400.bin"),
    "double_800": Path("experiments/week4/float_regression/2d/reference_800.bin"),
    "double_1600": Path(
        "experiments/week7/reference_1600/runs/lw3-n1600-gpu-double-strict/reference_1600.bin"
    ),
}


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def load_prim(path: Path, gamma: float) -> tuple[Any, np.ndarray]:
    header, cons = read_binary(path)
    return header, cons_to_prim(cons.astype(np.float64), gamma)


def compare_primitive(left: np.ndarray, right: np.ndarray) -> dict[str, dict[str, float]]:
    return primitive_error_norms(left, right)


def compare_to_finer(coarse_path: Path, fine_path: Path, gamma: float) -> dict[str, Any]:
    coarse_h, coarse_cons = read_binary(coarse_path)
    fine_h, fine_cons = read_binary(fine_path)
    fine_down_cons = downsample_conserved(
        fine_cons.astype(np.float64), coarse_h.nx, coarse_h.ny
    )
    coarse_prim = cons_to_prim(coarse_cons.astype(np.float64), gamma)
    fine_down_prim = cons_to_prim(fine_down_cons, gamma)
    return {
        "coarse_file": rel(coarse_path),
        "fine_file": rel(fine_path),
        "coarse_shape": [coarse_h.nx, coarse_h.ny],
        "fine_shape": [fine_h.nx, fine_h.ny],
        "metrics": compare_primitive(coarse_prim, fine_down_prim),
    }


def compare_same_grid(left_path: Path, right_path: Path, gamma: float) -> dict[str, Any]:
    left_h, left_prim = load_prim(left_path, gamma)
    right_h, right_prim = load_prim(right_path, gamma)
    if left_prim.shape != right_prim.shape:
        raise ValueError(f"Shape mismatch: {left_path} vs {right_path}")
    return {
        "left_file": rel(left_path),
        "right_file": rel(right_path),
        "shape": [left_h.nx, left_h.ny],
        "metrics": compare_primitive(left_prim, right_prim),
    }


def observed_order(e_coarse: float, e_fine: float) -> float:
    if e_coarse <= 0.0 or e_fine <= 0.0:
        return float("nan")
    return math.log(e_coarse / e_fine, 2.0)


def safe_ratio(num: float, den: float) -> float:
    return float("nan") if den == 0.0 else num / den


def fmt(x: float) -> str:
    if math.isnan(x):
        return "nan"
    return f"{x:.6e}"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def markdown_summary(result: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# LW3 Reference Budget")
    lines.append("")
    lines.append(
        "This diagnostic reuses existing LW3 binary grids and does not rerun or modify the solver."
    )
    lines.append(
        "Conserved variables from the finer fp64 grid are block-averaged to the coarser finite-volume grid before primitive-variable norms are computed."
    )
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    for key, value in result["inputs"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")

    lines.append("## Adjacent fp64 Reference Hierarchy")
    lines.append("")
    lines.append("| variable | 200 vs 400 | 400 vs 800 | 800 vs 1600 | p(200->800) | p(400->1600) |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    hierarchy = result["hierarchy"]
    orders = result["orders"]
    for var in VAR_NAMES:
        lines.append(
            f"| {var} | {fmt(hierarchy['200_vs_400']['metrics'][var]['L1'])} | "
            f"{fmt(hierarchy['400_vs_800']['metrics'][var]['L1'])} | "
            f"{fmt(hierarchy['800_vs_1600']['metrics'][var]['L1'])} | "
            f"{orders['200_to_800'][var]:.3f} | {orders['400_to_1600'][var]:.3f} |"
        )
    lines.append("")

    lines.append("## Precision Perturbation Budget")
    lines.append("")
    lines.append(
        "| grid | variable | fp32-fp64 L1 | ratio to same-grid 1600 reference error | ratio to adjacent fp64 hierarchy error |"
    )
    lines.append("|---:|---|---:|---:|---:|")
    for row in result["precision_budget_rows"]:
        lines.append(
            f"| {row['grid']} | {row['variable']} | {fmt(row['precision_l1'])} | "
            f"{fmt(row['ratio_to_1600_error'])} | {fmt(row['ratio_to_adjacent_hierarchy'])} |"
        )
    lines.append("")

    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "- The adjacent fp64 hierarchy still converges slowly, so the 1600^2 field remains a numerical reference rather than an exact solution."
    )
    lines.append(
        "- The added budget directly tests the report claim: same-resolution fp32-fp64 differences are compared with discretisation-dominated grid-hierarchy differences."
    )
    lines.append(
        "- Ratios much smaller than one support a precision-perturbation claim, but do not remove the need to state the reference limitation."
    )
    lines.append("")
    return "\n".join(lines)


def build_result(paths: dict[str, Path], gamma: float) -> dict[str, Any]:
    for label, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"Missing {label}: {path}")

    hierarchy = {
        "200_vs_400": compare_to_finer(paths["double_200"], paths["double_400"], gamma),
        "400_vs_800": compare_to_finer(paths["double_400"], paths["double_800"], gamma),
        "800_vs_1600": compare_to_finer(paths["double_800"], paths["double_1600"], gamma),
    }
    candidate_to_1600 = {
        "double_200": compare_to_finer(paths["double_200"], paths["double_1600"], gamma),
        "float_200": compare_to_finer(paths["float_200"], paths["double_1600"], gamma),
        "double_400": compare_to_finer(paths["double_400"], paths["double_1600"], gamma),
        "float_400": compare_to_finer(paths["float_400"], paths["double_1600"], gamma),
    }
    precision = {
        "200": compare_same_grid(paths["float_200"], paths["double_200"], gamma),
        "400": compare_same_grid(paths["float_400"], paths["double_400"], gamma),
    }

    orders: dict[str, dict[str, float]] = {"200_to_800": {}, "400_to_1600": {}}
    for var in VAR_NAMES:
        orders["200_to_800"][var] = observed_order(
            hierarchy["200_vs_400"]["metrics"][var]["L1"],
            hierarchy["400_vs_800"]["metrics"][var]["L1"],
        )
        orders["400_to_1600"][var] = observed_order(
            hierarchy["400_vs_800"]["metrics"][var]["L1"],
            hierarchy["800_vs_1600"]["metrics"][var]["L1"],
        )

    precision_budget_rows: list[dict[str, Any]] = []
    for grid, adjacent_key in (("200", "200_vs_400"), ("400", "400_vs_800")):
        for var in VAR_NAMES:
            precision_l1 = precision[grid]["metrics"][var]["L1"]
            ref_l1 = candidate_to_1600[f"double_{grid}"]["metrics"][var]["L1"]
            adjacent_l1 = hierarchy[adjacent_key]["metrics"][var]["L1"]
            precision_budget_rows.append(
                {
                    "grid": int(grid),
                    "variable": var,
                    "precision_l1": precision_l1,
                    "same_grid_1600_reference_l1": ref_l1,
                    "adjacent_hierarchy_l1": adjacent_l1,
                    "ratio_to_1600_error": safe_ratio(precision_l1, ref_l1),
                    "ratio_to_adjacent_hierarchy": safe_ratio(precision_l1, adjacent_l1),
                }
            )

    return {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": git_head(),
        "gamma": gamma,
        "inputs": {key: rel(path) for key, path in paths.items()},
        "hierarchy": hierarchy,
        "candidate_to_1600": candidate_to_1600,
        "precision": precision,
        "orders": orders,
        "precision_budget_rows": precision_budget_rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LW3 reference-hierarchy and precision-perturbation budget."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("experiments/report1_lw3_reference_budget"),
        help="Output experiment directory.",
    )
    parser.add_argument("--gamma", type=float, default=1.4)
    for label, default in DEFAULT_PATHS.items():
        parser.add_argument(f"--{label.replace('_', '-')}", type=Path, default=default)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = {
        label: getattr(args, label).resolve()
        for label in DEFAULT_PATHS
    }
    result = build_result(paths, args.gamma)

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "summary.md").write_text(markdown_summary(result), encoding="utf-8")
    write_csv(out_dir / "precision_budget.csv", result["precision_budget_rows"])

    metadata = {
        "created_utc": result["created_utc"],
        "git_head": result["git_head"],
        "command": " ".join(sys.argv),
        "outputs": [
            rel(out_dir / "summary.md"),
            rel(out_dir / "summary.json"),
            rel(out_dir / "precision_budget.csv"),
        ],
    }
    (out_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Wrote {out_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
