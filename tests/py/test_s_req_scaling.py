"""Invariants for s_req_metric: scaling, ceiling clamp, floor, block-avg, IO.

Six tests:
  1. Convergence: E_trunc ∝ 1/N implies s_req(2N) − s_req(N) ≈ log10(2).
  2. Perfect match: E_trunc == 0 clamps s_req to SIG_DIGITS_CEILING.
  3. Vacuum floor: U_ref ≈ 0 with tiny noise gives finite s_req.
  4. Block-average: 4×4 averaging conserves the integral exactly.
  5. Indivisible grid: factor != 4 raises ValueError.
  6. dtype: float32 candidate vs float64 reference yields finite output.

Run with: python3 -m pytest tests/py/test_s_req_scaling.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

# Make scripts/ importable regardless of working directory.
sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))

from s_req_metric import (  # noqa: E402
    block_average_4x_to_coarse,
    compute_e_trunc,
    compute_s_req,
)
from losos_metric import SIG_DIGITS_CEILING  # noqa: E402


# Test 1 — Δx convergence rate
def test_s_req_convergence_rate_doubles_with_grid_refinement() -> None:
    """If E_trunc ∝ 1/N, then s_req(2N) − s_req(N) == log10(2) ≈ 0.301."""
    rng = np.random.default_rng(seed=0)

    # Build a synthetic primitive field at N=100, with known truncation
    # E_trunc = C / N (linear convergence). C chosen so E_trunc(100) ~ 1e-3.
    def synth(N: int, var_amplitude: float = 1.0, C: float = 0.1) -> tuple[np.ndarray, np.ndarray]:
        u_ref = var_amplitude + 0.5 * np.sin(np.linspace(0, np.pi, N * N)).reshape(N, N, 1)
        u_ref = np.repeat(u_ref, 4, axis=2)  # 4 primitive vars
        # Add a deterministic O(1/N) bias to mu_sample relative to u_ref
        bias = (C / N) * np.ones_like(u_ref) * var_amplitude
        mu_sample = u_ref + bias
        return mu_sample.astype(np.float64), u_ref.astype(np.float64)

    eps = float(np.finfo(np.float64).eps)
    s_req_by_N: dict[int, float] = {}
    for N in (100, 200, 400):
        mu, ref = synth(N)
        e = compute_e_trunc(mu, ref, eps_real=eps)
        s = compute_s_req(e["rho"])
        s_req_by_N[N] = s

    delta_100_200 = s_req_by_N[200] - s_req_by_N[100]
    delta_200_400 = s_req_by_N[400] - s_req_by_N[200]
    assert abs(delta_100_200 - np.log10(2.0)) < 1e-3, \
        f"Expected s_req(200) − s_req(100) ≈ {np.log10(2.0):.4f}, got {delta_100_200:.4f}"
    assert abs(delta_200_400 - np.log10(2.0)) < 1e-3, \
        f"Expected s_req(400) − s_req(200) ≈ {np.log10(2.0):.4f}, got {delta_200_400:.4f}"


# Test 2 — Perfect match → ceiling clamp
def test_s_req_perfect_match_clamps_to_ceiling() -> None:
    """E_trunc == 0 → -log10 = +inf → must be clamped to SIG_DIGITS_CEILING."""
    eps = float(np.finfo(np.float64).eps)
    u_ref = np.full((4, 4, 4), 1.5)
    mu = u_ref.copy()  # exact match
    e = compute_e_trunc(mu, u_ref, eps_real=eps)
    s = compute_s_req(e["rho"])
    assert s == SIG_DIGITS_CEILING, \
        f"Expected s_req == SIG_DIGITS_CEILING ({SIG_DIGITS_CEILING}) for perfect match, got {s}"


# Test 3 — Vacuum floor doesn't blow up
def test_s_req_vacuum_floor_stays_finite() -> None:
    """U_ref ≈ 0 with √eps-magnitude noise → s_req must be finite (not nan/inf)."""
    eps = float(np.finfo(np.float64).eps)
    sqrt_eps = float(np.sqrt(eps))
    u_ref = np.zeros((4, 4, 4))
    mu = sqrt_eps * np.ones_like(u_ref)
    e = compute_e_trunc(mu, u_ref, eps_real=eps)
    s = compute_s_req(e["rho"])
    assert np.isfinite(s), f"Expected finite s_req for vacuum, got {s}"
    assert 0 <= s <= SIG_DIGITS_CEILING, \
        f"Expected s_req in [0, {SIG_DIGITS_CEILING}], got {s}"


# Test 4 — Block-average conserves the integral
def test_block_average_4x_conserves_integral() -> None:
    """coarse.sum() * 16 == fine.sum() exactly in float64."""
    rng = np.random.default_rng(seed=4)
    fine = rng.standard_normal((800, 800, 4))  # arbitrary
    coarse = block_average_4x_to_coarse(fine)
    assert coarse.shape == (200, 200, 4)
    # Each coarse cell is the mean of 16 fine cells, so coarse.sum() == fine.sum() / 16.
    np.testing.assert_allclose(coarse.sum() * 16, fine.sum(), rtol=0, atol=1e-9 * abs(fine.sum()))


# Test 5 — Indivisible grid raises
def test_block_average_indivisible_grid_raises() -> None:
    """ny_f or nx_f not divisible by 4 → ValueError."""
    fine = np.zeros((7, 8, 4))
    with pytest.raises(ValueError, match="factor-4"):
        block_average_4x_to_coarse(fine)


# Test 6 — dtype tolerance
def test_compute_e_trunc_handles_mixed_dtypes() -> None:
    """float32 candidate, float64 reference → no exception, finite result."""
    eps = float(np.finfo(np.float64).eps)
    u_ref = np.ones((10, 10, 4), dtype=np.float64) * 2.0
    mu = (u_ref + 1e-3).astype(np.float32)
    e = compute_e_trunc(mu, u_ref, eps_real=eps)
    s = compute_s_req(e["rho"])
    assert np.isfinite(s)
