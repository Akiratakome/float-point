#!/usr/bin/env python3
"""Compare real-float MCA runs against VPREC-p24 MCA runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

VARS = {"rho": 1, "u": 2, "p": 4}


def _load_mode_runs(mode_dir: Path, test: str) -> np.ndarray:
    test_dir = mode_dir / test
    if not test_dir.is_dir():
        raise FileNotFoundError(f"Missing test directory: {test_dir}")
    run_files = sorted(test_dir.glob("run_*.txt"))
    if not run_files:
        raise FileNotFoundError(f"No run_*.txt files found in: {test_dir}")

    runs = []
    expected_cells = None
    for file_path in run_files:
        data = np.loadtxt(file_path)
        if data.ndim != 2 or data.shape[1] < 5:
            raise ValueError(f"Invalid format in {file_path} (expected N x 5+ columns).")
        if expected_cells is None:
            expected_cells = data.shape[0]
        elif data.shape[0] != expected_cells:
            raise ValueError(
                f"Mismatched cell count in {file_path}: {data.shape[0]} vs {expected_cells}."
            )
        runs.append(data[:, :5])
    return np.array(runs)


def _compute_stats(runs: np.ndarray) -> dict:
    out = {}
    for var_name, col in VARS.items():
        samples = runs[:, :, col]
        mean = np.mean(samples, axis=0)
        std = np.std(samples, axis=0, ddof=1) if samples.shape[0] > 1 else np.zeros_like(mean)
        # True if every sample is bitwise identical for this cell — the actual
        # definition of "deterministic across MCA runs". Using this directly is
        # more robust than thresholding std, since np.std of identical doubles
        # still leaks ~1e-16 from mean-subtraction roundoff.
        if samples.shape[0] > 1:
            all_equal = np.all(samples == samples[0:1, :], axis=0)
        else:
            all_equal = np.ones_like(mean, dtype=bool)
        with np.errstate(divide="ignore", invalid="ignore"):
            sig = -np.log10(np.abs(std / mean))
            sig = np.where(np.isfinite(sig), sig, np.nan)
        out[var_name] = {"mean": mean, "std": std, "sig": sig, "all_equal": all_equal}
    return out


def _plot_test(
    out_dir: Path,
    test: str,
    x: np.ndarray,
    real_stats: dict,
    vprec_stats: dict,
    label_a: str = "real_float",
    label_b: str = "vprec_p24",
    out_stem: str = "real_vs_vprec",
) -> Path:
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    fig.suptitle(f"{label_a} vs {label_b}: {test}", fontsize=12, fontweight="bold")

    for ax, var in zip(axes, VARS.keys()):
        real_sig = real_stats[var]["sig"]
        vprec_sig = vprec_stats[var]["sig"]

        ax.plot(x, real_sig, label=label_a, lw=1.1, color="C0")

        if np.all(np.isnan(vprec_sig)):
            ax.text(
                0.5, 0.92,
                f"{label_b}: zero variance (deterministic backend)",
                transform=ax.transAxes, ha="center", va="top",
                color="C1", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="C1", alpha=0.85),
            )
        else:
            ax.plot(x, vprec_sig, label=label_b, lw=1.1, color="C1")

        finite_real = real_sig[np.isfinite(real_sig)]
        ymin = -2.0
        if finite_real.size:
            ymin = float(min(ymin, np.min(finite_real) - 0.5))
        ax.axhline(0.0, color="gray", ls=":", lw=0.5, alpha=0.6)
        ax.set_ylabel(f"{var} sig.d")
        ax.set_ylim(ymin, 17)
        ax.grid(alpha=0.25)
        ax.legend(loc="best", fontsize=8)

    axes[-1].set_xlabel("x")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out_path = out_dir / f"{test}_{out_stem}_sigdigits.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def _summary_entry(stats: dict) -> dict:
    summary = {}
    for var in VARS:
        sig = stats[var]["sig"]
        finite = sig[np.isfinite(sig)]
        if finite.size == 0:
            summary[var] = {"min_sig_digits": None, "median_sig_digits": None}
            continue
        summary[var] = {
            "min_sig_digits": float(np.min(finite)),
            "median_sig_digits": float(np.median(finite)),
        }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare per-cell MCA profiles between real-float and VPREC-p24 runs."
    )
    parser.add_argument("real_dir", type=Path, help="MCA run directory for real float mode.")
    parser.add_argument("vprec_dir", type=Path, help="MCA run directory for VPREC p24 mode.")
    parser.add_argument(
        "--tests",
        nargs="+",
        required=True,
        help="One or more test names (e.g. sod toro4).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("docs/week4/figures/real_float_vs_vprec"),
        help="Directory for plots + JSON summary.",
    )
    parser.add_argument("--label-a", default="real_float",
                        help="Legend/title label for the first directory (default: real_float).")
    parser.add_argument("--label-b", default="vprec_p24",
                        help="Legend/title label for the second directory (default: vprec_p24).")
    parser.add_argument("--out-stem", default=None,
                        help="Base filename stem for plots (default: real_vs_<label-b>).")
    args = parser.parse_args()
    out_stem = args.out_stem or f"real_vs_{args.label_b}"

    if not args.real_dir.is_dir():
        raise FileNotFoundError(f"real_dir not found: {args.real_dir}")
    if not args.vprec_dir.is_dir():
        raise FileNotFoundError(f"vprec_dir not found: {args.vprec_dir}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary = {}

    for test in args.tests:
        real_runs = _load_mode_runs(args.real_dir, test)
        vprec_runs = _load_mode_runs(args.vprec_dir, test)

        if real_runs.shape[1] != vprec_runs.shape[1]:
            raise ValueError(
                f"Cell count mismatch for test '{test}': "
                f"real={real_runs.shape[1]} vs vprec={vprec_runs.shape[1]}."
            )

        x_real = real_runs[0, :, 0]
        x_vprec = vprec_runs[0, :, 0]
        # Allow small differences due to different precision in x-coordinate computation
        if not np.allclose(x_real, x_vprec, rtol=1e-6, atol=1e-7):
            raise ValueError(f"x-grid mismatch for test '{test}' between modes.")

        real_stats = _compute_stats(real_runs)
        vprec_stats = _compute_stats(vprec_runs)
        for var in VARS:
            # VPREC backend is deterministic: mark cells where all MCA samples
            # are bitwise identical as NaN, so the plot can annotate determinism
            # rather than draw a misleading line at the np.std roundoff floor.
            v_sig = vprec_stats[var]["sig"]
            v_sig = np.where(vprec_stats[var]["all_equal"], np.nan, v_sig)
            v_sig = np.where(np.isfinite(v_sig), v_sig, np.nan)
            vprec_stats[var]["sig"] = v_sig

            # Keep real-float sig.d as-is, including negative values where
            # |mean|->0 (e.g. stationary contact velocity). Earlier code clipped
            # these to 0 which made the line vanish at the y-axis floor.
            r_sig = real_stats[var]["sig"]
            real_stats[var]["sig"] = np.where(np.isfinite(r_sig), r_sig, np.nan)

        plot_path = _plot_test(
            args.out_dir, test, x_real, real_stats, vprec_stats,
            label_a=args.label_a, label_b=args.label_b, out_stem=out_stem,
        )

        summary[test] = {
            args.label_a: _summary_entry(real_stats),
            args.label_b: _summary_entry(vprec_stats),
            "n_samples_real": int(real_runs.shape[0]),
            "n_samples_vprec": int(vprec_runs.shape[0]),
            "plot_file": str(plot_path),
        }
        print(f"[ok] {test}: wrote {plot_path}")

    summary_path = args.out_dir / f"{out_stem}_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"[ok] summary: {summary_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
