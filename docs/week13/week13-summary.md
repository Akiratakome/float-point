# Week 13 Summary

Week 13 added 2D MHD benchmark coverage and a cfg-selectable HLLD solver path
without changing the default HLL Brio-Wu path.

## Delivered

- Added Orszag-Tang and Kelvin-Helmholtz 2D MHD initial conditions, cfgs, and
  validation drivers.
- Shared the Week 13 Python MHD validation harness across OT/KH and solver
  comparison runs.
- Added `HlldFlux` as an additive Riemann functor and `riemann = hll | hlld`
  runtime selection in `hrsc_mhd`; the default remains `hll`.
- Ran the HLLD-vs-HLL Orszag-Tang comparison at `256^2`, `t=0.5`.

## Decision

HLLD is deferred for production MHD precision-study runs. It completed the
Orszag-Tang comparison with finite density, but the measured `divB_max` was
`3.429e+01` for HLLD versus `3.720e+00` for HLL on the same grid/config.

HLL remains the production solver for the next MHD precision-study step until
the HLLD div(B) behavior is understood.

## Evidence

- Plan: [week13-plan.md](week13-plan.md)
- Paper-grounded benchmark matrix:
  [paper_benchmark_matrix.md](paper_benchmark_matrix.md)
- Orszag-Tang paper-style figure packet:
  [paper_summary.md](../../experiments/week13/orszag_tang/paper_summary.md)
- Solver comparison summary:
  [summary.md](../../experiments/week13/solver_compare/summary.md)
- Solver comparison data:
  [summary.json](../../experiments/week13/solver_compare/summary.json)
