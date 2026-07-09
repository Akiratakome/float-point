# Orszag-Tang Precision Smoke Summary

- Experiment: week15-mhd-orszag-tang-precision-smoke
- Case: orszag_tang.cfg
- Solver: hlld
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
| cpu-double-O2-ieee-leq | True | 812 | 24.45 | 0.0 | 0.0 | 3.0943291535107835e-13 | 30.490584400016814 |
| cpu-double-O2-ieee-strict | True | 812 | 24.45 | 0.0 | 0.0 | 3.0943291535107835e-13 | 30.93128649983555 |
| cpu-double-Ofast-ieee-leq | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 31.33050200017169 |
| cpu-double-Ofast-ieee-strict | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 31.307897799881175 |
| cpu-float-O2-ieee-leq | True | 812 | 24.45 | 0.0002854978853115142 | 0.003121124636215278 | 2.2795131744704374e-05 | 26.286802500020713 |
| cpu-float-O2-ieee-strict | True | 812 | 24.45 | 0.00028466342028465874 | 0.0031201709618988716 | 9.937520198211786e-05 | 26.71901150001213 |
| cpu-float-Ofast-ieee-leq | True | 812 | 24.45 | 0.0002863323502986237 | 0.0031130184045258247 | 4.1973820647210925e-05 | 26.379992899950594 |
| cpu-float-Ofast-ieee-strict | True | 812 | 24.45 | 0.0002862131410488189 | 0.003114448916746504 | 0.00015108269390253792 | 26.527425999986008 |

## Comparison Focus

Use Linf(By) and Linf(rho) for deterministic comparison language. L1/L2 row values, where present, are same-grid proxy norms, not strict 2D area-integral norms.

## Figures

- figures/reference_fields.png
- figures/drift_fields.png

## MCA Note

Docker Verificarlo is required separately for MCA evidence; this helper only summarises deterministic smoke rows.
