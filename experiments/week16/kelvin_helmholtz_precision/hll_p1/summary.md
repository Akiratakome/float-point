# Week 16 Kelvin-Helmholtz Precision Packet

- Solver: `hll`
- Phase: `p1`
- Mode: `deterministic-with-blocked-mca`
- Commit: `0fe1239a942e852c092eec9a0ab9849bbbc71dfd`
- Deterministic gate: `True`
- MCA gate: `blocked_environment`
- Report-grade gate: `False`

| variant | finite | steps | divB_max | Linf_rho | Linf_By | walltime_s |
|---|---|---:|---:|---:|---:|---:|
| cpu-double-O2-ieee-leq | True | 1148 | 6.714000e-04 | 0.000000e+00 | 0.000000e+00 | 37.632 |
| cpu-double-O2-ieee-strict | True | 1148 | 6.714000e-04 | 0.000000e+00 | 0.000000e+00 | 36.873 |
| cpu-double-O2-fastmath-leq | True | 1148 | 6.714000e-04 | 1.998401e-15 | 4.038111e-16 | 38.011 |
| cpu-double-O2-fastmath-strict | True | 1148 | 6.714000e-04 | 1.998401e-15 | 4.038111e-16 | 38.494 |
| cpu-double-O3-ieee-leq | True | 1148 | 6.714000e-04 | 0.000000e+00 | 0.000000e+00 | 37.259 |
| cpu-double-O3-ieee-strict | True | 1148 | 6.714000e-04 | 0.000000e+00 | 0.000000e+00 | 38.351 |
| cpu-double-O3-fastmath-leq | True | 1148 | 6.714000e-04 | 1.998401e-15 | 4.038111e-16 | 39.751 |
| cpu-double-O3-fastmath-strict | True | 1148 | 6.714000e-04 | 1.998401e-15 | 4.038111e-16 | 38.461 |
| cpu-double-Ofast-ieee-leq | True | 1148 | 6.714000e-04 | 1.998401e-15 | 4.038111e-16 | 38.337 |
| cpu-double-Ofast-ieee-strict | True | 1148 | 6.714000e-04 | 1.998401e-15 | 4.038111e-16 | 37.815 |
| cpu-double-Ofast-fastmath-leq | True | 1148 | 6.714000e-04 | 1.998401e-15 | 4.038111e-16 | 37.659 |
| cpu-double-Ofast-fastmath-strict | True | 1148 | 6.714000e-04 | 1.998401e-15 | 4.038111e-16 | 34.817 |
| cpu-float-O2-ieee-leq | True | 1148 | 6.721000e-04 | 1.786043e-06 | 2.673616e-07 | 28.649 |
| cpu-float-O2-ieee-strict | True | 1148 | 6.721000e-04 | 1.786043e-06 | 2.673616e-07 | 29.407 |
| cpu-float-O2-fastmath-leq | True | 1148 | 6.728000e-04 | 1.821419e-06 | 2.838715e-07 | 29.456 |
| cpu-float-O2-fastmath-strict | True | 1148 | 6.728000e-04 | 1.821419e-06 | 2.838715e-07 | 28.195 |
| cpu-float-O3-ieee-leq | True | 1148 | 6.721000e-04 | 1.786043e-06 | 2.673616e-07 | 27.902 |
| cpu-float-O3-ieee-strict | True | 1148 | 6.721000e-04 | 1.786043e-06 | 2.673616e-07 | 28.078 |
| cpu-float-O3-fastmath-leq | True | 1148 | 6.728000e-04 | 1.821419e-06 | 2.838715e-07 | 29.118 |
| cpu-float-O3-fastmath-strict | True | 1148 | 6.728000e-04 | 1.821419e-06 | 2.838715e-07 | 28.260 |
| cpu-float-Ofast-ieee-leq | True | 1148 | 6.728000e-04 | 1.821419e-06 | 2.838715e-07 | 28.330 |
| cpu-float-Ofast-ieee-strict | True | 1148 | 6.728000e-04 | 1.821419e-06 | 2.838715e-07 | 28.396 |
| cpu-float-Ofast-fastmath-leq | True | 1148 | 6.728000e-04 | 1.821419e-06 | 2.838715e-07 | 28.817 |
| cpu-float-Ofast-fastmath-strict | True | 1148 | 6.728000e-04 | 1.821419e-06 | 2.838715e-07 | 28.292 |

MCA blocks are schema-complete but blocked by the local Docker daemon.
No KH MCA precision-noise claim is made from this packet.
