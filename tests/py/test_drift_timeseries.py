from __future__ import annotations

import math
import struct
from pathlib import Path

import numpy as np
import pytest


def _write_binary(
    path: Path,
    cons: np.ndarray,
    *,
    t: float = 0.0,
    dx: float | None = None,
    dy: float | None = None,
) -> None:
    cons = np.asarray(cons)
    ny, nx, nvars = cons.shape
    if cons.dtype == np.float32:
        precision_tag = 4
        payload = cons.astype("<f4", copy=False).tobytes()
    else:
        precision_tag = 8
        payload = cons.astype("<f8", copy=False).tobytes()

    header = bytearray(64)
    header[:4] = b"HRSC"
    struct.pack_into("<iiii", header, 4, nx, ny, nvars, precision_tag)
    struct.pack_into(
        "<ddd",
        header,
        20,
        t,
        1.0 / nx if dx is None else dx,
        1.0 / max(ny, 1) if dy is None else dy,
    )
    path.write_bytes(bytes(header) + payload)


def test_fit_exponential_growth_recovers_known_lambda() -> None:
    from scripts.metrics.drift_timeseries import fit_exponential_growth

    times = np.array([0.0, 1.0, 2.0, 3.0])
    errors = 2.0 * np.exp(0.3 * times)

    fit = fit_exponential_growth(times, errors)

    assert fit["lambda"] == pytest.approx(0.3, abs=1e-12)
    assert fit["n_fit"] == 4


def test_fit_skips_zero_and_nonfinite_errors() -> None:
    from scripts.metrics.drift_timeseries import fit_exponential_growth

    fit = fit_exponential_growth(
        [0.0, 1.0, 2.0, 3.0, 4.0],
        [
            0.0,
            float("nan"),
            2.0 * math.exp(0.3 * 2.0),
            float("inf"),
            2.0 * math.exp(0.3 * 4.0),
        ],
    )

    assert fit["lambda"] == pytest.approx(0.3, abs=1e-12)
    assert fit["n_fit"] == 2
    assert fit["skipped"] == 3


def test_density_only_mode_ignores_degenerate_velocity(tmp_path: Path) -> None:
    from scripts.metrics.drift_timeseries import compute_l1_linf_pair

    a = np.array(
        [[[1.0, 0.0, 0.0, 2.5], [0.0, 1.0, 0.0, 2.5]]],
        dtype=np.float64,
    )
    b = a.copy()
    b[0, 0, 0] += 0.25
    b[0, 1, 0] += 0.50
    path_a = tmp_path / "a.bin"
    path_b = tmp_path / "b.bin"
    _write_binary(path_a, a, t=0.1)
    _write_binary(path_b, b, t=0.1)

    metric = compute_l1_linf_pair(path_a, path_b, variable="rho")

    assert metric["time"] == pytest.approx(0.1)
    assert metric["variable"] == "rho"
    assert metric["l1"] == pytest.approx(0.375)
    assert metric["linf"] == pytest.approx(0.5)


def test_compute_l1_linf_pair_supports_variable_index(tmp_path: Path) -> None:
    from scripts.metrics.drift_timeseries import compute_l1_linf_pair

    a = np.array(
        [[[1.0, 0.1, 0.0, 2.5], [2.0, 0.2, 0.0, 5.0]]],
        dtype=np.float64,
    )
    b = a.copy()
    b[..., 0] += [0.2, -0.4]
    path_a = tmp_path / "a.bin"
    path_b = tmp_path / "b.bin"
    _write_binary(path_a, a, t=0.2)
    _write_binary(path_b, b, t=0.2)

    metric = compute_l1_linf_pair(path_a, path_b, variable=0)

    assert metric["l1"] == pytest.approx(0.3)
    assert metric["linf"] == pytest.approx(0.4)


def test_compute_l1_linf_pair_rejects_mismatched_header_times(tmp_path: Path) -> None:
    from scripts.metrics.drift_timeseries import compute_l1_linf_pair

    cons = np.ones((1, 2, 4), dtype=np.float64)
    path_a = tmp_path / "a.bin"
    path_b = tmp_path / "b.bin"
    _write_binary(path_a, cons, t=0.1)
    _write_binary(path_b, cons, t=0.1001)

    with pytest.raises(ValueError, match="time mismatch") as excinfo:
        compute_l1_linf_pair(path_a, path_b)

    message = str(excinfo.value)
    assert str(path_a) in message
    assert str(path_b) in message
    assert "0.1" in message
    assert "0.1001" in message


def test_compute_l1_linf_pair_rejects_mismatched_dx_or_dy(tmp_path: Path) -> None:
    from scripts.metrics.drift_timeseries import compute_l1_linf_pair

    cons = np.ones((2, 2, 4), dtype=np.float64)
    path_a = tmp_path / "a.bin"
    path_b = tmp_path / "b.bin"
    _write_binary(path_a, cons, t=0.1, dx=0.5, dy=0.25)
    _write_binary(path_b, cons, t=0.1, dx=0.5001, dy=0.25)

    with pytest.raises(ValueError, match="dx mismatch"):
        compute_l1_linf_pair(path_a, path_b)

    _write_binary(path_b, cons, t=0.1, dx=0.5, dy=0.2501)

    with pytest.raises(ValueError, match="dy mismatch"):
        compute_l1_linf_pair(path_a, path_b)


def test_compute_l1_linf_pair_uses_average_compatible_time(tmp_path: Path) -> None:
    from scripts.metrics.drift_timeseries import compute_l1_linf_pair

    a = np.ones((1, 2, 4), dtype=np.float64)
    b = a.copy()
    b[..., 0] += 0.25
    path_a = tmp_path / "a.bin"
    path_b = tmp_path / "b.bin"
    _write_binary(path_a, a, t=0.1)
    _write_binary(path_b, b, t=0.1 + 5e-13)

    metric = compute_l1_linf_pair(path_a, path_b, variable="rho")

    assert metric["time"] == pytest.approx((0.1 + (0.1 + 5e-13)) / 2.0)
    assert metric["l1"] == pytest.approx(0.25)
