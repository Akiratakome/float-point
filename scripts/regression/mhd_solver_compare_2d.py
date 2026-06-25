#!/usr/bin/env python3
"""HLLD-vs-HLL comparison on Orszag-Tang (Week 13 decision point).

Runs the OT candidate grid with ``riemann=hll`` and ``riemann=hlld``, then
reports the density difference between the two solvers and each solver's
divB floor. HLLD is expected to be less diffusive, so a nonzero difference is
normal; the gate here is only that HLLD stays finite.

NumPy and the shared MHD harness are imported inside ``main`` so this driver
can still be compile-checked on machines where the Python environment is
missing runtime dependencies.
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
BIN = ROOT / "build-double" / "hrsc_mhd"
CFG = ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg"
OUT = ROOT / "experiments" / "week13" / "solver_compare"


def clear_scalar_summaries() -> None:
    for name in ("summary.json", "summary.md"):
        path = OUT / name
        if path.exists():
            path.unlink()


def require_divb_max(meta, label):
    diagnostics = meta.get("stderr_diagnostics") or {}
    if "divB_max" not in diagnostics:
        stderr_path = meta.get("stderr", "<unknown stderr path>")
        raise RuntimeError(f"run '{label}' did not report divB_max; see {stderr_path}")
    return diagnostics["divB_max"]


def sanitize_scalar_results(results):
    safe = {}
    for key, value in results.items():
        if isinstance(value, float) and not math.isfinite(value):
            safe[key] = None
            safe[f"{key}_status"] = "non-finite"
        else:
            safe[key] = value
    return safe


def json_safe_run_meta(meta):
    safe = dict(meta)
    diagnostics = dict(safe.get("stderr_diagnostics") or {})
    for key, value in diagnostics.items():
        if isinstance(value, float) and not math.isfinite(value):
            diagnostics[key] = None
    safe["stderr_diagnostics"] = diagnostics
    return safe


def fmt_optional(value) -> str:
    return "n/a" if value is None else f"{value:.3e}"


def run_solver(riemann, bin_path, commit, sha):
    out_bin = OUT / f"ot_256_{riemann}.bin"
    out_bin.parent.mkdir(parents=True, exist_ok=True)
    if out_bin.exists():
        out_bin.unlink()
    text = CFG.read_text(encoding="utf-8")
    text = replace_or_append_cfg(text, "output_format", "binary")
    text = replace_or_append_cfg(text, "output_file", str(out_bin))
    text = replace_or_append_cfg(text, "riemann", riemann)
    _, meta, _ = run_case(f"ot_{riemann}", text, OUT / "runs" / riemann, bin_path, CFG,
                          commit, sha, output_bin=out_bin,
                          experiment="week13-solver-compare")
    _, arr = read_binary(out_bin)
    return meta, arr


def main() -> None:
    global np, RHO, git_commit, read_binary, replace_or_append_cfg
    global resolve_binary, run_case, sha256_file

    OUT.mkdir(parents=True, exist_ok=True)
    clear_scalar_summaries()

    import numpy as np

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from _mhd_harness import (RHO, git_commit, read_binary, replace_or_append_cfg,
                              resolve_binary, run_case, sha256_file)

    bin_path = resolve_binary(BIN)
    sha, commit = sha256_file(bin_path), git_commit()

    meta_hll, a_hll = run_solver("hll", bin_path, commit, sha)
    meta_hlld, a_hlld = run_solver("hlld", bin_path, commit, sha)

    rho_hll = a_hll[..., RHO].astype(np.float64)
    rho_hlld = a_hlld[..., RHO].astype(np.float64)
    diff = rho_hlld - rho_hll
    linf = float(np.abs(diff).max())
    l1 = float(np.abs(diff).sum() / diff.size)
    finite = bool(np.isfinite(rho_hlld).all())

    results = {
        "L1_rho_hlld_vs_hll": l1,
        "Linf_rho_hlld_vs_hll": linf,
        "divB_max_hll": require_divb_max(meta_hll, "ot_hll"),
        "divB_max_hlld": require_divb_max(meta_hlld, "ot_hlld"),
        "hlld_finite": finite,
        "steps_hll": meta_hll["stderr_diagnostics"].get("steps"),
        "steps_hlld": meta_hlld["stderr_diagnostics"].get("steps"),
    }
    safe_results = sanitize_scalar_results(results)
    json_payload = {
        "experiment": "week13-solver-compare",
        "git_commit": commit,
        "binary_sha256": sha,
        "results": safe_results,
        "runs": {
            "hll": json_safe_run_meta(meta_hll),
            "hlld": json_safe_run_meta(meta_hlld),
        },
    }
    json_text = json.dumps(json_payload, indent=2, allow_nan=False) + "\n"
    md = [
        "# Week 13 HLLD-vs-HLL Comparison (Orszag-Tang 256^2, t=0.5)",
        "",
        "| metric | value |",
        "|---|---:|",
        f"| L1(rho) HLLD-HLL | {fmt_optional(safe_results['L1_rho_hlld_vs_hll'])} |",
        f"| Linf(rho) HLLD-HLL | {fmt_optional(safe_results['Linf_rho_hlld_vs_hll'])} |",
        f"| divB_max HLL | {fmt_optional(safe_results['divB_max_hll'])} |",
        f"| divB_max HLLD | {fmt_optional(safe_results['divB_max_hlld'])} |",
        f"| HLLD finite | {finite} |",
        f"| steps HLL | {safe_results['steps_hll']} |",
        f"| steps HLLD | {safe_results['steps_hlld']} |",
        "",
        "## Decision",
        "",
        "- [ ] HLLD validated and adopted for remaining MHD work, OR",
        "- [ ] HLLD deferred; HLL remains the production solver (fallback per overall.md).",
        "",
        "Record the chosen option and rationale here and in week13-summary.md.",
    ]
    md_text = "\n".join(md) + "\n"

    (OUT / "summary.json").write_text(json_text, encoding="utf-8")
    (OUT / "summary.md").write_text(md_text, encoding="utf-8")
    print(md_text, end="")
    if not finite:
        raise SystemExit("GATE FAIL: HLLD produced a non-finite Orszag-Tang field")
    print("[solver_compare] HLLD finite; comparison written.")


if __name__ == "__main__":
    main()
