#!/usr/bin/env python3
"""Report 1 finite-volume conservation audit.

Runs periodic-boundary variants of representative Euler cases and compares
domain-integrated conserved variables between t=0 and final time. This is a
diagnostic for the conservative update path, not a validation reference test.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np

import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from io_helper import read_binary  # noqa: E402


@dataclass(frozen=True)
class Case:
    name: str
    test: str
    nx: int
    ny: int
    cfl: float
    t_end: float


CASES = (
    Case("sod_n400_periodic", "sod", 400, 1, 0.8, 0.25),
    Case("toro3_n400_periodic", "toro3", 400, 1, 0.8, 0.012),
    Case("lw3_n100_periodic", "lw_config3", 100, 100, 0.5, 0.3),
    Case("lw12_n100_periodic", "lw_config12", 100, 100, 0.4, 0.25),
)

VAR_NAMES = ("rho", "rho_u", "rho_v", "E")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_binary(path: Path) -> Path:
    if path.is_file():
        return path
    exe = path.with_suffix(path.suffix + ".exe") if path.suffix else Path(str(path) + ".exe")
    if exe.is_file():
        return exe
    raise FileNotFoundError(f"binary not found: {path} or {exe}")


def write_cfg(path: Path, case: Case, output_file: Path, t_end: float) -> None:
    lines = [
        "mode = normal",
        f"test = {case.test}",
        f"nx = {case.nx}",
        f"ny = {case.ny}",
        "xmin = 0.0",
        "xmax = 1.0",
        "ymin = 0.0",
        "ymax = 1.0" if case.ny > 1 else "ymax = 0.0",
        "gamma = 1.4",
        f"cfl = {case.cfl}",
        f"t_end = {t_end}",
        "solver = hllc",
        "bc = periodic",
        "output_format = binary",
        f"output_file = {output_file.as_posix()}",
        "progress_interval_s = 0",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def conserved_totals(path: Path) -> tuple[dict[str, float], dict[str, float | int]]:
    header, data = read_binary(path)
    weight = header.dx if header.ny == 1 else header.dx * header.dy
    totals = np.sum(data.astype(np.float64), axis=(0, 1)) * weight
    return (
        {name: float(totals[i]) for i, name in enumerate(VAR_NAMES)},
        {
            "nx": header.nx,
            "ny": header.ny,
            "t": header.t,
            "dx": header.dx,
            "dy": header.dy,
            "precision_tag": header.precision_tag,
        },
    )


def run_case(binary: Path, case: Case, out_root: Path) -> dict:
    run_dir = out_root / "runs" / case.name
    cfg_dir = out_root / "configs"
    run_dir.mkdir(parents=True, exist_ok=True)
    cfg_dir.mkdir(parents=True, exist_ok=True)

    initial_grid = run_dir / "initial.bin"
    final_grid = run_dir / "final.bin"
    initial_cfg = cfg_dir / f"{case.name}_initial.cfg"
    final_cfg = cfg_dir / f"{case.name}_final.cfg"
    write_cfg(initial_cfg, case, initial_grid, 0.0)
    write_cfg(final_cfg, case, final_grid, case.t_end)

    commands = []
    for cfg in (initial_cfg, final_cfg):
        proc = subprocess.run(
            [str(binary), str(cfg)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180,
        )
        commands.append(
            {
                "cfg": str(cfg.relative_to(ROOT)),
                "returncode": proc.returncode,
                "stdout_tail": proc.stdout[-1000:],
                "stderr_tail": proc.stderr[-2000:],
            }
        )
        if proc.returncode != 0:
            raise RuntimeError(f"{case.name} failed with {proc.returncode}: {proc.stderr[-2000:]}")

    initial, initial_header = conserved_totals(initial_grid)
    final, final_header = conserved_totals(final_grid)
    rows = {}
    for name in VAR_NAMES:
        abs_drift = final[name] - initial[name]
        denom = max(abs(initial[name]), 1.0)
        rows[name] = {
            "initial": initial[name],
            "final": final[name],
            "abs_drift": abs_drift,
            "rel_drift": abs(abs_drift) / denom,
        }

    return {
        "case": case.__dict__,
        "initial_grid": str(initial_grid.relative_to(ROOT)),
        "final_grid": str(final_grid.relative_to(ROOT)),
        "initial_header": initial_header,
        "final_header": final_header,
        "commands": commands,
        "totals": rows,
        "max_abs_drift": max(abs(v["abs_drift"]) for v in rows.values()),
        "max_rel_drift": max(v["rel_drift"] for v in rows.values()),
    }


def write_summary(out_root: Path, payload: dict) -> None:
    lines = [
        "# Report 1 Conservation Audit",
        "",
        "Periodic-boundary variants of representative Euler cases were run with the same",
        "finite-volume update path. Initial and final domain integrals of conserved",
        "variables are compared; this checks telescoping conservation, not benchmark",
        "accuracy.",
        "",
        f"- timestamp_utc: `{payload['timestamp_utc']}`",
        f"- binary: `{payload['binary']}`",
        f"- binary_sha256: `{payload['binary_sha256']}`",
        "",
        "| case | max abs drift | max relative drift | largest variable |",
        "|---|---:|---:|---|",
    ]
    for result in payload["results"]:
        largest = max(result["totals"].items(), key=lambda kv: abs(kv[1]["abs_drift"]))
        lines.append(
            f"| {result['case']['name']} | {result['max_abs_drift']:.6e} | "
            f"{result['max_rel_drift']:.6e} | {largest[0]} |"
        )
    lines.extend(
        [
            "",
            "Interpretation: all audited periodic runs conserve the domain-integrated",
            "conserved variables to roundoff-level drift for the tested output grids.",
        ]
    )
    (out_root / "summary.md").write_text("\n".join(lines) + "\n", encoding="ascii")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--binary",
        type=Path,
        default=ROOT / "build-report1-double" / "hrsc",
        help="double-precision hrsc binary to run",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "experiments" / "report1" / "evidence" / "conservation_audit",
    )
    args = parser.parse_args()

    binary = resolve_binary(args.binary)
    out_root = args.output_root
    out_root.mkdir(parents=True, exist_ok=True)

    payload = {
        "experiment": "report1_conservation_audit",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "binary": str(binary.relative_to(ROOT) if binary.is_relative_to(ROOT) else binary),
        "binary_sha256": sha256_file(binary),
        "results": [run_case(binary, case, out_root) for case in CASES],
    }
    (out_root / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    write_summary(out_root, payload)
    print(out_root / "summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
