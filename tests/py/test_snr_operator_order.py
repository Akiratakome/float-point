"""Regression guard: SNR operator order must be per-cell-std-first, then spatial L1.

The WRONG order (spatial L1 first, then std across samples) silently zeros out
spatially anti-correlated FP perturbations, making the solver appear more robust
than it actually is.  These tests catch any future refactor that swaps the order.

Run with: pytest tests/py/test_snr_operator_order.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

# Make scripts/ importable regardless of working directory.
sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))

from snr_metric import compute_sigma_fp_field, compute_snr_fields  # noqa: E402


# ---------------------------------------------------------------------------
# Shared synthetic data for operator-order tests
# ---------------------------------------------------------------------------

def _make_checkerboard_samples(
    nx: int = 8,
    ny: int = 4,
    nsamples: int = 30,
    seed: int = 42,
) -> np.ndarray:
    """Build samples with strong spatial anti-correlation.

    Neighbouring cells get OPPOSITE signs of the same per-sample amplitude.
    The large constant background (100.0) keeps all samples positive, so the
    spatial L1 norm is exactly constant across samples (each sample sums to
    ny*nx*100, independent of amp) — making sigma_wrong ~ 0.  At the same time,
    per-cell std equals the std of the amplitudes, so sigma_right is large.

    Returns samples of shape (nsamples, ny, nx).
    """
    rng = np.random.default_rng(seed=seed)
    # Large background ensures samples never go negative, so L1 = sum (not abs).
    u_base = np.full((ny, nx), 100.0)
    checkerboard = np.indices((ny, nx)).sum(axis=0) % 2  # 0/1 per cell
    sign = np.where(checkerboard == 0, +1.0, -1.0)       # +-1 per cell
    amp = rng.standard_normal(size=nsamples) * 1.0        # per-sample amplitude
    samples = u_base[None, :, :] + amp[:, None, None] * sign[None, :, :]
    return samples


# ---------------------------------------------------------------------------
# Test 1: wrong order severely underestimates noise on anti-correlated data
# ---------------------------------------------------------------------------

def test_wrong_order_underestimates_noise() -> None:
    """sigma_right / sigma_wrong >= 100 on checkerboard-anti-correlated samples."""
    samples = _make_checkerboard_samples()

    # WRONG order: spatial L1 of each sample first, then std across samples.
    per_sample_l1 = np.sum(np.abs(samples), axis=(1, 2))  # (nsamples,)
    sigma_wrong = float(np.std(per_sample_l1, ddof=1))

    # CORRECT order: per-cell std first, then spatial L1.
    sigma_fp_field = compute_sigma_fp_field(samples)      # (ny, nx)
    sigma_right = float(np.sum(np.abs(sigma_fp_field)))

    ratio = sigma_right / max(sigma_wrong, 1e-300)
    assert ratio >= 100.0, (
        f"Operator order invariant violated: sigma_right={sigma_right:.6g}, "
        f"sigma_wrong={sigma_wrong:.6g}, ratio={ratio:.3f} (expected >= 100).\n"
        "This means the implementation is using the WRONG spatial-L1-first order."
    )


# ---------------------------------------------------------------------------
# Test 2: public API matches reference per-cell-std computation byte-for-byte
# ---------------------------------------------------------------------------

def test_right_order_equals_public_api() -> None:
    """compute_sigma_fp_field matches np.std(axis=0, ddof=1) exactly."""
    samples = _make_checkerboard_samples()

    expected = samples.std(axis=0, ddof=1)
    actual = compute_sigma_fp_field(samples)

    np.testing.assert_array_equal(
        actual, expected,
        err_msg=(
            "compute_sigma_fp_field does not match np.std(axis=0, ddof=1). "
            "The implementation is using a different formula or axis."
        ),
    )


# ---------------------------------------------------------------------------
# Test 3: SNR_local matches definition for uniform mu_trunc and sigma_fp
# ---------------------------------------------------------------------------

def test_snr_local_matches_definition() -> None:
    """SNR_local ~ 100 when mu_trunc=0.01 uniform and sigma_fp=1e-4 uniform."""
    ny, nx, nsamples = 6, 6, 30

    # Reference: flat field of value 1.0.
    u_ref = np.ones((ny, nx))

    # Construct samples such that:
    #   mean(samples) - u_ref = 0.01   (truncation bias)
    #   std(samples, ddof=1)  = 1e-4   (FP noise)
    rng = np.random.default_rng(seed=7)
    noise = rng.standard_normal(size=(nsamples, ny, nx))
    # Normalise noise to exactly std=1, then scale.
    noise = noise - noise.mean(axis=0, keepdims=True)
    noise_std = noise.std(axis=0, ddof=1, keepdims=True)
    noise_std = np.where(noise_std == 0, 1.0, noise_std)
    noise = noise / noise_std * 1e-4   # sigma_fp = 1e-4

    samples = u_ref[None, :, :] + 0.01 + noise
    # After this: mean(samples) ~ u_ref + 0.01, std(samples, ddof=1) ~ 1e-4

    _, _, snr_local = compute_snr_fields(samples, u_ref)

    # Expected SNR = 0.01 / 1e-4 = 100 (floor << 1e-4 for u_ref~1)
    expected_snr = 0.01 / 1e-4  # 100.0
    # Allow 5 % relative tolerance to account for finite-sample std estimation.
    np.testing.assert_allclose(
        snr_local, expected_snr, rtol=0.05,
        err_msg=(
            f"SNR_local should be ~{expected_snr:.1f} (mu=0.01, sigma=1e-4). "
            "Definition mismatch or wrong axis."
        ),
    )
