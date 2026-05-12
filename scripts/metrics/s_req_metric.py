"""Truncation-anchored required significant digits s_req(N).

Computes E_trunc(N) = ||μ_sample(N) − U_ref||_1 / max(||U_ref||_1, floor_L1)
on a coarse grid against an integer-ratio block-averaged double reference,
and emits s_req(N) = -log10(E_trunc) + 1 per primitive variable (rho, u, v, p).

Floor design (related to but NOT identical to snr_metric / losos_metric):

    floor_L1 = sqrt(eps_real) * max_j |U_ref(j)| * N_cells     # this script

vs.

    floor_per_cell = max(sqrt(eps_real) * max_j |U_ref(j)|,    # snr / losos
                         sqrt(eps_real))

The two are the same noise-budget reasoning at different aggregation levels:
snr / losos normalise pointwise ratios (per-cell denominator), so their floor
is a per-cell quantity. s_req normalises an L1-aggregated quantity, so the
same per-cell budget multiplies through N_cells. This is intentional — using
the per-cell floor as an L1 floor would underflow on large grids.

Inf clamp: when E_trunc == 0 (perfect match) -log10 yields +inf, which we
clamp to losos_metric.SIG_DIGITS_CEILING — same constant as the LoSoS
ceiling, intentionally reused to avoid a second magic ceiling.

Side output: a .npz with primitive-form u_ref_hllc / u_ref_rusanov arrays
shaped (ny, nx, 4) at the coarse grid, ready for losos_metric.py --reference.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # io_helper at scripts/ root
sys.path.insert(0, str(Path(__file__).resolve().parent))           # sibling: losos_metric
from io_helper import read_binary, cons_to_prim
from losos_metric import SIG_DIGITS_CEILING

# Primitive variable names and order — mirrors IDX_* in io_helper.py.
VAR_ORDER = ("rho", "u", "v", "p")

# ---------------------------------------------------------------------------
# Core compute functions (public API; called by tests and CLI)
# ---------------------------------------------------------------------------

def block_average_to_shape(fine: np.ndarray, target_ny: int, target_nx: int) -> np.ndarray:
    """Conservation-preserving integer-ratio block average.

    Parameters
    ----------
    fine : ndarray of shape (ny_f, nx_f, nvars). Both ny_f and nx_f MUST be
           integer multiples of the target shape.
    target_ny, target_nx : target coarse-grid dimensions.

    Returns
    -------
    coarse : ndarray of shape (target_ny, target_nx, nvars).
             Each coarse cell is the mean of the fine cells it covers.
    """
    ny_f, nx_f, _ = fine.shape
    if target_ny <= 0 or target_nx <= 0:
        raise ValueError(f"target shape must be positive, got ({target_ny}, {target_nx})")
    if ny_f % target_ny != 0 or nx_f % target_nx != 0:
        raise ValueError(
            f"Block-average requires integer reference/candidate ratio; "
            f"got fine ({ny_f}, {nx_f}) and target ({target_ny}, {target_nx})"
        )
    ry = ny_f // target_ny
    rx = nx_f // target_nx
    f = fine.astype(np.float64, copy=False)
    return f.reshape(
        target_ny, ry,
        target_nx, rx,
        f.shape[2],
    ).mean(axis=(1, 3))


def block_average_4x_to_coarse(fine: np.ndarray) -> np.ndarray:
    """Backward-compatible 4x coarsening helper used by existing tests."""
    ny_f, nx_f, _ = fine.shape
    if ny_f % 4 != 0 or nx_f % 4 != 0:
        raise ValueError(f"Block-average requires factor-4 grid; got ({ny_f}, {nx_f})")
    return block_average_to_shape(fine, ny_f // 4, nx_f // 4)


def compute_e_trunc(
    mu: np.ndarray,
    u_ref: np.ndarray,
    eps_real: float,
) -> dict[str, float]:
    """Per-variable E_trunc with precision-aware floor.

    Parameters
    ----------
    mu, u_ref : (ny, nx, nvars=4) primitive arrays at the same grid.
    eps_real  : machine epsilon of the candidate's REAL type (e.g. 2.22e-16
                for float64). Used to set floor_L1.

    Returns
    -------
    Dict keyed by VAR_ORDER. Each value is the dimensionless E_trunc for
    that variable.
    """
    if mu.shape != u_ref.shape:
        raise ValueError(f"shape mismatch: mu {mu.shape} vs u_ref {u_ref.shape}")
    if mu.shape[-1] != len(VAR_ORDER):
        raise ValueError(f"last axis must be {len(VAR_ORDER)}, got {mu.shape[-1]}")

    mu_64 = mu.astype(np.float64, copy=False)
    ref_64 = u_ref.astype(np.float64, copy=False)
    n_cells = ref_64.shape[0] * ref_64.shape[1]
    sqrt_eps = float(np.sqrt(eps_real))

    out: dict[str, float] = {}
    for k, name in enumerate(VAR_ORDER):
        diff_l1 = float(np.abs(mu_64[..., k] - ref_64[..., k]).sum())
        ref_l1 = float(np.abs(ref_64[..., k]).sum())
        ref_inf = float(np.abs(ref_64[..., k]).max())
        floor_l1 = sqrt_eps * ref_inf * n_cells
        denom = max(ref_l1, floor_l1)
        # denom is strictly > 0 because sqrt_eps > 0 and either ref_inf > 0
        # or we're in a vacuum-like cell where ref_l1 == 0 and floor_l1 may
        # also collapse to 0 — guard with a final absolute floor.
        if denom == 0.0:
            denom = sqrt_eps
        out[name] = diff_l1 / denom
    return out


def compute_s_req(e_trunc: float) -> float:
    """s_req = -log10(E_trunc) + 1, clamped to [0, SIG_DIGITS_CEILING].

    Reuses losos_metric.SIG_DIGITS_CEILING to keep a single ceiling
    constant across the project.
    """
    with np.errstate(divide="ignore"):
        raw = -np.log10(e_trunc) + 1.0
    if not np.isfinite(raw):
        return SIG_DIGITS_CEILING
    return float(np.clip(raw, 0.0, SIG_DIGITS_CEILING))


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def _load_coarse_candidate(bin_path: Path, gamma: float) -> np.ndarray:
    """Read a candidate .bin (e.g. deterministic 200²) and return primitive (ny, nx, 4)."""
    h, cons = read_binary(bin_path)
    if cons.ndim != 3 or cons.shape[-1] != len(VAR_ORDER):
        raise ValueError(f"unexpected candidate shape {cons.shape} in {bin_path}")
    return cons_to_prim(cons.astype(np.float64), gamma)


def _load_block_avg_reference(
    bin_path: Path, gamma: float, target_shape: tuple[int, int]
) -> tuple[np.ndarray, int]:
    """Read fine reference, block-average conserved variables, convert to primitive.

    Returns (prim_coarse (ny, nx, 4), fine_N).
    """
    h, cons_fine = read_binary(bin_path)
    if cons_fine.ndim != 3 or cons_fine.shape[-1] != len(VAR_ORDER):
        raise ValueError(f"unexpected reference shape {cons_fine.shape} in {bin_path}")
    target_ny, target_nx = target_shape
    cons_coarse = block_average_to_shape(
        cons_fine.astype(np.float64), target_ny, target_nx
    )
    prim_coarse = cons_to_prim(cons_coarse, gamma)
    return prim_coarse, h.nx


# ---------------------------------------------------------------------------
# CSV emission
# ---------------------------------------------------------------------------

_CSV_FIELDNAMES = [
    "solver", "variable", "N",
    "U_ref_L1", "U_ref_inf", "n_cells", "floor_L1",
    "mu_trunc_l1", "E_trunc", "s_req",
]


def _row_for(
    solver: str, variable: str, N: int,
    mu: np.ndarray, u_ref: np.ndarray, eps_real: float,
    var_index: int,
) -> dict:
    n_cells = u_ref.shape[0] * u_ref.shape[1]
    sqrt_eps = float(np.sqrt(eps_real))
    diff_l1 = float(np.abs(mu[..., var_index] - u_ref[..., var_index]).sum())
    ref_l1 = float(np.abs(u_ref[..., var_index]).sum())
    ref_inf = float(np.abs(u_ref[..., var_index]).max())
    floor_l1 = sqrt_eps * ref_inf * n_cells
    denom = max(ref_l1, floor_l1) or sqrt_eps
    e_trunc = diff_l1 / denom
    return {
        "solver": solver,
        "variable": variable,
        "N": N,
        "U_ref_L1": ref_l1,
        "U_ref_inf": ref_inf,
        "n_cells": n_cells,
        "floor_L1": floor_l1,
        "mu_trunc_l1": diff_l1,
        "E_trunc": e_trunc,
        "s_req": compute_s_req(e_trunc),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Compute s_req(N) for HLLC and Rusanov via block-averaged references."
    )
    p.add_argument("--candidate-hllc-bin",  required=True, type=Path)
    p.add_argument("--candidate-rusanov-bin", required=True, type=Path)
    p.add_argument("--reference-hllc-bin",  required=True, type=Path)
    p.add_argument("--reference-rusanov-bin", required=True, type=Path)
    p.add_argument("--gamma", type=float, default=1.4,
                   help="Ratio of specific heats (default: 1.4).")
    p.add_argument("--out-csv", required=True, type=Path,
                   help="Output CSV path (parent dir created if absent).")
    p.add_argument("--out-ref-npz", required=True, type=Path,
                   help="Side-output .npz with u_ref_hllc / u_ref_rusanov primitive arrays "
                        "for losos_metric.py --reference.")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    args.out_ref_npz.parent.mkdir(parents=True, exist_ok=True)

    eps_real = float(np.finfo(np.float64).eps)

    print("[s_req] loading candidates…", file=sys.stderr)
    mu_hllc = _load_coarse_candidate(args.candidate_hllc_bin, args.gamma)
    mu_rusanov = _load_coarse_candidate(args.candidate_rusanov_bin, args.gamma)

    print("[s_req] loading + block-averaging references…", file=sys.stderr)
    ref_hllc, fine_N_h = _load_block_avg_reference(
        args.reference_hllc_bin, args.gamma, mu_hllc.shape[:2]
    )
    ref_rusanov, fine_N_r = _load_block_avg_reference(
        args.reference_rusanov_bin, args.gamma, mu_rusanov.shape[:2]
    )

    if mu_hllc.shape != ref_hllc.shape:
        raise ValueError(
            f"HLLC shape mismatch: candidate {mu_hllc.shape} vs block-avg ref {ref_hllc.shape}"
        )
    if mu_rusanov.shape != ref_rusanov.shape:
        raise ValueError(
            f"Rusanov shape mismatch: candidate {mu_rusanov.shape} vs block-avg ref {ref_rusanov.shape}"
        )

    N = mu_hllc.shape[0]
    print(
        f"[s_req] coarse grid: {N}² "
        f"(fine refs were HLLC {fine_N_h}², Rusanov {fine_N_r}²)",
        file=sys.stderr,
    )

    rows: list[dict] = []
    for solver, mu, u_ref in (
        ("hllc", mu_hllc, ref_hllc),
        ("rusanov", mu_rusanov, ref_rusanov),
    ):
        for vi, var_name in enumerate(VAR_ORDER):
            rows.append(_row_for(solver, var_name, N, mu, u_ref, eps_real, vi))

    with open(args.out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[s_req] wrote {args.out_csv}", file=sys.stderr)

    np.savez(
        args.out_ref_npz,
        u_ref_hllc=ref_hllc,
        u_ref_rusanov=ref_rusanov,
    )
    print(f"[s_req] wrote {args.out_ref_npz}", file=sys.stderr)
    print("[s_req] done.", file=sys.stderr)


if __name__ == "__main__":
    main()
