# overall.md C2 Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align `docs/requirement/overall.md` with current Week-4 project state per the C2 design (content alignment without re-sequencing the 20-week timeline).

**Architecture:** Six surgical edits to a single file. No code touched, no tests run. Verification is acceptance-criteria checklist + IDE markdown render-check + grep-based path validation.

**Tech Stack:** Markdown only. The `Edit` tool's `old_string` / `new_string` mechanism is the primary instrument; each task's `old_string` anchor is small enough to be unique without ambiguity.

**Spec:** [docs/superpowers/specs/2026-04-29-overall-md-c2-alignment-design.md](../specs/2026-04-29-overall-md-c2-alignment-design.md)

---

## File Structure

Files affected:
- **Modify**: `docs/requirement/overall.md` (single file; ~150–200 line net change)

No files created or deleted. The companion spec already exists at `docs/superpowers/specs/2026-04-29-overall-md-c2-alignment-design.md` and is unmodified by this plan.

**Anchor reference** (from `grep -n "^##\|^###\|^####" docs/requirement/overall.md` at plan-write time; line numbers shift as edits land — use header text, not line numbers, when locating regions):

| Region | Anchor header |
|---|---|
| 3.1 insert | between `### Numerical Method` and `### Directory & File Structure` |
| 3.2 replace | the fenced ``` code block under `### Directory & File Structure` |
| 3.3 replace | table under `### Report 1 (Euler Validation)` |
| 3.4 append | end of Week 1 / 2 / 3 / 4 bodies, just before the next `#### Week N (...)` header |
| 3.5 replace | content under `#### Week 5 (04/20 - 04/26): ...`, `#### Week 6 (...)`, `#### Week 7 (...)` |
| 3.6 replace | three Tier tables under `## Appendix: Secondary & Optional Items (...)` |

---

## Task 1: Insert Cross-cutting numerical-analysis methods subsection

**Files:**
- Modify: `docs/requirement/overall.md` — insert new `### Cross-cutting numerical-analysis methods` subsection between `### Numerical Method` (closes around the `GLM divergence cleaning` bullets) and `### Directory & File Structure`.

- [ ] **Step 1: Locate the boundary anchor**

Run: `grep -n "### Directory & File Structure" docs/requirement/overall.md`
Expected: a single match (one line number).

- [ ] **Step 2: Apply the insertion**

Use the Edit tool with this exact `old_string` / `new_string` pair. The `old_string` is the blank line + the next section header — short, unique, sufficient anchor:

`old_string`:
```

### Directory & File Structure
```

`new_string`:
```

### Cross-cutting numerical-analysis methods

Beyond the deterministic FVM solver, the project relies on a set of stochastic / instrumented FP-analysis tools as **core methodology** (not optional extensions):

- **Verificarlo MCA (Monte-Carlo Arithmetic)** — perturbs every FP op at chosen virtual precision *p*. Used to (i) establish noise floors per test (`p=53` baseline), (ii) act as a virtual-precision surrogate for `float` (`p=24`) when comparing against real `float`, (iii) drive 2D large-grid statistical batches (200²×30 SLURM array on CSC).
- **Verificarlo `vfc_precexp` (mixed-precision exploration)** — per-call minimum-precision search; informs which routines tolerate `float` vs require `double`. Feeds Report 2 mixed-precision argument.
- **Verificarlo unstable-branch detection** — flags conditional branches whose taken-side is FP-rounding-sensitive (e.g. HLLC `S* == 0` selection, `<= vs <` choice).
- **FMA instrumentation** (`--inst-fma`) — quantifies the contribution of fused-multiply-add single-rounding to result drift.
- **SNR / LoSoS / s_req(N) / Pareto metrics** — quantitative answer to «how many significant digits does the simulation actually deliver, and at what cost?». `s_req(N)` anchors precision to truncation-error level; Pareto plots trade σ_FP against worst-cell error.

Implication: Verificarlo is treated as a *Tier-1 cross-cutting method* (originally Tier 3 in the Week-1 plan), used continuously from Week 3 onward, not deferred to Week 17.

### Directory & File Structure
```

- [ ] **Step 3: Verify insertion**

Run: `grep -n "Cross-cutting numerical-analysis methods" docs/requirement/overall.md`
Expected: exactly one match.

Run: `grep -c "### Directory & File Structure" docs/requirement/overall.md`
Expected: `1` (still unique).

- [ ] **Step 4: Commit**

```bash
git add docs/requirement/overall.md
git commit -m "docs(requirement): add Cross-cutting numerical-analysis methods subsection (C2 §3.1)"
```

---

## Task 2: Replace Directory & File Structure tree

**Files:**
- Modify: `docs/requirement/overall.md` — replace the fenced code block under `### Directory & File Structure`.

- [ ] **Step 1: Apply the replacement**

`old_string` is the entire current tree, anchored by the opening `CMakeLists.txt` comment and the closing `submit_gpu.sh, submit_cpu.sh` line:

`old_string`:
````
```
CMakeLists.txt                          # Root build config
cmake/
  CompilerFlags.cmake                   # -O2/-O3/-Ofast, -ffast-math, --use_fast_math
  CUDASetup.cmake                      # CUDA arch detection
  PrecisionConfig.cmake                # float/double/quad selection

src/
  main.cpp                             # Entry: parse config, select solver, run, output

  common/
    types.hpp                          # HD_FUNC macro, Constants<Real>
    vec.hpp                            # Vec<Real,N> fixed-size array with arithmetic ops
    grid.hpp                           # Grid2D<Real,NVars>: cells, ghost cells, data storage
    boundary.hpp                       # BCs: periodic, reflective, outflow
    eos.hpp                            # Ideal gas: pressure, sound speed, cons<->prim
    io.hpp                             # Binary output (header + raw data), numpy-compatible
    timer.hpp                          # Wall-clock timing utility
    error_norms.hpp                    # L1, L2, Linf norm computation + div(B) monitoring (mean/max |∇·B|)
    config.hpp                         # key=value config file parser

  euler/
    euler_state.hpp                    # Conserved variable indexing (rho, rho*u, rho*v, E)
    euler_flux.hpp                     # Physical flux F(U), G(U) for x,y directions
    hllc.hpp                           # HLLC Riemann solver (with configurable <= vs <)
    muscl.hpp                          # MUSCL reconstruction (minmod, van Leer, MC limiters)
    hancock.hpp                        # Hancock half-step predictor
    euler_solver.hpp/.cpp              # EulerSolver<Real>: full 2D update with dim. splitting

  mhd/
    mhd_state.hpp                      # 9-component state (rho, rho*v, B, E, psi)
    mhd_flux.hpp                       # MHD flux with magnetic pressure/tension
    hll.hpp                            # HLL solver (2-wave, simpler fallback)
    hlld.hpp                           # HLLD solver (5-wave, Miyoshi & Kusano 2005)
    glm.hpp                            # GLM div-cleaning: psi flux terms + multi-dim source step + psi BCs
    mhd_muscl.hpp                      # MUSCL reconstruction for 9 MHD variables
    mhd_hancock.hpp                    # Hancock predictor for MHD
    mhd_solver.hpp/.cpp                # MHDSolver<Real>: full 2D MHD update

  gpu/
    cuda_utils.cuh                     # CUDA_CHECK macro, DeviceArray wrapper
    gpu_grid.cuh                       # Device mirror of Grid2D, host<->device transfers
    euler_kernels.cuh                  # CUDA kernels: reconstruct, predict, HLLC, update
    euler_gpu_solver.cu                # EulerGPUSolver<Real>: kernel orchestration
    mhd_kernels.cuh                    # CUDA kernels for MHD
    mhd_gpu_solver.cu                  # MHDGPUSolver<Real>: MHD kernel orchestration

  tests/
    toro_1d/
      toro_tests.hpp                   # IC for Toro tests 1-5 (Sod, Lax, 123, blast)
      toro_exact.hpp                   # Exact Riemann solver for reference solutions
      sod.cfg, lax.cfg, test123.cfg, blast.cfg
    liska_wendroff_2d/
      lw_tests.hpp                     # IC for 2D Riemann problems (configs 3,4,6,12)
      config3.cfg, config4.cfg, config6.cfg, config12.cfg
    shock_bubble/
      shock_bubble.hpp, shock_bubble.cfg
    orszag_tang/
      orszag_tang.hpp, orszag_tang.cfg
    kelvin_helmholtz/
      kh.hpp, kh.cfg

analysis/
  compare.py                           # Load binary, compute norms (iterative, deletes grid files)
  plot_1d.py                           # 1D profiles vs exact solution
  plot_2d.py                           # 2D pseudocolor & schlieren plots
  convergence.py                       # Grid convergence (log-log error vs N)
  precision_comparison.py              # float vs double norm tables (LaTeX-ready)
  roundoff_vs_truncation.py            # Separate round-off from truncation error (core analysis)
  cfl_sensitivity.py                   # CFL number effect on error accumulation
  temporal_divergence.py               # log(error) vs time + Lyapunov exponent fitting
  divb_evolution.py                    # MHD: mean/max |∇·B| vs time for float vs double
  run_matrix.py                        # Run full parameter matrix (iterative batch processing)
  ml_error_predictor.py                # [If time permits] ML error norm prediction
  requirements.txt                     # numpy, matplotlib, pandas, scipy

scripts/
  build_all.sh                         # Build all precision x opt x cuda variants
  run_experiments.sh                   # Run full test matrix
  submit_gpu.sh, submit_cpu.sh         # Cluster job submission (SLURM/PBS)
```
````

`new_string`:
````
```
CMakeLists.txt                          # Root build config
cmake/
  CompilerFlags.cmake                   # -O2/-O3/-Ofast, -ffast-math, --use_fast_math
  CUDASetup.cmake                       # CUDA arch detection (planned Week 5–6)
  PrecisionConfig.cmake                 # FLOAT_PRECISION = float | double | quad

src/
  main.cpp                              # cfg-driven entry; selects test, solver, BCs, precision

  core/
    types.hpp                           # HD_FUNC macro, Constants<Real>, TimeReal=double
    vec.hpp                             # Vec<Real,N> with arithmetic operators
    grid.hpp                            # Grid2D<Real,NVars>: cells, ghost cells, data storage
    boundary.hpp                        # BCs: outflow / periodic / reflective, per-axis dispatch
    eos.hpp                             # Ideal gas: pressure, sound speed, cons<->prim

  utils/
    io.hpp                              # Binary writer (auto-creates parent dir) + reader
    config.hpp                          # key=value config file parser
    error_norms.hpp                     # L1 / L2 / Linf helpers used by tests + scripts
    timer.hpp                           # Wall-clock timing utility (planned Week 5)

  euler/
    euler_state.hpp                     # Conserved variable indexing
    euler_flux.hpp                      # F(U), G(U) for x,y directions
    hllc.hpp                            # HLLC Riemann solver (configurable <= vs <)
    rusanov.hpp                         # Rusanov solver (default since Week 4)
    muscl.hpp                           # MUSCL reconstruction (minmod, van Leer, MC)
    hancock.hpp                         # Hancock half-step predictor
    exact_riemann.hpp                   # Exact 1D Euler Riemann solver (reference)
    euler_solver.{hpp,cpp}              # EulerSolver<Real> (split for explicit instantiation)

  mhd/                                  # (planned Week 12+)
    mhd_state.hpp / mhd_flux.hpp / hll.hpp / hlld.hpp / glm.hpp
    mhd_muscl.hpp / mhd_hancock.hpp / mhd_solver.{hpp,cpp}

  gpu/                                  # (stub directory; bring-up Week 5–6)
    cuda_utils.cuh / gpu_grid.cuh / euler_kernels.cuh / euler_gpu_solver.cu
    mhd_kernels.cuh / mhd_gpu_solver.cu

tests/                                  # (top-level, NOT under src/)
  unit/                                 # Catch2: 115 cases / 3660 assertions
    test_boundary.cpp                   # 10 cases / 572 assertions, outflow/periodic/reflective × 1D/2D
    ... (other unit tests)
  cases/
    toro_1d/                            # sod, toro2, toro3, toro4, toro5, stationary_contact (+ rusanov twins)
                                        # convergence_*.cfg drive resolutions = 50,100,200,400,800
    liska_wendroff_2d/                  # config3_n200.cfg, config3_n400.cfg, config3_ref800.cfg
                                        # config4 / config6 / shock_bubble (planned Week 5)
  py/                                   # pytest: ssim_scalar, snr_*, losos_*, s_req_*, divergence_marker

scripts/                                # Replaces the original `analysis/` directory
  build_all.sh                          # Multi-variant build matrix driver (planned Week 7)
  regression/                           # float_regression_{1d,2d}.sh, float_regression_report.py
  metrics/                              # ssim_scalar.py, snr_metric.py, losos_metric.py, s_req_metric.py,
                                        #   phase_error_metrics.py, downsample_2d.py
  verificarlo/                          # verificarlo_run.sh, noise_floor_run.sh, compute_noise_floor.py
  figures/                              # plot_real_vs_vprec.py, pareto_plot.py, plot_divergence_marker.py,
                                        #   tradeoff_summary_table.py
  cluster/                              # SLURM submission helpers for CSC

experiments/                            # Output artefacts (gitignored beyond the index pointers)
  week4/{float_regression,figures,2d_vfc_cluster}/
  verificarlo/{runs_p53_mca*, runs_compare_p24_mca_real_vs_double*}/
```
````

- [ ] **Step 2: Verify the new tree against actual filesystem**

Run: `ls src/core src/utils src/euler tests/cases/toro_1d`
Expected output (excerpts):
- `src/core/`: `boundary.hpp eos.hpp grid.hpp types.hpp vec.hpp`
- `src/utils/`: `config.hpp error_norms.hpp io.hpp` (no `timer.hpp` yet — that's why it's marked `(planned Week 5)`)
- `src/euler/`: contains `hllc.hpp rusanov.hpp muscl.hpp hancock.hpp exact_riemann.hpp euler_solver.hpp euler_solver.cpp euler_state.hpp euler_flux.hpp`
- `tests/cases/toro_1d/`: contains `sod.cfg toro2.cfg toro3.cfg toro4.cfg toro5.cfg stationary_contact.cfg` and `_rusanov.cfg` twins.

If any tree entry references a path that does not exist on disk **and** is not annotated `(planned Week N)`, fix the spec mismatch by adding the annotation — do not invent files.

- [ ] **Step 3: Commit**

```bash
git add docs/requirement/overall.md
git commit -m "docs(requirement): replace dir tree with current src/utils + scripts/ layout (C2 §3.2)"
```

---

## Task 3: Update Test Matrix Report 1 — Toro test names + Rusanov default note

**Files:**
- Modify: `docs/requirement/overall.md` — replace table under `### Report 1 (Euler Validation)` and append a Rusanov-default note immediately after the table.

- [ ] **Step 1: Apply the table replacement + note insertion in one Edit**

`old_string`:
```
### Report 1 (Euler Validation)

| Test Case | Grid | t_end | Type |
|---|---|---|---|
| Sod (Toro 1) | 200x1 | 0.25 | 1D shock tube |
| Lax (Toro 2) | 200x1 | 0.15 | 1D stronger shock |
| 123 Problem (Toro 3) | 200x1 | 0.15 | 1D two rarefactions |
| Blast Wave (Toro 4) | 200x1 | 0.035 | 1D strong blasts |
| Stationary Contact | 200x1 | 0.5 | 1D: p_L=p_R, u=0, rho differs → S_M=0 exactly. **Targeted test for `<=` vs `<` and ±0.0 FP edge cases** |
| Liska-Wendroff Config 3 | 400x400 | 0.3 | 2D four-shock |
| Liska-Wendroff Config 6 | 400x400 | 0.3 | 2D different pattern |
| Shock-Bubble | 400x200 | varies | 2D complex interaction |

Each run in: {float, double} x {O2, Ofast} x {CPU, GPU} = 8 configs minimum.
```

`new_string`:
```
### Report 1 (Euler Validation)

| Test Case | cfg | Grid | t_end | Type |
|---|---|---|---|---|
| sod (Toro 1) | `tests/cases/toro_1d/sod.cfg` | 200×1 | 0.25 | 1D shock tube |
| toro2 (Lax) | `toro2.cfg` | 200×1 | 0.15 | 1D stronger shock |
| toro3 (123 problem) | `toro3.cfg` | 200×1 | 0.15 | 1D two rarefactions |
| toro4 (blast) | `toro4.cfg` | 200×1 | 0.035 | 1D strong shocks |
| toro5 | `toro5.cfg` | 200×1 | 0.012 | 1D shock-contact-shock |
| stationary_contact | `stationary_contact.cfg` | 200×1 | 0.5 | 1D: p_L=p_R, u=0, ρ_L≠ρ_R → S_M=0 (targeted `<=` vs `<` test) |
| Liska-Wendroff Config 3 | `liska_wendroff_2d/config3_n200.cfg` | 200×200 / 400×400 | 0.3 | 2D four-shock |
| Liska-Wendroff Config 6 | (planned Week 5) | 400×400 | 0.3 | 2D different pattern |
| Shock-Bubble | (planned Week 5) | 400×200 | varies | 2D complex interaction |

> **Solver default**: `solver = rusanov` is the default since Week 4 (supervisor Phase A1). HLLC is enabled per-cfg via `solver = hllc`; `*_rusanov.cfg` and HLLC twins exist for several Toro cases for direct A/B comparison.

Each run in: {float, double} x {O2, Ofast} x {CPU, GPU} = 8 configs minimum.
```

- [ ] **Step 2: Verify cfg paths exist**

Run: `ls tests/cases/toro_1d/sod.cfg tests/cases/toro_1d/toro2.cfg tests/cases/toro_1d/toro3.cfg tests/cases/toro_1d/toro4.cfg tests/cases/toro_1d/toro5.cfg tests/cases/toro_1d/stationary_contact.cfg`
Expected: all six files listed (no «No such file»).

Run: `ls tests/cases/liska_wendroff_2d/config3_n200.cfg`
Expected: file present.

- [ ] **Step 3: Commit**

```bash
git add docs/requirement/overall.md
git commit -m "docs(requirement): align Report-1 Euler test matrix with shipped cfgs + Rusanov default (C2 §3.3)"
```

---

## Task 4: Append «Actually delivered» callouts to Weeks 1–4

**Files:**
- Modify: `docs/requirement/overall.md` — at the end of each Week 1, 2, 3, 4 body, just before the horizontal rule `---` that separates weeks, append a single block-quote line.

This task has four sub-edits (one per week). All four are landed in a single commit because they are conceptually one change.

- [ ] **Step 1: Append Week 1 callout**

`old_string`:
```
**Writing:** Begin reading literature (Toro 2009, Goldberg floating-point paper, Bard & Dorelli 2014)

---

#### Week 2 (03/30 - 04/05): 1D Euler Solver Core
```

`new_string`:
```
**Writing:** Begin reading literature (Toro 2009, Goldberg floating-point paper, Bard & Dorelli 2014)

> **Actually delivered (as of 2026-04-29)**: Core infrastructure landed; `src/common/` split into `src/core/` + `src/utils/` for clearer FP-vs-utility boundaries — see [week1-summary.md](../week1/week1-summary.md).

---

#### Week 2 (03/30 - 04/05): 1D Euler Solver Core
```

- [ ] **Step 2: Append Week 2 callout**

`old_string`:
```
**Milestone:** Sod shock tube (含激波，超音速) produces correct density/pressure/velocity profiles

---

#### Week 3 (04/06 - 04/12): Complete 1D Tests + Exact Solver + Analysis Tools
```

`new_string`:
```
**Milestone:** Sod shock tube (含激波，超音速) produces correct density/pressure/velocity profiles

> **Actually delivered (as of 2026-04-29)**: Sod 1D end-to-end correct; HLLC + Rusanov both available (Rusanov added as fallback solver) — see [week2-summary.md](../week2/week2-summary.md).

---

#### Week 3 (04/06 - 04/12): Complete 1D Tests + Exact Solver + Analysis Tools
```

- [ ] **Step 3: Append Week 3 callout**

`old_string`:
```
**Milestone:** All 4 Toro tests pass validation. >=3 tests contain supersonic waves (shocks).

---

#### Week 4 (04/13 - 04/19): Float/Double Templating + 2D Extension
```

`new_string`:
```
**Milestone:** All 4 Toro tests pass validation. >=3 tests contain supersonic waves (shocks).

> **Actually delivered (as of 2026-04-29)**: All Toro 1D tests pass against exact Riemann solution. Verificarlo MCA brought online (`p=53` noise floor). Supervisor Week-3 feedback added a parallel work-line — SLIC branch + `vfc_precexp` / unstable-branch detection / FMA instrumentation — folded into Cross-cutting numerical-analysis methods (§Architecture). See [week3-summary.md](../week3/week3-summary.md).

---

#### Week 4 (04/13 - 04/19): Float/Double Templating + 2D Extension
```

- [ ] **Step 4: Append Week 4 callout**

`old_string`:
```
**Milestone:** 1D tests run in both float and double. 2D solver framework compiles.

---

#### Week 5 (04/20 - 04/26): 2D Euler Tests + GPU Development Start
```

`new_string`:
```
**Milestone:** 1D tests run in both float and double. 2D solver framework compiles.

> **Actually delivered (as of 2026-04-29)**: Three phases delivered — Phase A (A1 Rusanov default, A2 divergence-marker tool, A3 2D Verificarlo cluster runs at 200²×30, A4 SNR / LoSoS / s_req(N) / Pareto metrics), Phase B (PrecisionConfig, EulerSolver split for explicit instantiation, per-axis BC dispatch with periodic+reflective, Catch2 115 cases / 3660 assertions), Phase C (C1 1D + 2D float regression, C2 real-float vs VPREC p24 comparison). See [week4-summary.md](../week4/week4-summary.md).

---

#### Week 5 (04/20 - 04/26): 2D Euler Tests + GPU Development Start
```

- [ ] **Step 5: Verify all four callouts landed and links resolve**

Run: `grep -c "Actually delivered (as of 2026-04-29)" docs/requirement/overall.md`
Expected: `4`.

Run: `ls docs/week1/week1-summary.md docs/week2/week2-summary.md docs/week3/week3-summary.md docs/week4/week4-summary.md`
Expected: all four files present (the relative paths from `docs/requirement/` are `../weekN/weekN-summary.md`).

- [ ] **Step 6: Commit**

```bash
git add docs/requirement/overall.md
git commit -m "docs(requirement): add Weeks 1-4 'Actually delivered' callouts (C2 §3.4)"
```

---

## Task 5: Adjust Weeks 5–7 forward content

**Files:**
- Modify: `docs/requirement/overall.md` — three sub-edits in Weeks 5, 6, 7 bodies.

- [ ] **Step 1: Replace Week 5 «Code (2D tests)» + «Code (GPU)» blocks**

`old_string`:
```
**Code (2D tests — only 2 configs needed initially, can add more later):**
- `tests/liska_wendroff_2d/lw_tests.hpp` — IC for configs 3 and 6 (supersonic shocks ✓, satisfies 1D+2D requirement with Toro tests)
- `tests/shock_bubble/shock_bubble.hpp` — shock-bubble IC (supersonic shock ✓)
- Config files for 2D tests
- `common/timer.hpp` — wall-clock timing (records every run for performance analysis)

**Code (GPU — start early to reduce Week 6 risk):**
- Add `#pragma omp parallel for` to sweep loops in euler_solver
- `gpu/cuda_utils.cuh` — CUDA error checking, DeviceArray wrapper
- `gpu/gpu_grid.cuh` — device mirror of Grid2D, host<->device transfers
- Begin `gpu/euler_kernels.cuh` — first kernels (conservative update, boundary conditions)

**Analysis:**
- `analysis/plot_2d.py` — 2D density pseudocolor, schlieren plots

**Milestone:** 2D CPU results match published figures. GPU infrastructure compiles on local machine.
```

`new_string`:
```
**Code (2D tests + closing Phase 1 infra gaps):**
- Replace the Config-6 stub in `tests/cases/liska_wendroff_2d/lw_tests.hpp` (`setup_liska_wendroff_config6` currently throws) with a real IC + add `config6_n200.cfg` / `config6_n400.cfg`.
- `tests/cases/shock_bubble/` — new IC header + cfg for shock-bubble interaction (supersonic shock ✓, satisfies 1D+2D requirement with Toro tests).
- `src/utils/timer.hpp` — wall-clock timer (records every run for performance analysis).

**Code (GPU bring-up — skeleton only):**
- OpenMP `#pragma omp parallel for` already wired into sweep loops + CFL reduction (delivered Week 4 — no action needed here).
- `src/gpu/cuda_utils.cuh` — CUDA error-check macro, DeviceArray wrapper.
- `src/gpu/gpu_grid.cuh` — device mirror of Grid2D, host↔device transfers.
- `src/gpu/euler_kernels.cuh` — first kernels (conservative update, BC). Compilable empty implementations are acceptable; full kernels are Week 6.

**Risk note:** Full GPU Euler solver is deferred to Weeks 6–7. If Week 5 progress is tight, shock-bubble may slip to Week 6 — Config 6 + GPU skeleton are the non-deferrable items because they unblock 2D test coverage and the Week-6 kernel work.

**Analysis:**
- `scripts/figures/plot_2d.py` (or equivalent in `scripts/figures/`) — 2D density pseudocolor, schlieren plots. Note: phase-error heatmaps + SSIM already provided by `scripts/metrics/phase_error_metrics.py` from Week 4.

**Milestone:** 2D CPU results match published figures. GPU infrastructure compiles on local machine.
```

- [ ] **Step 2: Append Week 6 carry-over paragraph**

`old_string`:
```
**Milestone:** GPU Euler solver matches CPU to machine epsilon. Runs on CSC cluster GPU nodes.

---

#### Week 7 (05/04 - 05/10): Experiments + Data Collection for Report 1
```

`new_string`:
```
**Milestone:** GPU Euler solver matches CPU to machine epsilon. Runs on CSC cluster GPU nodes.

> **Carry-over from Week 5**: complete remaining 2D Euler tests if not finished. Extend the Phase-C float-regression pipeline to GPU outputs once kernels land — same `summary.{md,json}` schema, same SSIM / L1 / phase metrics; CPU-vs-GPU same-precision diff must be ≤ ULP-level.

---

#### Week 7 (05/04 - 05/10): Experiments + Data Collection for Report 1
```

- [ ] **Step 3: Append Week 7 reuse paragraph**

`old_string`:
```
**Experiments (on CSC cluster):**
- All 7 Euler test cases x {float, double} x {CPU, GPU} x {O2, Ofast} = 56 runs
- L1/L2/Linf error norms for each configuration
- Grid convergence: N = 50, 100, 200, 400, 800
- Generate all plots: 1D profiles, 2D pseudocolor, difference maps, convergence curves

**Milestone:** All experimental data for Report 1 collected and analyzed.
```

`new_string`:
```
**Experiments (on CSC cluster):**
- All 7 Euler test cases x {float, double} x {CPU, GPU} x {O2, Ofast} = 56 runs
- L1/L2/Linf error norms for each configuration
- Grid convergence: N = 50, 100, 200, 400, 800
- Generate all plots: 1D profiles, 2D pseudocolor, difference maps, convergence curves
- Reuse the Week-4-established Verificarlo + SNR / LoSoS / s_req(N) / Pareto pipeline for the full Euler matrix. Performance timing (via `src/utils/timer.hpp`) recorded per run; build matrix automated via `scripts/build_all.sh`. CPU-vs-GPU same-precision diff is enforced as a regression gate.

**Milestone:** All experimental data for Report 1 collected and analyzed.
```

- [ ] **Step 4: Verify all three Week 5–7 changes landed**

Run: `grep -n "Code (GPU bring-up — skeleton only)" docs/requirement/overall.md`
Expected: one match (Week 5).

Run: `grep -n "Carry-over from Week 5" docs/requirement/overall.md`
Expected: one match (Week 6).

Run: `grep -n "Reuse the Week-4-established Verificarlo" docs/requirement/overall.md`
Expected: one match (Week 7).

- [ ] **Step 5: Commit**

```bash
git add docs/requirement/overall.md
git commit -m "docs(requirement): adjust Weeks 5-7 to reflect current Phase 1 status (C2 §3.5)"
```

---

## Task 6: Re-tier Appendix Tier 1/2/3

**Files:**
- Modify: `docs/requirement/overall.md` — replace the three Tier tables (and their preceding `### Tier ...` headers) inside `## Appendix: Secondary & Optional Items (Week 17 if time permits)`.

- [ ] **Step 1: Apply the Appendix replacement**

`old_string`:
```
### Tier 1 — Secondary experiments (highest value, lowest effort)

| Item | Effort | Insight | Notes |
|---|---|---|---|
| **FMA control** (`-ffp-contract`, `--fmad`) | Low (CMake flag) | Explains specific compiler effect on FP associativity | Add to CompilerFlags.cmake |
| **CFL sensitivity** (0.2, 0.4, 0.6, 0.8) | Low (re-run existing tests) | Separates time integration error from flux error | `cfl_sensitivity.py` |
| **Limiter sensitivity** (minmod, van Leer, MC) | Low (already in code) | Does reconstruction amplify round-off? | Compare float-double norms across limiters |

### Tier 2 — Additional experiments (medium value)

| Item | Effort | Insight | Notes |
|---|---|---|---|
| **OpenMP thread count** (1, 2, 4, 8) | Low | Non-deterministic reduction ordering | Addresses "thread/process scheduling" in brief |
| **-mtune / vectorisation** | Low (CMake flag) | CPU microarchitecture effects | |
| **Quad precision** (1D CPU only) | Medium (Boost) | Ground truth reference | |
| **MPI non-determinism demo** | Medium | Standalone MPI_Reduce script showing LSB variance across process counts. Provides empirical evidence for "reproducibility" section and justifies MPI omission from main code | |

### Tier 3 — Advanced tools and ML (lowest priority)

| Item | Effort | Insight | Notes |
|---|---|---|---|
| **Verificarlo** (stochastic arithmetic) | High (special compiler) | Complements round-off analysis | `/lsc/opt/verificarlo-2.4.0`, clang++-18 |
| **RAPTOR** (mixed precision) | High (special compiler) | Which variables tolerate lower precision | `/lsc/opt/raptor`, clang++-20 |
| **ML error predictor** | Medium | Predictive model from sweep data | `ml_error_predictor.py`, scikit-learn |
```

`new_string`:
```
### Tier 1 — Core methods (already adopted in Weeks 3–4)

| Item | Status | Notes |
|---|---|---|
| Verificarlo MCA (`p=53` noise floor, `p=24` float-surrogate, 2D batch) | adopted | See `scripts/verificarlo/`, `experiments/verificarlo/runs_p53_mca*` |
| SNR / LoSoS / s_req(N) / Pareto metrics | adopted | See `scripts/metrics/` + `scripts/figures/pareto_plot.py` |
| FMA control (`-ffp-contract`, `--fmad`, `--inst-fma`) | adopted | C2 `_fma` variant runs already exist |
| `vfc_precexp` (mixed-precision exploration) | planned (carry-over from Week-3 supervisor ask) | Schedule: Week 14 once MHD lands, or earlier if MHD slips |
| Verificarlo unstable-branch detection | planned (carry-over from Week-3 supervisor ask) | Schedule: alongside `vfc_precexp` |

### Tier 2 — Incremental experiments (do if time permits)

| Item | Notes |
|---|---|
| CFL sensitivity (0.2, 0.4, 0.6, 0.8) | Time integration vs flux error separation |
| Limiter sensitivity (minmod, van Leer, MC) | Reconstruction round-off amplification |
| OpenMP thread count (1, 2, 4, 8) | Reduction-ordering non-determinism |
| `-mtune` / vectorisation options | CPU microarchitecture effects |
| Quad precision (1D CPU only) | Ground-truth reference; do not attempt 2D / GPU |
| MPI non-determinism demo | Standalone `MPI_Reduce` script for Report 2 reproducibility section |

### Tier 3 — Advanced / exploratory (lowest priority)

| Item | Notes |
|---|---|
| RAPTOR (mixed precision, special compiler) | `/lsc/opt/raptor`, clang++-20 |
| ML error predictor | scikit-learn; only if Tier-1+2 complete |
```

- [ ] **Step 2: Verify Verificarlo migrated to Tier 1**

Run: `grep -n "Verificarlo MCA" docs/requirement/overall.md`
Expected: matches in (a) the new Cross-cutting subsection (Task 1) and (b) the new Tier-1 table — at least 2 matches total.

Run: `grep -n "### Tier 3 — Advanced / exploratory" docs/requirement/overall.md`
Expected: one match.

Run: `grep -n "Tier 3 — Advanced tools and ML" docs/requirement/overall.md`
Expected: zero matches (old heading must be gone).

- [ ] **Step 3: Commit**

```bash
git add docs/requirement/overall.md
git commit -m "docs(requirement): re-tier Appendix — promote Verificarlo + SNR/LoSoS/Pareto + FMA to Tier 1 (C2 §3.6)"
```

---

## Task 7: Final verification — acceptance criteria + render check

**Files:** none modified. This task is a checklist, not an edit.

- [ ] **Step 1: Full grep-based acceptance check**

Run each of the following commands and confirm the expected result:

```bash
# 1. New Cross-cutting subsection exists exactly once.
grep -c "^### Cross-cutting numerical-analysis methods$" docs/requirement/overall.md
# Expected: 1

# 2. Old common/ tree paths are gone.
grep -c "src/common/" docs/requirement/overall.md
# Expected: 1  (only the Week-1 callout retains "src/common/" as historical reference)

# 3. Each Week 1-4 has exactly one "Actually delivered" callout.
grep -c "Actually delivered (as of 2026-04-29)" docs/requirement/overall.md
# Expected: 4

# 4. Week 5 risk note present.
grep -c "Risk note" docs/requirement/overall.md
# Expected: 1

# 5. Tier headers updated.
grep "^### Tier" docs/requirement/overall.md
# Expected three lines exactly:
#   ### Tier 1 — Core methods (already adopted in Weeks 3–4)
#   ### Tier 2 — Incremental experiments (do if time permits)
#   ### Tier 3 — Advanced / exploratory (lowest priority)

# 6. Untouched anchors still present.
grep -c "^## Verification Strategy$" docs/requirement/overall.md
# Expected: 1
grep -c "^## Mapping to Report Requirements$" docs/requirement/overall.md
# Expected: 1
grep -c "^## Supersonic Wave Test Cases" docs/requirement/overall.md
# Expected: 1

# 7. All weekly summary links resolve.
for w in 1 2 3 4; do test -f docs/week${w}/week${w}-summary.md && echo "week${w} ok" || echo "week${w} MISSING"; done
# Expected: four "ok" lines.
```

- [ ] **Step 2: Verify cfg paths in the new Test Matrix exist**

```bash
for f in sod toro2 toro3 toro4 toro5 stationary_contact; do
  test -f tests/cases/toro_1d/${f}.cfg && echo "${f}.cfg ok" || echo "${f}.cfg MISSING"
done
test -f tests/cases/liska_wendroff_2d/config3_n200.cfg && echo "config3_n200.cfg ok" || echo "config3_n200.cfg MISSING"
```

Expected: seven "ok" lines.

- [ ] **Step 3: IDE markdown render-check**

Open `docs/requirement/overall.md` in VSCode preview (Ctrl+Shift+V). Visually scan:
- Architecture Overview now shows three subsections in order: Precision-Generic Design, Numerical Method, **Cross-cutting numerical-analysis methods**, then Directory & File Structure heading begins.
- Directory tree renders as a single fenced code block, no broken backticks.
- Test Matrix Report 1 table has 5 columns (Test Case, cfg, Grid, t_end, Type).
- Each Week 1–4 ends in a block-quote callout (rendered as indented italic-ish block).
- Tier tables render as three separate tables under three headers.

If any link is broken (red underline in IDE) or table mis-renders, fix inline before continuing.

- [ ] **Step 4: Confirm git diff scope**

```bash
git diff main..HEAD --stat
```
Expected: shows changes only to `docs/requirement/overall.md` and `docs/superpowers/specs/2026-04-29-overall-md-c2-alignment-design.md` (+ this plan if committed). No code, no tests, no other docs.

- [ ] **Step 5: No final commit needed for this task** — verification is read-only.

---

## Self-Review

**Spec coverage:**
- Spec §3.1 → Task 1 ✓
- Spec §3.2 → Task 2 ✓
- Spec §3.3 → Task 3 ✓
- Spec §3.4 → Task 4 ✓
- Spec §3.5 → Task 5 ✓
- Spec §3.6 → Task 6 ✓
- Spec §5 acceptance criteria → Task 7 ✓
- Spec §4 commit policy: this plan uses 6 commits (one per task) instead of the spec's "Commit 2" single-commit suggestion. This is finer-grained but compatible — each commit is independently revertable. Acceptable deviation.

**Placeholder scan:** No "TBD", no "implement later", no "similar to Task N". All Edit `old_string` / `new_string` pairs are concrete. Verification commands have expected outputs.

**Type / name consistency:** "Cross-cutting numerical-analysis methods" header text identical in Tasks 1, 7, and spec §3.1. "Actually delivered (as of 2026-04-29)" string identical in Tasks 4 and 7. Tier-1 status string ("adopted") consistent across rows.

---
