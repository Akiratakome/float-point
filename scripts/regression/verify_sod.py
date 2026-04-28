"""
Week 2 Verification: Sod Shock Tube (Toro Test 1)
Compares MUSCL-Hancock + HLLC numerical solution against the exact Riemann solution.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ── Exact Riemann solver for Sod problem ──────────────────────────────────────

def exact_sod(x, t, gamma=1.4, x0=0.5,
              rhoL=1.0, uL=0.0, pL=1.0,
              rhoR=0.125, uR=0.0, pR=0.1):
    """Exact solution of the Sod shock tube at time t (Toro Ch.4)."""
    gm1 = gamma - 1.0
    gp1 = gamma + 1.0

    aL = np.sqrt(gamma * pL / rhoL)
    aR = np.sqrt(gamma * pR / rhoR)

    # Solve for p_star iteratively (Newton-Raphson on pressure function)
    p_star = _solve_pstar(gamma, rhoL, uL, pL, aL, rhoR, uR, pR, aR)

    # Contact velocity
    u_star = 0.5 * (uL + uR) + 0.5 * (
        _f(p_star, rhoR, pR, gamma) - _f(p_star, rhoL, pL, gamma))

    # Star-region densities
    # Left: rarefaction
    rho_starL = rhoL * (p_star / pL) ** (1.0 / gamma)
    # Right: shock
    rho_starR = rhoR * ((p_star / pR + gm1 / gp1) /
                        (gm1 / gp1 * p_star / pR + 1.0))

    # Wave speeds
    a_starL = aL * (p_star / pL) ** (gm1 / (2.0 * gamma))
    # Rarefaction head and tail
    s_HL = uL - aL
    s_TL = u_star - a_starL
    # Shock speed (right)
    s_R = uR + aR * np.sqrt(gp1 / (2.0 * gamma) * p_star / pR + gm1 / (2.0 * gamma))

    # Sample solution
    rho = np.empty_like(x)
    u   = np.empty_like(x)
    p   = np.empty_like(x)

    for i, xi in enumerate(x):
        s = (xi - x0) / t  # self-similar variable
        if s <= s_HL:
            # Left data
            rho[i], u[i], p[i] = rhoL, uL, pL
        elif s <= s_TL:
            # Inside rarefaction fan
            rho[i], u[i], p[i] = _rarefaction(s, gamma, rhoL, uL, pL, aL)
        elif s <= u_star:
            # Left star region
            rho[i], u[i], p[i] = rho_starL, u_star, p_star
        elif s <= s_R:
            # Right star region
            rho[i], u[i], p[i] = rho_starR, u_star, p_star
        else:
            # Right data
            rho[i], u[i], p[i] = rhoR, uR, pR

    e = p / (gm1 * rho)  # specific internal energy
    return rho, u, p, e


def _f(p, rho_k, p_k, gamma):
    """Pressure function f_K(p) for the exact Riemann solver."""
    gm1 = gamma - 1.0
    gp1 = gamma + 1.0
    A = 2.0 / (gp1 * rho_k)
    B = gm1 / gp1 * p_k
    if p > p_k:
        # Shock
        return (p - p_k) * np.sqrt(A / (p + B))
    else:
        # Rarefaction
        a_k = np.sqrt(gamma * p_k / rho_k)
        return 2.0 * a_k / gm1 * ((p / p_k) ** (gm1 / (2.0 * gamma)) - 1.0)


def _df(p, rho_k, p_k, gamma):
    """Derivative of pressure function."""
    gm1 = gamma - 1.0
    gp1 = gamma + 1.0
    A = 2.0 / (gp1 * rho_k)
    B = gm1 / gp1 * p_k
    if p > p_k:
        return np.sqrt(A / (p + B)) * (1.0 - (p - p_k) / (2.0 * (p + B)))
    else:
        a_k = np.sqrt(gamma * p_k / rho_k)
        return 1.0 / (rho_k * a_k) * (p / p_k) ** (-(gp1) / (2.0 * gamma))


def _solve_pstar(gamma, rhoL, uL, pL, aL, rhoR, uR, pR, aR, tol=1e-12):
    """Newton-Raphson iteration for p_star."""
    # Initial guess: linearised solution
    p = 0.5 * (pL + pR) - 0.125 * (uR - uL) * (rhoL + rhoR) * (aL + aR)
    p = max(p, 1e-15)
    for _ in range(100):
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


def _rarefaction(s, gamma, rho_k, u_k, p_k, a_k):
    """Sample inside a left rarefaction fan."""
    gm1 = gamma - 1.0
    gp1 = gamma + 1.0
    rho = rho_k * (2.0 / gp1 + gm1 / (gp1 * a_k) * (u_k - s)) ** (2.0 / gm1)
    u   = 2.0 / gp1 * (a_k + gm1 / 2.0 * u_k + s)
    p   = p_k * (2.0 / gp1 + gm1 / (gp1 * a_k) * (u_k - s)) ** (2.0 * gamma / gm1)
    return rho, u, p


# ── Load numerical data ──────────────────────────────────────────────────────

def load_numerical(path):
    data = np.loadtxt(path)
    return data[:, 0], data[:, 1], data[:, 2], data[:, 4]  # x, rho, u, p


# ── Plotting ──────────────────────────────────────────────────────────────────

def plot_sod(x_num, rho_num, u_num, p_num, x_ex, rho_ex, u_ex, p_ex, e_ex, outpath):
    """4-panel comparison: rho, u, p, specific internal energy."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle("Sod Shock Tube  (t = 0.25, MUSCL-Hancock + HLLC, 200 cells)",
                 fontsize=14, fontweight="bold")

    # Compute numerical internal energy
    gm1 = 0.4
    e_num = p_num / (gm1 * rho_num)

    panels = [
        (axes[0, 0], "Density",                  rho_num, rho_ex),
        (axes[0, 1], "Velocity",                  u_num,   u_ex),
        (axes[1, 0], "Pressure",                  p_num,   p_ex),
        (axes[1, 1], "Specific Internal Energy",  e_num,   e_ex),
    ]

    for ax, title, num, ex in panels:
        ax.plot(x_ex, ex, "k-", lw=1.2, label="Exact")
        ax.plot(x_num, num, "ro", ms=2.0, alpha=0.6, label="Numerical")
        ax.set_title(title)
        ax.set_xlabel("x")
        ax.legend(loc="best", fontsize=9)
        ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(str(outpath), dpi=150)
    print(f"Saved: {outpath}")
    plt.close()


def compute_errors(x_num, rho_num, u_num, p_num, rho_ex, u_ex, p_ex):
    """L1 and Linf errors."""
    dx = x_num[1] - x_num[0]
    errors = {}
    for name, num, ex in [("rho", rho_num, rho_ex),
                           ("u",   u_num,   u_ex),
                           ("p",   p_num,   p_ex)]:
        diff = np.abs(num - ex)
        errors[name] = {"L1": np.sum(diff) * dx, "Linf": np.max(diff)}
    return errors


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    data_path = root / "output" / "sod_result.txt"
    fig_path  = root / "output" / "sod_verification.png"

    # Load numerical
    x_num, rho_num, u_num, p_num = load_numerical(data_path)
    print(f"Loaded {len(x_num)} cells from {data_path}")

    # Exact solution sampled at same x
    rho_ex, u_ex, p_ex, e_ex = exact_sod(x_num, t=0.25)

    # Errors
    errors = compute_errors(x_num, rho_num, u_num, p_num, rho_ex, u_ex, p_ex)
    print("\n--- Error norms (numerical vs exact) ---")
    for var, e in errors.items():
        print(f"  {var:>3s}:  L1 = {e['L1']:.6e}   Linf = {e['Linf']:.6e}")

    # Plot
    plot_sod(x_num, rho_num, u_num, p_num, x_num, rho_ex, u_ex, p_ex, e_ex, fig_path)

    # Pass/fail check
    print("\n--- Sanity checks ---")
    ok = True
    if errors["rho"]["L1"] > 0.02:
        print("  FAIL: rho L1 error too large")
        ok = False
    if errors["p"]["L1"] > 0.02:
        print("  FAIL: p L1 error too large")
        ok = False
    if errors["u"]["Linf"] > 0.25:
        print("  FAIL: u Linf error too large")
        ok = False

    if ok:
        print("  ALL CHECKS PASSED")
    else:
        print("  SOME CHECKS FAILED")
