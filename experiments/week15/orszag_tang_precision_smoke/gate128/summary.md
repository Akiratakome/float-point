# Orszag-Tang Precision Smoke Summary

- Experiment: week15-mhd-orszag-tang-precision-smoke
- Case: orszag_tang.cfg
- Solver: hll
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
| cpu-double-O2-ieee-leq | True | 76 | 1.173 | 0.0 | 0.0 | 1.1976894932717111e-15 | 0.5908564000856131 |
| cpu-double-O2-ieee-strict | True | 76 | 1.173 | 0.0 | 0.0 | 1.1976894932717111e-15 | 0.5843084999360144 |
| cpu-double-Ofast-ieee-leq | True | 76 | 1.173 | 1.1379786002407855e-15 | 7.105427357601002e-15 | 1.0646128829081876e-15 | 0.5935498999897391 |
| cpu-double-Ofast-ieee-strict | True | 76 | 1.173 | 1.1379786002407855e-15 | 7.105427357601002e-15 | 1.0646128829081876e-15 | 0.5897991999518126 |
| cpu-float-O2-ieee-leq | True | 76 | 1.173 | 1.8420339669214525e-06 | 3.3284610720940577e-06 | 7.858945923879107e-07 | 0.49278769991360605 |
| cpu-float-O2-ieee-strict | True | 76 | 1.173 | 1.8420339669214525e-06 | 3.3284610720940577e-06 | 7.858945923879107e-07 | 0.4787308999802917 |
| cpu-float-Ofast-ieee-leq | True | 76 | 1.173 | 1.9558329736879543e-06 | 3.4432778175386147e-06 | 7.144496294435552e-07 | 0.4868003998417407 |
| cpu-float-Ofast-ieee-strict | True | 76 | 1.173 | 1.9558329736879543e-06 | 3.4432778175386147e-06 | 7.144496294435552e-07 | 0.48638550005853176 |

## Comparison Focus

Use Linf(By) and Linf(rho) for deterministic comparison language. L1/L2 row values, where present, are same-grid proxy norms, not strict 2D area-integral norms.

## Figures

- figures/reference_fields.png
- figures/drift_fields.png

## MCA Note

Docker Verificarlo is required separately for MCA evidence; this helper only summarises deterministic smoke rows.
