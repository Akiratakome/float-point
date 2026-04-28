"""
Week 2 Verification: Toro 1D Riemann Tests 1-5
Compares MUSCL-Hancock + HLLC numerical solutions against exact Riemann solutions.
Generates per-test 4-panel plots and a combined summary figure.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ── Toro test definitions ─────────────────────────────────────────────────────

TESTS = {
    "sod": {
        "title": "Test 1: Sod Shock Tube",
        "file": "sod_result.txt",
        "t_end": 0.25, "x0": 0.5, "gamma": 1.4,
        "rhoL": 1.0,     "uL": 0.0,     "pL": 1.0,
        "rhoR": 0.125,   "uR": 0.0,     "pR": 0.1,
    },
    "toro2": {
        "title": "Test 2: 123 Problem (Two Rarefactions)",
        "file": "toro2_result.txt",
        "t_end": 0.15, "x0": 0.5, "gamma": 1.4,
        "rhoL": 1.0,  "uL": -2.0,  "pL": 0.4,
        "rhoR": 1.0,  "uR":  2.0,  "pR": 0.4,
    },
    "toro3": {
        "title": "Test 3: Blast Wave (Left Woodward-Colella)",
        "file": "toro3_result.txt",
        "t_end": 0.012, "x0": 0.5, "gamma": 1.4,
        "rhoL": 1.0,  "uL": 0.0,  "pL": 1000.0,
        "rhoR": 1.0,  "uR": 0.0,  "pR": 0.01,
    },
    "toro4": {
        "title": "Test 4: Lax Problem",
        "file": "toro4_result.txt",
        "t_end": 0.035, "x0": 0.5, "gamma": 1.4,
        "rhoL": 0.445,  "uL": 0.698,  "pL": 3.528,
        "rhoR": 0.5,    "uR": 0.0,    "pR": 0.571,
    },
    "toro5": {
        "title": "Test 5: Slow Moving Contact",
        "file": "toro5_result.txt",
        "t_end": 0.035, "x0": 0.5, "gamma": 1.4,
        "rhoL": 5.99924,  "uL": 19.5975,   "pL": 460.894,
        "rhoR": 5.99242,  "uR": -6.19633,  "pR": 46.0950,
    },
}

# ── Exact Riemann solver (general, Toro Ch.4) ────────────────────────────────

def _f(p, rho_k, p_k, gamma):
    gm1, gp1 = gamma - 1.0, gamma + 1.0
    A = 2.0 / (gp1 * rho_k)
    B = gm1 / gp1 * p_k
    if p > p_k:
        return (p - p_k) * np.sqrt(A / (p + B))
    else:
        a_k = np.sqrt(gamma * p_k / rho_k)
        return 2.0 * a_k / gm1 * ((p / p_k) ** (gm1 / (2.0 * gamma)) - 1.0)


def _df(p, rho_k, p_k, gamma):
    gm1, gp1 = gamma - 1.0, gamma + 1.0
    A = 2.0 / (gp1 * rho_k)
    B = gm1 / gp1 * p_k
    if p > p_k:
        return np.sqrt(A / (p + B)) * (1.0 - (p - p_k) / (2.0 * (p + B)))
    else:
        a_k = np.sqrt(gamma * p_k / rho_k)
        return 1.0 / (rho_k * a_k) * (p / p_k) ** (-(gp1) / (2.0 * gamma))


def _solve_pstar(gamma, rhoL, uL, pL, aL, rhoR, uR, pR, aR, tol=1e-12):
    p = 0.5 * (pL + pR) - 0.125 * (uR - uL) * (rhoL + rhoR) * (aL + aR)
    p = max(p, 1e-15)
    for _ in range(200):
        fL  = _f(p, rhoL, pL, gamma)
        fR  = _f(p, rhoR, pR, gamma)
        dfL = _df(p, rhoL, pL, gamma)
        dfR = _df(p, rhoR, pR, gamma)
        dp = -(fL + fR + uR - uL) / (dfL + dfR)
        p_new = max(p + dp, 1e-15)
        if abs(p_new - p) < tol * 0.5 * (p_new + p):
            return p_new
        p = p_new
    return p


def exact_riemann(x, t, gamma, x0, rhoL, uL, pL, rhoR, uR, pR):
    """Exact Riemann solver sampling for general initial data."""
    gm1, gp1 = gamma - 1.0, gamma + 1.0
    aL = np.sqrt(gamma * pL / rhoL)
    aR = np.sqrt(gamma * pR / rhoR)

    p_star = _solve_pstar(gamma, rhoL, uL, pL, aL, rhoR, uR, pR, aR)
    u_star = 0.5 * (uL + uR) + 0.5 * (_f(p_star, rhoR, pR, gamma)
                                       - _f(p_star, rhoL, pL, gamma))

    # Left wave
    if p_star > pL:
        # Left shock
        rho_starL = rhoL * ((p_star / pL + gm1 / gp1) /
                            (gm1 / gp1 * p_star / pL + 1.0))
        s_L = uL - aL * np.sqrt(gp1 / (2 * gamma) * p_star / pL + gm1 / (2 * gamma))
        left_type = "shock"
    else:
        # Left rarefaction
        rho_starL = rhoL * (p_star / pL) ** (1.0 / gamma)
        a_starL = aL * (p_star / pL) ** (gm1 / (2.0 * gamma))
        s_HL = uL - aL
        s_TL = u_star - a_starL
        left_type = "rarefaction"

    # Right wave
    if p_star > pR:
        # Right shock
        rho_starR = rhoR * ((p_star / pR + gm1 / gp1) /
                            (gm1 / gp1 * p_star / pR + 1.0))
        s_R = uR + aR * np.sqrt(gp1 / (2 * gamma) * p_star / pR + gm1 / (2 * gamma))
        right_type = "shock"
    else:
        # Right rarefaction
        rho_starR = rhoR * (p_star / pR) ** (1.0 / gamma)
        a_starR = aR * (p_star / pR) ** (gm1 / (2.0 * gamma))
        s_HR = uR + aR
        s_TR = u_star + a_starR
        right_type = "rarefaction"

    rho = np.empty_like(x)
    u   = np.empty_like(x)
    p   = np.empty_like(x)

    for i, xi in enumerate(x):
        s = (xi - x0) / t

        # Left wave region
        if left_type == "shock":
            if s <= s_L:
                rho[i], u[i], p[i] = rhoL, uL, pL; continue
            in_left_wave = False
        else:
            if s <= s_HL:
                rho[i], u[i], p[i] = rhoL, uL, pL; continue
            if s <= s_TL:
                # Inside left rarefaction fan
                rho[i] = rhoL * (2.0 / gp1 + gm1 / (gp1 * aL) * (uL - s)) ** (2.0 / gm1)
                u[i]   = 2.0 / gp1 * (aL + gm1 / 2.0 * uL + s)
                p[i]   = pL * (2.0 / gp1 + gm1 / (gp1 * aL) * (uL - s)) ** (2.0 * gamma / gm1)
                continue
            in_left_wave = False

        # Contact / star regions
        if s <= u_star:
            rho[i], u[i], p[i] = rho_starL, u_star, p_star
            continue

        # Right wave region
        if right_type == "shock":
            if s <= s_R:
                rho[i], u[i], p[i] = rho_starR, u_star, p_star
                continue
            else:
                rho[i], u[i], p[i] = rhoR, uR, pR
                continue
        else:
            if s <= s_TR:
                rho[i], u[i], p[i] = rho_starR, u_star, p_star
                continue
            if s <= s_HR:
                # Inside right rarefaction fan
                rho[i] = rhoR * (2.0 / gp1 - gm1 / (gp1 * aR) * (uR - s)) ** (2.0 / gm1)
                u[i]   = 2.0 / gp1 * (-aR + gm1 / 2.0 * uR + s)
                p[i]   = pR * (2.0 / gp1 - gm1 / (gp1 * aR) * (uR - s)) ** (2.0 * gamma / gm1)
                continue
            else:
                rho[i], u[i], p[i] = rhoR, uR, pR
                continue

    e = p / (gm1 * rho)
    return rho, u, p, e


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_numerical(path):
    data = np.loadtxt(path)
    return data[:, 0], data[:, 1], data[:, 2], data[:, 4]  # x, rho, u, p


def compute_errors(x, rho_num, u_num, p_num, rho_ex, u_ex, p_ex):
    dx = x[1] - x[0]
    errors = {}
    for name, num, ex in [("rho", rho_num, rho_ex),
                           ("u",   u_num,   u_ex),
                           ("p",   p_num,   p_ex)]:
        diff = np.abs(num - ex)
        errors[name] = {"L1": np.sum(diff) * dx, "Linf": np.max(diff)}
    return errors


# ── Per-test plot ─────────────────────────────────────────────────────────────

def plot_single(test_key, cfg, x_num, rho_num, u_num, p_num,
                rho_ex, u_ex, p_ex, e_ex, outpath):
    gm1 = cfg["gamma"] - 1.0
    e_num = p_num / (gm1 * rho_num)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    fig.suptitle(f"{cfg['title']}  (t={cfg['t_end']}, MUSCL-Hancock+HLLC, {len(x_num)} cells)",
                 fontsize=13, fontweight="bold")

    for ax, title, num, ex in [
        (axes[0, 0], "Density",                  rho_num, rho_ex),
        (axes[0, 1], "Velocity",                  u_num,   u_ex),
        (axes[1, 0], "Pressure",                  p_num,   p_ex),
        (axes[1, 1], "Specific Internal Energy",  e_num,   e_ex),
    ]:
        ax.plot(x_num, ex, "k-", lw=1.2, label="Exact")
        ax.plot(x_num, num, "ro", ms=1.8, alpha=0.55, label="Numerical")
        ax.set_title(title)
        ax.set_xlabel("x")
        ax.legend(loc="best", fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(str(outpath), dpi=150)
    plt.close()


# ── Combined summary plot (density only, all 5 tests) ────────────────────────

def plot_summary(results, outpath):
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    fig.suptitle("Week 2 Verification: Toro 1D Tests (MUSCL-Hancock + HLLC, 200 cells)",
                 fontsize=14, fontweight="bold")
    axes_flat = axes.flatten()

    for idx, (key, r) in enumerate(results.items()):
        ax = axes_flat[idx]
        ax.plot(r["x"], r["rho_ex"], "k-", lw=1.2, label="Exact")
        ax.plot(r["x"], r["rho_num"], "ro", ms=1.5, alpha=0.5, label="Numerical")
        ax.set_title(r["title"], fontsize=10)
        ax.set_xlabel("x", fontsize=9)
        ax.set_ylabel("Density", fontsize=9)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
        # Annotate L1 error
        ax.text(0.02, 0.02, f"L1(rho)={r['errors']['rho']['L1']:.2e}",
                transform=ax.transAxes, fontsize=8, verticalalignment="bottom",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="wheat", alpha=0.7))

    # Hide 6th subplot
    axes_flat[5].set_visible(False)

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    plt.savefig(str(outpath), dpi=150)
    plt.close()


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    out_dir = root / "output"
    doc_dir = root / "docs" / "week2"
    doc_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    all_ok = True

    for key, cfg in TESTS.items():
        data_path = out_dir / cfg["file"]
        if not data_path.exists():
            print(f"[SKIP] {key}: {data_path} not found")
            continue

        x, rho_num, u_num, p_num = load_numerical(data_path)
        rho_ex, u_ex, p_ex, e_ex = exact_riemann(
            x, cfg["t_end"], cfg["gamma"], cfg["x0"],
            cfg["rhoL"], cfg["uL"], cfg["pL"],
            cfg["rhoR"], cfg["uR"], cfg["pR"])

        errors = compute_errors(x, rho_num, u_num, p_num, rho_ex, u_ex, p_ex)

        print(f"\n{'='*60}")
        print(f"  {cfg['title']}")
        print(f"{'='*60}")
        for var, e in errors.items():
            print(f"  {var:>3s}:  L1 = {e['L1']:.6e}   Linf = {e['Linf']:.6e}")

        # Per-test figure
        fig_path = doc_dir / f"{key}_verification.png"
        plot_single(key, cfg, x, rho_num, u_num, p_num, rho_ex, u_ex, p_ex, e_ex, fig_path)
        print(f"  Saved: {fig_path.name}")

        results[key] = {
            "x": x, "rho_num": rho_num, "rho_ex": rho_ex,
            "title": cfg["title"], "errors": errors
        }

    # Summary plot
    if results:
        summary_path = doc_dir / "toro_summary.png"
        plot_summary(results, summary_path)
        print(f"\nSaved summary: {summary_path}")

    # Error table
    print(f"\n{'='*60}")
    print("  Summary: L1 error norms")
    print(f"{'='*60}")
    print(f"  {'Test':<35s} {'rho':>10s} {'u':>10s} {'p':>10s}")
    print(f"  {'-'*35} {'-'*10} {'-'*10} {'-'*10}")
    for key, r in results.items():
        e = r["errors"]
        print(f"  {r['title']:<35s} {e['rho']['L1']:10.2e} {e['u']['L1']:10.2e} {e['p']['L1']:10.2e}")

    print("\nWeek 2 verification complete.")
