"""Invariant tests for the LoSoS 3-field metric.

Three tests enforce the core mathematical guarantees:
  1. s_worst is the pointwise minimum of s_reliability and s_accuracy.
  2. Reliability and accuracy are genuinely independent: tight-but-wrong samples
     yield high reliability and low accuracy, and s_worst follows accuracy.
  3. All three fields are finite (no NaN, no -inf) for adversarial edge cases.

Run with: python3 -m pytest tests/py/test_losos_three_fields.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# Make scripts/ importable regardless of working directory.
sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))

from losos_metric import (  # noqa: E402
    compute_s_reliability,
    compute_s_accuracy,
    compute_s_worst,
    compute_losos_fields,
    _SQRT_EPS,
    _var_floor,
)


# ---------------------------------------------------------------------------
# Test 1 — s_worst is the pointwise minimum of reliability and accuracy
# ---------------------------------------------------------------------------

def test_s_worst_is_pointwise_minimum_of_reliability_and_accuracy() -> None:
    """s_worst(i) == min(s_reliability(i), s_accuracy(i)) everywhere."""
    rng = np.random.default_rng(seed=0)

    n_samples, n_cells = 30, 8
    # Use shape (n_samples, 1, n_cells) for a single variable "row".
    # We construct two regions:
    #   cells 0..3 : sigma small, |mu - ref| large  → s_rel >> s_acc
    #   cells 4..7 : sigma large, |mu - ref| small  → s_acc >> s_rel

    samples = np.ones((n_samples, 1, n_cells))

    # Region A (cells 0–3): tight cluster at 1.0, but reference is 2.0
    # sigma ~ 1e-15, |mu - ref| ~ 1.0 → s_rel high, s_acc low
    samples[:, :, :4] = 1.0 + 1e-15 * rng.standard_normal((n_samples, 1, 4))

    # Region B (cells 4–7): wide spread, but mean ≈ reference = 1.0
    # sigma ~ 0.3, |mu - ref| ~ 1e-15 → s_rel low, s_acc high
    noise_b = rng.standard_normal((n_samples, 1, 4)) * 0.3
    # Shift so mean ≈ 1.0 + tiny offset
    noise_b -= noise_b.mean(axis=0, keepdims=True)
    noise_b += 1e-15
    samples[:, :, 4:] = 1.0 + noise_b

    u_ref = np.ones((1, n_cells))
    u_ref[:, :4] = 2.0   # region A reference far from cluster
    u_ref[:, 4:] = 1.0   # region B reference matches mean

    floor = _var_floor(u_ref)

    s_rel = compute_s_reliability(samples, floor)
    s_acc = compute_s_accuracy(samples, u_ref, floor)
    s_worst = compute_s_worst(s_rel, s_acc)

    np.testing.assert_array_equal(
        s_worst,
        np.minimum(s_rel, s_acc),
        err_msg=(
            "s_worst must be the element-wise minimum of s_reliability and "
            "s_accuracy at every cell, not just on average."
        ),
    )


# ---------------------------------------------------------------------------
# Test 2 — reliability and accuracy diverge for tight-but-wrong samples
# ---------------------------------------------------------------------------

def test_reliability_and_accuracy_diverge_when_tight_but_wrong() -> None:
    """Tight cluster far from reference: s_rel >> s_acc, s_worst ≈ s_acc."""
    rng = np.random.default_rng(seed=1)

    n_samples, n_cells = 30, 8
    # 30 samples of value 1.0 ± 1e-15; reference = 0.5 (100 % relative error).
    samples = 1.0 + 1e-15 * rng.standard_normal((n_samples, 1, n_cells))
    u_ref = np.full((1, n_cells), 0.5)

    floor = _var_floor(u_ref)

    s_rel, s_acc, s_worst = compute_losos_fields(samples, u_ref, floor)
    assert s_acc is not None and s_worst is not None

    # s_reliability should be very high: sigma_fp ~ 1e-15, mu ~ 1.0
    # → ratio ~ 1e-15 → s_rel ~ 15.
    assert np.all(s_rel >= 14), (
        f"Expected s_reliability >= 14 everywhere (tight cluster), "
        f"got min={s_rel.min():.2f}"
    )

    # s_accuracy should be low: |mu - ref| ~ 0.5, |ref| = 0.5 → ratio = 1.0
    # → s_acc = -log10(1.0) = 0.
    assert np.all(s_acc <= 1), (
        f"Expected s_accuracy <= 1 everywhere (wrong by 100%), "
        f"got max={s_acc.max():.2f}"
    )

    # s_worst should equal s_accuracy everywhere (accuracy is the bottleneck).
    np.testing.assert_array_equal(
        s_worst,
        np.minimum(s_rel, s_acc),
        err_msg="s_worst must equal min(s_rel, s_acc).",
    )
    # Since s_acc << s_rel, s_worst should track s_acc closely.
    np.testing.assert_allclose(
        s_worst, s_acc, rtol=1e-12,
        err_msg=(
            "s_worst should be essentially equal to s_accuracy here, "
            "because accuracy is the binding constraint."
        ),
    )


# ---------------------------------------------------------------------------
# Test 3 — all fields finite for adversarial edge cases
# ---------------------------------------------------------------------------

def test_all_fields_finite() -> None:
    """No NaN and no -inf in any field, even for adversarial inputs.

    Edge cases exercised:
    - u_ref == 0 for all cells (v-component in symmetric flow)
    - sigma_fp == 0 exactly (all samples identical — constant field)
    - mu_sample == u_ref exactly (truncation error is zero → ratio = 0 → log10(0))

    +inf is acceptable for s_reliability where sigma_fp == 0, and for
    s_accuracy where mu == u_ref exactly.  The tests assert isfinite is False
    only for -inf or NaN, i.e. they allow +inf.
    """
    rng = np.random.default_rng(seed=2)

    n_samples = 30
    ny, nx = 4, 8

    # Build samples: shape (n_samples, ny, nx, 4) primitive variables.
    # var 0 (rho): normal data
    # var 1 (u)  : all samples identical → sigma_fp == 0
    # var 2 (v)  : u_ref == 0 (symmetric flow)
    # var 3 (p)  : mu exactly equals u_ref → accuracy ratio == 0

    samples_4d = rng.standard_normal((n_samples, ny, nx, 4)) * 0.1 + 1.0

    # var 1: make all samples equal to the mean so sigma_fp == 0
    mean_v1 = samples_4d[:, :, :, 1].mean(axis=0, keepdims=True)
    samples_4d[:, :, :, 1] = mean_v1

    # var 2: u_ref = 0 everywhere
    u_ref_4d = np.ones((ny, nx, 4))
    u_ref_4d[:, :, 2] = 0.0

    # var 3: set mu exactly equal to u_ref → abs_err == 0
    u_ref_4d[:, :, 3] = samples_4d[:, :, :, 3].mean(axis=0)

    for vi in range(4):
        samples_var = samples_4d[:, :, :, vi]          # (n_samples, ny, nx)
        u_ref_var   = u_ref_4d[:, :, vi]               # (ny, nx)
        floor = _var_floor(u_ref_var)

        s_rel, s_acc, s_wst = compute_losos_fields(samples_var, u_ref_var, floor)
        assert s_acc is not None and s_wst is not None

        # No NaN and no -inf; +inf is allowed.
        assert not np.any(np.isnan(s_rel)), \
            f"var[{vi}] s_reliability contains NaN"
        assert not np.any(s_rel == -np.inf), \
            f"var[{vi}] s_reliability contains -inf"

        assert not np.any(np.isnan(s_acc)), \
            f"var[{vi}] s_accuracy contains NaN"
        assert not np.any(s_acc == -np.inf), \
            f"var[{vi}] s_accuracy contains -inf"

        assert not np.any(np.isnan(s_wst)), \
            f"var[{vi}] s_worst contains NaN"
        assert not np.any(s_wst == -np.inf), \
            f"var[{vi}] s_worst contains -inf"
