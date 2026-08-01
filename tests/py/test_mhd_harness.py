import json
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts" / "regression"))
from _mhd_harness import (
    ROOT,
    block_average_2d,
    parse_mhd_diagnostics,
    point_symmetry_residual,
    reflect_y_residual,
    replace_or_append_cfg,
    run_case,
)


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


def test_block_average_requires_positive_target_shape():
    arr = np.ones((4, 4))
    try:
        block_average_2d(arr, 0, 2)
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


def test_symmetry_residuals_handle_zero_fields():
    field = np.zeros((3, 5))
    assert point_symmetry_residual(field) == 0.0
    assert reflect_y_residual(field) == 0.0


def test_replace_or_append_cfg_preserves_inline_comment():
    text = "nx = 128  # validation grid\n# ny = 64\nny = 32\n"
    out = replace_or_append_cfg(text, "nx", "256")
    assert out == "nx = 256  # validation grid\n# ny = 64\nny = 32\n"


def test_replace_or_append_cfg_appends_missing_key_with_trailing_newline():
    out = replace_or_append_cfg("nx = 128", "ny", "64")
    assert out == "nx = 128\nny = 64\n"


def test_parse_mhd_diagnostics_reads_last_mhd_line():
    stderr = "\n".join([
        "[mhd] t=0.100000 steps=10 divB_mean=1.000e-05 divB_max=2.000e-04",
        "noise",
        "[mhd] t=0.200000 steps=20 divB_mean=3.000e-06 divB_max=4.000e-05",
    ])
    diag = parse_mhd_diagnostics(stderr)
    assert diag["t"] == 0.2
    assert diag["steps"] == 20
    assert diag["divB_mean"] == 3e-6
    assert diag["divB_max"] == 4e-5


def test_run_case_checks_relative_output_bin_against_root(tmp_path):
    rel_out = pathlib.Path("test_mhd_harness_relative_output.bin")
    abs_out = ROOT / rel_out
    if abs_out.exists():
        abs_out.unlink()
    source_cfg = tmp_path / "source.cfg"
    source_cfg.write_text("placeholder = 1\n", encoding="utf-8")
    cfg_text = (
        "import pathlib\n"
        f"pathlib.Path({str(rel_out)!r}).write_bytes(b'ok')\n"
    )
    try:
        _, meta, _ = run_case(
            "relative-output",
            cfg_text,
            tmp_path / "run",
            pathlib.Path(sys.executable),
            source_cfg,
            "test-commit",
            "test-sha",
            output_bin=rel_out,
        )
        assert meta["schema"] == {"name": "hrsc.run-record", "version": 1}
        assert meta["status"] == "success"
        assert meta["output_binary"] == str(abs_out)
        assert meta["artifacts"]["primary_output"] == str(abs_out)
        assert meta["elapsed_wall_s"] == meta["timing"]["elapsed_wall_s"]
        assert meta["stderr_diagnostics"] == {}
        assert meta["build_semantics"]["effective_math_mode"] == "unknown"
    finally:
        if abs_out.exists():
            abs_out.unlink()


def test_run_case_writes_failed_metadata_before_raising(tmp_path):
    source_cfg = tmp_path / "source.cfg"
    source_cfg.write_text("placeholder = 1\n", encoding="utf-8")
    run_dir = tmp_path / "run"

    with pytest.raises(RuntimeError, match=r"failed \(rc=7\)"):
        run_case(
            "failed-run",
            "import sys\nsys.exit(7)\n",
            run_dir,
            pathlib.Path(sys.executable),
            source_cfg,
            "test-commit",
            "test-sha",
        )

    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "failed"


def test_run_case_replaces_non_utf8_stderr_and_accepts_required_output(tmp_path):
    source_cfg = tmp_path / "source.cfg"
    output_bin = tmp_path / "output.bin"
    source_cfg.write_text("placeholder = 1\n", encoding="utf-8")
    cfg_text = (
        "import pathlib\n"
        "import sys\n"
        f"pathlib.Path({str(output_bin)!r}).write_bytes(b'ok')\n"
        "sys.stderr.buffer.write(b'\\x80')\n"
    )

    result, metadata, stderr_text = run_case(
        "non-utf8-stderr",
        cfg_text,
        tmp_path / "run",
        pathlib.Path(sys.executable),
        source_cfg,
        "test-commit",
        "test-sha",
        output_bin=output_bin,
    )

    assert result.returncode == 0
    assert metadata["status"] == "success"
    assert "\ufffd" in stderr_text


def test_run_case_propagates_missing_binary_as_file_not_found(tmp_path):
    source_cfg = tmp_path / "source.cfg"
    missing_binary = tmp_path / "missing-hrsc"
    run_dir = tmp_path / "run"
    source_cfg.write_text("placeholder = 1\n", encoding="utf-8")

    with pytest.raises(FileNotFoundError) as error:
        run_case(
            "missing-binary",
            "placeholder = 1\n",
            run_dir,
            missing_binary,
            source_cfg,
            "test-commit",
            "test-sha",
        )

    assert error.value.filename == str(missing_binary)
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "failed"
    assert metadata["failure"]["category"] == "infrastructure_error"
    assert metadata["failure"]["exception_type"] == "FileNotFoundError"
