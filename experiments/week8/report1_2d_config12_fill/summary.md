# Report 1 2D Config12 Evidence Fill

Purpose: add a second two-dimensional Euler Riemann validation case for Report 1, beyond the existing LW3 evidence. The case is Liska-Wendroff config12, run with HLLC under strict-IEEE CPU and GPU builds at N=200 and N=400 in both fp64 and fp32.

## Artifacts

| role | artifact |
|---|---|
| run matrix | `experiments/week8/report1_2d_config12_fill/matrix.json` |
| run metadata | `experiments/week8/report1_2d_config12_fill/matrix_summary.json` |
| fp32/fp64 same-resolution summary | `experiments/week8/report1_2d_config12_fill/precision_summary.md` |
| CPU/GPU device comparison | `experiments/week8/report1_2d_config12_fill/cpu_vs_gpu_config12_hllc_strict.md` |
| N=800 reference matrix | `experiments/week8/report1_2d_config12_fill/reference_matrix.json` |
| N=800 reference output | `experiments/week8/report1_2d_config12_fill/reference/runs/lw12-n800-cpu-double-strict-hllc-reference/reference_800.bin` |
| reference-scaled fp32/fp64 summary | `experiments/week8/report1_2d_config12_fill/reference_comparison/summary.md` |
| main visual candidates | `experiments/week8/report1_2d_config12_fill/figures/lw12_n400_double_rho.png`; `experiments/week8/report1_2d_config12_fill/figures/lw12_n400_double_rho_schlieren.png` |

## Key Numbers

| measurement | N=200 | N=400 |
|---|---:|---:|
| CPU fp64/fp32 conservative-state L1 | 1.556777e-07 | 1.975379e-07 |
| CPU fp64/fp32 conservative-state Linf | 1.060498e-05 | 3.579891e-05 |
| GPU fp64/fp32 conservative-state L1 | 1.556777e-07 | 1.975379e-07 |
| GPU fp64/fp32 conservative-state Linf | 1.060498e-05 | 3.579891e-05 |
| CPU/GPU L1, fp64 | 0.000000e+00 | 0.000000e+00 |
| CPU/GPU L1, fp32 | 0.000000e+00 | 0.000000e+00 |
| rho double-reference L1, fp64 | 2.952149e-03 | 1.330052e-03 |
| rho float-double / double-reference ratio | 4.626293e-05 | 1.300607e-04 |
| pressure float-double / double-reference ratio | 3.845983e-05 | 1.128902e-04 |
| SSIM rho against N=800 reference, fp64 | 0.988960 | 0.996270 |

## Report Claim Supported

This experiment supports the statement that Report 1 includes two 2D Euler Riemann configurations, LW3 and LW12/config12, with quantitative fp32/fp64 and CPU/GPU evidence. For config12, the matched strict-HLLC CPU/GPU comparisons are bit-identical at final time in both precisions and both resolutions. The fp32/fp64 drift remains several orders of magnitude below the N=800-reference error in rho and pressure for N=200 and N=400.

## Boundaries

- The N=800 reference is a higher-resolution numerical reference, not an exact solution.
- The CPU/GPU claim is final-time conservative-state drift under `solver=hllc` and `STRICT_IEEE=ON`.
- The evidence does not test non-strict builds, other 2D Liska-Wendroff configurations, shock-bubble, or MHD.
