# Week 16 Summary: Temporal Divergence

> Current evidence status is maintained in the [Report 2 evidence map](../experiment_logs/report2_evidence_map.md).

Only phase 1, temporal divergence, is complete. Its authority is
[experiments/week15/mhd_temporal_divergence/summary.md](../../experiments/week15/mhd_temporal_divergence/summary.md):
80 successful provenance-complete runs provide 15 paired Brio-Wu samples and
25 paired Orszag-Tang samples.

The result is an unexpected bounded `negative-result`: fixed-window,
fp32-vs-fp64 Lyapunov-like engineering fits did not observe the planned
OT > Brio-Wu contrast. It does not claim a formal maximal Lyapunov exponent,
a physical instability rate, or a general OT/KH ordering.

The GPU HLL MHD prerequisite is now implemented behind `-DENABLE_CUDA=ON`:
`device=gpu` is available for `hrsc_mhd` HLL runs, with Brio-Wu 1D and
Orszag-Tang 2D CPU-vs-GPU validation in float and double. This is a solver
validation gate, not yet the matched hardware-axis experiment packet.

The following work is still incomplete: matched CPU/GPU hardware-axis evidence,
KH report-grade precision evidence, and OT/KH 512^2 consolidation. Their current
status and dependencies are recorded in the [Report 2 evidence map](../experiment_logs/report2_evidence_map.md).
