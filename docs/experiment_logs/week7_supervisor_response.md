# Week 7 Supervisor Response

## Criterion for the regime label

The current A4 table labels a row using

`margin = s_worst_q05 - s_req(N)`.

Here `s_req(N) = -log10(||E_trunc(N)||_1) + 1`, so it is a truncation-anchored target for how many significant digits the FP path needs to avoid dominating the grid-resolution error. A negative margin means the 5th-percentile worst-cell significant-digit estimate is below that target.

For Report 1, describe this first as a precision-adequacy margin before calling it round-off limited. The phrase round-off limited can be misleading when the same row also has truncation-dominated bulk error. The safer sentence is: "at this resolution, the significant-digit margin is below the truncation anchored target, while the bulk L1 error remains dominated by truncation."

No code or output-format change is required for this terminology clarification. Future outputs may add an explicit `precision_margin` column if needed, but the existing `regime` column should remain unchanged for traceability.

## Why Rusanov can look cleaner

Rusanov is more diffusive than HLLC. Extra dissipation smooths sharp gradients
and reduces local amplification of round-off noise near shocks and contacts.
The plausible mechanism is not more accurate physics; it damps high-frequency
structure before EOS pressure calculation and reconstruction stages can amplify
small perturbations.

This is an interpretation of measured data, not a solver recommendation: HLLC
remains sharper and generally more accurate in these validation tests.

Supporting rho-only derived check for LW Config 3 at 200^2, computed from:

- `experiments/week4/metrics/a4_snr_with_float.csv`
- `experiments/week4/metrics/a4_losos_with_float.csv`
- `experiments/week4/metrics/s_req_lw_config3_200.csv`

| Precision | sigma_FP_L1 HLLC | sigma_FP_L1 Rusanov | sigma ratio HLLC/Rusanov | truncation penalty Rusanov/HLLC | s_worst_q05 HLLC | s_worst_q05 Rusanov | digit delta Rusanov-HLLC |
|---|---:|---:|---:|---:|---:|---:|---:|
| p53 | 5.216e-11 | 2.278e-11 | 2.29 | 1.51 | 1.542 | 1.230 | -0.312 |
| p24-real-float | 2.956e-02 | 8.199e-03 | 3.60 | 1.51 | 1.542 | 1.230 | -0.312 |

The truncation penalty uses the rho `mu_trunc_l1` ratio from
`s_req_lw_config3_200.csv`; the same ratio is obtained from `E_trunc` because
both values share the same reference normalization. A copy of this derived
calculation is saved in `experiments/week7/rusanov_noise/summary.csv`.

| Evidence | Interpretation |
|---|---|
| Rusanov has larger deterministic truncation error than HLLC: rho `mu_trunc_l1` is 418.0 vs 277.3, a 1.51x penalty. | Cleaner noise is bought by diffusivity, not by a more accurate physical solution. |
| Rusanov has lower `sigma_FP_L1` in the LW3 rho rows: 2.278e-11 vs 5.216e-11 at p53, and 8.199e-03 vs 2.956e-02 at p24-real-float. | Round-off variance is damped by the smoother numerical state. |
| C2 shows pressure and other variables are most sensitive near discontinuities; on Sod, Rusanov is about 0.2 significant digits cleaner than HLLC. | EOS subtraction remains a likely amplification point, and smoothing discontinuities can reduce the measured variance before EOS and reconstruction effects grow. |
| Stationary-contact `u` in C2 is degenerate/noise-floor: the sign of the real-vs-double gap flips between HLLC and Rusanov and should not be overread. | The cleaner-Rusanov statement should be based on non-degenerate rho/p and Sod-style flow, not near-zero relative metrics. |
| Rusanov fails or degrades where excessive diffusion is harmful, including the earlier near-vacuum Toro 2 failure and smeared stationary-contact density. | Noise reduction is not general superiority; it is a trade-off against sharp contact and shock resolution. |

## Task 5 - Full Pareto Example For Philip

Generated artefacts:

- `experiments/week7/pareto_full/pareto_lw3_full_logx.png`
- `experiments/week7/pareto_full/pareto_lw3_full_twopanel.png`
- `experiments/week7/pareto_full/pareto_lw3_full.csv`
- `experiments/week7/pareto_full/summary.md`

The Pareto plot demonstrates the trade-off between emitted FP noise
(`sigma_FP_L1`, x-axis) and delivered significant digits (`s_worst_q05`,
y-axis). The horizontal `s_req(N)` target marks the significant digits implied
by truncation error at the same grid resolution. This is the precision demand
that the FP path should meet if it is not to fall below the truncation-anchored
target.

Log scaling on the FP-noise axis is required because p24-real-float and p53
differ by many orders of magnitude in emitted noise. In the Week 4 A4 headline
rho rows reused here, p24-real-float moves the point far to the right while
the delivered `s_worst_q05` remains below `s_req(N)`. The two-panel output
therefore shows both the raw trade-off and the precision-adequacy margin
`s_worst_q05 - s_req(N)`.

No Verificarlo rerun was performed. The script reuses:

- `experiments/week4/metrics/a4_snr_with_float.csv`
- `experiments/week4/metrics/a4_losos_with_float.csv`
- `experiments/week4/metrics/s_req_lw_config3_200.csv`
