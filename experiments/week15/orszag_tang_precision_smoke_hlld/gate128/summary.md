# Orszag-Tang Precision Smoke Summary

- Experiment: week15-mhd-orszag-tang-precision-smoke
- Case: orszag_tang.cfg
- Solver: hlld
- Profile: gate
- Reference: cpu-double-O2-ieee-leq
- Git commit: cf75613b1d57b1d125cc428bfae1698e2469a3e9

## Gate G0

- Pass: True
- Steps exact: True
- divB tolerance: True

## Deterministic Rows

| variant | finite | steps | divB_max | Linf_By | Linf_rho | symmetry_residual_rho | walltime_s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cpu-double-O2-ieee-leq | True | 76 | 1.085 | 0.0 | 0.0 | 2.0165744833834902e-15 | 0.6489174000453204 |
| cpu-double-O2-ieee-strict | True | 76 | 1.085 | 0.0 | 0.0 | 2.0165744833834902e-15 | 0.6558856999035925 |
| cpu-double-Ofast-ieee-leq | True | 76 | 1.085 | 2.4424906541753444e-15 | 1.2878587085651816e-14 | 2.079592435989226e-15 | 0.6387768001295626 |
| cpu-double-Ofast-ieee-strict | True | 76 | 1.085 | 2.4424906541753444e-15 | 1.2878587085651816e-14 | 2.079592435989226e-15 | 0.6409106000792235 |
| cpu-float-O2-ieee-leq | True | 76 | 1.085 | 1.8534660023716842e-06 | 1.6498294719280437e-05 | 2.2667767530743923e-06 | 0.5761448999401182 |
| cpu-float-O2-ieee-strict | True | 76 | 1.085 | 1.8534660023716842e-06 | 1.6498294719280437e-05 | 2.2667767530743923e-06 | 0.5670038000680506 |
| cpu-float-Ofast-ieee-leq | True | 76 | 1.085 | 1.7618332145974414e-06 | 1.091984187739925e-05 | 1.5224617922988605e-06 | 0.5617338998708874 |
| cpu-float-Ofast-ieee-strict | True | 76 | 1.085 | 1.7618332145974414e-06 | 1.091984187739925e-05 | 1.5224617922988605e-06 | 0.5615296999458224 |

## Comparison Focus

Use Linf(By) and Linf(rho) for deterministic comparison language. L1/L2 row values, where present, are same-grid proxy norms, not strict 2D area-integral norms.

## Figures

- figures/reference_fields.png
- figures/drift_fields.png

## MCA Note

Docker Verificarlo is required separately for MCA evidence; this helper only summarises deterministic smoke rows.
