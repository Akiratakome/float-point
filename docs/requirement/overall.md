# Implementation Plan: Effect of Floating-Point Precision and Hardware on HRSC Schemes

## Context

This is an academic project investigating how floating-point precision, hardware (CPU vs GPU), compiler options, and subtle implementation differences affect the accuracy and reproducibility of High-Resolution Shock-Capturing (HRSC) finite-volume solvers. The project requires two reports:

- **Report 1**: Euler equations - literature review, mathematical theory, code description, validation (4+ test cases, CPU+GPU, float+double)
- **Report 2**: Ideal-MHD equations - systematic accuracy exploration across hardware/precision/compiler options, conclusions about reproducibility

The code is standalone C++17/CUDA (not AMReX) for easier customization and profiling.

---

## Architecture Overview

### Precision-Generic Design
All computational kernels are **templated on `Real`** (float, double, optionally quad). The build system instantiates for one precision at a time. A macro `HD_FUNC` wraps `__host__ __device__` for CPU/GPU portability.

### Numerical Method
- **MUSCL-Hancock** (2nd-order explicit finite-volume)
- **HLLC** Riemann solver for Euler, **HLLD** for MHD
- **Dimensional splitting** (alternating Lie splitting for 2D)
- **GLM divergence cleaning** for MHD (Dedner et al. 2002) — uses **operator splitting**:
  1. X-sweep and Y-sweep: regular flux updates (hyperbolic transport of psi included in fluxes, but **no multi-dimensional source terms**)
  2. **Separate multi-dimensional source term step** after both sweeps: compute div(B) = ∂Bx/∂x + ∂By/∂y over the full 2D grid, then integrate the source `∂ψ/∂t = -c_h² div(B) - (c_h/c_p)ψ`. This avoids diagonal divergence accumulation from splitting the inherently multi-dimensional divergence operator into 1D sweeps.

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

### Build System (CMake)

Key CMake options:
- `FLOAT_PRECISION` = float | double | quad
- `OPT_LEVEL` = O2 | O3 | Ofast
- `FAST_MATH` = ON | OFF
- `ENABLE_CUDA` = ON | OFF
- `ENABLE_OPENMP` = ON | OFF
- `RIEMANN_STRICT_INEQUALITY` = ON | OFF (controls `<` vs `<=` in HLLC/HLLD)
- `FMA_CONTRACT` = off | fast (**secondary**, if time permits: GCC/Clang `-ffp-contract=off|fast`, NVCC `--fmad=false|true`)

`build_all.sh` primary builds: 2 precisions x 6 compiler configs (O2/O3/Ofast x fast_math) x 2 hardware x 2 riemann = **48 variants per test**. Secondary flags (FMA, -mtune, etc.) explored separately if time permits.

### Key Implementation Details

**HLLC Solver** - The project specifically asks to investigate `<=` vs `<`:
```cpp
// Controlled by RIEMANN_STRICT_INEQUALITY compile flag
#ifdef RIEMANN_STRICT_INEQUALITY
if (SL < Real(0) && Real(0) < S_star)
#else
if (SL <= Real(0) && Real(0) <= S_star)
#endif
```

**Grid2D** - Row-major, variable-last ordering: `data[j * nx * nvars + i * nvars + var]`. Ghost cells: 2 layers on each side.

**Output format** - 64-byte header (magic "HRSC", nx, ny, nvars, precision tag, time) + raw array. **Forced little-endian byte order** in io.hpp (`htole32`/`htole64` or equivalent) to ensure cross-architecture portability between CSC cluster and local machine. Python reads with explicit dtype `<f4` (float) or `<f8` (double) to match.

**GPU kernels** - Separate kernels for each step (not fused) for easier debugging and precision isolation. Thread blocks 16x16. Deterministic tree reduction for CFL computation (no atomics).

**Quad precision** - **1D CPU only**. Do not attempt 2D or GPU quad precision — it would waste cluster time and corrupt profiling metrics. Use quad only as a "ground truth" reference for 1D tests.

**MPI strategy** - This standalone code uses **OpenMP + CUDA** (single-node). MPI is omitted because: (1) the project focuses on precision/hardware effects, not scalable parallelism; (2) single-node execution gives cleaner profiling; (3) MPI's non-deterministic message ordering would add another variable. **This omission must be explicitly justified in Report 2** to avoid losing marks, noting that MPI thread/reduction ordering effects could be explored as future work.

**MHD solver fallback** - If the HLLD solver proves too buggy by end of Week 13, fall back to **HLL** (already implemented in Week 12). HLL is less accurate but sufficient for the precision comparison study — the project's focus is on how precision/hardware affect a *given* solver, not on the solver's absolute accuracy.

**Batch data processing** - `compare.py` and `run_matrix.py` must process results **iteratively**: load one result file at a time, compute scalar L1/L2/Linf norms, append to a summary CSV, then **delete the high-resolution grid file** to avoid disk/memory exhaustion. Never load all results into memory simultaneously.

---

## Test Matrix

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

### Report 2 (MHD + Full Study)

| Test Case | Grid | t_end | Type |
|---|---|---|---|
| Brio-Wu | 800x1 | 0.1 | **1D MHD** shock tube (required: tests must include 1D and 2D) |
| Orszag-Tang | 256x256 | 1.0 | 2D MHD turbulence (chaotic) |
| Kelvin-Helmholtz | 256x512 | varies | 2D MHD shear instability |

Full parameter sweep: precision x opt_level x fast_math x hardware x riemann_variant.
**Performance timing**: wall-clock time recorded for every run (trivial with timer.hpp).

### Error Metrics
- **1D Euler**: L1, L2, Linf vs exact Riemann solution
- **2D Euler/MHD**: L1, L2, Linf vs high-resolution double-precision CPU reference

---

## Weekly Schedule (20 weeks: 2026-03-23 to 2026-08-07)

**Key Deadlines:**
- Report 1 due: **2026-05-29 (Week 10)** — Euler validation, CPU+GPU, float+double
- Mid-term presentation: **Week of 2026-06-01 (Week 11)**
- Report 2 due: **2026-08-07 (Week 20)** — MHD + systematic precision study + ML
- Poster video: **2026-08-12**
- Viva: **2026-08-20 to 2026-09-04**

**Writing buffer policy:** Each report reserves **2 full weeks for writing** + **1 week buffer** before deadline.

---

### Phase 1: Euler Solver + Report 1 (Weeks 1-10)

Report 1 要求 (each 20%):
1. Literature review & background (Euler equations, ideal-MHD overview, FVM, floating-point discussion)
2. Mathematical theory (MUSCL-Hancock, HLLC, algorithmic variation points)
3. Code description (framework choice, precision templating, testing methodology)
4. Validation (>=4 Euler tests with supersonic waves, CPU+GPU, float+double comparison)
5. Write-up quality

---

#### Week 1 (03/23 - 03/29): Foundation - Core Infrastructure

**Code:**
- `common/types.hpp` — HD_FUNC macro, Constants<Real>
- `common/vec.hpp` — Vec<Real,N> with arithmetic operators
- `common/config.hpp` — key=value config file parser
- `common/grid.hpp` — Grid2D<Real,NVars> with ghost cells (test as 1D with Ny=1)
- `common/eos.hpp` — ideal gas EOS: pressure, sound speed, conserved<->primitive
- `common/boundary.hpp` — outflow (transmissive) BCs
- Root `CMakeLists.txt` (minimal, CPU + double only)

**Milestone:** Grid and EOS infrastructure compiles and can be unit-tested

**Writing:** Begin reading literature (Toro 2009, Goldberg floating-point paper, Bard & Dorelli 2014)

> **Actually delivered (as of 2026-04-29)**: Core infrastructure landed; `src/common/` split into `src/core/` + `src/utils/` for clearer FP-vs-utility boundaries — see [week1-summary.md](../week1/week1-summary.md).

---

#### Week 2 (03/30 - 04/05): 1D Euler Solver Core

**Code:**
- `euler/euler_state.hpp` — conserved variable indexing (rho, rho*u, rho*v, E)
- `euler/euler_flux.hpp` — physical flux F(U) for x-direction
- `euler/hllc.hpp` — HLLC Riemann solver (with configurable `<=` vs `<`)
- `euler/muscl.hpp` — MUSCL reconstruction with minmod limiter
- `euler/hancock.hpp` — Hancock half-step predictor
- `euler/euler_solver.hpp/.cpp` — EulerSolver<Real> for 1D (x-sweep only)
- Minimal `main.cpp`
- `tests/toro_1d/toro_tests.hpp` — Sod IC
- `tests/toro_1d/sod.cfg`

**Milestone:** Sod shock tube (含激波，超音速) produces correct density/pressure/velocity profiles

> **Actually delivered (as of 2026-04-29)**: Sod 1D end-to-end correct; HLLC + Rusanov both available (Rusanov added as fallback solver) — see [week2-summary.md](../week2/week2-summary.md).

---

#### Week 3 (04/06 - 04/12): Complete 1D Tests + Exact Solver + Analysis Tools

**Code:**
- `tests/toro_1d/toro_exact.hpp` — exact Riemann solver for reference solutions
- Remaining Toro ICs + config files:
  - **Lax** (含激波，超音速) ✓
  - **123 problem** (两个稀疏波，无激波)
  - **Blast wave** (含强激波，超音速) ✓
  - **Stationary contact discontinuity** (p_L=p_R, u=0, rho_L≠rho_R → S_M=0 exactly). Targeted test for `<=` vs `<` and ±0.0 edge cases. The HLLC numerator for S_M should be zero analytically, but FP round-off may produce ±epsilon.
- `common/io.hpp` — binary output writer (numpy-compatible)
- `common/error_norms.hpp` — L1, L2, Linf norm computation
- Add van Leer and MC slope limiters to `muscl.hpp`

**Analysis:**
- `analysis/compare.py` — load binary data, compute norms
- `analysis/plot_1d.py` — plot 1D profiles with exact solution overlay
- `analysis/requirements.txt`

**Milestone:** All 4 Toro tests pass validation. >=3 tests contain supersonic waves (shocks).

> **Actually delivered (as of 2026-04-29)**: All Toro 1D tests pass against exact Riemann solution. Verificarlo MCA brought online (`p=53` noise floor). Supervisor Week-3 feedback added a parallel work-line — SLIC branch + `vfc_precexp` / unstable-branch detection / FMA instrumentation — folded into Cross-cutting numerical-analysis methods (§Architecture). See [week3-summary.md](../week3/week3-summary.md).

---

#### Week 4 (04/13 - 04/19): Float/Double Templating + 2D Extension

**Code:**
- Template solver for `float` and `double` (explicit instantiations in `euler_solver.cpp`)
- `cmake/PrecisionConfig.cmake` — float/double build selection
- Extend `euler_solver.hpp` with `y_sweep()` and alternating Lie splitting
- `common/boundary.hpp` — add periodic and reflective BCs for 2D

**Milestone:** 1D tests run in both float and double. 2D solver framework compiles.

> **Actually delivered (as of 2026-04-29)**: Three phases delivered — Phase A (A1 Rusanov default, A2 divergence-marker tool, A3 2D Verificarlo cluster runs at 200²×30, A4 SNR / LoSoS / s_req(N) / Pareto metrics), Phase B (PrecisionConfig, EulerSolver split for explicit instantiation, per-axis BC dispatch with periodic+reflective, Catch2 115 cases / 3660 assertions), Phase C (C1 1D + 2D float regression, C2 real-float vs VPREC p24 comparison). See [week4-summary.md](../week4/week4-summary.md).

---

#### Week 5 (04/20 - 04/26): 2D Euler Tests + GPU Development Start

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

---

#### Week 6 (04/27 - 05/03): Complete GPU Euler Solver

**Code:**
- Complete `gpu/euler_kernels.cuh` — remaining kernels (reconstruct, predict, HLLC, CFL reduction)
- `gpu/euler_gpu_solver.cu` — full GPU solver orchestration
- Update `main.cpp` — select CPU/GPU solver via config
- `cmake/CUDASetup.cmake` + `cmake/CompilerFlags.cmake`
- Add remaining 2D tests if needed (Liska-Wendroff configs 4, 12)

**GPU is mandatory for Report 1.** If GPU development slips, use early Week 7 to complete it before experiments.

**Milestone:** GPU Euler solver matches CPU to machine epsilon. Runs on CSC cluster GPU nodes.

---

#### Week 7 (05/04 - 05/10): Experiments + Data Collection for Report 1

**Code:**
- `scripts/build_all.sh` — automated multi-variant builds
- `analysis/precision_comparison.py` — float vs double norm tables
- `analysis/convergence.py` — grid convergence study

**Experiments (on CSC cluster):**
- All 7 Euler test cases x {float, double} x {CPU, GPU} x {O2, Ofast} = 56 runs
- L1/L2/Linf error norms for each configuration
- Grid convergence: N = 50, 100, 200, 400, 800
- Generate all plots: 1D profiles, 2D pseudocolor, difference maps, convergence curves

**Milestone:** All experimental data for Report 1 collected and analyzed.

---

#### Week 8 (05/11 - 05/17): Report 1 Writing - Week 1 of 2 ✍️

**Writing:**
- Literature review & background (20%):
  - Euler equations for compressible ideal gas
  - **Overview of Ideal-MHD equations** (required even though MHD code comes in Report 2)
  - Finite-volume schemes derivation
  - Floating-point arithmetic: IEEE 754, round-off vs truncation, hardware/compiler/thread-ordering effects
- Mathematical theory (20%):
  - MUSCL-Hancock method (reconstruction, Hancock predictor, conservative update)
  - HLLC Riemann solver derivation and wave-speed estimates
  - **MHD-specific numerical methods**: HLLD/HLL Riemann solvers, GLM divergence cleaning (required by marking criteria even for Report 1)
  - Points in algorithms that could be varied: `<` vs `<=`, tolerances, limiter choice
- Code description (20%):
  - Why standalone (not AMReX): full control over FP operations, compiler flags, profiling
  - **Ease-of-implementation features** (required when writing own code): template precision genericity, HD_FUNC macro for CPU/GPU, dimensional splitting architecture, automated build matrix
  - Testing framework: exact Riemann solver for reference, automated parameter sweep, iterative batch processing
  - How exact/converged solutions are determined

**Code (minor):** Fix any issues, generate missing plots

---

#### Week 9 (05/18 - 05/24): Report 1 Writing - Week 2 of 2 ✍️

**Writing:**
- Validation (20%): 1D profiles vs exact, 2D plots vs published results, CPU/GPU comparison tables, float/double comparison tables, convergence rate plots
- Write-up quality (20%): polish all figures (captions, labels, axes), proofread, check references
- Complete first full draft

**Milestone:** Report 1 draft complete and internally reviewed

---

#### Week 10 (05/25 - 05/29): Report 1 Buffer + Submission 📋

**Buffer week:**
- Final proofreading and formatting
- Address any weak sections
- Ensure all marking criteria covered
- Check references (Toro 2009, Liska & Wendroff 2003, Goldberg 1991, etc.)

**Deliverable:** **Report 1 submitted by 2026-05-29 (Friday)**

---

### Mid-term Presentation (Week 11, 06/01 - 06/05)

Prepare and deliver mid-term presentation based on Report 1 results.
Start thinking about Report 2 direction based on Report 1 findings.

---

### Phase 2: MHD + Systematic Study + Report 2 (Weeks 12-20)

Report 2 要求 (weights):
1. Project development (20%): methodology, how Report 1 informed direction
2. Computational results (40%): MHD validation, systematic accuracy study, temporal divergence
3. Conclusions & future work (20%): which changes matter most, reproducibility implications
4. Write-up quality (20%)

**Core marks come from:** systematic accuracy study, temporal divergence quantification, hardware reproducibility analysis. These are the priority.

---

#### Week 12 (06/08 - 06/14): MHD Solver Foundation + HLL

**Code:**
- `mhd/mhd_state.hpp` — 9-component state (rho, rho*v_xyz, B_xyz, E, psi)
- `mhd/mhd_flux.hpp` — MHD flux with magnetic pressure and tension terms
- `mhd/hll.hpp` — HLL 2-wave solver (the **safe baseline**, always works)
- `mhd/glm.hpp` — GLM divergence cleaning:
  - Psi flux terms for 1D sweeps (hyperbolic transport of psi at speed c_h)
  - **Multi-dimensional source term step**: compute div(B) over full 2D grid, update psi source `∂ψ/∂t = -c_h² ∇·B - (c_h/c_p)ψ`
  - **GLM-specific boundary conditions for psi**: outflow BCs → psi = 0 at ghost cells (prevent divergence reflection); periodic BCs → psi wraps naturally
- `mhd/mhd_muscl.hpp` — MUSCL for 9 MHD variables
- `mhd/mhd_hancock.hpp` — Hancock predictor for MHD
- `mhd/mhd_solver.hpp/.cpp` — MHDSolver<Real>: X-sweep → Y-sweep → GLM source step (operator splitting)
- `error_norms.hpp` — add `compute_divB_norms()`: mean and max |∇·B| over the computational domain
- `tests/toro_1d/brio_wu.cfg` — 1D MHD Brio-Wu shock tube config (also used in systematic study later)

**Milestone:** MHD solver with HLL compiles and runs. Brio-Wu 1D MHD shock tube correct. div(B) remains at machine epsilon level. This 1D MHD test is kept for the systematic parameter sweep (requirement: "range of tests in both 1D and 2D").

---

#### Week 13 (06/15 - 06/21): HLLD Solver (with HLL fallback)

**Code:**
- `mhd/hlld.hpp` — HLLD 5-wave solver (Miyoshi & Kusano 2005) — most complex function
- Validate HLLD against HLL on simple tests
- `tests/orszag_tang/orszag_tang.hpp` + config — Orszag-Tang vortex IC
- `tests/kelvin_helmholtz/kh.hpp` + config — KH instability with B field

**Fallback plan:** If HLLD is too buggy by end of this week, **proceed with HLL** for all subsequent MHD work. The precision comparison study is valid with any correct Riemann solver — the focus is on how precision/hardware affect the *same* solver, not on solver accuracy.

**Milestone:** Orszag-Tang at t=0.5 correct (with HLLD or HLL). Decision point: HLLD or HLL for remainder.

---

#### Week 14 (06/22 - 06/28): GPU MHD + Experiment Infrastructure

**Code:**
- `gpu/mhd_kernels.cuh` + `gpu/mhd_gpu_solver.cu` — CUDA MHD solver
- `scripts/run_experiments.sh` — full automated experiment runner
- `analysis/run_matrix.py` — orchestrate full parameter sweep
  - **Must process iteratively**: load one result, compute norms, append to CSV, delete grid file
  - Never load all results into memory

**Experiments (begin data collection):**
- MHD CPU+GPU validation (float + double)
- Begin systematic Euler parameter sweep

**Milestone:** MHD runs on both CPU and GPU. Automated pipeline ready.

---

#### Week 15 (06/29 - 07/05): Systematic Precision Study - Primary Axes

**Primary investigation axes** (exhaustive sweep):
1. **Floating-point precision**: {float, double} — primary source of round-off differences
2. **Compiler optimisation + fast-math**: {O2, O3, Ofast} x {fast_math ON/OFF} — FP associativity & instruction reordering
3. **Hardware platform**: {CPU, GPU} — architectural differences in numerical behaviour
4. **Implementation variation**: {<= vs <} — sensitivity to small algorithmic changes

**Core experiment matrix**: 2 x 6 x 2 x 2 = **48 runs per test case** on all Euler + MHD tests (1D+2D).
- `analysis/precision_comparison.py` — LaTeX-ready norm tables and bar charts
- **Performance timing**: wall-clock for every run (enables accuracy-vs-performance trade-offs)

**Milestone:** Primary parameter sweep complete for all test cases.

---

#### Week 16 (07/06 - 07/12): Error Source Analysis (核心分析周)

This week focuses on **understanding and explaining** the errors, not just measuring them.

**A. Round-off vs Truncation Error Separation** (core):
- `analysis/roundoff_vs_truncation.py`
- Run same test at resolutions N = 50, 100, 200, 400, 800, 1600 in both float and double
- Plot L2 error vs dx on log-log scale for both precisions
- **Key insight**: identify the crossover resolution where float round-off dominates truncation error (the "precision saturation point")

**B. div(B) Evolution** (core for MHD):
- `analysis/divb_evolution.py`
- For Orszag-Tang and KH: mean/max |∇·B| vs time for float vs double
- **Key insight**: does lower precision degrade divergence cleaning effectiveness?

**C. Temporal Divergence + Lyapunov Exponent Fitting** (core):
- `analysis/temporal_divergence.py`
- For chaotic tests: output at many time steps, compute ||u_A - u_B|| for each primary axis
- Fit `log(error) = λt + c` to extract Lyapunov-like exponent
- **Key insight**: quantify how fast precision/hardware differences grow in chaotic flows

**Milestone:** Error source decomposition complete. Round-off saturation point identified. Lyapunov exponents extracted.

---

#### Week 17 (07/13 - 07/19): Results Synthesis + Secondary Experiments

**Core synthesis (must complete):**
- Which primary axes have most effect on accuracy? Rank: precision > compiler > hardware?
- Which test cases are most sensitive to which changes?
- Round-off vs truncation crossover table per test
- Lyapunov exponent table across test cases
- Explicit justification for MPI omission
- Generate all final plots and tables

**Secondary experiments (if time permits — extend from Week 17 buffer):**

| Secondary Item | What it adds | Can add in |
|---|---|---|
| FMA control (`-ffp-contract=off` vs `fast`, `--fmad`) | Another compiler-level FP variation | Week 17 |
| CFL sensitivity (0.2, 0.4, 0.6, 0.8) | Time integration vs flux error separation | Week 17 |
| Limiter sensitivity (minmod, van Leer, MC) | Reconstruction round-off amplification | Week 17 |
| OpenMP thread count (1, 2, 4, 8) | Thread-ordering non-determinism | Week 17 |
| `-mtune` / vectorisation options | CPU microarchitecture effects | Week 17 |
| Quad precision (1D CPU only) | Ground truth reference | Week 17 |
| RAPTOR / Verificarlo | Advanced FP analysis tools | Week 17 |
| ML error predictor | Predictive model from sweep data | Week 17 |

**Strategy**: Complete core synthesis first. Then pick secondary items by expected insight-per-effort ratio. FMA and CFL sensitivity are highest-value secondary items (directly explain *why* results differ). Thread count and limiters are next. RAPTOR/Verificarlo/ML are lowest priority.

**Milestone:** Core analysis complete. Secondary items done if time allowed. Ready for writing.

---

#### Week 18 (07/20 - 07/26): Report 2 Writing - Week 1 of 2 ✍️

**Writing:**
- Project development (20%): methodology for parameter selection, how Report 1 findings informed direction, explicit justification for omitting MPI
- Computational results (40%):
  - MHD validation: Brio-Wu 1D + Orszag-Tang + KH 2D (CPU+GPU, float+double)
  - **Primary axes results**: precision x compiler x hardware x implementation variation
  - Performance timing comparison (float vs double, CPU vs GPU speedup)
  - Round-off vs truncation separation (precision saturation point)
  - div(B) evolution: float vs double divergence cleaning effectiveness
  - Temporal divergence + Lyapunov exponents (key for chaotic MHD)
  - [If completed] Secondary results (FMA, CFL, limiters, thread count) as additional exploration

---

#### Week 19 (07/27 - 08/02): Report 2 Writing - Week 2 of 2 ✍️

**Writing:**
- Conclusions & future work (20%):
  - Which changes (precision, hardware, compiler, implementation) have most effect
  - Reproducibility implications for CFD community
  - Future work: MPI effects, ML-assisted precision analysis, more test cases
- Write-up quality (20%): polish figures, proofread, references
- Complete full draft

**Milestone:** Report 2 draft complete

---

#### Week 20 (08/03 - 08/07): Report 2 Buffer + Submission 📋

**Buffer week:**
- Final proofreading and formatting
- Address any weak sections
- Ensure all marking criteria fully covered
- Final reference check

**Deliverable:** **Report 2 submitted by 2026-08-07 (Friday)**

---

### Post-Report 2

**Week 21 (08/08 - 08/12):** Poster presentation video (due 2026-08-12)
- Summarize key findings visually
- Focus on most impactful results (precision/hardware/compiler effects)

**Weeks 22-24 (08/13 - 09/04):** Viva preparation
- Review both reports and all results
- Prepare for oral examination questions
- Be ready to explain: why no MPI, why standalone (not AMReX), HLLD vs HLL decision

---

## Supersonic Wave Test Cases (满足 Report 1 要求: >= 4 tests with supersonic waves)

| # | Test Case | Supersonic Feature | Type |
|---|---|---|---|
| 1 | Sod Shock Tube | Shock wave (Ma > 1 relative to pre-shock gas) | 1D ✓ |
| 2 | Lax Shock Tube | Stronger shock wave | 1D ✓ |
| 3 | 123 Problem | Two rarefaction waves only (no shock) | 1D ✗ |
| 4 | Blast Wave | Two strong shocks (very high Ma) | 1D ✓ |
| 5 | Stationary Contact | No waves (contact only, S_M=0 edge case) | 1D ✗ |
| 6 | Liska-Wendroff Config 3 | Four interacting shocks | 2D ✓ |
| 7 | Liska-Wendroff Config 6 | Shock interactions | 2D ✓ |
| 8 | Shock-Bubble | Planar shock hitting bubble | 2D ✓ |

**Total with supersonic waves: 6 out of 8 tests ✓** (far exceeds minimum of 4). Tests 3 and 5 serve different purposes: 123 tests near-vacuum handling, stationary contact tests `<=` vs `<` at S_M=0.

---

## Appendix: Secondary & Optional Items (Week 17 if time permits)

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

### If none completed:

Mention uncompleted items as **future work** in Report 2 conclusions. The core analysis (4-axis primary sweep, round-off vs truncation separation, div(B) evolution, Lyapunov exponents) is sufficient for full marks on "Computational Results (40%)".

---

## Verification Strategy

1. **Unit validation**: Each component tested in isolation (exact Riemann solver matches Toro's published values, MUSCL produces correct slopes, etc.)
2. **Convergence verification**: Second-order convergence on smooth problems confirms correct implementation
3. **Cross-validation**: CPU vs GPU must agree to machine epsilon for same precision/flags (any discrepancy = bug)
4. **Published benchmarks**: Compare 2D plots against Liska & Wendroff (2003), Bard & Dorelli (2014)
5. **Precision cascade**: double reference -> float comparison -> norm tables -> temporal divergence plots

---

## Mapping to Report Requirements

### Report 1 Sections -> Implementation Phases

| Report Section (20% each) | Code Done By | Writing In | Key Requirements |
|---|---|---|---|
| Literature review & background | — | Weeks 8-9 | Must cover Euler AND MHD equations, FVM, FP arithmetic |
| Mathematical theory | Week 2-3 | Weeks 8-9 | MUSCL-Hancock, HLLC, **MHD methods (HLLD, GLM)**, variation points |
| Code description | Week 6 | Weeks 8-9 | Why standalone, **ease-of-impl features**, testing framework, reference solutions |
| Validation | Week 7 experiments | Weeks 8-9 | >=4 tests w/ supersonic, 1D+2D, CPU+GPU, float+double |
| Write-up quality | — | Weeks 8-10 | Figures, references, completeness |

### Report 2 Sections -> Implementation Phases

| Report Section | Data Collected By | Writing In |
|---|---|---|
| Project development (20%) | — | Weeks 18-19 |
| Computational results (40%) | **Weeks 14-17** (MHD + full parameter sweep) | Weeks 18-19 |
| Conclusions & future work (20%) | Week 16-17 synthesis | Weeks 18-19 |
| Write-up quality (20%) | — | Weeks 18-20 (buffer in Week 20) |
