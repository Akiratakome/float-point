#!/usr/bin/env python3
"""
Plot 1D numerical vs exact Riemann solution.
Usage: python analysis/plot_1d.py output/sod.bin --gamma 1.4 --x0 0.5 --t-end 0.25 \
       --rhoL 1.0 --uL 0.0 --pL 1.0 --rhoR 0.125 --uR 0.0 --pR 0.1 \
       --title "Sod Shock Tube" -o output/sod_plot.png
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.verify_toro import exact_riemann
from analysis.compare import read_binary


def main():
    parser = argparse.ArgumentParser(description="Plot 1D numerical vs exact Riemann solution")
    parser.add_argument("binfile", help="Path to .bin output file")
    parser.add_argument("--gamma", type=float, default=1.4)
    parser.add_argument("--x0", type=float, default=0.5)
    parser.add_argument("--t-end", type=float, required=True)
    parser.add_argument("--rhoL", type=float, required=True)
    parser.add_argument("--uL", type=float, required=True)
    parser.add_argument("--pL", type=float, required=True)
    parser.add_argument("--rhoR", type=float, required=True)
    parser.add_argument("--uR", type=float, required=True)
    parser.add_argument("--pR", type=float, required=True)
    parser.add_argument("--title", type=str, default="1D Riemann Problem")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Output PNG path (default: show interactively)")
    args = parser.parse_args()

    data, nx, ny, nvars, time, dx, dy = read_binary(args.binfile)

    # Extract primitives from conservative variables
    rho = data[0, :, 0]
    rhou = data[0, :, 1]
    rhov = data[0, :, 2]
    E    = data[0, :, 3]
    u_num = rhou / rho
    p_num = (args.gamma - 1.0) * (E - 0.5 * rho * (u_num**2 + (rhov/rho)**2))

    x = np.array([(i + 0.5) * dx for i in range(nx)])

    # Exact solution (1000 points for smooth curve)
    x_exact = np.linspace(x[0], x[-1], 1000)
    rho_ex, u_ex, p_ex, _ = exact_riemann(
        x_exact, args.t_end, args.gamma, args.x0,
        args.rhoL, args.uL, args.pL,
        args.rhoR, args.uR, args.pR)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    fig.suptitle(f"{args.title}  (N={nx}, t={time:.4f})", fontsize=12, fontweight="bold")

    for ax, title, num, ex in [
        (axes[0], "Density", rho, rho_ex),
        (axes[1], "Velocity", u_num, u_ex),
        (axes[2], "Pressure", p_num, p_ex),
    ]:
        ax.plot(x_exact, ex, "k-", lw=1.2, label="Exact")
        ax.plot(x, num, "ro", ms=2.0, alpha=0.5, label="Numerical")
        ax.set_title(title)
        ax.set_xlabel("x")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    if args.output:
        plt.savefig(args.output, dpi=150, bbox_inches="tight")
        print(f"Saved: {args.output}")
    else:
        plt.show()
    plt.close()


if __name__ == "__main__":
    main()
