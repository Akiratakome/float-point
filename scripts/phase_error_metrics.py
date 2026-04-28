#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from io_helper import cons_to_prim, read_binary


def _gaussian_smooth_1d(values: np.ndarray, sigma: float) -> np.ndarray:
    if sigma <= 0.0:
        return values
    radius = max(1, int(np.ceil(3.0 * sigma)))
    x = np.arange(-radius, radius + 1, dtype=np.float64)
    kernel = np.exp(-0.5 * (x / sigma) ** 2)
    kernel /= np.sum(kernel)
    padded = np.pad(values, (radius, radius), mode="reflect")
    return np.convolve(padded, kernel, mode="valid")


def _shock_centroid_1d(values: np.ndarray, coords: np.ndarray, smooth_sigma: float) -> float:
    smooth = _gaussian_smooth_1d(values.astype(np.float64), smooth_sigma)
    grad = np.abs(np.gradient(smooth, coords))
    weight_sum = float(np.sum(grad))
    if weight_sum <= 0.0:
        return float(np.mean(coords))
    return float(np.sum(coords * grad) / weight_sum)


def _write_difference_heatmaps(
    candidate_prim: np.ndarray,
    reference_prim: np.ndarray,
    out_dir: Path,
    prefix: str,
) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    heatmaps: dict[str, str] = {}
    for idx, var_name in enumerate(("rho", "u", "v", "p")):
        diff = candidate_prim[..., idx] - reference_prim[..., idx]
        vmax = float(np.max(np.abs(diff)))
        if vmax <= 0.0:
            vmax = 1.0
        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(diff, origin="lower", cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="equal")
        ax.set_title(f"{prefix}: {var_name} (candidate - reference)")
        ax.set_xlabel("i")
        ax.set_ylabel("j")
        fig.colorbar(im, ax=ax, shrink=0.85)
        fig.tight_layout()
        out_path = out_dir / f"{prefix}_diff_{var_name}.png"
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        heatmaps[var_name] = str(out_path)
    return heatmaps


def _ssim_scalar(a: np.ndarray, b: np.ndarray, allow_fallback: bool) -> tuple[float, bool]:
    data_range = float(np.max(b) - np.min(b))
    if data_range <= 0.0:
        data_range = 1.0
    try:
        from skimage.metrics import structural_similarity

        return float(
            structural_similarity(
                a,
                b,
                data_range=data_range,
                gaussian_weights=True,
                sigma=1.5,
            )
        ), False
    except ImportError as exc:
        if not allow_fallback:
            raise RuntimeError(
                "scikit-image is required for SSIM. Install scikit-image or enable fallback."
            ) from exc
        print(
            "[phase-error] WARNING: skimage unavailable; SSIM disabled, keeping L1 + heatmaps only.",
            file=sys.stderr,
        )
        return float("nan"), True


def compute_phase_metrics_from_primitive(
    candidate_prim: np.ndarray,
    reference_prim: np.ndarray,
    dx: float,
    dy: float,
    smooth_sigma: float,
    allow_ssim_fallback: bool,
    heatmap_out_dir: Path | None = None,
    heatmap_prefix: str = "candidate",
) -> dict[str, object]:
    if candidate_prim.shape != reference_prim.shape:
        raise ValueError(
            f"Shape mismatch: candidate {candidate_prim.shape} vs reference {reference_prim.shape}"
        )
    if candidate_prim.shape[-1] != 4:
        raise ValueError(f"Expected primitive with last axis=4, got {candidate_prim.shape}")
    ny, nx = candidate_prim.shape[0], candidate_prim.shape[1]
    rho_cand = candidate_prim[..., 0]
    rho_ref = reference_prim[..., 0]
    l1_rho = float(np.mean(np.abs(rho_cand - rho_ref)))
    ssim_rho, ssim_fallback_used = _ssim_scalar(rho_cand, rho_ref, allow_ssim_fallback)

    x = (np.arange(nx, dtype=np.float64) + 0.5) * dx
    y = (np.arange(ny, dtype=np.float64) + 0.5) * dy
    j_center = ny // 2
    i_center = nx // 2
    x_shock_cand = _shock_centroid_1d(rho_cand[j_center, :], x, smooth_sigma)
    x_shock_ref = _shock_centroid_1d(rho_ref[j_center, :], x, smooth_sigma)
    y_shock_cand = _shock_centroid_1d(rho_cand[:, i_center], y, smooth_sigma)
    y_shock_ref = _shock_centroid_1d(rho_ref[:, i_center], y, smooth_sigma)

    metrics: dict[str, object] = {
        "L1_rho": l1_rho,
        "ssim_rho": float(ssim_rho),
        "delta_x_shock": abs(x_shock_cand - x_shock_ref),
        "delta_y_shock": abs(y_shock_cand - y_shock_ref),
        "ssim_fallback_used": bool(ssim_fallback_used),
    }
    if heatmap_out_dir is not None:
        metrics["difference_heatmaps"] = _write_difference_heatmaps(
            candidate_prim,
            reference_prim,
            heatmap_out_dir,
            heatmap_prefix,
        )
    return metrics


def metrics_markdown_row(label: str, metrics: dict[str, object]) -> str:
    return (
        f"| {label} | {float(metrics['L1_rho']):.6e} | {float(metrics['ssim_rho']):.6f} | "
        f"{float(metrics['delta_x_shock']):.6e} | {float(metrics['delta_y_shock']):.6e} |"
    )


def compute_phase_metrics_from_bins(
    candidate_bin: Path,
    reference_bin: Path,
    gamma: float,
    smooth_sigma: float,
    allow_ssim_fallback: bool,
    heatmap_out_dir: Path | None = None,
    heatmap_prefix: str = "candidate",
) -> dict[str, object]:
    cand_header, cand_cons = read_binary(candidate_bin)
    ref_header, ref_cons = read_binary(reference_bin)
    if (cand_header.nx, cand_header.ny) != (ref_header.nx, ref_header.ny):
        raise ValueError(
            f"Candidate/reference size mismatch: {cand_header.nx}x{cand_header.ny} vs "
            f"{ref_header.nx}x{ref_header.ny}"
        )
    cand_prim = cons_to_prim(cand_cons.astype(np.float64), gamma)
    ref_prim = cons_to_prim(ref_cons.astype(np.float64), gamma)
    return compute_phase_metrics_from_primitive(
        cand_prim,
        ref_prim,
        cand_header.dx,
        cand_header.dy,
        smooth_sigma,
        allow_ssim_fallback,
        heatmap_out_dir,
        heatmap_prefix,
    )


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compute 2D phase-oriented metrics for candidate vs reference.")
    p.add_argument("--candidate", required=True, type=Path)
    p.add_argument("--reference", required=True, type=Path)
    p.add_argument("--gamma", type=float, default=1.4)
    p.add_argument("--smooth-sigma", type=float, default=0.5)
    p.add_argument("--allow-ssim-fallback", action="store_true")
    p.add_argument("--heatmap-dir", type=Path, default=None, help="Optional output directory for difference heatmaps")
    p.add_argument("--heatmap-prefix", type=str, default="candidate")
    p.add_argument("--out", type=Path, default=None, help="Optional JSON output path")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    metrics = compute_phase_metrics_from_bins(
        args.candidate,
        args.reference,
        args.gamma,
        args.smooth_sigma,
        args.allow_ssim_fallback,
        args.heatmap_dir,
        args.heatmap_prefix,
    )
    md = [
        "| case | L1_rho | ssim_rho | delta_x_shock | delta_y_shock |",
        "|------|-------:|---------:|--------------:|--------------:|",
        metrics_markdown_row("candidate", metrics),
    ]
    print("\n".join(md))
    print("")
    print(json.dumps(metrics, indent=2))
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

