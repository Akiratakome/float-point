# Week 14 Supervisor Validation Note

## What Was Validated

- Benchmark: Brio-Wu 1D ideal-MHD shock tube, following the classic Brio & Wu (1988) validation problem.
- Solver path: HLL, CPU only; HLLD remains deferred diagnostic work.
- Formal Week-14 gate: G0 pass = True.
- Reference row: `cpu-double-O2-ieee-leq` with steps = 759 and divB_max = 4.441e-14.
- Docker Verificarlo MCA: p53 completed with n = 8; p24 completed with n = 8.

## Literature Comparison

The result should be presented as a benchmark-aligned validation, not as a new
exact-solution claim. Brio-Wu is a standard MHD shock-tube problem used to check
shock-capturing behavior. Athena and PLUTO provide the relevant code-validation
context: robust Godunov-type MHD methods are expected to capture the wave
pattern while differing in dissipation depending on the Riemann solver. The HLL
choice here is therefore framed as a robust production baseline, with sharper
HLLD-style comparisons left to later work.

## Claim boundary

- Supported now: finite Brio-Wu HLL execution, reproduced Week-14 reference
  anchor, bounded divB diagnostic, deterministic precision deltas, and Docker
  Verificarlo MCA noise evidence.
- Not claimed now: exact Riemann-solution agreement, HLLD superiority/production
  readiness, 2D MHD conclusions, GPU MHD conclusions, or P1/P2 scaling claims.

## Sources

- [Brio & Wu (1988)](https://doi.org/10.1016/0021-9991(88)90120-9): classic one-dimensional ideal-MHD shock-tube benchmark.
- [Athena code paper (Stone et al., 2008)](https://arxiv.org/abs/0804.0402): modern MHD code test-suite context for comparison claims.
- [PLUTO code paper (Mignone et al., 2007)](https://arxiv.org/abs/astro-ph/0701854): Godunov shock-capturing benchmark context.
- [Takahashi & Yamada (2012)](https://arxiv.org/abs/1210.5584): Brio-Wu Riemann-problem non-uniqueness caution.
