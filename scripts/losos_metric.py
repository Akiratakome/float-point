"""LoSoS (Loss of Significance) 3-field metric for Verificarlo MCA ensembles.

Separates two conceptually-distinct "significant digits" quantities:
  - Reliability  : how clustered are the 30 MCA samples? (classical Verificarlo)
  - Accuracy     : how close is the sample mean to a reference solution?
  - Worst        : per-cell min(reliability, accuracy) — "digits actually trustworthy"

All three fields are computed per-cell first (field-first principle), then
aggregated spatially.  Operator order is identical to snr_metric.py.

Edge-case policy
----------------
- sigma_fp == 0 exactly  → ratio argument to -log10 is 0 → log10(0) = -inf.
  We use np.errstate(divide="ignore", invalid="ignore") to suppress the
  RuntimeWarning.  The raw -log10 value is +inf in that case; we immediately
  clamp it to SIG_DIGITS_CEILING (20.0) via nan_to_num so that all emitted
  fields are strictly finite and downstream percentile/mean follow the spec
  literal formulas without any finite-only filtering workaround.
- mu_sample == 0 / u_ref == 0 : covered by max(|...|, floor_var) in denominator.
- All three fields are guaranteed finite in [0, SIG_DIGITS_CEILING].
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from io_helper import stack_samples, load_seeds, cons_to_prim

# Primitive variable names and order — mirrors IDX_* in io_helper.py.
VAR_ORDER = ("rho", "u", "v", "p")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_EPS = np.finfo(np.float64).eps
_SQRT_EPS = np.sqrt(_EPS)

# Ceiling for significant-digit counts: float64 gives 15–17 sig digits, so
# 20.0 is safely above any physically meaningful value and serves as the
# clamp target for cells where sigma_fp == 0 or mu == u_ref exactly.
SIG_DIGITS_CEILING = 20.0

# Display cap: values are clamped to this for heatmap display.
_DISPLAY_CAP = 16.0

_CSV_FIELDNAMES = [
    "solver", "precision", "variable",
    "s_reliability_min", "s_reliability_q05", "s_reliability_mean",
    "s_accuracy_min",    "s_accuracy_q05",    "s_accuracy_mean",
    "s_worst_min",       "s_worst_q05",       "s_worst_mean",
    "n_cells", "n_samples",
]


# ---------------------------------------------------------------------------
# Floor helper (same convention as snr_metric.py)
# ---------------------------------------------------------------------------

def _var_floor(u_ref_var: np.ndarray) -> float:
    """Return precision-aware floor: sqrt(eps) * max_j |U_ref(j)|, never zero."""
    return max(_SQRT_EPS * float(np.abs(u_ref_var).max()), _SQRT_EPS)


# ---------------------------------------------------------------------------
# Core computation functions (public API, called by tests)
# ---------------------------------------------------------------------------

def compute_s_reliability(
    samples: np.ndarray,
    floor: float,
) -> np.ndarray:
    """Compute per-cell reliability field: -log10( sigma_fp / max(|mu|, floor) ).

    Parameters
    ----------
    samples : (n_samples, ny, nx) float64 array for a single variable.
    floor   : never-vanishing denominator floor (use _var_floor(u_ref_var)).

    Returns
    -------
    s_reliability : (ny, nx) significant-digit count, clamped to
                    [0, SIG_DIGITS_CEILING].  Strictly finite — no NaN, no inf.
    """
    mu = samples.mean(axis=0)                           # (ny, nx)
    sigma = samples.std(axis=0, ddof=1)                 # (ny, nx)
    denom = np.maximum(np.abs(mu), floor)               # (ny, nx), >= floor > 0

    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = sigma / denom
        raw = -np.log10(ratio)                          # +inf where sigma==0

    # Clamp: +inf (sigma==0) → SIG_DIGITS_CEILING; NaN → 0; -inf → 0.
    return np.nan_to_num(raw, nan=0.0,
                         posinf=SIG_DIGITS_CEILING, neginf=0.0)


def compute_s_accuracy(
    samples: np.ndarray,
    u_ref: np.ndarray,
    floor: float,
) -> np.ndarray:
    """Compute per-cell accuracy field: -log10( |mu - u_ref| / max(|u_ref|, floor) ).

    Parameters
    ----------
    samples : (n_samples, ny, nx) float64 array for a single variable.
    u_ref   : (ny, nx) reference solution for the same variable.
    floor   : never-vanishing denominator floor (use _var_floor(u_ref)).

    Returns
    -------
    s_accuracy : (ny, nx) significant-digit count, clamped to
                 [0, SIG_DIGITS_CEILING].  Strictly finite — no NaN, no inf.
    """
    mu = samples.mean(axis=0)                           # (ny, nx)
    denom = np.maximum(np.abs(u_ref), floor)            # (ny, nx), >= floor > 0
    abs_err = np.abs(mu - u_ref)                        # (ny, nx), >= 0

    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = abs_err / denom
        raw = -np.log10(ratio)                          # +inf where abs_err==0

    # Clamp: +inf (mu==u_ref) → SIG_DIGITS_CEILING; NaN → 0; -inf → 0.
    return np.nan_to_num(raw, nan=0.0,
                         posinf=SIG_DIGITS_CEILING, neginf=0.0)


def compute_s_worst(
    s_reliability: np.ndarray,
    s_accuracy: np.ndarray,
) -> np.ndarray:
    """Per-cell minimum of reliability and accuracy fields."""
    return np.minimum(s_reliability, s_accuracy)


def compute_losos_fields(
    samples: np.ndarray,
    u_ref: np.ndarray | None,
    floor: float,
) -> tuple[np.ndarray, np.ndarray | None, np.ndarray | None]:
    """Compute all three LoSoS fields for one variable.

    Parameters
    ----------
    samples : (n_samples, ny, nx) float64.
    u_ref   : (ny, nx) reference or None.
    floor   : _var_floor(u_ref_var) — pass even when u_ref is None,
              using _SQRT_EPS as the absolute floor.

    Returns
    -------
    s_rel   : (ny, nx) always.
    s_acc   : (ny, nx) when u_ref is not None, else None.
    s_worst : (ny, nx) when u_ref is not None, else None.
    """
    s_rel = compute_s_reliability(samples, floor)
    if u_ref is None:
        return s_rel, None, None
    s_acc = compute_s_accuracy(samples, u_ref, floor)
    s_wrst = compute_s_worst(s_rel, s_acc)
    return s_rel, s_acc, s_wrst


def compute_losos_scalars(
    field: np.ndarray,
) -> tuple[float, float, float]:
    """Compute (min, q05, mean) for a LoSoS field.

    Fields are guaranteed finite (clamped to [0, SIG_DIGITS_CEILING] at
    computation time), so these are the literal spec formulas with no
    finite-only filtering.

    Returns
    -------
    f_min  : minimum value (worst cell)
    f_q05  : 5th-percentile (worst 5% region)
    f_mean : spatial mean
    """
    f_min  = float(np.min(field))
    f_q05  = float(np.percentile(field, 5))
    f_mean = float(np.mean(field))
    return f_min, f_q05, f_mean


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _load_prim(
    root: Path, subdir: str, gamma: float, expected_n: int
) -> tuple[int, np.ndarray]:
    """Load MCA samples and convert to primitive variables.

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
    return (
        data["u_ref_hllc"].astype(np.float64),
        data["u_ref_rusanov"].astype(np.float64),
    )


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

def _clamp_for_display(field: np.ndarray, cap: float = _DISPLAY_CAP) -> np.ndarray:
    """Replace +inf with cap and clamp to [0, cap] for imshow."""
    return np.clip(np.where(np.isinf(field), cap, field), 0.0, cap)


def _plot_losos_heatmap(
    fields_hllc: list[np.ndarray],
    fields_rusanov: list[np.ndarray],
    title: str,
    out_path: Path,
) -> None:
    """Save 2×4 LoSoS field heatmap (rows: HLLC, Rusanov; cols: rho, u, v, p)."""
    fig, axes = plt.subplots(2, 4, figsize=(16, 7))
    extent = [0, 1, 0, 1]
    rows = [("HLLC", fields_hllc), ("Rusanov", fields_rusanov)]

    for row_idx, (solver_label, field_list) in enumerate(rows):
        for col_idx, (var_label, field) in enumerate(zip(VAR_ORDER, field_list)):
            ax = axes[row_idx, col_idx]
            display = _clamp_for_display(field)
            im = ax.imshow(
                display,
                origin="lower",
                extent=extent,
                aspect="equal",
                cmap="viridis",
                vmin=0,
                vmax=_DISPLAY_CAP,
            )
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            ax.set_title(f"{solver_label}  {var_label}", fontsize=8)
            ax.set_xlabel("x", fontsize=7)
            ax.set_ylabel("y", fontsize=7)
            ax.tick_params(labelsize=6)

    fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(f"[losos] wrote {out_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main routine
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Compute LoSoS 3-field metric for Verificarlo MCA 2D ensembles."
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
    """Entry point: compute LoSoS metrics and write CSV + PNG outputs."""
    args = _parse_args()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[losos] output directory: {out_dir}", file=sys.stderr)

    # Seed-independence check (fail fast before any expensive I/O)
    hllc_root = args.root / args.hllc_subdir
    rusanov_root = args.root / args.rusanov_subdir
    print(f"[losos] checking seed independence for HLLC ({hllc_root / 'seeds'})",
          file=sys.stderr)
    load_seeds(hllc_root / "seeds", args.expected_n)
    print(f"[losos] checking seed independence for Rusanov ({rusanov_root / 'seeds'})",
          file=sys.stderr)
    load_seeds(rusanov_root / "seeds", args.expected_n)

    # Load MCA ensembles
    print(f"[losos] loading HLLC samples from {hllc_root}", file=sys.stderr)
    n_hllc, prim_hllc = _load_prim(
        args.root, args.hllc_subdir, args.gamma, args.expected_n
    )
    print(f"[losos] loading Rusanov samples from {rusanov_root}", file=sys.stderr)
    n_rusanov, prim_rusanov = _load_prim(
        args.root, args.rusanov_subdir, args.gamma, args.expected_n
    )

    ny, nx = prim_hllc.shape[1], prim_hllc.shape[2]
    n_cells = ny * nx
    print(f"[losos] grid size: {ny}x{nx} = {n_cells} cells", file=sys.stderr)

    # Optionally load reference
    has_ref = args.reference is not None
    u_ref_hllc: np.ndarray | None = None
    u_ref_rusanov: np.ndarray | None = None
    if has_ref:
        print(f"[losos] loading reference from {args.reference}", file=sys.stderr)
        u_ref_hllc, u_ref_rusanov = _load_reference(args.reference)
    else:
        print("[losos] no reference provided — only s_reliability computed",
              file=sys.stderr)

    # Per-variable processing
    rel_hllc_fields:   list[np.ndarray] = []
    rel_rusanov_fields: list[np.ndarray] = []
    acc_hllc_fields:   list[np.ndarray] = []
    acc_rusanov_fields: list[np.ndarray] = []
    wst_hllc_fields:   list[np.ndarray] = []
    wst_rusanov_fields: list[np.ndarray] = []
    csv_rows: list[dict] = []

    solvers = [
        ("hllc",    prim_hllc,    n_hllc,    u_ref_hllc,
         rel_hllc_fields,    acc_hllc_fields,    wst_hllc_fields),
        ("rusanov", prim_rusanov, n_rusanov, u_ref_rusanov,
         rel_rusanov_fields, acc_rusanov_fields, wst_rusanov_fields),
    ]

    for solver_name, prim, n_samples, u_ref_all, rel_list, acc_list, wst_list in solvers:
        for vi, var_name in enumerate(VAR_ORDER):
            samples_var = prim[:, :, :, vi]                 # (n_samples, ny, nx)

            # Compute floor from reference if available, else absolute floor only.
            if u_ref_all is not None:
                u_ref_var = u_ref_all[:, :, vi]             # (ny, nx)
                floor = _var_floor(u_ref_var)
            else:
                u_ref_var = None
                floor = _SQRT_EPS

            s_rel, s_acc, s_wst = compute_losos_fields(samples_var, u_ref_var, floor)

            rel_list.append(s_rel)

            row: dict = {
                "solver":    solver_name,
                "precision": "p53",
                "variable":  var_name,
                "n_cells":   n_cells,
                "n_samples": n_samples,
            }

            # Reliability scalars — always
            r_min, r_q05, r_mean = compute_losos_scalars(s_rel)
            row["s_reliability_min"]  = r_min
            row["s_reliability_q05"]  = r_q05
            row["s_reliability_mean"] = r_mean

            # Accuracy / worst scalars — only with reference
            if has_ref and s_acc is not None and s_wst is not None:
                acc_list.append(s_acc)
                wst_list.append(s_wst)
                a_min, a_q05, a_mean = compute_losos_scalars(s_acc)
                w_min, w_q05, w_mean = compute_losos_scalars(s_wst)
                row["s_accuracy_min"]  = a_min
                row["s_accuracy_q05"]  = a_q05
                row["s_accuracy_mean"] = a_mean
                row["s_worst_min"]     = w_min
                row["s_worst_q05"]     = w_q05
                row["s_worst_mean"]    = w_mean
            else:
                row["s_accuracy_min"]  = ""
                row["s_accuracy_q05"]  = ""
                row["s_accuracy_mean"] = ""
                row["s_worst_min"]     = ""
                row["s_worst_q05"]     = ""
                row["s_worst_mean"]    = ""

            csv_rows.append(row)

    # Write CSV
    csv_path = out_dir / "losos_scalars.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"[losos] wrote {csv_path}", file=sys.stderr)

    # Write reliability heatmap (always)
    rel_png = out_dir / "losos_reliability_heatmap.png"
    _plot_losos_heatmap(
        rel_hllc_fields, rel_rusanov_fields,
        "LoSoS Reliability  $s_{rel}$ = $-\\log_{10}(\\sigma_{FP}/|\\mu|)$  (MCA p=53)",
        rel_png,
    )

    # Write accuracy and worst heatmaps only when reference is present
    if has_ref and acc_hllc_fields and acc_rusanov_fields:
        acc_png = out_dir / "losos_accuracy_heatmap.png"
        _plot_losos_heatmap(
            acc_hllc_fields, acc_rusanov_fields,
            "LoSoS Accuracy  $s_{acc}$ = $-\\log_{10}(|\\mu - u_{ref}|/|u_{ref}|)$  (MCA p=53)",
            acc_png,
        )
        wst_png = out_dir / "losos_worst_heatmap.png"
        _plot_losos_heatmap(
            wst_hllc_fields, wst_rusanov_fields,
            "LoSoS Worst  $s_{worst}$ = $\\min(s_{rel}, s_{acc})$  (MCA p=53)",
            wst_png,
        )

    print("[losos] done.", file=sys.stderr)


if __name__ == "__main__":
    main()
