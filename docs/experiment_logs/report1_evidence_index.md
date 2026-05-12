# Report 1 Evidence Index

Purpose: map Week-7 and supporting artefacts to the Report 1 narrative. This is an evidence routing index, not report prose.

## Evidence Map

| Report 1 section | Artefact | Path | State | Owner task |
|---|---|---|---|---|
| Section 2 Mathematical theory: schemes, HLLC vs Rusanov, variation points `<=`/`<` | Rusanov interpretation and supporting analysis | `docs/experiment_logs/week7_supervisor_response.md`; `experiments/week7/rusanov_noise/summary.csv` | new / ready | Task 1 |
| Section 2 Mathematical theory: schemes, HLLC vs Rusanov, variation points `<=`/`<` | A4 tradeoff table plus terminology note for precision-adequacy wording | `docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md` | ready / append note present | Task 2 |
| Section 3 Code description: precision templating, harness, GPU bring-up | CSC GPU smoke summary | `experiments/week6/csc_smoke/summary.md` | already produced / ready | Week 6 |
| Section 3 Code description: precision templating, harness, GPU bring-up | CPU vs GPU strict regression summary | `experiments/week6/regression/summary.md` | already produced / ready | Week 6 |
| Section 3 Code description: precision templating, harness, GPU bring-up | Drift pipeline final-state smoke metadata | `experiments/week7/drift/summary.md`; `experiments/week7/drift/summary.csv`; `experiments/week7/drift/summary.json` | new / final-state smoke | Task 3 |
| Section 4 Validation: 1D Toro, 2D LW3, CPU vs GPU, float vs double, convergence | 1D float regression Philip metric | `experiments/week4/float_regression/1d/summary.md` | missing in worktree / regenerate needed or recover external artefact | Week 4 |
| Section 4 Validation: 1D Toro, 2D LW3, CPU vs GPU, float vs double, convergence | 2D LW3 float regression | `experiments/week4/float_regression/2d/summary.md` | missing in worktree / regenerate needed or recover external artefact | Week 4 |
| Section 4 Validation: 1D Toro, 2D LW3, CPU vs GPU, float vs double, convergence | CPU vs GPU regression summary | `experiments/week6/regression/summary.md` | already produced / ready | Week 6 |
| Section 4 Validation: 1D Toro, 2D LW3, CPU vs GPU, float vs double, convergence | CSC GPU smoke summary | `experiments/week6/csc_smoke/summary.md` | already produced / ready | Week 6 |
| Cross-cutting: precision-adequacy / Pareto / drift evidence | Full Pareto example | `experiments/week7/pareto_full/pareto_lw3_full_*.png` | new / ready | Task 5 |
| Cross-cutting: Verificarlo precision sweep and supervisor-response figures | Week 7 Verificarlo refresh bundle | `docs/experiment_logs/week7_verificarlo_refresh.md`; `experiments/week7/verificarlo_report1_refresh/summary.md`; `experiments/week7/verificarlo_report1_refresh/figures/` | new / ready after refresh | Verificarlo refresh |
| Cross-cutting: precision-adequacy / Pareto / drift evidence | Precision-to-drift interpretation table | `docs/experiment_logs/week7_supervisor_response.md` | new / ready | Task 4 |
| Cross-cutting: precision-adequacy / Pareto / drift evidence | Drift time-series/final smoke summaries | `experiments/week7/drift/summary.md`; `experiments/week7/drift/summary.csv`; `experiments/week7/drift/summary.json` | new / final-state smoke; time-series fit not yet available | Task 3 |
| Cross-cutting: precision-adequacy / Pareto / drift evidence | A4 tradeoff table and terminology note | `docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md` | ready / append note present | Task 2 |
| Section 4 Validation: 1D Toro, 2D LW3, CPU vs GPU, float vs double, convergence / Cross-cutting: precision-adequacy | 1D precision-axis validation summary | `experiments/week7/report1_validation_1d/summary.md` | new / ready | Task 12 |
| Section 4 Validation: 1D Toro, 2D LW3, CPU vs GPU, float vs double, convergence | 2D CPU precision-axis validation summary | `experiments/week7/report1_validation_2d/summary.md` | new / ready | Task 12 |
| Section 4 Validation: 1D Toro, 2D LW3, CPU vs GPU, float vs double, convergence | 2D GPU precision-axis validation summary | `experiments/week7/report1_validation_2d_gpu/summary.md` | new / ready | Task 12 |
| Section 4 Validation: 1D Toro, 2D LW3, CPU vs GPU, float vs double, convergence | HLLC strict CPU-to-GPU preflight | `experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md` | new / ready | Task 12 |
| Section 2 Mathematical theory: schemes, HLLC vs Rusanov, variation points `<=`/`<` / Cross-cutting: implementation sensitivity | Compiler and implementation-axis variation summary | `experiments/week7/report1_variation/summary.md` | new / ready | Task 12 |
| Section 4 Validation: 1D Toro, 2D LW3, CPU vs GPU, float vs double, convergence | 1600^2 GPU reference candidate summary | `experiments/week7/reference_1600/summary.md` | new / ready | Task 12 |
| Section 3 Code description: precision templating, harness, GPU bring-up | Week 7 Report 1 aggregate evidence routing | `experiments/week7/report1_aggregate/summary.md` | new / ready | Task 12 |

## Gaps

| Gap | Impact | Next action |
|---|---|---|
| `experiments/week4/float_regression/1d/summary.md` is absent from this worktree. | Report 1 validation cannot cite the 1D float regression Philip metric from this checkout. | Regenerate with the Week-4 regression script or recover the external artefact before writing Section 4. |
| `experiments/week4/float_regression/2d/summary.md` is absent from this worktree. | Report 1 validation cannot cite the 2D LW3 float-vs-double regression summary from this checkout. | Regenerate with the Week-4 regression script or recover the external artefact before writing Section 4. |
| Drift evidence is a synchronized final-state smoke, not a fitted multi-time series. | Report 1 can use it as pipeline and final-state reproducibility evidence, but not as a growth-rate or Lyapunov-style claim. | Run synchronized multi-checkpoint drift jobs if a time-series claim is needed. |
| CPU/GPU strict smoke rows currently show zero final-state drift. | This supports GPU bring-up reproducibility, but does not demonstrate hardware-driven divergence. | Treat as a validation pass; use branch-rule, compiler, fast-math, or longer-window runs for divergence evidence. |
| Full Pareto example is present as PNG output only in this worktree. | Suitable for narrative figure placement, but final report captions should cite the metric source table when available. | Confirm final figure choice between `pareto_lw3_full_logx.png` and `pareto_lw3_full_twopanel.png` during Report 1 assembly. |
