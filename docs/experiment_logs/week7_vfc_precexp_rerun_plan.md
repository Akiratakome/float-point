# vfc_precexp Rerun Plan

Purpose: produce the missing per-function / per-call precision evidence requested by Philip. This is a future CSC Verificarlo task and is not part of the current result-refresh operation.

## Current Artefact Status

`experiments/verificarlo/precexp/` contains precision-labelled whole-program outputs and `exrun`/`excmp`, but no function-level precision assignment table. It must not be cited as completed per-function analysis.

## Required Rerun Output

| output | meaning |
|---|---|
| `experiments/week7/vfc_precexp/function_precision.csv` | function or call-site, minimum accepted precision, tested case, pass/fail criterion |
| `experiments/week7/vfc_precexp/summary.md` | report interpretation and limitations |
| `experiments/week7/vfc_precexp/logs/` | CSC command, Verificarlo version, stdout/stderr |

## Candidate Functions To Track

- MUSCL reconstruction / limiter functions.
- Hancock predictor.
- HLLC/Rusanov flux calls.
- EOS pressure / sound-speed computations.
- CFL computation.

## Pass Criterion

Use the existing `excmp` style only as a starting point. The report-facing rerun should compare against a trusted reference and report both global pass/fail and per-function precision assignments.
