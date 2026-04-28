"""
Combined Verificarlo MCA + Exact Solution Error Analysis

Links floating-point stability (MCA std) with discretisation error (|numerical - exact|)
at each grid cell, identifying where floating-point noise becomes the precision bottleneck.

Usage:
    python scripts/verificarlo/verificarlo_vs_exact.py                # all tests
    python scripts/verificarlo/verificarlo_vs_exact.py --test sod     # single test

Output (in docs/verificarlo/):
    - vfc_{test}_error_budget.png   — per-cell discretisation vs FP error
    - vfc_{test}_noise_ratio.png    — noise-to-error ratio profile
    - vfc_error_budget_summary.png  — combined summary across all tests
    - vfc_{test}_error_budget.csv   — per-cell numerical data
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ── Reuse exact Riemann solver from verify_toro.py ───────────────────────────
# (imported via sys.path to avoid code duplication)

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "regression"))  # verify_toro lives in regression/
from verify_toro import exact_riemann, TESTS

# Variable columns in the output: x=0, rho=1, u=2, v=3, p=4
ANALYSIS_VARS = {"rho": 1, "u": 2, "p": 4}
VAR_LABELS = {
    "rho": r"$\rho$ (density)",
    "u":   r"$u$ (velocity)",
    "p":   r"$p$ (pressure)",
}


# ── I/O ──────────────────────────────────────────────────────────────────────

def load_mca_runs(test_dir: Path):
    """Load all MCA run files and the IEEE reference."""
    run_files = sorted(test_dir.glob("run_*.txt"))
    if not run_files:
        return None, None
    runs = np.array([np.loadtxt(f) for f in run_files])
    ref_path = test_dir / "reference_ieee.txt"
    ref = np.loadtxt(ref_path) if ref_path.exists() else None
    return runs, ref


# ── Core analysis ────────────────────────────────────────────────────────────

def compute_error_budget(runs, ref, cfg):
    """For each cell and variable, compute discretisation error and FP noise.

    Returns dict: var_name -> {
        disc_error:  |mean_numerical - exact|        (discretisation error)
        fp_noise:    std of MCA samples              (floating-point noise)
        ratio:       fp_noise / disc_error            (noise-to-error ratio)
        exact:       exact solution values
        mean:        MCA mean
    }
    """
    x = runs[0, :, 0]
    gamma = cfg["gamma"]
    rho_ex, u_ex, p_ex, _ = exact_riemann(
        x, cfg["t_end"], gamma, cfg["x0"],
        cfg["rhoL"], cfg["uL"], cfg["pL"],
        cfg["rhoR"], cfg["uR"], cfg["pR"],
    )
    exact = {"rho": rho_ex, "u": u_ex, "p": p_ex}

    result = {}
    for var_name, col in ANALYSIS_VARS.items():
        samples = runs[:, :, col]       # (n_samples, n_cells)
        mean = np.mean(samples, axis=0)
        std = np.std(samples, axis=0, ddof=1)

        disc_err = np.abs(mean - exact[var_name])

        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = std / disc_err
            ratio = np.where(np.isfinite(ratio), ratio, np.nan)

        result[var_name] = {
            "disc_error": disc_err,
            "fp_noise": std,
            "ratio": ratio,
            "exact": exact[var_name],
            "mean": mean,
        }

    return x, result


# ── Plotting ─────────────────────────────────────────────────────────────────

def plot_error_budget(x, budget, cfg, out_path):
    """Per-cell comparison: discretisation error vs FP noise for each variable."""
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle(
        f"Error Budget — {cfg['title']}\n"
        f"Discretisation error vs floating-point noise (200 cells, double)",
        fontsize=12, fontweight="bold",
    )

    for ax, (var_name, info) in zip(axes, budget.items()):
        disc = info["disc_error"]
        fp = info["fp_noise"]

        # Mask zeros for log plot
        disc_plot = np.where(disc > 0, disc, np.nan)
        fp_plot = np.where(fp > 0, fp, np.nan)

        ax.semilogy(x, disc_plot, "b-", lw=1.0, alpha=0.9,
                     label="Discretisation error  |mean - exact|")
        ax.semilogy(x, fp_plot, "r-", lw=1.0, alpha=0.9,
                     label=r"FP noise  $\sigma_{\mathrm{MCA}}$")

        # Shade region where FP noise > 1% of discretisation error
        with np.errstate(invalid="ignore"):
            contested = (fp > 0.01 * disc) & np.isfinite(disc_plot)
        ax.fill_between(x, ax.get_ylim()[0], ax.get_ylim()[1],
                         where=contested, alpha=0.08, color="red")

        ax.set_ylabel(VAR_LABELS[var_name], fontsize=9)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True, alpha=0.2, which="both")
        ax.yaxis.set_minor_locator(ticker.LogLocator(subs="auto", numticks=20))

        # Annotate the crossover point (if any) where fp_noise > disc_error
        with np.errstate(invalid="ignore"):
            crossover = np.where((fp > disc) & (disc > 0))[0]
        if len(crossover) > 0:
            ci = crossover[len(crossover) // 2]
            ax.axvline(x=x[ci], color="red", ls=":", lw=0.8, alpha=0.6)
            ax.annotate(
                f"FP > disc\nx={x[ci]:.2f}",
                xy=(x[ci], fp[ci]), fontsize=7, color="red",
                xytext=(15, 10), textcoords="offset points",
                arrowprops=dict(arrowstyle="->", color="red", lw=0.7),
            )

    axes[-1].set_xlabel("x")
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig(str(out_path), dpi=150)
    plt.close()


def plot_noise_ratio(x, budget, cfg, out_path):
    """Noise-to-error ratio: sigma_MCA / |mean - exact|.

    ratio << 1: discretisation-limited (scheme accuracy is the bottleneck)
    ratio ~ 1:  floating-point noise competes with discretisation error
    ratio >> 1: floating-point-limited (precision is the bottleneck)
    """
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    fig.suptitle(
        f"Noise-to-Error Ratio — {cfg['title']}\n"
        r"$\sigma_{\mathrm{MCA}} \;/\; |\bar{x} - x_{\mathrm{exact}}|$"
        "   (>1 = FP-limited, <1 = discretisation-limited)",
        fontsize=11, fontweight="bold",
    )

    for ax, (var_name, info) in zip(axes, budget.items()):
        ratio = info["ratio"]
        ratio_plot = np.clip(np.nan_to_num(ratio, nan=1e-20), 1e-20, 1e20)

        colors = np.where(ratio_plot >= 1.0, "red", "steelblue")
        ax.bar(x, np.log10(ratio_plot), width=x[1] - x[0],
               color=colors, edgecolor="none", alpha=0.7)

        ax.axhline(y=0, color="black", lw=1.0)  # ratio = 1 line
        ax.axhline(y=-2, color="green", ls="--", lw=0.7, alpha=0.6,
                    label="ratio = 0.01")
        ax.set_ylabel(f"log10(ratio)\n{VAR_LABELS[var_name]}", fontsize=8)
        ax.set_ylim(-18, 5)
        ax.grid(True, alpha=0.2)

        # Count cells where FP-limited
        n_fp_limited = np.sum(ratio_plot >= 1.0)
        n_total = len(ratio_plot)
        ax.text(0.02, 0.95,
                f"FP-limited: {n_fp_limited}/{n_total} cells",
                transform=ax.transAxes, fontsize=8, va="top",
                color="red" if n_fp_limited > 0 else "green",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))

    axes[0].legend(fontsize=7, loc="lower right")
    axes[-1].set_xlabel("x")
    plt.tight_layout(rect=[0, 0, 1, 0.92])
    plt.savefig(str(out_path), dpi=150)
    plt.close()


def plot_combined_summary(all_results, out_path):
    """Summary: for each test and variable, show the fraction of cells where
    FP noise exceeds 1% of discretisation error, and the median ratio."""
    test_names = list(all_results.keys())
    var_names = list(ANALYSIS_VARS.keys())
    n_tests = len(test_names)
    n_vars = len(var_names)

    # Median log10(ratio) matrix
    median_matrix = np.zeros((n_tests, n_vars))
    # Fraction of cells where ratio > 0.01
    frac_matrix = np.zeros((n_tests, n_vars))

    for i, tname in enumerate(test_names):
        budget = all_results[tname]["budget"]
        for j, vname in enumerate(var_names):
            ratio = budget[vname]["ratio"]
            valid = ratio[np.isfinite(ratio) & (ratio > 0)]
            if len(valid) > 0:
                median_matrix[i, j] = np.median(np.log10(valid))
                frac_matrix[i, j] = np.sum(valid > 0.01) / len(ratio) * 100
            else:
                median_matrix[i, j] = -16
                frac_matrix[i, j] = 0

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Error Budget Summary: FP Noise vs Discretisation Error",
                 fontsize=13, fontweight="bold")

    # Left: median log10(ratio)
    im1 = ax1.imshow(median_matrix, cmap="RdYlGn_r", aspect="auto",
                      vmin=-16, vmax=2)
    ax1.set_xticks(range(n_vars))
    ax1.set_xticklabels([VAR_LABELS[v] for v in var_names], fontsize=9)
    ax1.set_yticks(range(n_tests))
    ax1.set_yticklabels([TESTS[t]["title"] for t in test_names], fontsize=9)
    for i in range(n_tests):
        for j in range(n_vars):
            val = median_matrix[i, j]
            color = "white" if val > -5 else "black"
            ax1.text(j, i, f"{val:.1f}", ha="center", va="center",
                     fontsize=10, fontweight="bold", color=color)
    plt.colorbar(im1, ax=ax1, label=r"Median $\log_{10}$( ratio )", shrink=0.8)
    ax1.set_title(r"Median $\log_{10}(\sigma_\mathrm{MCA} / |\bar{x}-x_\mathrm{exact}|)$",
                  fontsize=10)

    # Right: fraction of cells where ratio > 1%
    im2 = ax2.imshow(frac_matrix, cmap="Reds", aspect="auto",
                      vmin=0, vmax=100)
    ax2.set_xticks(range(n_vars))
    ax2.set_xticklabels([VAR_LABELS[v] for v in var_names], fontsize=9)
    ax2.set_yticks(range(n_tests))
    ax2.set_yticklabels([TESTS[t]["title"] for t in test_names], fontsize=9)
    for i in range(n_tests):
        for j in range(n_vars):
            val = frac_matrix[i, j]
            color = "white" if val > 40 else "black"
            ax2.text(j, i, f"{val:.0f}%", ha="center", va="center",
                     fontsize=10, fontweight="bold", color=color)
    plt.colorbar(im2, ax=ax2, label="% cells", shrink=0.8)
    ax2.set_title(r"% cells where $\sigma_\mathrm{MCA} > 1\%$ of disc. error",
                  fontsize=10)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig(str(out_path), dpi=150)
    plt.close()


# ── CSV export ───────────────────────────────────────────────────────────────

def export_csv(x, budget, out_path):
    """Export per-cell error budget to CSV."""
    header = "x"
    cols = [x]
    for var_name in ANALYSIS_VARS:
        info = budget[var_name]
        header += (f",{var_name}_exact,{var_name}_mean,"
                   f"{var_name}_disc_error,{var_name}_fp_noise,{var_name}_ratio")
        cols.extend([info["exact"], info["mean"],
                     info["disc_error"], info["fp_noise"],
                     np.nan_to_num(info["ratio"], nan=-1)])
    data = np.column_stack(cols)
    np.savetxt(str(out_path), data, delimiter=",", header=header,
               comments="", fmt="%.8e")


# ── Main ─────────────────────────────────────────────────────────────────────

def analyze_test(test_name, vfc_dir, doc_dir):
    """Analyze one test: compute error budget, generate plots."""
    test_dir = vfc_dir / test_name
    if not test_dir.exists():
        print(f"  [SKIP] {test_name}: directory not found")
        return None

    runs, ref = load_mca_runs(test_dir)
    if runs is None:
        print(f"  [SKIP] {test_name}: no MCA run files found")
        return None

    cfg = TESTS[test_name]
    n_samples = runs.shape[0]
    print(f"\n{'=' * 65}")
    print(f"  {cfg['title']}  ({n_samples} MCA samples)")
    print(f"{'=' * 65}")

    x, budget = compute_error_budget(runs, ref, cfg)

    # Per-variable summary
    print(f"  {'Variable':<8s} {'Disc. L1':>12s} {'FP noise L1':>12s} "
          f"{'Median ratio':>13s} {'FP>disc cells':>14s}")
    print(f"  {'-'*8} {'-'*12} {'-'*12} {'-'*13} {'-'*14}")
    dx = x[1] - x[0]
    for var_name, info in budget.items():
        disc_L1 = np.sum(info["disc_error"]) * dx
        fp_L1 = np.sum(info["fp_noise"]) * dx
        ratio = info["ratio"]
        valid_ratio = ratio[np.isfinite(ratio) & (ratio > 0)]
        med = np.median(np.log10(valid_ratio)) if len(valid_ratio) > 0 else float("nan")
        n_fp = np.sum(valid_ratio >= 1.0) if len(valid_ratio) > 0 else 0
        print(f"  {var_name:<8s} {disc_L1:12.4e} {fp_L1:12.4e} "
              f"  10^{med:+.1f}      {n_fp:>4d}/{len(ratio)}")

    # Generate plots
    budget_path = doc_dir / f"vfc_{test_name}_error_budget.png"
    plot_error_budget(x, budget, cfg, budget_path)
    print(f"\n  Saved: {budget_path.name}")

    ratio_path = doc_dir / f"vfc_{test_name}_noise_ratio.png"
    plot_noise_ratio(x, budget, cfg, ratio_path)
    print(f"  Saved: {ratio_path.name}")

    csv_path = doc_dir / f"vfc_{test_name}_error_budget.csv"
    export_csv(x, budget, csv_path)
    print(f"  Saved: {csv_path.name}")

    return {"x": x, "budget": budget, "n_samples": n_samples}


def main():
    parser = argparse.ArgumentParser(
        description="Combined Verificarlo MCA + exact solution error analysis")
    parser.add_argument("--test", "-t", type=str, default=None,
                        help="Analyse only this test (e.g., sod)")
    parser.add_argument("--vfc-dir", type=str, default=None,
                        help="Override Verificarlo output directory")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    vfc_dir = Path(args.vfc_dir) if args.vfc_dir else root / "experiments" / "verificarlo" / "runs_p53_mca"
    doc_dir = root / "experiments" / "verificarlo" / "results"
    doc_dir.mkdir(parents=True, exist_ok=True)

    if not vfc_dir.exists():
        print(f"ERROR: Verificarlo output not found: {vfc_dir}")
        print("Run  bash scripts/verificarlo/verificarlo_run.sh  first.")
        sys.exit(1)

    test_names = [args.test] if args.test else list(TESTS.keys())

    print("Combined Error Budget Analysis: FP noise vs discretisation error")
    print(f"Data:   {vfc_dir}")
    print(f"Output: {doc_dir}")

    all_results = {}
    for tname in test_names:
        if tname not in TESTS:
            print(f"  [SKIP] Unknown test: {tname}")
            continue
        result = analyze_test(tname, vfc_dir, doc_dir)
        if result is not None:
            all_results[tname] = result

    if len(all_results) > 1:
        summary_path = doc_dir / "vfc_error_budget_summary.png"
        plot_combined_summary(all_results, summary_path)
        print(f"\nSaved summary: {summary_path.name}")

    # Final table
    if all_results:
        print(f"\n{'=' * 75}")
        print(f"  Summary: Median noise-to-error ratio (log10)")
        print(f"{'=' * 75}")
        print(f"  {'Test':<30s} {'rho':>10s} {'u':>10s} {'p':>10s}")
        print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*10}")
        for tname, res in all_results.items():
            vals = []
            for vname in ANALYSIS_VARS:
                r = res["budget"][vname]["ratio"]
                v = r[np.isfinite(r) & (r > 0)]
                med = np.median(np.log10(v)) if len(v) > 0 else float("nan")
                vals.append(med)
            print(f"  {TESTS[tname]['title']:<30s} "
                  f"{vals[0]:10.1f} {vals[1]:10.1f} {vals[2]:10.1f}")

    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()
