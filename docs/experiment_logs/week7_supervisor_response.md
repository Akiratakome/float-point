# Week 7 Supervisor Response

## Criterion for the regime label

The current A4 table labels a row using

`margin = s_worst_q05 - s_req(N)`.

Here `s_req(N) = -log10(||E_trunc(N)||_1) + 1`, so it is a truncation-anchored target for how many significant digits the FP path needs to avoid dominating the grid-resolution error. A negative margin means the 5th-percentile worst-cell significant-digit estimate is below that target.

For Report 1, describe this first as a precision-adequacy margin before calling it round-off limited. The phrase round-off limited can be misleading when the same row also has truncation-dominated bulk error. The safer sentence is: "at this resolution, the significant-digit margin is below the truncation anchored target, while the bulk L1 error remains dominated by truncation."

No code or output-format change is required for this terminology clarification. Future outputs may add an explicit `precision_margin` column if needed, but the existing `regime` column should remain unchanged for traceability.

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
