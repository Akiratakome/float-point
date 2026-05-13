from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.io_helper import cons_to_prim, read_binary


def _relative_l1(ref: np.ndarray, cand: np.ndarray) -> float:
    denom = float(np.sum(np.abs(ref)))
    if denom == 0.0:
        return float("inf")
    return float(np.sum(np.abs(cand - ref)) / denom)


def _relative_linf(ref: np.ndarray, cand: np.ndarray) -> float:
    denom = float(np.max(np.abs(ref)))
    if denom == 0.0:
        return float("inf")
    return float(np.max(np.abs(cand - ref)) / denom)


def compare_primitive_arrays(
    ref: np.ndarray,
    cand: np.ndarray,
    density_l1_rel_max: float,
    pressure_linf_rel_max: float,
) -> dict:
    if ref.shape != cand.shape:
        return {"accepted": False, "reason": f"shape mismatch {ref.shape} vs {cand.shape}"}

    density_l1_rel = _relative_l1(ref[..., 0], cand[..., 0])
    pressure_linf_rel = _relative_linf(ref[..., 3], cand[..., 3])
    accepted = (
        density_l1_rel <= density_l1_rel_max
        and pressure_linf_rel <= pressure_linf_rel_max
    )
    return {
        "accepted": accepted,
        "density_l1_rel": density_l1_rel,
        "pressure_linf_rel": pressure_linf_rel,
        "criterion": "density_l1_relative_and_pressure_linf_relative",
    }


def compare_binary(
    reference: Path,
    candidate: Path,
    gamma: float,
    density_l1_rel_max: float,
    pressure_linf_rel_max: float,
) -> dict:
    _, ref_cons = read_binary(reference)
    _, cand_cons = read_binary(candidate)
    ref = cons_to_prim(ref_cons.astype(np.float64), gamma)
    cand = cons_to_prim(cand_cons.astype(np.float64), gamma)
    return compare_primitive_arrays(
        ref,
        cand,
        density_l1_rel_max,
        pressure_linf_rel_max,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--gamma", type=float, default=1.4)
    parser.add_argument("--density-l1-rel-max", type=float, required=True)
    parser.add_argument("--pressure-linf-rel-max", type=float, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    result = compare_binary(
        args.reference,
        args.candidate,
        args.gamma,
        args.density_l1_rel_max,
        args.pressure_linf_rel_max,
    )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if result["accepted"] else 1)


if __name__ == "__main__":
    main()
