#!/usr/bin/env python3
"""CPU instruction-set axis for the Brio--Wu MHD shock tube.

The assignment lists CPU architecture and vectorisation options alongside
precision and compiler flags. This driver holds optimisation level,
floating-point model, solver, grid, CFL and branch rule fixed and changes only
the MSVC baseline instruction set (``/arch:SSE2`` versus ``/arch:AVX2``), so
any output difference comes from the code the vectoriser is permitted to emit
rather than from relaxed floating-point semantics.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments" / "week20" / "brio_wu_cpu_arch"
EXPERIMENT = "week20-brio-wu-cpu-arch"

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

CFG = ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg"
SOLVERS = ("hll", "hlld")
BINS = {
    ("double", "sse2"): ROOT / "build-sse2" / "hrsc_mhd",
    ("float", "sse2"): ROOT / "build-sse2-float" / "hrsc_mhd",
    ("double", "avx2"): ROOT / "build-avx2" / "hrsc_mhd",
    ("float", "avx2"): ROOT / "build-avx2-float" / "hrsc_mhd",
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    runs = OUT / "runs"
    runs.mkdir(exist_ok=True)
    commit = git_commit()
    rows = []

    for solver in SOLVERS:
        for precision in ("double", "float"):
            grids = {}
            for arch in ("sse2", "avx2"):
                name = f"brio_wu_1d-{solver}-{precision}-{arch}"
                run_dir = runs / name
                run_dir.mkdir(exist_ok=True)
                out_bin = run_dir / "grid.bin"
                cfg_text = CFG.read_text(encoding="utf-8")
                cfg_text = replace_or_append_cfg(cfg_text, "riemann", solver)
                cfg_text = replace_or_append_cfg(cfg_text, "device", "cpu")
                cfg_text = replace_or_append_cfg(cfg_text, "output_format", "binary")
                cfg_text = replace_or_append_cfg(cfg_text, "output_file", str(out_bin))
                binary = resolve_binary(BINS[(precision, arch)])
                _proc, meta, _err = run_case(
                    label=name,
                    cfg_text=cfg_text,
                    run_dir=run_dir,
                    bin_path=binary,
                    source_cfg=CFG,
                    commit=commit,
                    binary_sha256=sha256_file(binary),
                    output_bin=out_bin,
                    experiment=EXPERIMENT,
                )
                _header, data = read_binary(out_bin)
                grids[arch] = np.asarray(data)
                print(f"  ran {name}: steps={meta['stderr_diagnostics']['steps']}")

            ref = grids["sse2"].astype(np.float64)
            cand = grids["avx2"].astype(np.float64)
            rho = np.abs(cand[..., 0] - ref[..., 0])
            # A null output difference is only informative if the two builds are
            # genuinely different programs, so both binary hashes are retained.
            sse2_sha = sha256_file(resolve_binary(BINS[(precision, "sse2")]))
            avx2_sha = sha256_file(resolve_binary(BINS[(precision, "avx2")]))
            rows.append({
                "case": "brio_wu_1d",
                "solver": solver,
                "precision": precision,
                "changed_axis": "/arch:AVX2 versus /arch:SSE2",
                "held_fixed": "O2, compiler-default math, <= branch, N=800, t=0.1, CFL 0.4",
                "rho_linf_abs": float(np.max(rho)),
                "rho_l1_mean_abs": float(np.mean(rho)),
                "bitwise_identical": bool(np.array_equal(grids["sse2"], grids["avx2"])),
                "sse2_binary_sha256": sse2_sha,
                "avx2_binary_sha256": avx2_sha,
                "binaries_differ": sse2_sha != avx2_sha,
            })
            r = rows[-1]
            print(f"  {solver} {precision}: bitwise={r['bitwise_identical']} "
                  f"rho_Linf={r['rho_linf_abs']:.6e}")

    summary = {
        "schema": {"name": "hrsc.week20-brio-wu-cpu-arch", "version": 1},
        "experiment": EXPERIMENT,
        "git_commit": commit,
        "claim_boundary": (
            "Only the MSVC baseline instruction set differs between the two "
            "columns; optimisation level, floating-point model, branch rule, "
            "solver, grid, CFL and final time are held fixed. Results describe "
            "this compiler on this processor."
        ),
        "rows": rows,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    for path in runs.rglob("grid.bin"):
        path.unlink()
    print(f"\nwrote {OUT / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
