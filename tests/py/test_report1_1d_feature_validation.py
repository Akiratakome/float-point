from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "regression"))

import report1_1d_feature_validation as fv  # noqa: E402


def test_sod_star_state_and_wave_features_are_reasonable() -> None:
    cfg = fv.TESTS["sod"]

    solution = fv.solve_riemann_features(cfg)

    assert solution.p_star == pytest.approx(0.30313, rel=1e-4)
    assert solution.u_star == pytest.approx(0.92745, rel=1e-4)
    assert solution.contact_position == pytest.approx(0.5 + solution.u_star * 0.25)
    assert solution.left.kind == "rarefaction"
    assert solution.right.kind == "shock"
    assert len(solution.shocks) == 1
    assert solution.shocks[0].side == "right"
    assert solution.shocks[0].speed == pytest.approx(1.75216, rel=1e-4)
    assert solution.shocks[0].position == pytest.approx(0.93804, rel=1e-4)


def test_discontinuity_band_marks_only_contact_and_shocks() -> None:
    x = np.array([0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95])
    dx = 0.1

    mask = fv.discontinuity_band_mask(
        x,
        feature_positions=[0.5, 0.8],
        band_cells=1,
        dx=dx,
    )

    assert mask.tolist() == [
        False,
        False,
        False,
        False,
        True,
        True,
        False,
        True,
        True,
        False,
    ]


def test_feature_locator_uses_local_gradient_window() -> None:
    x = np.linspace(0.05, 0.95, 10)
    rho = np.array([0.0, 50.0, 0.0, 0.0, 1.0, 4.0, 4.0, 4.0, 4.0, 4.0])

    located = fv.locate_feature_by_gradient(
        x,
        rho,
        exact_position=0.52,
        dx=0.1,
        domain_length=1.0,
        min_window_cells=1,
        window_fraction=0.1,
    )

    assert located.position == pytest.approx(0.5)
    assert located.abs_error == pytest.approx(0.02)
    assert located.window_radius == pytest.approx(0.1)
    assert located.gradient_index == 4


def test_feature_locator_can_bound_window_away_from_nearby_feature() -> None:
    x = np.linspace(0.405, 0.595, 20)
    rho = np.ones_like(x)
    rho[x >= 0.5] += 1.0
    rho[x >= 0.55] += 20.0

    located = fv.locate_feature_by_gradient(
        x,
        rho,
        exact_position=0.5,
        dx=0.01,
        domain_length=1.0,
        min_window_cells=2,
        window_fraction=0.05,
        blocker_positions=[0.55],
    )

    assert located.position == pytest.approx(0.5)
    assert located.window_radius < 0.05
    assert located.window_upper < 0.55
