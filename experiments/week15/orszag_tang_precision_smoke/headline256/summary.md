# Orszag-Tang Precision Smoke Summary

- Experiment: week15-mhd-orszag-tang-precision-smoke
- Case: orszag_tang.cfg
- Solver: hll
- Profile: headline
- Reference: cpu-double-O2-ieee-leq
- Git commit: cf75613b1d57b1d125cc428bfae1698e2469a3e9

## Gate G0

- Pass: True
- Steps exact: True
- divB tolerance: True

## Deterministic Rows

| variant | finite | steps | divB_max | Linf_By | Linf_rho | symmetry_residual_rho | walltime_s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cpu-double-O2-ieee-leq | True | 806 | 3.72 | 0.0 | 0.0 | 6.396578710446008e-15 | 27.18837170000188 |
| cpu-double-O2-ieee-strict | True | 806 | 3.72 | 0.0 | 0.0 | 6.396578710446008e-15 | 27.37606310006231 |
| cpu-double-Ofast-ieee-leq | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 28.435362699907273 |
| cpu-double-Ofast-ieee-strict | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 28.291941199917346 |
| cpu-float-O2-ieee-leq | True | 806 | 3.72 | 4.9307928153830005e-06 | 9.886709070094923e-06 | 2.261504651077473e-06 | 22.610068100038916 |
| cpu-float-O2-ieee-strict | True | 806 | 3.72 | 4.9307928153830005e-06 | 9.886709070094923e-06 | 2.261504651077473e-06 | 22.52611649991013 |
| cpu-float-Ofast-ieee-leq | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 23.909954800037667 |
| cpu-float-Ofast-ieee-strict | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 24.12741980003193 |

## Comparison Focus

Use Linf(By) and Linf(rho) for deterministic comparison language. L1/L2 row values, where present, are same-grid proxy norms, not strict 2D area-integral norms.

## Figures

- figures/reference_fields.png
- figures/drift_fields.png

## MCA Note

Docker Verificarlo is required separately for MCA evidence; this helper only summarises deterministic smoke rows.
