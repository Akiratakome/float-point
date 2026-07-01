import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "metrics"))

from mhd_fields import (
    mca_field_spread,
    mhd_primitive_fields,
    field_norms,
    FIELD_NAMES,
    GATE_FIELDS,
)


def _cell(rho, vx, By, p, gamma):
    # Build one conserved cell with vy=vz=0, Bx=Bz=0 so p reduces cleanly.
    E = p / (gamma - 1.0) + 0.5 * rho * vx * vx + 0.5 * By * By
    return [rho, rho * vx, 0.0, 0.0, 0.0, By, 0.0, E, 0.0]


def test_primitive_fields_roundtrip():
    gamma = 5.0 / 3.0
    arr = np.array([[_cell(2.0, 0.5, 0.3, 1.5, gamma)]], dtype=np.float64)  # (1,1,9)
    prim = mhd_primitive_fields(arr, gamma)
    assert np.isclose(prim["rho"][0, 0], 2.0)
    assert np.isclose(prim["vx"][0, 0], 0.5)
    assert np.isclose(prim["By"][0, 0], 0.3)
    assert np.isclose(prim["p"][0, 0], 1.5)


def test_field_norms_zero_on_identical():
    gamma = 5.0 / 3.0
    arr = np.array([[_cell(1.0, 0.2, 0.1, 1.0, gamma)],
                    [_cell(1.3, 0.0, 0.2, 0.7, gamma)]], dtype=np.float64)  # (2,1,9)
    norms = field_norms(arr, arr, gamma, dx=0.5)
    for f in FIELD_NAMES:
        assert norms[f"L1_{f}"] == 0.0
        assert norms[f"L2_{f}"] == 0.0
        assert norms[f"Linf_{f}"] == 0.0
    assert set(GATE_FIELDS) == {"rho", "By", "p"}


def test_field_norms_scale_with_dx():
    gamma = 5.0 / 3.0
    a = np.array([[_cell(1.0, 0.0, 0.0, 1.0, gamma)]], dtype=np.float64)
    b = np.array([[_cell(1.5, 0.0, 0.0, 1.0, gamma)]], dtype=np.float64)
    norms = field_norms(a, b, gamma, dx=0.25)
    assert np.isclose(norms["L1_rho"], 0.5 * 0.25)
    assert np.isclose(norms["L2_rho"], 0.25)
    assert np.isclose(norms["Linf_rho"], 0.5)


@pytest.mark.parametrize("dx", [0.0, -1.0, float("nan")])
def test_field_norms_rejects_invalid_dx(dx):
    gamma = 5.0 / 3.0
    arr = np.array([[_cell(1.0, 0.0, 0.0, 1.0, gamma)]], dtype=np.float64)
    with pytest.raises(ValueError, match="dx"):
        field_norms(arr, arr, gamma, dx=dx)


def test_primitive_fields_rejects_flat_state():
    gamma = 5.0 / 3.0
    with pytest.raises(ValueError, match="shape"):
        mhd_primitive_fields(np.zeros(9), gamma)


def test_mca_field_spread_zero_when_identical():
    gamma = 5.0 / 3.0
    one = np.array([[_cell(1.0, 0.2, 0.1, 1.0, gamma)]], dtype=np.float64)  # (1,1,9)
    samples = np.stack([one, one, one], axis=0)  # (3,1,1,9)
    out = mca_field_spread(samples, gamma)
    assert out["spread_rho"] == 0.0
    assert out["spread_By"] == 0.0
    assert out["rho_mean_spread"] == 0.0
    assert "snr_p" in out


def test_mca_field_spread_detects_rho_variation():
    gamma = 5.0 / 3.0
    s0 = np.array([[_cell(1.0, 0.0, 0.1, 1.0, gamma)]], dtype=np.float64)
    s1 = np.array([[_cell(1.2, 0.0, 0.1, 1.0, gamma)]], dtype=np.float64)
    samples = np.stack([s0, s1], axis=0)
    out = mca_field_spread(samples, gamma)
    assert out["spread_rho"] > 0.0
    assert np.isclose(out["rho_mean_spread"], 0.2)


@pytest.mark.parametrize(
    "samples",
    [
        np.empty((0, 1, 1, 9), dtype=np.float64),
        np.zeros((1, 1, 1, 9), dtype=np.float64),
    ],
)
def test_mca_field_spread_rejects_too_few_samples(samples):
    gamma = 5.0 / 3.0
    with pytest.raises(ValueError, match="at least 2"):
        mca_field_spread(samples, gamma)


def test_mca_field_spread_uses_ddof_one_for_spread():
    gamma = 5.0 / 3.0
    s0 = np.array([[_cell(1.0, 0.0, 0.1, 1.0, gamma)]], dtype=np.float64)
    s1 = np.array([[_cell(1.2, 0.0, 0.1, 1.0, gamma)]], dtype=np.float64)
    samples = np.stack([s0, s1], axis=0)
    out = mca_field_spread(samples, gamma)
    assert np.isclose(out["spread_rho"], np.sqrt(0.02))
