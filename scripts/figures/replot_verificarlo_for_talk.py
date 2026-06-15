"""Regenerate two Verificarlo figures for presentation1/talk with deck styling.

Reuses the existing data-loading and metric computation from report1_d2_replots
(same MCA grids + reference npz), but changes ONLY the plotting:
  (A) region_noise_to_error_ratio_precision_grid_rho.pdf
      - HLLC only, median bars only (q95 dropped), large fonts.
  (B) noise_to_error_ratio_heatmap_grid_rho.pdf
      - HLLC only (one row of 3 panels p8/p16/p32), large titles + colorbar.

Outputs are written directly into presentation1/talk/figs/ with the exact
filenames the deck references. Originals in report1/.../Figs/report1/ are not
touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "figures"))

# Reuse the exact data-loading and metric computation from the report script.
from report1_d2_replots import (  # noqa: E402
    build_noise_ratio_rows,
    build_region_noise_ratio_rows,
)

SWEEP_ROOT = REPO_ROOT / "experiments/report1/review3/mca_n30/2d_vfc_precision_sweep"
REFERENCE = REPO_ROOT / "experiments/week4/metrics/u_ref_200_blockavg.npz"
FIGS_DIR = REPO_ROOT / "presentation1" / "talk" / "figs"
GAMMA = 1.4

REGIONS = [
    "smooth_grad_p00_p70",
    "transition_grad_p70_p95",
    "discontinuity_grad_p95_p100",
]
REGION_SHORT = {
    "smooth_grad_p00_p70": "smooth",
    "transition_grad_p70_p95": "transition",
    "discontinuity_grad_p95_p100": "shock-front",
}
PRECISIONS = ["p8", "p16", "p32"]


def plot_region_grid_hllc(rows, out_path: Path) -> None:
    """Figure (A): HLLC-only, median bars only, large fonts."""
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 6.0), sharey=True)
    for col_idx, precision in enumerate(PRECISIONS):
        ax = axes[col_idx]
        group = [
            row
            for row in rows
            if row["solver"] == "hllc" and row["precision"] == precision
        ]
        lookup = {str(row["region"]): row for row in group}
        x = np.arange(len(REGIONS))
        med = [float(lookup[r]["median_log10_ratio"]) for r in REGIONS]
        frac = [100.0 * float(lookup[r]["fraction_ratio_gt_1"]) for r in REGIONS]

        ax.bar(x, med, width=0.62, color="#4C78A8")
        ax.axhline(0.0, color="black", linewidth=1.2, linestyle="--", label=r"$\eta=1$ (log $=0$)")
        ax.set_xticks(x, [REGION_SHORT[r] for r in REGIONS], fontsize=13)
        ax.tick_params(axis="y", labelsize=13)
        ax.set_title(f"HLLC {precision}", fontsize=18)
        ax.grid(True, axis="y", alpha=0.3)
        for xi, m, pct in zip(x, med, frac):
            # Anchor labels near the zero line so deep-negative bars do not
            # push the annotation off the bottom of the panel.
            y_anchor = m if m >= 0 else 0.0
            ax.annotate(
                f"{pct:.1f}%",
                (xi, y_anchor),
                textcoords="offset points",
                xytext=(0, 6 if m >= 0 else -16),
                ha="center",
                va="bottom" if m >= 0 else "top",
                fontsize=17,
                fontweight="bold",
            )
        if col_idx == 0:
            ax.set_ylabel(
                r"$\log_{10}(\sigma_{\mathrm{FP}}/|\rho-\rho_{\mathrm{ref}}|)$",
                fontsize=15,
            )
    # Single reference line only; place its legend in the empty top of the
    # last (p32) panel so it never overlaps the bars or % annotations.
    axes[-1].legend(loc="upper right", fontsize=12, framealpha=0.9)
    fig.suptitle(
        "HLLC noise-to-error ratio by region (labels: % cells with $\\eta>1$)",
        fontsize=18,
    )
    fig.tight_layout()
    fig.savefig(out_path)
    fig.savefig(out_path.with_suffix(".png"), dpi=180)
    plt.close(fig)


def plot_heatmap_grid_hllc(fields, out_path: Path) -> None:
    """Figure (B): HLLC-only single row of three precision panels."""
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 5.4), constrained_layout=True)
    im = None
    for col_idx, precision in enumerate(PRECISIONS):
        ax = axes[col_idx]
        ratio = fields[("hllc", precision)]
        log_ratio = np.log10(np.clip(ratio, 1e-20, 1e20))
        im = ax.imshow(log_ratio, origin="lower", cmap="coolwarm", vmin=-8, vmax=2)
        ax.contour(log_ratio >= 0.0, levels=[0.5], colors="black", linewidths=0.5)
        frac = float(np.mean(ratio > 1.0))
        ax.set_title(f"HLLC {precision}", fontsize=20)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.text(
            0.02,
            0.98,
            f"$\\eta>1$: {100.0 * frac:.1f}%",
            transform=ax.transAxes,
            va="top",
            ha="left",
            fontsize=13,
            bbox=dict(facecolor="white", alpha=0.8, edgecolor="none"),
        )
    cbar = fig.colorbar(im, ax=axes, shrink=0.9)
    cbar.set_label(
        r"$\log_{10}(\sigma_{\mathrm{FP}}/|\rho-\rho_{\mathrm{ref}}|)$",
        fontsize=16,
    )
    cbar.ax.tick_params(labelsize=13)
    fig.suptitle(
        "HLLC noise-to-error ratio across virtual precision", fontsize=20
    )
    fig.savefig(out_path)
    fig.savefig(out_path.with_suffix(".png"), dpi=180)
    plt.close(fig)


def main() -> int:
    FIGS_DIR.mkdir(parents=True, exist_ok=True)

    region_rows = build_region_noise_ratio_rows(SWEEP_ROOT, REFERENCE, GAMMA)
    plot_region_grid_hllc(
        region_rows,
        FIGS_DIR / "region_noise_to_error_ratio_precision_grid_rho.pdf",
    )

    _, fields = build_noise_ratio_rows(SWEEP_ROOT, REFERENCE, GAMMA)
    plot_heatmap_grid_hllc(
        fields, FIGS_DIR / "noise_to_error_ratio_heatmap_grid_rho.pdf"
    )

    print(f"[talk-replot] wrote figures into {FIGS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
