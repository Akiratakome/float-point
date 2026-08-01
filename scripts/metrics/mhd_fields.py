"""Primitive MHD field extraction and same-grid field norms."""

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path

import numpy as np

_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from snr_metric import compute_sigma_fp_field


FIELD_NAMES = ("rho", "vx", "By", "p")
GATE_FIELDS = ("rho", "By", "p")
_SQRT_EPS = float(np.sqrt(np.finfo(np.float64).eps))


def _as_mhd_array(arr: np.ndarray, name: str) -> np.ndarray:
    out = np.asarray(arr)
    if out.ndim != 3 or out.shape[-1] != 9:
        raise ValueError(f"{name} must have shape (ny, nx, 9)")
    return out


def mhd_primitive_fields(arr: np.ndarray, gamma: float) -> dict[str, np.ndarray]:
    """Return rho, vx, By, and pressure from conserved ideal-MHD fields."""

    state = _as_mhd_array(arr, "arr")

    rho = state[..., 0]
    mx = state[..., 1]
    my = state[..., 2]
    mz = state[..., 3]
    bx = state[..., 4]
    by = state[..., 5]
    bz = state[..., 6]
    energy = state[..., 7]

    vx = mx / rho
    vy = my / rho
    vz = mz / rho
    kinetic = 0.5 * rho * (vx * vx + vy * vy + vz * vz)
    magnetic = 0.5 * (bx * bx + by * by + bz * bz)
    pressure = (gamma - 1.0) * (energy - kinetic - magnetic)

    return {"rho": rho, "vx": vx, "By": by, "p": pressure}


def field_norms(
    candidate: np.ndarray,
    reference: np.ndarray,
    gamma: float,
    dx: float,
    dy: float | None = None,
) -> dict[str, float]:
    """Compute physical-domain L1, L2, and Linf same-grid differences.

    Arrays with one row are treated as one-dimensional.  For two-dimensional
    arrays, ``dy`` defaults to ``dx`` for the square grids used by the existing
    experiment drivers.
    """

    cand = _as_mhd_array(candidate, "candidate")
    ref = _as_mhd_array(reference, "reference")
    if cand.shape != ref.shape:
        raise ValueError("candidate and reference must have matching shapes")
    if not np.isfinite(dx) or dx <= 0.0:
        raise ValueError("dx must be finite and > 0.0")
    if dy is not None and (not np.isfinite(dy) or dy <= 0.0):
        raise ValueError("dy must be finite and > 0.0")

    cell_measure = dx if cand.shape[0] == 1 else dx * (dx if dy is None else dy)

    cand_fields = mhd_primitive_fields(cand, gamma)
    ref_fields = mhd_primitive_fields(ref, gamma)

    norms: dict[str, float] = {}
    for field in FIELD_NAMES:
        diff = cand_fields[field] - ref_fields[field]
        abs_diff = np.abs(diff)
        norms[f"L1_{field}"] = float(np.sum(abs_diff) * cell_measure)
        norms[f"L2_{field}"] = float(np.sqrt(np.sum(diff * diff) * cell_measure))
        norms[f"Linf_{field}"] = float(np.max(abs_diff))
    return norms


def mca_field_spread(samples: np.ndarray, gamma: float) -> dict[str, float]:
    """Aggregate MCA primitive-field spread and gated SNR scalars."""

    sample_stack = np.asarray(samples)
    if sample_stack.ndim != 4 or sample_stack.shape[-1] != 9:
        raise ValueError("samples must have shape (n, ny, nx, 9)")
    if sample_stack.shape[0] < 2:
        raise ValueError("samples must contain at least 2 samples")

    sample_fields = [mhd_primitive_fields(sample_stack[k], gamma) for k in range(sample_stack.shape[0])]

    out: dict[str, float] = {}
    for field in FIELD_NAMES:
        field_samples = np.stack([fields[field] for fields in sample_fields], axis=0)
        sigma = compute_sigma_fp_field(field_samples)
        sigma = np.where(np.ptp(field_samples, axis=0) == 0.0, 0.0, sigma)
        out[f"spread_{field}"] = float(np.max(np.abs(sigma)))

        if field in GATE_FIELDS:
            signal_mean = float(np.mean(np.abs(field_samples.mean(axis=0))))
            sigma_mean = float(np.mean(np.abs(sigma)))
            out[f"snr_{field}"] = signal_mean / (sigma_mean if sigma_mean != 0.0 else _SQRT_EPS)

    rho_means = np.array(
        [float(np.mean(fields["rho"])) for fields in sample_fields],
        dtype=np.float64,
    )
    out["rho_mean_spread"] = float(np.max(rho_means) - np.min(rho_means))
    return out
