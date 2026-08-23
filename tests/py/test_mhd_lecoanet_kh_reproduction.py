import importlib.util
import math
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "regression" / "mhd_lecoanet_kh_reproduction.py"


def _load():
    spec = importlib.util.spec_from_file_location("mhd_lecoanet_kh_reproduction", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_analytic_initial_mode_is_positive_and_shape_checked() -> None:
    mod = _load()
    nx, ny = 64, 128
    x = (np.arange(nx) + 0.5) / nx
    y = (np.arange(ny) + 0.5) * (2.0 / ny)
    vy = mod.analytic_initial_vy(x, y)

    assert vy.shape == (ny, nx)
    assert mod.lecoanet_mode_amplitude(vy, x, y) > 0.0
    with pytest.raises(ValueError, match="does not match"):
        mod.lecoanet_mode_amplitude(vy[:, :-1], x, y)


def test_growth_fit_recovers_exponential_rate() -> None:
    mod = _load()
    expected = 3.227
    rows = [
        {"time": time, "mode_amplitude": 0.01 * math.exp(expected * time)}
        for time in (0.0, 0.25, 0.5, 0.75, 1.0)
    ]

    rate, r2 = mod.fit_growth_rate(rows)

    assert rate == pytest.approx(expected, rel=1e-12)
    assert r2 == pytest.approx(1.0)
