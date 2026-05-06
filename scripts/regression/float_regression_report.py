#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
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
DEVICE_COLUMNS = [
    "pair_a",
    "pair_b",
    "precision",
    "l1_a_minus_b",
    "linf_a_minus_b",
    "philip_ratio",
    "ulp_max",
    "gate_passed",
    "notes",
]


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


def _l1_norm_diff(a: np.ndarray, b: np.ndarray, dx: float) -> float:
    return float(np.sum(np.abs(a - b)) * dx)


def _precision_dtype(precision: str) -> np.dtype:
    if precision == "double":
        return np.dtype(np.float64)
    if precision == "float":
        return np.dtype(np.float32)
    raise ValueError(f"Unsupported precision={precision!r}; expected 'float' or 'double'")


def _precision_from_tag(precision_tag: int) -> str:
    if precision_tag == 8:
        return "double"
    if precision_tag == 4:
        return "float"
    raise ValueError(f"Unsupported precision_tag={precision_tag}")


def _display_device_path(path: Path) -> str:
    return str(path)


def _is_stationary_contact_pair(cpu_path: Path, gpu_path: Path) -> bool:
    text = " ".join(
        part.lower()
        for path in (cpu_path, gpu_path)
        for part in (*path.parts, path.stem)
    )
    return "stationary_contact" in text or "stationary-contact" in text


def _validate_device_headers(cpu_path: Path, cpu_header, gpu_path: Path, gpu_header) -> None:
    if (cpu_header.nx, cpu_header.ny, cpu_header.nvars) != (
        gpu_header.nx,
        gpu_header.ny,
        gpu_header.nvars,
    ):
        raise ValueError(
            f"Grid shape mismatch: {cpu_path} is "
            f"{cpu_header.nx}x{cpu_header.ny}x{cpu_header.nvars}, "
            f"{gpu_path} is {gpu_header.nx}x{gpu_header.ny}x{gpu_header.nvars}"
        )
    if cpu_header.precision_tag != gpu_header.precision_tag:
        raise ValueError(
            f"Precision mismatch: {cpu_path} tag={cpu_header.precision_tag}, "
            f"{gpu_path} tag={gpu_header.precision_tag}"
        )
    for field in ("dx", "dy", "t"):
        cpu_value = float(getattr(cpu_header, field))
        gpu_value = float(getattr(gpu_header, field))
        if not np.isclose(cpu_value, gpu_value, rtol=0.0, atol=1e-15):
            raise ValueError(
                f"Header mismatch for {field}: {cpu_path} has {cpu_value}, "
                f"{gpu_path} has {gpu_value}"
            )


def _report_device_pair(
    cpu_path: Path,
    gpu_path: Path,
    precision: str | None,
    reference_path: Path | None = None,
    gate_ulp: float | None = None,
) -> dict[str, object]:
    cpu_header, cpu_cons = read_binary(cpu_path)
    gpu_header, gpu_cons = read_binary(gpu_path)
    _validate_device_headers(cpu_path, cpu_header, gpu_path, gpu_header)

    header_precision = _precision_from_tag(cpu_header.precision_tag)
    if precision is not None and precision != header_precision:
        raise ValueError(
            f"precision={precision!r} does not match binary header "
            f"precision={header_precision!r} for {cpu_path}"
        )
    precision = header_precision
    dtype = _precision_dtype(precision)
    cpu = cpu_cons.astype(np.float64, copy=False)
    gpu = gpu_cons.astype(np.float64, copy=False)
    abs_diff = np.abs(cpu - gpu)
    l1 = float(np.mean(abs_diff))
    linf = float(np.max(abs_diff)) if abs_diff.size else 0.0
    linf_a = float(np.max(np.abs(cpu))) if cpu.size else 0.0
    eps = float(np.finfo(dtype).eps)
    ulp_max = _safe_ratio(linf, eps * linf_a)

    notes: list[str] = []
    if gate_ulp is None:
        gate_ulp = 4.0 if _is_stationary_contact_pair(cpu_path, gpu_path) else 16.0
    if gate_ulp != 16.0:
        notes.append(f"gate_ulp={gate_ulp:g}")

    if reference_path is not None and str(reference_path).lower() == "exact":
        cpu_minus_ref_l1: float | None = None
        notes.append("reference_exact_not_available")
    elif reference_path is not None:
        ref_header, ref_cons = read_binary(reference_path)
        if (ref_header.nx, ref_header.ny, ref_header.nvars) != (
            cpu_header.nx,
            cpu_header.ny,
            cpu_header.nvars,
        ):
            raise ValueError(
                f"Reference shape mismatch: {reference_path} is "
                f"{ref_header.nx}x{ref_header.ny}x{ref_header.nvars}, "
                f"{cpu_path} is {cpu_header.nx}x{cpu_header.ny}x{cpu_header.nvars}"
            )
        ref = ref_cons.astype(np.float64, copy=False)
        cpu_minus_ref_l1 = float(np.mean(np.abs(cpu - ref)))
    else:
        cpu_minus_ref_l1 = None
        notes.append("no_reference")

    return {
        "pair_a": _display_device_path(cpu_path),
        "pair_b": _display_device_path(gpu_path),
        "precision": precision,
        "l1_a_minus_b": l1,
        "linf_a_minus_b": linf,
        "philip_ratio": (
            _safe_ratio(l1, cpu_minus_ref_l1)
            if cpu_minus_ref_l1 is not None
            else None
        ),
        "ulp_max": ulp_max,
        "gate_passed": bool(ulp_max <= gate_ulp),
        "notes": ";".join(notes) if notes else "ok",
    }


def _device_pair_label(path: Path) -> str:
    parent = path.parent.name.lower()
    stem = path.stem.lower()
    return parent if ("cpu" in parent or "gpu" in parent) else stem


def _device_pair_key(path: Path) -> str:
    key = _device_pair_label(path)
    for token in ("cpu", "gpu"):
        key = key.replace(token, "")
    return key.replace("__", "_").strip("_-. ")


def _pair_device_inputs(inputs: list[Path]) -> list[tuple[Path, Path]]:
    cpu_paths = [p for p in inputs if "cpu" in _device_pair_label(p)]
    gpu_paths = [p for p in inputs if "gpu" in _device_pair_label(p)]
    if not cpu_paths and not gpu_paths and len(inputs) == 2:
        return [(inputs[0], inputs[1])]
    if len(cpu_paths) == 1 and len(gpu_paths) == 1:
        return [(cpu_paths[0], gpu_paths[0])]
    pairs: list[tuple[Path, Path]] = []
    remaining_gpu = {_device_pair_key(p): p for p in gpu_paths}
    for cpu_path in cpu_paths:
        key = _device_pair_key(cpu_path)
        gpu_path = remaining_gpu.pop(key, None)
        if gpu_path is not None:
            pairs.append((cpu_path, gpu_path))
    if len(pairs) != min(len(cpu_paths), len(gpu_paths)):
        raise ValueError(
            "Could not pair all device inputs by cpu/gpu filename tokens; "
            "use one CPU/GPU pair or names with matching stems"
        )
    return pairs


def _summary_path(prefix: Path, suffix: str) -> Path:
    if prefix.suffix:
        return prefix.with_suffix(suffix)
    return Path(str(prefix) + suffix)


def _write_device_outputs(output_prefix: Path, rows: list[dict[str, object]]) -> dict[str, object]:
    csv_path = _summary_path(output_prefix, ".csv")
    json_path = _summary_path(output_prefix, ".json")
    md_path = _summary_path(output_prefix, ".md")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DEVICE_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: ("n/a" if row.get(key) is None else row.get(key))
                for key in DEVICE_COLUMNS
            })

    summary = {
        "mode": "device",
        "rows": rows,
        "outputs": {
            "csv": str(csv_path),
            "json": str(json_path),
            "markdown": str(md_path),
        },
    }
    _write_text(json_path, json.dumps(summary, indent=2) + "\n")

    md_lines = [
        "# CPU vs GPU Device Regression",
        "",
        "| pair_a | pair_b | precision | l1_a_minus_b | linf_a_minus_b | philip_ratio | ulp_max | gate_passed | notes |",
        "|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        philip = row["philip_ratio"]
        philip_text = (
            f"{float(philip):.6e}"
            if isinstance(philip, (int, float))
            else "n/a"
        )
        md_lines.append(
            f"| {row['pair_a']} | {row['pair_b']} | {row['precision']} | "
            f"{float(row['l1_a_minus_b']):.6e} | {float(row['linf_a_minus_b']):.6e} | "
            f"{philip_text} | {float(row['ulp_max']):.6e} | "
            f"{row['gate_passed']} | {row['notes']} |"
        )
    _write_text(md_path, "\n".join(md_lines) + "\n")
    return summary


def _report_device_pairs(
    pairs: list[tuple[Path, Path]],
    output_prefix: Path,
    precision: str | None,
    reference_path: Path | None = None,
) -> dict[str, object]:
    if not pairs:
        raise ValueError("No CPU/GPU device pairs found")
    rows = [
        _report_device_pair(cpu_path, gpu_path, precision, reference_path)
        for cpu_path, gpu_path in pairs
    ]
    return _write_device_outputs(output_prefix, rows)


def _report_device(
    inputs: list[Path],
    output_prefix: Path,
    precision: str | None,
    reference_path: Path | None = None,
) -> dict[str, object]:
    pairs = _pair_device_inputs(inputs)
    return _report_device_pairs(pairs, output_prefix, precision, reference_path)


def _read_grid_primitive(path: Path, gamma: float) -> tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    """Return (dx, rho, u, p) from a 1D HRSC binary."""
    header, cons = read_binary(path)
    if header.ny != 1:
        raise ValueError(f"{path}: expected 1D dump (ny=1), got ny={header.ny}")
    prim = cons_to_prim(cons.astype(np.float64), gamma)
    return (
        float(header.dx),
        prim[0, :, 0],
        prim[0, :, 1],
        prim[0, :, 3],
    )


def _report_1d(input_dir: Path) -> dict[str, object]:
    per_test: dict[str, object] = {}
    md_lines = [
        "# Float vs Double Regression (1D)",
        "",
        "Two metrics per test are reported side-by-side:",
        "",
        "- **legacy d/f**: `||float - exact||_p / ||double - exact||_p`.",
        "- **philip fmd/d_err**: `||float - double||_1 / ||double - exact||_1`.",
        "",
        "| test | N_last | L1_rho d/f | L2_rho d/f | Linf_rho d/f | L1_u d/f | L2_u d/f | Linf_u d/f | L1_p d/f | L2_p d/f | Linf_p d/f | L1_rho fmd/d_err | L1_u fmd/d_err | L1_p fmd/d_err |",
        "|------|-------:|-----------:|-----------:|-------------:|---------:|---------:|-----------:|---------:|---------:|-----------:|-----------------:|---------------:|---------------:|",
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
        gamma = 1.4
        gd = input_dir / f"{test}_double_grid.bin"
        gf = input_dir / f"{test}_float_grid.bin"
        if not gd.is_file() or not gf.is_file():
            raise FileNotFoundError(f"Missing grid pair for {test}: {gd} / {gf}")
        dx_d, rho_d, u_d, p_d = _read_grid_primitive(gd, gamma)
        dx_f, rho_f, u_f, p_f = _read_grid_primitive(gf, gamma)
        if rho_d.shape != rho_f.shape:
            raise ValueError(f"Grid shape mismatch for {test}: {rho_d.shape} vs {rho_f.shape}")
        if abs(dx_d - dx_f) > max(1e-12, 1e-6 * abs(dx_d)):
            raise ValueError(f"dx mismatch for {test}: {dx_d} vs {dx_f}")
        rho_fmd = _l1_norm_diff(rho_f, rho_d, dx_d)
        u_fmd = _l1_norm_diff(u_f, u_d, dx_d)
        p_fmd = _l1_norm_diff(p_f, p_d, dx_d)
        philip = {
            "L1_rho_fmd": rho_fmd,
            "L1_u_fmd": u_fmd,
            "L1_p_fmd": p_fmd,
            "L1_rho_ratio": _safe_ratio(rho_fmd, r_double["L1_rho"]),
            "L1_u_ratio": _safe_ratio(u_fmd, r_double["L1_u"]),
            "L1_p_ratio": _safe_ratio(p_fmd, r_double["L1_p"]),
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
            "philip": philip,
        }
        md_lines.append(
            f"| {test} | {r_double['N']} | "
            f"{ratios['L1_rho_ratio']:.6e} | {ratios['L2_rho_ratio']:.6e} | {ratios['Linf_rho_ratio']:.6e} | "
            f"{ratios['L1_u_ratio']:.6e} | {ratios['L2_u_ratio']:.6e} | {ratios['Linf_u_ratio']:.6e} | "
            f"{ratios['L1_p_ratio']:.6e} | {ratios['L2_p_ratio']:.6e} | {ratios['Linf_p_ratio']:.6e} | "
            f"{philip['L1_rho_ratio']:.6e} | {philip['L1_u_ratio']:.6e} | {philip['L1_p_ratio']:.6e} |"
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
    # Order matters: each double_NNN precedes its float_NNN twin, so the
    # Philip metric can reuse the double-vs-reference denominator.
    cases = [
        ("double_200", input_dir / "double_200.bin"),
        ("float_200", input_dir / "float_200.bin"),
        ("double_400", input_dir / "double_400.bin"),
        ("float_400", input_dir / "float_400.bin"),
    ]
    md_lines = [
        "# Float vs Double Regression (2D)",
        "",
        "Two metrics per case:",
        "",
        "- **L1_rho** etc.: `||candidate - reference_800_downsampled||_1`.",
        "- **L1_rho fmd/d_err**: `||float - double||_1 / ||double - reference_800_downsampled||_1`.",
        "",
        "| case | L1_rho | L2_rho | Linf_rho | ssim_rho | delta_x_shock | delta_y_shock | L1_rho fmd/d_err | L1_u fmd/d_err | L1_p fmd/d_err |",
        "|------|-------:|-------:|---------:|---------:|--------------:|--------------:|-----------------:|---------------:|---------------:|",
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
        philip_metrics: dict[str, float] = {}
        if label.startswith("float_"):
            res_tag = label.split("_", 1)[1]
            twin_label = f"double_{res_tag}"
            twin_path = input_dir / f"{twin_label}.bin"
            if not twin_path.is_file():
                raise FileNotFoundError(f"Missing double twin for {label}: {twin_path}")
            twin_header, twin_cons = read_binary(twin_path)
            if (twin_header.nx, twin_header.ny) != (cand_header.nx, cand_header.ny):
                raise ValueError(
                    f"Grid shape mismatch for {label}: "
                    f"{cand_header.nx}x{cand_header.ny} vs "
                    f"{twin_header.nx}x{twin_header.ny}"
                )
            twin_prim = cons_to_prim(twin_cons.astype(np.float64), gamma)
            cell_area = float(cand_header.dx * cand_header.dy)
            for var_name, idx in (("rho", 0), ("u", 1), ("v", 2), ("p", 3)):
                fmd = float(np.sum(np.abs(cand_prim[..., idx] - twin_prim[..., idx])) * cell_area)
                philip_metrics[f"L1_{var_name}_fmd"] = fmd
                d_err = float(out_cases[twin_label]["downsample_metrics"][var_name]["L1"])  # type: ignore[index]
                philip_metrics[f"L1_{var_name}_ratio"] = _safe_ratio(fmd, d_err)
        out_cases[label]["philip"] = philip_metrics  # type: ignore[index]
        rho_norms = downsample_metrics["metrics"]["rho"]
        philip = out_cases[label].get("philip", {})  # type: ignore[union-attr]

        def _fmt_philip(key: str) -> str:
            value = philip.get(key)
            return f"{value:.6e}" if isinstance(value, (int, float)) and np.isfinite(value) else "-"

        md_lines.append(
            f"| {label} | {rho_norms['L1']:.6e} | {rho_norms['L2']:.6e} | {rho_norms['Linf']:.6e} | "
            f"{float(phase_metrics['ssim_rho']):.6f} | {float(phase_metrics['delta_x_shock']):.6e} | "
            f"{float(phase_metrics['delta_y_shock']):.6e} | "
            f"{_fmt_philip('L1_rho_ratio')} | {_fmt_philip('L1_u_ratio')} | {_fmt_philip('L1_p_ratio')} |"
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
    p.add_argument("--mode", required=True, choices=("1d", "2d", "fp", "device"))
    p.add_argument("--input", type=Path, help="Input directory for legacy 1d/2d reports")
    p.add_argument("--inputs", nargs="+", type=Path, help="Input binaries for fp/device reports")
    p.add_argument("--cpu", nargs="+", type=Path, help="CPU binary path(s) for device mode")
    p.add_argument("--gpu", nargs="+", type=Path, help="GPU binary path(s) for device mode")
    p.add_argument("--precision", choices=("float", "double"), default=None)
    p.add_argument("--reference", type=Path, help="Optional exact/reference binary")
    p.add_argument("--output", type=Path, help="Output prefix for summary.{csv,json,md}")
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
    if args.mode == "device":
        if args.cpu or args.gpu:
            cpu_paths = args.cpu or []
            gpu_paths = args.gpu or []
            if len(cpu_paths) != len(gpu_paths):
                raise ValueError("--cpu and --gpu must provide the same number of paths")
            if args.output is None:
                raise ValueError("--mode device requires --output")
            summary = _report_device_pairs(
                list(zip(cpu_paths, gpu_paths)),
                args.output,
                args.precision,
                args.reference,
            )
        else:
            inputs = args.inputs or []
            if not inputs:
                raise ValueError("--mode device requires --inputs or --cpu/--gpu")
            if args.output is None:
                raise ValueError("--mode device requires --output")
            summary = _report_device(inputs, args.output, args.precision, args.reference)
    elif args.mode == "fp":
        if args.input is None:
            raise ValueError("--mode fp is a compatibility alias and requires --input")
        summary = _report_1d(args.input)
    elif args.mode == "1d":
        if args.input is None:
            raise ValueError("--mode 1d requires --input")
        summary = _report_1d(args.input)
    else:
        if args.input is None:
            raise ValueError("--mode 2d requires --input")
        summary = _report_2d(args.input, args.gamma, args.smooth_sigma, allow_ssim_fallback)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

