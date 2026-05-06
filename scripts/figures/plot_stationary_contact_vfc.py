"""
Verificarlo MCA analysis for Stationary Contact Discontinuity.

Generates spatial profiles of significant digits to reveal:
  - Where the contact interface is located (sig digits dip)
  - Whether FP precision can distinguish which side is denser
  - HLLC vs Rusanov sensitivity near the contact

Usage:
    python scripts/figures/plot_stationary_contact_vfc.py
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLOT_DIR = ROOT / "experiments" / "week4_rusanov" / "plots"
DATA_BASE = ROOT / "experiments" / "verificarlo_docker" / "runs_p53_mca_stationary_contact"
DATA_P24  = ROOT / "experiments" / "verificarlo_docker" / "runs_p24_mca_stationary_contact"

COL = {"x": 0, "rho": 1, "u": 2, "v": 3, "p": 4}


def load_runs(run_dir):
    """Load all MCA sample files from a directory."""
    files = sorted(Path(run_dir).glob("run_*.txt"))
    if not files:
        return None
    return np.array([np.loadtxt(f) for f in files])


def sig_digits(samples, col):
    """Compute significant digits at each cell: s = -log10(|std/mean|)."""
    vals = samples[:, :, col]
    mean = np.mean(vals, axis=0)
    std = np.std(vals, axis=0, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        s = -np.log10(np.abs(std / mean))
        s = np.where(np.isfinite(s), s, np.nan)
    return mean, std, s


def plot_spatial_profile():
    """Main figure: significant digits vs x for stationary contact."""
    hllc_53 = load_runs(DATA_BASE / "hllc")
    rus_53  = load_runs(DATA_BASE / "rusanov")
    hllc_24 = load_runs(DATA_P24 / "hllc")
    rus_24  = load_runs(DATA_P24 / "rusanov")

    if hllc_53 is None:
        print("ERROR: no HLLC p53 data found")
        return

    x = hllc_53[0, :, COL["x"]]

    fig, axes = plt.subplots(3, 2, figsize=(16, 12))
    fig.suptitle("Verificarlo MCA: Stationary Contact Discontinuity\n"
                 r"$\rho_L=1.0,\ \rho_R=0.5,\ u=0,\ p=1.0$ — contact at $x=0.5$",
                 fontsize=14, fontweight="bold")

    col_labels = [("double (p=53)", hllc_53, rus_53),
                  ("float32 (p=24)", hllc_24, rus_24)]

    for col_idx, (prec_label, hllc, rus) in enumerate(col_labels):
        for row_idx, (vname, vcol) in enumerate([("rho", COL["rho"]),
                                                  ("u", COL["u"]),
                                                  ("p", COL["p"])]):
            ax = axes[row_idx, col_idx]

            # HLLC
            h_mean, h_std, h_sig = sig_digits(hllc, vcol)
            ax.plot(x, h_sig, "b-", lw=1.2, label="HLLC", alpha=0.9)

            # Rusanov
            if rus is not None:
                r_mean, r_std, r_sig = sig_digits(rus, vcol)
                ax.plot(x, r_sig, "r-", lw=1.2, label="Rusanov", alpha=0.9)

            # Mark contact location
            ax.axvline(x=0.5, color="grey", ls="--", lw=0.8, alpha=0.5,
                       label="contact at x=0.5")

            ax.set_xlabel("x")
            ax.set_ylabel("Significant digits")
            ax.legend(fontsize=7, loc="lower left")
            ax.grid(True, alpha=0.2)

            if row_idx == 0:
                ax.set_title(prec_label, fontsize=11)

            # y-label on left edge
            if col_idx == 0:
                var_labels = {"rho": r"$\rho$", "u": r"$u$", "p": r"$p$"}
                ax.set_ylabel(f"{var_labels[vname]} — sig digits", fontsize=10)

            # float32 reference line
            if col_idx == 1:
                ax.axhline(y=7, color="orange", ls=":", lw=0.8, alpha=0.5)

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    out = PLOT_DIR / "vfc_stationary_contact_spatial.png"
    plt.savefig(str(out), dpi=150)
    plt.close()
    print(f"Saved: {out}")


def plot_mca_overlay():
    """Overlay all 30 MCA samples to visually show spread near contact."""
    hllc_53 = load_runs(DATA_BASE / "hllc")
    rus_53  = load_runs(DATA_BASE / "rusanov")

    if hllc_53 is None:
        return

    x = hllc_53[0, :, COL["x"]]

    # Load IEEE reference
    ref_file = DATA_BASE / "reference_ieee.txt"
    ref = np.loadtxt(ref_file) if ref_file.exists() else None

    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    fig.suptitle("MCA Sample Overlay — Stationary Contact (30 samples, p=53)\n"
                 "Top: HLLC, Bottom: Rusanov",
                 fontsize=13, fontweight="bold")

    datasets = [("HLLC", hllc_53), ("Rusanov", rus_53)]
    var_info = [("rho", COL["rho"], r"$\rho$"),
                ("u",   COL["u"],   r"$u$"),
                ("p",   COL["p"],   r"$p$")]

    for row, (scheme, runs) in enumerate(datasets):
        if runs is None:
            continue
        for col, (vname, vcol, vlabel) in enumerate(var_info):
            ax = axes[row, col]

            # Plot all 30 samples in light grey
            for i in range(runs.shape[0]):
                ax.plot(x, runs[i, :, vcol], color="grey", lw=0.3, alpha=0.3)

            # MCA mean
            mean = np.mean(runs[:, :, vcol], axis=0)
            ax.plot(x, mean, "b-", lw=1.2, label="MCA mean")

            # IEEE reference
            if ref is not None:
                ax.plot(x, ref[:, vcol], "r--", lw=0.8, alpha=0.7, label="IEEE ref")

            ax.axvline(x=0.5, color="green", ls="--", lw=0.6, alpha=0.4)
            ax.set_xlabel("x")
            ax.set_ylabel(vlabel)
            ax.legend(fontsize=7, loc="best")
            ax.grid(True, alpha=0.2)

            if row == 0:
                ax.set_title(vlabel, fontsize=11)
            if col == 0:
                ax.text(-0.15, 0.5, scheme, transform=ax.transAxes,
                        fontsize=11, fontweight="bold", va="center", rotation=90)

    plt.tight_layout(rect=[0.02, 0, 1, 0.92])
    out = PLOT_DIR / "vfc_stationary_contact_overlay.png"
    plt.savefig(str(out), dpi=150)
    plt.close()
    print(f"Saved: {out}")


def plot_std_profile():
    """Absolute and relative std profile — shows exactly where FP sensitivity is."""
    hllc_53 = load_runs(DATA_BASE / "hllc")
    rus_53  = load_runs(DATA_BASE / "rusanov")
    hllc_24 = load_runs(DATA_P24 / "hllc")
    rus_24  = load_runs(DATA_P24 / "rusanov")

    x = hllc_53[0, :, COL["x"]]

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("Stationary Contact: FP Perturbation Profile\n"
                 r"Absolute std($\rho$) and relative std($\rho$)/mean($\rho$) across MCA samples",
                 fontsize=13, fontweight="bold")

    for col_idx, (prec_label, hllc, rus) in enumerate([
        ("double (p=53)", hllc_53, rus_53),
        ("float32 (p=24)", hllc_24, rus_24),
    ]):
        # Row 0: absolute std of rho
        ax = axes[0, col_idx]
        h_std = np.std(hllc[:, :, COL["rho"]], axis=0, ddof=1)
        ax.semilogy(x, h_std, "b-", lw=1.0, label="HLLC")
        if rus is not None:
            r_std = np.std(rus[:, :, COL["rho"]], axis=0, ddof=1)
            ax.semilogy(x, r_std, "r-", lw=1.0, label="Rusanov")
        ax.axvline(x=0.5, color="grey", ls="--", lw=0.8, alpha=0.5)
        ax.set_title(f"Absolute std(ρ) — {prec_label}", fontsize=10)
        ax.set_xlabel("x")
        ax.set_ylabel(r"$\sigma(\rho)$")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.2)

        # Row 1: relative std of rho
        ax = axes[1, col_idx]
        h_mean = np.mean(hllc[:, :, COL["rho"]], axis=0)
        h_rel = h_std / np.abs(h_mean)
        ax.semilogy(x, h_rel, "b-", lw=1.0, label="HLLC")
        if rus is not None:
            r_mean = np.mean(rus[:, :, COL["rho"]], axis=0)
            r_rel = r_std / np.abs(r_mean)
            ax.semilogy(x, r_rel, "r-", lw=1.0, label="Rusanov")
        ax.axvline(x=0.5, color="grey", ls="--", lw=0.8, alpha=0.5)
        ax.set_title(f"Relative std(ρ)/mean(ρ) — {prec_label}", fontsize=10)
        ax.set_xlabel("x")
        ax.set_ylabel(r"$\sigma(\rho) / |\mu(\rho)|$")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.2)

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    out = PLOT_DIR / "vfc_stationary_contact_std.png"
    plt.savefig(str(out), dpi=150)
    plt.close()
    print(f"Saved: {out}")


def plot_zoom_contact():
    """Zoomed view of significant digits near the contact at x=0.5."""
    hllc_53 = load_runs(DATA_BASE / "hllc")
    rus_53  = load_runs(DATA_BASE / "rusanov")
    hllc_24 = load_runs(DATA_P24 / "hllc")
    rus_24  = load_runs(DATA_P24 / "rusanov")

    x = hllc_53[0, :, COL["x"]]

    # Zoom range: x in [0.3, 0.7]
    mask = (x >= 0.3) & (x <= 0.7)
    xz = x[mask]

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("Zoomed View: Significant Digits Near Contact (x=0.5)\n"
                 r"$\rho_L=1.0$ (left), $\rho_R=0.5$ (right) — can MCA detect the interface?",
                 fontsize=13, fontweight="bold")

    for col_idx, (prec_label, hllc, rus) in enumerate([
        ("double (p=53)", hllc_53, rus_53),
        ("float32 (p=24)", hllc_24, rus_24),
    ]):
        for row_idx, (vname, vcol, vlabel) in enumerate([
            ("rho", COL["rho"], r"$\rho$ — Density"),
            ("p",   COL["p"],   r"$p$ — Pressure"),
        ]):
            ax = axes[row_idx, col_idx]

            _, _, h_sig = sig_digits(hllc, vcol)
            ax.plot(xz, h_sig[mask], "b-o", lw=1.0, ms=2, label="HLLC")

            if rus is not None:
                _, _, r_sig = sig_digits(rus, vcol)
                ax.plot(xz, r_sig[mask], "r-s", lw=1.0, ms=2, label="Rusanov")

            ax.axvline(x=0.5, color="green", ls="--", lw=1.0, alpha=0.6,
                       label="exact contact")
            ax.axvspan(0.3, 0.5, alpha=0.05, color="blue")
            ax.axvspan(0.5, 0.7, alpha=0.05, color="red")
            ax.text(0.38, ax.get_ylim()[0] + 0.5 if ax.get_ylim()[0] > 0 else 0.5,
                    r"$\rho=1.0$", fontsize=9, color="blue", ha="center")
            ax.text(0.62, ax.get_ylim()[0] + 0.5 if ax.get_ylim()[0] > 0 else 0.5,
                    r"$\rho=0.5$", fontsize=9, color="red", ha="center")

            ax.set_xlabel("x")
            ax.set_ylabel("Significant digits")
            ax.set_title(f"{vlabel} — {prec_label}", fontsize=10)
            ax.legend(fontsize=7, loc="lower left")
            ax.grid(True, alpha=0.2)

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    out = PLOT_DIR / "vfc_stationary_contact_zoom.png"
    plt.savefig(str(out), dpi=150)
    plt.close()
    print(f"Saved: {out}")


def print_summary():
    """Print summary statistics."""
    hllc_53 = load_runs(DATA_BASE / "hllc")
    rus_53  = load_runs(DATA_BASE / "rusanov")
    hllc_24 = load_runs(DATA_P24 / "hllc")
    rus_24  = load_runs(DATA_P24 / "rusanov")

    x = hllc_53[0, :, COL["x"]]

    # Find cells near contact (x=0.5)
    contact_cells = np.where((x >= 0.49) & (x <= 0.51))[0]
    left_cells = np.where((x >= 0.1) & (x <= 0.4))[0]
    right_cells = np.where((x >= 0.6) & (x <= 0.9))[0]

    print("\n" + "=" * 80)
    print("  Stationary Contact: Sig Digits by Region")
    print("=" * 80)

    for prec_label, hllc, rus in [
        ("double (p=53)", hllc_53, rus_53),
        ("float32 (p=24)", hllc_24, rus_24),
    ]:
        print(f"\n  --- {prec_label} ---")
        for scheme, runs, name in [("HLLC", hllc, "HLLC"), ("Rusanov", rus, "Rusanov")]:
            if runs is None:
                continue
            _, _, sig_rho = sig_digits(runs, COL["rho"])
            _, _, sig_p = sig_digits(runs, COL["p"])

            print(f"  {name}:")
            print(f"    rho: left(x<0.4) mean={np.nanmean(sig_rho[left_cells]):.2f}, "
                  f"contact(x~0.5) min={np.nanmin(sig_rho[contact_cells]):.2f}, "
                  f"right(x>0.6) mean={np.nanmean(sig_rho[right_cells]):.2f}")
            print(f"    p:   left(x<0.4) mean={np.nanmean(sig_p[left_cells]):.2f}, "
                  f"contact(x~0.5) min={np.nanmin(sig_p[contact_cells]):.2f}, "
                  f"right(x>0.6) mean={np.nanmean(sig_p[right_cells]):.2f}")


if __name__ == "__main__":
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    plot_spatial_profile()
    plot_mca_overlay()
    plot_std_profile()
    plot_zoom_contact()
    print_summary()
