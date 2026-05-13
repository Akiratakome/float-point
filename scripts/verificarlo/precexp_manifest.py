from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_OUTPUT_ROOT = "experiments/week7/vfc_precexp"

CANDIDATE_SYMBOLS = [
    {
        "component": "muscl",
        "symbol_hint": "reconstruct_* / minmod / limiter path",
        "source": "src/euler/muscl.hpp",
        "reason": "slope reconstruction can amplify cancellation near discontinuities",
    },
    {
        "component": "hancock",
        "symbol_hint": "hancock_* predictor path",
        "source": "src/euler/hancock.hpp",
        "reason": "predictor combines reconstructed states and flux differences",
    },
    {
        "component": "flux",
        "symbol_hint": "hllc_flux / rusanov_flux",
        "source": "src/euler/hllc.hpp; src/euler/rusanov.hpp",
        "reason": "supervisor asked whether flux choice is the FP bottleneck",
    },
    {
        "component": "eos",
        "symbol_hint": "pressure / sound_speed / cons_to_prim",
        "source": "src/core/eos.hpp",
        "reason": "pressure subtracts kinetic energy from total energy",
    },
    {
        "component": "cfl",
        "symbol_hint": "CFL / timestep computation",
        "source": "src/euler/euler_solver.hpp; src/gpu/* future",
        "reason": "precision changes in timestep can alter trajectories",
    },
]


def build_manifest(
    cases: list[str],
    solvers: list[str],
    output_root: str = DEFAULT_OUTPUT_ROOT,
) -> dict:
    return {
        "experiment": "week7-vfc-precexp",
        "output_root": output_root,
        "cases": cases,
        "solvers": solvers,
        "candidate_symbols": CANDIDATE_SYMBOLS,
        "acceptance_criterion": "density_l1_relative_and_pressure_linf_against_ieee_reference",
        "old_artifact_boundary": "experiments/verificarlo/precexp is whole-program only",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", action="append", default=["sod", "stationary_contact"])
    parser.add_argument("--solver", action="append", default=["hllc", "rusanov"])
    parser.add_argument("--out", type=Path, default=Path(DEFAULT_OUTPUT_ROOT) / "manifest.json")
    args = parser.parse_args()

    manifest = build_manifest(args.case, args.solver)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
