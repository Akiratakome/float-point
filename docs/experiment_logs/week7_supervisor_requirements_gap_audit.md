# Week 7 Supervisor Requirements Gap Audit

Purpose: classify the four supervisor-requested follow-ups before refreshing Verificarlo figures. This note audits existing artefacts only; it does not change solver numerics, cfg defaults, or experiment results.

| requirement | status | evidence | next action |
|---|---|---|---|
| `vfc_precexp` per-function precision analysis | partial only | `experiments/verificarlo/precexp/prec_*` contains whole-program precision-labelled outputs plus `exrun`/`excmp`, not a function or call-site precision table | plan a CSC `vfc_precexp` rerun with function/call-site reporting |
| GPU porting guided by FP bottleneck finding | GPU port complete for Euler validation; mixed precision not implemented | `src/gpu/*`, `experiments/week6/regression/summary.md`, `experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md` | keep this as design evidence; do not change kernels in this figure-refresh task |
| 2D Verificarlo analysis | completed for LW3, with caveats | `docs/experiment_logs/week4_a3_2d_vfc_report.md`, `experiments/week7/metrics/precision_sweep_summary.md`, `experiments/week7/metrics/p*/` | consolidate figures and label Week 7 p8/p16/p32 as exploratory |
| point-style HLLC/Rusanov plots | completed as new artefacts | `scripts/figures/plot_hllc_rusanov_points.py`, `experiments/week7/verificarlo_report1_refresh/figures/hllc_rusanov_points_*.png` | use new point-style figures beside existing historical plots |

## Existing `vfc_precexp` Artefact Boundary

The existing `exrun` runs a Sod case at a requested output directory, and `excmp` applies a global density L1 relative-error threshold. The `prec_*` outputs are therefore suitable only as a coarse whole-program precision sweep. They must not be cited as completed per-function analysis.
