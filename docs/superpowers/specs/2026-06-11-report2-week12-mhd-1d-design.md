# Report 2 Week 1 (Week 12) — 1D Ideal-MHD Walking Skeleton: Design

**Date:** 2026-06-11
**Status:** Approved (brainstorming) → ready for writing-plans
**Scope week:** Master-schedule Week 12 (Report 2, first code week)
**Owner:** beren

---

## Context

Report 1 (Euler validation) is complete. The codebase is precision-generic and
`NVars`-templated at the core layer (`Grid2D<Real, NVars, Ptr>`), so it is
architecturally ready to host MHD without rearchitecting storage, indexing, IO,
or boundaries. `src/mhd/` exists but is empty; `tests/cases/orszag_tang/` and
`tests/cases/kelvin_helmholtz/` are empty placeholders; there is no
`brio_wu.cfg` and no `compute_divB_norms()`.

This spec covers **only** the first Report 2 code week: a correct, verifiable
**1D ideal-MHD pipeline**, validated against a self-converged double reference,
delivered without touching the Report-1-validated Euler binary.

### Decisions locked during brainstorming

| # | Decision | Choice |
|---|---|---|
| 1 | Week-1 deliverable scope | **1D walking skeleton** (defer GLM, 2D, HLLD) |
| 2 | MHD state layout | **9-var incl. psi from the start** (zero re-index when GLM lands) |
| 3 | Brio-Wu validation | **Self-converged high-res double reference** + L1/L2/Linf + eyeball vs published |
| 4 | Doc/dir convention | **`docs/week12/`** (continuous master-schedule numbering) |
| 5 | Executable integration | **Separate `hrsc_mhd` executable** (Euler binary/app layer untouched) |

### Key numerics rationale

- **Brio-Wu is 1D ⇒ `div(B) ≡ 0` by construction** (`Bx` constant), so GLM
  divergence cleaning is inactive in 1D. GLM only earns its keep in 2D
  (Orszag-Tang / KH), deferred to Weeks 13+. `compute_divB_norms` max staying at
  round-off is therefore a cheap correctness sentinel this week, not a cleaning
  test.
- The 9-var state carries `psi` now so that the Week-13 2D GLM **source step**
  activates without re-indexing state/flux/IO-header/tests/saved-binaries.

---

## Architecture

All new code is **additive**. The `hrsc` Euler binary and the `src/app/` layer
(which is hardcoded to `EulerNVars` / `FluxScheme` / `EulerSolver`) are not
modified. MHD is an isolated, independently testable unit; it will be folded into
a shared app layer in Week 14 alongside GPU MHD, once the physics is trusted.

### New files

```
src/mhd/
  mhd_state.hpp        # MhdNVars=9, index enum, cons<->prim, magnetic energy
  mhd_flux.hpp         # 1D x-flux: magnetic pressure + tension + psi transport
  hll.hpp              # 2-wave HLL with fast-magnetosonic wave speeds
  mhd_muscl.hpp        # MUSCL reconstruction generalized over MhdNVars
  mhd_hancock.hpp      # Hancock half-step predictor for MHD
  mhd_solver.hpp       # MhdSolver<Real> declaration (1D x-sweep)
  mhd_solver.cpp       # definitions + explicit float/double instantiation
src/mhd_main.cpp       # thin cfg-driven entry; reuses config/io/error_norms

tests/cases/brio_wu_1d/
  brio_wu.cfg          # Brio & Wu 1988 IC, N=800
  brio_wu_ref.cfg      # N=8000 double self-converged reference
  bw_tests.hpp         # IC setup (if a wrapper is needed for unit tests)
```

### Modified files

```
src/utils/error_norms.hpp   # add compute_divB_norms() (mean/max |dBx/dx|)
CMakeLists.txt              # add hrsc_mhd target behind existing flags
```

### Component responsibilities

- **`mhd_state.hpp`** — `constexpr int MhdNVars = 9`; index enum
  `(RHO, MX, MY, MZ, BX, BY, BZ, E, PSI)`. Primitive↔conserved conversion with
  total energy `E = p/(γ−1) + ½ρ|v|² + ½|B|²`. Reuses ideal-gas constants from
  `core/eos.hpp`. **Interface:** `cons_to_prim`, `prim_to_cons`,
  `pressure(cons)`. **Depends on:** `core/eos.hpp`, `core/vec.hpp`.
- **`mhd_flux.hpp`** — 1D x-direction physical flux. Magnetic pressure
  `p* = p + ½|B|²`; momentum flux includes `−Bx·B` tension; energy flux
  `(E + p*)u − Bx(v·B)`. psi terms (1D, hyperbolic transport only):
  `F[BX] = psi`, `F[PSI] = c_h²·Bx`. **Interface:** `flux_x(cons, ch) -> Vec`.
  **Depends on:** `mhd_state.hpp`.
- **`hll.hpp`** — HLL 2-wave solver. Fast-magnetosonic speed
  `c_f = sqrt( ½[ a² + b²/ρ + sqrt((a² + b²/ρ)² − 4 a² Bx²/ρ) ] )` with
  `a² = γp/ρ`, `b² = |B|²`. Davis wave-speed estimates
  `S_L = min(u_L − c_fL, u_R − c_fR)`, `S_R = max(u_R + c_fR, u_L + c_fL)`.
  Honors `RIEMANN_STRICT_INEQUALITY` for the `S==0` tie branch.
  **Interface:** `hll_flux(UL, UR, ch) -> Vec`. **Depends on:** `mhd_flux.hpp`.
- **`mhd_muscl.hpp` / `mhd_hancock.hpp`** — reconstruction + predictor
  generalized over `MhdNVars`; limiter math reused from the Euler equivalents.
- **`mhd_solver.{hpp,cpp}`** — `MhdSolver<Real>`: 1D x-sweep
  (reconstruct → predict → HLL flux → conservative update), CFL from fast speed.
  Split header/impl with explicit `float`/`double` instantiation, mirroring
  `EulerSolver`. **Depends on:** all of `src/mhd/`, `core/`, `utils/`.
- **`mhd_main.cpp`** — parses cfg, builds `Grid2D<Real, MhdNVars>`, runs solver,
  writes via `utils/io.hpp` (header already records `nvars=9`, so Python readers
  and `io_helper.py` work unchanged). ~100 lines, deliberately duplicating
  minimal Euler-main plumbing rather than refactoring the shared layer now.
- **`error_norms.hpp::compute_divB_norms()`** — mean and max of `|∂Bx/∂x|`
  (extensible to 2D `∂Bx/∂x + ∂By/∂y` later). In 1D the result is ~round-off;
  this is the correctness sentinel.

---

## Numerics correctness gates

- **Brio-Wu IC** (Brio & Wu 1988): `γ = 2`, domain `[0,1]`, discontinuity at
  `x = 0.5`. Left `(ρ, p, By) = (1, 1, 1)`, right `(0.125, 0.1, −1)`,
  `Bx = 0.75` (constant), `vx = vy = vz = 0`, `Bz = 0`, `t_end = 0.1`.
- **div(B) sentinel:** `compute_divB_norms` max must remain at round-off
  (1D ⇒ Bx constant ⇒ analytic 0). A nonzero value flags a flux-sign or
  indexing bug.
- **Expected structure:** the standard Brio-Wu 7-wave profile (fast rarefaction,
  compound wave, contact, slow shock, etc.) in `ρ`, `By`, `vx`.

---

## Build system

- Add a `hrsc_mhd` executable target to `CMakeLists.txt`, reusing the existing
  options: `FLOAT_PRECISION`, `OPT_LEVEL`, `FAST_MATH`,
  `RIEMANN_STRICT_INEQUALITY` (the `<` vs `<=` flag also governs HLL wave-speed
  tie handling, pre-wiring the Report 2 implementation-variation axis),
  `ENABLE_OPENMP`. No change to the `hrsc` target.
- Builds in both `build-double/` and `build-float/` via the existing recipe.

---

## Testing (TDD, bottom-up)

Matches house style: Catch2 unit suite + pytest + regression harness.

1. **Unit (Catch2):**
   - `mhd_state` cons↔prim round-trip (float + double tolerances).
   - `mhd_flux` against hand-computed values for a known state.
   - HLL consistency: identical L/R states ⇒ physical flux; `S_L = S_R` degenerate
     case handled.
   - `compute_divB_norms` on an analytic field (constant Bx ⇒ 0; linear Bx ⇒
     known slope).
2. **Integration:** Brio-Wu N=400 and N=800 complete in float + double; output
   shape and discontinuity count plausible.
3. **Validation:** N=8000 double **self-converged reference**; compute L1/L2/Linf
   of N=400/800 against it via the existing regression harness; confirm ~1st-order
   HLL convergence; eyeball `By/ρ/vx` vs the published Brio-Wu figure.

---

## Out of scope (named to prevent scope creep)

GLM source step · 2D sweeps and 2D boundary handling · Orszag-Tang / KH ·
HLLD 5-wave solver · GPU MHD · `run_matrix.py` / `build_matrix.py` MHD-awareness.
All deferred to Weeks 13–14 per `docs/requirement/overall.md`.

---

## Acceptance / milestone

- `hrsc_mhd` builds in float + double.
- All new Catch2 unit tests green.
- Brio-Wu N=800 matches the published profile; N=400/800 self-converge against
  the N=8000 double reference at ~1st order (HLL).
- `divB_max` at round-off for all Brio-Wu runs.
- **Euler regression suite still passes, untouched** (no edits to `hrsc` / `app/`).

---

## Deliverable docs

- `docs/week12/week12-plan.md` — checkbox implementation plan (produced by
  writing-plans from this spec).
- `docs/week12/week12-summary.md` — written at week close.
- INDEX per-week table extended with a Week 12 row.
