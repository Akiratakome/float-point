# Week 16 Kelvin-Helmholtz Precision Packet

- Solver: `hll`
- Phase: `p1`
- Mode: `deterministic-with-blocked-mca`
- Commit: `2082dd5e2825a42038c8e9ceb050092c6211adc8`
- Deterministic gate: `True`
- MCA gate: `blocked_environment`
- Report-grade gate: `False`

| variant | finite | steps | divB_max | Linf_rho | Linf_By | walltime_s |
|---|---|---:|---:|---:|---:|---:|
| cpu-double-O2-ieee-leq | True | 1148 | 6.714000e-04 | 0.000000e+00 | 0.000000e+00 | 35.631 |
| cpu-double-O2-ieee-strict | True | 1148 | 6.714000e-04 | 0.000000e+00 | 0.000000e+00 | 34.501 |
| cpu-double-O2-fastmath-leq | True | 1148 | 6.714000e-04 | 1.998401e-15 | 4.038111e-16 | 34.902 |
| cpu-double-O2-fastmath-strict | True | 1148 | 6.714000e-04 | 1.998401e-15 | 4.038111e-16 | 34.651 |
| cpu-double-O3-ieee-leq | True | 1148 | 6.714000e-04 | 0.000000e+00 | 0.000000e+00 | 34.020 |
| cpu-double-O3-ieee-strict | True | 1148 | 6.714000e-04 | 0.000000e+00 | 0.000000e+00 | 33.970 |
| cpu-double-O3-fastmath-leq | True | 1148 | 6.714000e-04 | 1.998401e-15 | 4.038111e-16 | 34.814 |
| cpu-double-O3-fastmath-strict | True | 1148 | 6.714000e-04 | 1.998401e-15 | 4.038111e-16 | 34.971 |
| cpu-double-Ofast-ieee-leq | True | 1148 | 6.714000e-04 | 1.998401e-15 | 4.038111e-16 | 34.992 |
| cpu-double-Ofast-ieee-strict | True | 1148 | 6.714000e-04 | 1.998401e-15 | 4.038111e-16 | 35.160 |
| cpu-double-Ofast-fastmath-leq | True | 1148 | 6.714000e-04 | 1.998401e-15 | 4.038111e-16 | 34.690 |
| cpu-double-Ofast-fastmath-strict | True | 1148 | 6.714000e-04 | 1.998401e-15 | 4.038111e-16 | 35.067 |
| cpu-float-O2-ieee-leq | True | 1148 | 6.721000e-04 | 1.786043e-06 | 2.673616e-07 | 28.392 |
| cpu-float-O2-ieee-strict | True | 1148 | 6.721000e-04 | 1.786043e-06 | 2.673616e-07 | 28.354 |
| cpu-float-O2-fastmath-leq | True | 1148 | 6.728000e-04 | 1.821419e-06 | 2.838715e-07 | 28.929 |
| cpu-float-O2-fastmath-strict | True | 1148 | 6.728000e-04 | 1.821419e-06 | 2.838715e-07 | 28.867 |
| cpu-float-O3-ieee-leq | True | 1148 | 6.721000e-04 | 1.786043e-06 | 2.673616e-07 | 28.127 |
| cpu-float-O3-ieee-strict | True | 1148 | 6.721000e-04 | 1.786043e-06 | 2.673616e-07 | 28.535 |
| cpu-float-O3-fastmath-leq | True | 1148 | 6.728000e-04 | 1.821419e-06 | 2.838715e-07 | 28.902 |
| cpu-float-O3-fastmath-strict | True | 1148 | 6.728000e-04 | 1.821419e-06 | 2.838715e-07 | 28.986 |
| cpu-float-Ofast-ieee-leq | True | 1148 | 6.728000e-04 | 1.821419e-06 | 2.838715e-07 | 29.005 |
| cpu-float-Ofast-ieee-strict | True | 1148 | 6.728000e-04 | 1.821419e-06 | 2.838715e-07 | 29.203 |
| cpu-float-Ofast-fastmath-leq | True | 1148 | 6.728000e-04 | 1.821419e-06 | 2.838715e-07 | 29.065 |
| cpu-float-Ofast-fastmath-strict | True | 1148 | 6.728000e-04 | 1.821419e-06 | 2.838715e-07 | 28.544 |

MCA blocks are schema-complete but blocked by the local Docker daemon.
No KH MCA precision-noise claim is made from this packet.
