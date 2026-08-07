#!/usr/bin/env python3
"""Analyse the HLL CFL 0.2 ladder using the week18 diagnostic definitions.

The week18 driver's report writer expects the full two-solver matrix, so this
reads the completed HLL-only runs directly and applies the same block-averaged
adjacent-grid and same-grid density norms. The point of the extra ladder is that
HLL now shares the HLLD time step, so the observed rates and the fp32-fp64
discrepancies become comparable across solvers instead of being confounded by
CFL.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
RUNS = ROOT / "experiments" / "week21" / "resolution_ladder_hll_cfl02" / "runs"
OUT = RUNS.parent

for path in (ROOT, ROOT / "scripts", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(path))

from io_helper import read_binary  # noqa: E402
from mhd_week18_resolution_ladder import (  # noqa: E402
    density_pair_norms,
    observed_order,
    same_grid_density_norms,
)

CASES = ("orszag_tang_2d", "kelvin_helmholtz_2d")
PRECISIONS = ("double", "float")
RESOLUTIONS = (128, 256, 512)
# Published CFL-0.2 HLLD counterparts, for the now-matched cross-solver read.
HLLD_ORDER = {"orszag_tang_2d": 0.846, "kelvin_helmholtz_2d": 1.442}


def load(case: str, precision: str, n: int) -> np.ndarray:
    d = RUNS / f"{case}-hll-{precision}-n{n}-cfl0p2" / "grid.bin"
    _header, arr = read_binary(d)
    return np.asarray(arr, dtype=np.float64)


def main() -> int:
    groups = []
    for case in CASES:
        for precision in PRECISIONS:
            fields = {n: load(case, precision, n) for n in RESOLUTIONS}
            e = {
                (128, 256): density_pair_norms(fields[128], fields[256])["l1"],
                (256, 512): density_pair_norms(fields[256], fields[512])["l1"],
            }
            groups.append({
                "case": case, "solver": "hll", "precision": precision, "cfl": 0.2,
                "e_128_256": e[(128, 256)], "e_256_512": e[(256, 512)],
                "observed_p": observed_order(e[(128, 256)], e[(256, 512)]),
            })
    # Same-grid fp32-fp64 discrepancy at matched CFL.
    precision_cells = []
    for case in CASES:
        for n in RESOLUTIONS:
            d = same_grid_density_norms(load(case, "float", n), load(case, "double", n))
            precision_cells.append({"case": case, "solver": "hll", "cfl": 0.2,
                                    "resolution": n, **d})

    payload = {
        "schema": {"name": "hrsc.week21-hll-ladder-cfl02", "version": 1},
        "experiment": "week21-hll-ladder-cfl02",
        "note": ("HLL re-run at the HLLD time step so the solver axis is no longer "
                 "confounded with CFL; diagnostics follow the week18 definitions."),
        "groups": groups,
        "precision_cells": precision_cells,
        "hlld_reference_order_cfl02": HLLD_ORDER,
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for g in groups:
        print(f"{g['case']:22s} {g['precision']:6s} p={g['observed_p']:.3f} "
              f"E(128,256)={g['e_128_256']:.5g} E(256,512)={g['e_256_512']:.5g}")
    print()
    for c in precision_cells:
        print(f"{c['case']:22s} N={c['resolution']:4d} D_N(mean L1)={c['l1']:.4e} "
              f"Linf={c['linf']:.4e}")
    print(f"\nwrote {OUT / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
