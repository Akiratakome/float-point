# Week 18 OT/KH three-resolution diagnostic

Full-matrix gate pass: `True`. Attempted runs: `24/24`; complete three-grid groups: `8/8`; same-grid fp32--fp64 cells: `12/12`.

HLL uses CFL=0.4 and HLLD uses CFL=0.2. Solver-to-solver timing or error comparisons are therefore excluded; each resolution ladder is interpreted only within a fixed solver, precision, and CFL.

| case | solver | precision | L1 128-256 | L1 256-512 | observed p |
|---|---|---|---:|---:|---:|
| Orszag-Tang | HLL | FP64 | 1.203e-01 | 7.722e-02 | 0.639 |
| Orszag-Tang | HLL | FP32 | 1.203e-01 | 7.722e-02 | 0.639 |
| Orszag-Tang | HLLD | FP64 | 7.515e-02 | 4.182e-02 | 0.846 |
| Orszag-Tang | HLLD | FP32 | 7.515e-02 | 4.181e-02 | 0.846 |
| Kelvin-Helmholtz | HLL | FP64 | 3.473e-03 | 1.836e-03 | 0.919 |
| Kelvin-Helmholtz | HLL | FP32 | 3.473e-03 | 1.837e-03 | 0.919 |
| Kelvin-Helmholtz | HLLD | FP64 | 2.309e-04 | 8.496e-05 | 1.442 |
| Kelvin-Helmholtz | HLLD | FP32 | 2.308e-04 | 8.527e-05 | 1.436 |

## Same-grid fp32--fp64 density separation

These values compare matched outputs at one grid and are not discretisation errors or accuracy measures.

| case | solver | N | mean L1 | mean L2 | Linf |
|---|---|---:|---:|---:|---:|
| Orszag-Tang | HLL | 128 | 3.825e-07 | 5.084e-07 | 3.565e-06 |
| Orszag-Tang | HLL | 256 | 7.896e-07 | 1.122e-06 | 9.887e-06 |
| Orszag-Tang | HLL | 512 | 9.080e-06 | 1.383e-05 | 1.676e-04 |
| Orszag-Tang | HLLD | 128 | 2.147e-06 | 1.377e-05 | 6.687e-04 |
| Orszag-Tang | HLLD | 256 | 1.127e-05 | 1.508e-04 | 2.596e-02 |
| Orszag-Tang | HLLD | 512 | 5.554e-05 | 4.833e-04 | 5.031e-02 |
| Kelvin-Helmholtz | HLL | 128 | 1.357e-07 | 1.709e-07 | 7.066e-07 |
| Kelvin-Helmholtz | HLL | 256 | 2.877e-07 | 3.894e-07 | 1.786e-06 |
| Kelvin-Helmholtz | HLL | 512 | 8.498e-07 | 1.138e-06 | 4.400e-06 |
| Kelvin-Helmholtz | HLLD | 128 | 5.536e-07 | 7.047e-07 | 3.630e-06 |
| Kelvin-Helmholtz | HLLD | 256 | 1.078e-06 | 1.367e-06 | 7.204e-06 |
| Kelvin-Helmholtz | HLLD | 512 | 2.348e-06 | 2.979e-06 | 1.461e-05 |

## Claim boundary

Three resolutions expose the direction of self-convergence, but do not by themselves prove an asymptotic convergence regime for discontinuous MHD solutions.

Positive observed order is reported as evidence, not used as a pass/fail requirement. All eight groups are complete, but they remain bounded subgroup diagnostics rather than proof of an asymptotic regime.
