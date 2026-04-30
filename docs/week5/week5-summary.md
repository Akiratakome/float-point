# Week 5 Summary

**Branch**: `week4-implementation`
**Period**: Week 5 (2026-04-30 closure)
**Spec**: [`week5-plan.md`](week5-plan.md)
**Recipe**: [`week5-verification.md`](week5-verification.md)

---

## Delivered

- **Block A** - `Timer` is always available, and `ProfilingRegistry` /
  `ScopedTimer` remain gated behind `HRSC_ENABLE_PROFILING`. `main.cpp` emits
  `[timing] total_s=...` on stderr per solver run, and `scripts/run_matrix.py`
  records it as `metadata.json.timing.total_s`. ScopedTimer currently records 3
  phases (`bc`, `cfl`, `sweep`), not the 5-way spec split.
- **Block B** - Liska-Wendroff Config 6 initial condition, `config6_n200.cfg`,
  `config6_n400.cfg`, and unit coverage for quadrant values and uniform
  pressure. `overall.md` now records Config 6 as a contact-only case.
- **Block C** - Half-symmetric shock-bubble initial condition, Rankine-Hugoniot
  helper, HLLC and Rusanov cfgs, and unit coverage for the post-shock state and
  bubble geometry.
- **Block D.1** - Opt-in CUDA bring-up via `ENABLE_CUDA`, `cmake/CUDASetup.cmake`,
  and standalone `gpu_smoke`. The MSVC CUDA workaround is scoped under
  `ENABLE_CUDA`.
- **Block D.2** - GPU data-path skeleton: `HRSC_CUDA_CHECK`, `DeviceArray<T>`,
  `GpuGrid<Real,NVars>`, templated copy kernel, and Catch2 `[gpu]` roundtrip
  tests. Actual roundtrip result is 2 cases / 400 assertions.
- **Block E** - `scripts/figures/plot_2d.py` single-grid plotter with `rho`,
  `p`, `vmag`, and `schlieren`; the schlieren path computes gradients with
  physical `dx` / `dy`, not index spacing.
- **Harness smoke** - `experiments/week5/smoke/matrix.json` exercises the
  6-run matrix through config -> build -> run -> measure -> aggregate -> plot.
  The matrix file was committed in `f28be89`; smoke `grid.bin` files were
  deleted after aggregation and figure generation per `HARNESS.md` output
  discipline.

MSVC note: `HRSC_MSVC_OPENMP_LLVM` is opt-in. Default MSVC CPU builds fall back
to serial execution when classic OpenMP is unsupported, and CUDA/MSVC flag
workarounds stay under `ENABLE_CUDA`.

---

## Commits

```text
245341e docs(index): add Week 5 row + verification.md link
94c52f9 docs(week5): add week5-summary.md (deliverables + handoff)
e9ef67c docs(week5): add reproduction recipe (week5-verification.md)
f28be89 feat(harness): add Week 5 smoke matrix
a41e4fb fix(cmake): avoid unsupported classic MSVC OpenMP by default
96940cf fix(cmake): keep MSVC CUDA workarounds inside ENABLE_CUDA
0967745 feat(gpu): add GPU data path skeleton + Catch2 [gpu] roundtrip test
0f393eb test(py): smoke test for plot_2d.py (4 fields, PNG dims)
6397176 fix(figures): compute schlieren gradient in physical coordinates
adcdb83 feat(figures): add scripts/figures/plot_2d.py single-grid plotter
9846c45 feat(cases): add shock-bubble HLLC + Rusanov cfgs (400x100, half-symmetric)
409fbf3 feat(main): dispatch test=shock_bubble in setup_ic
3a276fe feat(cases): half-symmetric shock-bubble IC + unit tests
58b0849 docs(overall): correct LW Config 6 in supersonic test table
cc0f139 feat(cases): add LW Config 6 cfgs at 200x200 and 400x400
5e4395c test(lw): cover Config 6 IC quadrant values + uniform pressure
c152f17 feat(lw): implement Liska-Wendroff Config 6 IC (4 contact discontinuities)
4d7c645 feat(harness): parse [timing] total_s from solver stderr into metadata.json
```

---

## Artefact Map

| Path | Status | Contents |
|---|---|---|
| `docs/week5/week5-summary.md` | tracked | Week 5 deliverables and handoff summary |
| `docs/week5/week5-verification.md` | tracked | Manual Week 5 reproduction recipe |
| `experiments/week5/smoke/matrix.json` | tracked | 6-run harness smoke matrix recipe |
| `experiments/week5/baselines/lw_config6_n200/grid.bin` | ignored/generated kept | Config 6 200x200 local reference grid; do not commit as a routine doc/harness artefact |
| `experiments/week5/baselines/lw_config6_n400/grid.bin` | ignored/generated kept | Config 6 400x400 local reference grid; do not commit as a routine doc/harness artefact |
| `experiments/week5/baselines/shock_bubble_n400x100_hllc/grid.bin` | ignored/generated kept | Shock-bubble HLLC local reference grid; do not commit as a routine doc/harness artefact |
| `experiments/week5/baselines/shock_bubble_n400x100_rusanov/grid.bin` | ignored/generated kept | Shock-bubble Rusanov local reference grid; do not commit as a routine doc/harness artefact |
| `experiments/week5/baselines/figures/` | ignored/generated kept | 12 baseline PNGs (`rho`, `p`, `schlieren`) |
| `experiments/week5/smoke/matrix_summary.json` | ignored/generated kept | Matrix dry-run / run summary |
| `experiments/week5/smoke/summary.json` | ignored/generated kept | Aggregated smoke metadata summary |
| `experiments/week5/smoke/figures/` | ignored/generated kept | 6 smoke `rho` PNGs |
| `experiments/week5/smoke/runs/<name>/metadata.json` | ignored/generated kept | Per-run metadata, command, cfg, git commit, timing |
| `experiments/week5/smoke/runs/<name>/stdout.txt` | ignored/generated kept | Solver stdout logs |
| `experiments/week5/smoke/runs/<name>/stderr.txt` | ignored/generated kept | Solver stderr logs, including `[timing]` |
| `experiments/week5/smoke/runs/<name>/config.cfg` | ignored/generated kept | Generated per-run cfg |
| `experiments/week5/smoke/runs/<name>/grid.bin` | deleted transient | Smoke grids removed after `matrix_summary.json`, `summary.json`, and figures exist |

Tracked recipe/matrix files are the committed harness contract. Generated
summaries, logs, figures, and baseline grids may be kept locally for review, but
large grids should not be added to commits unless explicitly promoted to
reference data. Smoke `grid.bin` files are transient and should stay deleted
after aggregation and plotting.

---

## Week 5 -> Week 6 Handoff

Week 6 starts from a CPU-green, CUDA-gated base:

- `GpuGrid<Real,NVars>` mirrors `Grid2D` row-major, var-last layout with ghost
  cells included. Week 6 kernels should use the same indexing model as host
  grid code.
- `HRSC_CUDA_CHECK` and `DeviceArray<T>` are the allocation / error-checking
  primitives for CUDA code. New kernels should not introduce ad hoc
  `cudaMalloc` / `cudaFree` paths.
- `ENABLE_CUDA` remains default OFF. CPU builds, cfg defaults, and output
  formats stay unchanged.
- `HRSC_MSVC_OPENMP_LLVM` remains a deliberate MSVC opt-in; classic MSVC CPU
  builds may fall back serial by default.
- `Timer` and harness timing metadata are already available for CPU/GPU
  comparisons.
- The smoke matrix path is proven. Week 6 GPU smoke should add rows to a new
  matrix rather than bypassing `scripts/run_matrix.py`.
- `plot_2d.py` is ready for GPU outputs and CPU/GPU visual checks; use existing
  metric scripts for quantitative diffs.

Suggested Week 6 order:

1. Outflow boundary-condition kernel with CPU-vs-GPU grid comparison.
2. CFL kernel with deterministic reduction.
3. Reconstruction / predictor device helpers.
4. HLLC flux kernel.
5. `EulerGpuSolver<Real>` orchestration.
6. End-to-end CPU-vs-GPU regression on Sod and LW Config 3.

---

## Deferred

- ScopedTimer 5-way phase split: current implementation is 3 phases (`bc`,
  `cfl`, `sweep`).
- CSC GPU build: deferred until local CUDA kernels are stable.
- Verificarlo carry-over (`vfc_precexp` and unstable-branch detection): deferred
  from Week 5.
