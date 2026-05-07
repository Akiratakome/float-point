# Drift Time-Series Summary

| case | pair | variable | n | final L1 | final Linf | lambda L1 | notes |
|---|---|---|---:|---:|---:|---:|---|
| sod | hllc_vs_rusanov_cpu_strict_smoke | rho | 3 | 4.134993e-03 | 5.809514e-02 | 31.4602 | Smoke pair validates CPU output_times and drift aggregation; full branch/fast-math/hardware axes should be expanded with build-matrix and CUDA artefacts. |
| lw3 | hllc_vs_rusanov_cpu_strict_smoke | rho | 3 | 1.229633e-02 | 1.841195e-01 | -8.7063 | 2D output_times smoke at reduced resolution; intended LW3 axes include CPU/GPU, branch rule, optimisation, fast-math, and extended t_end=1.0 fitting windows. |
