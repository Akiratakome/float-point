# Week 15 Summary: CPU Precision Evidence

> Current evidence status is maintained in the [Report 2 evidence map](../experiment_logs/report2_evidence_map.md).

The following four CPU evidence sets each contain a 24-variant deterministic
fan plus separate N=30 MCA observations. All four remain `provisional`: no
machine-readable unified deterministic-plus-MCA gate or authoritative combined
summary currently promotes them to a Report 2 precision headline claim.

| Evidence set | Deterministic authority | MCA authority |
|---|---|---|
| Brio-Wu HLL | [summary.md](../../experiments/week15/brio_wu_precision_pilot_p1/summary.md) | [summary.json](../../experiments/week15/brio_wu_precision_pilot_p1/summary.json) |
| Brio-Wu HLLD | [summary.md](../../experiments/week15/brio_wu_precision_pilot_hlld_p1/summary.md) | [summary.json](../../experiments/week15/brio_wu_precision_pilot_hlld_p1/summary.json) |
| OT HLL | [headline256_p1 summary.md](../../experiments/week15/orszag_tang_precision_smoke/headline256_p1/summary.md) | [mca_n30 summary.json](../../experiments/week15/orszag_tang_precision_smoke/mca_n30/summary.json) |
| OT HLLD | [headline256_p1 summary.md](../../experiments/week15/orszag_tang_precision_smoke_hlld/headline256_p1/summary.md) | [mca_n30 summary.json](../../experiments/week15/orszag_tang_precision_smoke_hlld/mca_n30/summary.json) |

The six figures below are dated Week 15 presentation material, not current
status authorities: [Figure 1](figures/fig1_precision_axis.png),
[Figure 2](figures/fig2_mca_noise_floor.png),
[Figure 3](figures/fig3_compiler_axis.png), [Figure 4](figures/fig4_walltime.png),
[Figure 5](figures/fig5_ot_hll_reference_fields.png), and
[Figure 6](figures/fig6_ot_hll_fp32_drift.png).

GPU HLL MHD, the hardware axis, KH report-grade precision, and 512^2
consolidation remain deferred. Temporal divergence is routed to
[Week 16](../week16/week16-summary.md).
