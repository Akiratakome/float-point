# Week 16 Kelvin-Helmholtz Precision Packet

- Solver: `hlld`
- Phase: `p1`
- Mode: `deterministic-with-blocked-mca`
- Commit: `2082dd5e2825a42038c8e9ceb050092c6211adc8`
- Deterministic gate: `True`
- MCA gate: `blocked_environment`
- Report-grade gate: `False`

| variant | finite | steps | divB_max | Linf_rho | Linf_By | walltime_s |
|---|---|---:|---:|---:|---:|---:|
| cpu-double-O2-ieee-leq | True | 1148 | 4.228000e-03 | 0.000000e+00 | 0.000000e+00 | 38.755 |
| cpu-double-O2-ieee-strict | True | 1148 | 4.228000e-03 | 0.000000e+00 | 0.000000e+00 | 38.387 |
| cpu-double-O2-fastmath-leq | True | 1148 | 4.228000e-03 | 9.992007e-15 | 1.391248e-15 | 37.880 |
| cpu-double-O2-fastmath-strict | True | 1148 | 4.228000e-03 | 9.992007e-15 | 1.391248e-15 | 37.923 |
| cpu-double-O3-ieee-leq | True | 1148 | 4.228000e-03 | 0.000000e+00 | 0.000000e+00 | 38.664 |
| cpu-double-O3-ieee-strict | True | 1148 | 4.228000e-03 | 0.000000e+00 | 0.000000e+00 | 38.646 |
| cpu-double-O3-fastmath-leq | True | 1148 | 4.228000e-03 | 9.992007e-15 | 1.391248e-15 | 38.796 |
| cpu-double-O3-fastmath-strict | True | 1148 | 4.228000e-03 | 9.992007e-15 | 1.391248e-15 | 38.882 |
| cpu-double-Ofast-ieee-leq | True | 1148 | 4.228000e-03 | 9.992007e-15 | 1.391248e-15 | 38.918 |
| cpu-double-Ofast-ieee-strict | True | 1148 | 4.228000e-03 | 9.992007e-15 | 1.391248e-15 | 38.816 |
| cpu-double-Ofast-fastmath-leq | True | 1148 | 4.228000e-03 | 9.992007e-15 | 1.391248e-15 | 38.521 |
| cpu-double-Ofast-fastmath-strict | True | 1148 | 4.228000e-03 | 9.992007e-15 | 1.391248e-15 | 37.930 |
| cpu-float-O2-ieee-leq | True | 1148 | 4.233000e-03 | 3.230010e-06 | 5.035195e-07 | 33.556 |
| cpu-float-O2-ieee-strict | True | 1148 | 4.236000e-03 | 3.677032e-06 | 5.484720e-07 | 33.883 |
| cpu-float-O2-fastmath-leq | True | 1148 | 4.237000e-03 | 3.829415e-06 | 5.235451e-07 | 36.791 |
| cpu-float-O2-fastmath-strict | True | 1148 | 4.232000e-03 | 4.322404e-06 | 5.091189e-07 | 36.064 |
| cpu-float-O3-ieee-leq | True | 1148 | 4.233000e-03 | 3.230010e-06 | 5.035195e-07 | 36.074 |
| cpu-float-O3-ieee-strict | True | 1148 | 4.236000e-03 | 3.677032e-06 | 5.484720e-07 | 37.116 |
| cpu-float-O3-fastmath-leq | True | 1148 | 4.237000e-03 | 3.829415e-06 | 5.235451e-07 | 35.921 |
| cpu-float-O3-fastmath-strict | True | 1148 | 4.232000e-03 | 4.322404e-06 | 5.091189e-07 | 36.917 |
| cpu-float-Ofast-ieee-leq | True | 1148 | 4.237000e-03 | 3.829415e-06 | 5.235451e-07 | 36.324 |
| cpu-float-Ofast-ieee-strict | True | 1148 | 4.232000e-03 | 4.322404e-06 | 5.091189e-07 | 36.073 |
| cpu-float-Ofast-fastmath-leq | True | 1148 | 4.237000e-03 | 3.829415e-06 | 5.235451e-07 | 36.979 |
| cpu-float-Ofast-fastmath-strict | True | 1148 | 4.232000e-03 | 4.322404e-06 | 5.091189e-07 | 35.301 |

MCA blocks are schema-complete but blocked by the local Docker daemon.
No KH MCA precision-noise claim is made from this packet.
