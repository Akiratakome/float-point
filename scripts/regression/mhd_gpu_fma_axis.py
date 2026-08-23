#!/usr/bin/env python3
"""GPU multiply-add contraction axis for the MHD HLL path.

The reported CPU/GPU bitwise agreement is obtained with the device kernels
compiled ``--fmad=false`` so that they match MSVC's non-contracting
``/fp:precise`` host default.  This driver rebuilds the same kernels with
nvcc's own default ``--fmad=true`` (CMake option ``GPU_FMA_CONTRACT=ON``) and
re-runs the matched comparison, so that the effect of contraction is measured
rather than assumed.

Only the device build differs between the two GPU columns; case, grid,
precision, host binary and update order are held fixed.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments" / "week20" / "gpu_fma_contraction"
EXPERIMENT = "week20-gpu-fma-contraction"

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

CASES = {
    "brio_wu_1d": ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg",
    "orszag_tang_2d": ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg",
}

# (precision, device, contraction) -> build directory
BINS = {
    ("double", "cpu", "host"): ROOT / "build-double" / "hrsc_mhd",
    ("float", "cpu", "host"): ROOT / "build-float" / "hrsc_mhd",
    ("double", "gpu", "off"): ROOT / "build-cuda" / "hrsc_mhd",
    ("float", "gpu", "off"): ROOT / "build-cuda-float" / "hrsc_mhd",
    ("double", "gpu", "on"): ROOT / "build-cuda-fmad" / "hrsc_mhd",
    ("float", "gpu", "on"): ROOT / "build-cuda-fmad-float" / "hrsc_mhd",
}


def ulp_max(a: np.ndarray, b: np.ndarray, dtype: str) -> int:
    """Largest cellwise distance in units in the last place.

    Sign-adjusted bit patterns of one IEEE type map to monotone integers; the
    reported value is the maximum absolute difference of those integers.
    """
    itype = np.int32 if dtype == "float32" else np.int64
    offset = np.iinfo(itype).min

    def to_ordered(x: np.ndarray) -> np.ndarray:
        bits = x.astype(dtype).view(itype).astype(np.int64)
        return np.where(bits < 0, offset - bits, bits)

    return int(np.max(np.abs(to_ordered(a) - to_ordered(b))))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    runs_dir = OUT / "runs"
    runs_dir.mkdir(exist_ok=True)
    commit = git_commit()
    rows = []

    for case, cfg_path in CASES.items():
        for precision in ("double", "float"):
            grids = {}
            for device, contraction in (("cpu", "host"), ("gpu", "off"), ("gpu", "on")):
                name = f"{case}-{precision}-{device}-fmad_{contraction}"
                run_dir = runs_dir / name
                run_dir.mkdir(exist_ok=True)
                out_bin = run_dir / "grid.bin"
                cfg_text = cfg_path.read_text(encoding="utf-8")
                cfg_text = replace_or_append_cfg(cfg_text, "riemann", "hll")
                cfg_text = replace_or_append_cfg(cfg_text, "device", device)
                cfg_text = replace_or_append_cfg(cfg_text, "output_format", "binary")
                cfg_text = replace_or_append_cfg(cfg_text, "output_file", str(out_bin))
                binary = resolve_binary(BINS[(precision, device, contraction)])
                record = run_case(
                    label=name,
                    cfg_text=cfg_text,
                    run_dir=run_dir,
                    bin_path=binary,
                    source_cfg=cfg_path,
                    commit=commit,
                    binary_sha256=sha256_file(binary),
                    output_bin=out_bin,
                    experiment=EXPERIMENT,
                )
                _proc, meta, _err = record
                header, data = read_binary(out_bin)
                grids[(device, contraction)] = (header, np.asarray(data))
                steps = meta["stderr_diagnostics"]["steps"]
                print(f"  ran {name}: steps={steps}")

            dtype = "float64" if precision == "double" else "float32"
            cpu = grids[("cpu", "host")][1]
            for contraction in ("off", "on"):
                gpu = grids[("gpu", contraction)][1]
                diff = np.abs(cpu.astype(np.float64) - gpu.astype(np.float64))
                rho_diff = np.abs(cpu.astype(np.float64)[..., 0]
                                  - gpu.astype(np.float64)[..., 0])
                rows.append({
                    "case": case,
                    "precision": precision,
                    "solver": "hll",
                    "device_pair": "cpu-vs-gpu",
                    "fma_contraction": contraction,
                    "nvcc_flag": "--fmad=false" if contraction == "off" else "--fmad=true",
                    "linf_abs": float(np.max(diff)),
                    "l1_mean_abs": float(np.mean(diff)),
                    "rho_linf_abs": float(np.max(rho_diff)),
                    "rho_l1_mean_abs": float(np.mean(rho_diff)),
                    "ulp_max": ulp_max(cpu, gpu, dtype),
                    "bitwise_identical": bool(np.array_equal(cpu, gpu)),
                    "nx": int(grids[("cpu", "host")][0].nx),
                    "ny": int(grids[("cpu", "host")][0].ny),
                })
                print(f"  {case} {precision} fmad={contraction}: "
                      f"bitwise={rows[-1]['bitwise_identical']} "
                      f"rho_Linf={rows[-1]['rho_linf_abs']:.6e} "
                      f"all_Linf={rows[-1]['linf_abs']:.6e}")

    summary = {
        "schema": {"name": "hrsc.week20-gpu-fma-contraction", "version": 1},
        "experiment": EXPERIMENT,
        "git_commit": commit,
        "claim_boundary": (
            "Only the device translation-unit contraction flag differs between the "
            "two GPU columns. Host binary, case, grid, precision and update order "
            "are held fixed, so the difference isolates nvcc multiply-add "
            "contraction against MSVC's non-contracting /fp:precise default."
        ),
        "rows": rows,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Transient grids are not retained; the scalar comparison is the evidence.
    for path in runs_dir.rglob("grid.bin"):
        path.unlink()

    print(f"\nwrote {OUT / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
