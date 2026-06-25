#!/usr/bin/env python3
"""Shared helpers for Week 13 2D MHD validation drivers.

Pure-numeric helpers (block_average_2d, point_symmetry_residual,
reflect_y_residual, conserved_totals) are unit-tested in
tests/py/test_mhd_harness.py. The subprocess runner mirrors the Week-12
mhd_2d_week12.py provenance discipline (generated cfg, stdout/stderr,
metadata.json per run).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

import numpy as np

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from io_helper import read_binary  # noqa: E402  (re-exported)

ROOT = pathlib.Path(__file__).resolve().parents[2]
RHO, MX, MY, MZ, BX, BY, BZ, E, PSI = range(9)

_DIAG_RE = re.compile(
    r"\[mhd\]\s+t=(?P<t>\S+)\s+steps=(?P<steps>\d+)\s+"
    r"divB_mean=(?P<divB_mean>\S+)\s+divB_max=(?P<divB_max>\S+)"
)


# --- pure-numeric helpers (unit-tested) ------------------------------------

def block_average_2d(arr: np.ndarray, ny_c: int, nx_c: int) -> np.ndarray:
    """Block-mean a (ny, nx) array down to (ny_c, nx_c). Requires integer factors."""
    if ny_c <= 0 or nx_c <= 0:
        raise ValueError(f"target shape must be positive, got ({ny_c},{nx_c})")
    ny, nx = arr.shape
    if ny % ny_c != 0 or nx % nx_c != 0:
        raise ValueError(f"non-integer downsample factor: ({ny},{nx}) -> ({ny_c},{nx_c})")
    fy, fx = ny // ny_c, nx // nx_c
    return arr.reshape(ny_c, fy, nx_c, fx).mean(axis=(1, 3))


def point_symmetry_residual(field: np.ndarray) -> float:
    """Relative residual under 180-deg rotation about the grid centre (OT invariant)."""
    rot = field[::-1, ::-1]
    denom = float(np.abs(field).max()) or 1.0
    return float(np.abs(field - rot).max() / denom)


def reflect_y_residual(field: np.ndarray) -> float:
    """Relative residual under y -> Ny-1-y reflection (KH shear-layer invariant)."""
    refl = field[::-1, :]
    denom = float(np.abs(field).max()) or 1.0
    return float(np.abs(field - refl).max() / denom)


def conserved_totals(arr: np.ndarray, gamma: float) -> dict[str, float]:
    """Domain sums of conserved mass and total energy (periodic-domain invariants)."""
    _ = gamma  # kept for API parity; conserved totals use stored fields directly.
    return {"mass": float(arr[..., RHO].sum()), "energy": float(arr[..., E].sum())}


# --- subprocess / provenance helpers ---------------------------------------

def resolve_binary(path: pathlib.Path) -> pathlib.Path:
    if path.is_file():
        return path
    exe = pathlib.Path(str(path) + ".exe")
    if exe.is_file():
        return exe
    raise FileNotFoundError(f"missing MHD binary: {path} (or {exe})")


def replace_or_append_cfg(text: str, key: str, value: str) -> str:
    out, replaced = [], False
    for line in text.splitlines():
        if line.strip().startswith("#") or "=" not in line:
            out.append(line)
            continue
        if line.split("=", 1)[0].strip() == key:
            suffix = ""
            comment_start = line.find("#")
            if comment_start >= 0:
                before_comment = line[:comment_start]
                comment_gap = before_comment[len(before_comment.rstrip()):]
                suffix = f"{comment_gap}{line[comment_start:]}"
            out.append(f"{key} = {value}{suffix}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"{key} = {value}")
    return "\n".join(out) + "\n"


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True,
            stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unknown"


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_mhd_diagnostics(stderr_text: str) -> dict[str, Any]:
    for line in reversed(stderr_text.splitlines()):
        m = _DIAG_RE.search(line)
        if m:
            return {"t": float(m.group("t")), "steps": int(m.group("steps")),
                    "divB_mean": float(m.group("divB_mean")),
                    "divB_max": float(m.group("divB_max")), "line": line}
    return {}


def run_case(label, cfg_text, run_dir, bin_path, source_cfg, commit, binary_sha256,
             *, output_bin=None, experiment="week13-mhd-2d"):
    run_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = run_dir / "config.cfg"
    cfg_path.write_text(cfg_text, encoding="utf-8")
    stdout_path, stderr_path = run_dir / "stdout.txt", run_dir / "stderr.txt"
    command = [str(bin_path), str(cfg_path)]
    output_bin_path = None
    if output_bin is not None:
        output_bin_path = pathlib.Path(output_bin)
        if not output_bin_path.is_absolute():
            output_bin_path = ROOT / output_bin_path
    start = time.time()
    t0 = time.perf_counter()
    with stdout_path.open("w", encoding="utf-8") as fo, stderr_path.open("w", encoding="utf-8") as fe:
        result = subprocess.run(command, cwd=str(ROOT), stdout=fo, stderr=fe, check=False)
    elapsed = time.perf_counter() - t0
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
    meta = {
        "experiment": experiment, "name": label,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": commit, "binary": str(bin_path), "binary_sha256": binary_sha256,
        "source_config": str(source_cfg), "source_config_sha256": sha256_file(source_cfg),
        "run_config": str(cfg_path), "run_config_sha256": sha256_file(cfg_path),
        "run_config_text": cfg_text, "command": command,
        "returncode": result.returncode, "elapsed_wall_s": elapsed,
        "stdout": str(stdout_path), "stderr": str(stderr_path),
        "stderr_diagnostics": parse_mhd_diagnostics(stderr_text),
    }
    if output_bin_path is not None:
        meta["output_binary"] = str(output_bin_path)
    (run_dir / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"run '{label}' failed (rc={result.returncode}); see {stderr_path}")
    if output_bin_path is not None:
        if not output_bin_path.is_file() or output_bin_path.stat().st_mtime < start:
            raise RuntimeError(f"run '{label}' did not (re)produce {output_bin_path}; see {stderr_path}")
    return result, meta, stderr_text
