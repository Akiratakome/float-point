#!/usr/bin/env python3
"""Run a local diagnostic HLL/HLLD GLM sweep for Orszag-Tang MHD.

This is an experiment harness driver, not a solver-default change. It copies
the source cfg into per-run directories, appends only run-specific overrides,
captures logs/metadata, derives scalar diagnostics, and writes lightweight
summaries. HLLD remains diagnostic/deferred unless a later production decision
records otherwise.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import platform
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_CASE = ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg"
DEFAULT_OUT = ROOT / "experiments" / "week13" / "hlld_glm_sweep"
DEFAULT_GLM_CR = (0.05, 0.1, 0.18, 0.3, 0.5)
DEFAULT_RIEMANN = ("hll", "hlld")
RHO = 0

if platform.system().lower().startswith("win"):
    DEFAULT_BINARY = ROOT / "build-double" / "hrsc_mhd.exe"
else:
    DEFAULT_BINARY = ROOT / "build-double" / "hrsc_mhd"

sys.path.insert(0, str(ROOT / "scripts" / "regression"))
from _mhd_harness import (  # noqa: E402
    git_commit,
    parse_mhd_diagnostics,
    replace_or_append_cfg,
    resolve_binary,
    run_case,
    sha256_file,
)


def glm_label(value: float) -> str:
    return f"{value:g}"


def is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def json_sanitise(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: json_sanitise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_sanitise(v) for v in value]
    if isinstance(value, tuple):
        return [json_sanitise(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def default_rho_metrics(status: str = "missing") -> dict[str, Any]:
    return {"grid_status": status, "finite_rho": None, "rho_min": None, "rho_max": None}


def read_rho_metrics(grid_path: pathlib.Path) -> dict[str, Any]:
    if not grid_path.is_file():
        return default_rho_metrics()
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from io_helper import read_binary  # noqa: WPS433

        _, arr = read_binary(grid_path)
        rho = arr[..., RHO]
        finite = bool(getattr(rho, "size", 0) and rho.size == int((rho == rho).sum()))
        finite = finite and bool(math.isfinite(float(rho.min()))) and bool(math.isfinite(float(rho.max())))
        return {
            "grid_status": "read",
            "finite_rho": finite,
            "rho_min": float(rho.min()),
            "rho_max": float(rho.max()),
        }
    except Exception as exc:  # pragma: no cover - exercised by real smoke runs.
        return {
            "grid_status": f"unreadable: {type(exc).__name__}: {exc}",
            "finite_rho": None,
            "rho_min": None,
            "rho_max": None,
        }


def make_run_cfg(
    source_text: str,
    *,
    grid_path: pathlib.Path,
    riemann: str,
    glm_cr: float,
    nx: int | None,
    t_end: float | None,
) -> str:
    text = source_text
    for key, value in (
        ("output_format", "binary"),
        ("output_file", str(grid_path)),
        ("riemann", riemann),
        ("glm_cr", f"{glm_cr:g}"),
    ):
        text = replace_or_append_cfg(text, key, value)
    if nx is not None:
        text = replace_or_append_cfg(text, "nx", str(nx))
        text = replace_or_append_cfg(text, "ny", str(nx))
    if t_end is not None:
        text = replace_or_append_cfg(text, "t_end", f"{t_end:g}")
    return text


def load_metadata(path: pathlib.Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def write_metadata(path: pathlib.Path, meta: dict[str, Any]) -> None:
    path.write_text(json.dumps(json_sanitise(meta), indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load_existing_row(run_dir: pathlib.Path, riemann: str, glm_cr: float) -> dict[str, Any] | None:
    meta_path = run_dir / "metadata.json"
    meta = load_metadata(meta_path)
    if meta is None:
        return None
    if meta.get("returncode") != 0:
        return None
    row = row_from_metadata(meta, run_dir, riemann, glm_cr, reused=True)
    if "rho_metrics" not in meta:
        meta["rho_metrics"] = {
            "grid_status": row.get("grid_status"),
            "finite_rho": row.get("finite_rho"),
            "rho_min": row.get("rho_min"),
            "rho_max": row.get("rho_max"),
        }
        write_metadata(meta_path, meta)
    return row


def row_from_metadata(
    meta: dict[str, Any],
    run_dir: pathlib.Path,
    riemann: str,
    glm_cr: float,
    *,
    reused: bool,
) -> dict[str, Any]:
    diag = meta.get("stderr_diagnostics") or {}
    grid_path = pathlib.Path(meta.get("output_binary") or (run_dir / "grid.bin"))
    rho_metrics = meta.get("rho_metrics") or read_rho_metrics(grid_path)
    row = {
        "name": run_dir.name,
        "riemann": riemann,
        "glm_cr": float(glm_cr),
        "returncode": meta.get("returncode"),
        "reused": bool(reused),
        "elapsed_wall_s": meta.get("elapsed_wall_s"),
        "t": diag.get("t"),
        "steps": diag.get("steps"),
        "divB_mean": diag.get("divB_mean"),
        "divB_max": diag.get("divB_max"),
        "diagnostics_line": diag.get("line"),
        "grid": str(grid_path),
        "metadata": str(run_dir / "metadata.json"),
    }
    row.update(rho_metrics)
    return row


def failed_row_from_run_dir(
    run_dir: pathlib.Path,
    riemann: str,
    glm_cr: float,
    error: Exception,
) -> dict[str, Any]:
    meta_path = run_dir / "metadata.json"
    meta = load_metadata(meta_path) or {}
    stderr_path = pathlib.Path(meta.get("stderr") or (run_dir / "stderr.txt"))
    stderr_text = ""
    if stderr_path.is_file():
        stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
    diag = meta.get("stderr_diagnostics") or parse_mhd_diagnostics(stderr_text)
    grid_path = pathlib.Path(meta.get("output_binary") or (run_dir / "grid.bin"))
    rho_metrics = meta.get("rho_metrics") or default_rho_metrics()
    row = {
        "name": run_dir.name,
        "riemann": riemann,
        "glm_cr": float(glm_cr),
        "returncode": meta.get("returncode", 1),
        "reused": False,
        "elapsed_wall_s": meta.get("elapsed_wall_s"),
        "t": diag.get("t"),
        "steps": diag.get("steps"),
        "divB_mean": diag.get("divB_mean"),
        "divB_max": diag.get("divB_max"),
        "diagnostics_line": diag.get("line"),
        "grid": str(grid_path),
        "metadata": str(meta_path),
        "error": f"{type(error).__name__}: {error}",
    }
    row.update(rho_metrics)
    if meta_path.is_file():
        meta["stderr_diagnostics"] = diag
        meta["rho_metrics"] = rho_metrics
        meta["sweep_error"] = row["error"]
        write_metadata(meta_path, meta)
    return row


def run_one(
    *,
    bin_path: pathlib.Path,
    case_path: pathlib.Path,
    source_text: str,
    out_root: pathlib.Path,
    riemann: str,
    glm_cr: float,
    nx: int | None,
    t_end: float | None,
    reuse: bool,
    commit: str,
    binary_sha256: str,
) -> dict[str, Any]:
    run_dir = out_root / "runs" / f"{riemann}_glm{glm_label(glm_cr)}"
    if reuse:
        existing = load_existing_row(run_dir, riemann, glm_cr)
        if existing is not None:
            return existing

    grid_path = run_dir / "grid.bin"
    cfg_text = make_run_cfg(
        source_text,
        grid_path=grid_path,
        riemann=riemann,
        glm_cr=glm_cr,
        nx=nx,
        t_end=t_end,
    )
    try:
        _, meta, stderr_text = run_case(
            run_dir.name,
            cfg_text,
            run_dir,
            bin_path,
            case_path,
            commit,
            binary_sha256,
            output_bin=grid_path,
            experiment="week13-hlld-glm-sweep",
        )
    except Exception as exc:
        return failed_row_from_run_dir(run_dir, riemann, glm_cr, exc)
    # Be tolerant of older metadata by reparsing the captured stderr if needed.
    if not meta.get("stderr_diagnostics"):
        meta["stderr_diagnostics"] = parse_mhd_diagnostics(stderr_text)
    meta["rho_metrics"] = read_rho_metrics(grid_path)
    write_metadata(run_dir / "metadata.json", meta)
    return row_from_metadata(meta, run_dir, riemann, glm_cr, reused=False)


def summarise_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    finite_hlld = [
        row for row in rows
        if row.get("riemann") == "hlld" and is_finite_number(row.get("divB_max"))
    ]
    best = min(finite_hlld, key=lambda row: float(row["divB_max"])) if finite_hlld else None
    completed = sum(1 for row in rows if row.get("returncode") == 0)
    finite_rho = sum(1 for row in rows if row.get("finite_rho") is True)
    return {
        "total_runs": len(rows),
        "completed_runs": completed,
        "finite_rho_runs": finite_rho,
        "best_finite_hlld": best,
        "hlld_adopted": False,
        "decision": (
            "HLLD remains diagnostic/deferred; this sweep is not production adoption. "
            "Use it only as local evidence for a later, separately recorded decision."
        ),
    }


def write_summary_csv(rows: list[dict[str, Any]], path: pathlib.Path) -> None:
    fieldnames = [
        "name",
        "riemann",
        "glm_cr",
        "returncode",
        "reused",
        "elapsed_wall_s",
        "t",
        "steps",
        "divB_mean",
        "divB_max",
        "finite_rho",
        "rho_min",
        "rho_max",
        "grid_status",
        "grid",
        "metadata",
        "error",
        "diagnostics_line",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        if not math.isfinite(value):
            return "n/a"
        return f"{value:.6g}"
    return str(value)


def write_summary_md(rows: list[dict[str, Any]], summary: dict[str, Any], path: pathlib.Path) -> None:
    lines = [
        "# Week 13 HLLD GLM Sweep",
        "",
        "This is a local diagnostic sweep for Orszag-Tang MHD GLM cleaning. "
        "HLLD remains diagnostic/deferred, and this sweep is not production adoption.",
        "",
        f"- completed runs: {summary['completed_runs']}/{summary['total_runs']}",
        f"- finite rho grids: {summary['finite_rho_runs']}/{summary['total_runs']}",
        "- HLLD production status: deferred",
        "",
        "## Best finite HLLD diagnostic",
        "",
    ]
    best = summary.get("best_finite_hlld")
    if best:
        lines.extend([
            f"- run: `{best['name']}`",
            f"- glm_cr: {fmt(best.get('glm_cr'))}",
            f"- divB_max: {fmt(best.get('divB_max'))}",
        ])
    else:
        lines.append("- no finite HLLD divB_max row was recorded")

    lines.extend([
        "",
        "## Runs",
        "",
        "| run | riemann | glm_cr | rc | t | steps | divB_mean | divB_max | finite_rho | rho_min | rho_max |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|",
    ])
    for row in rows:
        lines.append(
            "| {name} | {riemann} | {glm_cr} | {returncode} | {t} | {steps} | "
            "{divB_mean} | {divB_max} | {finite_rho} | {rho_min} | {rho_max} |".format(
                name=row["name"],
                riemann=row["riemann"],
                glm_cr=fmt(row.get("glm_cr")),
                returncode=fmt(row.get("returncode")),
                t=fmt(row.get("t")),
                steps=fmt(row.get("steps")),
                divB_mean=fmt(row.get("divB_mean")),
                divB_max=fmt(row.get("divB_max")),
                finite_rho=fmt(row.get("finite_rho")),
                rho_min=fmt(row.get("rho_min")),
                rho_max=fmt(row.get("rho_max")),
            )
        )
    lines.extend([
        "",
        "Generated artifacts: `summary.csv`, `summary.json`, per-run `config.cfg`, "
        "`stderr.txt` logs, and `metadata.json`. `stdout.txt` is a local run artifact "
        "when non-empty. Binary grids are transient analysis inputs and are not "
        "intended for commit.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_summaries(rows: list[dict[str, Any]], out_root: pathlib.Path, args: argparse.Namespace) -> dict[str, Any]:
    summary = summarise_rows(rows)
    payload = {
        "experiment": "week13-hlld-glm-sweep",
        "case": str(args.case),
        "binary": str(args.binary),
        "resolved_binary": str(args.resolved_binary),
        "output_root": str(out_root),
        "nx": args.nx,
        "t_end": args.t_end,
        "glm_cr": [float(v) for v in args.glm_cr],
        "riemann": list(args.riemann),
        "summary": summary,
        "runs": rows,
    }
    write_summary_csv(rows, out_root / "summary.csv")
    (out_root / "summary.json").write_text(
        json.dumps(json_sanitise(payload), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    write_summary_md(rows, summary, out_root / "summary.md")
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=pathlib.Path, default=DEFAULT_CASE)
    parser.add_argument("--binary", type=pathlib.Path, default=DEFAULT_BINARY)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--nx", type=int, default=None)
    parser.add_argument("--t-end", type=float, default=None)
    parser.add_argument("--glm-cr", nargs="+", type=float, default=list(DEFAULT_GLM_CR))
    parser.add_argument("--riemann", nargs="+", default=list(DEFAULT_RIEMANN))
    parser.add_argument("--reuse", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_root = args.out if args.out.is_absolute() else ROOT / args.out
    case_path = args.case if args.case.is_absolute() else ROOT / args.case
    bin_path = args.binary if args.binary.is_absolute() else ROOT / args.binary
    bin_path = resolve_binary(bin_path)
    args.resolved_binary = bin_path
    out_root.mkdir(parents=True, exist_ok=True)

    source_text = case_path.read_text(encoding="utf-8")
    binary_sha256 = sha256_file(bin_path)
    commit = git_commit()
    rows = []
    for riemann in args.riemann:
        for glm_cr in args.glm_cr:
            rows.append(
                run_one(
                    bin_path=bin_path,
                    case_path=case_path,
                    source_text=source_text,
                    out_root=out_root,
                    riemann=riemann,
                    glm_cr=float(glm_cr),
                    nx=args.nx,
                    t_end=args.t_end,
                    reuse=args.reuse,
                    commit=commit,
                    binary_sha256=binary_sha256,
                )
            )
    summary = write_summaries(rows, out_root, args)
    print(f"wrote {out_root / 'summary.md'}")
    print(summary["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
