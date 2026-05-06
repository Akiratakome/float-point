"""
Unit tests for plot_divergence_marker (Stage 1 + Stage 2).

Covers all three modes: visible, noise_floor, strict_fp.

Run with:  pytest tests/py/test_plot_divergence_marker.py -v
"""

import os
import sys
import warnings

import numpy as np
import pytest

# Ensure the scripts directory is importable regardless of working directory
_SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
sys.path.insert(0, os.path.abspath(_SCRIPTS_DIR))

from plot_divergence_marker import (  # noqa: E402
    all_divergence_indices,
    filtered_divergence_segment_rejoins,
    divergence_segment_onsets,
    first_divergence_index,
)


# ---------------------------------------------------------------------------
# Test 1: identical arrays → None, parametrized over all three modes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", ["visible", "noise_floor", "strict_fp"])
def test_identical_arrays_returns_none(mode):
    """Identical sine waves must return None in every mode."""
    x = np.linspace(0, 2 * np.pi, 300)
    a = np.sin(x)
    b = np.sin(x)

    kwargs = {}
    if mode == "noise_floor":
        # Realistic non-zero noise floor so the detector has something to work with.
        kwargs["noise_floor_a"] = np.full_like(a, 1e-8)
        kwargs["noise_floor_b"] = np.full_like(b, 1e-8)

    with warnings.catch_warnings():
        # strict_fp emits an expected "degraded fallback" warning
        warnings.simplefilter("ignore")
        result = first_divergence_index(a, b, mode=mode, **kwargs)

    assert result is None, f"[mode={mode}] expected None for identical arrays, got {result}"


# ---------------------------------------------------------------------------
# Test 2: single large spike at index 42 → returns 42 (visible mode)
# ---------------------------------------------------------------------------

def test_big_single_point_divergence_identified():
    """A spike at index 42 must be identified as the first divergence (visible mode)."""
    a = np.zeros(100)
    b = np.zeros(100)
    b[42] = 1.0  # large deviation; tol at that point = 1e-3 * 1.0 = 0.001; diff = 1.0
    result = first_divergence_index(a, b, mode="visible")
    assert result == 42, f"Expected 42, got {result}"


# ---------------------------------------------------------------------------
# Test 3: noise_floor mode, diff < 3·noise_floor → None (absorbed)
# ---------------------------------------------------------------------------

def test_noise_floor_absorbs_diff_below_3sigma():
    """Difference of 1·σ must be absorbed by the 3-σ noise-floor envelope."""
    n = 200
    a = np.ones(n)
    # Flat field, no gradient contribution. Noise floor = 1e-6 everywhere.
    # Per-cell 3σ envelope = 3e-6; plus abs_floor = 3·max(nf) = 3e-6.
    # So tol ≈ 6e-6 everywhere. A diff of 1e-6 must NOT trigger.
    nf = np.full(n, 1.0e-6)
    b = a + 1.0e-6
    result = first_divergence_index(
        a, b, mode="noise_floor",
        noise_floor_a=nf, noise_floor_b=nf,
    )
    assert result is None, f"Expected None (absorbed), got {result}"


# ---------------------------------------------------------------------------
# Test 4: noise_floor mode, diff > 3·noise_floor + abs_floor → identified
# ---------------------------------------------------------------------------

def test_noise_floor_flags_diff_above_3sigma():
    """Difference well above the 3-σ envelope must be flagged at the injection cell."""
    n = 200
    a = np.ones(n)
    nf = np.full(n, 1.0e-6)       # tol component from noise ≈ 3e-6
    b = a.copy()
    # Inject 1e-3 spike well above 3σ noise + abs_floor (both O(3e-6)).
    spike_idx = 77
    b[spike_idx] += 1.0e-3
    result = first_divergence_index(
        a, b, mode="noise_floor",
        noise_floor_a=nf, noise_floor_b=nf,
    )
    assert result == spike_idx, f"Expected {spike_idx}, got {result}"


# ---------------------------------------------------------------------------
# Test 5: shock 1-cell offset, no amplitude diff → not identified (absorbed by k_grad·|∇|)
# ---------------------------------------------------------------------------

def test_shock_one_cell_offset_absorbed_by_gradient_term():
    """Linear ramp shifted by one cell: diff == |∇|, so k_grad=1.0 absorbs it."""
    n = 100
    # Linear ramp: np.gradient = 1 everywhere (interior).
    a = np.arange(n, dtype=float)
    # One-cell left shift: diff = 1 everywhere in the interior, matching |∇a| = 1.
    b = a + 1.0
    nf = np.zeros(n)              # zero noise floor → isolate the gradient term
    result = first_divergence_index(
        a, b, mode="noise_floor",
        noise_floor_a=nf, noise_floor_b=nf,
        abs_floor_frac=0.0,       # disable global abs floor for a clean comparison
    )
    # tol = 0 + 1.0 * 0.5*(1 + 1) + 0 = 1.0; diff = 1.0 → not `>` tol → None.
    assert result is None, f"Gradient term should absorb pure 1-cell offset; got {result}"


# ---------------------------------------------------------------------------
# Test 6: shock 1-cell offset + amplitude diff → identified
# ---------------------------------------------------------------------------

def test_shock_offset_plus_amplitude_diff_identified():
    """Same 1-cell ramp offset plus constant amplitude bump: amplitude part is flagged."""
    n = 100
    a = np.arange(n, dtype=float)
    b = a + 1.0                   # the shift part, absorbable by k_grad=1.0
    amp_bump = 5.0                # well above the k_grad·|∇| ≈ 1.0 budget
    b += amp_bump
    nf = np.zeros(n)
    result = first_divergence_index(
        a, b, mode="noise_floor",
        noise_floor_a=nf, noise_floor_b=nf,
        abs_floor_frac=0.0,
    )
    # Every interior cell has diff = 1 + amp_bump = 6, tol = 1.0, so first flagged
    # index is 0 (the left boundary — at i=0 np.gradient is a forward diff of 1 too,
    # so tol stays at 1.0 there as well).
    assert result == 0, f"Expected first flagged index 0, got {result}"


# ---------------------------------------------------------------------------
# Test 7: noise_floor mode missing noise_floor arrays → ValueError
# ---------------------------------------------------------------------------

def test_noise_floor_mode_requires_noise_floor_arrays():
    """mode='noise_floor' without noise_floor_a/b must raise ValueError (not NotImplementedError)."""
    a = np.ones(50)
    b = np.ones(50)
    with pytest.raises(ValueError) as exc_info:
        first_divergence_index(a, b, mode="noise_floor")
    assert "noise_floor" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test 8: strict_fp mode — float32 absorbs ~7th-digit diff, float64 flags it.
# ---------------------------------------------------------------------------

def test_strict_fp_precision_sensitivity():
    """Source precision controls what strict_fp absorbs.

    NOTE: The plan text says "float32 ... identified; float64 ... not identified",
    but strict_fp tolerance = k_eps·eps·max(|a|,|b|) grows with eps, so a LARGER
    eps (float32) means a LARGER tolerance and therefore FEWER detections. The
    physically-consistent reading is: float64 (tiny eps) flags a 7th-digit diff
    that float32 (eps ~1.2e-7) absorbs. Implemented accordingly; the plan
    bullet is inverted.
    """
    n = 50
    a = np.ones(n)
    # ~7th significant digit diff at a single interior cell (index 25). Small
    # enough that |∇| at i=25 is ~0.5·1e-6, so the k_grad term alone is O(5e-7).
    diff_mag = 1.0e-6
    b = a.copy()
    b[25] += diff_mag

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # strict_fp "degraded fallback" warning is expected
        idx_f32 = first_divergence_index(a, b, mode="strict_fp", source_precision="float32")
        idx_f64 = first_divergence_index(a, b, mode="strict_fp", source_precision="float64")

    # float32 tol at i=25: 10·1.19e-7·1 + 1·0.5·1e-6 ≈ 1.69e-6 > diff 1e-6 → absorbed.
    assert idx_f32 is None, f"float32 strict_fp should absorb 7th-digit diff, got {idx_f32}"
    # float64 tol at i=25: 10·2.22e-16·1 + 1·0.5·1e-6 ≈ 5e-7 < diff 1e-6 → flagged at 25.
    assert idx_f64 == 25, f"float64 strict_fp should flag 7th-digit diff at 25, got {idx_f64}"


# ---------------------------------------------------------------------------
# Bonus tests retained from Stage 1 (keep `all_divergence_indices` /
# `divergence_segment_onsets` regression coverage — lets the figure pipeline
# survive future refactors).
# ---------------------------------------------------------------------------

def test_all_divergence_indices_returns_every_cell():
    """Two isolated spikes and a 3-cell run must all appear in the output."""
    a = np.zeros(100)
    b = np.zeros(100)
    b[10] = 1.0
    b[50:53] = 1.0
    b[80] = 1.0
    idx = all_divergence_indices(a, b, mode="visible")
    assert idx.tolist() == [10, 50, 51, 52, 80]


def test_divergence_segment_onsets_collapses_contiguous_runs():
    """Onsets: isolated spike at 10, contiguous run starting 50, isolated at 80 -> [10,50,80]."""
    a = np.zeros(100)
    b = np.zeros(100)
    b[10] = 1.0
    b[50:53] = 1.0
    b[80] = 1.0
    onsets = divergence_segment_onsets(a, b, mode="visible")
    assert onsets == [10, 50, 80]


def test_filtered_divergence_segment_rejoins_marks_split_to_merge_points():
    """Rejoin points should be first non-divergent cells after kept segments."""
    a = np.zeros(100)
    b = np.zeros(100)
    b[10] = 1.0
    b[50:53] = 1.0
    b[80] = 1.0
    rejoins = filtered_divergence_segment_rejoins(
        a, b, mode="visible", visible_rel_tol=1e-6,
        merge_gap=0, min_segment_len=1, min_onset_distance=0,
    )
    assert rejoins == [11, 53, 81]


# ---------------------------------------------------------------------------
# Regression: strict_fp stacklevel=3 must point to the user's call site from
# ALL three public entry points. Before the fix, divergence_segment_onsets
# chained through all_divergence_indices and the warning pointed one frame
# too deep. We use warnings.catch_warnings(record=True) and assert the
# recorded frame is this test file.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "entry_point",
    [first_divergence_index, all_divergence_indices, divergence_segment_onsets],
)
def test_strict_fp_warning_stacklevel_points_to_caller(entry_point):
    """The strict_fp degraded-fallback warning must blame the user's line."""
    a = np.ones(20)
    b = np.ones(20)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        entry_point(a, b, mode="strict_fp")  # <- this is the user call site
    assert len(captured) >= 1, "expected a strict_fp fallback warning"
    # stacklevel=3 in _tolerance should attribute the warning to THIS test file.
    assert captured[0].filename.endswith("test_plot_divergence_marker.py"), (
        f"[{entry_point.__name__}] warning attributed to {captured[0].filename}, "
        "expected this test file"
    )
