#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.io_helper import cons_to_prim, read_binary  # noqa: E402


PRIMITIVE_NAMES = ("rho", "u", "v", "p")
CONSERVED_NAMES = ("rho_cons", "rhou", "rhov", "E")


def fit_exponential_growth(
    times: Sequence[float],
    errors: Sequence[float],
    fit_window: Sequence[float] | None = None,
) -> dict[str, Any]:
    """Fit ``log(error) = lambda * t + c`` while skipping unusable errors."""
    t = np.asarray(times, dtype=np.float64)
    e = np.asarray(errors, dtype=np.float64)
    if t.shape != e.shape:
        raise ValueError(f"times/errors shape mismatch: {t.shape} vs {e.shape}")

    mask = np.isfinite(t) & np.isfinite(e) & (e > 0.0)
    window: list[float] | None = None
    if fit_window is not None:
        if len(fit_window) != 2:
            raise ValueError("fit_window must contain exactly two values")
        lo = float(fit_window[0])
        hi = float(fit_window[1])
        if hi < lo:
            raise ValueError("fit_window upper bound must be >= lower bound")
        mask &= (t >= lo) & (t <= hi)
        window = [lo, hi]

    fit_t = t[mask]
    fit_e = e[mask]
    skipped = int(t.size - fit_t.size)
    if fit_t.size < 2:
        return {
            "lambda": None,
            "slope": None,
            "intercept": None,
            "n_fit": int(fit_t.size),
            "skipped": skipped,
            "fit_window": window,
            "times_used": fit_t.tolist(),
        }

    slope, intercept = np.polyfit(fit_t, np.log(fit_e), 1)
    return {
        "lambda": float(slope),
        "slope": float(slope),
        "intercept": float(intercept),
        "n_fit": int(fit_t.size),
        "skipped": skipped,
        "fit_window": window,
        "times_used": fit_t.tolist(),
    }


def _normalise_variable(variable: str | int) -> tuple[str, int, bool]:
    if isinstance(variable, int):
        if variable < 0 or variable >= 4:
            raise ValueError(f"variable index out of range: {variable}")
        return CONSERVED_NAMES[variable], variable, False
    if isinstance(variable, str):
        value = variable.strip()
        if value.isdigit():
            return _normalise_variable(int(value))
        if value in PRIMITIVE_NAMES:
            return value, PRIMITIVE_NAMES.index(value), True
        if value in CONSERVED_NAMES:
            return value, CONSERVED_NAMES.index(value), False
    raise ValueError(
        f"Unknown variable {variable!r}; expected one of {PRIMITIVE_NAMES}, "
        f"{CONSERVED_NAMES}, or index 0..3"
    )


def _selected_variable_array(cons: np.ndarray, variable: str | int, gamma: float) -> tuple[str, np.ndarray]:
    name, idx, primitive = _normalise_variable(variable)
    if primitive and name != "rho":
        return name, cons_to_prim(cons, gamma)[..., idx]
    if primitive and name == "rho":
        return name, cons[..., 0]
    return name, cons[..., idx]


def _compatible(a: float, b: float, tolerance: float) -> bool:
    return abs(a - b) <= tolerance * max(1.0, abs(a), abs(b))


def _raise_header_mismatch(
    field: str,
    path_a: str | Path,
    value_a: Any,
    path_b: str | Path,
    value_b: Any,
) -> None:
    raise ValueError(f"{field} mismatch: {path_a} has {value_a}, {path_b} has {value_b}")


def compute_l1_linf_pair(
    path_a: str | Path,
    path_b: str | Path,
    variable: str | int = "rho",
    gamma: float = 1.4,
    time_tolerance: float = 1e-12,
    spatial_tolerance: float = 1e-12,
) -> dict[str, Any]:
    """Compute mean absolute and max absolute drift for one HRSC binary pair."""
    header_a, data_a = read_binary(path_a)
    header_b, data_b = read_binary(path_b)
    shape_a = (header_a.nx, header_a.ny, header_a.nvars)
    shape_b = (header_b.nx, header_b.ny, header_b.nvars)
    if shape_a != shape_b:
        _raise_header_mismatch("grid shape", path_a, shape_a, path_b, shape_b)
    if not _compatible(header_a.dx, header_b.dx, spatial_tolerance):
        _raise_header_mismatch("dx", path_a, header_a.dx, path_b, header_b.dx)
    if not _compatible(header_a.dy, header_b.dy, spatial_tolerance):
        _raise_header_mismatch("dy", path_a, header_a.dy, path_b, header_b.dy)
    if not _compatible(header_a.t, header_b.t, time_tolerance):
        _raise_header_mismatch("time", path_a, header_a.t, path_b, header_b.t)

    name_a, arr_a = _selected_variable_array(data_a.astype(np.float64), variable, gamma)
    name_b, arr_b = _selected_variable_array(data_b.astype(np.float64), variable, gamma)
    if name_a != name_b:
        raise AssertionError("internal variable normalisation mismatch")
    diff = np.abs(arr_a - arr_b)
    finite = np.isfinite(diff)
    if not finite.any():
        l1 = math.nan
        linf = math.nan
    else:
        l1 = float(np.mean(diff[finite]))
        linf = float(np.max(diff[finite]))
    return {
        "path_a": str(path_a),
        "path_b": str(path_b),
        "time": float(0.5 * (header_a.t + header_b.t)),
        "time_a": float(header_a.t),
        "time_b": float(header_b.t),
        "variable": name_a,
        "l1": l1,
        "linf": linf,
        "n_cells": int(diff.size),
        "n_finite": int(np.count_nonzero(finite)),
    }


def _read_pairs(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _coerce_paths(values: Iterable[str | Path]) -> list[Path]:
    return [Path(value) for value in values]


def _pair_entries(spec: dict[str, Any]) -> list[dict[str, Any]]:
    entries = spec.get("pairs", spec.get("drift_pairs"))
    if not isinstance(entries, list):
        raise ValueError("pairs spec must contain a 'pairs' or 'drift_pairs' list")
    return [dict(entry) for entry in entries]


def analyse_pair(
    entry: dict[str, Any],
    fit_window: Sequence[float] | None = None,
    time_tolerance: float = 1e-12,
    spatial_tolerance: float = 1e-12,
) -> dict[str, Any]:
    variable = entry.get("variable", "rho")
    paths_a = _coerce_paths(entry.get("a", []))
    paths_b = _coerce_paths(entry.get("b", []))
    if len(paths_a) != len(paths_b):
        raise ValueError(f"pair {entry.get('pair', '<unnamed>')} has unequal a/b series lengths")
    if not paths_a:
        raise ValueError(f"pair {entry.get('pair', '<unnamed>')} contains no binary paths")

    rows = [
        compute_l1_linf_pair(
            path_a,
            path_b,
            variable=variable,
            gamma=float(entry.get("gamma", 1.4)),
            time_tolerance=float(entry.get("time_tolerance", time_tolerance)),
            spatial_tolerance=float(entry.get("spatial_tolerance", spatial_tolerance)),
        )
        for path_a, path_b in zip(paths_a, paths_b)
    ]
    rows.sort(key=lambda row: row["time"])
    times = [row["time"] for row in rows]
    l1 = [row["l1"] for row in rows]
    linf = [row["linf"] for row in rows]
    fit_l1 = fit_exponential_growth(times, l1, fit_window=fit_window)
    fit_linf = fit_exponential_growth(times, linf, fit_window=fit_window)
    return {
        "case": entry.get("case", ""),
        "pair": entry.get("pair", entry.get("name", "")),
        "variable": _normalise_variable(variable)[0],
        "times": times,
        "l1": l1,
        "linf": linf,
        "lambda_l1": fit_l1["lambda"],
        "lambda_linf": fit_linf["lambda"],
        "fit_l1": fit_l1,
        "fit_linf": fit_linf,
        "fit_window": fit_l1["fit_window"],
        "notes": list(entry.get("notes", [])),
        "samples": rows,
    }


def _write_outputs(records: list[dict[str, Any]], output_prefix: Path) -> None:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_prefix.with_suffix(".json")
    csv_path = output_prefix.with_suffix(".csv")
    md_path = output_prefix.with_suffix(".md")

    json_path.write_text(json.dumps({"pairs": records}, indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["case", "pair", "variable", "time", "l1", "linf", "lambda_l1", "lambda_linf"],
        )
        writer.writeheader()
        for record in records:
            for t, l1, linf in zip(record["times"], record["l1"], record["linf"]):
                writer.writerow(
                    {
                        "case": record["case"],
                        "pair": record["pair"],
                        "variable": record["variable"],
                        "time": t,
                        "l1": l1,
                        "linf": linf,
                        "lambda_l1": record["lambda_l1"],
                        "lambda_linf": record["lambda_linf"],
                    }
                )

    lines = [
        "# Drift Time-Series Summary",
        "",
        "| case | pair | variable | n | final L1 | final Linf | lambda L1 | notes |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for record in records:
        n = len(record["times"])
        final_l1 = record["l1"][-1] if n else math.nan
        final_linf = record["linf"][-1] if n else math.nan
        lambda_l1 = record["lambda_l1"]
        lambda_text = "n/a" if lambda_l1 is None else f"{lambda_l1:.6g}"
        notes = "; ".join(str(note) for note in record["notes"])
        lines.append(
            f"| {record['case']} | {record['pair']} | {record['variable']} | {n} | "
            f"{final_l1:.6e} | {final_linf:.6e} | {lambda_text} | {notes} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_fit_window(value: str | None) -> list[float] | None:
    if not value:
        return None
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("--fit-window must be 't_min,t_max'")
    return [float(parts[0]), float(parts[1])]


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute HRSC drift time-series metrics.")
    parser.add_argument("--pairs", type=Path, help="JSON file with paired binary series")
    parser.add_argument("--matrix", type=Path, help="run_matrix JSON containing drift_pairs")
    parser.add_argument("--output", type=Path, required=True, help="Output prefix for summary.{json,csv,md}")
    parser.add_argument("--fit-window", type=_parse_fit_window, default=None, help="Fit window as t_min,t_max")
    parser.add_argument(
        "--time-tolerance",
        type=float,
        default=1e-12,
        help="Relative/absolute tolerance for paired binary header times",
    )
    parser.add_argument("--case", default="", help="Case label for explicit --a/--b mode")
    parser.add_argument("--pair", default="explicit_pair", help="Pair label for explicit --a/--b mode")
    parser.add_argument("--variable", default="rho", help="Variable name or conserved index")
    parser.add_argument("--a", nargs="*", default=None, help="First binary series in explicit mode")
    parser.add_argument("--b", nargs="*", default=None, help="Second binary series in explicit mode")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.pairs or args.matrix:
        entries = _pair_entries(_read_pairs(args.pairs or args.matrix))
    elif args.a is not None and args.b is not None:
        entries = [
            {
                "case": args.case,
                "pair": args.pair,
                "variable": args.variable,
                "a": args.a,
                "b": args.b,
            }
        ]
    else:
        raise SystemExit("Provide --pairs or both --a and --b")

    records = [
        analyse_pair(entry, fit_window=args.fit_window, time_tolerance=args.time_tolerance)
        for entry in entries
    ]
    _write_outputs(records, args.output)


if __name__ == "__main__":
    main()
