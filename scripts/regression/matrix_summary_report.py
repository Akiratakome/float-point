#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

_SCRIPTS_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _SCRIPTS_ROOT.parent
sys.path.insert(0, str(_SCRIPTS_ROOT))
sys.path.insert(0, str(_SCRIPTS_ROOT / "metrics"))

from io_helper import cons_to_prim, read_binary  # noqa: E402
from harness.metadata import require_successful_metadata  # noqa: E402


VAR_NAMES = ("rho", "rhou", "rhov", "E")
# Float and double binaries generated from the same cfg can store dx/dy with
# different precision tags. Keep this tight enough to catch mismatched grids
# while allowing representation roundoff between f32 and f64 headers.
HEADER_RTOL = 1.0e-6
HEADER_ATOL = 1.0e-12
PAIR_COLUMNS = [
    "row_type",
    "name",
    "precision",
    "build",
    "nx",
    "ny",
    "t_end",
    "total_s",
    "integral_min",
    "integral_max",
    "pair_label",
    "left",
    "right",
    "l1",
    "linf",
    "ulp_max",
    "philip_ratio",
]


@dataclass(frozen=True)
class RunData:
    name: str
    metadata: dict[str, Any]
    metadata_path: Path
    header: Any | None
    grid: np.ndarray | None

    @property
    def precision(self) -> str | None:
        value = self.metadata.get("precision")
        return str(value) if value not in (None, "") else None

    @property
    def build(self) -> str | None:
        value = self.metadata.get("build")
        return str(value) if value not in (None, "") else None


def _summary_path(prefix: Path, suffix: str) -> Path:
    if prefix.suffix:
        return prefix.with_suffix(suffix)
    return Path(str(prefix) + suffix)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _path_has_suffix(path: Path, suffix: Path) -> bool:
    path_parts = tuple(part.lower() for part in path.parts)
    suffix_parts = tuple(part.lower() for part in suffix.parts)
    return bool(suffix_parts) and len(path_parts) >= len(suffix_parts) and path_parts[-len(suffix_parts):] == suffix_parts


def _suffix_from_anchor(path: Path, anchor: str) -> Path | None:
    parts = path.parts
    lowered = [part.lower() for part in parts]
    if anchor.lower() not in lowered:
        return None
    idx = lowered.index(anchor.lower())
    return Path(*parts[idx:])


def _existing_candidate(candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _resolve_recorded_existing(
    path_text: str | None,
    *,
    output_root: Path,
    matrix_parent: Path,
    local_bases: list[Path] | None = None,
) -> Path | None:
    if not path_text:
        return None
    path = Path(path_text)
    if path.is_absolute():
        return path if path.exists() else None
    candidates = [Path.cwd() / path, _REPO_ROOT / path]
    candidates.extend([base / path for base in (local_bases or [])])
    candidates.extend([output_root / path, matrix_parent / path])
    suffix = _suffix_from_anchor(path, "runs")
    if suffix is not None:
        candidates.extend([output_root / suffix, matrix_parent / suffix])
    return _existing_candidate(candidates)


def _resolve_recorded_path(
    path_text: str | None,
    *,
    output_root: Path,
    matrix_parent: Path,
    local_bases: list[Path] | None = None,
) -> Path | None:
    """Resolve paths written by run_matrix without assuming today's CWD.

    Order is deliberate: first honor the recorded relative path from the
    current process and repo root, then try local run-dir context, then the
    resolved output root, then the matrix directory. If a canonical path like
    ``exp/out/runs/a/grid.bin`` is being read from ``exp/out/matrix_summary``,
    the final ``runs/...`` suffix fallback avoids ``exp/out/exp/out``.
    """
    if not path_text:
        return None
    path = Path(path_text)
    if path.is_absolute():
        return path
    existing = _resolve_recorded_existing(
        path_text,
        output_root=output_root,
        matrix_parent=matrix_parent,
        local_bases=local_bases,
    )
    if existing is not None:
        return existing
    suffix = _suffix_from_anchor(path, "runs")
    if suffix is not None:
        return output_root / suffix
    repo_relative = _REPO_ROOT / path
    if _path_has_suffix(output_root, path.parent):
        return output_root / path.name
    if repo_relative.parent.exists():
        return repo_relative
    return output_root / path


def _matrix_relative_path(path: Path) -> Path:
    return path if path.is_absolute() else (Path.cwd() / path).resolve()


def _output_root_from_matrix(matrix: dict[str, Any], matrix_path: Path) -> Path:
    raw = Path(str(matrix.get("output_root", matrix_path.parent)))
    if raw.is_absolute():
        return raw
    candidates = [Path.cwd() / raw, _REPO_ROOT / raw]
    existing = _existing_candidate(candidates)
    if existing is not None:
        return existing
    if _path_has_suffix(matrix_path.parent, raw):
        return matrix_path.parent
    return matrix_path.parent / raw


def _metadata_path_for_run(run: dict[str, Any], matrix_path: Path, output_root: Path) -> Path:
    explicit = _resolve_recorded_path(
        str(run.get("metadata")) if run.get("metadata") else None,
        output_root=output_root,
        matrix_parent=matrix_path.parent,
    )
    if explicit is not None:
        return explicit

    for key in ("run_config", "raw_output"):
        resolved = _resolve_recorded_existing(
            str(run.get(key)) if run.get(key) else None,
            output_root=output_root,
            matrix_parent=matrix_path.parent,
        )
        if resolved is not None:
            return resolved.parent / "metadata.json"

    name = run.get("name")
    if not name:
        raise ValueError(f"Run entry lacks name and metadata path: {run}")
    return output_root / "runs" / str(name) / "metadata.json"


def _load_runs(matrix_path: Path) -> list[RunData]:
    matrix_path = _matrix_relative_path(matrix_path)
    matrix = _load_json(matrix_path)
    output_root = _output_root_from_matrix(matrix, matrix_path)

    out: list[RunData] = []
    for run in matrix.get("runs", []):
        if not isinstance(run, dict):
            raise ValueError("matrix_summary runs must be objects")
        metadata_path = _metadata_path_for_run(run, matrix_path, output_root)
        metadata = require_successful_metadata(_load_json(metadata_path))
        name = str(metadata.get("name") or run.get("name") or metadata_path.parent.name)
        raw_output_value = (metadata.get("artifacts") or {}).get("primary_output")
        if not raw_output_value:
            raw_output_value = metadata.get("raw_output") or metadata.get("output_binary")
        raw_output = _resolve_recorded_path(
            str(raw_output_value) if raw_output_value else None,
            output_root=output_root,
            matrix_parent=matrix_path.parent,
            local_bases=[metadata_path.parent],
        )
        header = None
        grid = None
        if raw_output is not None:
            header, grid = read_binary(raw_output)
        out.append(RunData(name=name, metadata=metadata, metadata_path=metadata_path, header=header, grid=grid))
    if not out:
        raise ValueError(f"No runs found in {matrix_path}")
    return out


def _run_scalars(run: RunData) -> dict[str, Any]:
    artifacts = run.metadata.get("artifacts") or {}
    timing = run.metadata.get("timing") or {}
    row: dict[str, Any] = {
        "name": run.name,
        "precision": run.precision,
        "build": run.build,
        "source_config": run.metadata.get("source_config"),
        "metadata": str(run.metadata_path),
        "raw_output": artifacts.get("primary_output")
        or run.metadata.get("raw_output")
        or run.metadata.get("output_binary"),
        "total_s": timing.get("elapsed_wall_s")
        if timing.get("elapsed_wall_s") is not None
        else run.metadata.get("elapsed_wall_s")
        if run.metadata.get("elapsed_wall_s") is not None
        else timing.get("total_s"),
        "nx": None,
        "ny": None,
        "t_end": None,
        "integrals": {},
        "integral_min": None,
        "integral_max": None,
    }
    if run.header is None or run.grid is None:
        return row

    row["nx"] = int(run.header.nx)
    row["ny"] = int(run.header.ny)
    row["t_end"] = float(run.header.t)
    cell_volume = float(run.header.dx) * (float(run.header.dy) if int(run.header.ny) > 1 else 1.0)
    grid64 = run.grid.astype(np.float64, copy=False)
    integrals = {
        VAR_NAMES[idx] if idx < len(VAR_NAMES) else f"var{idx}": float(np.sum(grid64[..., idx]) * cell_volume)
        for idx in range(grid64.shape[-1])
    }
    row["integrals"] = integrals
    if integrals:
        values = list(integrals.values())
        row["integral_min"] = float(min(values))
        row["integral_max"] = float(max(values))
    return row


def _clean_key(value: str) -> str:
    value = re.sub(r"[-_]+", "-", value)
    return value.strip("-. _")


def _strip_token(name: str, token: str | None) -> str:
    if not token:
        return name
    parts = [part for part in re.split(r"([-_])", name) if part]
    rebuilt: list[str] = []
    for part in parts:
        if part in ("-", "_"):
            rebuilt.append(part)
        elif part.lower() != token.lower():
            rebuilt.append(part)
    stripped = "".join(rebuilt)
    if stripped == name:
        stripped = name.replace(token, "")
    return _clean_key(stripped)


def _pair_key(run: RunData, pair_by: str) -> str:
    if pair_by == "precision":
        return _strip_token(run.name, run.precision)
    if pair_by == "build":
        return _strip_token(run.name, run.build)
    raise ValueError(f"Unsupported pair_by={pair_by}")


def _implicit_pairs(runs: list[RunData], pair_by: str) -> list[tuple[str, RunData, RunData]]:
    if pair_by == "none":
        return []
    groups: dict[str, list[RunData]] = {}
    for run in runs:
        groups.setdefault(_pair_key(run, pair_by), []).append(run)

    pairs: list[tuple[str, RunData, RunData]] = []
    for label, members in groups.items():
        if len(members) < 2:
            continue
        if len(members) == 2:
            pairs.append((label, members[0], members[1]))
            continue
        for left, right in combinations(members, 2):
            pairs.append((label, left, right))
    return pairs


def _explicit_pairs(
    runs_by_name: dict[str, RunData],
    pair_args: list[list[str]] | None,
    labels: list[str] | None,
) -> list[tuple[str, RunData, RunData]]:
    if not pair_args:
        return []
    labels = labels or []
    if len(labels) == 1 and len(pair_args) > 1:
        labels = labels * len(pair_args)
    elif len(pair_args) != len(labels):
        raise ValueError("Provide either one --pair-label for all --pair entries or one label per pair")
    out: list[tuple[str, RunData, RunData]] = []
    for (left_name, right_name), label in zip(pair_args, labels):
        try:
            out.append((label, runs_by_name[left_name], runs_by_name[right_name]))
        except KeyError as exc:
            raise ValueError(f"Unknown run in explicit --pair: {exc.args[0]}") from exc
    return out


def _validate_header_compatible(
    left_header: Any,
    right_header: Any,
    context: str,
    *,
    shape_message: str,
    header_message: str,
) -> None:
    if (left_header.nx, left_header.ny, left_header.nvars) != (
        right_header.nx,
        right_header.ny,
        right_header.nvars,
    ):
        raise ValueError(
            f"{shape_message} for {context}: "
            f"{left_header.nx}x{left_header.ny}x{left_header.nvars} vs "
            f"{right_header.nx}x{right_header.ny}x{right_header.nvars}"
        )
    for field in ("t", "dx", "dy"):
        left_value = float(getattr(left_header, field))
        right_value = float(getattr(right_header, field))
        if not np.isclose(left_value, right_value, rtol=HEADER_RTOL, atol=HEADER_ATOL):
            raise ValueError(
                f"{header_message} for {context}: {field} differs "
                f"({left_value} vs {right_value})"
            )


def _validate_pair(left: RunData, right: RunData) -> None:
    if left.header is None or right.header is None or left.grid is None or right.grid is None:
        raise ValueError(f"Pair {left.name}/{right.name} requires raw_output binaries")
    _validate_header_compatible(
        left.header,
        right.header,
        f"pair {left.name}/{right.name}",
        shape_message="Grid shape mismatch",
        header_message="Header mismatch",
    )


def _safe_ratio(num: float, den: float) -> float | None:
    if den == 0.0:
        return None
    return num / den


def _ulp_max(left: RunData, right: RunData, abs_diff: np.ndarray) -> float | None:
    if left.precision != right.precision or left.header.precision_tag != right.header.precision_tag:
        return None
    dtype = np.dtype("<f8") if int(left.header.precision_tag) == 8 else np.dtype("<f4")
    scale = float(np.max(np.abs(left.grid.astype(np.float64, copy=False)))) if left.grid.size else 0.0
    den = float(np.finfo(dtype).eps) * scale
    return _safe_ratio(float(np.max(abs_diff)) if abs_diff.size else 0.0, den)


def _reference_l1(left: RunData, reference: str | Path | None) -> float | None:
    if reference is None or str(reference) == "exact":
        return None
    ref_header, ref_grid = read_binary(reference)
    _validate_header_compatible(
        left.header,
        ref_header,
        f"reference {reference} vs {left.name}",
        shape_message="Reference shape mismatch",
        header_message="Reference header mismatch",
    )
    return float(np.mean(np.abs(left.grid.astype(np.float64, copy=False) - ref_grid.astype(np.float64, copy=False))))


def _pair_row(
    label: str,
    left: RunData,
    right: RunData,
    gamma: float,
    reference: str | Path | None,
    with_phase: bool,
) -> dict[str, Any]:
    _validate_pair(left, right)
    left64 = left.grid.astype(np.float64, copy=False)
    right64 = right.grid.astype(np.float64, copy=False)
    abs_diff = np.abs(left64 - right64)
    l1 = float(np.mean(abs_diff)) if abs_diff.size else 0.0
    linf = float(np.max(abs_diff)) if abs_diff.size else 0.0
    ref_l1 = _reference_l1(left, reference)
    row: dict[str, Any] = {
        "pair_label": label,
        "left": left.name,
        "right": right.name,
        "left_precision": left.precision,
        "right_precision": right.precision,
        "l1": l1,
        "linf": linf,
        "ulp_max": _ulp_max(left, right, abs_diff),
        "reference_l1": ref_l1,
        "philip_ratio": _safe_ratio(l1, ref_l1) if ref_l1 is not None else None,
    }
    if with_phase and int(left.header.ny) > 1 and int(right.header.ny) > 1:
        from phase_error_metrics import compute_phase_metrics_from_primitive

        left_prim = cons_to_prim(left64, gamma)
        right_prim = cons_to_prim(right64, gamma)
        row["phase_metrics"] = compute_phase_metrics_from_primitive(
            left_prim,
            right_prim,
            float(left.header.dx),
            float(left.header.dy),
            smooth_sigma=0.5,
            allow_ssim_fallback=True,
        )
    return row


def _format_value(value: Any) -> Any:
    return "n/a" if value is None else value


def _write_outputs(prefix: Path, summary: dict[str, Any]) -> None:
    csv_path = _summary_path(prefix, ".csv")
    json_path = _summary_path(prefix, ".json")
    md_path = _summary_path(prefix, ".md")
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PAIR_COLUMNS)
        writer.writeheader()
        for run in summary["runs"]:
            writer.writerow(
                {
                    "row_type": "run",
                    "name": run["name"],
                    "precision": run["precision"],
                    "build": run["build"],
                    "nx": run["nx"],
                    "ny": run["ny"],
                    "t_end": run["t_end"],
                    "total_s": run["total_s"],
                    "integral_min": run["integral_min"],
                    "integral_max": run["integral_max"],
                    "pair_label": "",
                    "left": "",
                    "right": "",
                    "l1": "",
                    "linf": "",
                    "ulp_max": "",
                    "philip_ratio": "",
                }
            )
        for pair in summary["pairs"]:
            row = {key: _format_value(pair.get(key)) for key in PAIR_COLUMNS}
            row["row_type"] = "pair"
            writer.writerow(row)

    lines = [
        "# Matrix Summary Report",
        "",
        "## Runs",
        "",
        "| name | precision | build | nx | ny | t_end | total_s | integral_min | integral_max |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for run in summary["runs"]:
        lines.append(
            f"| {run['name']} | {_format_value(run['precision'])} | {_format_value(run['build'])} | "
            f"{_format_value(run['nx'])} | {_format_value(run['ny'])} | {_format_value(run['t_end'])} | "
            f"{_format_value(run['total_s'])} | {_format_value(run['integral_min'])} | "
            f"{_format_value(run['integral_max'])} |"
        )
    lines.extend(
        [
            "",
            "## Pairs",
            "",
            "| pair_label | left | right | l1 | linf | ulp_max | philip_ratio |",
            "|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for pair in summary["pairs"]:
        lines.append(
            f"| {pair['pair_label']} | {pair['left']} | {pair['right']} | "
            f"{pair['l1']:.6e} | {pair['linf']:.6e} | {_format_value(pair['ulp_max'])} | "
            f"{_format_value(pair['philip_ratio'])} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary["outputs"] = {"csv": str(csv_path), "json": str(json_path), "markdown": str(md_path)}
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    matrix_summary = _matrix_relative_path(args.matrix_summary)
    matrix = _load_json(matrix_summary)
    output_root = _output_root_from_matrix(matrix, matrix_summary)
    runs = _load_runs(matrix_summary)
    if args.filter_name_contains:
        needles = [part.strip() for part in args.filter_name_contains.split(",") if part.strip()]
        runs = [run for run in runs if any(needle in run.name for needle in needles)]
    runs_by_name = {run.name: run for run in runs}
    if len(runs_by_name) != len(runs):
        raise ValueError("Run names must be unique")

    reference: str | Path | None
    if args.reference == "exact":
        reference = "exact"
    elif args.reference:
        reference = _resolve_recorded_path(
            str(args.reference),
            output_root=output_root,
            matrix_parent=matrix_summary.parent,
        )
    else:
        reference = None

    pair_specs = _implicit_pairs(runs, args.pair_by)
    pair_specs.extend(_explicit_pairs(runs_by_name, args.pair, args.pair_label))
    pairs = [
        _pair_row(label, left, right, args.gamma, reference, args.with_phase)
        for label, left, right in pair_specs
    ]
    summary = {
        "mode": "matrix_summary",
        "matrix_summary": str(matrix_summary),
        "run_count": len(runs),
        "pair_count": len(pairs),
        "pair_by": args.pair_by,
        "runs": [_run_scalars(run) for run in runs],
        "pairs": pairs,
    }
    prefix = args.out if args.out is not None else matrix_summary.parent / "summary"
    _write_outputs(prefix, summary)
    return summary


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Summarise run_matrix.py matrix_summary.json outputs.")
    p.add_argument("matrix_summary", type=Path)
    p.add_argument("--gamma", type=float, default=1.4)
    p.add_argument("--pair-by", choices=("precision", "build", "none"), default="precision")
    p.add_argument("--pair", nargs=2, action="append", metavar=("LEFT_RUN", "RIGHT_RUN"))
    p.add_argument("--pair-label", action="append")
    p.add_argument("--reference", default=None)
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--with-phase", action="store_true")
    p.add_argument("--filter-name-contains", default=None)
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    summary = build_report(args)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
