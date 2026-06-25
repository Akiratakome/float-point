import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts" / "regression"))
from _mhd_harness import block_average_2d, point_symmetry_residual, reflect_y_residual


def test_block_average_halves_resolution():
    # 4x4 of known blocks -> 2x2 means.
    arr = np.array([[1, 1, 2, 2],
                    [1, 1, 2, 2],
                    [3, 3, 4, 4],
                    [3, 3, 4, 4]], dtype=float)
    out = block_average_2d(arr, 2, 2)
    assert out.shape == (2, 2)
    np.testing.assert_allclose(out, [[1, 2], [3, 4]])


def test_block_average_requires_integer_factor():
    arr = np.ones((5, 4))
    try:
        block_average_2d(arr, 2, 2)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_point_symmetry_residual_zero_for_symmetric_field():
    base = np.arange(16, dtype=float).reshape(4, 4)
    sym = base + base[::-1, ::-1]  # invariant under 180-deg rotation
    assert point_symmetry_residual(sym) < 1e-12


def test_reflect_y_residual_zero_for_y_symmetric_field():
    col = np.array([0.0, 1.0, 1.0, 0.0])
    field = np.tile(col[:, None], (1, 3))  # symmetric under y -> Ny-1-y
    assert reflect_y_residual(field) < 1e-12
