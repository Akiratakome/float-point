# Orszag-Tang Precision Smoke Summary

- Experiment: week15-mhd-orszag-tang-precision-smoke
- Case: orszag_tang.cfg
- Solver: hlld
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
| cpu-double-O2-ieee-leq | True | 812 | 24.45 | 0.0 | 0.0 | 3.0943291535107835e-13 | 28.32373079995159 |
| cpu-double-O2-ieee-strict | True | 812 | 24.45 | 0.0 | 0.0 | 3.0943291535107835e-13 | 28.031519199954346 |
| cpu-double-O2-fastmath-leq | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 27.7845810999861 |
| cpu-double-O2-fastmath-strict | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 27.622609699959867 |
| cpu-double-O3-ieee-leq | True | 812 | 24.45 | 0.0 | 0.0 | 3.0943291535107835e-13 | 28.230046099983156 |
| cpu-double-O3-ieee-strict | True | 812 | 24.45 | 0.0 | 0.0 | 3.0943291535107835e-13 | 28.027174800052308 |
| cpu-double-O3-fastmath-leq | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 27.84182359999977 |
| cpu-double-O3-fastmath-strict | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 27.650727900094353 |
| cpu-double-Ofast-ieee-leq | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 27.702567199943587 |
| cpu-double-Ofast-ieee-strict | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 27.919191899942234 |
| cpu-double-Ofast-fastmath-leq | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 28.024547399953008 |
| cpu-double-Ofast-fastmath-strict | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 27.805404099985026 |
| cpu-float-O2-ieee-leq | True | 812 | 24.45 | 0.0002854978853115142 | 0.003121124636215278 | 2.2795131744704374e-05 | 24.25106409995351 |
| cpu-float-O2-ieee-strict | True | 812 | 24.45 | 0.00028466342028465874 | 0.0031201709618988716 | 9.937520198211786e-05 | 24.233459200011566 |
| cpu-float-O2-fastmath-leq | True | 812 | 24.45 | 0.0002863323502986237 | 0.0031130184045258247 | 4.1973820647210925e-05 | 24.45698880008422 |
| cpu-float-O2-fastmath-strict | True | 812 | 24.45 | 0.0002862131410488189 | 0.003114448916746504 | 0.00015108269390253792 | 24.121171699953265 |
| cpu-float-O3-ieee-leq | True | 812 | 24.45 | 0.0002854978853115142 | 0.003121124636215278 | 2.2795131744704374e-05 | 24.307312400080264 |
| cpu-float-O3-ieee-strict | True | 812 | 24.45 | 0.00028466342028465874 | 0.0031201709618988716 | 9.937520198211786e-05 | 24.416844200110063 |
| cpu-float-O3-fastmath-leq | True | 812 | 24.45 | 0.0002863323502986237 | 0.0031130184045258247 | 4.1973820647210925e-05 | 24.012921100016683 |
| cpu-float-O3-fastmath-strict | True | 812 | 24.45 | 0.0002862131410488189 | 0.003114448916746504 | 0.00015108269390253792 | 24.056443299981765 |
| cpu-float-Ofast-ieee-leq | True | 812 | 24.45 | 0.0002863323502986237 | 0.0031130184045258247 | 4.1973820647210925e-05 | 23.94842609995976 |
| cpu-float-Ofast-ieee-strict | True | 812 | 24.45 | 0.0002862131410488189 | 0.003114448916746504 | 0.00015108269390253792 | 24.116911300108768 |
| cpu-float-Ofast-fastmath-leq | True | 812 | 24.45 | 0.0002863323502986237 | 0.0031130184045258247 | 4.1973820647210925e-05 | 24.089376299991272 |
| cpu-float-Ofast-fastmath-strict | True | 812 | 24.45 | 0.0002862131410488189 | 0.003114448916746504 | 0.00015108269390253792 | 24.304439999978058 |

## Comparison Focus

Use Linf(By) and Linf(rho) for deterministic comparison language. L1/L2 row values, where present, are same-grid proxy norms, not strict 2D area-integral norms.

## Figures

- figures/reference_fields.png
- figures/drift_fields.png

## MCA Note

Docker Verificarlo is required separately for MCA evidence; this helper only summarises deterministic smoke rows.
