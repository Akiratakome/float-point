#!/usr/bin/env python3
"""gen_a2_s2_figures.py — produce the 8 A2-S2 supervisor figures.

Pairs the MCA p=53 noise-floor .npz artefacts (from scripts/noise_floor_run.sh)
with IEEE-precision HLLC/Rusanov reference runs (from the host build) and
calls scripts/plot_divergence_marker.py in --mode noise_floor. Emits 4 figures
(one per test: sod, stationary_contact, toro2, toro4) × 2 variables (rho, p)
= 8 PNGs total.

Run from repo root after:
  (1) the overnight batch has produced all 8 noise_floor.npz files under
      experiments/week4/noise_floor/<test>/<solver>/, AND
  (2) a host-build hrsc.exe exists (cmake --build build -j).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

TESTS = ["sod", "stationary_contact", "toro2", "toro4"]
VARIABLES = ["rho", "p"]
REPO = Path(__file__).resolve().parent.parent
NF_BASE = REPO / "experiments" / "week4" / "noise_floor"
OUT_DIR = REPO / "experiments" / "week4" / "figures" / "a2_s2"


def run(cmd: list[str], *, cwd: Path = REPO) -> None:
    """Thin wrapper around subprocess.run that fails loud."""
    print(">>", " ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], cwd=str(cwd), check=True)


def reference_curve(test: str, solver: str) -> Path:
    """Return the reference-curve data file for (test, solver) plotting.

    We use sample_01.txt from the MCA p=53 batch rather than a native IEEE
    run because (a) toro2 in a debug host build trips an EOS near-vacuum
    assertion, and (b) MCA p=53 noise is ~1e-15, which is well below plot
    resolution and below the noise_floor envelope the plot already marks.
    """
    sample = NF_BASE / test / solver / "sample_01.txt"
    if not sample.exists():
        raise FileNotFoundError(f"missing {sample} — overnight batch not complete?")
    return sample


def npz_path(test: str, solver: str) -> Path:
    return NF_BASE / test / solver / "noise_floor.npz"


def plot(test: str, variable: str) -> None:
    """Dispatch plot_divergence_marker.py in noise_floor mode."""
    hllc_txt = reference_curve(test, "hllc")
    rus_txt = reference_curve(test, "rusanov")
    nf_hllc = npz_path(test, "hllc")
    nf_rus = npz_path(test, "rusanov")

    for p in (nf_hllc, nf_rus):
        if not p.exists():
            raise FileNotFoundError(f"missing {p} — batch not complete?")

    out_png = OUT_DIR / f"{test}_{variable}_noise_floor.png"
    out_png.parent.mkdir(parents=True, exist_ok=True)

    run([
        sys.executable, "scripts/plot_divergence_marker.py",
        "--input-a", hllc_txt, "--label-a", "HLLC",
        "--input-b", rus_txt, "--label-b", "Rusanov",
        "--variable", variable,
        "--mode", "noise_floor",
        "--noise-floor-a", nf_hllc,
        "--noise-floor-b", nf_rus,
        "--output", out_png,
        "--title", f"{test}: HLLC vs Rusanov ({variable}, MCA p=53 noise floor)",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests", nargs="+", default=TESTS,
                        help=f"subset of tests (default: {TESTS})")
    parser.add_argument("--variables", nargs="+", default=VARIABLES,
                        help=f"variables to plot (default: {VARIABLES})")
    args = parser.parse_args()

    for test in args.tests:
        for var in args.variables:
            plot(test, var)
    print(f"\nAll figures in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
