# Spec: Align `docs/requirement/overall.md` with current project state (C2)

**Date**: 2026-04-29
**Branch**: `week4-implementation`
**Author**: Claude (brainstorming session) + user approval
**Approach**: C2 — content alignment without re-sequencing the timeline.

---

## 1. Motivation

`docs/requirement/overall.md` is the Week-1 master plan written before any code existed. After 4 weeks of work it has drifted from current state in five concrete ways:

1. Source layout: plan says `src/common/`, actual is `src/core/` + `src/utils/`; plan says `src/tests/`, actual is top-level `tests/`; plan says `analysis/`, actual is `scripts/{regression,metrics,verificarlo,figures,cluster}/`.
2. Solver scope: plan only enumerates HLLC; default solver is now `rusanov` (supervisor Phase A1), and SLIC is on a separate branch per supervisor Week-3 feedback.
3. Verificarlo positioning: plan classifies Verificarlo as Tier 3 "if time permits, Week 17"; reality is that Weeks 3–4 already delivered MCA noise-floor calibration, p24-real comparison, 2D 200²×30 SLURM array, and C2 real-vs-VPREC analysis. Supervisor Week-3 also requested `vfc_precexp` / unstable-branch detection / FMA instrumentation, none of which appear in the plan.
4. New analytical metrics (SNR / LoSoS / s_req(N) / Pareto) introduced via supervisor Phase A4 — absent from the plan.
5. Mid-Week-4 infrastructure additions (per-axis `bc_x`/`bc_y`, `TimeReal=double` mixed-precision time step, Catch2 115×3660 unit suite) — absent from the plan.

**Goal**: Make `overall.md` self-consistent with the current code and per-week summaries while keeping the original 20-week schedule, Report 1/2 deliverable structure, and verification strategy intact. INDEX.md will continue to be the entry point; overall.md becomes the canonical "what we are building and why" document.

**Non-goals**:
- Do not re-sequence weeks or change Report deadlines.
- Do not duplicate the per-week summary content; use one-line callouts plus links.
- Do not rewrite Phase 2 (Weeks 12–20) text except where Phase 1 changes affect downstream wording.
- Do not produce a new file — edit `overall.md` in place.

---

## 2. Editing scope (binding)

The following six regions of `overall.md` will be modified. No edits outside this list.

| # | Region | Action |
|---|---|---|
| 2.1 | § Architecture Overview | Insert new subsection *Cross-cutting numerical-analysis methods* between «Numerical Method» and «Directory & File Structure» |
| 2.2 | § Directory & File Structure | Replace tree to match current source layout |
| 2.3 | § Test Matrix → Report 1 (Euler Validation) | Update 1D Toro test names + add Rusanov-default note |
| 2.4 | Weeks 1–4 (each week's body) | Append a one-callout *Actually delivered (as of 2026-04-29)* line linking to per-week summary |
| 2.5 | Weeks 5–7 (each week's body) | Targeted content adjustments reflecting current load + risk notes |
| 2.6 | § Appendix: Secondary & Optional Items | Re-tier Verificarlo / vfc_precexp / unstable-branches up; adjust Tier 1/2/3 ordering |

**Untouched regions** (explicit non-edits):
- Weekly date headers (e.g. "Week 5 (04/20 - 04/26)") and report deadlines.
- Report 1 / Report 2 section × weight tables (5 × 20% / 20+40+20+20).
- § Verification Strategy.
- § Mapping to Report Requirements.
- § Supersonic Wave Test Cases table.
- Phase 2 weeks (12–20) body, except where a Week 5–7 change forces a forward reference.

---

## 3. Detailed edits

### 3.1 New subsection — *Cross-cutting numerical-analysis methods*

**Location**: § Architecture Overview, inserted between «Numerical Method» and «Directory & File Structure» blocks.

**Verbatim content** (final wording, not draft):

> ### Cross-cutting numerical-analysis methods
>
> Beyond the deterministic FVM solver, the project relies on a set of stochastic / instrumented FP-analysis tools as **core methodology** (not optional extensions):
>
> - **Verificarlo MCA (Monte-Carlo Arithmetic)** — perturbs every FP op at chosen virtual precision *p*. Used to (i) establish noise floors per test (`p=53` baseline), (ii) act as a virtual-precision surrogate for `float` (`p=24`) when comparing against real `float`, (iii) drive 2D large-grid statistical batches (200²×30 SLURM array on CSC).
> - **Verificarlo `vfc_precexp` (mixed-precision exploration)** — per-call minimum-precision search; informs which routines tolerate `float` vs require `double`. Feeds Report 2 mixed-precision argument.
> - **Verificarlo unstable-branch detection** — flags conditional branches whose taken-side is FP-rounding-sensitive (e.g. HLLC `S* == 0` selection, `<= vs <` choice).
> - **FMA instrumentation** (`--inst-fma`) — quantifies the contribution of fused-multiply-add single-rounding to result drift.
> - **SNR / LoSoS / s_req(N) / Pareto metrics** — quantitative answer to «how many significant digits does the simulation actually deliver, and at what cost?». `s_req(N)` anchors precision to truncation-error level; Pareto plots trade σ_FP against worst-cell error.
>
> Implication: Verificarlo is treated as a *Tier-1 cross-cutting method* (originally Tier 3 in the Week-1 plan), used continuously from Week 3 onward, not deferred to Week 17.

### 3.2 § Directory & File Structure — replacement tree

Replace the existing tree with the following. Comments preserved where they remain accurate; (planned Week N) annotations added where files do not yet exist.

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

### 3.3 § Test Matrix — Report 1 (Euler Validation)

Replace the 1D Toro rows with:

| Test Case | cfg | Grid | t_end | Type |
|---|---|---|---|---|
| sod (Toro 1) | `tests/cases/toro_1d/sod.cfg` | 200×1 | 0.25 | 1D shock tube |
| toro2 (Lax) | `toro2.cfg` | 200×1 | 0.15 | 1D stronger shock |
| toro3 (123 problem) | `toro3.cfg` | 200×1 | 0.15 | 1D two rarefactions |
| toro4 (blast) | `toro4.cfg` | 200×1 | 0.035 | 1D strong shocks |
| toro5 | `toro5.cfg` | 200×1 | 0.012 | 1D shock-contact-shock |
| stationary_contact | `stationary_contact.cfg` | 200×1 | 0.5 | 1D: p_L=p_R, u=0, ρ_L≠ρ_R → S_M=0 (targeted `<=` vs `<` test) |

Add a paragraph immediately under the table:

> **Solver default**: `solver = rusanov` is the default since Week 4 (supervisor Phase A1). HLLC is enabled per-cfg via `solver = hllc`; `_rusanov.cfg` and HLLC twins exist for several Toro cases for direct A/B comparison.

The 2D rows (Liska–Wendroff Config 3 / Config 6 / Shock-Bubble) keep their existing entries; mark Config 6 and Shock-Bubble as «planned Week 5».

### 3.4 Weeks 1–4 — *Actually delivered* callouts

**Pattern**: at the end of each week's body, add a single block-quote line:

> **Actually delivered (as of 2026-04-29)**: \<one-line summary\> — see [weekN-summary.md](../weekN/weekN-summary.md).

**Per-week wording** (final):

- **Week 1**: «Core infrastructure landed; `src/common/` split into `src/core/` + `src/utils/` for clearer FP-vs-utility boundaries.»
- **Week 2**: «Sod 1D end-to-end correct; HLLC + Rusanov both available (Rusanov added as fallback solver).»
- **Week 3**: «All Toro 1D tests pass against exact Riemann solution. Verificarlo MCA brought online (`p=53` noise floor). Supervisor Week-3 feedback added a parallel work-line: SLIC branch + `vfc_precexp` / unstable-branch detection / FMA instrumentation as cross-cutting methods (folded into Cross-cutting numerical-analysis methods, §Architecture).»
- **Week 4**: «Three phases delivered — Phase A (A1 Rusanov default, A2 divergence-marker tool, A3 2D Verificarlo cluster runs at 200²×30, A4 SNR / LoSoS / s_req(N) / Pareto metrics), Phase B (PrecisionConfig, EulerSolver split for explicit instantiation, per-axis BC dispatch with periodic+reflective, Catch2 115 cases / 3660 assertions), Phase C (C1 1D + 2D float regression, C2 real-float vs VPREC p24 comparison).»

### 3.5 Weeks 5–7 — forward content adjustments

#### Week 5 (04/20 – 04/26)

Replace the body's «Code (2D tests)» and «Code (GPU)» blocks with:

> **Code (2D tests + closing Phase 1 infra gaps):**
> - Replace the Config-6 stub in `tests/cases/liska_wendroff_2d/lw_tests.hpp` (`setup_liska_wendroff_config6` currently throws) with a real IC + add `config6_n200.cfg` / `config6_n400.cfg`.
> - `tests/cases/shock_bubble/` — new IC header + cfg for shock-bubble interaction (supersonic shock, satisfies 1D+2D requirement).
> - `src/utils/timer.hpp` — wall-clock timer (records every run for performance analysis).
>
> **Code (GPU bring-up — skeleton only):**
> - `src/gpu/cuda_utils.cuh` — CUDA error-check macro, DeviceArray wrapper.
> - `src/gpu/gpu_grid.cuh` — device mirror of Grid2D, host↔device transfers.
> - `src/gpu/euler_kernels.cuh` — first kernels (conservative update, BC). Compilable empty implementations are acceptable; full kernels are Week 6.
>
> **Risk note**: Full GPU Euler solver is deferred to Weeks 6–7. If Week 5 progress is tight, shock-bubble may slip to Week 6 — Config 6 + GPU skeleton are the non-deferrable items because they unblock 2D test coverage and the Week-6 kernel work.

Keep the original «Analysis: `analysis/plot_2d.py`» line but replace the path with «`scripts/figures/plot_2d.py` (or equivalent in `scripts/figures/`)» and note that current 2D-plot capability is already partially provided by `phase_error_metrics.py` + heatmap scripts.

#### Week 6 (04/27 – 05/03)

Append one paragraph to the body:

> **Carry-over from Week 5**: complete remaining 2D Euler tests if not finished. Extend Phase-C float-regression pipeline to GPU outputs once kernels land — same `summary.{md,json}` schema, same SSIM / L1 / phase metrics; CPU-vs-GPU same-precision diff must be ≤ ULP-level.

#### Week 7 (05/04 – 05/10)

Append to the «Experiments» block:

> Reuse the Week-4-established Verificarlo + SNR / LoSoS / s_req(N) / Pareto pipeline for the full Euler matrix. Performance timing (via `src/utils/timer.hpp`) recorded per run; build matrix automated via `scripts/build_all.sh`. CPU-vs-GPU same-precision diff is enforced as a regression gate.

### 3.6 § Appendix: Secondary & Optional Items — re-tiering

Replace the three Tier tables with:

**Tier 1 — Core methods (already adopted in Weeks 3–4)**

| Item | Status | Notes |
|---|---|---|
| Verificarlo MCA (`p=53` noise floor, `p=24` float-surrogate, 2D batch) | adopted | See `scripts/verificarlo/`, `experiments/verificarlo/runs_p53_mca*` |
| SNR / LoSoS / s_req(N) / Pareto metrics | adopted | See `scripts/metrics/` + `scripts/figures/pareto_plot.py` |
| FMA control (`-ffp-contract`, `--fmad`, `--inst-fma`) | adopted | C2 `_fma` variant runs already exist |
| `vfc_precexp` (mixed-precision exploration) | planned (carry-over from Week-3 supervisor ask) | Schedule: Week 14 once MHD lands, or earlier if MHD slips |
| Verificarlo unstable-branch detection | planned (carry-over from Week-3 supervisor ask) | Schedule: alongside `vfc_precexp` |

**Tier 2 — Incremental experiments (do if time permits)**

| Item | Notes |
|---|---|
| CFL sensitivity (0.2, 0.4, 0.6, 0.8) | Time integration vs flux error separation |
| Limiter sensitivity (minmod, van Leer, MC) | Reconstruction round-off amplification |
| OpenMP thread count (1, 2, 4, 8) | Reduction-ordering non-determinism |
| `-mtune` / vectorisation options | CPU microarchitecture effects |
| Quad precision (1D CPU only) | Ground-truth reference; do not attempt 2D / GPU |
| MPI non-determinism demo | Standalone `MPI_Reduce` script for Report 2 reproducibility section |

**Tier 3 — Advanced / exploratory (lowest priority)**

| Item | Notes |
|---|---|
| RAPTOR (mixed precision, special compiler) | `/lsc/opt/raptor`, clang++-20 |
| ML error predictor | scikit-learn; only if Tier-1+2 complete |

---

## 4. Implementation plan (summary)

The detailed plan will be produced by `superpowers:writing-plans` after this spec is approved. High-level shape:

1. Single-PR / single-commit edit to `docs/requirement/overall.md`.
2. Diff size: ~150–200 lines (estimate; replacements + insertions roughly balance deletions).
3. Verification: `git diff --stat` shows only `docs/requirement/overall.md` + this spec. Render-check the markdown in IDE preview to confirm no broken links or table-syntax issues. No code changes; no test impact.
4. Commit policy:
   - Commit 1: `docs(spec): add C2 alignment design for overall.md` — adds this file.
   - Commit 2: `docs(requirement): align overall.md with Week-4 state (C2)` — applies §3 edits.

---

## 5. Acceptance criteria

- [ ] `overall.md` § Directory & File Structure matches `src/` layout verifiable by `ls src/` (no path that does not exist; no missing top-level dir).
- [ ] § Test Matrix Report-1 row names appear as cfg files in `tests/cases/toro_1d/`.
- [ ] New § Cross-cutting numerical-analysis methods exists between «Numerical Method» and «Directory & File Structure».
- [ ] Each of Weeks 1–4 ends with the *Actually delivered* callout linking to a real `weekN-summary.md`.
- [ ] Week 5 body includes the GPU-skeleton risk note and lists Config 6 + shock-bubble + `timer.hpp` as the closing-Phase-1 items.
- [ ] Appendix tier table moves Verificarlo / SNR-LoSoS-Pareto / FMA into Tier 1, demotes RAPTOR / ML to Tier 3.
- [ ] Phase 2 (Weeks 12–20) body unchanged except where a Week 5–7 carry-over reference forces it.
- [ ] Markdown renders without broken internal links (`../weekN/weekN-summary.md` paths resolve from `docs/requirement/`).

---

## 6. Open questions / explicit deferrals

- The plan lists Liska–Wendroff configs 3/4/6/12; current code has only config 3 plus a config-6 stub. Configs 4 / 12 stay in the Test Matrix as «optional» without changing the table — flagged in the Week-5 body.
- SLIC branch existence is asserted from supervisor-feedback memory (which is 18 days old). This spec's Week-3 callout phrases it as «added a parallel work-line» rather than asserting current branch state; if SLIC was abandoned, the wording still reads correctly as historical record.
- `experiments/` directory listing in the new tree is illustrative; actual contents are tracked by INDEX.md § 6 «Data products map» and will continue to live there, not in `overall.md`.

---

*End of spec.*
