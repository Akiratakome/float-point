#!/usr/bin/env python3
"""GPU relaxed-math axis: nvcc --use_fast_math against the matched CPU baseline.

The contraction driver (week20) varies only ``--fmad``. ``--use_fast_math`` is
nvcc's composite relaxed-math switch and the device counterpart of the host
``/fp:fast`` axis: it implies ``--fmad=true``, ``--ftz=true``,
``--prec-div=false``, ``--prec-sqrt=false`` and fast intrinsics. This driver
adds it as a third device column so the device build axis is measured over the
whole relaxed-math setting, not just contraction.

Only the device translation-unit flags differ between the GPU columns; case,
grid, precision, host binary and update order are held fixed.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments" / "week21" / "gpu_fast_math"
EXPERIMENT = "week21-gpu-fast-math"

for path in (ROOT, ROOT / "scripts", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(path))

from io_helper import read_binary  # noqa: E402
from _mhd_harness import (  # noqa: E402
    git_commit,
    replace_or_append_cfg,
    resolve_binary,
    run_case,
    sha256_file,
)
from mhd_gpu_fma_axis import ulp_max  # noqa: E402

CASES = {
    "brio_wu_1d": ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg",
    "orszag_tang_2d": ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg",
}

# (precision, device, device_math) -> build directory
BINS = {
    ("double", "cpu", "host"): ROOT / "build-double" / "hrsc_mhd",
    ("float", "cpu", "host"): ROOT / "build-float" / "hrsc_mhd",
    ("double", "gpu", "strict"): ROOT / "build-cuda" / "hrsc_mhd",
    ("float", "gpu", "strict"): ROOT / "build-cuda-float" / "hrsc_mhd",
    ("double", "gpu", "fmad"): ROOT / "build-cuda-fmad" / "hrsc_mhd",
    ("float", "gpu", "fmad"): ROOT / "build-cuda-fmad-float" / "hrsc_mhd",
    ("double", "gpu", "fast"): ROOT / "build-cuda-fastmath" / "hrsc_mhd",
    ("float", "gpu", "fast"): ROOT / "build-cuda-fastmath-float" / "hrsc_mhd",
}
FLAGS = {
    "strict": "--fmad=false",
    "fmad": "--fmad=true",
    "fast": "--use_fast_math",
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    runs_dir = OUT / "runs"
    runs_dir.mkdir(exist_ok=True)
    commit = git_commit()
    rows = []

    for case, cfg_path in CASES.items():
        for precision in ("double", "float"):
            grids = {}
            for device, math_level in (("cpu", "host"), ("gpu", "strict"),
                                       ("gpu", "fmad"), ("gpu", "fast")):
                name = f"{case}-{precision}-{device}-{math_level}"
                run_dir = runs_dir / name
                run_dir.mkdir(exist_ok=True)
                out_bin = run_dir / "grid.bin"
                cfg_text = cfg_path.read_text(encoding="utf-8")
                cfg_text = replace_or_append_cfg(cfg_text, "riemann", "hll")
                cfg_text = replace_or_append_cfg(cfg_text, "device", device)
                cfg_text = replace_or_append_cfg(cfg_text, "output_format", "binary")
                cfg_text = replace_or_append_cfg(cfg_text, "output_file", str(out_bin))
                binary = resolve_binary(BINS[(precision, device, math_level)])
                _proc, meta, _err = run_case(
                    label=name, cfg_text=cfg_text, run_dir=run_dir,
                    bin_path=binary, source_cfg=cfg_path, commit=commit,
                    binary_sha256=sha256_file(binary), output_bin=out_bin,
                    experiment=EXPERIMENT,
                )
                header, data = read_binary(out_bin)
                grids[math_level] = (header, np.asarray(data))
                print(f"  ran {name}: steps={meta['stderr_diagnostics']['steps']}")

            dtype = "float64" if precision == "double" else "float32"
            cpu = grids["host"][1]
            for math_level in ("strict", "fmad", "fast"):
                gpu = grids[math_level][1]
                diff = np.abs(cpu.astype(np.float64) - gpu.astype(np.float64))
                rho_diff = np.abs(cpu.astype(np.float64)[..., 0]
                                  - gpu.astype(np.float64)[..., 0])
                rows.append({
                    "case": case, "precision": precision, "solver": "hll",
                    "device_math": math_level, "nvcc_flag": FLAGS[math_level],
                    "linf_abs": float(np.max(diff)),
                    "rho_linf_abs": float(np.max(rho_diff)),
                    "rho_l1_mean_abs": float(np.mean(rho_diff)),
                    "ulp_max": ulp_max(cpu, gpu, dtype),
                    "bitwise_identical": bool(np.array_equal(cpu, gpu)),
                    "nx": int(grids["host"][0].nx), "ny": int(grids["host"][0].ny),
                })
                print(f"  {case} {precision} {math_level}: "
                      f"bitwise={rows[-1]['bitwise_identical']} "
                      f"rho_Linf={rows[-1]['rho_linf_abs']:.6e}")

    summary = {
        "schema": {"name": "hrsc.week21-gpu-fast-math", "version": 1},
        "experiment": EXPERIMENT,
        "git_commit": commit,
        "claim_boundary": (
            "Only the device translation-unit math flags differ between the GPU "
            "columns. Host binary, case, grid, precision and update order are held "
            "fixed, so each row isolates one nvcc relaxed-math setting against "
            "MSVC's non-contracting /fp:precise host default."
        ),
        "rows": rows,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    for path in runs_dir.rglob("grid.bin"):
        path.unlink()
    print(f"\nwrote {OUT / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
