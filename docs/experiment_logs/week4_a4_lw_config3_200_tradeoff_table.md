# LW Config 3 — Tradeoff conclusion (N=200², headline row = ρ)

| Solver  | Precision   | μ_trunc_L1 | σ_FP_L1 | s_worst_q05 | s_req(N) | s_worst − s_req | regime |
|---------|-------------|-----------:|--------:|------------:|---------:|----------------:|--------|
| HLLC    | p24-real-float | 2.773e+02 | 2.956e-02 | 1.54 | 3.13 | -1.59 | round-off-limited |
| HLLC    | p53         | 2.773e+02 | 5.216e-11 | 1.54 | 3.13 | -1.59 | round-off-limited |
| RUSANOV | p24-real-float | 4.180e+02 | 8.199e-03 | 1.23 | 2.95 | -1.72 | round-off-limited |
| RUSANOV | p53         | 4.180e+02 | 2.278e-11 | 1.23 | 2.95 | -1.72 | round-off-limited |

**Notes:**

- All values shown for the ρ variable; full per-variable breakdown is in `experiments/week4/metrics/s_req_lw_config3_200.csv` and `experiments/week4/metrics/losos_lw_config3_200.csv`.
- `μ_trunc_L1` is reference-anchored (candidate 200² minus 800² block-averaged reference, primitive variables); the column overrides the self-referenced value present in `snr_scalars.csv`.
- `s_worst_q05 = min(s_reliability, s_accuracy)` 5th-percentile over cells; the LoSoS reference is the same 800² block-averaged primitive `.npz` produced by `s_req_metric.py`. No upper-bound footnote is needed in this round.
- `regime` is classified by `s_worst − s_req`: `> 2.0 = over-provisioned`, `(1.0, 2.0] = well-matched`, `(0, 1.0] = marginal`, `≤ 0 = round-off-limited`. Thresholds in `scripts/_tradeoff_thresholds.py`.
- Included precision labels: p24-real-float, p53. Each non-p53 row must come from an MCA ensemble, not a single deterministic float run.
- For the headline ρ row, `s_worst_q05` is accuracy-limited rather than reliability-limited, so p24 and p53 share the same `s_worst_q05` and regime. The precision effect is still visible in `σ_FP_L1`: p24-real-float raises HLLC ρ noise from `5.216e-11` to `2.956e-02`, and Rusanov ρ noise from `2.278e-11` to `8.199e-03`.
- Athena execution details and image-reading notes are archived in `docs/experiment_logs/week4_a4_p24_real_float_execution_summary.md` and `docs/experiment_logs/week4_a4_p24_real_float_readme.md`. Generated p24 heatmaps live under `experiments/week4/figures/a4_float_p24/`.
