"""
Verificarlo HLLC vs Rusanov FP Sensitivity Comparison

Generates summary comparison plots from Verificarlo MCA data for both
flux schemes at p53 (double) and p24 (float32) precision levels.

Usage:
    python scripts/plot_vfc_hllc_vs_rusanov.py
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLOT_DIR = ROOT / "experiments" / "week4_rusanov" / "plots"

TESTS_4 = ["sod", "toro3", "toro4", "toro5"]  # tests with both HLLC and Rusanov
TESTS_5 = ["sod", "toro2", "toro3", "toro4", "toro5"]  # HLLC-only has toro2

TEST_TITLES = {
    "sod": "Sod", "toro2": "123 Problem",
    "toro3": "Blast Wave", "toro4": "Lax", "toro5": "Slow Contact",
}

ANALYSIS_COLS = {"rho": 1, "u": 2, "p": 4}
VAR_LABELS = {"rho": r"$\rho$", "u": r"$u$", "p": r"$p$"}


def load_runs(test_dir):
    """Load MCA samples from a test directory."""
    run_files = sorted(Path(test_dir).glob("run_*.txt"))
    if not run_files:
        return None
    runs = []
    for f in run_files:
        runs.append(np.loadtxt(f))
    return np.array(runs)


def compute_min_sigdigits(runs, col):
    """Compute minimum significant digits for a variable column."""
    samples = runs[:, :, col]
    mean = np.mean(samples, axis=0)
    std = np.std(samples, axis=0, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        sig = -np.log10(np.abs(std / mean))
        sig = np.where(np.isfinite(sig), sig, np.nan)
    return np.nanmin(sig), np.nanmean(sig)


def gather_results(base_dir, tests):
    """Gather min and mean sig digits for each test and variable."""
    results = {}
    for test in tests:
        test_dir = Path(base_dir) / test
        runs = load_runs(test_dir)
        if runs is None:
            continue
        results[test] = {}
        for vname, col in ANALYSIS_COLS.items():
            min_sd, mean_sd = compute_min_sigdigits(runs, col)
            results[test][vname] = {"min": min_sd, "mean": mean_sd}
    return results


def plot_p53_comparison():
    """Bar chart: HLLC vs Rusanov min significant digits at p53."""
    hllc_dir = ROOT / "experiments" / "week3_validation" / "verificarlo" / "runs_p53_mca"
    rus_dir  = ROOT / "experiments" / "verificarlo_docker" / "runs_p53_mca_rusanov"

    hllc = gather_results(hllc_dir, TESTS_4)
    rus  = gather_results(rus_dir, TESTS_4)

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.suptitle("FP Sensitivity: HLLC vs Rusanov at double precision (p=53)\n"
                 "Minimum significant digits across all cells (higher = more stable)",
                 fontsize=12, fontweight="bold")

    for idx, vname in enumerate(["rho", "u", "p"]):
        ax = axes[idx]
        tests = [t for t in TESTS_4 if t in hllc and t in rus]
        x = np.arange(len(tests))
        w = 0.35

        h_vals = [hllc[t][vname]["min"] for t in tests]
        r_vals = [rus[t][vname]["min"] for t in tests]

        ax.bar(x - w/2, h_vals, w, label="HLLC", color="steelblue")
        ax.bar(x + w/2, r_vals, w, label="Rusanov", color="indianred")
        ax.set_xticks(x)
        ax.set_xticklabels([TEST_TITLES[t] for t in tests], fontsize=9, rotation=15)
        ax.set_ylabel("Min significant digits")
        ax.set_title(VAR_LABELS[vname], fontsize=11)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.2, axis="y")
        ax.axhline(y=0, color="k", lw=0.5, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.9])
    out = PLOT_DIR / "vfc_hllc_vs_rusanov_p53.png"
    plt.savefig(str(out), dpi=150)
    plt.close()
    print(f"Saved: {out}")


def plot_p24_comparison():
    """Bar chart: HLLC vs Rusanov min significant digits at p24 (float32)."""
    hllc_dir = ROOT / "experiments" / "verificarlo_docker" / "runs_p24_mca"
    rus_dir  = ROOT / "experiments" / "verificarlo_docker" / "runs_p24_mca_rusanov"

    hllc = gather_results(hllc_dir, TESTS_4)
    rus  = gather_results(rus_dir, TESTS_4)

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.suptitle("FP Sensitivity: HLLC vs Rusanov at float32 precision (p=24)\n"
                 "Minimum significant digits across all cells (higher = more stable)",
                 fontsize=12, fontweight="bold")

    for idx, vname in enumerate(["rho", "u", "p"]):
        ax = axes[idx]
        tests = [t for t in TESTS_4 if t in hllc and t in rus]
        x = np.arange(len(tests))
        w = 0.35

        h_vals = [hllc[t][vname]["min"] for t in tests]
        r_vals = [rus[t][vname]["min"] for t in tests]

        ax.bar(x - w/2, h_vals, w, label="HLLC", color="steelblue")
        ax.bar(x + w/2, r_vals, w, label="Rusanov", color="indianred")
        ax.set_xticks(x)
        ax.set_xticklabels([TEST_TITLES[t] for t in tests], fontsize=9, rotation=15)
        ax.set_ylabel("Min significant digits")
        ax.set_title(VAR_LABELS[vname], fontsize=11)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.2, axis="y")
        ax.axhline(y=7, color="orange", ls="--", lw=0.8, alpha=0.5, label="float32 limit")
        ax.axhline(y=0, color="k", lw=0.5, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.9])
    out = PLOT_DIR / "vfc_hllc_vs_rusanov_p24.png"
    plt.savefig(str(out), dpi=150)
    plt.close()
    print(f"Saved: {out}")


def plot_precision_overview():
    """Combined 2x3 figure: p53 on top, p24 on bottom, rho/u/p columns."""
    hllc_p53 = gather_results(ROOT / "experiments" / "week3_validation" / "verificarlo" / "runs_p53_mca", TESTS_5)
    rus_p53  = gather_results(ROOT / "experiments" / "verificarlo_docker" / "runs_p53_mca_rusanov", TESTS_4)
    hllc_p24 = gather_results(ROOT / "experiments" / "verificarlo_docker" / "runs_p24_mca", TESTS_5)
    rus_p24  = gather_results(ROOT / "experiments" / "verificarlo_docker" / "runs_p24_mca_rusanov", TESTS_4)

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    fig.suptitle("Verificarlo MCA: HLLC vs Rusanov FP Sensitivity Overview\n"
                 "(min significant digits per variable, lower = more FP-sensitive)",
                 fontsize=13, fontweight="bold")

    for col, vname in enumerate(["rho", "u", "p"]):
        for row, (prec_label, hllc_data, rus_data, tests) in enumerate([
            ("double (p=53)", hllc_p53, rus_p53, TESTS_5),
            ("float32 (p=24)", hllc_p24, rus_p24, TESTS_5),
        ]):
            ax = axes[row, col]
            # Tests that have both HLLC and Rusanov data
            common = [t for t in tests if t in hllc_data and t in rus_data]
            hllc_only = [t for t in tests if t in hllc_data and t not in rus_data]

            x_all = np.arange(len(tests))
            labels = []
            h_vals = []
            r_vals = []

            for t in tests:
                labels.append(TEST_TITLES.get(t, t))
                h_vals.append(hllc_data[t][vname]["min"] if t in hllc_data else np.nan)
                r_vals.append(rus_data[t][vname]["min"] if t in rus_data else np.nan)

            w = 0.35
            ax.bar(x_all - w/2, h_vals, w, label="HLLC", color="steelblue")
            ax.bar(x_all + w/2, r_vals, w, label="Rusanov", color="indianred")
            ax.set_xticks(x_all)
            ax.set_xticklabels(labels, fontsize=8, rotation=15)

            if col == 0:
                ax.set_ylabel(f"{prec_label}\nMin sig. digits", fontsize=9)
            if row == 0:
                ax.set_title(VAR_LABELS[vname], fontsize=11)
            ax.legend(fontsize=7, loc="best")
            ax.grid(True, alpha=0.2, axis="y")
            ax.axhline(y=0, color="k", lw=0.5, alpha=0.3)

            if row == 1:
                ax.axhline(y=7, color="orange", ls=":", lw=0.8, alpha=0.5)

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    out = PLOT_DIR / "vfc_hllc_vs_rusanov_overview.png"
    plt.savefig(str(out), dpi=150)
    plt.close()
    print(f"Saved: {out}")


def print_summary_table():
    """Print combined summary table."""
    hllc_p53 = gather_results(ROOT / "experiments" / "week3_validation" / "verificarlo" / "runs_p53_mca", TESTS_5)
    rus_p53  = gather_results(ROOT / "experiments" / "verificarlo_docker" / "runs_p53_mca_rusanov", TESTS_4)
    hllc_p24 = gather_results(ROOT / "experiments" / "verificarlo_docker" / "runs_p24_mca", TESTS_5)
    rus_p24  = gather_results(ROOT / "experiments" / "verificarlo_docker" / "runs_p24_mca_rusanov", TESTS_4)

    print("\n" + "=" * 95)
    print("  Verificarlo MCA: Minimum Significant Digits (HLLC vs Rusanov)")
    print("=" * 95)

    for prec_label, hllc_data, rus_data in [
        ("double (p=53)", hllc_p53, rus_p53),
        ("float32 (p=24)", hllc_p24, rus_p24),
    ]:
        print(f"\n  --- {prec_label} ---")
        print(f"  {'Test':<18s}  {'HLLC rho':>9s} {'Rus rho':>9s}  "
              f"{'HLLC u':>9s} {'Rus u':>9s}  "
              f"{'HLLC p':>9s} {'Rus p':>9s}")
        print(f"  {'-'*18}  {'-'*9} {'-'*9}  {'-'*9} {'-'*9}  {'-'*9} {'-'*9}")

        for t in TESTS_5:
            title = TEST_TITLES.get(t, t)
            h = hllc_data.get(t, {})
            r = rus_data.get(t, {})

            def fmt(d, v):
                return f"{d[v]['min']:9.2f}" if v in d else "      N/A"

            print(f"  {title:<18s}  {fmt(h,'rho')} {fmt(r,'rho')}  "
                  f"{fmt(h,'u')} {fmt(r,'u')}  "
                  f"{fmt(h,'p')} {fmt(r,'p')}")

    print()


if __name__ == "__main__":
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    plot_p53_comparison()
    plot_p24_comparison()
    plot_precision_overview()
    print_summary_table()
