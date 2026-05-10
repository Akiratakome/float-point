# Week 7 Supervisor Response Evidence Log

Purpose: record Week 7 supervisor-response evidence for Report 1 without writing report prose.

Scope: Week 7 focuses on Report 1 evidence collection through the existing Euler harness. Solver numerics and existing cfg defaults are unchanged. One new cfg, `tests/cases/liska_wendroff_2d/config3_n1600.cfg`, supports the 1600^2 reference-candidate run without modifying existing defaults.

Inputs read for this log:

- `docs/emails/week7_progress_to_philip_2026-05-07.md`
- `docs/experiment_logs/report1_evidence_index.md`
- `docs/experiment_logs/week6_supervisor_response.md`

## Evidence Topics

### GPU validation

Evidence paths:

- Week 6 strict CPU/GPU regression: `experiments/week6/regression/summary.md`
- Week 6 CSC smoke: `experiments/week6/csc_smoke/summary.md`
- Week 7 2D GPU precision-axis summary: `experiments/week7/report1_validation_2d_gpu/summary.md`
- Week 7 HLLC strict CPU-to-GPU preflight: `experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md`

Interpretation: these artefacts support strict GPU-path validation and Report 1 harness provenance. They should not be overclaimed as general CPU/GPU equality evidence. The available strict rows show zero measured deltas for the recorded smoke/preflight cases, but that does not establish equality for every compiler, solver, resolution, or runtime condition.

### Float vs double validation

Evidence paths:

- Week 4 float-vs-double regression log: `docs/experiment_logs/week4_c1_float_vs_double_regression.md`
- Week 4 tradeoff table and precision-adequacy terminology note: `docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md`
- Week 4 metric inputs used by A4/Week 7 interpretation: `experiments/week4/metrics/a4_snr_with_float.csv`, `experiments/week4/metrics/a4_losos_with_float.csv`, `experiments/week4/metrics/s_req_lw_config3_200.csv`
- Week 7 1D precision-axis validation summary: `experiments/week7/report1_validation_1d/summary.md`
- Week 7 2D CPU precision-axis validation summary: `experiments/week7/report1_validation_2d/summary.md`
- Week 7 2D GPU precision-axis validation summary: `experiments/week7/report1_validation_2d_gpu/summary.md`

Current worktree note: the expected Week 4 summaries `experiments/week4/float_regression/1d/summary.md` and `experiments/week4/float_regression/2d/summary.md` are absent in this checkout, as recorded in `docs/experiment_logs/report1_evidence_index.md`. Report 1 can cite the Week 4 log and existing Week 4 metric artefacts, but those two summary files should be regenerated or recovered before claiming them as ready evidence.

### Compiler and implementation variation

Evidence paths:

- Variation summary: `experiments/week7/report1_variation/summary.md`
- Variation matrix: `experiments/week7/report1_variation/matrix.json`
- Variation matrix summary: `experiments/week7/report1_variation/matrix_summary.json`
- Axis notes: `experiments/week7/report1_variation/axis_leq_vs_strict.md`, `experiments/week7/report1_variation/axis_o2_vs_o3.md`, `experiments/week7/report1_variation/axis_o2_vs_ofast.md`, `experiments/week7/report1_variation/axis_hllc_vs_rusanov.md`

Interpretation: these artefacts route implementation sensitivity evidence across branch rule, compiler optimisation, fast-math, and solver-choice axes. They are evidence for the existing harness and selected cases only.

### 1600^2 GPU reference candidate

Evidence paths:

- Reference candidate summary: `experiments/week7/reference_1600/summary.md`
- Gate decision: `experiments/week7/reference_1600/gate_decision.md`
- Matrix summary: `experiments/week7/reference_1600/matrix_summary.json`
- Run matrix: `experiments/week7/reference_1600/matrix.json`
- Generated run cfg and metadata: `experiments/week7/reference_1600/runs/lw3-n1600-gpu-double-strict/config.cfg`, `experiments/week7/reference_1600/runs/lw3-n1600-gpu-double-strict/metadata.json`
- Source cfg: `tests/cases/liska_wendroff_2d/config3_n1600.cfg`

Interpretation: the 1600^2 artefact is a GPU high-resolution reference candidate for LW Config 3. It is anchored by Week 6 strict GPU smoke evidence and the Week 7 HLLC strict preflight, but it is not 1600^2 CPU-equivalent evidence. Do not claim 1600^2 CPU/GPU bit equality unless a matching 1600^2 CPU strict run is later produced and documented.

### Existing Week 7 evidence

Evidence paths:

- Rusanov noise note and derived calculation: `docs/experiment_logs/week6_supervisor_response.md`, `experiments/week7/rusanov_noise/summary.csv`
- Drift final-state smoke: `experiments/week7/drift/summary.md`, `experiments/week7/drift/summary.csv`, `experiments/week7/drift/summary.json`
- Full Pareto example: `experiments/week7/pareto_full/summary.md`, `experiments/week7/pareto_full/pareto_lw3_full.csv`, `experiments/week7/pareto_full/pareto_lw3_full_logx.png`, `experiments/week7/pareto_full/pareto_lw3_full_twopanel.png`
- Week 4 A4 tradeoff source used by Week 7: `docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md`, `experiments/week4/figures/a4_pareto/pareto_lw_config3_200.png`, `experiments/week4/figures/a4_float_p24/`
- Week 7 aggregate routing: `experiments/week7/report1_aggregate/summary.md`

Interpretation: these artefacts support supervisor-response routing for why Rusanov can look cleaner, how drift is currently measured, and how precision adequacy is presented through the Pareto view. They should be cited as evidence logs or experiment summaries, not as finished Report 1 prose.

### Degenerate stationary-contact policy

Evidence paths:

- Policy statement in prior supervisor-response notes: `docs/experiment_logs/week6_supervisor_response.md`
- Stationary-contact cfgs: `tests/cases/toro_1d/stationary_contact.cfg`, `tests/cases/toro_1d/stationary_contact_rusanov.cfg`
- Week 7 1D validation rows including stationary contact: `experiments/week7/report1_validation_1d/summary.md`
- Week 7 variation rows including stationary contact: `experiments/week7/report1_variation/summary.md`

Policy: ratios with zero or near-zero denominators are diagnostic or `n/a`, not pass/fail evidence. Philip-style ratios must exclude degenerate denominator rows. Per-cell relative significant-digit metrics near the noise floor are diagnostic. Absolute density is the safer stationary-contact quantity, but stationary-contact density can still be excluded from ratio evidence when the exact denominator is zero.

## Limitations

- Drift is currently a synchronized final-state smoke unless synchronized multi-time checkpoints or multiple exact-final-time samples are generated. Do not infer a fitted growth rate from the current drift artefact.
- Large transient grids are not retained except for promoted reference data. The 1600^2 binary grid remains a promoted GPU reference-candidate artefact, not a general transient-output retention policy.
- The Week 7 1600^2 run is GPU-only. It is not 1600^2 CPU/GPU bit-equality evidence and should not be described as CPU-equivalent.
- Week 4 float-regression summary files are absent in this worktree. Use the existing Week 4 logs/metrics carefully, and regenerate or recover the missing summaries before citing those specific paths as ready.
- Output formats remain stable; this log only records evidence routing and interpretation limits.
