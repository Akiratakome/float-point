# Orszag-Tang Precision Smoke Summary

- Experiment: week15-mhd-orszag-tang-precision-smoke
- Case: orszag_tang.cfg
- Solver: hll
- Profile: headline
- Reference: cpu-double-O2-ieee-leq
- Git commit: 0fe1239a942e852c092eec9a0ab9849bbbc71dfd

## Gate G0

- Pass: True
- Steps exact: True
- divB tolerance: True

## Deterministic Rows

| variant | finite | steps | divB_max | Linf_By | Linf_rho | symmetry_residual_rho | walltime_s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cpu-double-O2-ieee-leq | True | 806 | 3.72 | 0.0 | 0.0 | 6.396578710446008e-15 | 24.30936030007433 |
| cpu-double-O2-ieee-strict | True | 806 | 3.72 | 0.0 | 0.0 | 6.396578710446008e-15 | 24.338131699943915 |
| cpu-double-O2-fastmath-leq | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 24.631744600017555 |
| cpu-double-O2-fastmath-strict | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 24.775152300018817 |
| cpu-double-O3-ieee-leq | True | 806 | 3.72 | 0.0 | 0.0 | 6.396578710446008e-15 | 24.556581199984066 |
| cpu-double-O3-ieee-strict | True | 806 | 3.72 | 0.0 | 0.0 | 6.396578710446008e-15 | 24.60465110000223 |
| cpu-double-O3-fastmath-leq | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 24.862101300037466 |
| cpu-double-O3-fastmath-strict | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 24.78570090001449 |
| cpu-double-Ofast-ieee-leq | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 24.849074300029315 |
| cpu-double-Ofast-ieee-strict | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 24.795642699929886 |
| cpu-double-Ofast-fastmath-leq | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 24.766620000009425 |
| cpu-double-Ofast-fastmath-strict | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 24.840118799940683 |
| cpu-float-O2-ieee-leq | True | 806 | 3.72 | 4.9307928153830005e-06 | 9.886709070094923e-06 | 2.261504651077473e-06 | 20.12237490003463 |
| cpu-float-O2-ieee-strict | True | 806 | 3.72 | 4.9307928153830005e-06 | 9.886709070094923e-06 | 2.261504651077473e-06 | 20.084605799987912 |
| cpu-float-O2-fastmath-leq | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 20.377555800019763 |
| cpu-float-O2-fastmath-strict | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 20.276315800030716 |
| cpu-float-O3-ieee-leq | True | 806 | 3.72 | 4.9307928153830005e-06 | 9.886709070094923e-06 | 2.261504651077473e-06 | 20.067536500049755 |
| cpu-float-O3-ieee-strict | True | 806 | 3.72 | 4.9307928153830005e-06 | 9.886709070094923e-06 | 2.261504651077473e-06 | 20.07991299999412 |
| cpu-float-O3-fastmath-leq | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 20.25026339991018 |
| cpu-float-O3-fastmath-strict | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 20.129501799936406 |
| cpu-float-Ofast-ieee-leq | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 20.224679799983278 |
| cpu-float-Ofast-ieee-strict | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 20.264231399982236 |
| cpu-float-Ofast-fastmath-leq | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 20.259403600008227 |
| cpu-float-Ofast-fastmath-strict | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 20.250655599986203 |

## Comparison Focus

Use Linf(By) and Linf(rho) for deterministic comparison language. L1/L2 row values, where present, are same-grid proxy norms, not strict 2D area-integral norms.

## Figures

- figures/reference_fields.png
- figures/drift_fields.png

## MCA Note

Docker Verificarlo is required separately for MCA evidence; this helper only summarises deterministic smoke rows.
