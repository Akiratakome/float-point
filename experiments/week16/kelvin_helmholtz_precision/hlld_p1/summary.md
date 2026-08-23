# Week 16 Kelvin-Helmholtz Precision Packet

- Solver: `hlld`
- Phase: `p1`
- Mode: `deterministic-with-blocked-mca`
- Commit: `0fe1239a942e852c092eec9a0ab9849bbbc71dfd`
- Deterministic gate: `True`
- MCA gate: `blocked_environment`
- Report-grade gate: `False`

| variant | finite | steps | divB_max | Linf_rho | Linf_By | walltime_s |
|---|---|---:|---:|---:|---:|---:|
| cpu-double-O2-ieee-leq | True | 1148 | 4.228000e-03 | 0.000000e+00 | 0.000000e+00 | 38.698 |
| cpu-double-O2-ieee-strict | True | 1148 | 4.228000e-03 | 0.000000e+00 | 0.000000e+00 | 38.733 |
| cpu-double-O2-fastmath-leq | True | 1148 | 4.228000e-03 | 9.992007e-15 | 1.391248e-15 | 38.235 |
| cpu-double-O2-fastmath-strict | True | 1148 | 4.228000e-03 | 9.992007e-15 | 1.391248e-15 | 38.277 |
| cpu-double-O3-ieee-leq | True | 1148 | 4.228000e-03 | 0.000000e+00 | 0.000000e+00 | 38.635 |
| cpu-double-O3-ieee-strict | True | 1148 | 4.228000e-03 | 0.000000e+00 | 0.000000e+00 | 38.844 |
| cpu-double-O3-fastmath-leq | True | 1148 | 4.228000e-03 | 9.992007e-15 | 1.391248e-15 | 38.467 |
| cpu-double-O3-fastmath-strict | True | 1148 | 4.228000e-03 | 9.992007e-15 | 1.391248e-15 | 38.897 |
| cpu-double-Ofast-ieee-leq | True | 1148 | 4.228000e-03 | 9.992007e-15 | 1.391248e-15 | 39.729 |
| cpu-double-Ofast-ieee-strict | True | 1148 | 4.228000e-03 | 9.992007e-15 | 1.391248e-15 | 38.626 |
| cpu-double-Ofast-fastmath-leq | True | 1148 | 4.228000e-03 | 9.992007e-15 | 1.391248e-15 | 38.536 |
| cpu-double-Ofast-fastmath-strict | True | 1148 | 4.228000e-03 | 9.992007e-15 | 1.391248e-15 | 38.504 |
| cpu-float-O2-ieee-leq | True | 1148 | 4.233000e-03 | 3.230010e-06 | 5.035195e-07 | 35.062 |
| cpu-float-O2-ieee-strict | True | 1148 | 4.236000e-03 | 3.677032e-06 | 5.484720e-07 | 34.407 |
| cpu-float-O2-fastmath-leq | True | 1148 | 4.237000e-03 | 3.829415e-06 | 5.235451e-07 | 34.173 |
| cpu-float-O2-fastmath-strict | True | 1148 | 4.232000e-03 | 4.322404e-06 | 5.091189e-07 | 34.139 |
| cpu-float-O3-ieee-leq | True | 1148 | 4.233000e-03 | 3.230010e-06 | 5.035195e-07 | 34.552 |
| cpu-float-O3-ieee-strict | True | 1148 | 4.236000e-03 | 3.677032e-06 | 5.484720e-07 | 34.441 |
| cpu-float-O3-fastmath-leq | True | 1148 | 4.237000e-03 | 3.829415e-06 | 5.235451e-07 | 32.938 |
| cpu-float-O3-fastmath-strict | True | 1148 | 4.232000e-03 | 4.322404e-06 | 5.091189e-07 | 34.009 |
| cpu-float-Ofast-ieee-leq | True | 1148 | 4.237000e-03 | 3.829415e-06 | 5.235451e-07 | 33.562 |
| cpu-float-Ofast-ieee-strict | True | 1148 | 4.232000e-03 | 4.322404e-06 | 5.091189e-07 | 33.807 |
| cpu-float-Ofast-fastmath-leq | True | 1148 | 4.237000e-03 | 3.829415e-06 | 5.235451e-07 | 34.219 |
| cpu-float-Ofast-fastmath-strict | True | 1148 | 4.232000e-03 | 4.322404e-06 | 5.091189e-07 | 34.162 |

MCA blocks are schema-complete but blocked by the local Docker daemon.
No KH MCA precision-noise claim is made from this packet.
