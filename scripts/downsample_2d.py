#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from io_helper import cons_to_prim, read_binary

VAR_NAMES = ("rho", "u", "v", "p")


def downsample_conserved(reference_cons: np.ndarray, target_nx: int, target_ny: int) -> np.ndarray:
    ref_ny, ref_nx, ref_nvars = reference_cons.shape
    if ref_nvars != 4:
        raise ValueError(f"Expected nvars=4, got {ref_nvars}")
    if ref_nx % target_nx != 0 or ref_ny % target_ny != 0:
        raise ValueError(
            f"Reference shape {ref_nx}x{ref_ny} cannot downsample to "
            f"{target_nx}x{target_ny}: non-integer ratio"
        )
    rx = ref_nx // target_nx
    ry = ref_ny // target_ny
    return reference_cons.reshape(target_ny, ry, target_nx, rx, ref_nvars).mean(axis=(1, 3))


def primitive_error_norms(candidate_prim: np.ndarray, reference_prim: np.ndarray) -> dict[str, dict[str, float]]:
    if candidate_prim.shape != reference_prim.shape:
        raise ValueError(
            f"Shape mismatch: candidate {candidate_prim.shape} vs reference {reference_prim.shape}"
        )
    out: dict[str, dict[str, float]] = {}
    for idx, name in enumerate(VAR_NAMES):
        diff = candidate_prim[..., idx] - reference_prim[..., idx]
        out[name] = {
            "L1": float(np.mean(np.abs(diff))),
            "L2": float(np.sqrt(np.mean(diff * diff))),
            "Linf": float(np.max(np.abs(diff))),
        }
    return out


def compare_candidate_to_reference(
    candidate_bin: Path,
    reference_bin: Path,
    gamma: float,
) -> dict[str, object]:
    cand_header, cand_cons = read_binary(candidate_bin)
    ref_header, ref_cons = read_binary(reference_bin)
    if cand_cons.shape[-1] != 4 or ref_cons.shape[-1] != 4:
        raise ValueError("Only Euler nvars=4 binaries are supported")
    ref_down_cons = downsample_conserved(ref_cons.astype(np.float64), cand_header.nx, cand_header.ny)
    cand_prim = cons_to_prim(cand_cons.astype(np.float64), gamma)
    ref_down_prim = cons_to_prim(ref_down_cons, gamma)
    return {
        "candidate_file": str(candidate_bin),
        "reference_file": str(reference_bin),
        "candidate_shape": [cand_header.nx, cand_header.ny],
        "reference_shape": [ref_header.nx, ref_header.ny],
        "metrics": primitive_error_norms(cand_prim, ref_down_prim),
    }


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Conserved-variable block-average downsample + primitive error norms."
    )
    p.add_argument("--candidate", required=True, type=Path, help="Candidate binary path")
    p.add_argument("--reference", required=True, type=Path, help="Reference binary path")
    p.add_argument("--gamma", type=float, default=1.4)
    p.add_argument("--out", type=Path, default=None, help="Optional JSON output path")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    result = compare_candidate_to_reference(args.candidate, args.reference, args.gamma)
    text = json.dumps(result, indent=2)
    print(text)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

