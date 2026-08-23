# Week 18 Euler--MHD cross-system sensitivity

Gate pass: `True`. Completed runs: `16/16`.

| system | dimension | case | comparison | relative L1(rho) | Linf(rho) |
|---|---|---|---|---:|---:|
| Euler | 1D | Sod | FP32 vs FP64 / O2-default | 1.466e-07 | 3.837e-07 |
| Euler | 1D | Sod | FP32 vs FP64 / Ofast-fast | 1.466e-07 | 3.837e-07 |
| Euler | 1D | Sod | Ofast-fast vs O2-default / FP64 | 4.244e-17 | 7.494e-16 |
| Euler | 1D | Sod | Ofast-fast vs O2-default / FP32 | 0.000e+00 | 0.000e+00 |
| Euler | 2D | LW3 | FP32 vs FP64 / O2-default | 3.762e-07 | 5.254e-06 |
| Euler | 2D | LW3 | FP32 vs FP64 / Ofast-fast | 3.786e-07 | 7.058e-06 |
| Euler | 2D | LW3 | Ofast-fast vs O2-default / FP64 | 7.227e-17 | 5.773e-15 |
| Euler | 2D | LW3 | Ofast-fast vs O2-default / FP32 | 5.124e-07 | 5.245e-06 |
| ideal MHD | 1D | Brio-Wu | FP32 vs FP64 / O2-default | 1.401e-07 | 1.075e-06 |
| ideal MHD | 1D | Brio-Wu | FP32 vs FP64 / Ofast-fast | 1.657e-07 | 9.291e-07 |
| ideal MHD | 1D | Brio-Wu | Ofast-fast vs O2-default / FP64 | 4.215e-16 | 1.887e-15 |
| ideal MHD | 1D | Brio-Wu | Ofast-fast vs O2-default / FP32 | 2.091e-07 | 1.311e-06 |
| ideal MHD | 2D | Orszag-Tang | FP32 vs FP64 / O2-default | 1.377e-07 | 3.565e-06 |
| ideal MHD | 2D | Orszag-Tang | FP32 vs FP64 / Ofast-fast | 1.382e-07 | 3.327e-06 |
| ideal MHD | 2D | Orszag-Tang | Ofast-fast vs O2-default / FP64 | 3.043e-16 | 5.773e-15 |
| ideal MHD | 2D | Orszag-Tang | Ofast-fast vs O2-default / FP32 | 1.519e-07 | 2.384e-06 |

## Claim boundary

This packet compares bounded density-discrepancy sensitivity across selected Euler/HLLC and ideal-MHD/HLL cases. Different physical systems and Riemann solvers prevent a universal method ranking, and no cross-system accuracy claim is made.
