# Orszag-Tang Precision Smoke Summary

- Experiment: week15-mhd-orszag-tang-precision-smoke
- Case: orszag_tang.cfg
- Solver: hll
- Profile: headline
- Reference: cpu-double-O2-ieee-leq
- Git commit: 4d9697b933f5fa3e12164a3b05b814a7a191073c

## Gate G0

- Pass: True
- Steps exact: True
- divB tolerance: True

## Deterministic Rows

| variant | finite | steps | divB_max | Linf_By | Linf_rho | symmetry_residual_rho | walltime_s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cpu-double-O2-ieee-leq | True | 806 | 3.72 | 0.0 | 0.0 | 6.396578710446008e-15 | 29.02416479983367 |
| cpu-double-O2-ieee-strict | True | 806 | 3.72 | 0.0 | 0.0 | 6.396578710446008e-15 | 28.92883780016564 |
| cpu-double-O2-fastmath-leq | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 29.558151500066742 |
| cpu-double-O2-fastmath-strict | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 29.027227600105107 |
| cpu-double-O3-ieee-leq | True | 806 | 3.72 | 0.0 | 0.0 | 6.396578710446008e-15 | 28.030381799908355 |
| cpu-double-O3-ieee-strict | True | 806 | 3.72 | 0.0 | 0.0 | 6.396578710446008e-15 | 27.271507899975404 |
| cpu-double-O3-fastmath-leq | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 27.298498600022867 |
| cpu-double-O3-fastmath-strict | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 24.87022909987718 |
| cpu-double-Ofast-ieee-leq | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 24.650448200060055 |
| cpu-double-Ofast-ieee-strict | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 24.705268600024283 |
| cpu-double-Ofast-fastmath-leq | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 24.972059899941087 |
| cpu-double-Ofast-fastmath-strict | True | 806 | 3.72 | 8.382183835919932e-15 | 2.2648549702353193e-14 | 4.992451676445663e-15 | 24.733257499989122 |
| cpu-float-O2-ieee-leq | True | 806 | 3.72 | 4.9307928153830005e-06 | 9.886709070094923e-06 | 2.261504651077473e-06 | 20.36847299989313 |
| cpu-float-O2-ieee-strict | True | 806 | 3.72 | 4.9307928153830005e-06 | 9.886709070094923e-06 | 2.261504651077473e-06 | 20.535402899840847 |
| cpu-float-O2-fastmath-leq | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 21.165519300149754 |
| cpu-float-O2-fastmath-strict | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 21.197678299853578 |
| cpu-float-O3-ieee-leq | True | 806 | 3.72 | 4.9307928153830005e-06 | 9.886709070094923e-06 | 2.261504651077473e-06 | 19.9884065000806 |
| cpu-float-O3-ieee-strict | True | 806 | 3.72 | 4.9307928153830005e-06 | 9.886709070094923e-06 | 2.261504651077473e-06 | 20.80406180000864 |
| cpu-float-O3-fastmath-leq | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 21.502282599918544 |
| cpu-float-O3-fastmath-strict | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 22.603671100223437 |
| cpu-float-Ofast-ieee-leq | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 21.793686899822205 |
| cpu-float-Ofast-ieee-strict | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 21.65026229992509 |
| cpu-float-Ofast-fastmath-leq | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 21.006290199933574 |
| cpu-float-Ofast-fastmath-strict | True | 806 | 3.72 | 7.513932155311931e-06 | 1.6856194211545272e-05 | 2.8059407209424944e-06 | 20.71669919998385 |

## Comparison Focus

Use Linf(By) and Linf(rho) for deterministic comparison language. L1/L2 row values, where present, are same-grid proxy norms, not strict 2D area-integral norms.

## Figures

- figures/reference_fields.png
- figures/drift_fields.png

## MCA Note

Docker Verificarlo is required separately for MCA evidence; this helper only summarises deterministic smoke rows.
