# Week 16 Summary: Evidence Completion

> Current evidence status is maintained in the [Report 2 evidence map](../experiment_logs/report2_evidence_map.md).

Phase 1, temporal divergence, is complete. Its authority is
[experiments/week15/mhd_temporal_divergence/summary.md](../../experiments/week15/mhd_temporal_divergence/summary.md):
80 successful provenance-complete runs provide 15 paired Brio-Wu samples and
25 paired Orszag-Tang samples.

The result is an unexpected bounded `negative-result`: fixed-window,
fp32-vs-fp64 Lyapunov-like engineering fits did not observe the planned
OT > Brio-Wu contrast. It does not claim a formal maximal Lyapunov exponent,
a physical instability rate, or a general OT/KH ordering.

The GPU HLL MHD prerequisite is implemented behind `-DENABLE_CUDA=ON`:
`device=gpu` is available for `hrsc_mhd` HLL runs, with Brio-Wu 1D and
Orszag-Tang 2D CPU-vs-GPU validation in float and double.

The matched hardware-axis packet is complete at
[experiments/week16/cpu_gpu_hardware_axis/summary.md](../../experiments/week16/cpu_gpu_hardware_axis/summary.md):
all four covered HLL CPU/GPU rows have `ulp_max=0`; OT speedups are 5.965x
double and 6.353x float, while 1D Brio-Wu remains launch-overhead dominated.

KH has a completed 512^2 validation gate and deterministic precision packets:
[validation](../../experiments/week16/kelvin_helmholtz_precision/validation/summary.md),
[HLL P1](../../experiments/week16/kelvin_helmholtz_precision/hll_p1/summary.md),
and [HLLD P1](../../experiments/week16/kelvin_helmholtz_precision/hlld_p1/summary.md).
The deterministic gates pass, but MCA is blocked by the local Docker daemon, so
no KH MCA noise-floor or report-grade deterministic-plus-MCA claim is made.

OT/KH 512^2 consolidation is complete at
[experiments/week16/ot_kh_512_consolidation/summary.md](../../experiments/week16/ot_kh_512_consolidation/summary.md).
Both self-reference gates pass, and the package explicitly records that two
resolutions do not establish asymptotic convergence.
