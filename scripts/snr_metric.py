"""SNR (Signal-to-Noise Ratio) metric for Verificarlo MCA sample ensembles.

Quantifies the trade-off between truncation error (how far the numerical mean
is from a high-resolution reference) and FP round-off noise (spread across MCA
samples) using the CORRECT per-cell-first operator order: compute sigma_FP per
cell first, then aggregate spatially — never the other way round.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from io_helper import stack_samples, load_seeds, cons_to_prim

# Primitive variable names and order — mirrors IDX_* in io_helper.py.
VAR_ORDER = ("rho", "u", "v", "p")

# ---------------------------------------------------------------------------
# Floor helpers
# ---------------------------------------------------------------------------

_EPS = np.finfo(np.float64).eps
_SQRT_EPS = np.sqrt(_EPS)


def _var_floor(u_ref_var: np.ndarray) -> float:
    """Floor prevents div-by-zero in vacuum-like cells.

    Spec: sqrt(eps) * max_j |U_ref(j)|.  All-zero u_ref (v-component in
    a symmetric run, pure vacuum) collapses that to zero, so we also
    impose a never-vanishing absolute floor of sqrt(eps) itself.
    """
    return max(_SQRT_EPS * float(np.abs(u_ref_var).max()), _SQRT_EPS)

_CSV_FIELDNAMES = [
    "solver", "precision", "variable",
    "sigma_fp_l1", "sigma_fp_max", "n_cells", "n_samples",
    "mu_trunc_l1", "snr_global", "snr_median", "snr_q05",
]


# ---------------------------------------------------------------------------
# Core computation functions (exposed for unit tests)
# ---------------------------------------------------------------------------

def compute_sigma_fp_field(samples: np.ndarray) -> np.ndarray:
    """Compute per-cell FP noise as std over MCA samples (ddof=1).

    Parameters
    ----------
    samples : (n_samples, ny, nx) float64 array for a single variable.

    Returns
    -------
    sigma_fp : (ny, nx) per-cell standard deviation.
    """
    return samples.std(axis=0, ddof=1)


def compute_snr_fields(
    samples: np.ndarray,
    u_ref: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute per-cell truncation bias, FP noise, and local SNR.

    Parameters
    ----------
    samples : (n_samples, ny, nx) array for one variable.
    u_ref   : (ny, nx) reference solution for the same variable.

    Returns
    -------
    mu_trunc  : (ny, nx) mean - reference (truncation bias).
    sigma_fp  : (ny, nx) per-cell FP noise std.
    snr_local : (ny, nx) local SNR = |mu_trunc| / max(sigma_fp, floor).
    """
    sigma_fp = compute_sigma_fp_field(samples)
    mu_trunc = samples.mean(axis=0) - u_ref

    # Precision-aware floor: sqrt(eps_f64) * max_j |U_ref(j)|, never zero.
    floor = _var_floor(u_ref)
    snr_local = np.abs(mu_trunc) / np.maximum(sigma_fp, floor)

    return mu_trunc, sigma_fp, snr_local


def compute_snr_scalars(
    mu_trunc: np.ndarray,
    sigma_fp: np.ndarray,
    snr_local: np.ndarray,
) -> tuple[float, float, float]:
    """Aggregate per-cell SNR fields into three global scalars.

    Returns
    -------
    snr_global : ||mu_trunc||_1 / ||sigma_fp||_1
    snr_median : median of snr_local over all cells
    snr_q05    : 5th percentile of snr_local over all cells
    """
    l1_mu = np.sum(np.abs(mu_trunc))
    l1_sigma = np.sum(np.abs(sigma_fp))
    snr_global = l1_mu / l1_sigma if l1_sigma > 0.0 else np.inf
    snr_median = float(np.median(snr_local))
    snr_q05 = float(np.percentile(snr_local, 5))
    return float(snr_global), snr_median, snr_q05


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _load_prim(root: Path, subdir: str, gamma: float, expected_n: int
               ) -> tuple[int, np.ndarray]:
    """Load MCA samples for one solver and convert to primitive variables.

    Returns (n_samples, prim) where prim is (n_samples, ny, nx, 4).
    """
    solver_root = root / subdir
    h, cons, paths = stack_samples(solver_root)
    if len(paths) != expected_n:
        raise ValueError(
            f"Expected {expected_n} samples under {solver_root}, "
            f"found {len(paths)}"
        )
    prim = cons_to_prim(cons.astype(np.float64), gamma)
    return len(paths), prim


def _load_reference(ref_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Load reference .npz with u_ref_hllc and u_ref_rusanov arrays."""
    data = np.load(ref_path)
    missing = [k for k in ("u_ref_hllc", "u_ref_rusanov") if k not in data]
    if missing:
        raise ValueError(
            f"Reference .npz at {ref_path} is missing keys: {missing}. "
            "Expected both 'u_ref_hllc' and 'u_ref_rusanov' of shape (ny, nx, 4)."
        )
    return data["u_ref_hllc"].astype(np.float64), data["u_ref_rusanov"].astype(np.float64)


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

def _lognorm_for_field(field: np.ndarray, vmin_floor: float = 1e-20) -> mcolors.LogNorm:
    """Build a LogNorm with safe vmin for a field that may contain zeros."""
    fmin = max(field[field > 0].min() if np.any(field > 0) else vmin_floor, vmin_floor)
    fmax = field.max()
    if fmax <= fmin:
        fmax = fmin * 10.0
    return mcolors.LogNorm(vmin=fmin, vmax=fmax)


def _plot_sigma_heatmap(
    sigma_hllc: list[np.ndarray],
    sigma_rusanov: list[np.ndarray],
    out_path: Path,
) -> None:
    """Save 2x4 sigma_FP heatmap (rows: HLLC, Rusanov; cols: rho, u, v, p)."""
    fig, axes = plt.subplots(2, 4, figsize=(16, 7))
    extent = [0, 1, 0, 1]
    rows = [("HLLC", sigma_hllc), ("Rusanov", sigma_rusanov)]

    for row_idx, (solver_label, sigma_list) in enumerate(rows):
        for col_idx, (var_label, sigma) in enumerate(zip(VAR_ORDER, sigma_list)):
            ax = axes[row_idx, col_idx]
            norm = _lognorm_for_field(sigma)
            im = ax.imshow(
                sigma, origin="lower", extent=extent, aspect="equal",
                norm=norm, cmap="inferno",
            )
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            ax.set_title(f"{solver_label} $\\sigma_{{FP}}$({var_label})", fontsize=8)
            ax.set_xlabel("x", fontsize=7)
            ax.set_ylabel("y", fontsize=7)
            ax.tick_params(labelsize=6)

    fig.suptitle("Per-cell FP noise $\\sigma_{FP}$ (MCA p=53)", fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(f"[snr] wrote {out_path}", file=sys.stderr)


def _plot_snr_heatmap(
    snr_hllc: list[np.ndarray],
    snr_rusanov: list[np.ndarray],
    out_path: Path,
) -> None:
    """Save 2x4 SNR_local heatmap (rows: HLLC, Rusanov; cols: rho, u, v, p).

    Iso-contour lines at SNR=1 (white) and SNR=10 (yellow) are overlaid on
    each panel so readers can directly locate those thresholds in the image.
    If a panel's SNR range does not span a contour level, contour() silently
    draws nothing — no special-casing required.
    """
    fig, axes = plt.subplots(2, 4, figsize=(16, 7))
    extent = [0, 1, 0, 1]
    rows = [("HLLC", snr_hllc), ("Rusanov", snr_rusanov)]
    norm = mcolors.LogNorm(vmin=0.01, vmax=1e6)

    for row_idx, (solver_label, snr_list) in enumerate(rows):
        for col_idx, (var_label, snr) in enumerate(zip(VAR_ORDER, snr_list)):
            ax = axes[row_idx, col_idx]
            im = ax.imshow(
                snr, origin="lower", extent=extent, aspect="equal",
                norm=norm, cmap="RdYlGn",
            )
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            ax.set_title(f"{solver_label} SNR({var_label})", fontsize=8)
            ax.set_xlabel("x", fontsize=7)
            ax.set_ylabel("y", fontsize=7)
            ax.tick_params(labelsize=6)
            # Iso-contour lines marking SNR=1 and SNR=10 directly on the image
            ax.contour(
                snr, levels=[1.0, 10.0],
                colors=["white", "yellow"], linewidths=[1.2, 0.9],
                extent=extent, origin="lower",
            )

    fig.suptitle(
        "Local SNR = |$\\mu_{trunc}$| / $\\sigma_{FP}$ (MCA p=53)\n"
        "white contour: SNR=1    yellow contour: SNR=10",
        fontsize=10, fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(f"[snr] wrote {out_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main routine
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Compute SNR metric for Verificarlo MCA 2D ensembles."
    )
    p.add_argument("--root", required=True, type=Path,
                   help="Root directory containing HLLC and Rusanov subdirs.")
    p.add_argument("--hllc-subdir", default="hllc",
                   help="Subdir name under --root for HLLC samples (default: hllc).")
    p.add_argument("--rusanov-subdir", default="rusanov",
                   help="Subdir name under --root for Rusanov samples (default: rusanov).")
    p.add_argument("--expected-n", type=int, default=30,
                   help="Expected number of MCA samples per solver (default: 30).")
    p.add_argument("--gamma", type=float, default=1.4,
                   help="Ratio of specific heats (default: 1.4).")
    p.add_argument("--reference", type=Path, default=None,
                   help="Optional .npz with u_ref_hllc and u_ref_rusanov arrays.")
    p.add_argument("--out-dir", required=True, type=Path,
                   help="Output directory (created if absent).")
    return p.parse_args()


def main() -> None:
    """Entry point: compute SNR metrics and write CSV + PNG outputs."""
    args = _parse_args()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[snr] output directory: {out_dir}", file=sys.stderr)

    # Seed-independence check (fail fast before any expensive I/O)
    hllc_root = args.root / args.hllc_subdir
    rusanov_root = args.root / args.rusanov_subdir
    print(f"[snr] checking seed independence for HLLC ({hllc_root / 'seeds'})",
          file=sys.stderr)
    load_seeds(hllc_root / "seeds", args.expected_n)
    print(f"[snr] checking seed independence for Rusanov ({rusanov_root / 'seeds'})",
          file=sys.stderr)
    load_seeds(rusanov_root / "seeds", args.expected_n)

    # Load MCA ensembles
    print(f"[snr] loading HLLC samples from {hllc_root}",
          file=sys.stderr)
    n_hllc, prim_hllc = _load_prim(
        args.root, args.hllc_subdir, args.gamma, args.expected_n
    )
    print(f"[snr] loading Rusanov samples from {rusanov_root}",
          file=sys.stderr)
    n_rusanov, prim_rusanov = _load_prim(
        args.root, args.rusanov_subdir, args.gamma, args.expected_n
    )

    ny, nx = prim_hllc.shape[1], prim_hllc.shape[2]
    n_cells = ny * nx
    print(f"[snr] grid size: {ny}x{nx} = {n_cells} cells", file=sys.stderr)

    # Optionally load reference
    has_ref = args.reference is not None
    if has_ref:
        print(f"[snr] loading reference from {args.reference}", file=sys.stderr)
        u_ref_hllc, u_ref_rusanov = _load_reference(args.reference)

    # Per-variable processing
    sigma_hllc_fields: list[np.ndarray] = []
    sigma_rusanov_fields: list[np.ndarray] = []
    snr_hllc_fields: list[np.ndarray] = []
    snr_rusanov_fields: list[np.ndarray] = []
    csv_rows: list[dict] = []

    solvers = [
        ("hllc",    prim_hllc,    n_hllc,    u_ref_hllc    if has_ref else None,
         sigma_hllc_fields,    snr_hllc_fields),
        ("rusanov", prim_rusanov, n_rusanov, u_ref_rusanov if has_ref else None,
         sigma_rusanov_fields, snr_rusanov_fields),
    ]

    for solver_name, prim, n_samples, u_ref, sigma_list, snr_list in solvers:
        for vi, var_name in enumerate(VAR_ORDER):
            samples_var = prim[:, :, :, vi]  # (n_samples, ny, nx)

            sigma_fp = compute_sigma_fp_field(samples_var)
            sigma_list.append(sigma_fp)

            row: dict = {
                "solver":       solver_name,
                "precision":    "p53",
                "variable":     var_name,
                "sigma_fp_l1":  float(np.sum(np.abs(sigma_fp))),
                "sigma_fp_max": float(sigma_fp.max()),
                "n_cells":      n_cells,
                "n_samples":    n_samples,
                "mu_trunc_l1":  "",
                "snr_global":   "",
                "snr_median":   "",
                "snr_q05":      "",
            }

            if has_ref:
                u_ref_var = u_ref[:, :, vi]  # (ny, nx)
                mu_trunc, _, snr_local = compute_snr_fields(samples_var, u_ref_var)
                snr_list.append(snr_local)
                snr_global, snr_median, snr_q05 = compute_snr_scalars(
                    mu_trunc, sigma_fp, snr_local
                )
                row["mu_trunc_l1"] = float(np.sum(np.abs(mu_trunc)))
                row["snr_global"]  = snr_global
                row["snr_median"]  = snr_median
                row["snr_q05"]     = snr_q05

            csv_rows.append(row)

    # Write CSV
    csv_path = out_dir / "snr_scalars.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"[snr] wrote {csv_path}", file=sys.stderr)

    # Write sigma heatmap
    sigma_png = out_dir / "sigma_fp_heatmap.png"
    _plot_sigma_heatmap(sigma_hllc_fields, sigma_rusanov_fields, sigma_png)

    # Write SNR heatmap only when reference is present
    if has_ref and snr_hllc_fields and snr_rusanov_fields:
        snr_png = out_dir / "snr_local_heatmap.png"
        _plot_snr_heatmap(snr_hllc_fields, snr_rusanov_fields, snr_png)

    print("[snr] done.", file=sys.stderr)


if __name__ == "__main__":
    main()
