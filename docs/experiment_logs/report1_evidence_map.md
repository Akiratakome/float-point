# Report 1 experiment evidence map

This file classifies the useful artifacts under `experiments/` for Project
Report 1, using the Report 1 PDF requirements and the current agreed direction:

- Main axis: D1, direct drift and reproducibility across implementation,
  compiler, precision, and device axes.
- Supporting axis: D2, precision adequacy using region-aware LoSoS, SNR-like
  noise/error ratios, and float-vs-double/reference comparisons.

The labels `D1`, `D2`, `week*`, and other local experiment names are internal
evidence-location labels only. Do not use them in the Report 1 manuscript,
captions, headings, or conclusions. In the report, translate them into
descriptive scientific labels such as "compiler-flag comparison", "matched
CPU/GPU comparison", "precision adequacy diagnostic", or "time-resolved drift
measurement".

Priority scale:

- P0: core Report 1 evidence. Use in the main text or supervisor update.
- P1: useful support. Use in appendix, methods, or if space allows.
- P2: provenance or backup. Keep, but avoid as primary figures.
- P3: do not use directly in the report body. Raw, duplicate, failed, or
  superseded artifacts.

## Core evidence to use

| Artifact | Priority | Use? | Answers Report 1 requirement | Reason / interpretation |
|---|---:|---|---|---|
| `experiments/week7/report1_validation_1d/summary.md` | P0 | Yes | Validation: 1D Euler tests; single vs double precision | Clean 6-case 1D float/double matrix. Use as numerical table for precision comparison. |
| `experiments/week3/week3_validation/plots/sod_comparison.png` | P0 | Yes | Validation: correct 1D ideal-gas Euler results | Profile against exact Riemann solution; easy to read as baseline validation. |
| `experiments/week3/week3_validation/plots/toro3_comparison.png` | P0 | Yes | Validation: supersonic/strong-wave 1D case | Stronger wave case than Sod; shows solver handles severe 1D flow. |
| `experiments/week3/week3_validation/plots/toro5_comparison.png` | P0 | Yes | Validation: additional 1D supersonic/strong-wave case | Good fourth/fifth 1D validation evidence if the report needs multiple Toro cases. |
| `experiments/week3/week3_validation/plots/convergence_sod.png` | P1 | Optional | Validation and testing framework | Shows convergence behavior, but weaker than direct multi-case summaries. |
| `experiments/week4/float_regression/1d/summary.md` | P0 | Yes | Validation; exact/converged reference; float vs double | Best exact-reference 1D convergence and float adequacy evidence. Use ratios to argue float-double gaps are much smaller than discretization error for most cases. |
| `experiments/week4/float_regression/1d/*.csv` | P1 | Optional | Validation detail | Use only if a table needs exact L1/L2/Linf by resolution. |
| `experiments/report1_1d_feature_validation/summary.md` | P0 | Yes | Validation: 1D feature locations and region split | Derived post-processing of the Week 4 final grids. Reports contact/shock location errors and density-error split between narrow discontinuity bands and the remaining cells for Sod, Toro3, and Toro5 at \(N=800\). |
| `experiments/week7/report1_validation_2d/summary.md` | P0 | Yes | Validation: 2D Euler case; single vs double | Clean 2D LW3 float/double matrix at N=200 and N=400. |
| `experiments/week7/report1_validation_2d/figures/lw3_n400_double_rho_schlieren.png` | P0 | Yes | Validation: 2D Euler visual result | Best 2D main-text figure. Schlieren view makes waves and contacts visible. |
| `experiments/week7/report1_validation_2d/figures/lw3_n400_double_rho.png` | P1 | Optional | Validation: 2D Euler visual result | Use if a density-field figure is clearer than schlieren for the audience. |
| `experiments/week4/float_regression/2d/summary.md` | P0 | Yes | Validation; exact/converged reference; float vs double | 2D LW3 compared with high-resolution reference; supports claim that p24 noise is tiny relative to truncation/reference error. |
| `experiments/report1_reference_self_convergence/summary.md` | P0 | Yes | Validation; high-resolution numerical-reference support | Derived LW3 400-vs-800 and 800-vs-1600 self-convergence check using existing fp64 artifacts. Supports use of the 1600^2 field as a higher-resolution numerical reference, with the explicit limitation that this is not an exact-solution proof and no analogous LW12 1600^2 row is available. |
| `experiments/week8/report1_2d_config12_fill/summary.md` | P0 | Yes | Validation: second 2D Euler Riemann case; CPU/GPU; single vs double | Adds Liska-Wendroff config12 as a second 2D case with strict-HLLC CPU/GPU and fp32/fp64 evidence at N=200 and N=400. Use to avoid relying on LW3 as the only 2D case. |
| `experiments/week8/report1_2d_config12_fill/reference_comparison/summary.md` | P0 | Yes | Validation; high-resolution reference; float vs double | Config12 N=200/N=400 compared with an N=800 double numerical reference. Float-double/reference ratios are small: rho ≈ 4.63e-5 at N=200 and ≈ 1.30e-4 at N=400; pressure ≈ 3.85e-5 and ≈ 1.13e-4. |
| `experiments/week8/report1_2d_config12_fill/cpu_vs_gpu_config12_hllc_strict.md` | P0 | Yes | Required CPU vs GPU quantification for second 2D case | Config12 matched CPU/GPU strict-HLLC runs are zero L1/Linf/ULP drift for fp32 and fp64 at N=200 and N=400, measured on the final conservative state. |
| `experiments/week8/report1_2d_config12_fill/figures/lw12_n400_double_rho_schlieren.png` | P0 | Yes | Validation: second 2D Euler visual result | Main visual candidate for config12. Pair with LW3 schlieren to show two distinct 2D Riemann configurations. |
| `experiments/week8/report1_2d_config12_fill/figures/lw12_n400_double_rho.png` | P1 | Optional | Validation: second 2D Euler visual result | Use if density is easier to read than schlieren for config12; otherwise keep as appendix/supporting figure. |
| `experiments/week7/report1_validation_2d_gpu/summary.md` | P0 | Yes | Validation: CPU/GPU and precision | GPU side of the LW3 validation matrix. |
| `experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md` | P0 | Yes | Required CPU vs GPU quantification for selected 1D cases | Supplements the existing Sod/LW3 device evidence: Toro3 and Toro5 matched CPU/GPU HLLC strict runs pass with zero L1/Linf/ULP drift in both fp64 and fp32. |
| `experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md` | P0 | Yes | Required CPU vs GPU quantification (2D fp64) | Strongest CPU/GPU reproducibility evidence for LW3 fp64 N=200/N=400 under `solver=hllc`, `STRICT_IEEE=ON`: zero L1/Linf/ULP drift. |
| `experiments/week8/report1_device_hllc_fill/cpu_vs_gpu_sod_lw3fp32_hllc_strict.md` | P0 | Yes | Required CPU vs GPU quantification (Sod and LW3 fp32 under HLLC strict) | Closes the strict-HLLC CPU/GPU evidence for Sod fp32+fp64 and LW3 fp32 N=200/N=400. Bit-identical CPU vs GPU on the Linux/WSL toolchain; replaces the Rusanov-strict Week 6 rows in the HLLC reproducibility claim. |
| `experiments/week9/cpu_gpu_midtime/summary.md`; `experiments/week9/cpu_gpu_midtime_n400/summary.md` | P0 | Yes | Intermediate-time CPU vs GPU checkpoint quantification | Adds checkpointed strict-HLLC CPU/GPU evidence for Sod, LW3, and LW12 in fp32 and fp64. All listed same-precision CPU/GPU pairs are zero L1/Linf/ULP at saved checkpoints. Use only as checkpointed-output evidence, not proof of stage-by-stage identity. |
| `experiments/report1_cpu_gpu_zero_drift_audit/summary.md`; `experiments/report1_cpu_gpu_zero_drift_audit/hashes.csv`; `experiments/report1_cpu_gpu_zero_drift_audit/metrics.csv` | P0 | Yes | CPU/GPU saved-output reproducibility audit | Consolidates the strict-HLLC CPU/GPU saved-output evidence into 52 hash-audited metric pairs plus two metrics-only LW3 fp64 rows whose raw grids are absent from the working tree. Also records four GPU strict-vs-fast counterexample pairs. Use to scope the zero-drift claim to saved conservative states, not intermediate primitive variables or wave-speed estimates. |
| `experiments/week6/regression/summary.md` | P1 | Yes, as harness provenance | Testing framework / regression harness | Rusanov strict CPU/GPU regression for Sod and LW3 from Week 6. Use as harness/reproducibility-pipeline provenance only; do not cite for the HLLC strict CPU-vs-GPU claim because the runs used `solver=rusanov`. |
| `experiments/week7/report1_variation/summary.md` | P0 | Yes | Mathematical theory; implementation variations | Main summary for O2/O3/Ofast, HLLC branch rule (`<` vs `<=`, via `RIEMANN_STRICT_INEQUALITY`), and HLLC-vs-Rusanov variation axes. CPU double only. Covers Sod, stationary_contact, LW3-N200. The build-name suffix "leq" vs "strict" controls only the HLLC wave-speed branch, not STRICT_IEEE. |
| `experiments/week8/report1_variation_extend/summary.md` | P0 | Yes | Extends week 7 variation matrix to Toro3 and Toro5 under the same axes | Closes the Toro3/Toro5 gap in the compiler/branch variation matrix. HLLC `<=` vs `<` and O2 vs O3 are zero drift on both cases; O2 vs Ofast-fastmath gives L1 ~2-5e-13 and Linf ~3-7e-11 on Toro3/Toro5 — the largest non-stationary final-time drift in the combined matrix. Same axes, CPU double only. |
| `experiments/week9/variation_fp32/summary.md`; `experiments/week9/variation_fp32_extend/summary.md` | P0 | Yes | fp32 compiler-flag sensitivity | Adds CPU fp32 O2/O3/Ofast-fastmath rows for Sod, Toro3, Toro5, and LW3. O2 vs O3 is bit-identical where checked; Ofast-fastmath perturbs non-stationary cases, with the largest listed final-time fp32 drift in Toro5. |
| `experiments/week9/gpu_strict_vs_fast/summary.md` | P1 | Yes, with caveat | GPU strict-vs-fast build-control probe | Compares strict CUDA outputs against fast-math CUDA outputs for Sod and LW3. Use to show that strict/fast build flags materially affect saved GPU states; do not present it as a direct non-strict CPU/GPU comparison. |
| `experiments/week9/report1_square_figures/summary.md` | P1 | Yes, as figure provenance | Report-facing 2D figure replacements | Replots LW3/LW12 schlieren and the LW12 fp32-fp64 density heatmap with equal x/y aspect in the data panel and without internal figure titles. |
| `experiments/report1_limiter_variation_optin/summary.md` | P1 | Yes, as support/limitation | Opt-in limiter-variation probe | CPU fp64 HLLC minbee-vs-van-Leer comparison for Sod, Toro3, Toro5, and LW3 N=200 after adding a default-preserving `limiter` cfg key. Use only to bound limiter sensitivity as an implementation/method variation; do not mix it into same-solver reproducibility or hardware claims. |
| `experiments/week9/variation_limiter/summary.md` | P2 | Historical limitation | Limiter-variation status before opt-in interface | Earlier record that no limiter-sensitivity result was claimed because the report harness had no documented limiter-selection axis. Superseded for new support claims by `experiments/report1_limiter_variation_optin/summary.md`. |
| `experiments/report1_shock_bubble_support/summary.md`; `experiments/report1_shock_bubble_support/figures/shockbubble_cpu_double_hllc_rho_schlieren.png` | P1 | Yes, appendix/support only | Shock-bubble morphology and sensitivity support | CPU-only shock-bubble support packet at 400x100 for HLLC/Rusanov and fp32/fp64. Useful to show a more complex 2D shock/contact morphology and that solver-choice differences exceed fp64-vs-fp32 differences, but it has no exact or high-resolution reference strategy and must not replace the five-case main validation matrix. |
| `experiments/report1_toolchain_sanity_toro35/summary.md` | P1 | Yes, as method-sanity support | Toro3/Toro5 toolchain sanity check | CPU-only WSL/GCC strict rerun for Toro3/Toro5. The saved conservative states match the existing strict CPU report artifacts bit-for-bit for the four checked precision/case rows, and the fp64-vs-fp32 L1 values reproduce the report values to printed precision. Use only to answer the toolchain-split concern; do not present as a general cross-toolchain or CPU/GPU claim. |
| `experiments/report1_runtime_minimatrix/summary.md` | P1 | Yes, as support/cost context | Controlled runtime mini-matrix | Containerized CUDA 12.5.1/GCC 13 strict-HLLC runtime matrix for Sod N=800 and LW3 N=400, with five repeats for fp64/fp32 CPU/GPU and zero saved-state CPU/GPU drift for the checked rows. Use only as compact computational-cost context; do not present as a tuned or general performance benchmark. |
| `experiments/report1_shock_bubble_reference_upgrade/summary.md` | P1 | Yes, appendix/support only | Shock-bubble higher-resolution CPU reference check | Adds HLLC fp64 CPU 400x100 and 800x200 runs plus a conservative-state 400-vs-block-averaged-800 comparison. Useful as a stronger support check for shock-bubble morphology, but the 1600x400 row did not complete in the local polishing window and no CPU/GPU rows were added, so this still must not replace the five-case main validation matrix. |
| `experiments/week7/report1_variation/axis_o2_vs_ofast.*` | P0 | Yes | D1 compiler-flag drift | Directly answers compiler flag sensitivity; use table/CSV values, not necessarily every plot. |
| `experiments/week7/report1_variation/axis_leq_vs_strict.*` | P1 | Yes, with caveat | D1 implementation variation: `<=` vs `<` | Important because supervisor mentioned this axis. Results are mostly zero, which is still a finding. |
| `experiments/week7/report1_variation/axis_hllc_vs_rusanov.*` | P1 | Optional | Mathematical theory / method variation | This is method difference, not reproducibility drift. Use carefully as solver-variation context. |
| `experiments/week7/lyapunov_1d_full/summary.md` | P0 | Yes | D1 drift growth over time | Best written evidence for finite-time drift growth in 1D Toro cases. State clearly this is implementation-sensitivity rate, not a formal PDE Lyapunov exponent. The `<` branch on Toro2 (`toro2_hllc_lt_strict_ieee`) did not complete in this harness; see `experiments/week8/toro2_lt_branch_retry/summary.md` for an independent reproduction and the side-by-side `<=` baseline timing. |
| `experiments/week8/toro2_lt_branch_retry/summary.md` | P0 | Yes | Reproduces and bounds the toro2 `<` branch non-completion | Side-by-side: `<=` completes in 0.125 s at cfl=0.8, `<` does not produce a final grid.bin within at least 10 min wall under the same toolchain. Supports the brief's "wave-speeds very close to zero" prediction on the near-vacuum 123 case. |
| `experiments/week7/lyapunov_1d_full/figures/drift_timeseries_l1_normalized.png` | P0 | Yes | D1 drift growth over time | Best D1 figure for supervisor. Normalized L1 drift makes cases comparable. |
| `experiments/report1_fp32_fp64_time_drift/summary.md`; `experiments/report1_fp32_fp64_time_drift/figures/drift_timeseries_l1_normalized.png` | P0 | Yes | Precision drift over saved checkpoints | New CPU-only HLLC fp64-vs-fp32 saved-state time series for Sod, Toro3, Toro5, and LW3 N=200. Use to show precision-pair drift growth at saved outputs; do not describe it as fp32 error against an exact or converged reference. |
| `experiments/week7/lyapunov_1d_full/figures/drift_timeseries_l1.png` | P1 | Optional | D1 drift growth detail | Absolute L1 drift; useful in appendix or if normalization is challenged. |
| `experiments/week7/report1_d2_replots/float_double_over_reference_bar.png` | P0 | Yes | D2 precision adequacy; float vs reference | Clear replacement for hard-to-read Pareto plots. Y axis is `||float-double||_1 / ||double-reference||_1`; values below 1 mean float-double drift is below discretization/reference error. |
| `experiments/week7/report1_d2_replots/losos_quantiles_rho.png` | P0 | Yes | D2 LoSoS; significant digits | Uses q05/q25/median instead of only worst cell. Better explains why shock/contact regions reduce worst-case precision. |
| `experiments/week7/report1_d2_replots/region_losos_margin_rho_p32.png` | P0 | Yes | D2 region-aware precision adequacy margin | Keeps `s_req` but makes it interpretable by region: smooth, transition, and front. |
| `experiments/week7/report1_d2_replots/sigma_fp_vs_precision.png` | P0 | Yes | D2 FP noise vs precision bits | Directly shows `sigma_FP` decreases as precision bits increase; compare HLLC and Rusanov. |
| `experiments/verificarlo/results/vfc_sod_overlay.png` | P1 | Yes, as method explanation | Verificarlo MCA diagnostic framing | One-dimensional Sod overlay used to show how MCA ensemble spread and significant-digit estimates are read. Treat as explanatory tooling evidence, not a new validation result and not IEEE fp32 evidence. |
| `experiments/week7/report1_d2_replots/noise_to_error_ratio_heatmap_grid_rho.png` | P0 | Yes | D2 SNR/noise-to-error spatial structure | Best heatmap-style answer: shows where FP noise competes with physical/discretization error across p8/p16/p32. |
| `experiments/week7/report1_d2_replots/noise_to_error_ratio_rho_p8.png` | P1 | Optional | D2 low-precision stress test | Use if explaining why p8 is clearly inadequate in some regions. |
| `experiments/week7/report1_d2_replots/noise_to_error_ratio_rho_p16.png` | P1 | Optional | D2 low/intermediate precision | Use if showing transition from inadequate to adequate precision. |
| `experiments/week7/report1_d2_replots/noise_to_error_ratio_rho_p32.png` | P1 | Optional | D2 p32 adequacy | Useful as a single p32-focused figure, but the grid figure is better for comparison. |
| `experiments/week7/report1_d2_replots/region_noise_to_error_ratio_precision_grid_rho.png` | P0 | Yes | D2 region-aware SNR | Shows the same ratio by region and precision; good companion to region LoSoS margin. |
| `experiments/week7/report1_d2_replots/*.csv` | P1 | Optional | Reproducible plotting and tables | Use for exact numeric values in tables. Do not put all CSVs in the main report. |

## Folder-by-folder classification

| Folder | Priority | Use? | Reason |
|---|---:|---|---|
| `experiments/week2/` | P2 | Backup only | Early 1D Sod verification and output plots. Superseded by Week 3 exact-reference validation and Week 4/7 regression summaries. |
| `experiments/week2/output/` | P2 | Backup only | Contains early verification plots. Use only if a historical development figure is needed. |
| `experiments/week3/week3_validation/` | P0 | Yes | Best readable 1D exact-reference validation plots. Use Sod plus selected Toro strong-wave cases. |
| `experiments/week3/week3_rusanov/` | P1 | Optional | HLLC-vs-Rusanov 1D comparison. Useful for method variation, not for core reproducibility. |
| `experiments/week3/verificarlo*/` | P2 | Mostly no | Older MCA/Verificarlo attempts. Superseded by `experiments/verificarlo/results` and Week 7 D2 replots. Keep for provenance. |
| `experiments/week3/humming-inventing-stonebraker.md` | P3 | No | Draft/note artifact, not direct evidence. |
| `experiments/week4/float_regression/1d/` | P0 | Yes | Strong exact-reference 1D convergence and float/double adequacy evidence. |
| `experiments/week4/float_regression/2d/` | P0 | Yes | Strong 2D high-resolution-reference evidence and float/double comparison. |
| `experiments/week4/figures/deterministic_2d/` | P1 | Optional | Good visual method-comparison figures for HLLC vs Rusanov. |
| `experiments/week4/metrics/` | P2 | Avoid main text | Older LoSoS/Pareto-style metrics. Superseded by clearer Week 7 D2 replots. |
| `experiments/week4/figures/a4_float_p24/` | P2 | Avoid main text | Older p24 figures. Keep as provenance, but current D2 figures are clearer. |
| `experiments/week4/figures/a4_pareto/` | P2 | Avoid main text | Original Pareto-style figures were hard to explain. Use only as appendix/history. |
| `experiments/week4/reference/` | P2 | Provenance | Raw/reference grids and source material for validation. Do not use directly as report figures. |
| `experiments/week4/deterministic/` | P2 | Provenance | Raw deterministic outputs. Cite only indirectly through plotted/aggregated figures. |
| `experiments/week5/baselines/` | P2 | Backup only | Earlier shock-bubble/config baseline material. Use the report-facing `experiments/report1_shock_bubble_support/` packet instead if appendix/support evidence is needed. |
| `experiments/week5/smoke/` | P3 | No | Smoke tests only. |
| `experiments/week5/harness_smoke/` | P3 | No | Harness smoke/provenance only; not report evidence. |
| `experiments/week6/regression/` | P0 | Yes | Important CPU/GPU strict regression summary. |
| `experiments/week6/csc_smoke/` | P2 | Provenance | Shows GPU/CSC execution environment; use only in code/testing description. |
| `experiments/week6/baselines/` | P2 | Provenance | Baseline raw outputs; use summarized Week 6/7 results instead. |
| `experiments/week6/smoke/` | P3 | No | Smoke-only material. |
| `experiments/week7/report1_validation_1d/` | P0 | Yes | Main Report 1 1D precision validation matrix. |
| `experiments/week7/report1_validation_1d_device/` | P0 | Yes | Matched CPU/GPU evidence for the selected Toro3 and Toro5 1D cases. |
| `experiments/week7/report1_validation_2d/` | P0 | Yes | Main Report 1 2D CPU validation matrix and LW3 figures. |
| `experiments/week7/report1_validation_2d_gpu/` | P0 | Yes | GPU side of 2D validation. |
| `experiments/week7/report1_validation_2d_device/` | P0 | Yes | Best CPU-vs-GPU strict double reproducibility evidence. |
| `experiments/week8/report1_2d_config12_fill/` | P0 | Yes | Second 2D Riemann validation case for Report 1: config12 CPU/GPU, fp32/fp64, N=800 reference comparison, and report-facing figures. |
| `experiments/week7/report1_variation/` | P0 | Yes | Main D1 variation matrix: compiler flags, branch rule, solver variation. |
| `experiments/week7/lyapunov_1d_full/` | P0 | Yes | Best time-growth drift evidence. |
| `experiments/week7/lyapunov_1d/` | P2 | Backup only | Earlier/smaller version of the drift study. Superseded by `lyapunov_1d_full`. |
| `experiments/week7/report1_d2_replots/` | P0 | Yes | Current recommended D2 figure set after simplifying Pareto/LoSoS interpretation. |
| `experiments/week7/verificarlo_report1_refresh/` | P1 | Optional | Refreshed Verificarlo precision sweep. Good support/provenance, but D2 replots are easier to explain. |
| `experiments/week7/metrics/` | P2 | Avoid main text | Source/older metric outputs. Use only to reproduce clearer replots. |
| `experiments/week7/pareto_full/` | P2 | Avoid main text | Older Pareto output. Keep out of main report unless specifically defending metric development. |
| `experiments/week7/reference_1600/` | P1 | Yes, as provenance | Explains 1600-resolution reference used by 2D reference comparisons. Do not overclaim CPU/GPU equivalence from this folder alone. |
| `experiments/week7/reference_1600_rusanov/` | P1 | Optional provenance | Same as above for Rusanov reference. |
| `experiments/week7/report1_aggregate/` | P1 | Yes, as index | Useful routing summary, not a primary result. |
| `experiments/week7/report1_smoke/` | P2 | Provenance | Build/run smoke and metadata; use for code/testing description only. |
| `experiments/week7/vfc_precexp/` | P3 | No as result | Full-solver precexp attempt was not successfully reported/parsed. Mention only as tooling limitation/future work. |
| `experiments/week7/vfc_precexp_micro/` | P2 | Optional future work | Micro-kernel precision experiment accepted near 52-bit results. Not central to Report 1. |
| `experiments/verificarlo/results/` | P1 | Optional | Canonical 1D MCA examples such as `vfc_sod_overlay.png` and `vfc_sod_noise_ratio.png`. Good for explaining MCA/SNR, but Week 7 D2 figures remain the stronger precision-adequacy evidence. |
| `experiments/verificarlo/results_fma/` | P1 | Optional | FMA-related MCA support. Use only if discussing hardware/compiler arithmetic details. |
| `experiments/verificarlo/runs_compare_p24_mca_real_vs_double*/` | P2 | Provenance | Useful to explain p24 real-float vs VPREC caveats; not main evidence. |
| `experiments/c2_bundle_for_download/` | P3 | No | Duplicate/download bundle of C2 artifacts. Use canonical `experiments/verificarlo` or Week 7 folders instead. |

## Recommended supervisor packet

Use a selected but evidence-rich set of figures/tables rather than sending every plot:

1. `experiments/week7/lyapunov_1d_full/figures/drift_timeseries_l1_normalized.png`
   - Main D1 story: drift grows differently by Toro case and compiler/implementation axis.
2. `experiments/week7/report1_variation/summary.md`
   - Variation matrix for O2/O3/Ofast, HLLC branch rule, and solver differences.
3. `experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md`
   - Direct CPU-vs-GPU reproducibility quantification for the selected Toro3/Toro5 1D cases.
4. `experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md`
   - Direct CPU-vs-GPU reproducibility quantification for the LW3 2D case.
5. `experiments/week7/report1_validation_2d/figures/lw3_n400_double_rho_schlieren.png`
   - Main 2D validation visual.
6. `experiments/week8/report1_2d_config12_fill/summary.md`
   - Second 2D Riemann validation summary, including CPU/GPU zero drift and fp32/fp64 reference-scaled ratios.
7. `experiments/week8/report1_2d_config12_fill/figures/lw12_n400_double_rho_schlieren.png`
   - Main second-2D-case visual.
8. `experiments/week7/report1_d2_replots/float_double_over_reference_bar.png`
   - Clear p24 adequacy comparison without relying on the old Pareto plot.
9. `experiments/week7/report1_d2_replots/region_losos_margin_rho_p32.png`
   - Region-aware precision-adequacy margin.
10. `experiments/week7/report1_d2_replots/noise_to_error_ratio_heatmap_grid_rho.png`
   - Spatial SNR/noise-to-error interpretation across p8, p16, and p32.

## Planned supplementary experiments

These runs were identified during the Report 1 plan review as evidence-chain gaps that, when filled, materially strengthen §5.5, §5.6, §3.5, and §6.3. Current status is recorded in the table. If a run does not complete in time for drafting, the corresponding section keeps its existing scoped wording without claiming the unrun evidence.

Naming convention: in prose, write "Liska-Wendroff configuration 12 (LW12)" — never "config12". Directory names below retain the existing experiment-folder convention for evidence-location traceability only.

| Planned artifact | Priority | Specification | Consumed by |
|---|---:|---|---|
| `experiments/week9/cpu_gpu_midtime/summary.md`; `experiments/week9/cpu_gpu_midtime_n400/summary.md` | P0 (completed) | Intermediate-time CPU vs GPU snapshots on Sod, LW3, and LW12 under `solver=hllc`, `STRICT_IEEE=ON`. Reports L1, Linf, and ULP_max between matched CPU and GPU binaries at saved checkpoints. | §5.5 (bounds the "final-time only" caveat with one optional table row); §6.3 (whether device drift accumulates in time). |
| `experiments/week9/variation_fp32/summary.md`; `experiments/week9/variation_fp32_extend/summary.md` | P0 (completed) | fp32 × compiler-flag mini-matrix on Sod, Toro3, Toro5, and LW3. CPU only. Axes: O2 vs O3 and O2 vs Ofast+fast-math. | §5.6a (one fp32 table); §6.3 (comparison of "compiler effect vs precision effect"). |
| `experiments/report1_limiter_variation_optin/summary.md` | P1 (completed) | CPU-only opt-in limiter variation after adding a default-preserving `limiter` cfg key. Matrix compares minbee with van Leer on Sod, Toro3, Toro5, and LW3 N=200. | §3.5 / §5.6 / appendix support; use as a method-sensitivity bound, not as hardware or same-solver reproducibility evidence. |
| `experiments/report1_shock_bubble_support/summary.md` | P1 (completed) | CPU-only shock-bubble support packet, fp64/fp32 and HLLC/Rusanov at 400x100. No exact/high-resolution reference strategy is claimed. | Appendix/support; optional one-sentence discussion only if space remains. |

Each summary must follow the same structure as the existing `report1_variation/summary.md`: case, axis, precision, hardware, L1/Linf/ULP_max for the conservative state at final time (or per-checkpoint for the intermediate-time experiment), plus a one-sentence interpretation. None of these runs is required to ship Report 1, but each is required to claim the corresponding strengthened conclusion in §5.5/§5.6/§3.5/§6.3.

## Recommended exclusions from the main text

- Raw grids, `grid.bin`, intermediate `sample_*` files, and unaggregated run folders:
  keep as provenance, do not cite directly.
- Original Pareto-only figures from Week 4/Week 7:
  they are mathematically defensible but hard to explain and were already
  identified as confusing.
- `vfc_precexp/` full-solver results:
  failed/not_reported, so do not present as a successful result.
- Download bundles and duplicate copied outputs:
  cite canonical experiment folders instead.
