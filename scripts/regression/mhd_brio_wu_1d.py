#!/usr/bin/env python3
"""Brio-Wu 1D MHD validation with a self-converged double reference.

Runs candidate resolutions plus an 8000-cell double reference, downsamples the
reference, and writes L1/L2/Linf density summaries. This is a Week 12 1D-only
driver; it keeps the local harness discipline of generated cfgs, stdout/stderr,
metadata, and summary.{csv,json,md}.
"""

from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from io_helper import read_binary  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE_BIN = ROOT / "build-double" / "hrsc_mhd"
BASE_CFG = ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg"
OUT = ROOT / "experiments" / "week12" / "brio_wu_1d"
RHO = 0
REF_NX = 8000
CANDIDATE_NX = (200, 400, 800)
MHD_DIAGNOSTIC_RE = re.compile(
    r"\[mhd\]\s+t=(?P<t>\S+)\s+steps=(?P<steps>\d+)\s+"
    r"divB_mean=(?P<divB_mean>\S+)\s+divB_max=(?P<divB_max>\S+)"
)


def resolve_binary(path: pathlib.Path) -> pathlib.Path:
    """Return the executable path, accepting Windows .exe builds."""
    if path.is_file():
        return path
    exe = path.with_suffix(path.suffix + ".exe") if path.suffix else pathlib.Path(str(path) + ".exe")
    if exe.is_file():
        return exe
    raise FileNotFoundError(f"missing MHD binary: {path} (or {exe})")


def replace_or_append_cfg(text: str, key: str, value: str) -> str:
    out: list[str] = []
    replaced = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or "=" not in line:
            out.append(line)
            continue
        lhs = line.split("=", 1)[0].strip()
        if lhs == key:
            out.append(f"{key} = {value}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"{key} = {value}")
    return "\n".join(out) + "\n"


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_mhd_diagnostics(stderr_text: str) -> dict[str, Any]:
    for line in reversed(stderr_text.splitlines()):
        match = MHD_DIAGNOSTIC_RE.search(line)
        if match:
            return {
                "t": float(match.group("t")),
                "steps": int(match.group("steps")),
                "divB_mean": float(match.group("divB_mean")),
                "divB_max": float(match.group("divB_max")),
                "line": line,
            }
    return {}


def write_run_config(nx: int, run_dir: pathlib.Path, raw_output: pathlib.Path) -> tuple[pathlib.Path, str]:
    cfg_text = BASE_CFG.read_text(encoding="utf-8")
    cfg_text = replace_or_append_cfg(cfg_text, "nx", str(nx))
    cfg_text = replace_or_append_cfg(cfg_text, "output_format", "binary")
    cfg_text = replace_or_append_cfg(cfg_text, "output_file", str(raw_output))
    cfg_path = run_dir / "config.cfg"
    cfg_path.write_text(cfg_text, encoding="utf-8")
    return cfg_path, cfg_text


def run_resolution(nx: int, commit: str, bin_path: pathlib.Path, binary_sha256: str) -> np.ndarray:
    run_dir = OUT / "runs" / f"bw_{nx}_double"
    run_dir.mkdir(parents=True, exist_ok=True)
    raw_output = OUT / f"bw_{nx}.bin"
    if raw_output.exists():
        raw_output.unlink()
    cfg_path, cfg_text = write_run_config(nx, run_dir, raw_output)

    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    command = [str(bin_path), str(cfg_path)]
    run_start_wall_s = time.time()
    start = time.perf_counter()
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr:
        result = subprocess.run(
            command,
            cwd=str(ROOT),
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    elapsed_wall_s = time.perf_counter() - start
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")

    metadata: dict[str, Any] = {
        "experiment": "week12-brio-wu-1d",
        "name": f"bw_{nx}_double",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": commit,
        "binary": str(bin_path),
        "binary_sha256": binary_sha256,
        "source_config": str(BASE_CFG),
        "source_config_sha256": sha256_file(BASE_CFG),
        "run_config": str(cfg_path),
        "run_config_sha256": sha256_file(cfg_path),
        "run_config_text": cfg_text,
        "precision": "double",
        "build": "build-double",
        "nx": nx,
        "raw_output": str(raw_output),
        "command": command,
        "returncode": result.returncode,
        "elapsed_wall_s": elapsed_wall_s,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "stderr_diagnostics": parse_mhd_diagnostics(stderr_text),
    }
    (run_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(f"run failed for nx={nx}; see {stderr_path}")
    if not raw_output.is_file():
        raise RuntimeError(
            f"run returned 0 for nx={nx} but did not produce {raw_output}; see {stderr_path}"
        )
    raw_output_mtime_s = raw_output.stat().st_mtime
    if raw_output_mtime_s < run_start_wall_s:
        raise RuntimeError(
            f"run returned 0 for nx={nx} but {raw_output} is older than the run start; "
            f"see {stderr_path}"
        )

    header, arr = read_binary(raw_output)
    if header.nvars != 9:
        raise RuntimeError(f"expected MHD nvars=9 in {raw_output}, got {header.nvars}")
    if header.nx != nx or header.ny != 1:
        raise RuntimeError(
            f"unexpected grid shape in {raw_output}: nx={header.nx}, ny={header.ny}"
        )
    return arr[0, :, RHO].astype(np.float64, copy=False)


def density_error_row(nx: int, rho: np.ndarray, reference: np.ndarray) -> dict[str, Any]:
    if REF_NX % nx != 0:
        raise ValueError(f"reference nx={REF_NX} is not divisible by nx={nx}")
    factor = REF_NX // nx
    reference_downsampled = reference.reshape(nx, factor).mean(axis=1)
    diff = np.abs(rho - reference_downsampled)
    dx = 1.0 / nx
    return {
        "nx": nx,
        "reference_nx": REF_NX,
        "L1": float(diff.sum() * dx),
        "L2": float(np.sqrt((diff**2).sum() * dx)),
        "Linf": float(diff.max()),
    }


def monotonic_convergence(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: row["nx"])
    metrics: dict[str, Any] = {}
    for metric in ("L1", "L2"):
        values = [float(row[metric]) for row in ordered]
        strictly_decreasing = all(a > b for a, b in zip(values, values[1:]))
        metrics[metric] = {
            "strictly_decreasing": strictly_decreasing,
            "values": values,
        }
    return {
        "candidate_nx": [int(row["nx"]) for row in ordered],
        "strictly_decreasing_L1_L2": all(
            metric["strictly_decreasing"] for metric in metrics.values()
        ),
        "metrics": metrics,
    }


def read_run_metadata(nx_values: tuple[int, ...]) -> list[dict[str, Any]]:
    metadata_rows: list[dict[str, Any]] = []
    for nx in nx_values:
        metadata_path = OUT / "runs" / f"bw_{nx}_double" / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata_rows.append(
            {
                "nx": nx,
                "metadata": str(metadata_path),
                "elapsed_wall_s": metadata["elapsed_wall_s"],
                "stderr_diagnostics": metadata["stderr_diagnostics"],
                "source_config_sha256": metadata["source_config_sha256"],
                "run_config_sha256": metadata["run_config_sha256"],
                "binary_sha256": metadata["binary_sha256"],
            }
        )
    return metadata_rows


def write_summaries(rows: list[dict[str, Any]], run_metadata: list[dict[str, Any]]) -> tuple[str, bool]:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["nx", "reference_nx", "L1", "L2", "Linf"])
        writer.writeheader()
        writer.writerows(rows)

    monotonic = monotonic_convergence(rows)
    summary = {
        "experiment": "week12-brio-wu-1d",
        "reference_nx": REF_NX,
        "candidate_nx": list(CANDIDATE_NX),
        "metric": "density self-convergence vs block-averaged aligned N=8000 double reference",
        "monotonic_convergence": monotonic,
        "runs": run_metadata,
        "rows": rows,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    md = [
        "# Week 12 Brio-Wu 1D Validation",
        "",
        "Density errors compare each candidate against a block-averaged aligned "
        "N=8000 double reference.",
        "",
        "| N | reference N | L1(rho) | L2(rho) | Linf(rho) |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        md.append(
            f"| {row['nx']} | {row['reference_nx']} | {row['L1']:.6e} | "
            f"{row['L2']:.6e} | {row['Linf']:.6e} |"
        )
    md.extend(
        [
            "",
            "## Monotonic convergence",
            "",
            f"Strictly decreasing L1 and L2 over N={list(CANDIDATE_NX)}: "
            f"{monotonic['strictly_decreasing_L1_L2']}",
            "",
            "| metric | strictly decreasing | values |",
            "|---|---:|---|",
        ]
    )
    for metric, result in monotonic["metrics"].items():
        values = ", ".join(f"{value:.6e}" for value in result["values"])
        md.append(f"| {metric} | {result['strictly_decreasing']} | {values} |")
    md.extend(
        [
            "",
            "## Run metadata",
            "",
            "| N | steps | divB_mean | divB_max | elapsed wall s |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for item in run_metadata:
        diagnostics = item["stderr_diagnostics"]
        md.append(
            f"| {item['nx']} | {diagnostics.get('steps', '')} | "
            f"{diagnostics.get('divB_mean', float('nan')):.3e} | "
            f"{diagnostics.get('divB_max', float('nan')):.3e} | "
            f"{item['elapsed_wall_s']:.3f} |"
        )
    md.extend(
        [
            "",
            "Generated cfgs, stdout/stderr, and per-run metadata live under "
            "`experiments/week12/brio_wu_1d/runs/`.",
        ]
    )
    text = "\n".join(md) + "\n"
    (OUT / "summary.md").write_text(text, encoding="utf-8")
    return text, bool(monotonic["strictly_decreasing_L1_L2"])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bin_path = resolve_binary(BASE_BIN)
    binary_sha256 = sha256_file(bin_path)
    commit = git_commit()
    reference = run_resolution(REF_NX, commit, bin_path, binary_sha256)
    rows = [
        density_error_row(nx, run_resolution(nx, commit, bin_path, binary_sha256), reference)
        for nx in CANDIDATE_NX
    ]
    run_metadata = read_run_metadata((REF_NX,) + CANDIDATE_NX)
    text, monotonic_ok = write_summaries(rows, run_metadata)
    print(text, end="")
    if not monotonic_ok:
        raise SystemExit("L1/L2 errors are not strictly decreasing over candidate resolutions")


if __name__ == "__main__":
    main()
