# Report 2 publication figure set

Generated from machine-readable summaries after the source-evidence audit. PNG files are for review and PDF files are the preferred manuscript assets.

| Figure | Importance | Chapters | Source | Claim boundary |
|---|---|---|---|---|
| `validation_refinement_glm` | `P1` | 4 | `experiments/week12/brio_wu_1d/summary.json`; `experiments/week12/mhd_2d/divb_clean/summary.json` | Numerical-reference refinement and GLM diagnostics validate bounded MHD behavior. Excludes: Exact-solution accuracy and precision adequacy. |
| `cross_system_sensitivity` | `P0` | 5 | `experiments/week18/euler_mhd_cross_system/summary.json` | Within-case density discrepancy responds differently to precision and math mode across the selected cases. Excludes: Cross-system accuracy or a universal solver/system ranking. |
| `hardware_reproducibility` | `P0` | 5 | `experiments/week18/supplemental/hardware_repeats/summary.json`; `experiments/week21/gpu_fast_math/summary.json` | The bounded HLL GPU path is bit-exact for the covered cases only at --fmad=false, and has workload-dependent repeated timing. Excludes: A generic GPU performance or solver matrix. |
| `resolution_precision` | `P0` | 4, 5 | `experiments/week18/resolution_ladder/summary.json`; `experiments/week21/resolution_ladder_hll_cfl02/summary.json` | Three-grid diagnostics at a matched time step bound the observed refinement behavior without establishing an asymptotic regime. Excludes: Asymptotic convergence, exact-solution accuracy, precision adequacy, or a cross-solver ranking. |
| `temporal_discrepancy` | `P0` | 5 | `experiments/week15/mhd_temporal_divergence/summary.json` | Fixed-window fits compare exponential against power-law growth on identical samples and do not show the planned OT-greater-than-Brio–Wu contrast. Excludes: A formal maximal Lyapunov exponent or physical instability rate. |
| `precision_refinement_context` | `P0` | 5 | `experiments/week18/resolution_ladder/summary.json` | All 12 same-grid precision cells are shown relative to the matched fp64 finest adjacent-grid mean-L1 scale. Excludes: Exact error, fp32 adequacy, asymptotic convergence, or cross-solver ranking. |
| `kh_timing` | `P1` | 5 | `experiments/week18/kh_solver_timing/summary.json` | Repeated matched KH timings quantify FP32 speed-up and HLLD-over-HLL cost on the tested workstation. Excludes: Accuracy-cost position, universal solver ranking, or portability. |

`experiments/week17/report2_synthesis/figures/axis_ranking.png` is excluded from the manuscript because its arbitrary scale ranks incomparable metrics.
