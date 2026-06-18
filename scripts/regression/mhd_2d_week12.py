#!/usr/bin/env python3
"""2D MHD validation harness — Week 12 Tasks 17 + 18.

Sub-validation 1 (brio_wu_2d):  Transverse invariance of the 800x4 Brio-Wu run.
Sub-validation 2 (divb_clean):  GLM divergence-cleaning decay sweep (glm_cr x t_end).

Usage:
    python scripts/regression/mhd_2d_week12.py [--case {brio_wu_2d,divb_clean,all}]

Output root: experiments/week12/mhd_2d/
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pathlib
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from typing import Any

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from io_helper import read_binary  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE_BIN = ROOT / "build-double" / "hrsc_mhd"
CFG_BW2D = ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu_2d.cfg"
CFG_BW1D = ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg"
CFG_DIVB = ROOT / "tests" / "cases" / "mhd_divb_clean" / "divb_blob.cfg"

OUT_ROOT = ROOT / "experiments" / "week12" / "mhd_2d"
OUT_BW2D = OUT_ROOT / "brio_wu_2d"
OUT_DIVB = OUT_ROOT / "divb_clean"

# MHD variable indices (RHO=0 .. PSI=8)
RHO, MX, MY, MZ, BX, BY, BZ, E, PSI = range(9)

MHD_DIAGNOSTIC_RE = re.compile(
    r"\[mhd\]\s+t=(?P<t>\S+)\s+steps=(?P<steps>\d+)\s+"
    r"divB_mean=(?P<divB_mean>\S+)\s+divB_max=(?P<divB_max>\S+)"
)

# ---------------------------------------------------------------------------
# Helpers (matching mhd_brio_wu_1d.py style)
# ---------------------------------------------------------------------------

def resolve_binary(path: pathlib.Path) -> pathlib.Path:
    """Return the executable path, accepting Windows .exe builds."""
    if path.is_file():
        return path
    exe = (
        path.with_suffix(path.suffix + ".exe")
        if path.suffix
        else pathlib.Path(str(path) + ".exe")
    )
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


def run_case(
    label: str,
    cfg_text: str,
    run_dir: pathlib.Path,
    bin_path: pathlib.Path,
    source_cfg: pathlib.Path,
    commit: str,
    binary_sha256: str,
    *,
    output_bin: pathlib.Path | None = None,
) -> tuple[subprocess.CompletedProcess, dict[str, Any], str]:
    """Write generated config, run executable, write provenance metadata.

    Returns (result, metadata_dict, stderr_text).
    output_bin: if given, the binary grid path to verify was produced.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = run_dir / "config.cfg"
    cfg_path.write_text(cfg_text, encoding="utf-8")

    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    command = [str(bin_path), str(cfg_path)]

    run_start_wall_s = time.time()
    t0 = time.perf_counter()
    with stdout_path.open("w", encoding="utf-8") as fout, stderr_path.open(
        "w", encoding="utf-8"
    ) as ferr:
        result = subprocess.run(
            command,
            cwd=str(ROOT),
            stdout=fout,
            stderr=ferr,
            check=False,
        )
    elapsed_wall_s = time.perf_counter() - t0
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")

    metadata: dict[str, Any] = {
        "experiment": "week12-mhd-2d",
        "name": label,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": commit,
        "binary": str(bin_path),
        "binary_sha256": binary_sha256,
        "source_config": str(source_cfg),
        "source_config_sha256": sha256_file(source_cfg),
        "run_config": str(cfg_path),
        "run_config_sha256": sha256_file(cfg_path),
        "run_config_text": cfg_text,
        "precision": "double",
        "build": "build-double",
        "command": command,
        "returncode": result.returncode,
        "elapsed_wall_s": elapsed_wall_s,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "stderr_diagnostics": parse_mhd_diagnostics(stderr_text),
    }
    (run_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"run '{label}' failed (returncode={result.returncode}); see {stderr_path}"
        )
    if output_bin is not None and not output_bin.is_file():
        raise RuntimeError(
            f"run '{label}' returned 0 but did not produce {output_bin}; see {stderr_path}"
        )
    if output_bin is not None and output_bin.stat().st_mtime < run_start_wall_s:
        raise RuntimeError(
            f"run '{label}' returned 0 but {output_bin} is older than run start; see {stderr_path}"
        )

    return result, metadata, stderr_text


# ===========================================================================
# Sub-validation 1: brio_wu_2d  (transverse invariance)
# ===========================================================================

def run_brio_wu_2d(bin_path: pathlib.Path, commit: str, binary_sha256: str) -> dict[str, Any]:
    OUT_BW2D.mkdir(parents=True, exist_ok=True)
    print("[brio_wu_2d] Starting transverse-invariance check ...")

    # ---- 2D run -----------------------------------------------------------
    bw2d_bin = OUT_BW2D / "bw2d.bin"
    if bw2d_bin.exists():
        bw2d_bin.unlink()

    cfg_text = CFG_BW2D.read_text(encoding="utf-8")
    cfg_text = replace_or_append_cfg(cfg_text, "output_format", "binary")
    cfg_text = replace_or_append_cfg(cfg_text, "output_file", str(bw2d_bin))

    run_dir_2d = OUT_BW2D / "runs" / "bw2d"
    _, meta_2d, stderr_2d = run_case(
        "bw2d",
        cfg_text,
        run_dir_2d,
        bin_path,
        CFG_BW2D,
        commit,
        binary_sha256,
        output_bin=bw2d_bin,
    )
    diag_2d = meta_2d["stderr_diagnostics"]
    print(f"[brio_wu_2d]   2D run done in {meta_2d['elapsed_wall_s']:.2f}s  "
          f"divB_max={diag_2d.get('divB_max', float('nan')):.3e}")

    # ---- Read 2D grid and check transverse invariance --------------------
    header, arr = read_binary(bw2d_bin)
    if header.nvars != 9:
        raise RuntimeError(f"expected nvars=9, got {header.nvars}")
    ny, nx, nvars = arr.shape
    print(f"[brio_wu_2d]   grid shape: ny={ny}, nx={nx}, nvars={nvars}")

    # For each variable k and each row j, max_i |arr[j,i,k] - arr[0,i,k]|
    row0 = arr[0:1, :, :]  # shape (1, nx, nvars)
    dev = np.abs(arr - row0)  # shape (ny, nx, nvars)
    max_transverse_dev = float(dev.max())
    print(f"[brio_wu_2d]   max_transverse_dev = {max_transverse_dev:.3e}")

    # ---- 1D reference run (in-process) ------------------------------------
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_bin = pathlib.Path(tmpdir) / "bw1d_ref.bin"
        cfg1d_text = CFG_BW1D.read_text(encoding="utf-8")
        cfg1d_text = replace_or_append_cfg(cfg1d_text, "output_format", "binary")
        cfg1d_text = replace_or_append_cfg(cfg1d_text, "output_file", str(tmp_bin))

        run_dir_1d = OUT_BW2D / "runs" / "bw1d_ref"
        _, meta_1d, stderr_1d = run_case(
            "bw1d_ref",
            cfg1d_text,
            run_dir_1d,
            bin_path,
            CFG_BW1D,
            commit,
            binary_sha256,
            output_bin=tmp_bin,
        )
        header_1d, arr_1d = read_binary(tmp_bin)
        print(f"[brio_wu_2d]   1D ref run done in {meta_1d['elapsed_wall_s']:.2f}s  "
              f"shape: ny={header_1d.ny}, nx={header_1d.nx}")

        rho_2d_row0 = arr[0, :, RHO].astype(np.float64)
        rho_1d = arr_1d[0, :, RHO].astype(np.float64)

        # Both nx=800 by default; if they differ, resample the 1D to match
        if rho_1d.shape[0] != rho_2d_row0.shape[0]:
            raise RuntimeError(
                f"1D nx={rho_1d.shape[0]} != 2D nx={rho_2d_row0.shape[0]}; "
                "cannot compare without resampling"
            )
        mean_abs_rho_diff_vs_1d = float(np.abs(rho_2d_row0 - rho_1d).mean())
        print(f"[brio_wu_2d]   mean_abs_rho_diff_vs_1d = {mean_abs_rho_diff_vs_1d:.3e}")

    divb_max_2d = float(diag_2d.get("divB_max", float("nan")))
    divb_mean_2d = float(diag_2d.get("divB_mean", float("nan")))

    # ---- Gate checks -------------------------------------------------------
    gate_transverse = max_transverse_dev <= 1e-12
    gate_divb = divb_max_2d <= 1e-10
    gate_rho_vs_1d = mean_abs_rho_diff_vs_1d < 2e-2

    results: dict[str, Any] = {
        "max_transverse_dev": max_transverse_dev,
        "divB_max": divb_max_2d,
        "divB_mean": divb_mean_2d,
        "mean_abs_rho_diff_vs_1d": mean_abs_rho_diff_vs_1d,
        "gate_transverse_passed": gate_transverse,
        "gate_divB_passed": gate_divb,
        "gate_rho_vs_1d_passed": gate_rho_vs_1d,
        "grid_shape": {"ny": ny, "nx": nx, "nvars": nvars},
    }

    # ---- Summary markdown -------------------------------------------------
    md_lines = [
        "# Week 12 Brio-Wu 2D Transverse-Invariance Validation",
        "",
        "800x4 grid, outflow-x, periodic-y, glm_cr=0.18, t_end=0.1.",
        "",
        "## Results",
        "",
        "| metric | value | gate | pass? |",
        "|---|---:|---|---:|",
        f"| max_transverse_dev | {max_transverse_dev:.3e} | <= 1e-12 | {gate_transverse} |",
        f"| divB_max (2D) | {divb_max_2d:.3e} | <= 1e-10 | {gate_divb} |",
        f"| mean_abs_rho_diff_vs_1d | {mean_abs_rho_diff_vs_1d:.3e} | < 2e-2 | {gate_rho_vs_1d} |",
        "",
        "## Diagnostics",
        "",
        f"- 2D run elapsed: {meta_2d['elapsed_wall_s']:.2f}s",
        f"- 1D ref elapsed: {meta_1d['elapsed_wall_s']:.2f}s",
        f"- 2D steps: {diag_2d.get('steps', '?')}",
        f"- 2D grid shape: ny={ny}, nx={nx}, nvars={nvars}",
        "",
        "Generated cfgs, stdout/stderr, and per-run metadata live under "
        "`experiments/week12/mhd_2d/brio_wu_2d/runs/`.",
    ]
    md_text = "\n".join(md_lines) + "\n"
    (OUT_BW2D / "summary.md").write_text(md_text, encoding="utf-8")

    summary_json: dict[str, Any] = {
        "experiment": "week12-brio-wu-2d",
        "git_commit": commit,
        "binary_sha256": binary_sha256,
        "results": results,
        "runs": {
            "bw2d": meta_2d,
            "bw1d_ref": meta_1d,
        },
    }
    (OUT_BW2D / "summary.json").write_text(
        json.dumps(summary_json, indent=2) + "\n", encoding="utf-8"
    )

    # Print summary
    print()
    print(md_text)

    # ---- Raise if any gate fails ------------------------------------------
    failures = []
    if not gate_transverse:
        failures.append(
            f"GATE FAIL: max_transverse_dev={max_transverse_dev:.3e} > 1e-12 "
            "(rows are not transversely invariant)"
        )
    if not gate_divb:
        failures.append(
            f"GATE FAIL: divB_max={divb_max_2d:.3e} > 1e-10 (unexpected div-B growth)"
        )
    if not gate_rho_vs_1d:
        failures.append(
            f"GATE FAIL: mean_abs_rho_diff_vs_1d={mean_abs_rho_diff_vs_1d:.3e} >= 2e-2 "
            "(2D row 0 deviates too much from 1D reference)"
        )
    if failures:
        for f in failures:
            print(f, file=sys.stderr)
        raise SystemExit("\n".join(failures))

    print("[brio_wu_2d] ALL GATES PASSED")
    return results


# ===========================================================================
# Sub-validation 2: divb_clean  (GLM divergence cleaning sweep)
# ===========================================================================

GLM_CR_SWEEP = [0.0, 0.18, 0.36]
T_END_SWEEP = [0.05, 0.1, 0.2, 0.35, 0.5]
# Output binary only for (cr in {0.0, 0.18}, t_end=0.5)
FIGURE_OUTPUT_CRS = {0.0, 0.18}


def cr_label(cr: float) -> str:
    return f"cr{cr:.2f}".replace(".", "p")


def run_divb_clean(bin_path: pathlib.Path, commit: str, binary_sha256: str) -> dict[str, Any]:
    OUT_DIVB.mkdir(parents=True, exist_ok=True)
    print("[divb_clean] Starting GLM cleaning sweep "
          f"(cr={GLM_CR_SWEEP}, t_end={T_END_SWEEP}) ...")
    print(f"[divb_clean] Total runs: {len(GLM_CR_SWEEP) * len(T_END_SWEEP)}")

    # cr -> list of {t_end, divB_max, divB_mean, steps, elapsed_wall_s}
    decay_table: dict[float, list[dict[str, Any]]] = {cr: [] for cr in GLM_CR_SWEEP}
    figure_grids: dict[str, str] = {}  # key -> path string
    all_runs_meta: list[dict[str, Any]] = []

    run_index = 0
    for cr in GLM_CR_SWEEP:
        for t_end in T_END_SWEEP:
            run_index += 1
            label = f"divb_cr{cr_label(cr)}_t{t_end}"
            run_dir = OUT_DIVB / "runs" / label
            print(f"[divb_clean]   [{run_index:2d}/{len(GLM_CR_SWEEP)*len(T_END_SWEEP)}] "
                  f"cr={cr}, t_end={t_end} ...", flush=True)

            # Build config text
            cfg_text = CFG_DIVB.read_text(encoding="utf-8")
            cfg_text = replace_or_append_cfg(cfg_text, "glm_cr", str(cr))
            cfg_text = replace_or_append_cfg(cfg_text, "t_end", str(t_end))

            output_bin: pathlib.Path | None = None
            if cr in FIGURE_OUTPUT_CRS and math.isclose(t_end, 0.5):
                output_bin = OUT_DIVB / f"divb_blob_{cr_label(cr)}_t0p5.bin"
                if output_bin.exists():
                    output_bin.unlink()
                cfg_text = replace_or_append_cfg(cfg_text, "output_format", "binary")
                cfg_text = replace_or_append_cfg(cfg_text, "output_file", str(output_bin))

            _, meta, stderr_text = run_case(
                label,
                cfg_text,
                run_dir,
                bin_path,
                CFG_DIVB,
                commit,
                binary_sha256,
                output_bin=output_bin,
            )

            diag = meta["stderr_diagnostics"]
            divb_max = float(diag.get("divB_max", float("nan")))
            divb_mean = float(diag.get("divB_mean", float("nan")))
            steps = int(diag.get("steps", -1))

            decay_table[cr].append({
                "t_end": t_end,
                "divB_max": divb_max,
                "divB_mean": divb_mean,
                "steps": steps,
                "elapsed_wall_s": meta["elapsed_wall_s"],
            })

            if output_bin is not None:
                key = f"cr{cr}_t0.5"
                figure_grids[key] = str(output_bin)

            all_runs_meta.append(meta)
            print(f"[divb_clean]       divB_max={divb_max:.3e}  divB_mean={divb_mean:.3e}  "
                  f"steps={steps}  elapsed={meta['elapsed_wall_s']:.1f}s")

    # ---- Gate check --------------------------------------------------------
    def val_at_t(cr: float, t: float) -> float:
        for row in decay_table[cr]:
            if math.isclose(row["t_end"], t):
                return float(row["divB_max"])
        return float("nan")

    divb_max_ctrl = val_at_t(0.0, 0.5)
    divb_max_018 = val_at_t(0.18, 0.5)
    divb_max_036 = val_at_t(0.36, 0.5)

    all_finite = all(
        math.isfinite(v) for v in [divb_max_ctrl, divb_max_018, divb_max_036]
    )
    cleaning_018 = divb_max_018 < divb_max_ctrl
    cleaning_036 = divb_max_036 < divb_max_ctrl
    cr036_better_than_cr018 = divb_max_036 < divb_max_018  # informational only

    print()
    print(f"[divb_clean] Gate check:")
    print(f"  divB_max(cr=0.00, t=0.5) = {divb_max_ctrl:.3e}  (control)")
    print(f"  divB_max(cr=0.18, t=0.5) = {divb_max_018:.3e}  cleaned < control? {cleaning_018}")
    print(f"  divB_max(cr=0.36, t=0.5) = {divb_max_036:.3e}  cleaned < control? {cleaning_036}")
    print(f"  cr=0.36 better than cr=0.18? {cr036_better_than_cr018}  (informational)")

    # ---- Build summary.csv -------------------------------------------------
    csv_rows = []
    for cr in GLM_CR_SWEEP:
        for entry in decay_table[cr]:
            csv_rows.append({
                "glm_cr": cr,
                "t_end": entry["t_end"],
                "divB_max": entry["divB_max"],
                "divB_mean": entry["divB_mean"],
                "steps": entry["steps"],
                "elapsed_wall_s": entry["elapsed_wall_s"],
            })
    with (OUT_DIVB / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["glm_cr", "t_end", "divB_max", "divB_mean", "steps", "elapsed_wall_s"]
        )
        writer.writeheader()
        writer.writerows(csv_rows)

    # ---- Build summary.json -----------------------------------------------
    summary_json: dict[str, Any] = {
        "experiment": "week12-divb-clean",
        "git_commit": commit,
        "binary_sha256": binary_sha256,
        "glm_cr_sweep": GLM_CR_SWEEP,
        "t_end_sweep": T_END_SWEEP,
        "decay_table": {str(cr): decay_table[cr] for cr in GLM_CR_SWEEP},
        "gate": {
            "divB_max_ctrl_t0p5": divb_max_ctrl,
            "divB_max_cr018_t0p5": divb_max_018,
            "divB_max_cr036_t0p5": divb_max_036,
            "all_finite": all_finite,
            "cleaning_018_passed": cleaning_018,
            "cleaning_036_passed": cleaning_036,
            "cr036_better_than_cr018": cr036_better_than_cr018,
        },
        "figure_grids": figure_grids,
    }
    (OUT_DIVB / "summary.json").write_text(
        json.dumps(summary_json, indent=2) + "\n", encoding="utf-8"
    )

    # ---- Build summary.md -------------------------------------------------
    cr_labels = [f"cr={cr}" for cr in GLM_CR_SWEEP]
    header_row = "| t_end | " + " | ".join(cr_labels) + " |"
    separator  = "|---:|" + ":---:|" * len(GLM_CR_SWEEP)

    md_lines = [
        "# Week 12 div(B) Cleaning Decay Validation",
        "",
        "128x128 doubly-periodic Gaussian Bx bump. GLM glm_cr sweep.",
        "Values are `divB_max` at the stated `t_end`.",
        "",
        "## Decay table (divB_max)",
        "",
        header_row,
        separator,
    ]
    # Look-up for easy access
    lookup: dict[tuple[float, float], float] = {}
    for cr in GLM_CR_SWEEP:
        for entry in decay_table[cr]:
            lookup[(cr, entry["t_end"])] = entry["divB_max"]

    for t in T_END_SWEEP:
        cells = [f"{lookup.get((cr, t), float('nan')):.3e}" for cr in GLM_CR_SWEEP]
        md_lines.append(f"| {t} | " + " | ".join(cells) + " |")

    md_lines.extend([
        "",
        "## Gate results",
        "",
        f"| check | value | pass? |",
        f"|---|---:|---:|",
        f"| divB_max(cr=0.00, t=0.5) control | {divb_max_ctrl:.3e} | n/a |",
        f"| divB_max(cr=0.18, t=0.5) < control | {divb_max_018:.3e} | {cleaning_018} |",
        f"| divB_max(cr=0.36, t=0.5) < control | {divb_max_036:.3e} | {cleaning_036} |",
        f"| cr=0.36 < cr=0.18 (informational) | {cr036_better_than_cr018} | n/a |",
        "",
        "## Figure grids",
        "",
    ])
    for key, path in figure_grids.items():
        md_lines.append(f"- `{key}`: `{path}`")
    md_lines.extend([
        "",
        "Generated cfgs, stdout/stderr, and per-run metadata live under "
        "`experiments/week12/mhd_2d/divb_clean/runs/`.",
    ])

    md_text = "\n".join(md_lines) + "\n"
    (OUT_DIVB / "summary.md").write_text(md_text, encoding="utf-8")

    print()
    print(md_text)

    # ---- Raise if gate fails -----------------------------------------------
    if not all_finite:
        raise SystemExit(
            "GATE FAIL: one or more divB_max values at t=0.5 are non-finite "
            "(possible blow-up); BLOCKED"
        )
    failures = []
    if not cleaning_018:
        failures.append(
            f"GATE FAIL: divB_max(cr=0.18)={divb_max_018:.3e} >= "
            f"divB_max(cr=0.0)={divb_max_ctrl:.3e} — GLM cr=0.18 is NOT cleaning better"
        )
    if not cleaning_036:
        failures.append(
            f"GATE FAIL: divB_max(cr=0.36)={divb_max_036:.3e} >= "
            f"divB_max(cr=0.0)={divb_max_ctrl:.3e} — GLM cr=0.36 is NOT cleaning better"
        )
    if failures:
        for f in failures:
            print(f, file=sys.stderr)
        raise SystemExit(
            "BLOCKED: GLM cleaning gate failed. Full decay table printed above. "
            "This likely indicates a real GLM bug.\n" + "\n".join(failures)
        )

    print("[divb_clean] ALL GATES PASSED")
    return {
        "decay_table": {cr: decay_table[cr] for cr in GLM_CR_SWEEP},
        "gate": summary_json["gate"],
        "figure_grids": figure_grids,
    }


# ===========================================================================
# main
# ===========================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Week 12 2D MHD validation harness")
    parser.add_argument(
        "--case",
        choices=["brio_wu_2d", "divb_clean", "all"],
        default="all",
        help="Which sub-validation to run (default: all)",
    )
    args = parser.parse_args()

    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    bin_path = resolve_binary(BASE_BIN)
    binary_sha256 = sha256_file(bin_path)
    commit = git_commit()

    print(f"[mhd_2d_week12] binary: {bin_path}")
    print(f"[mhd_2d_week12] sha256: {binary_sha256[:16]}...")
    print(f"[mhd_2d_week12] commit: {commit[:12]}")
    print()

    if args.case in ("brio_wu_2d", "all"):
        run_brio_wu_2d(bin_path, commit, binary_sha256)
        print()

    if args.case in ("divb_clean", "all"):
        run_divb_clean(bin_path, commit, binary_sha256)
        print()

    print("[mhd_2d_week12] Done -- all selected validations passed.")


if __name__ == "__main__":
    main()
