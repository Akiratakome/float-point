import numpy as np
import subprocess
import sys

from scripts.verificarlo.precexp_compare import compare_primitive_arrays


def test_compare_primitive_arrays_accepts_small_density_and_pressure_errors() -> None:
    ref = np.array([[[1.0, 0.0, 0.0, 1.0], [0.5, 0.0, 0.0, 0.5]]])
    cand = ref.copy()
    cand[..., 0] *= 1.001
    cand[..., 3] *= 0.999

    result = compare_primitive_arrays(
        ref,
        cand,
        density_l1_rel_max=1.0e-2,
        pressure_linf_rel_max=5.0e-2,
    )

    assert result["accepted"] is True
    assert result["density_l1_rel"] < 1.0e-2
    assert result["pressure_linf_rel"] < 5.0e-2


def test_cli_help_works_when_run_by_script_path() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/verificarlo/precexp_compare.py",
            "--help",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0
    assert "--reference" in result.stdout
