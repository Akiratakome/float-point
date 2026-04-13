#!/usr/bin/env python3
"""
Load binary output files and compute error norms against exact Riemann solutions.
Usage: python analysis/compare.py output/sod.bin --gamma 1.4 --x0 0.5 --t-end 0.25 \
       --rhoL 1.0 --uL 0.0 --pL 1.0 --rhoR 0.125 --uR 0.0 --pR 0.1
"""
import argparse
import struct
import numpy as np
import sys
from pathlib import Path

# Add project root so we can import from scripts
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.verify_toro import exact_riemann


def read_binary(filename):
    """Read binary file with 64-byte HRSC header."""
    with open(filename, 'rb') as f:
        header = f.read(64)
        magic = header[0:4].decode('ascii')
        if magic != 'HRSC':
            raise ValueError(f"Bad magic: {magic!r}, expected 'HRSC'")
        nx, ny, nvars, prec_tag = struct.unpack('<4i', header[4:20])
        time, dx, dy = struct.unpack('<3d', header[20:44])
        dtype = '<f4' if prec_tag == 4 else '<f8'
        data = np.fromfile(f, dtype=dtype).reshape(ny, nx, nvars)
    return data, nx, ny, nvars, time, dx, dy


def compute_norms(numerical, exact, dx):
    """Compute L1, L2, Linf error norms."""
    diff = np.abs(numerical - exact)
    L1 = np.sum(diff) * dx
    L2 = np.sqrt(np.sum(diff**2) * dx)
    Linf = np.max(diff)
    return L1, L2, Linf


def main():
    parser = argparse.ArgumentParser(description="Compare binary output to exact Riemann solution")
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
    args = parser.parse_args()

    data, nx, ny, nvars, time, dx, dy = read_binary(args.binfile)

    # Extract 1D slice (row 0 for 1D data)
    rho_num = data[0, :, 0]
    # cons_to_prim: rhou/rho = u, p = (gamma-1)*(E - 0.5*rho*(u^2+v^2))
    rhou = data[0, :, 1]
    rhov = data[0, :, 2]
    E    = data[0, :, 3]
    rho  = data[0, :, 0]
    u_num = rhou / rho
    v_num = rhov / rho
    p_num = (args.gamma - 1.0) * (E - 0.5 * rho * (u_num**2 + v_num**2))

    # Cell centers
    x = np.array([(i + 0.5) * dx for i in range(nx)])

    # Exact solution
    rho_ex, u_ex, p_ex, _ = exact_riemann(
        x, args.t_end, args.gamma, args.x0,
        args.rhoL, args.uL, args.pL,
        args.rhoR, args.uR, args.pR)

    # Compute norms
    print(f"{'Variable':>8s}  {'L1':>12s}  {'L2':>12s}  {'Linf':>12s}")
    print(f"{'--------':>8s}  {'---':>12s}  {'---':>12s}  {'----':>12s}")
    for name, num, ex in [("rho", rho_num, rho_ex),
                           ("u", u_num, u_ex),
                           ("p", p_num, p_ex)]:
        L1, L2, Linf = compute_norms(num, ex, dx)
        print(f"{name:>8s}  {L1:12.6e}  {L2:12.6e}  {Linf:12.6e}")


if __name__ == "__main__":
    main()
