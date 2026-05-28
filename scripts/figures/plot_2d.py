#!/usr/bin/env python3
# scripts/figures/plot_2d.py
#
# Single-grid 2D visualisation. Reads one .bin produced by hrsc and writes
# one PNG per --field. Reuses scripts/io_helper.read_binary so the precision
# tag (float vs double) is honoured automatically.
#
# Week 5 scope: single-grid viewer only. No batch mode, no summary.json
# reading.

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from io_helper import IDX_E, IDX_RHO, IDX_RHOU, IDX_RHOV, read_binary  # noqa: E402
from _style import SEQUENTIAL_CMAP, apply, save_pair  # noqa: E402

apply()

GAMMA_DEFAULT = 1.4
SUPPORTED_FIELDS = ("rho", "p", "vmag", "schlieren")


def compute_field(
    arr: np.ndarray, field: str, gamma: float, *, dx: float, dy: float
) -> np.ndarray:
    """Return a 2D (ny, nx) array for the named field.

    arr shape: (ny, nx, 4), conserved variables (rho, rho*u, rho*v, E).
    """
    rho = arr[..., IDX_RHO]
    momx = arr[..., IDX_RHOU]
    momy = arr[..., IDX_RHOV]
    energy = arr[..., IDX_E]

    if field == "rho":
        return rho
    if field == "p":
        u = momx / rho
        v = momy / rho
        kinetic = 0.5 * rho * (u * u + v * v)
        return (gamma - 1.0) * (energy - kinetic)
    if field == "vmag":
        u = momx / rho
        v = momy / rho
        return np.sqrt(u * u + v * v)
    if field == "schlieren":
        gx = np.gradient(rho, dx, axis=1)
        gy = np.gradient(rho, dy, axis=0)
        return np.sqrt(gx * gx + gy * gy)
    raise ValueError(f"Unknown field: {field}")


def render_field(
    arr2d: np.ndarray,
    header,
    *,
    out_path: Path,
    field: str,
    cmap: str,
    vmin: float | None,
    vmax: float | None,
    title: str | None,
    save_pair_outdir: Path | None = None,
) -> None:
    height = max(3.0, 8.0 * header.ny / max(header.nx, 1))
    fig, ax = plt.subplots(figsize=(8, height))
    extent = [0, header.nx * header.dx, 0, header.ny * header.dy]
    field_label = "density schlieren" if field == "schlieren" else field
    im = ax.imshow(
        arr2d,
        origin="lower",
        extent=extent,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        aspect="equal",
    )
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    if title is not None:
        ax.set_title(title)
    fig.colorbar(im, ax=ax, label=field_label)
    fig.tight_layout()
    if save_pair_outdir is not None:
        save_pair(fig, out_path.stem, str(save_pair_outdir))
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=120)
    plt.close(fig)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Single-grid 2D plotter for hrsc binary outputs."
    )
    parser.add_argument("input", type=Path, help="Path to .bin written by hrsc")
    parser.add_argument(
        "--field",
        action="append",
        required=True,
        choices=SUPPORTED_FIELDS,
        help="Field to plot; repeat for multiple PNGs",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output PNG path; later fields append '_<field>' to the stem",
    )
    parser.add_argument("--cmap", default=SEQUENTIAL_CMAP)
    parser.add_argument("--vmin", type=float, default=None)
    parser.add_argument("--vmax", type=float, default=None)
    parser.add_argument("--title", default=None)
    parser.add_argument(
        "--save-pair",
        type=Path,
        default=None,
        help="If set, save both PDF and PNG via _style.save_pair to this directory. "
             "The stem is derived from --out (and per-field suffix). Overrides direct savefig.",
    )
    parser.add_argument(
        "--gamma",
        type=float,
        default=GAMMA_DEFAULT,
        help="EOS gamma for derived fields; default 1.4",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    header, arr = read_binary(args.input)
    out_base = args.out

    for index, field in enumerate(args.field):
        if index == 0:
            out_path = out_base
        else:
            out_path = out_base.with_name(f"{out_base.stem}_{field}{out_base.suffix}")
        arr2d = compute_field(arr, field, args.gamma, dx=header.dx, dy=header.dy)
        render_field(
            arr2d,
            header,
            out_path=out_path,
            field=field,
            cmap=args.cmap,
            vmin=args.vmin,
            vmax=args.vmax,
            title=args.title,
            save_pair_outdir=args.save_pair,
        )
        if args.save_pair is not None:
            print(f"wrote pair {args.save_pair}/{out_path.stem}.{{pdf,png}}")
        else:
            print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
