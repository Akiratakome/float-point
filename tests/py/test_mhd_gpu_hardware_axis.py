import numpy as np

from scripts.regression import mhd_gpu_hardware_axis as hw


def test_ulp_distance_is_zero_for_bit_equal_arrays():
    arr = np.array([[1.0, -2.0, 0.0]], dtype=np.float64)

    assert hw.max_ulp_distance(arr, arr.copy()) == 0


def test_ulp_distance_counts_adjacent_float32_values():
    arr = np.array([1.0, -1.0], dtype=np.float32)
    next_arr = np.nextafter(arr, np.array([2.0, -2.0], dtype=np.float32))

    assert hw.max_ulp_distance(arr, next_arr) == 1


def test_pair_metrics_pass_only_for_bit_exact_rows():
    cpu = np.array([[[1.0, 2.0]]], dtype=np.float64)
    gpu = cpu.copy()

    row = hw.compute_pair_metrics("case", "double", cpu, gpu, 2.5, 1.25)

    assert row["ulp_max"] == 0
    assert row["gate_passed"] is True
    assert row["speedup_cpu_over_gpu"] == 2.0

    gpu[..., 0] = np.nextafter(gpu[..., 0], 2.0)
    row = hw.compute_pair_metrics("case", "double", cpu, gpu, 1.25, 2.5)

    assert row["ulp_max"] == 1
    assert row["gate_passed"] is False


def test_cleanup_removes_only_recorded_grid_files(tmp_path):
    keep = tmp_path / "metadata.json"
    grid = tmp_path / "grid.bin"
    keep.write_text("{}", encoding="utf-8")
    grid.write_bytes(b"grid")

    hw.cleanup_transient_grids([grid])

    assert keep.is_file()
    assert not grid.exists()
