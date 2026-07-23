# Regression And Summary Scripts

This directory contains validation scripts and scalar summary generators.

## Preferred For New Harness Runs

- `matrix_summary_report.py`: consumes `matrix_summary.json` produced by
  `scripts/run_matrix.py`. Use this for Report 2 matrix-based experiments.
- `convergence.py`: convergence helper for exact/reference comparisons.
- `verify_sod.py`, `verify_toro.py`: exact-solution validation helpers.

## Report 2 MHD Validation

- `_mhd_harness.py`: shared Week 13 MHD subprocess, metadata, binary-read, and
  scalar-helper layer used by the 2D validation drivers.
- `mhd_orszag_tang_2d.py`, `mhd_kh_2d.py`: HLL production validation/figure
  drivers for the Week 13 2D MHD benchmarks.
- `mhd_solver_compare_2d.py`: HLL-vs-HLLD Orszag-Tang diagnostic used for the
  Week 13 deferred-HLLD decision; do not treat HLLD as the production solver
  unless a later summary records a new decision.
- `mhd_hlld_glm_sweep.py`, `mhd_hlld_diagnostics.py`: local HLLD diagnostics,
  not production validation.
- `mhd_paper_style_mk2005.py`: optional matplotlib renderer for paper-style
  Week 13 figures; it consumes existing Week 13 binary grids and intentionally
  stays separate from the numpy-only validation drivers.
- `mhd_orszag_tang_precision_smoke.py`: Week-15 solver-aware Orszag-Tang 2D
  precision packets (`--solver hll|hlld` x `--profile gate|headline` x
  `--phase p0|p1`): deterministic build fan (P0=8 variants, P1=24 variants
  adding O3 + fastmath) vs the same-solver fp64 reference, with an anchor gate
  from the HLLD div(B) follow-up and a soft `gates.G1.ordering_flags`
  fastmath-vs-ieee check; MCA recorded separately via
  `scripts/verificarlo/mhd_precision_sampling.py --case ... --samples N`
  (n=3 smoke in `mca/`, n=30 depth in `mca_n30/`).
- `mhd_temporal_divergence.py`: runs fp32-vs-fp64 HLL time slices for Brio-Wu
  1D and Orszag-Tang 2D, fits Lyapunov-like density-drift growth rates, and
  writes `experiments/week15/mhd_temporal_divergence/summary.{json,csv,md}`
  plus `figures/temporal_divergence.png`. Before the full run, use
  `mhd_temporal_divergence.py --smoke --out experiments/week15/mhd_temporal_divergence_smoke`
  so diagnostic output cannot overwrite canonical evidence.
  With the default output, `--smoke` and `--case` are also routed automatically
  to `_smoke`, `_<case>`, or `_<case>_smoke` sibling directories; passing the
  canonical output explicitly does not bypass this protection. An explicit
  noncanonical `--out` is honored. `gates.pass` is the report-grade gate;
  diagnostic packets always have `mode=diagnostic` and `pass=false` while
  retaining a separate `technical_pass` result.
  The fixed-window evidence does not show the planned OT>Brio-Wu L1 contrast;
  neither gate is a physical-ordering claim.
- `mhd_gpu_hardware_axis.py`: Week-16 matched HLL CPU/GPU evidence driver for
  Brio-Wu 1D and Orszag-Tang 2D in float and double. It writes
  `experiments/week16/cpu_gpu_hardware_axis/summary.{json,csv,md}` plus
  figures, removes generated grids after measurement, and gates on exact
  same-precision CPU/GPU output (`ulp_max=0`) for the covered cases.
- `mhd_kh_precision.py`: Week-16 KH deterministic precision driver for HLL and
  HLLD. Use `--smoke --phase p0` before a full `--phase p1` run. The current
  Windows workstation records MCA as `blocked_environment` when Docker is not
  available, so no KH MCA claim is made from that packet.
- `mhd_512_consolidation.py`: reads the completed Orszag-Tang and
  Kelvin-Helmholtz 256^2-vs-512^2 validation summaries and writes
  `experiments/week16/ot_kh_512_consolidation/summary.{json,csv,md}`. Its
  gate is a bounded engineering sensitivity checkpoint, not an asymptotic
  convergence claim.

## Compatibility / Provenance

- `float_regression_report.py`: still useful and tested, but tied to the older
  Week 4/Report 1 float-regression layout.
- `float_regression_1d.sh`, `float_regression_2d.sh`: historical regression
  drivers for the Report 1 evidence base.
- `report1_1d_feature_validation.py`: compatibility wrapper for the archived
  Report 1 feature-validation artefact.
- `run_comparison.py`: compatibility wrapper for the older HLLC-vs-Rusanov
  comparison path.

For new Report 2 work, avoid adding new output-layout assumptions to the
compatibility scripts. Prefer adding metrics in `scripts/metrics/` and reporting
through `matrix_summary_report.py`.
