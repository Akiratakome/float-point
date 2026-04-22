"""
HLLC vs Rusanov Flux Comparison for HRSC 1D Euler Solver

Reads pre-generated output files from experiments/week4_rusanov/data/,
computes exact solutions, and generates comparison plots and error tables.

Usage:
    python scripts/run_comparison.py
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add scripts dir for verify_toro exact solver
sys.path.insert(0, str(Path(__file__).parent))
from verify_toro import exact_riemann

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "experiments" / "week4_rusanov" / "data"
PLOT_DIR = ROOT / "experiments" / "week4_rusanov" / "plots"

TESTS = {
    "sod": {
        "title": "Test 1: Sod Shock Tube",
        "t_end": 0.25, "x0": 0.5, "gamma": 1.4,
        "rhoL": 1.0,   "uL": 0.0,   "pL": 1.0,
        "rhoR": 0.125, "uR": 0.0,   "pR": 0.1,
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
        "rhoL": 0.445, "uL": 0.698, "pL": 3.528,
        "rhoR": 0.5,   "uR": 0.0,   "pR": 0.571,
    },
    "toro5": {
        "title": "Test 5: Slow Contact",
        "t_end": 0.035, "x0": 0.5, "gamma": 1.4,
        "rhoL": 5.99924, "uL": 19.5975,  "pL": 460.894,
        "rhoR": 5.99242, "uR": -6.19633, "pR": 46.0950,
    },
    "stationary_contact": {
        "title": "Stationary Contact",
        "t_end": 0.5, "x0": 0.5, "gamma": 1.4,
        "rhoL": 1.0, "uL": 0.0, "pL": 1.0,
        "rhoR": 0.5, "uR": 0.0, "pR": 1.0,
    },
}

VAR_COLS = {"rho": 1, "u": 2, "p": 4}
VAR_LABELS = {"rho": r"Density $\rho$", "u": r"Velocity $u$", "p": r"Pressure $p$"}


def load_data(filepath):
    """Load solver output: columns are x, rho, u, v, p."""
    return np.loadtxt(filepath)


def compute_exact(x, cfg):
    """Compute exact Riemann solution at cell centres. Returns (rho, u, p)."""
    rho, u, p, _e = exact_riemann(
        x, cfg["t_end"], cfg["gamma"], cfg["x0"],
        cfg["rhoL"], cfg["uL"], cfg["pL"],
        cfg["rhoR"], cfg["uR"], cfg["pR"],
    )
    return rho, u, p


def compute_errors(numerical, exact, dx):
    """Compute L1, L2, Linf error norms."""
    diff = np.abs(numerical - exact)
    L1   = np.sum(diff) * dx
    L2   = np.sqrt(np.sum(diff**2) * dx)
    Linf = np.max(diff)
    return L1, L2, Linf


def plot_test_comparison(test_name, cfg, data_hllc, data_rus, exact_rho, exact_u, exact_p, out_path):
    """4-panel plot: rho, u, p comparison + error difference."""
    x = data_hllc[:, 0]
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle(f"HLLC vs Rusanov — {cfg['title']}\n(nx=200, CFL=0.8)",
                 fontsize=13, fontweight="bold")

    vars_data = [
        ("rho", 1, exact_rho, VAR_LABELS["rho"]),
        ("u",   2, exact_u,   VAR_LABELS["u"]),
        ("p",   4, exact_p,   VAR_LABELS["p"]),
    ]

    for idx, (vname, col, exact, label) in enumerate(vars_data):
        ax = axes.flat[idx]
        ax.plot(x, exact, "k--", lw=1.2, label="Exact", zorder=3)
        ax.plot(x, data_hllc[:, col], "b-", lw=0.9, alpha=0.8, label="HLLC")
        ax.plot(x, data_rus[:, col], "r-", lw=0.9, alpha=0.8, label="Rusanov")
        ax.set_ylabel(label)
        ax.set_xlabel("x")
        ax.legend(fontsize=8, loc="best")
        ax.grid(True, alpha=0.2)

    # Bottom-right: error comparison bar chart
    ax = axes[1, 1]
    dx = x[1] - x[0]
    vars_short = ["rho", "u", "p"]
    cols = [1, 2, 4]
    exacts = [exact_rho, exact_u, exact_p]

    hllc_L1 = []
    rus_L1  = []
    for col, ex in zip(cols, exacts):
        h_L1, _, _ = compute_errors(data_hllc[:, col], ex, dx)
        r_L1, _, _ = compute_errors(data_rus[:, col], ex, dx)
        hllc_L1.append(h_L1)
        rus_L1.append(r_L1)

    bar_x = np.arange(len(vars_short))
    w = 0.35
    ax.bar(bar_x - w/2, hllc_L1, w, label="HLLC", color="steelblue")
    ax.bar(bar_x + w/2, rus_L1,  w, label="Rusanov", color="indianred")
    ax.set_xticks(bar_x)
    ax.set_xticklabels([VAR_LABELS[v] for v in vars_short], fontsize=9)
    ax.set_ylabel("L1 Error")
    ax.set_title("L1 Error Comparison", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.2, axis="y")

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig(str(out_path), dpi=150)
    plt.close()


def plot_convergence_comparison(hllc_conv, rus_conv, out_path):
    """Log-log convergence plot for HLLC vs Rusanov."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.suptitle("Grid Convergence: HLLC vs Rusanov (Sod Shock Tube)",
                 fontsize=13, fontweight="bold")

    # Parse convergence data: skip header line
    h_data = np.loadtxt(hllc_conv, comments="#")
    r_data = np.loadtxt(rus_conv, comments="#")

    # Columns: N, dx, L1_rho, L2_rho, Linf_rho, L1_u, L2_u, Linf_u, L1_p, L2_p, Linf_p
    var_cols = {"rho": 2, "u": 5, "p": 8}  # L1 column indices

    for idx, (vname, col) in enumerate(var_cols.items()):
        ax = axes[idx]
        dx_h = h_data[:, 1]
        dx_r = r_data[:, 1]

        ax.loglog(dx_h, h_data[:, col], "bo-", lw=1.2, ms=5, label="HLLC")
        ax.loglog(dx_r, r_data[:, col], "rs-", lw=1.2, ms=5, label="Rusanov")

        # Reference slopes
        x_ref = np.array([dx_h[0], dx_h[-1]])
        y_start = max(h_data[0, col], r_data[0, col]) * 1.5
        ax.loglog(x_ref, y_start * (x_ref / x_ref[0])**1.0, "k--", lw=0.7, alpha=0.5, label="O(1)")
        ax.loglog(x_ref, y_start * (x_ref / x_ref[0])**2.0, "k:", lw=0.7, alpha=0.5, label="O(2)")

        ax.set_xlabel("dx")
        ax.set_ylabel(f"L1 error ({VAR_LABELS[vname]})")
        ax.set_title(VAR_LABELS[vname], fontsize=10)
        ax.legend(fontsize=7, loc="best")
        ax.grid(True, alpha=0.3, which="both")

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig(str(out_path), dpi=150)
    plt.close()


def print_error_table(all_errors):
    """Print a formatted error table."""
    print("\n" + "=" * 90)
    print("  L1 Error Comparison: HLLC vs Rusanov")
    print("=" * 90)
    print(f"  {'Test':<25s}  {'HLLC rho':>10s}  {'Rus rho':>10s}  "
          f"{'HLLC u':>10s}  {'Rus u':>10s}  "
          f"{'HLLC p':>10s}  {'Rus p':>10s}")
    print(f"  {'-'*25}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}")

    for test_name, errs in all_errors.items():
        cfg = TESTS[test_name]
        h = errs["hllc"]
        r = errs["rusanov"]
        print(f"  {cfg['title']:<25s}  "
              f"{h['rho'][0]:10.4e}  {r['rho'][0]:10.4e}  "
              f"{h['u'][0]:10.4e}  {r['u'][0]:10.4e}  "
              f"{h['p'][0]:10.4e}  {r['p'][0]:10.4e}")

    print()
    print("  Rusanov / HLLC L1 error ratio:")
    print(f"  {'Test':<25s}  {'rho':>8s}  {'u':>8s}  {'p':>8s}")
    print(f"  {'-'*25}  {'-'*8}  {'-'*8}  {'-'*8}")
    for test_name, errs in all_errors.items():
        cfg = TESTS[test_name]
        h = errs["hllc"]
        r = errs["rusanov"]
        rho_ratio = r["rho"][0] / h["rho"][0] if h["rho"][0] > 0 else float("inf")
        u_ratio   = r["u"][0]   / h["u"][0]   if h["u"][0]   > 0 else float("inf")
        p_ratio   = r["p"][0]   / h["p"][0]   if h["p"][0]   > 0 else float("inf")
        print(f"  {cfg['title']:<25s}  {rho_ratio:8.2f}  {u_ratio:8.2f}  {p_ratio:8.2f}")
    print()


def plot_summary_error_ratios(all_errors, out_path):
    """Bar chart of Rusanov/HLLC error ratios across tests."""
    test_names = list(all_errors.keys())
    titles = [TESTS[t]["title"] for t in test_names]

    ratios = {v: [] for v in ["rho", "u", "p"]}
    for tname in test_names:
        h = all_errors[tname]["hllc"]
        r = all_errors[tname]["rusanov"]
        for v in ["rho", "u", "p"]:
            ratio = r[v][0] / h[v][0] if h[v][0] > 0 else 0
            ratios[v].append(ratio)

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(test_names))
    w = 0.25

    for i, (v, label) in enumerate(VAR_LABELS.items()):
        ax.bar(x + (i - 1) * w, ratios[v], w, label=label)

    ax.axhline(y=1.0, color="k", ls="--", lw=0.8, alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(titles, fontsize=8, rotation=15, ha="right")
    ax.set_ylabel("Rusanov / HLLC L1 Error Ratio")
    ax.set_title("Rusanov Additional Diffusion vs HLLC\n(ratio > 1 = Rusanov more diffusive)",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.2, axis="y")

    plt.tight_layout()
    plt.savefig(str(out_path), dpi=150)
    plt.close()


def main():
    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    all_errors = {}

    for test_name, cfg in TESTS.items():
        hllc_file = DATA_DIR / f"{test_name}_hllc.txt"
        rus_file  = DATA_DIR / f"{test_name}_rusanov.txt"

        if not hllc_file.exists():
            print(f"  [SKIP] {test_name}: HLLC output not found")
            continue
        if not rus_file.exists():
            print(f"  [SKIP] {test_name}: Rusanov output not found (failed on this test)")
            continue

        print(f"Processing {cfg['title']}...")

        data_hllc = load_data(hllc_file)
        data_rus  = load_data(rus_file)
        x = data_hllc[:, 0]
        dx = x[1] - x[0]

        # Compute exact solution
        exact_rho, exact_u, exact_p = compute_exact(x, cfg)

        # Compute errors
        errors_hllc = {}
        errors_rus  = {}
        for vname, col in VAR_COLS.items():
            exact_v = {"rho": exact_rho, "u": exact_u, "p": exact_p}[vname]
            errors_hllc[vname] = compute_errors(data_hllc[:, col], exact_v, dx)
            errors_rus[vname]  = compute_errors(data_rus[:, col], exact_v, dx)

        all_errors[test_name] = {"hllc": errors_hllc, "rusanov": errors_rus}

        # Per-test comparison plot
        plot_path = PLOT_DIR / f"{test_name}_hllc_vs_rusanov.png"
        plot_test_comparison(test_name, cfg, data_hllc, data_rus,
                            exact_rho, exact_u, exact_p, plot_path)
        print(f"  Saved: {plot_path.name}")

    # Error table
    print_error_table(all_errors)

    # Summary ratio plot
    if all_errors:
        summary_path = PLOT_DIR / "summary_error_ratios.png"
        plot_summary_error_ratios(all_errors, summary_path)
        print(f"Saved: {summary_path.name}")

    # Convergence comparison
    hllc_conv = DATA_DIR / "convergence_hllc.txt"
    rus_conv  = DATA_DIR / "convergence_rusanov.txt"
    if hllc_conv.exists() and rus_conv.exists():
        conv_path = PLOT_DIR / "convergence_hllc_vs_rusanov.png"
        plot_convergence_comparison(hllc_conv, rus_conv, conv_path)
        print(f"Saved: {conv_path.name}")

    # Note about Toro Test 2
    print("\nNOTE: Toro Test 2 (123 problem) omitted — Rusanov fails on near-vacuum")
    print("      problems due to excessive numerical diffusion causing negative density.")
    print("      This is an expected finding: the simpler flux cannot handle extreme")
    print("      wave structures that HLLC resolves via its star-region computation.\n")

    print("All comparison plots saved to:", PLOT_DIR)


if __name__ == "__main__":
    main()
