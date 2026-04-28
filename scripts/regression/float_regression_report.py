#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

_SCRIPTS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SCRIPTS_ROOT))               # io_helper at scripts/ root
sys.path.insert(0, str(_SCRIPTS_ROOT / "metrics"))   # downsample_2d, phase_error_metrics
from downsample_2d import compare_candidate_to_reference, downsample_conserved
from io_helper import cons_to_prim, read_binary
from phase_error_metrics import compute_phase_metrics_from_primitive

TESTS_1D = ("sod", "toro2", "toro3", "toro4", "toro5", "stationary_contact")


def _parse_convergence_table(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            cols = line.split()
            if len(cols) < 11:
                raise ValueError(f"Malformed convergence row in {path}: {line}")
            rows.append(
                {
                    "N": int(cols[0]),
                    "L1_rho": float(cols[2]),
                    "L2_rho": float(cols[3]),
                    "Linf_rho": float(cols[4]),
                    "L1_u": float(cols[5]),
                    "L2_u": float(cols[6]),
                    "Linf_u": float(cols[7]),
                    "L1_p": float(cols[8]),
                    "L2_p": float(cols[9]),
                    "Linf_p": float(cols[10]),
                }
            )
    if not rows:
        raise ValueError(f"No convergence data found in {path}")
    return rows


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _safe_ratio(num: float, den: float) -> float:
    if den == 0.0:
        return 1.0 if num == 0.0 else float("inf")
    return num / den


def _report_1d(input_dir: Path) -> dict[str, object]:
    per_test: dict[str, dict[str, float]] = {}
    md_lines = [
        "# Float vs Double Regression (1D)",
        "",
        "| test | N_last | L1_rho d/f | L2_rho d/f | Linf_rho d/f | L1_u d/f | L2_u d/f | Linf_u d/f | L1_p d/f | L2_p d/f | Linf_p d/f |",
        "|------|-------:|------------:|------------:|--------------:|---------:|---------:|-----------:|---------:|---------:|-----------:|",
    ]
    for test in TESTS_1D:
        p_double = input_dir / f"{test}_double.csv"
        p_float = input_dir / f"{test}_float.csv"
        if not p_double.is_file() or not p_float.is_file():
            raise FileNotFoundError(f"Missing pair for {test}: {p_double} / {p_float}")
        r_double = _parse_convergence_table(p_double)[-1]
        r_float = _parse_convergence_table(p_float)[-1]
        if r_double["N"] != r_float["N"]:
            raise ValueError(f"Final N mismatch for {test}: {r_double['N']} vs {r_float['N']}")
        ratios = {
            "L1_rho_ratio": _safe_ratio(r_float["L1_rho"], r_double["L1_rho"]),
            "L2_rho_ratio": _safe_ratio(r_float["L2_rho"], r_double["L2_rho"]),
            "Linf_rho_ratio": _safe_ratio(r_float["Linf_rho"], r_double["Linf_rho"]),
            "L1_u_ratio": _safe_ratio(r_float["L1_u"], r_double["L1_u"]),
            "L2_u_ratio": _safe_ratio(r_float["L2_u"], r_double["L2_u"]),
            "Linf_u_ratio": _safe_ratio(r_float["Linf_u"], r_double["Linf_u"]),
            "L1_p_ratio": _safe_ratio(r_float["L1_p"], r_double["L1_p"]),
            "L2_p_ratio": _safe_ratio(r_float["L2_p"], r_double["L2_p"]),
            "Linf_p_ratio": _safe_ratio(r_float["Linf_p"], r_double["Linf_p"]),
        }
        per_test[test] = {
            "N_last": r_double["N"],
            "double": {
                "L1_rho": r_double["L1_rho"],
                "L2_rho": r_double["L2_rho"],
                "Linf_rho": r_double["Linf_rho"],
                "L1_u": r_double["L1_u"],
                "L2_u": r_double["L2_u"],
                "Linf_u": r_double["Linf_u"],
                "L1_p": r_double["L1_p"],
                "L2_p": r_double["L2_p"],
                "Linf_p": r_double["Linf_p"],
            },
            "float": {
                "L1_rho": r_float["L1_rho"],
                "L2_rho": r_float["L2_rho"],
                "Linf_rho": r_float["Linf_rho"],
                "L1_u": r_float["L1_u"],
                "L2_u": r_float["L2_u"],
                "Linf_u": r_float["Linf_u"],
                "L1_p": r_float["L1_p"],
                "L2_p": r_float["L2_p"],
                "Linf_p": r_float["Linf_p"],
            },
            "ratio_float_over_double": ratios,
        }
        md_lines.append(
            f"| {test} | {r_double['N']} | {ratios['L1_rho_ratio']:.3f} | {ratios['L2_rho_ratio']:.3f} | {ratios['Linf_rho_ratio']:.3f} | "
            f"{ratios['L1_u_ratio']:.3f} | {ratios['L2_u_ratio']:.3f} | {ratios['Linf_u_ratio']:.3f} | "
            f"{ratios['L1_p_ratio']:.3f} | {ratios['L2_p_ratio']:.3f} | {ratios['Linf_p_ratio']:.3f} |"
        )
    summary = {"mode": "1d", "input_dir": str(input_dir), "tests": per_test}
    _write_text(input_dir / "summary.md", "\n".join(md_lines) + "\n")
    _write_text(input_dir / "summary.json", json.dumps(summary, indent=2) + "\n")
    return summary


def _report_2d(input_dir: Path, gamma: float, smooth_sigma: float, allow_ssim_fallback: bool) -> dict[str, object]:
    ref_path = input_dir / "reference_800.bin"
    if not ref_path.is_file():
        raise FileNotFoundError(f"Missing reference binary: {ref_path}")
    ref_header, ref_cons = read_binary(ref_path)
    ref_cons_f64 = ref_cons.astype(np.float64)
    cases = [
        ("double_200", input_dir / "double_200.bin"),
        ("float_200", input_dir / "float_200.bin"),
        ("double_400", input_dir / "double_400.bin"),
        ("float_400", input_dir / "float_400.bin"),
    ]
    md_lines = [
        "# Float vs Double Regression (2D)",
        "",
        "| case | L1_rho | L2_rho | Linf_rho | ssim_rho | delta_x_shock | delta_y_shock |",
        "|------|-------:|-------:|---------:|---------:|--------------:|--------------:|",
    ]
    out_cases: dict[str, object] = {}
    any_ssim_fallback = False
    heatmap_root = input_dir / "phase_error_heatmaps"
    for label, cand_path in cases:
        if not cand_path.is_file():
            raise FileNotFoundError(f"Missing candidate binary: {cand_path}")
        cand_header, cand_cons = read_binary(cand_path)
        if ref_header.nx % cand_header.nx != 0 or ref_header.ny % cand_header.ny != 0:
            raise ValueError(
                f"Reference {ref_header.nx}x{ref_header.ny} not integer-multiple of "
                f"{cand_header.nx}x{cand_header.ny} for {label}"
            )
        downsample_metrics = compare_candidate_to_reference(cand_path, ref_path, gamma)
        ref_down_cons = downsample_conserved(ref_cons_f64, cand_header.nx, cand_header.ny)
        cand_prim = cons_to_prim(cand_cons.astype(np.float64), gamma)
        ref_down_prim = cons_to_prim(ref_down_cons, gamma)
        phase_metrics = compute_phase_metrics_from_primitive(
            cand_prim,
            ref_down_prim,
            cand_header.dx,
            cand_header.dy,
            smooth_sigma,
            allow_ssim_fallback,
            heatmap_root / label,
            label,
        )
        any_ssim_fallback = any_ssim_fallback or bool(phase_metrics.get("ssim_fallback_used", False))
        out_cases[label] = {
            "candidate_file": str(cand_path),
            "downsample_metrics": downsample_metrics["metrics"],
            "phase_metrics": phase_metrics,
        }
        rho_norms = downsample_metrics["metrics"]["rho"]
        md_lines.append(
            f"| {label} | {rho_norms['L1']:.6e} | {rho_norms['L2']:.6e} | {rho_norms['Linf']:.6e} | "
            f"{float(phase_metrics['ssim_rho']):.6f} | {float(phase_metrics['delta_x_shock']):.6e} | "
            f"{float(phase_metrics['delta_y_shock']):.6e} |"
        )
    md_lines.extend(["", "## Difference heatmaps", ""])
    for label, _cand_path in cases:
        case_obj = out_cases[label]
        phase = case_obj["phase_metrics"]  # type: ignore[index]
        heatmaps = phase.get("difference_heatmaps", {})  # type: ignore[union-attr]
        md_lines.append(f"- {label}:")
        for var_name in ("rho", "u", "v", "p"):
            path = heatmaps.get(var_name)
            if path is not None:
                md_lines.append(f"  - {var_name}: `{path}`")
    if any_ssim_fallback:
        md_lines = [
            "**WARN:** scikit-image unavailable in at least one case; SSIM is marked as NaN and only L1/L2/Linf + heatmaps are authoritative.",
            "",
        ] + md_lines
    summary = {
        "mode": "2d",
        "input_dir": str(input_dir),
        "reference_file": str(ref_path),
        "ssim_fallback_used": any_ssim_fallback,
        "cases": out_cases,
    }
    _write_text(input_dir / "summary.md", "\n".join(md_lines) + "\n")
    _write_text(input_dir / "summary.json", json.dumps(summary, indent=2) + "\n")
    return summary


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Float-vs-double regression summary generator.")
    p.add_argument("--mode", required=True, choices=("1d", "2d"))
    p.add_argument("--input", required=True, type=Path, help="Input directory")
    p.add_argument("--gamma", type=float, default=1.4)
    p.add_argument("--smooth-sigma", type=float, default=0.5)
    p.add_argument(
        "--allow-ssim-fallback",
        action="store_true",
        help="Deprecated alias. Fallback is enabled by default; use --no-ssim-fallback to disable.",
    )
    p.add_argument("--no-ssim-fallback", action="store_true")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    allow_ssim_fallback = True
    if args.no_ssim_fallback:
        allow_ssim_fallback = False
    elif args.allow_ssim_fallback:
        allow_ssim_fallback = True
    if args.mode == "1d":
        summary = _report_1d(args.input)
    else:
        summary = _report_2d(args.input, args.gamma, args.smooth_sigma, allow_ssim_fallback)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

