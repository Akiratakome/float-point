# Week 12 Brio-Wu 1D Validation

Density errors compare each candidate against a block-averaged aligned N=8000 double reference.

| N | reference N | L1(rho) | L2(rho) | Linf(rho) |
|---:|---:|---:|---:|---:|
| 200 | 8000 | 1.480554e-02 | 3.641584e-02 | 2.083493e-01 |
| 400 | 8000 | 9.463267e-03 | 2.713726e-02 | 1.914836e-01 |
| 800 | 8000 | 5.641658e-03 | 1.923045e-02 | 1.546849e-01 |

## Monotonic convergence

Strictly decreasing L1 and L2 over N=[200, 400, 800]: True

| metric | strictly decreasing | values |
|---|---:|---|
| L1 | True | 1.480554e-02, 9.463267e-03, 5.641658e-03 |
| L2 | True | 3.641584e-02, 2.713726e-02, 1.923045e-02 |

## Run metadata

| N | steps | divB_mean | divB_max | elapsed wall s |
|---:|---:|---:|---:|---:|
| 8000 | 7604 | 5.908e-14 | 1.776e-12 | 9.931 |
| 200 | 189 | 0.000e+00 | 0.000e+00 | 0.018 |
| 400 | 379 | 0.000e+00 | 0.000e+00 | 0.037 |
| 800 | 759 | 3.339e-16 | 4.441e-14 | 0.096 |

Generated cfgs, stdout/stderr, and per-run metadata live under `experiments/week12/brio_wu_1d/runs/`.
