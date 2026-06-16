#!/usr/bin/env python3
"""Brio-Wu 1D MHD validation with a self-converged double reference.

Runs candidate resolutions plus an 8000-cell double reference, downsamples the
reference, and writes L1/L2/Linf density summaries. This is a Week 12 1D-only
driver; it keeps the local harness discipline of generated cfgs, stdout/stderr,
metadata, and summary.{csv,json,md}.
"""

from __future__ import annotations

import csv
import json
import pathlib
import subprocess
import sys
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


def resolve_binary(path: pathlib.Path) -> pathlib.Path:
    """Return the executable path, accepting Windows .exe builds."""
    if path.is_file():
        return path
    exe = path.with_suffix(path.suffix + ".exe") if path.suffix else pathlib.Path(str(path) + ".exe")
    if exe.is_file():
        return exe
    raise FileNotFoundError(f"missing MHD binary: {path} (or {exe})")


BIN = resolve_binary(BASE_BIN)


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


def write_run_config(nx: int, run_dir: pathlib.Path, raw_output: pathlib.Path) -> pathlib.Path:
    cfg_text = BASE_CFG.read_text(encoding="utf-8")
    cfg_text = replace_or_append_cfg(cfg_text, "nx", str(nx))
    cfg_text = replace_or_append_cfg(cfg_text, "output_format", "binary")
    cfg_text = replace_or_append_cfg(cfg_text, "output_file", str(raw_output))
    cfg_path = run_dir / "config.cfg"
    cfg_path.write_text(cfg_text, encoding="utf-8")
    return cfg_path


def run_resolution(nx: int, commit: str) -> np.ndarray:
    run_dir = OUT / "runs" / f"bw_{nx}_double"
    run_dir.mkdir(parents=True, exist_ok=True)
    raw_output = OUT / f"bw_{nx}.bin"
    cfg_path = write_run_config(nx, run_dir, raw_output)

    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    command = [str(BIN), str(cfg_path)]
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

    metadata: dict[str, Any] = {
        "experiment": "week12-brio-wu-1d",
        "name": f"bw_{nx}_double",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": commit,
        "binary": str(BIN),
        "source_config": str(BASE_CFG),
        "run_config": str(cfg_path),
        "precision": "double",
        "build": "build-double",
        "nx": nx,
        "raw_output": str(raw_output),
        "command": command,
        "returncode": result.returncode,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
    }
    (run_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(f"run failed for nx={nx}; see {stderr_path}")

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


def write_summaries(rows: list[dict[str, Any]]) -> str:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["nx", "reference_nx", "L1", "L2", "Linf"])
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "experiment": "week12-brio-wu-1d",
        "reference_nx": REF_NX,
        "candidate_nx": list(CANDIDATE_NX),
        "metric": "density self-convergence vs block-averaged double reference",
        "rows": rows,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    md = [
        "# Week 12 Brio-Wu 1D Validation",
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
            "Generated cfgs, stdout/stderr, and per-run metadata live under "
            "`experiments/week12/brio_wu_1d/runs/`.",
        ]
    )
    text = "\n".join(md) + "\n"
    (OUT / "summary.md").write_text(text, encoding="utf-8")
    return text


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    commit = git_commit()
    reference = run_resolution(REF_NX, commit)
    rows = [
        density_error_row(nx, run_resolution(nx, commit), reference)
        for nx in CANDIDATE_NX
    ]
    print(write_summaries(rows), end="")


if __name__ == "__main__":
    main()
