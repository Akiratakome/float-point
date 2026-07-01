"""Primitive MHD field extraction and same-grid field norms."""

from __future__ import annotations

import numpy as np


FIELD_NAMES = ("rho", "vx", "By", "p")
GATE_FIELDS = ("rho", "By", "p")


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
    candidate: np.ndarray, reference: np.ndarray, gamma: float, dx: float
) -> dict[str, float]:
    """Compute L1, L2, and Linf primitive-field differences on the same grid."""

    cand = _as_mhd_array(candidate, "candidate")
    ref = _as_mhd_array(reference, "reference")
    if cand.shape != ref.shape:
        raise ValueError("candidate and reference must have matching shapes")
    if not np.isfinite(dx) or dx <= 0.0:
        raise ValueError("dx must be finite and > 0.0")

    cand_fields = mhd_primitive_fields(cand, gamma)
    ref_fields = mhd_primitive_fields(ref, gamma)

    norms: dict[str, float] = {}
    for field in FIELD_NAMES:
        diff = cand_fields[field] - ref_fields[field]
        abs_diff = np.abs(diff)
        norms[f"L1_{field}"] = float(np.sum(abs_diff) * dx)
        norms[f"L2_{field}"] = float(np.sqrt(np.sum(diff * diff) * dx))
        norms[f"Linf_{field}"] = float(np.max(abs_diff))
    return norms
