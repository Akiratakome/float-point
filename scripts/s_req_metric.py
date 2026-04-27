"""Truncation-anchored required significant digits s_req(N).

Computes E_trunc(N) = ||μ_sample(N) − U_ref||_1 / max(||U_ref||_1, floor_L1)
on a coarse 200² grid against a 4×4 block-averaged 800² double reference,
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

sys.path.insert(0, str(Path(__file__).parent))
from io_helper import read_binary, cons_to_prim
from losos_metric import SIG_DIGITS_CEILING

# Primitive variable names and order — mirrors IDX_* in io_helper.py.
VAR_ORDER = ("rho", "u", "v", "p")

# Coarsening factor: 800² fine reference → 200² coarse candidate grid.
# Hardcoded as 4 because the only candidate-vs-reference pair this round is
# 200² ↔ 800². Generalisation to other ratios is deferred to next round.
_BLOCK_FACTOR = 4


# ---------------------------------------------------------------------------
# Core compute functions (public API; called by tests and CLI)
# ---------------------------------------------------------------------------

def block_average_4x_to_coarse(fine: np.ndarray) -> np.ndarray:
    """Conservation-preserving 4×4 block average.

    Parameters
    ----------
    fine : ndarray of shape (ny_f, nx_f, nvars). Both ny_f and nx_f MUST be
           divisible by 4. Acts on the leading two spatial axes only.

    Returns
    -------
    coarse : ndarray of shape (ny_f//4, nx_f//4, nvars).
             Each coarse cell == mean of the 16 fine cells it covers.
             Conservation: coarse.sum() * 16 == fine.sum() (float64 exact).
    """
    ny_f, nx_f, _ = fine.shape
    if ny_f % _BLOCK_FACTOR != 0 or nx_f % _BLOCK_FACTOR != 0:
        raise ValueError(
            f"Block-average requires factor-{_BLOCK_FACTOR} grid; "
            f"got ({ny_f}, {nx_f})"
        )
    f = fine.astype(np.float64, copy=False)
    return f.reshape(
        ny_f // _BLOCK_FACTOR, _BLOCK_FACTOR,
        nx_f // _BLOCK_FACTOR, _BLOCK_FACTOR,
        f.shape[2],
    ).mean(axis=(1, 3))


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
