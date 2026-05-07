# Email draft: Week-7 progress update (2026-05-07)

**To:** Philip Blakely (supervisor)
**From:** Yudong Tang
**Subject:** Week 7 progress - supervisor-response evidence, drift smoke, Pareto example, and Report 1 framing
**Status:** Draft only; not sent.

---

Dear Philip,

This week I treated the supervisor-response items as Report 1 evidence preparation rather than as solver development. I have chosen **Direction 1 as the primary Report 1 line**: explain precision adequacy and implementation sensitivity using the existing Euler harness, rather than expanding the GPU/MHD scope now. The drift pipeline and final-state smoke are complete, the full p53 plus p24 Pareto example is produced, the degenerate-case policy is formalised, and the "round-off limited" wording is now clarified as a precision-adequacy margin. The important limitation is that the drift artefact is still a synchronized final-state smoke only: no growth rate has been fitted yet, because that requires exact aligned multi-time checkpoints or multiple exact-final-time runs.

## Per-ask responses

### Why can Rusanov look cleaner?

I wrote the interpretation note in [week7_supervisor_response.md](../experiment_logs/week7_supervisor_response.md), with a small supporting rho-only calculation saved at [experiments/week7/rusanov_noise/summary.csv](../../experiments/week7/rusanov_noise/summary.csv). The short version is that Rusanov's lower measured FP noise is consistent with its extra diffusivity: it damps sharp gradients before reconstruction and EOS pressure calculations can amplify perturbations. This is not a recommendation to prefer Rusanov; the same table records the deterministic truncation penalty relative to HLLC.

### What exactly does "round-off limited" mean here?

I have stopped using that phrase as the first explanation. The criterion is now stated as a precision-adequacy margin,

`margin = s_worst_q05 - s_req(N)`,

where `s_req(N)` is the truncation-anchored significant-digit target. Negative margin means the delivered cell-level significant digits are below that target, while the bulk error can still be truncation dominated. The clarification is in [week7_supervisor_response.md](../experiment_logs/week7_supervisor_response.md), and the older A4 table has a trailing terminology note at [week4_a4_lw_config3_200_tradeoff_table.md](../experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md) without changing its original columns.

### Should GPU work expand this week?

I kept GPU expansion out of scope. Week 6 already closed the strict CPU/GPU smoke path, and the Week 7 evidence index keeps those artefacts as validation evidence rather than opening new kernel work. The mapping is in [report1_evidence_index.md](../experiment_logs/report1_evidence_index.md).

### Can we show drift from small implementation changes?

The pipeline now compares synchronized outputs and rejects incompatible checkpoint times before measuring differences. The available result is a final-state smoke, not a fitted time series: [experiments/week7/drift/summary.md](../../experiments/week7/drift/summary.md). In this smoke, HLLC-vs-Rusanov gives nonzero final-state rho drift, while strict CPU/GPU rows in the existing Week 6 evidence remain zero or ULP-level. The interpretation table is in the Task 4 section of [week7_supervisor_response.md](../experiment_logs/week7_supervisor_response.md).

### How does precision adequacy inform the drift study?

The Task 4 table links final-state drift to `sigma_FP_L1`, Philip-ratio availability, and the precision-adequacy margin. This keeps the interpretation honest: a nonzero final-state difference is not automatically important unless it is read relative to truncation demand and emitted FP noise. The key table is in [week7_supervisor_response.md](../experiment_logs/week7_supervisor_response.md).

### Can I show a full Pareto example?

Yes. I generated a full LW3 example that includes p53 and p24-real-float rows, with both a single log-x version and a two-panel version:

- [pareto_lw3_full_logx.png](../../experiments/week7/pareto_full/pareto_lw3_full_logx.png)
- [pareto_lw3_full_twopanel.png](../../experiments/week7/pareto_full/pareto_lw3_full_twopanel.png)
- [pareto_lw3_full.csv](../../experiments/week7/pareto_full/pareto_lw3_full.csv)
- [summary.md](../../experiments/week7/pareto_full/summary.md)

No new Verificarlo run was needed; this reuses the Week 4 A4 metric rows.

### How are degenerate cases handled?

The policy is now explicit in [week7_supervisor_response.md](../experiment_logs/week7_supervisor_response.md). Ratio pass/fail metrics exclude zero or near-zero denominators. Per-cell relative significant-digit metrics near the noise floor are diagnostic, not pass/fail evidence. Density remains the safest stationary-contact variable, but even stationary-contact density can be excluded for Philip-style ratio evidence if the exact denominator is zero.

## Drift study results

The current drift artefact is [experiments/week7/drift/summary.md](../../experiments/week7/drift/summary.md). It reports two final-state rho comparisons:

| case | pair | final L1 | final Linf | lambda |
|---|---|---:|---:|---|
| sod | HLLC vs Rusanov CPU strict smoke | 4.134993e-03 | 5.809514e-02 | not fitted |
| lw3 | HLLC vs Rusanov CPU strict smoke | 1.229633e-02 | 1.841195e-01 | not fitted |

These are useful as pipeline and final-state sensitivity evidence, not as Lyapunov-style growth rates. To fit lambda properly, I need either synchronized multi-time output at exact aligned checkpoints or repeated runs that end at exactly matched final times. Until then, I will report lambda as `n/a` and avoid implying an extracted growth rate.

## Open questions for Week 8

1. For the Pareto figure, should Report 1 use the single-panel log-x plot, or the two-panel version that separates delivered digits from precision-adequacy margin?
2. Should the chaotic-extension drift run move to Orszag-Tang before the MHD schedule, or should I keep Week 8 focused on Euler evidence and writing?
3. For the Report 1 systematic sweep, which axes should be added or dropped first: branch rule, optimisation level, fast-math/FMA, CPU/GPU, or solver choice?
4. For degenerate stationary-contact cases, is density-only pass/fail evidence acceptable, with velocity kept as a diagnostic plot?

## Status note

Report 1 is due on 2026-05-29. Week 8 should begin writing against the evidence index, using the current Week 7 artefacts as the Report 1 map and leaving new experiment expansion to only the axes that directly strengthen the draft.

Best,
Yudong
