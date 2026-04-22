"""
compute_noise_floor.py — build per-cell MCA noise-floor envelope.

Stage 2 (A2-S2). Consumes N Verificarlo MCA sample files produced by
``scripts/noise_floor_run.sh`` and writes a single ``.npz`` containing
per-cell standard deviations for (rho, u, v, p), plus provenance metadata.

Input sample file format (produced by the HRSC solver in 1D):
    columns: x  rho  u  v  p     (5 columns)

The divergence detector (``scripts/plot_divergence_marker.py`` in mode
``noise_floor``) consumes the resulting ``.npz`` to build per-cell tolerance.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

import numpy as np

# ---------------------------------------------------------------------------
# Module constants — each explained in-place (no magic numbers rule)
# ---------------------------------------------------------------------------

# Verificarlo MCA precision at full binary64 mantissa. Stage 2 pins this to 53
# per plan §A2.1; any other value in the .npz metadata is a contract violation.
PRECISION_BITS_P53 = 53

# HRSC 1D column layout in sample_NN.txt files (0-based indexing)
COL_X = 0
COL_RHO = 1
COL_U = 2
COL_V = 3
COL_P = 4
N_FIELD_COLS = 4           # rho, u, v, p — x is the grid, handled separately
EXPECTED_N_COLS = 5        # x, rho, u, v, p


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_cmd_capture(cmd: Sequence[str]) -> str:
    """Run a short command, return stripped stdout, or 'unknown' on any failure.

    Used only for provenance (vfc version, git sha). Never aborts the run.
    """
    try:
        out = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, text=True, timeout=5
        )
        return out.strip().splitlines()[0] if out.strip() else "unknown"
    except Exception:
        return "unknown"


def _load_samples(sample_paths: Sequence[Path]) -> tuple[np.ndarray, np.ndarray]:
    """Load N sample files into a stacked ``(N, nx, 4)`` field array.

    Returns
    -------
    x : np.ndarray, shape (nx,)
        Grid, taken from the first sample. Subsequent samples must share it.
    fields : np.ndarray, shape (N, nx, 4)
        Axis-2 order: (rho, u, v, p).
    """
    arrays = []
    x_ref = None
    for p in sample_paths:
        data = np.loadtxt(str(p))
        if data.ndim != 2 or data.shape[1] != EXPECTED_N_COLS:
            raise ValueError(
                f"{p}: expected 2-D array with {EXPECTED_N_COLS} columns "
                f"(x,rho,u,v,p); got shape {data.shape}"
            )
        if x_ref is None:
            x_ref = data[:, COL_X]
        elif not np.array_equal(x_ref, data[:, COL_X]):
            raise ValueError(
                f"{p}: grid disagrees with first sample {sample_paths[0]}; "
                "all MCA samples must share the same x-grid."
            )
        arrays.append(data[:, [COL_RHO, COL_U, COL_V, COL_P]])
    fields = np.stack(arrays, axis=0)
    return x_ref, fields


def _check_seed_independence(seeds_csv: Path, n_expected: int) -> str:
    """Assert /dev/urandom gave N distinct seeds, return seeds-sha256 hex.

    Uses stdlib csv (no pandas dependency assumed). Fails loudly on duplicates,
    which would mean /dev/urandom is broken or the bash loop was mis-seeded.
    """
    import csv
    seeds = []
    with seeds_csv.open() as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or "seed_hex" not in reader.fieldnames:
            raise ValueError(
                f"{seeds_csv}: expected CSV with header including 'seed_hex'; "
                f"got fields {reader.fieldnames!r}"
            )
        for row in reader:
            seeds.append(row["seed_hex"].strip())

    if len(seeds) != n_expected:
        raise ValueError(
            f"{seeds_csv}: found {len(seeds)} seed rows, expected "
            f"{n_expected} (one per sample file)"
        )
    unique = set(seeds)
    if len(unique) != len(seeds):
        raise ValueError(
            f"{seeds_csv}: duplicate seeds detected "
            f"({len(seeds) - len(unique)} duplicates). "
            "This indicates /dev/urandom failure or mis-wired loop; abort."
        )

    # sha256 of sorted seed list for reproducible provenance fingerprint.
    joined = "\n".join(sorted(seeds)).encode("utf-8")
    return hashlib.sha256(joined).hexdigest()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Compute per-cell MCA p=53 noise-floor std field from N Verificarlo "
            "samples, save as .npz for the divergence detector."
        )
    )
    p.add_argument(
        "--samples", required=True, nargs="+", metavar="PATH",
        help="Sample files (glob-expanded by the shell), one per MCA run.",
    )
    p.add_argument(
        "--seeds", required=True, metavar="CSV",
        help="CSV of per-sample seeds (sample_id,seed_hex,timestamp_utc).",
    )
    p.add_argument(
        "--out", required=True, metavar="NPZ",
        help="Output .npz path.",
    )
    p.add_argument(
        "--solver", required=True, metavar="STR",
        help="Solver label (e.g. 'hllc' or 'rusanov') for provenance.",
    )
    p.add_argument(
        "--cfg", required=True, metavar="STR",
        help="Config file path / identifier for provenance.",
    )
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    sample_paths = [Path(s) for s in args.samples]
    seeds_csv = Path(args.seeds)
    out_path = Path(args.out)

    n_samples = len(sample_paths)
    if n_samples < 2:
        raise ValueError(
            f"--samples expanded to {n_samples} files; need >=2 for a std."
        )

    x, fields = _load_samples(sample_paths)        # fields: (N, nx, 4)
    seeds_sha256 = _check_seed_independence(seeds_csv, n_samples)

    # ddof=1 = sample std (Bessel-corrected). We are estimating a population
    # noise floor from a finite MCA draw, so the unbiased estimator is right.
    std_field = np.std(fields, axis=0, ddof=1)     # (nx, 4)
    rho_std = std_field[:, 0]
    u_std = std_field[:, 1]
    v_std = std_field[:, 2]
    p_std = std_field[:, 3]

    vfc_version = _safe_cmd_capture(["verificarlo-c++", "--version"])
    git_sha = _safe_cmd_capture(["git", "rev-parse", "HEAD"])

    metadata = {
        "solver": args.solver,
        "cfg": args.cfg,
        "precision_bits": PRECISION_BITS_P53,
        "n_samples": n_samples,
        "vfc_version": vfc_version,
        "git_sha": git_sha,
        "seeds_sha256": seeds_sha256,
        "generated_utc": _dt.datetime.utcnow().isoformat() + "Z",
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        out_path,
        x=x,
        rho_std=rho_std,
        u_std=u_std,
        v_std=v_std,
        p_std=p_std,
        # Stored as 0-D object array; unpack on load with `.item()`.
        metadata=np.array(metadata, dtype=object),
    )

    print(
        f"Wrote {out_path}: nx={x.size}, N={n_samples}, "
        f"max(rho_std)={rho_std.max():.3e}, max(p_std)={p_std.max():.3e}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
