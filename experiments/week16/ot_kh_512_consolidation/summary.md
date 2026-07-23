# Week 16 OT/KH 512^2 Consolidation

This packet consolidates the completed 256^2 candidate vs 512^2 double-reference gates for the 2D MHD benchmarks.

| case | authority | L1(rho) | Linf(rho) | mass_rel | divB_max | gate pass? |
|---|---|---:|---:|---:|---:|---:|
| orszag_tang | `experiments/week13/orszag_tang/summary.json` | 7.722e-02 | 6.459e-01 | 0.000e+00 | 3.720e+00 | True |
| kelvin_helmholtz | `experiments/week16/kelvin_helmholtz_precision/validation/summary.json` | 1.836e-03 | 6.376e-03 | 0.000e+00 | 6.714e-04 | True |

## Claim boundary

The two-resolution gates support bounded engineering sensitivity checks; they do not establish asymptotic convergence.

All 512 gates pass: `True`.
Asymptotic convergence claim: `False`.
