# Week 12 Remainder — 2D MHD Machinery + GLM Cleaning: Design

**Date:** 2026-06-17
**Status:** Approved (brainstorming) → ready for writing-plans
**Scope:** Complete the 2D parts of master-schedule Week 12 left undone by the 1D walking skeleton
**Owner:** beren

---

## Context

The Week 12 1D MHD walking skeleton is complete and validated (see
[2026-06-11-report2-week12-mhd-1d-design.md](2026-06-11-report2-week12-mhd-1d-design.md)
and [docs/week12/week12-summary.md](../../week12/week12-summary.md)): 9-var state,
GLM-coupled x-flux, HLL solver, MUSCL-Hancock, `hrsc_mhd`, `compute_divB_norms`,
Brio-Wu self-converged validation. The `src/mhd/` layer is additive and the
Euler binary/`app/` layer is untouched.

This spec covers the **2D machinery that overall.md lists under Week 12 but the
1D skeleton deferred**: the Y-sweep, the GLM cleaning stage, ψ/periodic boundary
conditions, and two cheap validations that exercise them. Orszag-Tang and KH
physics validation remain Week 13 per overall.md.

### Established codebase patterns (verified against source)

- **Euler y-sweep is rotate-and-reuse**: `y_sweep` rotates state with
  `swap_momentum`, calls the x-direction flux, rotates back
  ([src/euler/euler_solver.cpp:258-264](../../../src/euler/euler_solver.cpp)).
  MHD mirrors this.
- **`apply_reflective_bc` is generic** over which components to sign-flip via a
  `flip_indices` array ([src/core/boundary.hpp:108](../../../src/core/boundary.hpp));
  `apply_periodic_bc` / `apply_outflow_bc` are `NVars`-generic. The MHD path
  already calls `apply_outflow_bc`.
- **`MhdSolver` already uses `Grid2D<Real, MhdNVars>` with `ny=1`**; extending to
  `ny>1` is the same unified-solver pattern `EulerSolver` already follows.
- **1D flux carries the full hyperbolic ψ–Bₙ coupling**: `F[BX]=ψ`,
  `F[PSI]=c_h²·Bx` ([src/mhd/mhd_flux.hpp:20,24](../../../src/mhd/mhd_flux.hpp)).

### Decisions locked during brainstorming

| # | Decision | Choice |
|---|---|---|
| 1 | 2D validation scope | Machinery + cheap validations (2D Brio-Wu regression + div(B)-cleaning diagnostic); Orszag-Tang/KH stay Week 13 |
| 2 | GLM damping parameter | cfg `glm_cr` (default 0.18), `c_p² = c_h·c_r`, analytic decay ψ·=exp(−Δt·c_h²/c_p²); with this convention smaller positive `c_r` damps faster |
| 3 | Boundary conditions | Add **periodic** for 9-var MHD + ψ=0-at-ghost rule for outflow; reflective deferred to Week 13 (KH) |
| 4 | GLM formulation | **Canonical Dedner**: keep 1D flux coupling untouched, add parabolic damping post-sweep, full-grid div(B) as diagnostic |
| 5 | Solver structure | Extend `MhdSolver<Real>` **in place** to unified 1D/2D (mirrors EulerSolver); 1D path bit-preserved |

### GLM formulation rationale (decision 4)

In canonical Dedner mixed-GLM the divergence cleaning is delivered by the
hyperbolic ψ–Bₙ flux coupling already present in 1D. Across a full 2D step the
x-sweep contributes `∂ψ/∂t ⊃ −c_h²·∂Bx/∂x` and the y-sweep contributes
`−c_h²·∂By/∂y`, so ψ sees `−c_h²·∇·B` automatically — no separate div(B) source
step is needed, and adding one on top of the flux term would **double-count** the
coupling (over-cleaning / instability). The only piece missing for multi-D is the
**parabolic damping** ψ·=exp(−Δt·c_h²/c_p²), added as the post-sweep stage. The
full-grid `div(B)` (already in `compute_divB_norms`) is used as the cleaning
**diagnostic** and as the assertion metric for the decay test.

This is a mild, documented deviation from overall.md's literal "compute div(B)
and source ψ" wording, adopted because it is textbook-correct, avoids
double-counting, and keeps the validated 1D flux bit-identical.

---

## Architecture

All changes are additive or in-place extensions of the existing MHD path. The
`hrsc` Euler binary and `src/app/` layer remain untouched.

### New / modified files

```
src/mhd/mhd_flux.hpp     # ADD mhd_swap_xy(U): swap (MX<->MY) and (BX<->BY)
src/mhd/glm.hpp          # NEW: glm_damp(gv, nx, ny, ch, cr, dt); c_p from c_r
src/mhd/mhd_config.hpp   # MODIFY: parse_mhd_boundary accepts "periodic"
src/mhd/mhd_solver.hpp   # MODIFY: add ny, dy, m_bc_y, m_glm_cr; declare y_sweep
src/mhd/mhd_solver.cpp   # MODIFY: y_sweep, 2D compute_ch, x->y->glm step order
src/core/boundary.hpp    # (reused as-is; ψ=0-ghost handled in solver post-pass)
src/mhd_main.cpp         # MODIFY: parse ny/ymin/ymax/bc_y/glm_cr; 2D grid + IO

tests/cases/brio_wu_1d/brio_wu_2d.cfg     # NEW: nx=800 ny=4 periodic-y
tests/cases/mhd_divb_clean/divb_blob.cfg  # NEW: doubly-periodic div(B) bump
tests/unit/test_mhd_swap.cpp              # NEW: swap round-trip + flux equivalence
tests/unit/test_glm.cpp                   # NEW: glm_damp decay factor
tests/unit/test_mhd_periodic.cpp          # NEW: 9-var periodic wrap
scripts/regression/mhd_2d_week12.py       # NEW: 2D regression + cleaning driver
```

### Component responsibilities

- **`mhd_swap_xy(U)`** — returns a copy of the 9-var state with MX↔MY and BX↔BY
  swapped (MZ, BZ, RHO, E, PSI unchanged). Self-inverse. Enables y-sweep to reuse
  `mhd_flux_x` and `mhd_hll_flux`. **Depends on:** `mhd_state.hpp`.
- **`glm.hpp::glm_damp`** — applies ψ·=exp(−Δt·c_h²/c_p²) to every cell, with
  `c_p² = c_h·c_r`. No-op when `c_r ≤ 0`. Owns the cfg-driven damping; the
  divergence source is NOT here (it lives in the sweep fluxes). **Depends on:**
  `mhd_state.hpp`, `core/grid.hpp`.
- **`MhdSolver<Real>` (extended)** — fields gain `m_ny`, `m_dy`, `m_bc_y`,
  `m_glm_cr`. Per step: `apply_bc()` → `compute_ch()` (2D max) →
  `x_sweep(dt)` → `apply_bc()` → `y_sweep(dt)` → `glm_damp(...)`. The second
  boundary pass refreshes y-ghost cells after the x-sweep, matching the existing
  Euler 2D sweep pattern. 1D (`ny==1`) skips `y_sweep`; with ψ≈0 the damping is
  negligible, so 1D Brio-Wu stays bit-identical.
  `y_sweep` = for each y-interface, reconstruct/predict in y by rotating cells
  with `mhd_swap_xy`, compute HLL on rotated states, rotate the flux back
  (mirrors Euler `y_sweep`). **Depends on:** `mhd_flux.hpp`, `hll.hpp`,
  `mhd_reconstruct.hpp`, `glm.hpp`, `core/boundary.hpp`.
- **ψ boundary rule** — after `apply_outflow_bc`, a small MHD post-pass sets
  ghost-cell PSI = 0 (prevents divergence-error reflection); periodic wraps ψ
  naturally via `apply_periodic_bc`. Applied per active axis.
- **`mhd_main.cpp`** — parses `ny` (default 1), `ymin`/`ymax`, `bc`/`bc_y`,
  `glm_cr` (default 0.18); builds the 2D grid; writes a 2D binary (nvars=9). 1D
  cfgs keep working (ny defaults to 1).

### Operator splitting

Lie splitting per step: `x_sweep(dt)` → boundary refresh → `y_sweep(dt)` →
`glm_damp(dt)`. Second-
order Strang alternation is deferred to Week 13 (Lie is sufficient to validate the
machinery and the cleaning behaviour). `compute_ch` becomes the global maximum of
`|vx|+c_f` and `|vy|+c_f` over physical cells; it sets both the CFL `dt` and the
GLM cleaning speed.

---

## Numerics correctness gates

- **2D Brio-Wu regression**: `nx=800, ny=4`, periodic in y, all rows identical
  ICs. Each row's density must match the 1D Brio-Wu result to L∞ ≤ 1e-10
  (double); `divB_max` stays at round-off (~1e-13). Confirms the y-sweep +
  rotation introduce no transverse corruption.
- **div(B)-cleaning diagnostic**: doubly-periodic 128² grid, uniform `ρ=1, p=1,
  v=0, By=Bz=0, ψ=0`, and a smooth Gaussian magnetic bump in the normal
  component: `Bx = B0·exp(−((x−0.5)²+(y−0.5)²)/σ²)` with `B0=1, σ=0.1`. This
  makes `div(B)=∂Bx/∂x` nonzero, smooth, and analytically known. Because the
  hyperbolic GLM subsystem propagates divergence waves, `max|div(B)|` is not a
  guaranteed monotone time series. The validation records div(B) over checkpoints
  and gates on robust comparisons: finite runs, damped cases no worse than the
  `glm_cr=0` control at the final checkpoint, and the smaller positive
  `glm_cr=0.18` no worse than `0.36` under the `c_p²=c_h·c_r` convention.

---

## Build system

No new CMake targets. `mhd_swap_xy` and `glm_damp` are header-only / compiled into
the existing `hrsc_mhd_lib`. New unit tests are picked up by the existing
`tests/unit/test_*.cpp` glob and link against `hrsc_mhd_lib`.

---

## Testing (TDD, bottom-up)

1. **Unit (Catch2):**
   - `mhd_swap_xy` is self-inverse; `mhd_flux_x(swap(U))` rotated back equals the
     y-flux of `U` for a known state.
   - `glm_damp` reduces ψ by exactly exp(−Δt·c_h²/c_p²); ψ=0 stays 0; c_r≤0 is a
     no-op.
   - 9-var periodic BC wraps every component including ψ.
2. **Integration:** 2D Brio-Wu (nx=800, ny=4) runs to t_end without NaNs; the
   div(B) bump case runs on a periodic grid.
3. **Validation:** the two correctness gates above, driven by
   `scripts/regression/mhd_2d_week12.py` with the project's provenance discipline
   (generated cfgs, stdout/stderr, metadata.json, summary.{csv,json,md}).

---

## Out of scope (named to prevent scope creep)

Orszag-Tang & KH physics validation · HLLD · GPU MHD · reflective MHD boundary
condition · `run_matrix.py` MHD-awareness · 2D result **figures** (the Week-12
figure gap is carried into the Week-13 plan) · Strang 2nd-order splitting.

---

## Acceptance / milestone

- `hrsc_mhd` runs 2D cfgs (ny>1) and still runs all 1D cfgs.
- 1D Brio-Wu output is **bit-identical** to the current validated result.
- 2D Brio-Wu (ny=4, periodic-y) reproduces the 1D profile (L∞ ≤ 1e-10) with
  `divB_max` at round-off.
- div(B)-cleaning diagnostic records checkpointed `max|div(B)|`/mean values and
  shows damped cases are no worse than the `glm_cr=0` control at the final
  checkpoint, with smaller positive `glm_cr` damping at least as strongly as a
  larger one under the chosen `c_p²=c_h·c_r` convention.
- New Catch2 unit tests green; existing MHD + Euler suites untouched and passing.

---

## Deliverable docs

- `docs/week12/week12-plan-2d.md` — checkbox implementation plan (from writing-plans).
- Update `docs/week12/week12-summary.md` with the 2D addendum at close.
- Carry the 2D-figure gap and Orszag-Tang/KH into the Week-13 plan.
