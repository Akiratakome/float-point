# Report 1 D2 Replots

These figures replace the hard-to-read Pareto/s_req presentation with direct, report-facing diagnostics.

## Outputs

| figure | source | interpretation |
|---|---|---|
| `float_double_over_reference_bar.png` | `experiments/week4/float_regression/2d/summary.json` | Float-double drift divided by double-reference discretisation error; lower is better. |
| `losos_quantiles_rho.png` | raw p8/p16/p32 MCA grids + `u_ref_200_blockavg.npz` | LoSoS rho distribution using q05/q25/median, avoiding a single worst-cell story. |
| `sigma_fp_vs_precision.png` | `C:\Users\tangy\Desktop\floatpoint\experiments\week7\pareto_full\pareto_lw3_full.csv` | sigma_FP_L1 falls as precision increases; this keeps the x/y relationship simple. |
| `region_float_double_over_reference_rho.png` | float/double/reference binaries + density-gradient masks | Float-double drift ratio split by smooth, transition, and strongest-gradient cells. |
| `region_losos_margin_rho_p32.png` | raw p32 MCA grids + density-gradient masks | LoSoS q25/median compared to s_req in each spatial region. |
| `noise_to_error_ratio_rho_p32.png` | raw p32 MCA grids + `u_ref_200_blockavg.npz` | 2D analogue of `vfc_sod_noise_ratio.png`: full-domain log10(noise/error) heatmap. |
| `noise_to_error_ratio_heatmap_grid_rho.png` | raw p8/p16/p32 MCA grids + `u_ref_200_blockavg.npz` | Heatmap grid showing FP-limited regions shrinking as precision increases. |
| `noise_to_error_ratio_quantiles_rho.png` | raw p8/p16/p32 MCA grids + `u_ref_200_blockavg.npz` | Whole-domain noise/error distribution versus virtual precision. |
| `region_noise_to_error_ratio_rho_p32.png` | raw p32 MCA grids + density-gradient masks | Noise/error ratio split by smooth, transition, and strongest-gradient cells. |
| `region_noise_to_error_ratio_precision_compare_rho.png` | raw p8/p16/p32 MCA grids + density-gradient masks | Region-wise median noise/error ratio across p8, p16, and p32. |
| `region_noise_to_error_ratio_precision_grid_rho.png` | raw p8/p16/p32 MCA grids + density-gradient masks | Region noise/error comparison across precision levels. |

## Notes

- The LoSoS quantile plot includes p8/p16/p32 because those raw MCA grids are present in the workspace.
- Additional scalar-only precision rows appear in the sigma_FP plot when the Pareto CSV contains them, but not in the LoSoS quantile plot unless raw MCA grids are present locally.
- For p8, the common HLLC/Rusanov subset is used so sample counts match.

## Float/double over reference ratios

| resolution | variable | ratio |
|---:|---|---:|
| 200 | p | 1.337747e-05 |
| 200 | rho | 4.466390e-05 |
| 200 | u | 1.591349e-05 |
| 200 | v | 1.626731e-05 |
| 400 | p | 2.585592e-05 |
| 400 | rho | 9.252833e-05 |
| 400 | u | 3.041850e-05 |
| 400 | v | 3.035915e-05 |

## LoSoS rho quantiles

| solver | precision | samples | q05 | q25 | median |
|---|---|---:|---:|---:|---:|
| hllc | p8 | 2 | 0.720551 | 1.07722 | 1.27862 |
| hllc | p16 | 3 | 1.46817 | 2.92127 | 3.25924 |
| hllc | p32 | 3 | 1.4679 | 2.93411 | 3.97209 |
| rusanov | p8 | 2 | 0.746282 | 1.32042 | 1.71475 |
| rusanov | p16 | 3 | 1.14955 | 2.32703 | 3.04732 |
| rusanov | p32 | 3 | 1.14964 | 2.32392 | 3.08119 |

## sigma_FP rows

| solver | precision | sigma_fp_l1 |
|---|---|---:|
| hllc | p8 | 1.650597e+03 |
| hllc | p16 | 9.496995e+00 |
| hllc | p24-real-float | 2.955522e-02 |
| hllc | p32 | 1.425469e-04 |
| hllc | p53 | 5.216000e-11 |
| rusanov | p8 | 6.709902e+02 |
| rusanov | p16 | 4.124859e+00 |
| rusanov | p24-real-float | 8.199457e-03 |
| rusanov | p32 | 6.019709e-05 |
| rusanov | p53 | 2.278000e-11 |

## Region-aware float/double rho ratios

| resolution | region | cells | ratio |
|---:|---|---:|---:|
| 200 | discontinuity_grad_p95_p100 | 2000 | 6.285335e-06 |
| 200 | smooth_grad_p00_p70 | 28054 | 3.759549e-04 |
| 200 | transition_grad_p70_p95 | 9946 | 5.551899e-05 |
| 400 | discontinuity_grad_p95_p100 | 8000 | 1.121554e-05 |
| 400 | smooth_grad_p00_p70 | 112000 | 2.338918e-03 |
| 400 | transition_grad_p70_p95 | 40000 | 1.654261e-04 |

## Region-aware LoSoS rho margins

| solver | precision | region | cells | q25 | median | s_req | median_margin |
|---|---|---|---:|---:|---:|---:|---:|
| hllc | p8 | discontinuity_grad_p95_p100 | 2000 | 0.417299 | 0.817717 | 3.07455 | -2.25683 |
| hllc | p8 | smooth_grad_p00_p70 | 28054 | 1.05941 | 1.24431 | 3.07455 | -1.83024 |
| hllc | p8 | transition_grad_p70_p95 | 9946 | 1.21844 | 1.40882 | 3.07455 | -1.66573 |
| hllc | p16 | discontinuity_grad_p95_p100 | 2000 | 0.588168 | 1.31182 | 3.07455 | -1.76273 |
| hllc | p16 | smooth_grad_p00_p70 | 28054 | 3.16753 | 3.39089 | 3.07455 | 0.316347 |
| hllc | p16 | transition_grad_p70_p95 | 9946 | 2.61725 | 2.88926 | 3.07455 | -0.185283 |
| hllc | p32 | discontinuity_grad_p95_p100 | 2000 | 0.58225 | 1.31136 | 3.07455 | -1.76319 |
| hllc | p32 | smooth_grad_p00_p70 | 28054 | 3.7556 | 4.99542 | 3.07455 | 1.92087 |
| hllc | p32 | transition_grad_p70_p95 | 9946 | 2.62652 | 2.89994 | 3.07455 | -0.174602 |
| rusanov | p8 | discontinuity_grad_p95_p100 | 2000 | 0.535593 | 0.728729 | 2.8773 | -2.14857 |
| rusanov | p8 | smooth_grad_p00_p70 | 28000 | 1.31109 | 1.64062 | 2.8773 | -1.23667 |
| rusanov | p8 | transition_grad_p70_p95 | 10000 | 1.69248 | 1.91342 | 2.8773 | -0.963878 |
| rusanov | p16 | discontinuity_grad_p95_p100 | 2000 | 0.446518 | 0.965382 | 2.8773 | -1.91192 |
| rusanov | p16 | smooth_grad_p00_p70 | 28000 | 2.72916 | 3.42565 | 2.8773 | 0.548355 |
| rusanov | p16 | transition_grad_p70_p95 | 10000 | 1.98827 | 2.31092 | 2.8773 | -0.566379 |
| rusanov | p32 | discontinuity_grad_p95_p100 | 2000 | 0.446348 | 0.965257 | 2.8773 | -1.91204 |
| rusanov | p32 | smooth_grad_p00_p70 | 28000 | 2.729 | 4.34936 | 2.8773 | 1.47206 |
| rusanov | p32 | transition_grad_p70_p95 | 10000 | 1.98834 | 2.31581 | 2.8773 | -0.561486 |

## Full-domain noise-to-error ratios

`noise_to_error_ratio_rho_p32.png` is the 2D analogue of the 1D `vfc_sod_noise_ratio.png`: values above zero in log10 space indicate cells where MCA noise exceeds the reference error.

| solver | precision | samples | median log10 ratio | q95 log10 ratio | ratio > 1 cells |
|---|---|---:|---:|---:|---:|
| hllc | p8 | 2 | 0.165537 | 1.28629 | 61.26% |
| hllc | p16 | 3 | -0.152478 | 1.1083 | 43.51% |
| hllc | p32 | 3 | -4.4984 | -0.968269 | 0% |
| rusanov | p8 | 2 | 0.0605655 | 1.11993 | 54.31% |
| rusanov | p16 | 3 | -1.15287 | 1.11161 | 33.01% |
| rusanov | p32 | 3 | -5.9806 | -1.22438 | 0% |

## Region-aware noise-to-error ratios

| solver | precision | region | cells | median log10 ratio | q95 log10 ratio | ratio > 1 cells |
|---|---|---|---:|---:|---:|---:|
| hllc | p8 | discontinuity_grad_p95_p100 | 2000 | -0.217329 | 0.98717 | 36.5% |
| hllc | p8 | smooth_grad_p00_p70 | 28054 | 0.211678 | 1.32452 | 64.3% |
| hllc | p8 | transition_grad_p70_p95 | 9946 | 0.0994421 | 1.20384 | 57.64% |
| hllc | p16 | discontinuity_grad_p95_p100 | 2000 | -2.09022 | -1.058 | 0.55% |
| hllc | p16 | smooth_grad_p00_p70 | 28054 | 0.162092 | 1.25003 | 60.5% |
| hllc | p16 | transition_grad_p70_p95 | 9946 | -0.909268 | -0.0730622 | 4.213% |
| hllc | p32 | discontinuity_grad_p95_p100 | 2000 | -7.06449 | -6.01194 | 0% |
| hllc | p32 | smooth_grad_p00_p70 | 28054 | -3.3697 | -0.905023 | 0% |
| hllc | p32 | transition_grad_p70_p95 | 9946 | -5.71096 | -4.89557 | 0% |
| rusanov | p8 | discontinuity_grad_p95_p100 | 2000 | -0.428679 | 0.246932 | 11.55% |
| rusanov | p8 | smooth_grad_p00_p70 | 28000 | 0.131848 | 1.1656 | 59.91% |
| rusanov | p8 | transition_grad_p70_p95 | 10000 | -0.0375825 | 1.07062 | 47.16% |
| rusanov | p16 | discontinuity_grad_p95_p100 | 2000 | -2.43903 | -1.66836 | 0.6% |
| rusanov | p16 | smooth_grad_p00_p70 | 28000 | -0.0996851 | 1.28138 | 46.86% |
| rusanov | p16 | transition_grad_p70_p95 | 10000 | -2.00325 | -1.02859 | 0.68% |
| rusanov | p32 | discontinuity_grad_p95_p100 | 2000 | -7.17312 | -6.52984 | 0% |
| rusanov | p32 | smooth_grad_p00_p70 | 28000 | -4.69873 | -1.17532 | 0% |
| rusanov | p32 | transition_grad_p70_p95 | 10000 | -6.82967 | -5.86391 | 0% |
