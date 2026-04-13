"""
Verificarlo MCA Analysis for HRSC 1D Euler Solver

Reads Monte Carlo Arithmetic samples produced by verificarlo_run.sh,
computes significant digits for each grid point and variable, and
generates diagnostic plots.

Usage:
    python scripts/verificarlo_analysis.py                  # all tests
    python scripts/verificarlo_analysis.py --test sod       # single test
    python scripts/verificarlo_analysis.py --precision 24   # annotate as float32 run

Output (in docs/verificarlo/):
    - Per-test significant-digit heatmaps
    - Per-test profile overlay (30 MCA runs + mean + IEEE reference)
    - Combined summary figure
    - CSV with per-cell significant digits
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

# ── Toro test metadata (must match verify_toro.py) ───────────────────────────

TESTS = {
    "sod": {
        "title": "Test 1: Sod Shock Tube",
        "t_end": 0.25, "x0": 0.5, "gamma": 1.4,
        "rhoL": 1.0,   "uL": 0.0,   "pL": 1.0,
        "rhoR": 0.125, "uR": 0.0,   "pR": 0.1,
    },
    "toro2": {
        "title": "Test 2: 123 Problem",
        "t_end": 0.15, "x0": 0.5, "gamma": 1.4,
        "rhoL": 1.0,  "uL": -2.0,  "pL": 0.4,
        "rhoR": 1.0,  "uR":  2.0,  "pR": 0.4,
    },
    "toro3": {
        "title": "Test 3: Blast Wave",
        "t_end": 0.012, "x0": 0.5, "gamma": 1.4,
        "rhoL": 1.0,  "uL": 0.0,  "pL": 1000.0,
        "rhoR": 1.0,  "uR": 0.0,  "pR": 0.01,
    },
    "toro4": {
        "title": "Test 4: Lax Problem",
        "t_end": 0.035, "x0": 0.5, "gamma": 1.4,
        "rhoL": 0.445,  "uL": 0.698,  "pL": 3.528,
        "rhoR": 0.5,    "uR": 0.0,    "pR": 0.571,
    },
    "toro5": {
        "title": "Test 5: Slow Contact",
        "t_end": 0.035, "x0": 0.5, "gamma": 1.4,
        "rhoL": 5.99924,  "uL": 19.5975,  "pL": 460.894,
        "rhoR": 5.99242,  "uR": -6.19633, "pR": 46.0950,
    },
}

VAR_NAMES = ["x", "rho", "u", "v", "p"]
VAR_LABELS = {
    "rho": r"Density $\rho$",
    "u":   r"Velocity $u$",
    "v":   r"Velocity $v$",
    "p":   r"Pressure $p$",
}
# Columns of interest (skip x=0, skip v=3 which is always 0 in 1D)
ANALYSIS_COLS = {"rho": 1, "u": 2, "p": 4}


# ── I/O ──────────────────────────────────────────────────────────────────────

def load_runs(test_dir: Path):
    """Load all MCA sample files from a test directory.

    Returns:
        runs: ndarray of shape (n_samples, n_cells, 5)
        ref:  ndarray of shape (n_cells, 5) or None  (IEEE reference)
    """
    run_files = sorted(test_dir.glob("run_*.txt"))
    if not run_files:
        return None, None

    runs = []
    for f in run_files:
        try:
            data = np.loadtxt(f)
            runs.append(data)
        except Exception as e:
            print(f"  Warning: skipping {f.name}: {e}")

    runs = np.array(runs)  # (n_samples, n_cells, 5)

    ref_file = test_dir / "reference_ieee.txt"
    ref = np.loadtxt(ref_file) if ref_file.exists() else None

    return runs, ref


# ── Significant digits computation ───────────────────────────────────────────

def significant_digits(samples, reference=None):
    """Compute significant decimal digits from MCA samples.

    Uses the Verificarlo standard formula:
        s = -log10( |std(X) / mean(X)| )

    When a reference value is available, also computes:
        s_ref = -log10( |std(X) / reference| )

    Args:
        samples: (n_samples, n_cells) array
        reference: (n_cells,) array or None

    Returns:
        sig: (n_cells,) significant digits relative to mean
        sig_ref: (n_cells,) significant digits relative to reference, or None
    """
    mean = np.mean(samples, axis=0)
    std = np.std(samples, axis=0, ddof=1)  # unbiased estimator

    # Avoid division by zero: where mean==0, use absolute std
    with np.errstate(divide="ignore", invalid="ignore"):
        # Relative significant digits (self-referential)
        ratio = np.abs(std / mean)
        sig = -np.log10(ratio)
        sig = np.where(np.isfinite(sig), sig, np.nan)

    sig_ref = None
    if reference is not None:
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio_ref = np.abs(std / reference)
            sig_ref = -np.log10(ratio_ref)
            sig_ref = np.where(np.isfinite(sig_ref), sig_ref, np.nan)

    return sig, sig_ref


def compute_all_sigdigits(runs, ref=None):
    """Compute significant digits for all analysis variables.

    Returns dict: var_name -> {"sig": array, "sig_ref": array_or_None,
                               "mean": array, "std": array, "min": float, "max": float}
    """
    result = {}
    for var_name, col in ANALYSIS_COLS.items():
        samples = runs[:, :, col]
        ref_col = ref[:, col] if ref is not None else None
        sig, sig_ref = significant_digits(samples, ref_col)
        result[var_name] = {
            "sig": sig,
            "sig_ref": sig_ref,
            "mean": np.mean(samples, axis=0),
            "std": np.std(samples, axis=0, ddof=1),
            "min_sig": np.nanmin(sig),
            "max_sig": np.nanmax(sig),
        }
    return result


# ── Plotting ─────────────────────────────────────────────────────────────────

def plot_sigdigit_heatmap(x, sigdigits, test_cfg, out_path):
    """Heatmap: x-position vs variable, colored by significant digits."""
    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
    fig.suptitle(
        f"Significant Digits — {test_cfg['title']}\n"
        f"(Verificarlo MCA, {len(x)} cells)",
        fontsize=13, fontweight="bold",
    )

    for ax, (var_name, info) in zip(axes, sigdigits.items()):
        sig = info["sig"]
        # Clamp display range to [0, 16]; NaN (zero std) = perfect precision
        sig_clamped = np.clip(np.nan_to_num(sig, nan=16.0), 0, 16)

        # Bar-style heatmap
        colors = plt.cm.RdYlGn(sig_clamped / 16.0)
        ax.bar(x, sig_clamped, width=x[1] - x[0], color=colors, edgecolor="none")
        ax.set_ylabel(f"sig. digits\n({VAR_LABELS[var_name]})", fontsize=9)
        ax.set_ylim(0, 17)
        ax.axhline(y=7, color="orange", ls="--", lw=0.8, alpha=0.7, label="float32 limit")
        ax.axhline(y=15, color="blue", ls="--", lw=0.8, alpha=0.7, label="float64 limit")
        ax.legend(fontsize=7, loc="lower right")
        ax.grid(True, alpha=0.2)

        # Annotate min
        min_idx = np.nanargmin(sig)
        ax.annotate(
            f"min={sig[min_idx]:.1f}",
            xy=(x[min_idx], sig_clamped[min_idx]),
            xytext=(x[min_idx], sig_clamped[min_idx] + 2),
            fontsize=7, color="red", ha="center",
            arrowprops=dict(arrowstyle="->", color="red", lw=0.8),
        )

    axes[-1].set_xlabel("x")
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig(str(out_path), dpi=150)
    plt.close()


def plot_mca_overlay(x, runs, ref, sigdigits, test_cfg, out_path):
    """Overlay all MCA runs for each variable, plus mean and IEEE reference."""
    fig, axes = plt.subplots(3, 2, figsize=(14, 10))
    fig.suptitle(
        f"MCA Sample Overlay — {test_cfg['title']}\n"
        f"({runs.shape[0]} samples)",
        fontsize=13, fontweight="bold",
    )

    for row, (var_name, col) in enumerate(ANALYSIS_COLS.items()):
        ax_val = axes[row, 0]  # value overlay
        ax_sig = axes[row, 1]  # significant digits profile

        samples = runs[:, :, col]

        # Left panel: value overlay
        for k in range(min(runs.shape[0], 30)):
            ax_val.plot(x, samples[k], color="gray", alpha=0.15, lw=0.5)

        mean = sigdigits[var_name]["mean"]
        ax_val.plot(x, mean, "b-", lw=1.2, label="MCA mean")
        if ref is not None:
            ax_val.plot(x, ref[:, col], "r--", lw=1.0, label="IEEE ref")
        ax_val.set_ylabel(VAR_LABELS[var_name], fontsize=9)
        ax_val.legend(fontsize=7, loc="best")
        ax_val.grid(True, alpha=0.2)

        # Right panel: significant digits
        sig = sigdigits[var_name]["sig"]
        sig_plot = np.clip(np.nan_to_num(sig, nan=16.0), 0, 16)
        ax_sig.fill_between(x, 0, sig_plot, alpha=0.4, color="green")
        ax_sig.plot(x, sig_plot, "g-", lw=0.8)
        ax_sig.axhline(y=7, color="orange", ls="--", lw=0.8, alpha=0.7)
        ax_sig.axhline(y=15, color="blue", ls="--", lw=0.8, alpha=0.7)
        ax_sig.set_ylabel("sig. digits", fontsize=9)
        ax_sig.set_ylim(0, 17)
        ax_sig.grid(True, alpha=0.2)

    axes[0, 0].set_title("MCA samples + mean", fontsize=10)
    axes[0, 1].set_title("Significant digits", fontsize=10)
    axes[-1, 0].set_xlabel("x")
    axes[-1, 1].set_xlabel("x")

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig(str(out_path), dpi=150)
    plt.close()


def plot_summary(all_results, out_path):
    """Combined summary: min significant digits per test per variable."""
    test_names = list(all_results.keys())
    var_names = list(ANALYSIS_COLS.keys())
    n_tests = len(test_names)
    n_vars = len(var_names)

    # Build matrix: (n_tests, n_vars) = min significant digits
    matrix = np.zeros((n_tests, n_vars))
    for i, tname in enumerate(test_names):
        for j, vname in enumerate(var_names):
            matrix[i, j] = all_results[tname]["sigdigits"][vname]["min_sig"]

    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(matrix, cmap="RdYlGn", aspect="auto",
                   vmin=0, vmax=16)

    ax.set_xticks(range(n_vars))
    ax.set_xticklabels([VAR_LABELS[v] for v in var_names], fontsize=10)
    ax.set_yticks(range(n_tests))
    ax.set_yticklabels([TESTS[t]["title"] for t in test_names], fontsize=9)

    # Annotate cells
    for i in range(n_tests):
        for j in range(n_vars):
            val = matrix[i, j]
            color = "white" if val < 5 else "black"
            ax.text(j, i, f"{val:.1f}", ha="center", va="center",
                    fontsize=11, fontweight="bold", color=color)

    plt.colorbar(im, ax=ax, label="Min significant digits", shrink=0.8)
    ax.set_title("Verificarlo MCA: Minimum Significant Digits\n"
                 "(lower = more numerically sensitive)",
                 fontsize=12, fontweight="bold")

    plt.tight_layout()
    plt.savefig(str(out_path), dpi=150)
    plt.close()


def plot_comparison_double_vs_float(all_results_d, all_results_f, out_path):
    """If both double and float runs exist, plot side-by-side comparison."""
    if all_results_f is None:
        return

    test_names = sorted(set(all_results_d.keys()) & set(all_results_f.keys()))
    if not test_names:
        return

    fig, axes = plt.subplots(len(test_names), 3, figsize=(14, 4 * len(test_names)),
                             squeeze=False)
    fig.suptitle("Significant Digits: double (53-bit) vs float (24-bit)",
                 fontsize=13, fontweight="bold")

    for row, tname in enumerate(test_names):
        for col, vname in enumerate(ANALYSIS_COLS.keys()):
            ax = axes[row, col]
            x = all_results_d[tname]["x"]
            sig_d = all_results_d[tname]["sigdigits"][vname]["sig"]
            sig_f = all_results_f[tname]["sigdigits"][vname]["sig"]

            sig_d = np.clip(np.nan_to_num(sig_d, nan=16), 0, 16)
            sig_f = np.clip(np.nan_to_num(sig_f, nan=16), 0, 16)

            ax.plot(x, sig_d, "b-", lw=1.0, alpha=0.8, label="double (p=53)")
            ax.plot(x, sig_f, "r-", lw=1.0, alpha=0.8, label="float (p=24)")
            ax.set_ylim(0, 17)
            ax.grid(True, alpha=0.2)

            if row == 0:
                ax.set_title(VAR_LABELS[vname], fontsize=10)
            if col == 0:
                ax.set_ylabel(f"{TESTS[tname]['title']}\nsig. digits", fontsize=8)
            if row == len(test_names) - 1:
                ax.set_xlabel("x")
            if row == 0 and col == 0:
                ax.legend(fontsize=7)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(str(out_path), dpi=150)
    plt.close()


# ── CSV export ───────────────────────────────────────────────────────────────

def export_csv(x, sigdigits, test_name, out_path):
    """Export per-cell significant digits to CSV."""
    header = "x"
    cols = [x]
    for var_name in ANALYSIS_COLS:
        sig = sigdigits[var_name]["sig"]
        mean = sigdigits[var_name]["mean"]
        std = sigdigits[var_name]["std"]
        header += f",{var_name}_mean,{var_name}_std,{var_name}_sigdigits"
        cols.extend([mean, std, sig])

    data = np.column_stack(cols)
    np.savetxt(str(out_path), data, delimiter=",", header=header, comments="",
               fmt="%.8e")


# ── Main ─────────────────────────────────────────────────────────────────────

def analyze_test(test_name, vfc_dir, doc_dir):
    """Analyze a single test. Returns result dict or None."""
    test_dir = vfc_dir / test_name
    if not test_dir.exists():
        print(f"  [SKIP] {test_name}: directory not found")
        return None

    runs, ref = load_runs(test_dir)
    if runs is None:
        print(f"  [SKIP] {test_name}: no run files found")
        return None

    n_samples = runs.shape[0]
    x = runs[0, :, 0]  # x coordinates (same for all runs)

    print(f"\n{'=' * 60}")
    print(f"  {TESTS[test_name]['title']}  ({n_samples} MCA samples)")
    print(f"{'=' * 60}")

    # Compute significant digits
    sigdigits = compute_all_sigdigits(runs, ref)

    # Print summary table
    print(f"  {'Variable':<12s} {'Min sig.d':>10s} {'Mean sig.d':>11s} {'Max sig.d':>10s}")
    print(f"  {'-' * 12} {'-' * 10} {'-' * 11} {'-' * 10}")
    for var_name, info in sigdigits.items():
        sig = info["sig"]
        print(f"  {var_name:<12s} {np.nanmin(sig):10.2f} {np.nanmean(sig):11.2f} {np.nanmax(sig):10.2f}")

    # Find most unstable cells
    print(f"\n  Most numerically sensitive cells:")
    for var_name, info in sigdigits.items():
        sig = info["sig"]
        worst_idx = np.nanargmin(sig)
        print(f"    {var_name}: cell {worst_idx} (x={x[worst_idx]:.4f}), "
              f"sig.digits={sig[worst_idx]:.2f}, "
              f"mean={info['mean'][worst_idx]:.6e}, "
              f"std={info['std'][worst_idx]:.6e}")

    # Generate plots
    cfg = TESTS[test_name]

    heatmap_path = doc_dir / f"vfc_{test_name}_heatmap.png"
    plot_sigdigit_heatmap(x, sigdigits, cfg, heatmap_path)
    print(f"\n  Saved: {heatmap_path.name}")

    overlay_path = doc_dir / f"vfc_{test_name}_overlay.png"
    plot_mca_overlay(x, runs, ref, sigdigits, cfg, overlay_path)
    print(f"  Saved: {overlay_path.name}")

    csv_path = doc_dir / f"vfc_{test_name}_sigdigits.csv"
    export_csv(x, sigdigits, test_name, csv_path)
    print(f"  Saved: {csv_path.name}")

    return {
        "x": x,
        "sigdigits": sigdigits,
        "n_samples": n_samples,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Verificarlo MCA samples for HRSC solver")
    parser.add_argument("--test", "-t", type=str, default=None,
                        help="Analyze only this test (e.g., sod)")
    parser.add_argument("--precision", "-p", type=int, default=53,
                        help="Annotate precision in output (53=double, 24=float)")
    parser.add_argument("--vfc-dir", type=str, default=None,
                        help="Override Verificarlo output directory")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    vfc_dir = Path(args.vfc_dir) if args.vfc_dir else root / "experiments" / "verificarlo" / "runs_p53_mca"
    doc_dir = root / "experiments" / "verificarlo" / "results"
    doc_dir.mkdir(parents=True, exist_ok=True)

    if not vfc_dir.exists():
        print(f"ERROR: Verificarlo output directory not found: {vfc_dir}")
        print("Run  bash scripts/verificarlo_run.sh  first.")
        sys.exit(1)

    test_names = [args.test] if args.test else list(TESTS.keys())

    print(f"Verificarlo MCA Analysis (precision annotation: {args.precision}-bit)")
    print(f"Data directory: {vfc_dir}")
    print(f"Output directory: {doc_dir}")

    all_results = {}
    for tname in test_names:
        if tname not in TESTS:
            print(f"  [SKIP] Unknown test: {tname}")
            continue
        result = analyze_test(tname, vfc_dir, doc_dir)
        if result is not None:
            all_results[tname] = result

    # Summary figure
    if len(all_results) > 1:
        summary_path = doc_dir / "vfc_summary.png"
        plot_summary(all_results, summary_path)
        print(f"\nSaved summary: {summary_path.name}")

    # Final summary table
    if all_results:
        print(f"\n{'=' * 70}")
        print(f"  Summary: Minimum Significant Digits per Test")
        print(f"{'=' * 70}")
        print(f"  {'Test':<30s} {'rho':>8s} {'u':>8s} {'p':>8s}")
        print(f"  {'-' * 30} {'-' * 8} {'-' * 8} {'-' * 8}")
        for tname, result in all_results.items():
            sd = result["sigdigits"]
            print(f"  {TESTS[tname]['title']:<30s} "
                  f"{sd['rho']['min_sig']:8.2f} "
                  f"{sd['u']['min_sig']:8.2f} "
                  f"{sd['p']['min_sig']:8.2f}")

    print(f"\nVerificarlo analysis complete.")


def analyze_branch_flips(branch_dir="output/branch_detection", n_cells=200):
    """Compare MCA samples to detect branch flips across FP perturbations."""
    import glob

    sample_files = sorted(glob.glob(f"{branch_dir}/sample_*.txt"))
    if not sample_files:
        print(f"No samples found in {branch_dir}/")
        return

    print(f"\n=== Unstable Branch Detection ({len(sample_files)} samples) ===")

    # Parse each sample: columns are x, rho, u, v, p
    all_data = []
    for sf in sample_files:
        data = np.loadtxt(sf)
        all_data.append(data)

    all_data = np.array(all_data)  # shape: (n_samples, n_cells, 5)
    n_samples = all_data.shape[0]

    # For each cell, compute std deviation across samples
    rho_std = np.std(all_data[:, :, 1], axis=0)  # rho is column 1
    u_std   = np.std(all_data[:, :, 2], axis=0)  # u is column 2
    p_std   = np.std(all_data[:, :, 4], axis=0)  # p is column 4

    # Flag cells where variability is high (potential branch flips)
    rho_mean = np.mean(np.abs(all_data[:, :, 1]), axis=0)
    relative_var = np.where(rho_mean > 1e-10, rho_std / rho_mean, 0.0)

    # Top 10 most variable cells
    top_cells = np.argsort(relative_var)[-10:][::-1]

    print("\nTop 10 cells with highest relative density variation (40-bit VPREC):")
    print(f"{'Cell':>6}  {'x':>10}  {'rel_std_rho':>12}  {'std_u':>12}  {'std_p':>12}")
    x_coords = all_data[0, :, 0]
    for c in top_cells:
        print(f"{c:6d}  {x_coords[c]:10.5f}  {relative_var[c]:12.4e}"
              f"  {u_std[c]:12.4e}  {p_std[c]:12.4e}")

    # Save summary
    summary_file = f"{branch_dir}/branch_flip_summary.txt"
    with open(summary_file, 'w') as f:
        f.write("# Unstable branch detection summary (VPREC 40-bit)\n")
        f.write(f"# {n_samples} MCA samples, {n_cells} cells\n")
        f.write(f"# cell  x  rel_std_rho  std_u  std_p\n")
        for c in range(len(x_coords)):
            f.write(f"{c}  {x_coords[c]:.6f}  {relative_var[c]:.6e}"
                    f"  {u_std[c]:.6e}  {p_std[c]:.6e}\n")

    print(f"\nFull summary saved to {summary_file}")


if __name__ == "__main__":
    main()
