# Week 4 Summary

**Date**: 2026-04-29
**Branch**: `week4-implementation`
**Plan**: [week4-plan.md](week4-plan.md)
**Verification recipe**: [week4-verification.md](week4-verification.md)

This document summarises what was actually delivered in Week 4 (calendar 04/22–04/28), grouped by sub-phase. For raw experiment logs see [docs/experiment_logs/](../experiment_logs/); for supervisor correspondence see [docs/emails/](../emails/).

---

## Phase A — Non-Week-4 supervisor asks (delivered)

### A1: Rusanov as default solver
- cfg-layer change: `solver = rusanov` is the default unless overridden.
- Detailed log: [week4_a4_lw_config3_200_tradeoff_table.md](../experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md) (covers comparison context).

### A2: divergence-marker tool — two-stage delivery
- Stage 1 (visible mode, supervisor-facing first cut): see email [week4_email_a2_s1_2026-04-22.md](../emails/week4_email_a2_s1_2026-04-22.md).
- Stage 2 (MCA p=53 noise-floor statistical batch): logs [week4_a2_s2_noise_floor_delivery.md](../experiment_logs/week4_a2_s2_noise_floor_delivery.md) and [week4_a2_noise_floor_calibration.md](../experiment_logs/week4_a2_noise_floor_calibration.md).
- Tooling: `scripts/plot_divergence_marker.py` (3 modes), `scripts/noise_floor_run.sh`, `scripts/compute_noise_floor.py`.

### A3: 2D Verificarlo on Liska–Wendroff Config 3
- Production: 200²×30 SLURM array, /dev/urandom seed CSV (no flock).
- Feasibility & report: [week4_a3_2d_vfc_feasibility.md](../experiment_logs/week4_a3_2d_vfc_feasibility.md), [week4_a3_2d_vfc_report.md](../experiment_logs/week4_a3_2d_vfc_report.md).
- 800² double reference workflow (used as ground truth for both A4 and Phase C1 2D): [week4_a3_800_reference_workflow.md](../experiment_logs/week4_a3_800_reference_workflow.md).

### A4: SNR / LoSoS metric + truncation-anchored s_req(N) + Pareto + headline conclusion
- Headline table: [week4_a4_lw_config3_200_tradeoff_table.md](../experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md).
- Pareto figure: [experiments/week4/figures/a4_pareto/pareto_lw_config3_200.png](../../experiments/week4/figures/a4_pareto/pareto_lw_config3_200.png) (HLLC vs RUSANOV at N=200² double; both points sit below `s_req(N=200) ≈ 3.13`, i.e. FP noise dominates truncation at this resolution — answers supervisor "how many sig digits do we need").
- Tooling: `scripts/snr_metric.py`, `scripts/losos_metric.py`, `scripts/s_req_metric.py`, `scripts/pareto_plot.py`, `scripts/tradeoff_summary_table.py`.

---

## Phase B — Week-4 core (overall.md 266–275) — committed

| Item | Commits | Status |
|---|---|---|
| B1 PrecisionConfig + EulerSolver split + TimeReal=double | `25ed579`, `79e4d18`, `38314d2` | done |
| B2 periodic + reflective BC (`std::array` flip indices) | `d38d774` | done |
| B3 BoundaryType enum + cfg `bc_x`/`bc_y` parsing (per-axis dispatch) | `d38d774`, `6b5d1dd` | done |
| B4 Catch2 unit tests (10 cases / 572 assertions) | `d38d774` | done |

**Verification (re-run 2026-04-28)**:
- Both `build-double` and `build-float` build cleanly (gcc/MSYS, ninja, OpenMP on)
- Unit tests: **115 cases / 3660 assertions PASS** in both precisions
- Sod 1D end-to-end matches Week-3 baseline in double; float in expected ULP range

Implementation deviation note (documented at [week4-plan.md §B3](week4-plan.md)): the planned single-call `apply_boundary(grid, bc_x, bc_y, flips_x, flips_y)` dispatcher was replaced by per-axis primitives (`apply_outflow_bc(grid, Axis::X, ...)` etc.) plus a switch-based dispatcher inside `EulerSolver::apply_boundary_conditions()`. Functionally equivalent; cleaner extension path to Week-12 MHD.

---

## Phase C — float regression — delivered

### C1.1 — 1D Toro 6-case float regression — done
- 12 CSVs, 5 resolutions each (50/100/200/400/800).
- Raw log: [week4_c1_float_vs_double_regression.md](../experiment_logs/week4_c1_float_vs_double_regression.md).
- Output: [experiments/week4/float_regression/1d/summary.md](../../experiments/week4/float_regression/1d/summary.md). All float/double ratios ≈ 1.000 at N=800: float is sufficient for 1D Toro in the truncation-dominated regime.

### C1.2 — 2D LW Config 3 float regression — done
- `reference_800.bin` (20.5 MB; 1388 steps, 16:34 wall time).
- Candidates: 200²/400² × {double, float}. Differences < 1e-4 between same-resolution float vs double.
- Phase metrics: SSIM ≥ 0.97, L1_rho halves on N→2N (first-order conv).
- Heatmaps: 16 PNGs in `experiments/week4/float_regression/2d/phase_error_heatmaps/`.
- Output: [experiments/week4/float_regression/2d/summary.md](../../experiments/week4/float_regression/2d/summary.md).

### C2 — Verificarlo real-float vs VPREC p24 — done
- Cluster run + analysis completed; main result file: [c2_real_float_vs_vprec.md](../experiment_logs/c2_real_float_vs_vprec.md).
- Tooling used: `scripts/figures/plot_real_vs_vprec.py`, `scripts/verificarlo/verificarlo_run.sh --compare-float`.
- Artifacts: `experiments/verificarlo/runs_compare_p24_mca_real_vs_double/` (+ `_fma`, `_rusanov` variants), with per-case overlays and JSON summaries.

---

## Side-effects from Week 4 review (committed 2026-04-28)

- `src/utils/io.hpp`: `write_binary` auto-creates parent directory (cfgs with nested `output_file` paths now work standalone).
- `scripts/float_regression_{1d,2d}.sh`: handle `.exe` suffix on MSYS + skip Microsoft-Store Python stub.

---

## Bridge from Week 3
[week3_to_week4_bridge.md](week3_to_week4_bridge.md) records the migration of Week-3 deliverables that affected Week-4 starting state (Verificarlo p24 numerics, Sod baseline, Rusanov solver wiring).

---

## Outstanding for Week 5

- Begin 2D Liska–Wendroff Configs 4/6 + Kelvin–Helmholtz (now that BC dispatch supports periodic + reflective, see plan §7.1).
- GPU development start (plan §7.1, §7.2).
