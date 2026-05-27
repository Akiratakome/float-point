"""Generate clearer Report 1 Direction-2 figures from existing artefacts.

Outputs:
  1. float/double drift divided by double/reference discretisation error.
  2. LoSoS rho distribution quantiles (q05, q25, median) for p8/p16/p32.
  3. sigma_FP_L1 versus precision bits for HLLC and Rusanov.

The script intentionally consumes existing experiment products only. It does not
run the solver or modify any cfg defaults.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "metrics"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from io_helper import cons_to_prim, read_binary  # noqa: E402
from losos_metric import compute_losos_fields, _var_floor  # noqa: E402
from downsample_2d import downsample_conserved  # noqa: E402
from _style import apply, PALETTE, DIVERGING_CMAP, SEQUENTIAL_CMAP, save_pair  # noqa: E402

apply()


VAR_ORDER = ("rho", "u", "v", "p")
VAR_INDEX = {name: i for i, name in enumerate(VAR_ORDER)}
PRECISION_BITS = {
    "p8": 8,
    "p16": 16,
    "p24-real-float": 24,
    "p32": 32,
    "p53": 53,
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _sample_paths(root: Path, precision: str, solver: str, limit: int | None) -> list[Path]:
    paths = sorted((root / precision / solver).glob("sample_*/grid.bin"))
    if limit is not None:
        paths = paths[:limit]
    if not paths:
        raise FileNotFoundError(f"No sample_*/grid.bin files under {root / precision / solver}")
    return paths


def _stack_primitive(paths: list[Path], gamma: float) -> np.ndarray:
    header0, arr0 = read_binary(paths[0])
    out = np.empty((len(paths), header0.ny, header0.nx, header0.nvars), dtype=np.float64)
    out[0] = arr0.astype(np.float64)
    for idx, path in enumerate(paths[1:], start=1):
        header, arr = read_binary(path)
        if (header.nx, header.ny, header.nvars, header.precision_tag) != (
            header0.nx,
            header0.ny,
            header0.nvars,
            header0.precision_tag,
        ):
            raise ValueError(f"Sample shape/type mismatch: {path} vs {paths[0]}")
        out[idx] = arr.astype(np.float64)
    return cons_to_prim(out, gamma)


def build_fmd_rows(summary_json: Path) -> list[dict[str, float | str]]:
    data = json.loads(summary_json.read_text(encoding="utf-8"))
    rows: list[dict[str, float | str]] = []
    for case, payload in data["cases"].items():
        if not case.startswith("float_"):
            continue
        resolution = int(case.split("_", 1)[1])
        philip = payload.get("philip", {})
        for var in VAR_ORDER:
            key = f"L1_{var}_ratio"
            if key not in philip:
                continue
            rows.append(
                {
                    "resolution": resolution,
                    "variable": var,
                    "ratio": float(philip[key]),
                }
            )
    return rows


def write_fmd_csv(rows: list[dict[str, float | str]], out_path: Path) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["resolution", "variable", "ratio"])
        writer.writeheader()
        writer.writerows(rows)


def plot_fmd_bar(rows: list[dict[str, float | str]], out_path: Path) -> None:
    variables = ["rho", "u", "v", "p"]
    resolutions = sorted({int(row["resolution"]) for row in rows})
    lookup = {
        (int(row["resolution"]), str(row["variable"])): float(row["ratio"])
        for row in rows
    }
    x = np.arange(len(variables))
    width = 0.36
    resolution_colors = [PALETTE["fp64"], PALETTE["fp32"]]

    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    for offset_idx, resolution in enumerate(resolutions):
        values = [lookup[(resolution, var)] for var in variables]
        offset = (offset_idx - (len(resolutions) - 1) / 2) * width
        color = resolution_colors[offset_idx % len(resolution_colors)]
        ax.bar(x + offset, values, width=width, label=f"N={resolution}", color=color)

    ax.set_yscale("log")
    ax.set_xticks(x, variables)
    ax.set_ylabel(
        r"$\|U_{\mathrm{fp32}}-U_{\mathrm{fp64}}\|_1"
        r"/\|U_{\mathrm{fp64}}-U_{\mathrm{ref}}\|_1$"
    )
    ax.set_xlabel("primitive variable")
    ax.set_title("Precision difference relative to discretisation error")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    save_pair(fig, out_path.stem, str(out_path.parent))
    plt.close(fig)


def _load_reference(ref_npz: Path) -> tuple[np.ndarray, np.ndarray]:
    with np.load(ref_npz) as data:
        return data["u_ref_hllc"].astype(np.float64), data["u_ref_rusanov"].astype(np.float64)


def build_losos_quantile_rows(
    sweep_root: Path,
    ref_npz: Path,
    gamma: float,
) -> list[dict[str, float | str | int]]:
    ref_hllc, ref_rusanov = _load_reference(ref_npz)
    rows: list[dict[str, float | str | int]] = []

    for precision in ("p8", "p16", "p32"):
        # Use the common subset so HLLC and Rusanov sample counts match.
        counts = {
            solver: len(sorted((sweep_root / precision / solver).glob("sample_*/grid.bin")))
            for solver in ("hllc", "rusanov")
        }
        common_n = min(counts.values())
        for solver, ref in (("hllc", ref_hllc), ("rusanov", ref_rusanov)):
            paths = _sample_paths(sweep_root, precision, solver, common_n)
            prim = _stack_primitive(paths, gamma)
            rho_samples = prim[..., VAR_INDEX["rho"]]
            rho_ref = ref[..., VAR_INDEX["rho"]]
            floor = _var_floor(rho_ref)
            _, _, s_worst = compute_losos_fields(rho_samples, rho_ref, floor)
            if s_worst is None:
                raise RuntimeError("LoSoS worst field was not computed")
            rows.append(
                {
                    "solver": solver,
                    "precision": precision,
                    "precision_bits": PRECISION_BITS[precision],
                    "variable": "rho",
                    "q05": float(np.percentile(s_worst, 5)),
                    "q25": float(np.percentile(s_worst, 25)),
                    "median": float(np.percentile(s_worst, 50)),
                    "mean": float(np.mean(s_worst)),
                    "n_samples": common_n,
                }
            )
    return rows


def _region_masks_from_reference(ref_prim: np.ndarray) -> dict[str, np.ndarray]:
    """Classify cells by density-gradient strength.

    The labels are intentionally descriptive rather than physical absolutes:
    smooth is the lower 70% of |grad rho|, transition is 70-95%, and
    discontinuity band is the strongest 5% of density gradients.
    """
    rho = ref_prim[..., VAR_INDEX["rho"]]
    gy, gx = np.gradient(rho)
    grad = np.sqrt(gx * gx + gy * gy)
    q70 = float(np.percentile(grad, 70))
    q95 = float(np.percentile(grad, 95))
    return {
        "smooth_grad_p00_p70": grad <= q70,
        "transition_grad_p70_p95": (grad > q70) & (grad <= q95),
        "discontinuity_grad_p95_p100": grad > q95,
    }


def _masked_l1(diff: np.ndarray, mask: np.ndarray) -> float:
    if not np.any(mask):
        return float("nan")
    return float(np.mean(np.abs(diff[mask])))


def build_region_fmd_rows(summary_json: Path, gamma: float) -> list[dict[str, float | str | int]]:
    """Compute float/double drift ratios separately by reference-gradient region."""
    data = json.loads(summary_json.read_text(encoding="utf-8"))
    reference_file = REPO_ROOT / data["reference_file"]
    _, ref_cons = read_binary(reference_file)

    rows: list[dict[str, float | str | int]] = []
    for resolution in (200, 400):
        double_case = data["cases"][f"double_{resolution}"]
        float_case = data["cases"][f"float_{resolution}"]
        double_file = REPO_ROOT / double_case["candidate_file"]
        float_file = REPO_ROOT / float_case["candidate_file"]
        h_double, cons_double = read_binary(double_file)
        h_float, cons_float = read_binary(float_file)
        if (h_double.nx, h_double.ny) != (h_float.nx, h_float.ny):
            raise ValueError(f"Shape mismatch for N={resolution} float/double candidates")

        ref_down_cons = downsample_conserved(ref_cons.astype(np.float64), h_double.nx, h_double.ny)
        ref_prim = cons_to_prim(ref_down_cons, gamma)
        double_prim = cons_to_prim(cons_double.astype(np.float64), gamma)
        float_prim = cons_to_prim(cons_float.astype(np.float64), gamma)
        masks = _region_masks_from_reference(ref_prim)

        for region, mask in masks.items():
            for var, idx in VAR_INDEX.items():
                fmd = _masked_l1(float_prim[..., idx] - double_prim[..., idx], mask)
                d_err = _masked_l1(double_prim[..., idx] - ref_prim[..., idx], mask)
                ratio = fmd / d_err if d_err > 0 else float("inf")
                rows.append(
                    {
                        "resolution": resolution,
                        "region": region,
                        "variable": var,
                        "n_cells": int(np.count_nonzero(mask)),
                        "float_double_l1": fmd,
                        "double_reference_l1": d_err,
                        "ratio": ratio,
                    }
                )
    return rows


def write_region_fmd_csv(rows: list[dict[str, float | str | int]], out_path: Path) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "resolution",
                "region",
                "variable",
                "n_cells",
                "float_double_l1",
                "double_reference_l1",
                "ratio",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def plot_region_fmd(rows: list[dict[str, float | str | int]], out_path: Path) -> None:
    regions = [
        "smooth_grad_p00_p70",
        "transition_grad_p70_p95",
        "discontinuity_grad_p95_p100",
    ]
    short = {
        "smooth_grad_p00_p70": "smooth\n0-70%",
        "transition_grad_p70_p95": "transition\n70-95%",
        "discontinuity_grad_p95_p100": "fronts\n95-100%",
    }
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    for ax, resolution in zip(axes, (200, 400)):
        group = [
            row
            for row in rows
            if int(row["resolution"]) == resolution and str(row["variable"]) == "rho"
        ]
        lookup = {str(row["region"]): float(row["ratio"]) for row in group}
        ax.bar([short[r] for r in regions], [lookup[r] for r in regions], color=PALETTE["fp64"])
        ax.set_yscale("log")
        ax.set_title(f"N={resolution}, rho")
        ax.set_xlabel("reference-density gradient region")
        ax.grid(True, axis="y", alpha=0.3)
    axes[0].set_ylabel(r"$||float-double||_1 / ||double-reference||_1$")
    fig.suptitle("Precision drift by spatial region")
    fig.tight_layout()
    save_pair(fig, out_path.stem, str(out_path.parent))
    plt.close(fig)


def build_region_losos_rows(
    sweep_root: Path,
    ref_npz: Path,
    pareto_csv: Path,
    gamma: float,
) -> list[dict[str, float | str | int]]:
    """Compute rho LoSoS quantiles and margin by reference-gradient region."""
    ref_hllc, ref_rusanov = _load_reference(ref_npz)
    s_req_by_solver = {
        row["solver"]: float(row["s_req"])
        for row in _read_csv(pareto_csv)
        if row["precision_label"] == "p16"
    }
    rows: list[dict[str, float | str | int]] = []
    for precision in ("p8", "p16", "p32"):
        counts = {
            solver: len(sorted((sweep_root / precision / solver).glob("sample_*/grid.bin")))
            for solver in ("hllc", "rusanov")
        }
        common_n = min(counts.values())
        for solver, ref in (("hllc", ref_hllc), ("rusanov", ref_rusanov)):
            paths = _sample_paths(sweep_root, precision, solver, common_n)
            prim = _stack_primitive(paths, gamma)
            rho_samples = prim[..., VAR_INDEX["rho"]]
            rho_ref = ref[..., VAR_INDEX["rho"]]
            floor = _var_floor(rho_ref)
            _, _, s_worst = compute_losos_fields(rho_samples, rho_ref, floor)
            if s_worst is None:
                raise RuntimeError("LoSoS worst field was not computed")
            masks = _region_masks_from_reference(ref)
            s_req = s_req_by_solver[solver]
            for region, mask in masks.items():
                values = s_worst[mask]
                q05 = float(np.percentile(values, 5))
                q25 = float(np.percentile(values, 25))
                median = float(np.percentile(values, 50))
                rows.append(
                    {
                        "solver": solver,
                        "precision": precision,
                        "precision_bits": PRECISION_BITS[precision],
                        "region": region,
                        "variable": "rho",
                        "n_cells": int(np.count_nonzero(mask)),
                        "n_samples": common_n,
                        "q05": q05,
                        "q25": q25,
                        "median": median,
                        "s_req": s_req,
                        "median_margin": median - s_req,
                        "q25_margin": q25 - s_req,
                    }
                )
    return rows


def build_noise_ratio_rows(
    sweep_root: Path,
    ref_npz: Path,
    gamma: float,
) -> tuple[list[dict[str, float | str | int]], dict[tuple[str, str], np.ndarray]]:
    """Compute per-cell sigma_FP / |mean-reference| for rho.

    Returns scalar distribution rows for p8/p16/p32 and retains p32 fields for
    report-facing 2D heatmaps.
    """
    ref_hllc, ref_rusanov = _load_reference(ref_npz)
    rows: list[dict[str, float | str | int]] = []
    fields: dict[tuple[str, str], np.ndarray] = {}

    for precision in ("p8", "p16", "p32"):
        counts = {
            solver: len(sorted((sweep_root / precision / solver).glob("sample_*/grid.bin")))
            for solver in ("hllc", "rusanov")
        }
        common_n = min(counts.values())
        for solver, ref in (("hllc", ref_hllc), ("rusanov", ref_rusanov)):
            paths = _sample_paths(sweep_root, precision, solver, common_n)
            prim = _stack_primitive(paths, gamma)
            rho_samples = prim[..., VAR_INDEX["rho"]]
            rho_ref = ref[..., VAR_INDEX["rho"]]
            mu = rho_samples.mean(axis=0)
            sigma = rho_samples.std(axis=0, ddof=1)
            disc = np.abs(mu - rho_ref)
            floor = _var_floor(rho_ref)
            ratio = sigma / np.maximum(disc, floor)
            ratio = np.nan_to_num(ratio, nan=0.0, posinf=1e20, neginf=0.0)
            positive = ratio[ratio > 0.0]
            log_ratio = np.log10(positive) if positive.size else np.array([float("-inf")])
            fields[(solver, precision)] = ratio
            rows.append(
                {
                    "solver": solver,
                    "precision": precision,
                    "precision_bits": PRECISION_BITS[precision],
                    "variable": "rho",
                    "n_samples": common_n,
                    "n_cells": int(ratio.size),
                    "median_log10_ratio": float(np.median(log_ratio)),
                    "q05_log10_ratio": float(np.percentile(log_ratio, 5)),
                    "q95_log10_ratio": float(np.percentile(log_ratio, 95)),
                    "fraction_ratio_gt_1": float(np.mean(ratio > 1.0)),
                    "fraction_ratio_gt_0p01": float(np.mean(ratio > 0.01)),
                }
            )
    return rows, fields


def build_region_noise_ratio_rows(
    sweep_root: Path,
    ref_npz: Path,
    gamma: float,
) -> list[dict[str, float | str | int]]:
    """Compute sigma_FP / |mean-reference| summaries by gradient region."""
    ref_hllc, ref_rusanov = _load_reference(ref_npz)
    rows: list[dict[str, float | str | int]] = []

    for precision in ("p8", "p16", "p32"):
        counts = {
            solver: len(sorted((sweep_root / precision / solver).glob("sample_*/grid.bin")))
            for solver in ("hllc", "rusanov")
        }
        common_n = min(counts.values())
        for solver, ref in (("hllc", ref_hllc), ("rusanov", ref_rusanov)):
            paths = _sample_paths(sweep_root, precision, solver, common_n)
            prim = _stack_primitive(paths, gamma)
            rho_samples = prim[..., VAR_INDEX["rho"]]
            rho_ref = ref[..., VAR_INDEX["rho"]]
            mu = rho_samples.mean(axis=0)
            sigma = rho_samples.std(axis=0, ddof=1)
            disc = np.abs(mu - rho_ref)
            floor = _var_floor(rho_ref)
            ratio = sigma / np.maximum(disc, floor)
            ratio = np.nan_to_num(ratio, nan=0.0, posinf=1e20, neginf=0.0)
            masks = _region_masks_from_reference(ref)

            for region, mask in masks.items():
                region_ratio = ratio[mask]
                positive = region_ratio[region_ratio > 0.0]
                log_ratio = (
                    np.log10(positive) if positive.size else np.array([float("-inf")])
                )
                rows.append(
                    {
                        "solver": solver,
                        "precision": precision,
                        "precision_bits": PRECISION_BITS[precision],
                        "region": region,
                        "variable": "rho",
                        "n_samples": common_n,
                        "n_cells": int(np.count_nonzero(mask)),
                        "median_log10_ratio": float(np.median(log_ratio)),
                        "q05_log10_ratio": float(np.percentile(log_ratio, 5)),
                        "q95_log10_ratio": float(np.percentile(log_ratio, 95)),
                        "fraction_ratio_gt_1": float(np.mean(region_ratio > 1.0)),
                        "fraction_ratio_gt_0p01": float(np.mean(region_ratio > 0.01)),
                    }
                )
    return rows


def write_noise_ratio_csv(rows: list[dict[str, float | str | int]], out_path: Path) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "solver",
                "precision",
                "precision_bits",
                "region",
                "variable",
                "n_samples",
                "n_cells",
                "median_log10_ratio",
                "q05_log10_ratio",
                "q95_log10_ratio",
                "fraction_ratio_gt_1",
                "fraction_ratio_gt_0p01",
            ],
        )
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out.setdefault("region", "whole_domain")
            writer.writerow(out)


def plot_noise_ratio_heatmap(
    fields: dict[tuple[str, str], np.ndarray],
    out_path: Path,
    precision: str = "p32",
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), constrained_layout=True)
    images = []
    for ax, solver in zip(axes, ("hllc", "rusanov")):
        ratio = fields[(solver, precision)]
        log_ratio = np.log10(np.clip(ratio, 1e-20, 1e20))
        im = ax.imshow(log_ratio, origin="lower", cmap=DIVERGING_CMAP, vmin=-8, vmax=2)
        images.append(im)
        ax.contour(log_ratio >= 0.0, levels=[0.5], colors="black", linewidths=0.4)
        ax.set_title(f"{solver.upper()} {precision} rho")
        ax.set_xticks([])
        ax.set_yticks([])
        frac = float(np.mean(ratio > 1.0))
        ax.text(
            0.02,
            0.98,
            f"ratio > 1: {100.0 * frac:.2f}%",
            transform=ax.transAxes,
            va="top",
            ha="left",
            fontsize=8,
            bbox=dict(facecolor="white", alpha=0.75, edgecolor="none"),
        )
    cbar = fig.colorbar(images[0], ax=axes, shrink=0.88)
    cbar.set_label(r"$\log_{10}(\sigma_{FP}/|\bar{\rho}-\rho_{ref}|)$")
    fig.suptitle(f"Full-domain noise-to-error ratio ({precision})")
    save_pair(fig, out_path.stem, str(out_path.parent))
    plt.close(fig)


def plot_noise_ratio_heatmap_grid(
    fields: dict[tuple[str, str], np.ndarray],
    out_path: Path,
) -> None:
    precisions = ("p8", "p16", "p32")
    solvers = ("hllc", "rusanov")
    fig, axes = plt.subplots(
        len(solvers),
        len(precisions),
        figsize=(12.5, 7.2),
        constrained_layout=True,
    )
    im = None
    for row_idx, solver in enumerate(solvers):
        for col_idx, precision in enumerate(precisions):
            ax = axes[row_idx, col_idx]
            ratio = fields[(solver, precision)]
            log_ratio = np.log10(np.clip(ratio, 1e-20, 1e20))
            im = ax.imshow(log_ratio, origin="lower", cmap=DIVERGING_CMAP, vmin=-8, vmax=2)
            ax.contour(log_ratio >= 0.0, levels=[0.5], colors="black", linewidths=0.35)
            frac = float(np.mean(ratio > 1.0))
            ax.set_title(f"{solver.upper()} {precision}")
            ax.set_xticks([])
            ax.set_yticks([])
            ax.text(
                0.02,
                0.98,
                f">1: {100.0 * frac:.1f}%",
                transform=ax.transAxes,
                va="top",
                ha="left",
                fontsize=8,
                bbox=dict(facecolor="white", alpha=0.75, edgecolor="none"),
            )
    if im is not None:
        cbar = fig.colorbar(im, ax=axes, shrink=0.88)
        cbar.set_label(r"$\log_{10}(\sigma_{FP}/|\bar{\rho}-\rho_{ref}|)$")
    fig.suptitle("Noise-to-error heatmaps across virtual precision")
    save_pair(fig, out_path.stem, str(out_path.parent))
    plt.close(fig)


def plot_noise_ratio_quantiles(rows: list[dict[str, float | str | int]], out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for solver in ("hllc", "rusanov"):
        group = sorted(
            [row for row in rows if row["solver"] == solver],
            key=lambda row: int(row["precision_bits"]),
        )
        bits = [int(row["precision_bits"]) for row in group]
        axes[0].plot(bits, [float(row["median_log10_ratio"]) for row in group], marker="o", label=solver.upper())
        axes[0].fill_between(
            bits,
            [float(row["q05_log10_ratio"]) for row in group],
            [float(row["q95_log10_ratio"]) for row in group],
            alpha=0.14,
        )
        axes[1].plot(
            bits,
            [100.0 * float(row["fraction_ratio_gt_1"]) for row in group],
            marker="o",
            label=solver.upper(),
        )
    axes[0].axhline(0.0, color="black", linewidth=0.8, linestyle="--")
    axes[0].set_ylabel(r"$\log_{10}(\sigma_{FP}/|\bar{\rho}-\rho_{ref}|)$")
    axes[0].set_xlabel("virtual precision")
    axes[0].set_xticks([8, 16, 32], ["p8", "p16", "p32"])
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()
    axes[1].set_ylabel("cells with ratio > 1 (%)")
    axes[1].set_xlabel("virtual precision")
    axes[1].set_xticks([8, 16, 32], ["p8", "p16", "p32"])
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    fig.suptitle("Full-domain noise-to-error distribution")
    fig.tight_layout()
    save_pair(fig, out_path.stem, str(out_path.parent))
    plt.close(fig)


def plot_region_noise_ratio(
    rows: list[dict[str, float | str | int]],
    out_path: Path,
) -> None:
    regions = [
        "smooth_grad_p00_p70",
        "transition_grad_p70_p95",
        "discontinuity_grad_p95_p100",
    ]
    short = {
        "smooth_grad_p00_p70": "smooth",
        "transition_grad_p70_p95": "transition",
        "discontinuity_grad_p95_p100": "fronts",
    }
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    for ax, solver in zip(axes, ("hllc", "rusanov")):
        group = [
            row for row in rows if row["solver"] == solver and row["precision"] == "p32"
        ]
        lookup = {str(row["region"]): row for row in group}
        x = np.arange(len(regions))
        ax.bar(
            x - 0.18,
            [float(lookup[r]["median_log10_ratio"]) for r in regions],
            width=0.36,
            label="median",
        )
        ax.bar(
            x + 0.18,
            [float(lookup[r]["q95_log10_ratio"]) for r in regions],
            width=0.36,
            label="q95",
        )
        ax.axhline(0.0, color="black", linewidth=0.9, linestyle="--", label="ratio=1")
        ax.set_xticks(x, [short[r] for r in regions])
        ax.set_title(f"{solver.upper()}, p32 rho")
        ax.set_xlabel("reference-density gradient region")
        ax.grid(True, axis="y", alpha=0.3)
    axes[0].set_ylabel(r"$\log_{10}(\sigma_{FP}/|\bar{\rho}-\rho_{ref}|)$")
    axes[1].legend(loc="best")
    fig.suptitle("Noise-to-error ratio by spatial region")
    fig.tight_layout()
    save_pair(fig, out_path.stem, str(out_path.parent))
    plt.close(fig)


def plot_region_noise_ratio_precision_compare(
    rows: list[dict[str, float | str | int]],
    out_path: Path,
) -> None:
    regions = [
        "smooth_grad_p00_p70",
        "transition_grad_p70_p95",
        "discontinuity_grad_p95_p100",
    ]
    short = {
        "smooth_grad_p00_p70": "smooth",
        "transition_grad_p70_p95": "transition",
        "discontinuity_grad_p95_p100": "fronts",
    }
    precisions = ("p8", "p16", "p32")
    colors = {"p8": PALETTE["accent"], "p16": PALETTE["fp32"], "p32": PALETTE["fp64"]}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    for ax, solver in zip(axes, ("hllc", "rusanov")):
        x = np.arange(len(regions))
        width = 0.24
        for idx, precision in enumerate(precisions):
            group = [
                row
                for row in rows
                if row["solver"] == solver and row["precision"] == precision
            ]
            lookup = {str(row["region"]): row for row in group}
            offset = (idx - 1) * width
            ax.bar(
                x + offset,
                [float(lookup[r]["median_log10_ratio"]) for r in regions],
                width=width,
                color=colors[precision],
                label=precision,
            )
        ax.axhline(0.0, color="black", linewidth=0.9, linestyle="--", label="ratio=1")
        ax.set_xticks(x, [short[r] for r in regions])
        ax.set_title(solver.upper())
        ax.set_xlabel("reference-density gradient region")
        ax.grid(True, axis="y", alpha=0.3)
    axes[0].set_ylabel(r"median $\log_{10}(\sigma_{FP}/|\bar{\rho}-\rho_{ref}|)$")
    axes[1].legend(loc="best")
    fig.suptitle("Region noise-to-error ratio across p8/p16/p32")
    fig.tight_layout()
    save_pair(fig, out_path.stem, str(out_path.parent))
    plt.close(fig)


def plot_region_noise_ratio_precision_grid(
    rows: list[dict[str, float | str | int]],
    out_path: Path,
) -> None:
    """Compare p8/p16/p32 region noise/error ratios in one report-facing figure."""
    regions = [
        "smooth_grad_p00_p70",
        "transition_grad_p70_p95",
        "discontinuity_grad_p95_p100",
    ]
    short = {
        "smooth_grad_p00_p70": "smooth",
        "transition_grad_p70_p95": "transition",
        "discontinuity_grad_p95_p100": "fronts",
    }
    precisions = ["p8", "p16", "p32"]
    fig, axes = plt.subplots(2, 3, figsize=(14.5, 7.2), sharey=True)
    for row_idx, solver in enumerate(("hllc", "rusanov")):
        for col_idx, precision in enumerate(precisions):
            ax = axes[row_idx, col_idx]
            group = [
                row
                for row in rows
                if row["solver"] == solver and row["precision"] == precision
            ]
            lookup = {str(row["region"]): row for row in group}
            x = np.arange(len(regions))
            med = [float(lookup[r]["median_log10_ratio"]) for r in regions]
            q95 = [float(lookup[r]["q95_log10_ratio"]) for r in regions]
            frac = [100.0 * float(lookup[r]["fraction_ratio_gt_1"]) for r in regions]

            ax.bar(x - 0.18, med, width=0.36, label="median")
            ax.bar(x + 0.18, q95, width=0.36, label="q95")
            ax.axhline(0.0, color="black", linewidth=0.9, linestyle="--")
            ax.set_xticks(x, [short[r] for r in regions])
            ax.set_title(f"{solver.upper()} {precision}")
            ax.grid(True, axis="y", alpha=0.3)
            for xi, pct in zip(x, frac):
                ax.annotate(
                    f"{pct:.1f}%",
                    (xi, 0.03),
                    textcoords="offset points",
                    xytext=(0, 4),
                    ha="center",
                    va="bottom",
                    fontsize=7,
                    rotation=90,
                )
            if col_idx == 0:
                ax.set_ylabel(r"$\log_{10}(\sigma_{FP}/|\bar{\rho}-\rho_{ref}|)$")
    axes[0, 0].legend(loc="lower left", fontsize=8)
    fig.suptitle("Region noise-to-error ratio across virtual precision (labels: % cells with ratio > 1)")
    fig.tight_layout()
    save_pair(fig, out_path.stem, str(out_path.parent))
    plt.close(fig)


def write_region_losos_csv(rows: list[dict[str, float | str | int]], out_path: Path) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "solver",
                "precision",
                "precision_bits",
                "region",
                "variable",
                "n_cells",
                "n_samples",
                "q05",
                "q25",
                "median",
                "s_req",
                "median_margin",
                "q25_margin",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def plot_region_losos(rows: list[dict[str, float | str | int]], out_path: Path) -> None:
    regions = [
        "smooth_grad_p00_p70",
        "transition_grad_p70_p95",
        "discontinuity_grad_p95_p100",
    ]
    short = {
        "smooth_grad_p00_p70": "smooth",
        "transition_grad_p70_p95": "transition",
        "discontinuity_grad_p95_p100": "fronts",
    }
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    for ax, solver in zip(axes, ("hllc", "rusanov")):
        group = [row for row in rows if row["solver"] == solver and row["precision"] == "p32"]
        lookup = {str(row["region"]): row for row in group}
        x = np.arange(len(regions))
        ax.bar(x - 0.18, [float(lookup[r]["q25"]) for r in regions], width=0.36, label="q25")
        ax.bar(x + 0.18, [float(lookup[r]["median"]) for r in regions], width=0.36, label="median")
        s_req = float(group[0]["s_req"]) if group else 0.0
        ax.axhline(s_req, color="black", linewidth=1.0, linestyle="--", label="s_req")
        ax.set_xticks(x, [short[r] for r in regions])
        ax.set_title(f"{solver.upper()}, p32 rho")
        ax.set_xlabel("reference-density gradient region")
        ax.grid(True, axis="y", alpha=0.3)
    axes[0].set_ylabel("LoSoS significant digits")
    axes[1].legend(loc="best")
    fig.suptitle("Region-aware LoSoS versus s_req")
    fig.tight_layout()
    save_pair(fig, out_path.stem, str(out_path.parent))
    plt.close(fig)


def write_losos_csv(rows: list[dict[str, float | str | int]], out_path: Path) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "solver",
                "precision",
                "precision_bits",
                "variable",
                "q05",
                "q25",
                "median",
                "mean",
                "n_samples",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def plot_losos_quantiles(rows: list[dict[str, float | str | int]], out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.8), sharey=True)
    quantiles = [("q05", "worst 5%"), ("q25", "q25"), ("median", "median")]
    for ax, solver in zip(axes, ("hllc", "rusanov")):
        group = sorted(
            [row for row in rows if row["solver"] == solver],
            key=lambda row: int(row["precision_bits"]),
        )
        bits = [int(row["precision_bits"]) for row in group]
        labels = [str(row["precision"]) for row in group]
        for key, label in quantiles:
            ax.plot(bits, [float(row[key]) for row in group], marker="o", label=label)
        for row in group:
            ax.annotate(
                f"n={int(row['n_samples'])}",
                (int(row["precision_bits"]), float(row["median"])),
                textcoords="offset points",
                xytext=(0, 7),
                ha="center",
                fontsize=7,
            )
        ax.set_title(solver.upper())
        ax.set_xticks(bits, labels)
        ax.set_xlabel("virtual precision")
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("LoSoS rho significant digits")
    axes[1].legend(loc="best")
    fig.suptitle("LoSoS distribution: q05/q25/median instead of worst-only")
    fig.tight_layout()
    save_pair(fig, out_path.stem, str(out_path.parent))
    plt.close(fig)


def build_sigma_rows(pareto_csv: Path) -> list[dict[str, float | str | int]]:
    rows = []
    for row in _read_csv(pareto_csv):
        precision = row["precision_label"]
        rows.append(
            {
                "solver": row["solver"],
                "precision": precision,
                "precision_bits": PRECISION_BITS[precision],
                "sigma_fp_l1": float(row["sigma_fp_l1"]),
            }
        )
    return rows


def write_sigma_csv(rows: list[dict[str, float | str | int]], out_path: Path) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["solver", "precision", "precision_bits", "sigma_fp_l1"]
        )
        writer.writeheader()
        writer.writerows(rows)


def plot_sigma(rows: list[dict[str, float | str | int]], out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for solver in ("hllc", "rusanov"):
        group = sorted(
            [row for row in rows if row["solver"] == solver],
            key=lambda row: int(row["precision_bits"]),
        )
        ax.plot(
            [int(row["precision_bits"]) for row in group],
            [float(row["sigma_fp_l1"]) for row in group],
            marker="o",
            label=solver.upper(),
        )
    ax.set_yscale("log")
    ax.set_xticks(
        [8, 16, 24, 32, 53],
        ["p8", "p16", "p24 real float", "p32", "p53"],
    )
    ax.set_xlabel("precision")
    ax.set_ylabel(r"$\sigma_{FP,L1}$ for rho")
    ax.set_title("Floating-point noise decreases with precision")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    save_pair(fig, out_path.stem, str(out_path.parent))
    plt.close(fig)


def write_summary(
    out_dir: Path,
    pareto_csv: Path,
    fmd_rows: list[dict[str, float | str]],
    losos_rows: list[dict[str, float | str | int]],
    sigma_rows: list[dict[str, float | str | int]],
    region_fmd_rows: list[dict[str, float | str | int]],
    region_losos_rows: list[dict[str, float | str | int]],
    noise_ratio_rows: list[dict[str, float | str | int]],
    region_noise_ratio_rows: list[dict[str, float | str | int]],
) -> None:
    lines = [
        "# Report 1 D2 Replots",
        "",
        "These figures replace the hard-to-read Pareto/s_req presentation with direct, report-facing diagnostics.",
        "",
        "## Outputs",
        "",
        "| figure | source | interpretation |",
        "|---|---|---|",
        "| `float_double_over_reference_bar.png` | `experiments/week4/float_regression/2d/summary.json` | Float-double drift divided by double-reference discretisation error; lower is better. |",
        "| `losos_quantiles_rho.png` | raw p8/p16/p32 MCA grids + `u_ref_200_blockavg.npz` | LoSoS rho distribution using q05/q25/median, avoiding a single worst-cell story. |",
        f"| `sigma_fp_vs_precision.png` | `{pareto_csv}` | sigma_FP_L1 falls as precision increases; this keeps the x/y relationship simple. |",
        "| `region_float_double_over_reference_rho.png` | float/double/reference binaries + density-gradient masks | Float-double drift ratio split by smooth, transition, and strongest-gradient cells. |",
        "| `region_losos_margin_rho_p32.png` | raw p32 MCA grids + density-gradient masks | LoSoS q25/median compared to s_req in each spatial region. |",
        "| `noise_to_error_ratio_rho_p32.png` | raw p32 MCA grids + `u_ref_200_blockavg.npz` | 2D analogue of `vfc_sod_noise_ratio.png`: full-domain log10(noise/error) heatmap. |",
        "| `noise_to_error_ratio_heatmap_grid_rho.png` | raw p8/p16/p32 MCA grids + `u_ref_200_blockavg.npz` | Heatmap grid showing FP-limited regions shrinking as precision increases. |",
        "| `noise_to_error_ratio_quantiles_rho.png` | raw p8/p16/p32 MCA grids + `u_ref_200_blockavg.npz` | Whole-domain noise/error distribution versus virtual precision. |",
        "| `region_noise_to_error_ratio_rho_p32.png` | raw p32 MCA grids + density-gradient masks | Noise/error ratio split by smooth, transition, and strongest-gradient cells. |",
        "| `region_noise_to_error_ratio_precision_compare_rho.png` | raw p8/p16/p32 MCA grids + density-gradient masks | Region-wise median noise/error ratio across p8, p16, and p32. |",
        "| `region_noise_to_error_ratio_precision_grid_rho.png` | raw p8/p16/p32 MCA grids + density-gradient masks | Region noise/error comparison across precision levels. |",
        "",
        "## Notes",
        "",
        "- The LoSoS quantile plot includes p8/p16/p32 because those raw MCA grids are present in the workspace.",
        "- Additional scalar-only precision rows appear in the sigma_FP plot when the Pareto CSV contains them, but not in the LoSoS quantile plot unless raw MCA grids are present locally.",
        "- For p8, the common HLLC/Rusanov subset is used so sample counts match.",
        "",
        "## Float/double over reference ratios",
        "",
        "| resolution | variable | ratio |",
        "|---:|---|---:|",
    ]
    for row in sorted(fmd_rows, key=lambda r: (int(r["resolution"]), str(r["variable"]))):
        lines.append(f"| {int(row['resolution'])} | {row['variable']} | {float(row['ratio']):.6e} |")

    lines.extend(["", "## LoSoS rho quantiles", "", "| solver | precision | samples | q05 | q25 | median |", "|---|---|---:|---:|---:|---:|"])
    for row in sorted(losos_rows, key=lambda r: (str(r["solver"]), int(r["precision_bits"]))):
        lines.append(
            f"| {row['solver']} | {row['precision']} | {int(row['n_samples'])} | "
            f"{float(row['q05']):.6g} | {float(row['q25']):.6g} | {float(row['median']):.6g} |"
        )

    lines.extend(["", "## sigma_FP rows", "", "| solver | precision | sigma_fp_l1 |", "|---|---|---:|"])
    for row in sorted(sigma_rows, key=lambda r: (str(r["solver"]), int(r["precision_bits"]))):
        lines.append(f"| {row['solver']} | {row['precision']} | {float(row['sigma_fp_l1']):.6e} |")

    lines.extend(
        [
            "",
            "## Region-aware float/double rho ratios",
            "",
            "| resolution | region | cells | ratio |",
            "|---:|---|---:|---:|",
        ]
    )
    for row in sorted(
        [r for r in region_fmd_rows if r["variable"] == "rho"],
        key=lambda r: (int(r["resolution"]), str(r["region"])),
    ):
        lines.append(
            f"| {int(row['resolution'])} | {row['region']} | {int(row['n_cells'])} | "
            f"{float(row['ratio']):.6e} |"
        )

    lines.extend(
        [
            "",
            "## Region-aware LoSoS rho margins",
            "",
            "| solver | precision | region | cells | q25 | median | s_req | median_margin |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in sorted(
        region_losos_rows,
        key=lambda r: (str(r["solver"]), int(r["precision_bits"]), str(r["region"])),
    ):
        lines.append(
            f"| {row['solver']} | {row['precision']} | {row['region']} | "
            f"{int(row['n_cells'])} | {float(row['q25']):.6g} | "
            f"{float(row['median']):.6g} | {float(row['s_req']):.6g} | "
            f"{float(row['median_margin']):.6g} |"
        )

    lines.extend(
        [
            "",
            "## Full-domain noise-to-error ratios",
            "",
            "`noise_to_error_ratio_rho_p32.png` is the 2D analogue of the 1D "
            "`vfc_sod_noise_ratio.png`: values above zero in log10 space indicate "
            "cells where MCA noise exceeds the reference error.",
            "",
            "| solver | precision | samples | median log10 ratio | q95 log10 ratio | ratio > 1 cells |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in sorted(noise_ratio_rows, key=lambda r: (str(r["solver"]), int(r["precision_bits"]))):
        lines.append(
            f"| {row['solver']} | {row['precision']} | {int(row['n_samples'])} | "
            f"{float(row['median_log10_ratio']):.6g} | {float(row['q95_log10_ratio']):.6g} | "
            f"{100.0 * float(row['fraction_ratio_gt_1']):.4g}% |"
        )

    lines.extend(
        [
            "",
            "## Region-aware noise-to-error ratios",
            "",
            "| solver | precision | region | cells | median log10 ratio | q95 log10 ratio | ratio > 1 cells |",
            "|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in sorted(
        region_noise_ratio_rows,
        key=lambda r: (str(r["solver"]), int(r["precision_bits"]), str(r["region"])),
    ):
        lines.append(
            f"| {row['solver']} | {row['precision']} | {row['region']} | "
            f"{int(row['n_cells'])} | {float(row['median_log10_ratio']):.6g} | "
            f"{float(row['q95_log10_ratio']):.6g} | "
            f"{100.0 * float(row['fraction_ratio_gt_1']):.4g}% |"
        )

    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--week4-2d-summary",
        type=Path,
        default=REPO_ROOT / "experiments/week4/float_regression/2d/summary.json",
    )
    parser.add_argument(
        "--sweep-root",
        type=Path,
        default=REPO_ROOT / "experiments/week7/2d_vfc_precision_sweep",
    )
    parser.add_argument(
        "--reference",
        type=Path,
        default=REPO_ROOT / "experiments/week4/metrics/u_ref_200_blockavg.npz",
    )
    parser.add_argument(
        "--pareto-csv",
        type=Path,
        default=REPO_ROOT / "experiments/week7/pareto_full/pareto_lw3_full.csv",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=REPO_ROOT / "experiments/week7/report1_d2_replots",
    )
    parser.add_argument("--gamma", type=float, default=1.4)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    fmd_rows = build_fmd_rows(args.week4_2d_summary)
    write_fmd_csv(fmd_rows, out_dir / "float_double_over_reference.csv")
    plot_fmd_bar(fmd_rows, out_dir / "float_double_over_reference_bar.png")

    region_fmd_rows = build_region_fmd_rows(args.week4_2d_summary, args.gamma)
    write_region_fmd_csv(region_fmd_rows, out_dir / "region_float_double_over_reference.csv")
    plot_region_fmd(region_fmd_rows, out_dir / "region_float_double_over_reference_rho.png")

    losos_rows = build_losos_quantile_rows(args.sweep_root, args.reference, args.gamma)
    write_losos_csv(losos_rows, out_dir / "losos_quantiles_rho.csv")
    plot_losos_quantiles(losos_rows, out_dir / "losos_quantiles_rho.png")

    region_losos_rows = build_region_losos_rows(
        args.sweep_root, args.reference, args.pareto_csv, args.gamma
    )
    write_region_losos_csv(region_losos_rows, out_dir / "region_losos_quantiles_rho.csv")
    plot_region_losos(region_losos_rows, out_dir / "region_losos_margin_rho_p32.png")

    noise_ratio_rows, noise_ratio_fields = build_noise_ratio_rows(
        args.sweep_root, args.reference, args.gamma
    )
    write_noise_ratio_csv(noise_ratio_rows, out_dir / "noise_to_error_ratio_rho.csv")
    plot_noise_ratio_heatmap(
        noise_ratio_fields, out_dir / "noise_to_error_ratio_rho_p32.png", precision="p32"
    )
    plot_noise_ratio_heatmap(
        noise_ratio_fields, out_dir / "noise_to_error_ratio_rho_p16.png", precision="p16"
    )
    plot_noise_ratio_heatmap(
        noise_ratio_fields, out_dir / "noise_to_error_ratio_rho_p8.png", precision="p8"
    )
    plot_noise_ratio_heatmap_grid(
        noise_ratio_fields, out_dir / "noise_to_error_ratio_heatmap_grid_rho.png"
    )
    plot_noise_ratio_quantiles(
        noise_ratio_rows, out_dir / "noise_to_error_ratio_quantiles_rho.png"
    )

    region_noise_ratio_rows = build_region_noise_ratio_rows(
        args.sweep_root, args.reference, args.gamma
    )
    write_noise_ratio_csv(
        region_noise_ratio_rows, out_dir / "region_noise_to_error_ratio_rho.csv"
    )
    plot_region_noise_ratio(
        region_noise_ratio_rows, out_dir / "region_noise_to_error_ratio_rho_p32.png"
    )
    plot_region_noise_ratio_precision_compare(
        region_noise_ratio_rows,
        out_dir / "region_noise_to_error_ratio_precision_compare_rho.png",
    )
    plot_region_noise_ratio_precision_grid(
        region_noise_ratio_rows,
        out_dir / "region_noise_to_error_ratio_precision_grid_rho.png",
    )

    sigma_rows = build_sigma_rows(args.pareto_csv)
    write_sigma_csv(sigma_rows, out_dir / "sigma_fp_vs_precision.csv")
    plot_sigma(sigma_rows, out_dir / "sigma_fp_vs_precision.png")

    write_summary(
        out_dir,
        args.pareto_csv,
        fmd_rows,
        losos_rows,
        sigma_rows,
        region_fmd_rows,
        region_losos_rows,
        noise_ratio_rows,
        region_noise_ratio_rows,
    )
    print(f"[report1-d2] wrote {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
