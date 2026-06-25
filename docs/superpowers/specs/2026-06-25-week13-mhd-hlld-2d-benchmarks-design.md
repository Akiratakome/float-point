# Week 13 — 2D MHD Benchmarks (HLL) + HLLD Solver Design

**Date:** 2026-06-25
**Branch base:** `week12-mhd-implementation` (Week 12 complete; see [week12-summary.md](../../week12/week12-summary.md))
**Requirement:** [overall.md](../../requirement/overall.md) §Week 13 — HLLD 5-wave solver (with HLL fallback), Orszag-Tang, Kelvin-Helmholtz.
**Coding guidance:** [coding guidance.md](../../requirement/coding%20guidance.md) — no magic numbers (named constants + source comment), project naming conventions, cfg-driven (no hardcoded params), comments explain *why*, modular, no committed build artifacts.

---

## 1. Goal & delivery split

Deliver **trustworthy 2D physical MHD benchmark validation on the proven HLL
solver**, and add **HLLD as a zero-cost, cfg-selectable alternative** that is
compared where it runs and recorded as a fallback decision if too risky. All
work is **additive**: the Report-1 Euler binary, the `src/app/` layer, and the
Week-12-validated 1D Brio-Wu path stay untouched and **bit-identical** (default
`riemann = hll`).

| Tier | Deliverable | Milestone protection |
|---|---|---|
| **Core** | Orszag-Tang (then Kelvin-Helmholtz) validated with HLL: self-converged double reference L1/L2/Linf + structural invariants. | Satisfies overall.md "2D physical benchmark" milestone *without* HLLD. |
| **Enhanced** | HLLD 5-wave solver, `riemann=hll\|hlld`; run OT/KH through HLLD and compare. | If HLLD is too buggy by week-end, ship the attempt + a documented fallback decision; the precision study proceeds on HLL. |

**Stop/fallback rule (overall.md):** the precision study (Report 2's 40%
"Computational Results") only needs a *correct* solver, not the *best* one. HLLD
is enhancement, never a blocker for the core deliverable.

---

## 2. Interfaces sustained from Week 12

These existing interfaces are preserved unchanged (consumers must not break):

- **Riemann solver signature:** `f(UL, UR, gamma, ch) → Vec<Real, MhdNVars>`
  (`MhdNVars = 9`, index enum `RHO,MX,MY,MZ,BX,BY,BZ,E,PSI`). HLL and HLLD both
  match this exactly; the y-sweep's `mhd_swap_xy` rotate-and-reuse means a solver
  only ever needs the **normal (x) flux**.
- **`RIEMANN_STRICT_INEQUALITY`** compile flag — strict `> / <` vs non-strict
  `>= / <=` wave-side tests (Report 2 implementation-variation axis). HLLD honors
  the same convention.
- **MUSCL-Hancock `predict_faces`** state-based face prediction and
  `mhd_swap_xy` / `mhd_swap_xy_prim` rotation pattern ([mhd_flux.hpp](../../../src/mhd/mhd_flux.hpp)).
- **cfg-driven case registry** ([mhd_config.hpp](../../../src/mhd/mhd_config.hpp)):
  `parse_mhd_test`, `parse_mhd_boundary`. New cases/solver extend this enum-parse
  pattern.
- **GLM subsystem:** `F[BX]=ψ`, `F[PSI]=ch²·Bx`, parabolic `glm_damp`
  ([glm.hpp](../../../src/mhd/glm.hpp)), ψ=0-outflow / periodic BCs. HLLD must be
  consistent with this 9-var GLM state.
- **Validation discipline:** generated cfgs, stdout/stderr, per-run metadata, and
  `summary.{csv,json,md}` scalar artefacts; binary grids stay transient/ignored
  (Week-12 `mhd_brio_wu_1d.py` / `mhd_2d_week12.py` pattern).

---

## 3. Component design

### 3.1 Functor-templated solver (the one refactor)

Wrap each Riemann solver in a stateless, default-constructible functor; the
free functions stay (unit tests call them directly):

```cpp
// src/mhd/hll.hpp  (mhd_hll_flux unchanged; add wrapper)
struct HllFlux {
    template <typename Real>
    HD_FUNC Vec<Real, MhdNVars> operator()(const Vec<Real, MhdNVars>& UL,
                                           const Vec<Real, MhdNVars>& UR,
                                           Real gamma, Real ch) const {
        return mhd_hll_flux(UL, UR, gamma, ch);
    }
};
// src/mhd/hlld.hpp  ->  HlldFlux wraps mhd_hlld_flux identically.
```

Parameterize the solver, defaulting to HLL so every existing call site and test
is bit-identical:

```cpp
template <typename Real, typename RiemannFlux = HllFlux>
class MhdSolver { ... };
```

- Sweeps call `RiemannFlux{}(lcr, rcl, m_gamma, ch)` in place of the hardcoded
  `mhd_hll_flux`. `x_sweep` / `y_sweep` bodies are otherwise unchanged; the
  `mhd_swap_xy` rotation is untouched.
- **Explicit instantiations grow 2 → 4:** `{float,double} × {HllFlux,HlldFlux}`
  in `mhd_solver.cpp`. Setup functions remain templated on `Real` only.
- **Runtime selection without virtuals:** factor the `mhd_main` body into
  `template<typename Flux> int run_mhd(const Config&, ...)` and dispatch once on
  the `riemann` cfg key:

```cpp
return (riemann == MhdRiemann::Hlld) ? run_mhd<HlldFlux>(cfg, ...)
                                     : run_mhd<HllFlux>(cfg, ...);
```

### 3.2 Case registry additions

`mhd_config.hpp`:
- `enum class MhdTestCase { BrioWu, DivbBlob, OrszagTang, KelvinHelmholtz };`
  + parse strings `"orszag_tang"`, `"kelvin_helmholtz"`.
- `enum class MhdRiemann { Hll, Hlld };` + `parse_mhd_riemann` (default `Hll`).

`mhd_solver.{hpp,cpp}`: add `setup_orszag_tang<Real>` and
`setup_kelvin_helmholtz<Real>` (explicit float/double instantiation, named
constants with a source comment).

### 3.3 Orszag-Tang IC — parameters pinned

Self-consistent rationalized units matching the solver's `ptot = p + 0.5·|B|²`
magnetic-pressure form (Tóth 2000; one normalization, not mixed):

| Quantity | Value |
|---|---|
| `gamma` | 5/3 |
| domain | `[0,1] × [0,1]`, doubly **periodic** |
| `rho` | `gamma*gamma` (= 25/9) |
| `p` | `gamma` (= 5/3) |
| `B0` | 1 |
| velocity | `vx = -sin(2*pi*y)`, `vy =  sin(2*pi*x)`, `vz = 0` |
| magnetic | `Bx = -B0*sin(2*pi*y)`, `By = B0*sin(4*pi*x)`, `Bz = 0` |
| `psi` | 0 |
| `cfl` | 0.4 |
| `glm_cr` | 0.18 (2D default) |
| `t_end` | 0.5 (milestone time; t=1.0 noted for richer turbulence) |

Constructed so `∇·B = 0` at `t=0` (∂Bx/∂x = ∂By/∂y = 0 for this field).

### 3.4 Kelvin-Helmholtz IC — parameters pinned

MHD KH has no single standard parameter set; this is a *reasonable benchmark*
(doubly-periodic double shear layer + flow-aligned B + small vy perturbation,
following periodic-shear-layer literature). All parameters pinned:

| Quantity | Value | Meaning |
|---|---|---|
| `gamma` | 5/3 | |
| domain | `[0,1] × [0,1]`, doubly **periodic** | square keeps symmetry checks clean (deviates from overall.md's indicative 256×512 single-interface sketch; noted) |
| `rho` | 1 (uniform) | |
| `p` | 1 (uniform) | high-β, weak field |
| `U0` | 0.5 | shear half-amplitude |
| shear profile | `vx = U0*(tanh((y-0.25)/a) - tanh((y-0.75)/a) - 1)` | +U0 mid-band, −U0 outside; two interfaces ⇒ periodic-compatible |
| `a` (shear_width) | 0.025 | |
| perturbation | `vy = delta*sin(2*pi*x)*(exp(-((y-0.25)/s)^2) + exp(-((y-0.75)/s)^2))` | seeds the instability symmetrically |
| `delta` (perturb_amp) | 0.01 | |
| `s` (perturb_width) | 0.05 | |
| `B0` | 0.1, flow-aligned `Bx=B0, By=Bz=0` | Alfvén Mach `M_A = U0/(B0/sqrt(rho)) = 5` (weak, does not suppress rollup) |
| `cfl` | 0.4 | |
| `glm_cr` | 0.18 | |
| `t_end` | 1.0 (vortex rollup; extendable) | |

### 3.5 HLLD solver (`src/mhd/hlld.hpp`)

`mhd_hlld_flux(UL, UR, gamma, ch)` — Miyoshi & Kusano (2005) 5-wave fan
(speeds `SL, SL*, SM, SR*, SR`; intermediate states `U*`, `U**`).

**GLM coupling (decoupled linear (Bx, ψ) 2-wave subsystem, solved exactly —
Dedner/Mignone):**

```
Bx*  = 0.5*(BxL + BxR) - 0.5*(psiR - psiL)/ch
psi* = 0.5*(psiL + psiR) - 0.5*ch*(BxR - BxL)

F[BX]  = psi*
F[PSI] = ch*ch * Bx*
```

The 5-wave fan then uses **`Bx*` as the constant normal field** in *all*
remaining components — momentum, energy, and transverse magnetic fluxes must use
`Bx*` consistently and must **not** mix the raw left/right `Bx`.

**Robustness & conventions:**
- Internal **HLL fallback** for degenerate states: `Bx*²/rho` below tolerance,
  vanishing `(SR-SL)` or intermediate denominators.
- Same `RIEMANN_STRICT_INEQUALITY` flag convention as HLL for wave-side tests.
- Named tolerance constant (no magic number).

---

## 4. Validation strategy (reference + symmetry)

Per-test driver under `scripts/regression/` (`mhd_orszag_tang_2d.py`,
`mhd_kh_2d.py`), reusing `io_helper.read_binary` and the Week-12 summary schema.

**Primary numeric gate — self-converged double reference:**
- Run candidate (256²) and a high-res double reference (512²), block-average the
  reference to the candidate grid, emit **L1/L2/Linf on density** into
  `summary.{csv,json,md}`. Same discipline as Brio-Wu.

**Structural / symmetry invariants (robust, always-correct gates):**
- **t=0 IC correctness** (unit test): fields match the analytic IC; `∇·B = 0` to
  round-off.
- **Conservation:** total mass exactly conserved on the periodic domain; total
  energy conserved to truncation level.
- **∇·B floor:** `divB_mean`/`divB_max` stay bounded and are reduced by GLM
  (`glm_cr=0.18` vs control `glm_cr=0`), reusing `compute_divB_norms`.
- **Symmetry diagnostic:** monitor the discrete point-symmetry residual of ρ
  about the domain centre (OT) / shear-reflection residual (KH); exact transform
  rules pinned during implementation from Tóth (2000). Reported, not a hard gate
  (nonlinear breakup eventually breaks it); the reference norms are the hard gate.

cfgs: `tests/cases/orszag_tang_2d/{orszag_tang.cfg, orszag_tang_ref.cfg}`,
`tests/cases/kelvin_helmholtz_2d/{kh.cfg, kh_ref.cfg}`.

---

## 5. Testing (TDD) & file structure

**New unit tests (auto-globbed Catch2, `tests/unit/`):**
- `test_mhd_hlld.cpp` — property-based (HLLD ≠ HLL in general; it is less
  diffusive):
  - identical L/R states → physical flux (`mhd_flux_x`);
  - degenerate/fallback states → agrees with `mhd_hll_flux`;
  - same-side supersonic waves → upwind physical flux;
  - finite / positive-pressure / conservative-consistency smoke;
  - short Brio-Wu / OT run produces no nonphysical state.
- `test_mhd_orszag_tang.cpp`, `test_mhd_kh.cpp` — IC correctness, `∇·B=0` at
  `t=0`, symmetry residual at `t=0`.
- Functor-templated-solver check: `MhdSolver<double, HllFlux>` reproduces the
  existing `MhdSolver<double>` Brio-Wu result bit-identically.

**Create:**
- `src/mhd/hlld.hpp`
- `tests/unit/test_mhd_hlld.cpp`, `test_mhd_orszag_tang.cpp`, `test_mhd_kh.cpp`
- `tests/cases/orszag_tang_2d/{orszag_tang.cfg, orszag_tang_ref.cfg}`
- `tests/cases/kelvin_helmholtz_2d/{kh.cfg, kh_ref.cfg}`
- `scripts/regression/mhd_orszag_tang_2d.py`, `scripts/regression/mhd_kh_2d.py`
- `docs/week13/week13-plan.md` (this design's implementation plan)

**Modify:**
- `src/mhd/hll.hpp` — add `HllFlux` functor.
- `src/mhd/mhd_solver.hpp/.cpp` — template on flux; add OT/KH setups; 4
  instantiations.
- `src/mhd/mhd_config.hpp` — `MhdTestCase` + `MhdRiemann` enums/parsers.
- `src/mhd_main.cpp` — `run_mhd<Flux>` dispatch; OT/KH case setup branch.
- `CMakeLists.txt` — headers are header-only (auto-included); confirm the 4
  `MhdSolver` instantiations compile; new test files auto-globbed.
- `docs/INDEX.md` — add Week 13 row.

**Generate (transient/ignored, not committed):** binary grids under
`experiments/week13/...`; only scalar `summary.*` + figures-if-any are kept.

---

## 6. Implementation order (dependency-respecting)

1. **Functor refactor** — `HllFlux` + `MhdSolver<Real, RiemannFlux=HllFlux>`;
   gate: full 33-case suite + Brio-Wu 759-step regression unchanged.
2. **Orszag-Tang case** — setup + cfg + reference/symmetry validation (HLL).
3. **Kelvin-Helmholtz case** — setup + cfg + validation (HLL). *Core complete.*
4. **HLLD solver** — `hlld.hpp` + GLM split + fallback; unit-validated; wired
   `riemann=hll|hlld`.
5. **HLLD on benchmarks + decision** — compare to HLL reference; record the
   Week-13 milestone decision (HLLD or HLL for the remainder).

---

## 7. References

- Miyoshi & Kusano (2005), *A multi-state HLL approximate Riemann solver for
  ideal MHD* — HLLD 5-wave fan.
- Dedner et al. (2002); Mignone & Tzeferacos / PLUTO GLM — GLM divergence
  cleaning and the exact (Bx, ψ) 2-wave split.
- Tóth (2000), *The ∇·B=0 Constraint in Shock-Capturing MHD Codes* — Orszag-Tang
  setup and symmetries.
- Brio & Wu (1988) — 1D MHD shock tube (Week 12 baseline, regression anchor).
- Periodic shear-layer MHD Kelvin-Helmholtz literature — KH benchmark precedent.
