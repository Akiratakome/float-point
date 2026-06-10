# Verificarlo Scripts

This directory contains Verificarlo/MCA and precexp experiment drivers.

## Preferred Current Pieces

- `precexp_manifest.py`
- `precexp_prepare_cfg.py`
- `precexp_compare.py`
- `precexp_aggregate.py`

These match the newer manifest/config/compare/aggregate style and are covered by
pytest.

## Older Provenance Entry Points

- `verificarlo_run.sh`
- `verificarlo_run_2d.sh`
- `verificarlo_analysis.py`
- `verificarlo_analysis_2d.py`
- `verificarlo_vs_exact.py`
- `noise_floor_run.sh`
- `noise_floor_all.sh`

Keep these for reproducing Report 1 evidence, but do not assume their default
output roots or precision labels are suitable for Report 2. Promote reusable
analysis logic into `scripts/metrics/` before using it in a new pipeline.
