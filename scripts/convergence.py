#!/usr/bin/env python3
"""Grid convergence study: reads error norm table from stdin, produces log-log plot."""

import sys
import numpy as np
import matplotlib.pyplot as plt

def main():
    lines = []
    for line in sys.stdin:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        lines.append(line.split())

    if not lines:
        print("No data read from stdin. Pipe convergence output to this script.", file=sys.stderr)
        sys.exit(1)

    data = np.array(lines, dtype=float)
    N    = data[:, 0].astype(int)
    dx   = data[:, 1]
    # Columns: N, dx, L1_rho, L2_rho, Linf_rho, L1_u, L2_u, Linf_u, L1_p, L2_p, Linf_p
    L1_rho = data[:, 2]

    # Compute convergence order between successive resolutions
    print("Convergence orders (L1_rho):")
    for i in range(1, len(N)):
        order = np.log(L1_rho[i-1] / L1_rho[i]) / np.log(dx[i-1] / dx[i])
        print(f"  N={N[i-1]:4d} -> {N[i]:4d}:  p = {order:.3f}")

    # Fit global slope
    coeffs = np.polyfit(np.log(dx), np.log(L1_rho), 1)
    slope = coeffs[0]
    print(f"\nGlobal fit: L1_rho ~ dx^{slope:.3f}")

    # Plot
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.loglog(dx, L1_rho, 'bo-', label=f'L1 rho (slope={slope:.2f})')

    # Reference lines
    dx_ref = np.array([dx[0], dx[-1]])
    ax.loglog(dx_ref, L1_rho[0] * (dx_ref / dx[0])**1, 'k--', alpha=0.3, label='O(1)')
    ax.loglog(dx_ref, L1_rho[0] * (dx_ref / dx[0])**2, 'k:',  alpha=0.3, label='O(2)')

    ax.set_xlabel('dx')
    ax.set_ylabel('L1 error (density)')
    ax.set_title('Grid Convergence — Sod Shock Tube')
    ax.legend()
    ax.grid(True, which='both', alpha=0.3)

    plt.tight_layout()
    plt.savefig('output/convergence_sod.png', dpi=150)
    print(f"\nPlot saved to output/convergence_sod.png")
    plt.show()

if __name__ == '__main__':
    main()
