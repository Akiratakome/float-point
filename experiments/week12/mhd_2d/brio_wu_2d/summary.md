# Week 12 Brio-Wu 2D Transverse-Invariance Validation

800x4 grid, outflow-x, periodic-y, glm_cr=0.18, t_end=0.1.

## Results

| metric | value | gate | pass? |
|---|---:|---|---:|
| max_transverse_dev | 0.000e+00 | <= 1e-12 | True |
| divB_max (2D) | 0.000e+00 | <= 1e-10 | True |
| mean_abs_rho_diff_vs_1d | 3.550e-04 | < 1e-3 | True |
| max_abs_rho_diff_vs_1d | 7.034e-03 | < 1e-2 | True |

## Diagnostics

- 2D run elapsed: 1.30s
- 1D ref elapsed: 0.16s
- 2D steps: 861
- 2D grid shape: ny=4, nx=800, nvars=9

Generated cfgs, stdout/stderr, and per-run metadata live under `experiments/week12/mhd_2d/brio_wu_2d/runs/`.
