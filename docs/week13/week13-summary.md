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

### Decision update (2026-07-06): div(B) behavior understood; HLLD cleared numerically

The follow-up audit
([hlld_divb_followup/summary.md](../../experiments/week13/hlld_divb_followup/summary.md))
found that the `divB_max=3.429e+01` above was measured on a **stale
`hrsc_mhd.exe`** (broken ninja/MSVC header-dependency tracking meant the
executable silently missed the `6491104` HLLD fan-consistency fix; see the
pitfall row in [docs/INDEX.md](../INDEX.md) §7). With a dependency-correct
rebuild: HLL reproduces bit-identically (divB_max 3.72), HLLD measures
**24.45**, and the remaining gap is bounded in time, convergent in the mean,
scales as a constant divB_max·dx jump fraction, and is localized at
under-resolved current sheets — reduced dissipation, not a GLM inconsistency.
The 5-wave fan was re-audited against Miyoshi & Kusano (2005) term-by-term,
and `RIEMANN_STRICT_INEQUALITY` now also covers HLLD's interior tie ownership
(SsL/SsR/SM). HLLD Brio-Wu anchor for future HLLD-as-default reruns:
`steps=761, divB_max=0.000e+00`. Production adoption for precision-study runs
remains a per-plan decision (see the follow-up summary's redo checklist).

## Evidence

- Plan: [week13-plan.md](week13-plan.md)
- Paper-grounded benchmark matrix:
  [paper_benchmark_matrix.md](paper_benchmark_matrix.md)
- Orszag-Tang paper-style figure packet:
  [paper_summary.md](../../experiments/week13/orszag_tang/paper_summary.md)
- Kelvin-Helmholtz paper-style figure packet:
  [paper_summary.md](../../experiments/week13/kelvin_helmholtz/paper_summary.md)
- Solver comparison summary:
  [summary.md](../../experiments/week13/solver_compare/summary.md)
- HLLD diagnostic figures:
  [figures/README.md](../../experiments/week13/solver_compare/figures/README.md)
- HLLD GLM local sweep:
  [summary.md](../../experiments/week13/hlld_glm_sweep/summary.md)
- HLLD div(B) follow-up (2026-07-06 decision update):
  [summary.md](../../experiments/week13/hlld_divb_followup/summary.md)
- MHD Verificarlo local smoke/probe:
  [summary.md](../../experiments/week13/mhd_verificarlo_smoke/summary.md)
- Solver comparison data:
  [summary.json](../../experiments/week13/solver_compare/summary.json)
- Week 14 brainstorming prompt:
  [week14-brainstorming-prompt.md](week14-brainstorming-prompt.md)
