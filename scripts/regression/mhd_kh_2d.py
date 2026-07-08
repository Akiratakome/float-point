#!/usr/bin/env python3
"""Kelvin-Helmholtz 2D MHD validation (Week 13).

Gates:
  1. Self-converged reference: L1/L2/Linf on density (candidate 256^2 vs the
     512^2 double reference block-averaged to 256^2). Must be finite and the
     L1 must be below a coarse sanity ceiling.
  2. Conservation: |mass(t_end) - mass(t0)| / mass(t0) at round-off level,
     using the analytic uniform rho0=1 initial mass.
  3. div(B) floor: glm_cr=0.18 run has finite divB_max below a hard
     ceiling. The glm_cr=0 cleaning ratio is diagnostic only.
  4. Symmetry (reported, not gated): y-reflection residual of density.
"""
from __future__ import annotations

import csv
import argparse
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
BIN = ROOT / "build-double" / "hrsc_mhd"
CFG = ROOT / "tests" / "cases" / "kelvin_helmholtz_2d" / "kh.cfg"
CFG_REF = ROOT / "tests" / "cases" / "kelvin_helmholtz_2d" / "kh_ref.cfg"
OUT = ROOT / "experiments" / "week13" / "kelvin_helmholtz"
GAMMA = 5.0 / 3.0
L1_CEILING = 0.2        # coarse sanity ceiling on L1(rho) (rho0=1)
DIVB_MAX_CEILING = 5.0  # hard gate: divB_max finite and below this
PAPER_NOTE = (
    "Paper anchor: Kelvin-Helmholtz is used here as a 2D ideal-MHD shear-layer "
    "morphology benchmark following Frank et al. 1996. Lecoanet et al. 2015 is "
    "recorded as the limitation anchor: inviscid KH comparisons are sensitive "
    "to perturbations and regularisation, so this packet is bounded morphology "
    "and diagnostic evidence, not a full convergence claim."
)
FIGURE_NAMES = (
    "kh_density_bmag.png",
    "kh_divb.png",
)
# kh_paper_style.png is rendered separately by
# scripts/regression/mhd_paper_style_mk2005.py (matplotlib, density isolines
# in the Dedner-2002 Fig. 8 layout) and is intentionally NOT regenerated here
# so the regression path stays matplotlib-free and does not clobber it.
PAPER_SUMMARY = OUT / "paper_summary.md"


def clear_scalar_summaries() -> None:
    for name in ("summary.csv", "summary.json", "summary.md"):
        path = OUT / name
        if path.exists():
            path.unlink()


def clear_generated_figures() -> None:
    fig_dir = OUT / "figures"
    for name in FIGURE_NAMES:
        path = fig_dir / name
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


def periodic_abs_divb(arr, dx: float, dy: float):
    bx = arr[..., BX].astype(np.float64)
    by = arr[..., BY].astype(np.float64)
    d_bx_dx = (np.roll(bx, -1, axis=1) - np.roll(bx, 1, axis=1)) / (2.0 * dx)
    d_by_dy = (np.roll(by, -1, axis=0) - np.roll(by, 1, axis=0)) / (2.0 * dy)
    return np.abs(d_bx_dx + d_by_dy)


def write_validation_figures(header, arr) -> list[str]:
    from mhd_paper_figures import mhd_primitive, plot_heatmap_panels

    fig_dir = OUT / "figures"
    prim = mhd_primitive(arr.astype(np.float64), GAMMA)
    density = prim["rho"]
    bmag = np.sqrt(prim["Bx"] ** 2 + prim["By"] ** 2 + prim["Bz"] ** 2)
    abs_divb = periodic_abs_divb(arr, header.dx, header.dy)

    paths = [
        plot_heatmap_panels(
            fig_dir / "kh_density_bmag.png",
            [
                {"title": "density", "field": density},
                {"title": "Bmag", "field": bmag},
            ],
            columns=2,
        ),
        plot_heatmap_panels(
            fig_dir / "kh_divb.png",
            [
                {"title": "abs divB log10", "field": abs_divb, "log10": True},
            ],
            columns=1,
        ),
    ]
    return [path.relative_to(ROOT).as_posix() for path in paths]


def import_runtime_helpers() -> None:
    global np, RHO, block_average_2d, conserved_totals, git_commit
    global BX, BY, read_binary, reflect_y_residual, replace_or_append_cfg
    global resolve_binary, run_case, sha256_file

    import numpy as np

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from _mhd_harness import (RHO, BX, BY, block_average_2d, conserved_totals, git_commit,
                              read_binary, reflect_y_residual, replace_or_append_cfg,
                              resolve_binary, run_case, sha256_file)


def load_metadata(path: pathlib.Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_paper_summary(figure_paths: list[str], meta: dict) -> None:
    diag = meta.get("stderr_diagnostics") or {}
    diag_line = diag.get("line", "(diagnostics unavailable)")
    lines = [
        "# Week 13 Kelvin-Helmholtz Paper-Style Figures",
        "",
        PAPER_NOTE,
        "",
        "This packet is generated from the local `256^2` HLL Kelvin-Helmholtz "
        "run using `tests/cases/kelvin_helmholtz_2d/kh.cfg` at `t=1.0`. It is "
        "paper-style morphology evidence and does not claim that the full "
        "`512^2` self-reference validation gate passed.",
        "",
        "## Local run diagnostic",
        "",
        f"`{diag_line}`",
        "",
        "## Figures",
        "",
    ]
    lines.extend(f"- `{path}`" for path in figure_paths)
    lines.extend([
        "",
        "## Pending validation",
        "",
        "The full `mhd_kh_2d.py` validation still requires the `512^2` "
        "self-reference run from `kh_ref.cfg` plus the `glm_cr=0` diagnostic "
        "control. Those runs are intentionally not launched by "
        "`--paper-figures-only`; the `512^2` gate remains pending under the "
        "local runtime policy for this workstation.",
        "",
    ])
    PAPER_SUMMARY.write_text("\n".join(lines), encoding="utf-8")


def paper_figures_only() -> None:
    import_runtime_helpers()
    OUT.mkdir(parents=True, exist_ok=True)
    clear_generated_figures()

    cand_bin = OUT / "kh_256.bin"
    meta_path = OUT / "runs" / "kh_256" / "metadata.json"
    meta = load_metadata(meta_path)
    if not cand_bin.is_file():
        bin_path = resolve_binary(BIN)
        sha, commit = sha256_file(bin_path), git_commit()
        meta = run_grid("kh_256", CFG, cand_bin, bin_path, commit, sha)

    cand_header, cand = read_binary(cand_bin)
    figure_paths = write_validation_figures(cand_header, cand)
    write_paper_summary(figure_paths, meta)
    print(PAPER_SUMMARY.read_text(encoding="utf-8"), end="")


def main() -> None:
    import_runtime_helpers()

    OUT.mkdir(parents=True, exist_ok=True)
    clear_scalar_summaries()

    bin_path = resolve_binary(BIN)
    sha, commit = sha256_file(bin_path), git_commit()

    cand_bin = OUT / "kh_256.bin"
    ref_bin = OUT / "kh_512_ref.bin"
    meta_c = run_grid("kh_256", CFG, cand_bin, bin_path, commit, sha)
    meta_r = run_grid("kh_512_ref", CFG_REF, ref_bin, bin_path, commit, sha)
    meta_ctrl = run_grid("kh_256_cr0", CFG, OUT / "kh_256_cr0.bin", bin_path,
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

    mass_now = conserved_totals(cand, GAMMA)["mass"]
    mass_ic = 1.0 * rho_c.size
    mass_rel = abs(mass_now - mass_ic) / mass_ic

    divb_cand = require_divb_max(meta_c, "kh_256")
    divb_ctrl_raw = require_divb_max(meta_ctrl, "kh_256_cr0")
    if np.isfinite(divb_ctrl_raw):
        divb_ctrl = float(divb_ctrl_raw)
        divb_ctrl_status = "finite"
    else:
        divb_ctrl = None
        divb_ctrl_status = "non-finite"
    sym = reflect_y_residual(rho_c)
    # Diagnostic only: the cr0 control may be zero or non-finite, and coupled
    # nonlinear flow does not guarantee a ratio below one.
    raw_cleaning_ratio = (divb_cand / divb_ctrl) if divb_ctrl else None
    if raw_cleaning_ratio is not None and np.isfinite(raw_cleaning_ratio):
        cleaning_ratio = float(raw_cleaning_ratio)
        cleaning_ratio_status = "finite"
    else:
        cleaning_ratio = None
        cleaning_ratio_status = "undefined"

    gate_norms = np.isfinite([l1, l2, linf]).all() and l1 < L1_CEILING
    gate_mass = mass_rel < 1e-10
    # Hard div(B) gate: finite and below a recorded ceiling.
    gate_divb = bool(np.isfinite(divb_cand) and divb_cand < DIVB_MAX_CEILING)

    results = {"L1_rho": l1, "L2_rho": l2, "Linf_rho": linf, "mass_rel": mass_rel,
               "divB_max_cr018": divb_cand, "divB_max_cr0": divb_ctrl,
               "divB_max_cr0_status": divb_ctrl_status,
               "cleaning_ratio_diagnostic": cleaning_ratio,
               "cleaning_ratio_status": cleaning_ratio_status,
               "reflect_y_residual": sym, "gate_norms": bool(gate_norms),
               "gate_mass": bool(gate_mass), "gate_divb": bool(gate_divb)}

    safe_results = sanitize_scalar_results(results)
    json_payload = {
        "experiment": "week13-kelvin-helmholtz", "git_commit": commit,
        "binary_sha256": sha, "results": safe_results,
        "runs": {"cand": json_safe_run_meta(meta_c),
                 "ref": json_safe_run_meta(meta_r),
                 "ctrl": json_safe_run_meta(meta_ctrl)},
    }
    json_text = json.dumps(json_payload, indent=2, allow_nan=False) + "\n"
    md = [
        "# Week 13 Kelvin-Helmholtz 2D Validation", "",
        "256^2 candidate vs 512^2 double reference (block-averaged), gamma=5/3, t=1.0.", "",
        "| metric | value | gate | pass? |", "|---|---:|---|---:|",
        f"| L1(rho) | {fmt_optional(safe_results['L1_rho'])} | < {L1_CEILING} | {gate_norms} |",
        f"| L2(rho) | {fmt_optional(safe_results['L2_rho'])} | finite | {gate_norms} |",
        f"| Linf(rho) | {fmt_optional(safe_results['Linf_rho'])} | finite | {gate_norms} |",
        f"| mass_rel | {fmt_optional(safe_results['mass_rel'])} | < 1e-10 | {gate_mass} |",
        f"| divB_max | {fmt_optional(safe_results['divB_max_cr018'])} | finite & < {DIVB_MAX_CEILING} | {gate_divb} |",
        f"| divB_max cr0 (diagnostic) | {fmt_optional(safe_results['divB_max_cr0'])} | {divb_ctrl_status} | n/a |",
        f"| cleaning_ratio cr0.18/cr0 (diagnostic) | {fmt_optional(safe_results['cleaning_ratio_diagnostic'])} | "
        f"{cleaning_ratio_status} | n/a |",
        f"| reflect_y_residual (reported) | {fmt_optional(safe_results['reflect_y_residual'])} | n/a | n/a |",
    ]
    md_text = "\n".join(md) + "\n"

    with (OUT / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(safe_results))
        w.writeheader()
        w.writerow(safe_results)
    (OUT / "summary.json").write_text(json_text, encoding="utf-8")
    (OUT / "summary.md").write_text(md_text, encoding="utf-8")
    print(md_text, end="")

    failures = [name for name, ok in
                [("norms", gate_norms), ("mass", gate_mass), ("divB", gate_divb)] if not ok]
    if failures:
        raise SystemExit(f"GATE FAIL: {failures}")
    print("[kelvin_helmholtz] ALL GATES PASSED")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper-figures-only", action="store_true",
                        help="write KH paper-style figures from the 256^2 candidate without claiming the full validation gate")
    args = parser.parse_args()
    if args.paper_figures_only:
        paper_figures_only()
    else:
        main()
