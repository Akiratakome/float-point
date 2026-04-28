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
        with np.errstate(divide="ignore", invalid="ignore"):
            sig = -np.log10(np.abs(std / mean))
            sig = np.where(np.isfinite(sig), sig, np.nan)
        out[var_name] = {"mean": mean, "std": std, "sig": sig}
    return out


def _plot_test(
    out_dir: Path,
    test: str,
    x: np.ndarray,
    real_stats: dict,
    vprec_stats: dict,
) -> Path:
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    fig.suptitle(f"Real float vs VPREC p24: {test}", fontsize=12, fontweight="bold")

    for ax, var in zip(axes, VARS.keys()):
        real_sig = np.clip(real_stats[var]["sig"], 0, 16)
        vprec_sig = np.clip(vprec_stats[var]["sig"], 0, 16)
        ax.plot(x, real_sig, label="real_float", lw=1.1)
        ax.plot(x, vprec_sig, label="vprec_p24", lw=1.1)
        ax.set_ylabel(f"{var} sig.d")
        ax.set_ylim(0, 17)
        ax.grid(alpha=0.25)
        ax.legend(loc="best", fontsize=8)

    axes[-1].set_xlabel("x")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out_path = out_dir / f"{test}_real_vs_vprec_sigdigits.png"
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
    args = parser.parse_args()

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
        if not np.allclose(x_real, x_vprec, rtol=0.0, atol=1e-12):
            raise ValueError(f"x-grid mismatch for test '{test}' between modes.")

        real_stats = _compute_stats(real_runs)
        vprec_stats = _compute_stats(vprec_runs)
        for var in VARS:
            if np.all(vprec_stats[var]["std"] == 0.0):
                print(
                    f"WARNING: {test}:{var} has zero VPREC sample variance; "
                    "sig-digits are undefined for deterministic traces.",
                    file=sys.stderr,
                )
        plot_path = _plot_test(args.out_dir, test, x_real, real_stats, vprec_stats)

        summary[test] = {
            "real_float": _summary_entry(real_stats),
            "vprec_p24": _summary_entry(vprec_stats),
            "n_samples_real": int(real_runs.shape[0]),
            "n_samples_vprec": int(vprec_runs.shape[0]),
            "plot_file": str(plot_path),
        }
        print(f"[ok] {test}: wrote {plot_path}")

    summary_path = args.out_dir / "real_vs_vprec_summary.json"
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
