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
  precision packets (`--solver hll|hlld` x `--profile gate|headline`):
  deterministic P0 build fan vs the same-solver fp64 reference with an anchor
  gate from the HLLD div(B) follow-up; MCA recorded separately via
  `scripts/verificarlo/mhd_precision_sampling.py --case`.

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
