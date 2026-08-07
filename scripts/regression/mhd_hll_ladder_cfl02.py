#!/usr/bin/env python3
"""HLL refinement ladder at CFL 0.2, matching the HLLD ladder's time step.

The reported ladders ran HLL at CFL 0.4 and HLLD at CFL 0.2, so their observed
rates and precision discrepancies could not be compared across solvers. This
driver re-runs the HLL ladder at CFL 0.2 so that the solver axis is isolated:
case, grid, precision, time step and stopping time all match the HLLD ladder,
and only the Riemann flux differs.

Writes to a separate experiment directory; the week18 packet is untouched.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "scripts", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(path))

import mhd_week18_resolution_ladder as ladder  # noqa: E402

OUT = ROOT / "experiments" / "week21" / "resolution_ladder_hll_cfl02"


def main() -> int:
    # Only the HLL arm is missing at CFL 0.2; HLLD already ran there.
    ladder.SOLVERS = ("hll",)
    ladder.CFL_BY_SOLVER = {"hll": 0.2, "hlld": 0.2}
    ladder.EXPERIMENT = "week21-hll-ladder-cfl02"
    return ladder.main(["--out", str(OUT)])


if __name__ == "__main__":
    raise SystemExit(main())
