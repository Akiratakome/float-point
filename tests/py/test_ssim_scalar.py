from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from phase_error_metrics import compute_phase_metrics_from_primitive


def _primitive_from_rho(rho: np.ndarray) -> np.ndarray:
    prim = np.zeros(rho.shape + (4,), dtype=np.float64)
    prim[..., 0] = rho
    prim[..., 1] = 0.1 * np.sin(rho)
    prim[..., 2] = 0.1 * np.cos(rho)
    prim[..., 3] = 1.0 + 0.05 * rho
    return prim


def _synthetic_rho(nx: int = 64, ny: int = 64) -> np.ndarray:
    x = np.linspace(0.0, 2.0 * np.pi, nx, endpoint=False)
    y = np.linspace(0.0, 2.0 * np.pi, ny, endpoint=False)
    xx, yy = np.meshgrid(x, y)
    return np.sin(4.0 * xx) + 0.6 * np.cos(3.0 * yy)


def test_ssim_identical_fields_near_one() -> None:
    pytest.importorskip("skimage.metrics")
    rho = _synthetic_rho()
    prim = _primitive_from_rho(rho)
    metrics = compute_phase_metrics_from_primitive(prim, prim.copy(), 1.0, 1.0, 0.5, False)
    assert float(metrics["ssim_rho"]) > 0.999


def test_ssim_phase_shifted_field_is_lower() -> None:
    pytest.importorskip("skimage.metrics")
    rho = _synthetic_rho()
    ref = _primitive_from_rho(rho)
    shifted = _primitive_from_rho(np.roll(rho, 8, axis=1))
    metrics_identical = compute_phase_metrics_from_primitive(ref, ref.copy(), 1.0, 1.0, 0.5, False)
    metrics_shifted = compute_phase_metrics_from_primitive(shifted, ref, 1.0, 1.0, 0.5, False)
    assert float(metrics_shifted["ssim_rho"]) < float(metrics_identical["ssim_rho"])
    assert float(metrics_shifted["ssim_rho"]) < 0.99
