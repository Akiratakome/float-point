# Week 7 Supervisor Response

## Criterion for the regime label

The current A4 table labels a row using

`margin = s_worst_q05 - s_req(N)`.

Here `s_req(N) = -log10(||E_trunc(N)||_1) + 1`, so it is a truncation-anchored target for how many significant digits the FP path needs to avoid dominating the grid-resolution error. A negative margin means the 5th-percentile worst-cell significant-digit estimate is below that target.

For Report 1, describe this first as a precision-adequacy margin before calling it round-off limited. The phrase round-off limited can be misleading when the same row also has truncation-dominated bulk error. The safer sentence is: "at this resolution, the significant-digit margin is below the truncation anchored target, while the bulk L1 error remains dominated by truncation."

No code or output-format change is required for this terminology clarification. Future outputs may add an explicit `precision_margin` column if needed, but the existing `regime` column should remain unchanged for traceability.
