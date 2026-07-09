# Orszag-Tang Precision Smoke Summary

- Experiment: week15-mhd-orszag-tang-precision-smoke
- Case: orszag_tang.cfg
- Solver: hlld
- Profile: headline
- Reference: cpu-double-O2-ieee-leq
- Git commit: 0221e05cc75394ac76f1d79afbc53cdd30550177

## Gate G0

- Pass: True
- Steps exact: True
- divB tolerance: True

## Deterministic Rows

| variant | finite | steps | divB_max | Linf_By | Linf_rho | symmetry_residual_rho | walltime_s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cpu-double-O2-ieee-leq | True | 812 | 24.45 | 0.0 | 0.0 | 3.0943291535107835e-13 | 33.194132399978116 |
| cpu-double-O2-ieee-strict | True | 812 | 24.45 | 0.0 | 0.0 | 3.0943291535107835e-13 | 31.850867199944332 |
| cpu-double-O2-fastmath-leq | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 28.7960520000197 |
| cpu-double-O2-fastmath-strict | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 27.72948129987344 |
| cpu-double-O3-ieee-leq | True | 812 | 24.45 | 0.0 | 0.0 | 3.0943291535107835e-13 | 27.863289899891242 |
| cpu-double-O3-ieee-strict | True | 812 | 24.45 | 0.0 | 0.0 | 3.0943291535107835e-13 | 27.4700401998125 |
| cpu-double-O3-fastmath-leq | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 27.50049120001495 |
| cpu-double-O3-fastmath-strict | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 27.27204760001041 |
| cpu-double-Ofast-ieee-leq | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 27.35147750005126 |
| cpu-double-Ofast-ieee-strict | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 29.48773799999617 |
| cpu-double-Ofast-fastmath-leq | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 27.369145200122148 |
| cpu-double-Ofast-fastmath-strict | True | 812 | 24.45 | 4.5469183973523286e-13 | 8.836043008386696e-12 | 6.151394500633748e-13 | 29.600302799837664 |
| cpu-float-O2-ieee-leq | True | 812 | 24.45 | 0.0002854978853115142 | 0.003121124636215278 | 2.2795131744704374e-05 | 27.14918849989772 |
| cpu-float-O2-ieee-strict | True | 812 | 24.45 | 0.00028466342028465874 | 0.0031201709618988716 | 9.937520198211786e-05 | 27.997711200034246 |
| cpu-float-O2-fastmath-leq | True | 812 | 24.45 | 0.0002863323502986237 | 0.0031130184045258247 | 4.1973820647210925e-05 | 28.015396100003272 |
| cpu-float-O2-fastmath-strict | True | 812 | 24.45 | 0.0002862131410488189 | 0.003114448916746504 | 0.00015108269390253792 | 25.691856400109828 |
| cpu-float-O3-ieee-leq | True | 812 | 24.45 | 0.0002854978853115142 | 0.003121124636215278 | 2.2795131744704374e-05 | 26.652106400113553 |
| cpu-float-O3-ieee-strict | True | 812 | 24.45 | 0.00028466342028465874 | 0.0031201709618988716 | 9.937520198211786e-05 | 27.263946500141174 |
| cpu-float-O3-fastmath-leq | True | 812 | 24.45 | 0.0002863323502986237 | 0.0031130184045258247 | 4.1973820647210925e-05 | 27.765575000084937 |
| cpu-float-O3-fastmath-strict | True | 812 | 24.45 | 0.0002862131410488189 | 0.003114448916746504 | 0.00015108269390253792 | 27.403464500093833 |
| cpu-float-Ofast-ieee-leq | True | 812 | 24.45 | 0.0002863323502986237 | 0.0031130184045258247 | 4.1973820647210925e-05 | 27.16716090007685 |
| cpu-float-Ofast-ieee-strict | True | 812 | 24.45 | 0.0002862131410488189 | 0.003114448916746504 | 0.00015108269390253792 | 26.74815100012347 |
| cpu-float-Ofast-fastmath-leq | True | 812 | 24.45 | 0.0002863323502986237 | 0.0031130184045258247 | 4.1973820647210925e-05 | 26.657034799922258 |
| cpu-float-Ofast-fastmath-strict | True | 812 | 24.45 | 0.0002862131410488189 | 0.003114448916746504 | 0.00015108269390253792 | 26.216961900005117 |

## Comparison Focus

Use Linf(By) and Linf(rho) for deterministic comparison language. L1/L2 row values, where present, are same-grid proxy norms, not strict 2D area-integral norms.

## Figures

- figures/reference_fields.png
- figures/drift_fields.png

## MCA Note

Docker Verificarlo is required separately for MCA evidence; this helper only summarises deterministic smoke rows.
