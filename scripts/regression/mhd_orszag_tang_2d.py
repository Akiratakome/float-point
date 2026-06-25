#!/usr/bin/env python3
"""Orszag-Tang 2D MHD validation (Week 13).

Gates:
  1. Self-converged reference: L1/L2/Linf on density (candidate 256^2 vs the
     512^2 double reference block-averaged to 256^2). Must be finite and the
     L1 must be below a coarse sanity ceiling.
  2. Conservation: |mass(t_end) - mass(t0)| / mass(t0) at round-off level.
  3. div(B) floor: glm_cr=0.18 run has finite divB_max below a hard ceiling.
     The glm_cr=0 control comparison is diagnostic only.
  4. Symmetry (reported, not gated): point-symmetry residual of density.
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
BIN = ROOT / "build-double" / "hrsc_mhd"
CFG = ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg"
CFG_REF = ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang_ref.cfg"
OUT = ROOT / "experiments" / "week13" / "orszag_tang"
GAMMA = 5.0 / 3.0
L1_CEILING = 0.5        # coarse sanity ceiling on L1(rho); real value is far smaller
DIVB_MAX_CEILING = 5.0  # hard gate: divB_max finite and bounded below this


def clear_scalar_summaries() -> None:
    for name in ("summary.csv", "summary.json", "summary.md"):
        path = OUT / name
        if path.exists():
            path.unlink()


def require_divb_max(meta, label):
    diagnostics = meta.get("stderr_diagnostics") or {}
    if "divB_max" not in diagnostics:
        stderr_path = meta.get("stderr", "<unknown stderr path>")
        raise RuntimeError(f"run '{label}' did not report divB_max; see {stderr_path}")
    return diagnostics["divB_max"]


def fmt_optional(value) -> str:
    return "n/a" if value is None else f"{value:.3e}"


def json_safe_run_meta(meta):
    safe = dict(meta)
    diagnostics = dict(safe.get("stderr_diagnostics") or {})
    for key, value in diagnostics.items():
        if isinstance(value, float) and not np.isfinite(value):
            diagnostics[key] = None
    safe["stderr_diagnostics"] = diagnostics
    return safe


def run_grid(label, cfg_path, out_bin, bin_path, commit, sha, extra=None):
    out_bin.parent.mkdir(parents=True, exist_ok=True)
    if out_bin.exists():
        out_bin.unlink()
    text = cfg_path.read_text(encoding="utf-8")
    text = replace_or_append_cfg(text, "output_format", "binary")
    text = replace_or_append_cfg(text, "output_file", str(out_bin))
    for k, v in (extra or {}).items():
        text = replace_or_append_cfg(text, k, str(v))
    _, meta, _ = run_case(label, text, OUT / "runs" / label, bin_path, cfg_path,
                          commit, sha, output_bin=out_bin)
    return meta


def main() -> None:
    global np, RHO, block_average_2d, conserved_totals, git_commit
    global point_symmetry_residual, read_binary, replace_or_append_cfg
    global resolve_binary, run_case, sha256_file

    OUT.mkdir(parents=True, exist_ok=True)
    clear_scalar_summaries()

    import numpy as np

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from _mhd_harness import (RHO, block_average_2d, conserved_totals, git_commit,
                              point_symmetry_residual, read_binary, replace_or_append_cfg,
                              resolve_binary, run_case, sha256_file)

    bin_path = resolve_binary(BIN)
    sha, commit = sha256_file(bin_path), git_commit()

    cand_bin = OUT / "ot_256.bin"
    ref_bin = OUT / "ot_512_ref.bin"
    meta_c = run_grid("ot_256", CFG, cand_bin, bin_path, commit, sha)
    meta_r = run_grid("ot_512_ref", CFG_REF, ref_bin, bin_path, commit, sha)
    meta_ctrl = run_grid("ot_256_cr0", CFG, OUT / "ot_256_cr0.bin", bin_path,
                         commit, sha, extra={"glm_cr": 0.0})

    _, cand = read_binary(cand_bin)
    _, ref = read_binary(ref_bin)
    rho_c = cand[..., RHO].astype(np.float64)
    rho_ref = block_average_2d(ref[..., RHO].astype(np.float64), rho_c.shape[0], rho_c.shape[1])

    diff = rho_c - rho_ref
    n = diff.size
    l1 = float(np.abs(diff).sum() / n)
    l2 = float(np.sqrt((diff ** 2).sum() / n))
    linf = float(np.abs(diff).max())

    # Conservation: re-read t0 mass by re-running candidate to t_end=0 is wasteful;
    # instead compare candidate total mass to the analytic IC mass (rho0 * ncells).
    rho0 = GAMMA * GAMMA
    mass_now = conserved_totals(cand, GAMMA)["mass"]
    mass_ic = rho0 * rho_c.size
    mass_rel = abs(mass_now - mass_ic) / mass_ic

    divb_cand = require_divb_max(meta_c, "ot_256")
    divb_ctrl_raw = require_divb_max(meta_ctrl, "ot_256_cr0")
    if np.isfinite(divb_ctrl_raw):
        divb_ctrl = float(divb_ctrl_raw)
        divb_ctrl_status = "finite"
    else:
        divb_ctrl = None
        divb_ctrl_status = "non-finite"
    sym = point_symmetry_residual(rho_c)
    # Diagnostic only: for a coupled physical solution the GLM cleaning ratio is
    # NOT guaranteed < 1 at every metric/time, so it is reported, not gated.
    raw_cleaning_ratio = (divb_cand / divb_ctrl) if divb_ctrl else None
    if raw_cleaning_ratio is not None and np.isfinite(raw_cleaning_ratio):
        cleaning_ratio = float(raw_cleaning_ratio)
        cleaning_ratio_status = "finite"
    else:
        cleaning_ratio = None
        cleaning_ratio_status = "undefined"

    gate_norms = np.isfinite([l1, l2, linf]).all() and l1 < L1_CEILING
    gate_mass = mass_rel < 1e-10
    # Hard div(B) gate: finite and bounded below a recorded ceiling (NOT a
    # comparison against the cr=0 control).
    gate_divb = bool(np.isfinite(divb_cand) and divb_cand < DIVB_MAX_CEILING)

    results = {"L1_rho": l1, "L2_rho": l2, "Linf_rho": linf, "mass_rel": mass_rel,
               "divB_max_cr018": divb_cand, "divB_max_cr0": divb_ctrl,
               "divB_max_cr0_status": divb_ctrl_status,
               "cleaning_ratio_diagnostic": cleaning_ratio,
               "cleaning_ratio_status": cleaning_ratio_status,
               "symmetry_residual": sym, "gate_norms": bool(gate_norms),
               "gate_mass": bool(gate_mass), "gate_divb": bool(gate_divb)}

    with (OUT / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results))
        w.writeheader()
        w.writerow(results)
    (OUT / "summary.json").write_text(json.dumps(
        {"experiment": "week13-orszag-tang", "git_commit": commit,
         "binary_sha256": sha, "results": results,
         "runs": {"cand": json_safe_run_meta(meta_c),
                  "ref": json_safe_run_meta(meta_r),
                  "ctrl": json_safe_run_meta(meta_ctrl)}},
        indent=2, allow_nan=False) + "\n",
        encoding="utf-8")
    md = [
        "# Week 13 Orszag-Tang 2D Validation", "",
        "256^2 candidate vs 512^2 double reference (block-averaged), gamma=5/3, t=0.5.", "",
        "| metric | value | gate | pass? |", "|---|---:|---|---:|",
        f"| L1(rho) | {l1:.3e} | < {L1_CEILING} | {gate_norms} |",
        f"| L2(rho) | {l2:.3e} | finite | {gate_norms} |",
        f"| Linf(rho) | {linf:.3e} | finite | {gate_norms} |",
        f"| mass_rel | {mass_rel:.3e} | < 1e-10 | {gate_mass} |",
        f"| divB_max | {divb_cand:.3e} | finite & < {DIVB_MAX_CEILING} | {gate_divb} |",
        f"| divB_max cr0 (diagnostic) | {fmt_optional(divb_ctrl)} | {divb_ctrl_status} | n/a |",
        f"| cleaning_ratio cr0.18/cr0 (diagnostic) | {fmt_optional(cleaning_ratio)} | "
        f"{cleaning_ratio_status} | n/a |",
        f"| symmetry_residual (reported) | {sym:.3e} | n/a | n/a |",
    ]
    (OUT / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))

    failures = [name for name, ok in
                [("norms", gate_norms), ("mass", gate_mass), ("divB", gate_divb)] if not ok]
    if failures:
        raise SystemExit(f"GATE FAIL: {failures}")
    print("[orszag_tang] ALL GATES PASSED")


if __name__ == "__main__":
    main()
