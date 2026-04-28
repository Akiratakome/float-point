# LW Config 3 — Tradeoff conclusion (N=200², headline row = ρ)

| Solver  | Precision   | μ_trunc_L1 | σ_FP_L1 | s_worst_q05 | s_req(N) | s_worst − s_req | regime |
|---------|-------------|-----------:|--------:|------------:|---------:|----------------:|--------|
| HLLC    | p53         | 2.773e+02 | 5.216e-11 | 1.54 | 3.13 | -1.59 | round-off-limited |
| RUSANOV | p53         | 4.180e+02 | 2.278e-11 | 1.23 | 2.95 | -1.72 | round-off-limited |

**Notes:**

- All values shown for the ρ variable; full per-variable breakdown is in `experiments/week4/metrics/s_req_lw_config3_200.csv` and `experiments/week4/metrics/losos_lw_config3_200.csv`.
- `μ_trunc_L1` is reference-anchored (candidate 200² minus 800² block-averaged reference, primitive variables); the column overrides the self-referenced value present in `snr_scalars.csv`.
- `s_worst_q05 = min(s_reliability, s_accuracy)` 5th-percentile over cells; the LoSoS reference is the same 800² block-averaged primitive `.npz` produced by `s_req_metric.py`. No upper-bound footnote is needed in this round.
- `regime` is classified by `s_worst − s_req`: `> 2.0 = over-provisioned`, `(1.0, 2.0] = well-matched`, `(0, 1.0] = marginal`, `≤ 0 = round-off-limited`. Thresholds in `scripts/_tradeoff_thresholds.py`.
- HLLC float / Rusanov float rows are intentionally omitted this round; they require the B1 PrecisionConfig refactor to land first.
