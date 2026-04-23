"""2D Verificarlo MCA analysis: heatmaps + y-slice comparison for HLLC vs Rusanov."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from io_helper import stack_samples, load_seeds, cons_to_prim
from plot_divergence_marker import plot_single_panel


# ---------------------------------------------------------------------------
# Significant-digits computation (mirrors verificarlo_analysis.py exactly)
# ---------------------------------------------------------------------------

def significant_digits_2d(samples: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute per-cell significant digits for a 2D field stack.

    Parameters
    ----------
    samples : (N, ny, nx) float64 — N MCA realisations of a single scalar field

    Returns
    -------
    mean, std, sig : each (ny, nx)
    """
    mean = samples.mean(axis=0)
    std = samples.std(axis=0, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        sig = -np.log10(np.abs(std / mean))
        sig = np.where(np.isfinite(sig), sig, np.nan)
    return mean, std, sig


# ---------------------------------------------------------------------------
# Heatmap figure (2x2 grid: [HLLC-mean, Rusanov-mean; HLLC-sig, Rusanov-sig])
# ---------------------------------------------------------------------------

def _plot_heatmap(
    mean_a: np.ndarray,
    sig_a: np.ndarray,
    mean_b: np.ndarray,
    sig_b: np.ndarray,
    label_a: str,
    label_b: str,
    var_label: str,
    out_path: Path,
) -> None:
    """Save a 2x2 heatmap PNG for one primitive variable."""
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    extent = [0, 1, 0, 1]

    # Row 0: mean fields
    for ax, mean, title in [
        (axes[0, 0], mean_a, f"{label_a} mean {var_label}"),
        (axes[0, 1], mean_b, f"{label_b} mean {var_label}"),
    ]:
        im = ax.imshow(mean, origin="lower", extent=extent, aspect="equal")
        fig.colorbar(im, ax=ax)
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("x")
        ax.set_ylabel("y")

    # Row 1: significant digits
    sig_a_disp = np.clip(np.nan_to_num(sig_a, nan=16.0), 0, 16)
    sig_b_disp = np.clip(np.nan_to_num(sig_b, nan=16.0), 0, 16)
    for ax, sig_disp, title in [
        (axes[1, 0], sig_a_disp, f"{label_a} significant digits"),
        (axes[1, 1], sig_b_disp, f"{label_b} significant digits"),
    ]:
        im = ax.imshow(sig_disp, origin="lower", extent=extent, aspect="equal",
                       cmap="viridis", vmin=0, vmax=16)
        cb = fig.colorbar(im, ax=ax)
        cb.set_label("significant digits", fontsize=8)
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("x")
        ax.set_ylabel("y")

    fig.suptitle(f"HLLC vs Rusanov — {var_label}", fontsize=11, fontweight="bold")
    fig.tight_layout()
    fig.savefig(str(out_path), dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# y-slice figure (3 vertically-stacked subplots: rho, u, p)
# ---------------------------------------------------------------------------

def _plot_slice(
    x: np.ndarray,
    prim_a: np.ndarray,
    prim_b: np.ndarray,
    sigma_a: np.ndarray,
    sigma_b: np.ndarray,
    j_slice: int,
    slice_y: float,
    label_a: str,
    label_b: str,
    out_path: Path,
) -> None:
    """Save the y-slice comparison PNG.

    Parameters
    ----------
    prim_a / prim_b : (ny, nx, 4) primitive-variable mean arrays.
    sigma_a / sigma_b : (ny, nx, 4) per-cell std arrays.
    """
    fig, axes = plt.subplots(3, 1, figsize=(8, 11), sharex=True,
                             gridspec_kw={"hspace": 0.55})
    fig.suptitle(f"y = {slice_y:g} slice — HLLC vs Rusanov", fontsize=11, fontweight="bold")

    var_info = [
        (0, "rho", r"$\rho$"),
        (1, "u",   r"$u$"),
        (3, "p",   r"$p$"),
    ]

    for ax, (vi, vname, vlabel) in zip(axes, var_info):
        a_slice = prim_a[j_slice, :, vi]
        b_slice = prim_b[j_slice, :, vi]
        nf_a = sigma_a[j_slice, :, vi]
        nf_b = sigma_b[j_slice, :, vi]

        # Title is set on the axes below with extra pad so divergence-marker
        # onset labels (placed above the data point) don't collide with it.
        plot_single_panel(
            ax, x, a_slice, x, b_slice,
            label_a=label_a,
            label_b=label_b,
            variable=vname,
            mode="noise_floor",
            noise_floor_a=nf_a,
            noise_floor_b=nf_b,
        )
        ax.set_title(f"y = {slice_y:g} slice — {vlabel}", fontsize=10, pad=18)

    axes[-1].set_xlabel("x")
    fig.savefig(str(out_path), dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="2D Verificarlo MCA analysis: heatmaps + y-slice for HLLC vs Rusanov."
    )
    p.add_argument("--root", required=True, metavar="DIR",
                   help="Root experiment directory containing the two solver subdirs.")
    p.add_argument("--hllc-subdir", default="hllc", metavar="STR")
    p.add_argument("--rusanov-subdir", default="rusanov", metavar="STR")
    p.add_argument("--gamma", type=float, default=1.4)
    p.add_argument("--expected-n", type=int, default=30, metavar="N")
    p.add_argument("--out-dir", default="docs/week4/figures/a3", metavar="DIR")
    p.add_argument("--slice-y", type=float, default=0.5, metavar="FLOAT")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    root = Path(args.root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    label_a = "HLLC"
    label_b = "Rusanov"
    hllc_root = root / args.hllc_subdir
    rusanov_root = root / args.rusanov_subdir

    # ---- seed-independence check (fail fast) --------------------------------
    load_seeds(hllc_root / "seeds", args.expected_n)
    load_seeds(rusanov_root / "seeds", args.expected_n)

    # ---- load and stack samples ---------------------------------------------
    h_a, cons_a, _ = stack_samples(hllc_root)
    h_b, cons_b, _ = stack_samples(rusanov_root)

    # Consistency: both grids must share the same shape
    if (h_a.nx, h_a.ny) != (h_b.nx, h_b.ny):
        sys.exit(
            f"[analysis-2d] ERROR: grid shape mismatch: "
            f"HLLC {h_a.nx}x{h_a.ny} vs Rusanov {h_b.nx}x{h_b.ny}"
        )

    # Use h_a as the reference header (grids agree)
    h = h_a

    # ---- convert to primitive variables: (N, ny, nx, 4) --------------------
    prim_a = cons_to_prim(cons_a.astype(np.float64), args.gamma)
    prim_b = cons_to_prim(cons_b.astype(np.float64), args.gamma)

    # ---- compute per-cell statistics ----------------------------------------
    # mean/std/sig per variable: (ny, nx)
    mean_a, std_a, sig_a = {}, {}, {}
    mean_b, std_b, sig_b = {}, {}, {}
    VAR_IDX = {"rho": 0, "u": 1, "v": 2, "p": 3}
    for vname, vi in VAR_IDX.items():
        mean_a[vname], std_a[vname], sig_a[vname] = significant_digits_2d(prim_a[:, :, :, vi])
        mean_b[vname], std_b[vname], sig_b[vname] = significant_digits_2d(prim_b[:, :, :, vi])

    # Also keep full std arrays shaped (ny, nx, 4) for the slice figure
    sigma_a_full = np.stack([std_a[v] for v in ("rho", "u", "v", "p")], axis=-1)
    sigma_b_full = np.stack([std_b[v] for v in ("rho", "u", "v", "p")], axis=-1)
    mean_a_full  = np.stack([mean_a[v] for v in ("rho", "u", "v", "p")], axis=-1)
    mean_b_full  = np.stack([mean_b[v] for v in ("rho", "u", "v", "p")], axis=-1)

    # ---- heatmap figures: density and pressure ------------------------------
    for vname, var_label in [("rho", "density"), ("p", "pressure")]:
        fname_map = {
            "rho": "heatmap_density_hllc_vs_rusanov.png",
            "p":   "heatmap_pressure_hllc_vs_rusanov.png",
        }
        out_path = out_dir / fname_map[vname]
        _plot_heatmap(
            mean_a[vname], sig_a[vname],
            mean_b[vname], sig_b[vname],
            label_a, label_b, var_label, out_path,
        )
        print(f"[analysis-2d] wrote {out_path}", file=sys.stderr)

    # ---- y = slice_y horizontal slice figure --------------------------------
    # Cell-centre y-coordinates: y_j = (j + 0.5) * dy
    j_slice = int(round((args.slice_y - 0.5 * h.dy) / h.dy))
    j_slice = max(0, min(h.ny - 1, j_slice))
    x = (np.arange(h.nx) + 0.5) * h.dx

    slice_str = f"{args.slice_y:g}"
    slice_path = out_dir / f"slice_y{slice_str}_comparison.png"
    _plot_slice(
        x,
        mean_a_full, mean_b_full,
        sigma_a_full, sigma_b_full,
        j_slice, args.slice_y,
        label_a, label_b,
        slice_path,
    )
    print(f"[analysis-2d] wrote {slice_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
