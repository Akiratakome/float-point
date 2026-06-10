# Regression And Summary Scripts

This directory contains validation scripts and scalar summary generators.

## Preferred For New Harness Runs

- `matrix_summary_report.py`: consumes `matrix_summary.json` produced by
  `scripts/run_matrix.py`. Use this for Report 2 matrix-based experiments.
- `convergence.py`: convergence helper for exact/reference comparisons.
- `verify_sod.py`, `verify_toro.py`: exact-solution validation helpers.

## Compatibility / Provenance

- `float_regression_report.py`: still useful and tested, but tied to the older
  Week 4/Report 1 float-regression layout.
- `float_regression_1d.sh`, `float_regression_2d.sh`: historical regression
  drivers for the Report 1 evidence base.
- `report1_1d_feature_validation.py`: Report 1 feature-validation artefact.
- `run_comparison.py`: older HLLC-vs-Rusanov comparison path.

For new Report 2 work, avoid adding new output-layout assumptions to the
compatibility scripts. Prefer adding metrics in `scripts/metrics/` and reporting
through `matrix_summary_report.py`.
