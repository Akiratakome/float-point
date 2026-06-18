# Week 12 div(B) Cleaning Decay Validation

128x128 doubly-periodic Gaussian Bx bump. GLM glm_cr sweep.
Values are `divB_max` at the stated `t_end`.

## Decay table (divB_max)

| t_end | cr=0.0 | cr=0.18 | cr=0.36 |
|---:|:---:|:---:|:---:|
| 0.05 | 2.977e+00 | 2.526e+00 | 2.548e+00 |
| 0.1 | 4.435e+00 | 2.440e+00 | 3.310e+00 |
| 0.2 | 2.994e+00 | 1.062e+00 | 1.836e+00 |
| 0.35 | 2.977e+00 | 6.644e-01 | 1.429e+00 |
| 0.5 | 3.030e+00 | 2.678e-01 | 8.429e-01 |

## Gate results

| check | value | pass? |
|---|---:|---:|
| divB_max(cr=0.00, t=0.5) control | 3.030e+00 | n/a |
| divB_max(cr=0.18, t=0.5) <= control*1.02 | 2.678e-01 | True |
| divB_max(cr=0.36, t=0.5) <= control*1.02 | 8.429e-01 | True |
| cr=0.18 <= cr=0.36*1.02 | True | True |
| cr=0.36 < cr=0.18 (informational) | False | n/a |

## Figure grids

- `cr0.0_t0.5`: `C:\Users\tangy\Desktop\floatpoint\experiments\week12\mhd_2d\divb_clean\divb_blob_cr0p00_t0p5.bin`
- `cr0.18_t0.5`: `C:\Users\tangy\Desktop\floatpoint\experiments\week12\mhd_2d\divb_clean\divb_blob_cr0p18_t0p5.bin`

Generated cfgs, stdout/stderr, and per-run metadata live under `experiments/week12/mhd_2d/divb_clean/runs/`.
