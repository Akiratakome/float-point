"""Binary grid I/O helper for 2D Verificarlo MCA samples.

Matches the 64-byte little-endian header written by ``hrsc::write_binary``
in ``src/utils/io.hpp``:

    offset  size  field
    ------  ----  -------------------------
         0     4  magic  = b"HRSC"
         4     4  nx       (int32)
         8     4  ny       (int32)
        12     4  nvars    (int32)
        16     4  precision_tag (int32, = sizeof(Real) in bytes)
        20     8  t        (float64)
        28     8  dx       (float64)
        36     8  dy       (float64)
        44    20  reserved (zeroed)

Body: row-major C order, shape (ny, nx, nvars), dtype matches
``precision_tag`` (4 → float32, 8 → float64).

Keeps numpy-only — no pandas / scipy — so analyzers can import from
minimal environments (e.g. cluster login nodes).
"""

from __future__ import annotations

import glob
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List

import numpy as np


_HEADER_SIZE = 64
_MAGIC = b"HRSC"

# Conserved-variable indices — mirror core/types.hpp (RHO, RHOU, RHOV, E).
IDX_RHO  = 0
IDX_RHOU = 1
IDX_RHOV = 2
IDX_E    = 3


@dataclass(frozen=True)
class GridHeader:
    nx: int
    ny: int
    nvars: int
    precision_tag: int   # bytes per Real
    t: float
    dx: float
    dy: float

    @property
    def dtype(self) -> np.dtype:
        if self.precision_tag == 8:
            return np.dtype("<f8")
        if self.precision_tag == 4:
            return np.dtype("<f4")
        raise ValueError(f"Unsupported precision_tag={self.precision_tag}")


def read_header(path: str | Path) -> GridHeader:
    with open(path, "rb") as f:
        buf = f.read(_HEADER_SIZE)
    if len(buf) != _HEADER_SIZE:
        raise IOError(f"Short header ({len(buf)}B) in {path}")
    if buf[:4] != _MAGIC:
        raise IOError(f"Bad magic {buf[:4]!r} in {path}")
    nx, ny, nvars, prec = struct.unpack("<iiii", buf[4:20])
    t, dx, dy = struct.unpack("<ddd", buf[20:44])
    return GridHeader(nx=nx, ny=ny, nvars=nvars, precision_tag=prec,
                      t=t, dx=dx, dy=dy)


def read_binary(path: str | Path) -> tuple[GridHeader, np.ndarray]:
    """Return (header, data[ny, nx, nvars]). dtype follows header.precision_tag."""
    h = read_header(path)
    with open(path, "rb") as f:
        f.seek(_HEADER_SIZE)
        raw = f.read()
    expected = h.ny * h.nx * h.nvars * h.precision_tag
    if len(raw) != expected:
        raise IOError(
            f"Body size {len(raw)}B != expected {expected}B "
            f"(nx={h.nx}, ny={h.ny}, nvars={h.nvars}, prec={h.precision_tag}) in {path}"
        )
    arr = np.frombuffer(raw, dtype=h.dtype).reshape(h.ny, h.nx, h.nvars)
    return h, arr


def cons_to_prim(cons: np.ndarray, gamma: float) -> np.ndarray:
    """Convert conserved (rho, rho*u, rho*v, E) → primitive (rho, u, v, p).

    Vectorised over leading axes; last axis is the variable axis of length 4.
    """
    if cons.shape[-1] != 4:
        raise ValueError(f"Expected last axis=4 (EulerNVars), got {cons.shape}")
    rho  = cons[..., IDX_RHO]
    u    = cons[..., IDX_RHOU] / rho
    v    = cons[..., IDX_RHOV] / rho
    E    = cons[..., IDX_E]
    p    = (gamma - 1.0) * (E - 0.5 * rho * (u * u + v * v))
    prim = np.stack([rho, u, v, p], axis=-1)
    return prim


def iter_sample_bins(sample_root: str | Path) -> Iterator[Path]:
    """Yield grid.bin paths for sample_* subdirs in sorted order."""
    root = Path(sample_root)
    for d in sorted(root.glob("sample_*")):
        bin_path = d / "grid.bin"
        if bin_path.is_file():
            yield bin_path


def stack_samples(sample_root: str | Path) -> tuple[GridHeader, np.ndarray, List[Path]]:
    """Stack all sample_*/grid.bin into (n_samples, ny, nx, nvars).

    All samples must share the same header shape. Raises if any differs.
    """
    paths = list(iter_sample_bins(sample_root))
    if not paths:
        raise FileNotFoundError(f"No sample_*/grid.bin under {sample_root}")
    ref_h, first = read_binary(paths[0])
    out = np.empty((len(paths), ref_h.ny, ref_h.nx, ref_h.nvars), dtype=first.dtype)
    out[0] = first
    for k, p in enumerate(paths[1:], start=1):
        h, arr = read_binary(p)
        if (h.nx, h.ny, h.nvars, h.precision_tag) != (
                ref_h.nx, ref_h.ny, ref_h.nvars, ref_h.precision_tag):
            raise ValueError(
                f"Shape / dtype mismatch at {p}: {h} vs ref {ref_h}")
        out[k] = arr
    return ref_h, out, paths


def load_seeds(seed_dir: str | Path, expected_n: int) -> List[dict]:
    """Concatenate per-task seed CSVs written by verificarlo_2d_array.sh.

    Each file is a 1-row CSV with (sample_id, seed_dec, seed_hex, timestamp_utc).
    Returns list of dicts. Pandas intentionally not required here.
    """
    import csv
    paths = sorted(glob.glob(str(Path(seed_dir) / "seed_*.csv")))
    if len(paths) != expected_n:
        raise AssertionError(
            f"Missing per-task seed files: {len(paths)}/{expected_n} in {seed_dir}"
        )
    rows: List[dict] = []
    for p in paths:
        with open(p, newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)
    seeds = {r["seed_hex"] for r in rows}
    if len(seeds) != len(rows):
        raise AssertionError(
            "Duplicate MCA seeds — /dev/urandom entropy failure; re-run affected samples"
        )
    return rows
