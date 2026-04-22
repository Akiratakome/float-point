"""
Stage-1 unit tests for plot_divergence_marker.first_divergence_index.

Run with:  pytest tests/py/test_plot_divergence_marker.py -v
"""

import sys
import os

import numpy as np
import pytest

# Ensure the scripts directory is importable regardless of working directory
_SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
sys.path.insert(0, os.path.abspath(_SCRIPTS_DIR))

from plot_divergence_marker import first_divergence_index  # noqa: E402


# ---------------------------------------------------------------------------
# Test 1: identical arrays → None
# ---------------------------------------------------------------------------

def test_identical_arrays_returns_none():
    """Identical sine waves must return None (no divergence)."""
    x = np.linspace(0, 2 * np.pi, 300)
    a = np.sin(x)
    b = np.sin(x)
    result = first_divergence_index(a, b, mode="visible")
    assert result is None, f"Expected None for identical arrays, got {result}"


# ---------------------------------------------------------------------------
# Test 2: single large spike at index 42 → returns 42
# ---------------------------------------------------------------------------

def test_big_single_point_divergence_identified():
    """A spike at index 42 must be identified as the first divergence."""
    a = np.zeros(100)
    b = np.zeros(100)
    b[42] = 1.0  # large deviation; tol at that point = 1e-3 * 1.0 = 0.001; diff = 1.0
    result = first_divergence_index(a, b, mode="visible")
    assert result == 42, f"Expected 42, got {result}"


# ---------------------------------------------------------------------------
# Test 3: noise_floor mode raises NotImplementedError mentioning Stage 2 / A2-S2
# ---------------------------------------------------------------------------

def test_noise_floor_mode_not_implemented_in_stage1():
    """noise_floor mode must raise NotImplementedError with 'Stage 2' or 'A2-S2' in message."""
    a = np.ones(50)
    b = np.ones(50)
    with pytest.raises(NotImplementedError) as exc_info:
        first_divergence_index(a, b, mode="noise_floor")
    msg = str(exc_info.value)
    assert "Stage 2" in msg or "A2-S2" in msg, (
        f"NotImplementedError message should mention 'Stage 2' or 'A2-S2', got: {msg!r}"
    )
