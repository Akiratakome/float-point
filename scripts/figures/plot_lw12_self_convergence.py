#!/usr/bin/env python3
"""LW12 fp64 self-convergence figure for Appendix A.4.

Block-averages successive fp64 grids (200, 400, 800, 1600) and reports
the L1 difference of each primitive variable between successive grid
pairs. Layout mirrors Appendix A.2 (LW3 self-convergence).
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from scripts.io_helper import IDX_E, IDX_RHO, IDX_RHOU, IDX_RHOV, read_binary  # noqa: E402
from _style import apply, save_pair  # noqa: E402

apply()
OUT = ROOT / "report1" / "phd-thesis-template-2.4" / "Figs" / "report1"
GAMMA = 1.4


def primitives(arr: np.ndarray):
    rho = arr[..., IDX_RHO]
    u = arr[..., IDX_RHOU] / rho
    v = arr[..., IDX_RHOV] / rho
    E = arr[..., IDX_E]
    p = (GAMMA - 1.0) * (E - 0.5 * rho * (u * u + v * v))
    return rho, u, v, p


def block_average(field: np.ndarray, ratio: int) -> np.ndarray:
    ny, nx = field.shape
    if ny % ratio != 0 or nx % ratio != 0:
        raise ValueError("grid not divisible by block ratio")
    return field.reshape(ny // ratio, ratio, nx // ratio, ratio).mean(axis=(1, 3))


def l1_diff(coarse: np.ndarray, fine: np.ndarray) -> float:
    """Block-average fine to coarse, then mean(|coarse - fine_avg|)."""
    if coarse.shape == fine.shape:
        return float(np.mean(np.abs(coarse - fine)))
    ratio = fine.shape[0] // coarse.shape[0]
    fine_coarsened = block_average(fine, ratio)
    return float(np.mean(np.abs(coarse - fine_coarsened)))


def main() -> None:
    paths = {
        200: ROOT / "experiments" / "week8" / "report1_2d_config12_fill"
                  / "runs" / "lw12-n200-cpu-double-strict-hllc" / "grid.bin",
        400: ROOT / "experiments" / "week8" / "report1_2d_config12_fill"
                  / "runs" / "lw12-n400-cpu-double-strict-hllc" / "grid.bin",
        800: ROOT / "experiments" / "week8" / "report1_2d_config12_fill"
                  / "reference" / "runs"
                  / "lw12-n800-cpu-double-strict-hllc-reference"
                  / "reference_800.bin",
        1600: ROOT / "experiments" / "add_experiment" / "lw12_1600_reference"
                   / "runs" / "lw12-n1600-double-gpu-hllc"
                   / "lw12_n1600_double_gpu_hllc.bin",
    }

    fields = {N: primitives(read_binary(p)[1]) for N, p in paths.items()}

    pairs = [(200, 400), (400, 800), (800, 1600)]
    var_names = ["rho", "u", "v", "p"]
    diffs = {v: [] for v in var_names}
    for nc, nf in pairs:
        coarse = fields[nc]
        fine = fields[nf]
        for vi, vn in enumerate(var_names):
            diffs[vn].append(l1_diff(coarse[vi], fine[vi]))

    fig, ax = plt.subplots(figsize=(7.8, 4.4), constrained_layout=True)
    x_pos = np.arange(len(pairs))
    labels = [f"{nc} vs {nf}" for nc, nf in pairs]
    palette = ["#1F4E79", "#E76F51", "#2A9D8F", "#9B2226"]
    for vn, color in zip(var_names, palette):
        y = diffs[vn]
        # observed order between last two pairs
        if y[-2] > 0 and y[-1] > 0:
            p_obs = float(np.log2(y[-2] / y[-1]))
        else:
            p_obs = float("nan")
        ax.plot(x_pos, y, marker="o", lw=1.5, color=color,
                label=f"{vn}, p={p_obs:.2f}")

    ax.set_yscale("log")
    ax.set_xticks(x_pos, labels=labels)
    ax.set_ylabel(r"$L_1$ difference")
    ax.set_title("LW12 fp64 self-convergence against finer grids")
    ax.legend(frameon=False, ncol=2)
    ax.grid(True, which="both", lw=0.4, alpha=0.35)

    save_pair(fig, "appendix_lw12_self_convergence", str(OUT))
    plt.close(fig)
    print(f"wrote {OUT}/appendix_lw12_self_convergence.{{pdf,png}}")
    for vn in var_names:
        print(f"  {vn}: {diffs[vn]}")


if __name__ == "__main__":
    main()
