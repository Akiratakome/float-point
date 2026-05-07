# Drift Time-Series Summary

| case | pair | variable | n | final L1 | final Linf | lambda L1 | notes |
|---|---|---|---:|---:|---:|---:|---|
| sod | hllc_vs_rusanov_cpu_strict_smoke | rho | 1 | 4.134993e-03 | 5.809514e-02 | n/a | Final-state smoke only; lambda is n/a until synchronized checkpoints or multiple exact-final-time runs are available.; Full branch/fast-math/hardware axes should be expanded with build-matrix and CUDA artefacts. |
| lw3 | hllc_vs_rusanov_cpu_strict_smoke | rho | 1 | 1.229633e-02 | 1.841195e-01 | n/a | Final-state smoke only; lambda is n/a until synchronized checkpoints or multiple exact-final-time runs are available.; 2D smoke at reduced resolution; intended LW3 axes include CPU/GPU, branch rule, optimisation, fast-math, and extended t_end=1.0 fitting windows. |
