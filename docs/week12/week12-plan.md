# Week 12 — 1D Ideal-MHD Walking Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a correct, verifiable 1D ideal-MHD pipeline (9-variable state incl. GLM `psi`, HLL Riemann solver, Brio-Wu shock tube) validated against a self-converged double reference, delivered as a separate `hrsc_mhd` executable that leaves the Report-1-validated Euler binary untouched.

**Architecture:** All MHD code is additive under `src/mhd/`. The core layer (`Grid2D<Real, NVars>`, `core/eos.hpp`, `core/boundary.hpp`, `core/vec.hpp`) and utilities (`utils/io.hpp`, `utils/config.hpp`, `utils/error_norms.hpp`) are reused unchanged except for one additive function (`compute_divB_norms`). MHD compiles into its own static lib + `hrsc_mhd` executable; the `hrsc` Euler target and the `src/app/` layer are not modified.

**Tech Stack:** C++17 templated-on-`Real` (float/double via `HRSC_REAL`), CMake/Ninja, Catch2 unit tests (`tests/unit/test_*.cpp`, auto-globbed), key=value cfg files, little-endian binary IO with a 64-byte header carrying `nvars`, Python regression harness for L1/L2/Linf.

**Reference specs:** Part 1 (1D) — [2026-06-11-report2-week12-mhd-1d-design.md](../superpowers/specs/2026-06-11-report2-week12-mhd-1d-design.md) · Part 2 (2D + GLM) — [2026-06-17-week12-2d-mhd-glm-design.md](../superpowers/specs/2026-06-17-week12-2d-mhd-glm-design.md)

> **STATUS (2026-06-17):** **Part 1 (Tasks 1–10) is COMPLETE and validated** — delivered in commits `b372e7b`→`1e91bcd`; see [week12-summary.md](week12-summary.md). The Part-1 checkboxes below are retained as the historical task record (left unchecked; do not re-run). **Part 2 (Tasks 11–19), appended at the end of this file, covers the remaining Week 12 2D machinery (Y-sweep + GLM cleaning + periodic/ψ BCs)** and is the active work.

**Structure:** Part 1 — 1D walking skeleton (Tasks 1–10, done). Part 2 — 2D MHD machinery + GLM (Tasks 11–19, active). Continuous task numbering across both parts.

---

## Physics reference (ideal MHD, source-free GLM-compatible 1D x-direction)

State (conserved), `MhdNVars = 9`, index enum order:
`U = (RHO, MX, MY, MZ, BX, BY, BZ, E, PSI)`, where `m = rho*v`.

Primitive recovery:
```
vx = mx/rho ; vy = my/rho ; vz = mz/rho
|v|^2 = vx^2 + vy^2 + vz^2 ; |B|^2 = Bx^2 + By^2 + Bz^2
p = (gamma - 1) * (E - 0.5*rho*|v|^2 - 0.5*|B|^2)
```

1D x-flux (GLM source-free flux; psi coupling in BX/PSI):
```
ptot = p + 0.5*|B|^2
vdotB = vx*Bx + vy*By + vz*Bz
F[RHO] = mx
F[MX]  = mx*vx + ptot - Bx*Bx
F[MY]  = mx*vy - Bx*By
F[MZ]  = mx*vz - Bx*Bz
F[BX]  = psi
F[BY]  = By*vx - Bx*vy
F[BZ]  = Bz*vx - Bx*vz
F[E]   = (E + ptot)*vx - Bx*vdotB
F[PSI] = ch*ch * Bx
```

Fast magnetosonic speed (x):
```
a2  = gamma*p/rho
ca2 = |B|^2 / rho
cax2 = Bx*Bx / rho
cf  = sqrt( 0.5 * ( (a2 + ca2) + sqrt( (a2+ca2)^2 - 4*a2*cax2 ) ) )
```

HLL flux (Davis estimates):
```
SL = min(vxL - cfL, vxR - cfR)
SR = max(vxR + cfR, vxL + cfL)
SL >= 0          -> F = FL
SR <= 0          -> F = FR
otherwise        -> F = (SR*FL - SL*FR + SL*SR*(UR - UL)) / (SR - SL)
```
`RIEMANN_STRICT_INEQUALITY` switches the `>= / <=` boundary tests to strict `> / <` (Report 2 implementation-variation axis; default OFF = non-strict).

Brio & Wu (1988) IC: `gamma = 2`, domain `[0,1]`, `x0 = 0.5`, `Bx = 0.75` everywhere, `t_end = 0.1`.
- Left  (`x < 0.5`): `rho=1.0, vx=vy=vz=0, By=1.0,  Bz=0, p=1.0`
- Right (`x >= 0.5`): `rho=0.125, vx=vy=vz=0, By=-1.0, Bz=0, p=0.1`

`ch` (GLM cleaning speed): per step, `ch = cfl * dx / dt` is **not** used; instead set `ch = max over cells of (|vx| + cf)` (the global fast speed), recomputed each step. In 1D Brio-Wu `psi` stays at round-off, so `ch` only needs to be finite and stable.

---

## File Structure

- Create: `src/mhd/mhd_state.hpp` — `MhdNVars`, index enum, `MhdPrim`, cons↔prim, `pressure`, `fast_speed_x`.
- Create: `src/mhd/mhd_flux.hpp` — `mhd_flux_x(U, ch)`.
- Create: `src/mhd/hll.hpp` — `mhd_hll_flux(UL, UR, ch)`.
- Create: `src/mhd/mhd_reconstruct.hpp` — minmod MUSCL slopes over `MhdNVars`; the Hancock half-step is implemented in the 1D solver for Week 12.
- Create: `src/mhd/mhd_solver.hpp` — `MhdSolver<Real>` declaration.
- Create: `src/mhd/mhd_solver.cpp` — definitions + explicit float/double instantiation.
- Create: `src/mhd_main.cpp` — cfg-driven entry for `hrsc_mhd`.
- Create: `tests/cases/brio_wu_1d/brio_wu.cfg` — N=800 production cfg.
- Create: `tests/cases/brio_wu_1d/brio_wu_ref.cfg` — N=8000 double reference cfg.
- Create: `tests/unit/test_mhd_state.cpp`, `test_mhd_flux.cpp`, `test_mhd_hll.cpp`, `test_divb.cpp`.
- Create: `scripts/regression/mhd_brio_wu_1d.py` — reference + L1/L2/Linf validation.
- Generate: `experiments/week12/brio_wu_1d/summary.{csv,json,md}` — scalar validation artefacts with per-run metadata.
- Modify: `src/utils/error_norms.hpp` — add `compute_divB_norms`.
- Modify: `CMakeLists.txt` — add `hrsc_mhd_lib` static lib + `hrsc_mhd` executable; link `unit_tests` to the lib.
- Modify: `docs/INDEX.md` — add Week 12 row.
- Create: `docs/week12/week12-summary.md` — written at week close (not in this plan's tasks).

---

## Task 1: MHD state (`mhd_state.hpp`)

**Files:**
- Create: `src/mhd/mhd_state.hpp`
- Test: `tests/unit/test_mhd_state.cpp`

- [ ] **Step 1: Write the failing test**

```cpp
// tests/unit/test_mhd_state.cpp
#include "catch.hpp"
#include "mhd/mhd_state.hpp"

using namespace hrsc;

TEST_CASE("MHD cons<->prim round-trips", "[mhd][state]") {
    const double gamma = 2.0;
    MhdPrim<double> w;
    w.rho = 1.3; w.vx = 0.4; w.vy = -0.2; w.vz = 0.1;
    w.Bx = 0.75; w.By = 0.9; w.Bz = -0.3; w.p = 1.1; w.psi = 0.0;

    Vec<double, MhdNVars> U = prim_to_cons(w, gamma);
    MhdPrim<double> w2 = cons_to_prim(U, gamma);

    REQUIRE(w2.rho == Approx(w.rho));
    REQUIRE(w2.vx  == Approx(w.vx));
    REQUIRE(w2.By  == Approx(w.By));
    REQUIRE(w2.p   == Approx(w.p));
}

TEST_CASE("MHD pressure subtracts kinetic and magnetic energy", "[mhd][state]") {
    const double gamma = 2.0;
    MhdPrim<double> w{};
    w.rho = 2.0; w.vx = 1.0; w.By = 2.0; w.p = 3.0;
    Vec<double, MhdNVars> U = prim_to_cons(w, gamma);
    // E = p/(g-1) + 0.5*rho*v^2 + 0.5*B^2 = 3 + 1 + 2 = 6
    REQUIRE(U[MhdIdx::E] == Approx(6.0));
    REQUIRE(pressure(U, gamma) == Approx(3.0));
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][state]"`
Expected: FAIL — `mhd/mhd_state.hpp` not found / `MhdPrim` undefined.

- [ ] **Step 3: Write minimal implementation**

```cpp
// src/mhd/mhd_state.hpp
#pragma once
#include "core/types.hpp"
#include "core/vec.hpp"
#include <cmath>
#include <algorithm>

namespace hrsc {

static constexpr int MhdNVars = 9;

struct MhdIdx {
    enum { RHO = 0, MX = 1, MY = 2, MZ = 3, BX = 4, BY = 5, BZ = 6, E = 7, PSI = 8 };
};

template <typename Real>
struct MhdPrim {
    Real rho, vx, vy, vz, Bx, By, Bz, p, psi;
};

template <typename Real>
HD_FUNC Vec<Real, MhdNVars> prim_to_cons(const MhdPrim<Real>& w, Real gamma) {
    Vec<Real, MhdNVars> U;
    const Real v2 = w.vx*w.vx + w.vy*w.vy + w.vz*w.vz;
    const Real B2 = w.Bx*w.Bx + w.By*w.By + w.Bz*w.Bz;
    U[MhdIdx::RHO] = w.rho;
    U[MhdIdx::MX]  = w.rho * w.vx;
    U[MhdIdx::MY]  = w.rho * w.vy;
    U[MhdIdx::MZ]  = w.rho * w.vz;
    U[MhdIdx::BX]  = w.Bx;
    U[MhdIdx::BY]  = w.By;
    U[MhdIdx::BZ]  = w.Bz;
    U[MhdIdx::E]   = w.p / (gamma - Real(1)) + Real(0.5) * w.rho * v2 + Real(0.5) * B2;
    U[MhdIdx::PSI] = w.psi;
    return U;
}

template <typename Real>
HD_FUNC Real pressure(const Vec<Real, MhdNVars>& U, Real gamma) {
    const Real rho = U[MhdIdx::RHO];
    const Real v2 = (U[MhdIdx::MX]*U[MhdIdx::MX]
                   + U[MhdIdx::MY]*U[MhdIdx::MY]
                   + U[MhdIdx::MZ]*U[MhdIdx::MZ]) / (rho * rho);
    const Real B2 = U[MhdIdx::BX]*U[MhdIdx::BX]
                  + U[MhdIdx::BY]*U[MhdIdx::BY]
                  + U[MhdIdx::BZ]*U[MhdIdx::BZ];
    return (gamma - Real(1)) * (U[MhdIdx::E] - Real(0.5)*rho*v2 - Real(0.5)*B2);
}

template <typename Real>
HD_FUNC MhdPrim<Real> cons_to_prim(const Vec<Real, MhdNVars>& U, Real gamma) {
    MhdPrim<Real> w;
    w.rho = U[MhdIdx::RHO];
    w.vx  = U[MhdIdx::MX] / w.rho;
    w.vy  = U[MhdIdx::MY] / w.rho;
    w.vz  = U[MhdIdx::MZ] / w.rho;
    w.Bx  = U[MhdIdx::BX];
    w.By  = U[MhdIdx::BY];
    w.Bz  = U[MhdIdx::BZ];
    w.psi = U[MhdIdx::PSI];
    w.p   = pressure(U, gamma);
    return w;
}

// Fast magnetosonic speed in x.
template <typename Real>
HD_FUNC Real fast_speed_x(const MhdPrim<Real>& w, Real gamma) {
    const Real B2 = w.Bx*w.Bx + w.By*w.By + w.Bz*w.Bz;
    const Real a2  = gamma * w.p / w.rho;
    const Real ca2 = B2 / w.rho;
    const Real cax2 = w.Bx*w.Bx / w.rho;
    Real disc = (a2 + ca2)*(a2 + ca2) - Real(4)*a2*cax2;
    disc = disc > Real(0) ? disc : Real(0);
    return std::sqrt(Real(0.5) * ((a2 + ca2) + std::sqrt(disc)));
}

} // namespace hrsc
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][state]"`
Expected: PASS (all assertions).

- [ ] **Step 5: Commit**

```bash
git add src/mhd/mhd_state.hpp tests/unit/test_mhd_state.cpp
git commit -m "feat(mhd): add 9-var MHD state with cons<->prim and fast speed"
```

---

## Task 2: MHD flux (`mhd_flux.hpp`)

**Files:**
- Create: `src/mhd/mhd_flux.hpp`
- Test: `tests/unit/test_mhd_flux.cpp`

- [ ] **Step 1: Write the failing test**

```cpp
// tests/unit/test_mhd_flux.cpp
#include "catch.hpp"
#include "mhd/mhd_flux.hpp"

using namespace hrsc;

TEST_CASE("MHD x-flux matches hand-computed values", "[mhd][flux]") {
    const double gamma = 2.0;
    MhdPrim<double> w{};
    w.rho = 1.0; w.vx = 2.0; w.vy = 0.0; w.vz = 0.0;
    w.Bx = 0.75; w.By = 1.0; w.Bz = 0.0; w.p = 1.0; w.psi = 0.0;
    Vec<double, MhdNVars> U = prim_to_cons(w, gamma);

    const double ch = 3.0;
    Vec<double, MhdNVars> F = mhd_flux_x(U, gamma, ch);

    // ptot = p + 0.5*B^2 = 1 + 0.5*(0.5625+1) = 1.78125
    const double ptot = 1.78125;
    REQUIRE(F[MhdIdx::RHO] == Approx(2.0));                 // mx
    REQUIRE(F[MhdIdx::MX]  == Approx(1.0*4.0 + ptot - 0.75*0.75)); // mx*vx+ptot-Bx^2
    REQUIRE(F[MhdIdx::BX]  == Approx(0.0));                 // psi
    REQUIRE(F[MhdIdx::BY]  == Approx(1.0*2.0 - 0.75*0.0));  // By*vx - Bx*vy
    REQUIRE(F[MhdIdx::PSI] == Approx(ch*ch*0.75));          // ch^2 * Bx
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][flux]"`
Expected: FAIL — `mhd_flux_x` undefined.

- [ ] **Step 3: Write minimal implementation**

```cpp
// src/mhd/mhd_flux.hpp
#pragma once
#include "mhd/mhd_state.hpp"

namespace hrsc {

template <typename Real>
HD_FUNC Vec<Real, MhdNVars> mhd_flux_x(const Vec<Real, MhdNVars>& U, Real gamma, Real ch) {
    const MhdPrim<Real> w = cons_to_prim(U, gamma);
    const Real B2 = w.Bx*w.Bx + w.By*w.By + w.Bz*w.Bz;
    const Real ptot = w.p + Real(0.5) * B2;
    const Real vdotB = w.vx*w.Bx + w.vy*w.By + w.vz*w.Bz;
    const Real mx = U[MhdIdx::MX];

    Vec<Real, MhdNVars> F;
    F[MhdIdx::RHO] = mx;
    F[MhdIdx::MX]  = mx*w.vx + ptot - w.Bx*w.Bx;
    F[MhdIdx::MY]  = mx*w.vy - w.Bx*w.By;
    F[MhdIdx::MZ]  = mx*w.vz - w.Bx*w.Bz;
    F[MhdIdx::BX]  = w.psi;
    F[MhdIdx::BY]  = w.By*w.vx - w.Bx*w.vy;
    F[MhdIdx::BZ]  = w.Bz*w.vx - w.Bx*w.vz;
    F[MhdIdx::E]   = (U[MhdIdx::E] + ptot)*w.vx - w.Bx*vdotB;
    F[MhdIdx::PSI] = ch*ch*w.Bx;
    return F;
}

} // namespace hrsc
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][flux]"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/mhd/mhd_flux.hpp tests/unit/test_mhd_flux.cpp
git commit -m "feat(mhd): add 1D GLM-coupled MHD x-flux"
```

---

## Task 3: HLL Riemann solver (`hll.hpp`)

**Files:**
- Create: `src/mhd/hll.hpp`
- Test: `tests/unit/test_mhd_hll.cpp`

- [ ] **Step 1: Write the failing test**

```cpp
// tests/unit/test_mhd_hll.cpp
#include "catch.hpp"
#include "mhd/hll.hpp"

using namespace hrsc;

TEST_CASE("HLL with identical states returns the physical flux", "[mhd][hll]") {
    const double gamma = 2.0;
    MhdPrim<double> w{};
    w.rho = 1.0; w.vx = 0.5; w.Bx = 0.75; w.By = 1.0; w.p = 1.0;
    Vec<double, MhdNVars> U = prim_to_cons(w, gamma);
    const double ch = 2.0;

    Vec<double, MhdNVars> Fhll = mhd_hll_flux(U, U, gamma, ch);
    Vec<double, MhdNVars> Fphys = mhd_flux_x(U, gamma, ch);
    for (int k = 0; k < MhdNVars; ++k)
        REQUIRE(Fhll[k] == Approx(Fphys[k]));
}

TEST_CASE("HLL is conservative (consistency)", "[mhd][hll]") {
    const double gamma = 2.0;
    MhdPrim<double> wl{}, wr{};
    wl.rho = 1.0;   wl.Bx = 0.75; wl.By = 1.0;  wl.p = 1.0;
    wr.rho = 0.125; wr.Bx = 0.75; wr.By = -1.0; wr.p = 0.1;
    Vec<double, MhdNVars> UL = prim_to_cons(wl, gamma);
    Vec<double, MhdNVars> UR = prim_to_cons(wr, gamma);
    const double ch = 3.0;
    // Bx flux component must equal psi on both sides (=0 here) -> 0.
    Vec<double, MhdNVars> F = mhd_hll_flux(UL, UR, gamma, ch);
    REQUIRE(F[MhdIdx::BX] == Approx(0.0));
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][hll]"`
Expected: FAIL — `mhd_hll_flux` undefined.

- [ ] **Step 3: Write minimal implementation**

```cpp
// src/mhd/hll.hpp
#pragma once
#include "mhd/mhd_flux.hpp"
#include <algorithm>

namespace hrsc {

template <typename Real>
HD_FUNC Vec<Real, MhdNVars> mhd_hll_flux(const Vec<Real, MhdNVars>& UL,
                                         const Vec<Real, MhdNVars>& UR,
                                         Real gamma, Real ch) {
    const MhdPrim<Real> wl = cons_to_prim(UL, gamma);
    const MhdPrim<Real> wr = cons_to_prim(UR, gamma);
    const Real cfl = fast_speed_x(wl, gamma);
    const Real cfr = fast_speed_x(wr, gamma);

    const Real SL = std::min(wl.vx - cfl, wr.vx - cfr);
    const Real SR = std::max(wr.vx + cfr, wl.vx + cfl);

    const Vec<Real, MhdNVars> FL = mhd_flux_x(UL, gamma, ch);
    const Vec<Real, MhdNVars> FR = mhd_flux_x(UR, gamma, ch);

#ifdef RIEMANN_STRICT_INEQUALITY
    if (SL > Real(0)) return FL;
    if (SR < Real(0)) return FR;
#else
    if (SL >= Real(0)) return FL;
    if (SR <= Real(0)) return FR;
#endif
    Vec<Real, MhdNVars> F;
    const Real inv = Real(1) / (SR - SL);
    for (int k = 0; k < MhdNVars; ++k)
        F[k] = (SR*FL[k] - SL*FR[k] + SL*SR*(UR[k] - UL[k])) * inv;
    return F;
}

} // namespace hrsc
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][hll]"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/mhd/hll.hpp tests/unit/test_mhd_hll.cpp
git commit -m "feat(mhd): add HLL 2-wave Riemann solver with strict-ineq flag"
```

---

## Task 4: `compute_divB_norms` (`error_norms.hpp`)

**Files:**
- Modify: `src/utils/error_norms.hpp`
- Test: `tests/unit/test_divb.cpp`

- [ ] **Step 1: Write the failing test**

```cpp
// tests/unit/test_divb.cpp
#include "catch.hpp"
#include "core/grid.hpp"
#include "mhd/mhd_state.hpp"
#include "utils/error_norms.hpp"

using namespace hrsc;

TEST_CASE("divB is zero for constant Bx (1D)", "[mhd][divb]") {
    Grid2D<double, MhdNVars> grid(8, 1);
    auto v = grid.view();
    for (int i = 0; i < 8; ++i) v(i, 0, MhdIdx::BX) = 0.75;
    DivBNorms<double> d = compute_divB_norms<double>(v, 8, 1, 0.1, 0.1);
    REQUIRE(d.mean == Approx(0.0).margin(1e-14));
    REQUIRE(d.max  == Approx(0.0).margin(1e-14));
}

TEST_CASE("divB picks up a linear Bx slope (1D)", "[mhd][divb]") {
    const double dx = 0.5;
    Grid2D<double, MhdNVars> grid(8, 1);
    auto v = grid.view();
    for (int i = 0; i < 8; ++i) v(i, 0, MhdIdx::BX) = 3.0 * (i * dx); // dBx/dx = 3
    DivBNorms<double> d = compute_divB_norms<double>(v, 8, 1, dx, dx);
    REQUIRE(d.max == Approx(3.0));
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][divb]"`
Expected: FAIL — `DivBNorms` / `compute_divB_norms` undefined.

- [ ] **Step 3: Write minimal implementation**

Append to `src/utils/error_norms.hpp` before the closing `} // namespace hrsc`:

```cpp
#include "core/grid.hpp"
#include "mhd/mhd_state.hpp"

namespace hrsc {

template <typename Real>
struct DivBNorms { Real mean, max; };

// Central-difference div(B). 1D uses dBx/dx; 2D adds dBy/dy.
// Interior cells only (skip first/last column/row so the stencil stays in-domain).
template <typename Real, typename Ptr>
DivBNorms<Real> compute_divB_norms(GridViewBase<Real, MhdNVars, Ptr> gv,
                                   int nx, int ny, Real dx, Real dy) {
    Real sum = Real(0), maxv = Real(0);
    long count = 0;
    const bool two_d = (ny > 1);
    for (int j = 0; j < ny; ++j) {
        for (int i = 1; i < nx - 1; ++i) {
            Real div = (gv(i+1, j, MhdIdx::BX) - gv(i-1, j, MhdIdx::BX)) / (Real(2)*dx);
            if (two_d && j > 0 && j < ny - 1)
                div += (gv(i, j+1, MhdIdx::BY) - gv(i, j-1, MhdIdx::BY)) / (Real(2)*dy);
            Real a = std::abs(div);
            sum += a;
            maxv = std::max(maxv, a);
            ++count;
        }
    }
    return { count ? sum / Real(count) : Real(0), maxv };
}

} // namespace hrsc
```

> Note: `error_norms.hpp` currently has no grid/mhd include. The new block adds them; keep the existing `compute_error` block above untouched. Do not duplicate the namespace — place the new `namespace hrsc { ... }` block after the existing one (two adjacent `namespace hrsc` blocks are legal and keep the diff small).

- [ ] **Step 4: Run test to verify it passes**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][divb]"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/utils/error_norms.hpp tests/unit/test_divb.cpp
git commit -m "feat(mhd): add compute_divB_norms (1D/2D central difference)"
```

---

## Task 5: MUSCL reconstruction (`mhd_reconstruct.hpp`)

**Files:**
- Create: `src/mhd/mhd_reconstruct.hpp`
- Test: covered indirectly by the solver integration (Task 6); add a minmod unit check here.
- Test: `tests/unit/test_mhd_state.cpp` (extend with a `[mhd][recon]` case)

- [ ] **Step 1: Write the failing test** (append to `tests/unit/test_mhd_state.cpp`)

```cpp
#include "mhd/mhd_reconstruct.hpp"

TEST_CASE("minmod returns zero across an extremum and the smaller slope otherwise", "[mhd][recon]") {
    REQUIRE(mhd_minmod(2.0, -1.0) == Approx(0.0));   // opposite signs
    REQUIRE(mhd_minmod(2.0, 3.0)  == Approx(2.0));   // same sign, pick smaller mag
    REQUIRE(mhd_minmod(-4.0, -1.0) == Approx(-1.0));
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][recon]"`
Expected: FAIL — `mhd_minmod` undefined.

- [ ] **Step 3: Write minimal implementation**

```cpp
// src/mhd/mhd_reconstruct.hpp
#pragma once
#include "mhd/mhd_state.hpp"

namespace hrsc {

template <typename Real>
HD_FUNC Real mhd_minmod(Real a, Real b) {
    if (a * b <= Real(0)) return Real(0);
    return (std::abs(a) < std::abs(b)) ? a : b;
}

// Component-wise minmod-limited slope for an MHD cell from its neighbours.
template <typename Real>
HD_FUNC Vec<Real, MhdNVars> mhd_slope(const Vec<Real, MhdNVars>& Um,
                                      const Vec<Real, MhdNVars>& U0,
                                      const Vec<Real, MhdNVars>& Up) {
    Vec<Real, MhdNVars> s;
    for (int k = 0; k < MhdNVars; ++k)
        s[k] = mhd_minmod(U0[k] - Um[k], Up[k] - U0[k]);
    return s;
}

} // namespace hrsc
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][recon]"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/mhd/mhd_reconstruct.hpp tests/unit/test_mhd_state.cpp
git commit -m "feat(mhd): add minmod slope reconstruction for MHD"
```

---

## Task 6: 1D MHD solver (`mhd_solver.{hpp,cpp}`) + CMake lib

**Files:**
- Create: `src/mhd/mhd_solver.hpp`
- Create: `src/mhd/mhd_solver.cpp`
- Modify: `CMakeLists.txt` (add `hrsc_mhd_lib`, link to `unit_tests`)
- Test: `tests/unit/test_mhd_solver.cpp`

- [ ] **Step 1: Write the failing test**

```cpp
// tests/unit/test_mhd_solver.cpp
#include "catch.hpp"
#include "mhd/mhd_solver.hpp"

using namespace hrsc;

TEST_CASE("MHD solver advances Brio-Wu without NaNs and keeps Bx≈const", "[mhd][solver]") {
    MhdSolver<double> solver(64, 1.0/64, 0.0, /*gamma=*/2.0, /*cfl=*/0.4, /*t_end=*/0.02);
    setup_brio_wu(solver.grid_view(), 64, 1.0/64, 0.0, 2.0, 0.5);
    solver.run();
    auto gv = solver.grid_view();
    for (int i = 0; i < 64; ++i) {
        REQUIRE(std::isfinite(gv(i, 0, MhdIdx::RHO)));
        REQUIRE(gv(i, 0, MhdIdx::BX) == Approx(0.75).margin(1e-10));
    }
    REQUIRE(solver.time() == Approx(0.02));
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][solver]"`
Expected: FAIL — `MhdSolver` / `setup_brio_wu` undefined.

- [ ] **Step 3: Write minimal implementation — header**

```cpp
// src/mhd/mhd_solver.hpp
#pragma once
#include "core/types.hpp"
#include "core/grid.hpp"
#include "core/boundary.hpp"
#include "mhd/hll.hpp"
#include "mhd/mhd_reconstruct.hpp"

namespace hrsc {

// Brio-Wu IC writer (declared here, used by tests and mhd_main).
template <typename Real>
void setup_brio_wu(GridView<Real, MhdNVars> gv, int nx, Real dx, Real xmin, Real gamma, Real x0);

template <typename Real>
class MhdSolver {
    Grid2D<Real, MhdNVars> m_grid;
    Real m_xmin, m_dx, m_gamma, m_cfl;
    TimeReal m_t_end, m_time;
    int m_step;
    BoundaryType m_bc_x;

    void apply_bc();
    Real compute_ch() const;        // global max(|vx|+cf)
public:
    MhdSolver(int nx, Real dx, Real xmin, Real gamma, Real cfl, TimeReal t_end,
              BoundaryType bc_x = BoundaryType::Outflow);
    GridView<Real, MhdNVars> grid_view() { return m_grid.view(); }
    TimeReal time() const { return m_time; }
    int step_count() const { return m_step; }
    Real dx() const { return m_dx; }
    Real xmin() const { return m_xmin; }
    Real gamma() const { return m_gamma; }
    TimeReal compute_dt(Real ch) const;
    void step();
    void run();
};

} // namespace hrsc
```

- [ ] **Step 4: Write minimal implementation — source**

```cpp
// src/mhd/mhd_solver.cpp
#include "mhd/mhd_solver.hpp"
#include <algorithm>
#include <cmath>
#include <vector>

namespace hrsc {

template <typename Real>
void setup_brio_wu(GridView<Real, MhdNVars> gv, int nx, Real dx, Real xmin, Real gamma, Real x0) {
    for (int i = 0; i < nx; ++i) {
        const Real x = xmin + (Real(i) + Real(0.5)) * dx;
        MhdPrim<Real> w{};
        w.Bx = Real(0.75); w.vx = w.vy = w.vz = Real(0); w.Bz = Real(0); w.psi = Real(0);
        if (x < x0) { w.rho = Real(1);     w.By = Real(1);  w.p = Real(1);   }
        else        { w.rho = Real(0.125); w.By = Real(-1); w.p = Real(0.1); }
        Vec<Real, MhdNVars> U = prim_to_cons(w, gamma);
        for (int k = 0; k < MhdNVars; ++k) gv(i, 0, k) = U[k];
    }
}

template <typename Real>
MhdSolver<Real>::MhdSolver(int nx, Real dx, Real xmin, Real gamma, Real cfl,
                           TimeReal t_end, BoundaryType bc_x)
    : m_grid(nx, 1), m_xmin(xmin), m_dx(dx), m_gamma(gamma), m_cfl(cfl),
      m_t_end(t_end), m_time(0), m_step(0), m_bc_x(bc_x) {
    m_grid.dx = dx;
    m_grid.dy = dx;
}

template <typename Real>
void MhdSolver<Real>::apply_bc() {
    auto v = m_grid.view();
    // core/boundary.hpp exposes per-type helpers (no generic dispatcher).
    // Brio-Wu uses outflow; other BC types are deferred to Week 13 (2D).
    apply_outflow_bc(v, Axis::X);
}

template <typename Real>
Real MhdSolver<Real>::compute_ch() const {
    auto v = m_grid.view();
    Real ch = Real(0);
    for (int i = 0; i < m_grid.nx; ++i) {
        Vec<Real, MhdNVars> U; for (int k=0;k<MhdNVars;++k) U[k]=v(i,0,k);
        MhdPrim<Real> w = cons_to_prim(U, m_gamma);
        ch = std::max(ch, std::abs(w.vx) + fast_speed_x(w, m_gamma));
    }
    return ch;
}

template <typename Real>
TimeReal MhdSolver<Real>::compute_dt(Real ch) const {
    TimeReal dt = m_cfl * m_dx / std::max(ch, Real(1e-30));
    if (m_time + dt > m_t_end) dt = m_t_end - m_time;
    return dt;
}

template <typename Real>
void MhdSolver<Real>::step() {
    apply_bc();
    const Real ch = compute_ch();
    const TimeReal dt = compute_dt(ch);
    const int nx = m_grid.nx;
    auto v = m_grid.view();

    auto getU = [&](int i){ Vec<Real,MhdNVars> U; for(int k=0;k<MhdNVars;++k) U[k]=v(i,0,k); return U; };

    // MUSCL-Hancock: limited slopes, half-step predictor, HLL at interfaces.
    std::vector<Vec<Real,MhdNVars>> UL(nx+1), UR(nx+1);
    for (int i = 0; i < nx; ++i) {
        Vec<Real,MhdNVars> s = mhd_slope(getU(i-1), getU(i), getU(i+1));
        Vec<Real,MhdNVars> U0 = getU(i);
        // Hancock half-step using flux of edge-extrapolated states.
        Vec<Real,MhdNVars> Ulo, Uhi;
        for (int k=0;k<MhdNVars;++k){ Ulo[k]=U0[k]-Real(0.5)*s[k]; Uhi[k]=U0[k]+Real(0.5)*s[k]; }
        Vec<Real,MhdNVars> Fl = mhd_flux_x(Ulo, m_gamma, ch);
        Vec<Real,MhdNVars> Fh = mhd_flux_x(Uhi, m_gamma, ch);
        Vec<Real,MhdNVars> half;
        const Real fac = Real(0.5)*Real(dt)/m_dx;
        for (int k=0;k<MhdNVars;++k){ Real d=fac*(Fh[k]-Fl[k]); Ulo[k]-=d; Uhi[k]-=d; }
        UR[i]   = Ulo;   // right interface of cell i-1 uses left face value... see indexing below
        UL[i+1] = Uhi;   // left  interface of cell i+1
    }

    // Interface flux F[i] between cell i-1 (UL[i]) and cell i (UR[i]).
    std::vector<Vec<Real,MhdNVars>> Fiface(nx+1);
    for (int i = 1; i < nx; ++i)
        Fiface[i] = mhd_hll_flux(UL[i], UR[i], m_gamma, ch);
    // Domain-edge fluxes from ghost-extrapolated cell values (outflow).
    Fiface[0]  = mhd_flux_x(getU(0),   m_gamma, ch);
    Fiface[nx] = mhd_flux_x(getU(nx-1),m_gamma, ch);

    for (int i = 0; i < nx; ++i)
        for (int k = 0; k < MhdNVars; ++k)
            v(i,0,k) -= Real(dt)/m_dx * (Fiface[i+1][k] - Fiface[i][k]);

    m_time += dt;
    ++m_step;
}

template <typename Real>
void MhdSolver<Real>::run() {
    while (m_time < m_t_end - TimeReal(1e-15)) step();
}

// Explicit instantiation (mirrors euler_solver.cpp).
template class MhdSolver<float>;
template class MhdSolver<double>;
template void setup_brio_wu<float>(GridView<float, MhdNVars>, int, float, float, float, float);
template void setup_brio_wu<double>(GridView<double, MhdNVars>, int, double, double, double, double);

} // namespace hrsc
```

> **Implementer note on interface indexing:** the `UL[i]`/`UR[i]` arrays must hold the *left* and *right* reconstructed states at interface `i` (between cells `i-1` and `i`). Verify the half-step block produces `UR[i] =` cell-`i` left face and `UL[i] =` cell-`(i-1)` right face before wiring; adjust the two assignment lines if the integration test in Step 2 shows asymmetric drift. The HLL consistency test (Task 3) guarantees the flux is correct given correct L/R, so any Brio-Wu asymmetry is an indexing bug here, not in the solver.

- [ ] **Step 5: Wire CMake**

In `CMakeLists.txt`, after the `hrsc_euler` library block (around line 86-87), add:

```cmake
add_library(hrsc_mhd_lib STATIC src/mhd/mhd_solver.cpp)
target_link_libraries(hrsc_mhd_lib PUBLIC hrsc_core)
```

And extend the `unit_tests` link line (line 103) to include the MHD lib:

```cmake
target_link_libraries(unit_tests PRIVATE hrsc_core hrsc_euler hrsc_app hrsc_mhd_lib)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cmake -B build-double -G Ninja -DFLOAT_PRECISION=double && cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][solver]"`
Expected: PASS — finite, `Bx≈0.75`, `time≈0.02`.

- [ ] **Step 7: Commit**

```bash
git add src/mhd/mhd_solver.hpp src/mhd/mhd_solver.cpp tests/unit/test_mhd_solver.cpp CMakeLists.txt
git commit -m "feat(mhd): add 1D MUSCL-Hancock HLL MHD solver + Brio-Wu IC"
```

---

## Task 7: `hrsc_mhd` executable (`mhd_main.cpp`)

**Files:**
- Create: `src/mhd_main.cpp`
- Modify: `CMakeLists.txt` (add `hrsc_mhd` executable)

- [ ] **Step 1: Write the implementation**

```cpp
// src/mhd_main.cpp
#include "utils/config.hpp"
#include "utils/error_norms.hpp"
#include "utils/io.hpp"
#include "mhd/mhd_solver.hpp"

#include <cstdio>
#include <string>

#ifndef HRSC_REAL
#define HRSC_REAL double
#endif
using Real = HRSC_REAL;

int main(int argc, char** argv) {
    if (argc < 2) { std::fprintf(stderr, "usage: hrsc_mhd <cfg>\n"); return 1; }
    hrsc::Config cfg(argv[1]);

    const int    nx    = cfg.get_int("nx", 800);
    const double xmin  = cfg.get_double("xmin", 0.0);
    const double xmax  = cfg.get_double("xmax", 1.0);
    const double gamma = cfg.get_double("gamma", 2.0);
    const double cfl   = cfg.get_double("cfl", 0.4);
    const double t_end = cfg.get_double("t_end", 0.1);
    const double x0    = cfg.get_double("x0", 0.5);
    const std::string out = cfg.get_string("output_file", "");

    const Real dx = static_cast<Real>((xmax - xmin) / nx);
    hrsc::MhdSolver<Real> solver(nx, dx, static_cast<Real>(xmin),
                                 static_cast<Real>(gamma), static_cast<Real>(cfl), t_end);
    hrsc::setup_brio_wu<Real>(solver.grid_view(), nx, dx, static_cast<Real>(xmin),
                              static_cast<Real>(gamma), static_cast<Real>(x0));
    solver.run();

    auto gv = solver.grid_view();
    hrsc::DivBNorms<Real> db = hrsc::compute_divB_norms<Real>(gv, nx, 1, dx, dx);
    std::fprintf(stderr, "[mhd] t=%.6f steps=%d divB_mean=%.3e divB_max=%.3e\n",
                 solver.time(), solver.step_count(), (double)db.mean, (double)db.max);

    if (!out.empty())
        hrsc::write_binary<Real, hrsc::MhdNVars>(out, gv, nx, 1, dx, dx, (Real)solver.time());
    return 0;
}
```

- [ ] **Step 2: Wire CMake**

In `CMakeLists.txt`, after the `hrsc` executable block (around line 97-98), add:

```cmake
add_executable(hrsc_mhd src/mhd_main.cpp)
target_link_libraries(hrsc_mhd PRIVATE hrsc_core hrsc_mhd_lib)
```

- [ ] **Step 3: Build both precisions**

Run:
```bash
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double && cmake --build build-double --target hrsc_mhd
cmake -B build-float  -G Ninja -DFLOAT_PRECISION=float  && cmake --build build-float  --target hrsc_mhd
```
Expected: both link an `hrsc_mhd` binary with no errors.

- [ ] **Step 4: Commit**

```bash
git add src/mhd_main.cpp CMakeLists.txt
git commit -m "feat(mhd): add hrsc_mhd executable (cfg-driven 1D Brio-Wu)"
```

---

## Task 8: Brio-Wu cfgs

**Files:**
- Create: `tests/cases/brio_wu_1d/brio_wu.cfg`
- Create: `tests/cases/brio_wu_1d/brio_wu_ref.cfg`

- [ ] **Step 1: Write production cfg**

```ini
# tests/cases/brio_wu_1d/brio_wu.cfg
# Brio & Wu (1988) 1D MHD shock tube. gamma=2, Bx=0.75, t_end=0.1.
test    = brio_wu
nx      = 800
xmin    = 0.0
xmax    = 1.0
x0      = 0.5
gamma   = 2.0
cfl     = 0.4
t_end   = 0.1
bc      = outflow
```

- [ ] **Step 2: Write reference cfg**

```ini
# tests/cases/brio_wu_1d/brio_wu_ref.cfg
# Self-converged double reference for Brio-Wu (high resolution).
test    = brio_wu
nx      = 8000
xmin    = 0.0
xmax    = 1.0
x0      = 0.5
gamma   = 2.0
cfl     = 0.4
t_end   = 0.1
bc      = outflow
```

- [ ] **Step 3: Smoke-run both precision builds**

Run:
```bash
./build-double/hrsc_mhd tests/cases/brio_wu_1d/brio_wu.cfg
./build-float/hrsc_mhd tests/cases/brio_wu_1d/brio_wu.cfg
```
Expected: both runs print stderr line `[mhd] t=0.100000 steps=... divB_mean=... divB_max=<round-off>`. The float run may have a looser round-off floor than double, but `Bx` should remain effectively constant.

- [ ] **Step 4: Commit**

```bash
git add tests/cases/brio_wu_1d/brio_wu.cfg tests/cases/brio_wu_1d/brio_wu_ref.cfg
git commit -m "test(mhd): add Brio-Wu production and reference cfgs"
```

---

## Task 9: Validation — self-converged reference + L1/L2/Linf

**Files:**
- Create: `scripts/regression/mhd_brio_wu_1d.py`

- [ ] **Step 1: Write the validation script**

```python
# scripts/regression/mhd_brio_wu_1d.py
"""Brio-Wu 1D MHD validation: run candidate resolutions + an 8000-cell double
reference, downsample the reference, and write L1/L2/Linf summaries on density.

This is a 1D-only Week 12 validation driver. It intentionally does not extend
run_matrix.py yet; instead it preserves the same harness discipline locally:
generated cfgs, stdout/stderr, per-run metadata, and summary.{csv,json,md}.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import pathlib
from datetime import datetime, timezone

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from io_helper import read_binary

ROOT = pathlib.Path(__file__).resolve().parents[2]
BIN = ROOT / "build-double" / "hrsc_mhd"
BASE_CFG = ROOT / "tests/cases/brio_wu_1d/brio_wu.cfg"
OUT = ROOT / "experiments/week12/brio_wu_1d"
OUT.mkdir(parents=True, exist_ok=True)
RHO = 0

def replace_or_append_cfg(text: str, key: str, value: str) -> str:
    out = []
    replaced = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or "=" not in line:
            out.append(line)
            continue
        lhs = line.split("=", 1)[0].strip()
        if lhs == key:
            out.append(f"{key} = {value}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"{key} = {value}")
    return "\n".join(out) + "\n"

def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"

def run_resolution(nx: int) -> np.ndarray:
    run_dir = OUT / f"runs/bw_{nx}_double"
    run_dir.mkdir(parents=True, exist_ok=True)
    out = OUT / f"bw_{nx}.bin"
    cfg_text = BASE_CFG.read_text(encoding="utf-8")
    cfg_text = replace_or_append_cfg(cfg_text, "nx", str(nx))
    cfg_text = replace_or_append_cfg(cfg_text, "output_file", str(out))
    cfg_path = run_dir / "config.cfg"
    cfg_path.write_text(cfg_text, encoding="utf-8")

    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    command = [str(BIN), str(cfg_path)]
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
        result = subprocess.run(command, cwd=str(ROOT), stdout=stdout, stderr=stderr, check=False)

    metadata = {
        "experiment": "week12-brio-wu-1d",
        "name": f"bw-{nx}-double",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(),
        "binary": str(BIN),
        "source_config": str(BASE_CFG),
        "run_config": str(cfg_path),
        "precision": "double",
        "build": "build-double",
        "nx": nx,
        "raw_output": str(out),
        "command": command,
        "returncode": result.returncode,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
    }
    (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"run failed for nx={nx}; see {stderr_path}")

    meta, arr = read_binary(str(out))     # arr shape [ny, nx, nvars]
    if meta.nvars != 9:
        raise RuntimeError(f"expected MHD nvars=9 in {out}, got {meta.nvars}")
    return arr[0, :, RHO]

def main() -> None:
    ref_nx = 8000
    ref = run_resolution(ref_nx)
    rows = []
    for nx in (200, 400, 800):
        rho = run_resolution(nx)
        factor = ref_nx // nx
        refd = ref.reshape(nx, factor).mean(axis=1)
        diff = np.abs(rho - refd)
        dx = 1.0 / nx
        rows.append({
            "nx": nx,
            "reference_nx": ref_nx,
            "L1": float(diff.sum() * dx),
            "L2": float(np.sqrt((diff**2).sum() * dx)),
            "Linf": float(diff.max()),
        })

    with (OUT / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["nx", "reference_nx", "L1", "L2", "Linf"])
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "summary.json").write_text(json.dumps({"rows": rows}, indent=2) + "\n", encoding="utf-8")

    md = ["# Week 12 Brio-Wu 1D Validation", "", "| N | reference N | L1(rho) | L2(rho) | Linf(rho) |", "|---:|---:|---:|---:|---:|"]
    for r in rows:
        md.append(f"| {r['nx']} | {r['reference_nx']} | {r['L1']:.6e} | {r['L2']:.6e} | {r['Linf']:.6e} |")
    md.append("")
    md.append("Generated cfgs, stdout/stderr, and per-run metadata live under `experiments/week12/brio_wu_1d/runs/`.")
    (OUT / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the validation**

Run: `python scripts/regression/mhd_brio_wu_1d.py`
Expected: `summary.csv`, `summary.json`, and `summary.md` are written under `experiments/week12/brio_wu_1d/`; rows N=200/400/800 show monotonically decreasing L1/L2 (≈1st-order HLL: roughly halving L1 as N doubles), and each run has generated cfg/stdout/stderr/metadata.

- [ ] **Step 3: Commit**

```bash
git add scripts/regression/mhd_brio_wu_1d.py
git commit -m "test(mhd): add Brio-Wu self-converged L1/L2/Linf validation"
```

---

## Task 10: divB sentinel + Euler-regression-green + docs

**Files:**
- Modify: `docs/INDEX.md`
- Create: `docs/week12/week12-summary.md`

- [ ] **Step 1: Confirm Euler regression is untouched and green**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests -r compact`
Expected: PASS — all pre-existing Euler/boundary/app cases plus the new `[mhd]` cases; no Euler case count regressions.

- [ ] **Step 2: Confirm divB sentinel on real Brio-Wu run**

Run: `./build-double/hrsc_mhd tests/cases/brio_wu_1d/brio_wu.cfg`
Expected: `divB_max` ≤ ~1e-12 (round-off; 1D Bx constant).

- [ ] **Step 3: Add Week 12 row to INDEX**

In `docs/INDEX.md` §2 per-week table, add after the Week 7 row:

```markdown
| 12 | [week12-plan.md](week12/week12-plan.md) | [week12-summary.md](week12/week12-summary.md) | (none) |
```

And under "Report 1 closeout / Report 2 transition", note that Week 12 delivers the 1D MHD walking skeleton.

- [ ] **Step 4: Write the week summary**

Create `docs/week12/week12-summary.md` capturing: delivered files, Brio-Wu L1/L2/Linf table, divB_max value, the indexing decision in Task 6, and a short "not attempted in Part 1" list (2D / GLM cleaning / HLLD / GPU / full run-matrix integration). The 2D machinery is now covered by Part 2 (Tasks 11–19) below.

- [ ] **Step 5: Commit**

```bash
git add docs/INDEX.md docs/week12/week12-summary.md
git commit -m "docs(mhd): record Week 12 1D MHD walking skeleton"
```

---

## Self-Review (writing-plans)

- **Spec coverage:** state (T1) · flux incl. psi (T2) · HLL + strict-ineq flag (T3) · compute_divB_norms (T4) · MUSCL-Hancock (T5–T6) · MhdSolver float/double instantiation (T6) · hrsc_mhd executable, Euler untouched (T7) · Brio-Wu cfgs (T8) · self-converged double reference + L1/L2/Linf (T9) · divB sentinel + Euler-green + docs (T10). All spec sections mapped.
- **Out-of-scope** (GLM source step, 2D, Orszag-Tang/KH, HLLD, GPU MHD, run_matrix MHD-awareness) intentionally absent from this plan. After the 1D Brio-Wu pipeline is green, start a separate follow-up plan only if time remains.
- **Type consistency:** `MhdNVars`, `MhdIdx`, `MhdPrim`, `prim_to_cons`/`cons_to_prim`/`pressure`/`fast_speed_x`, `mhd_flux_x`, `mhd_hll_flux`, `mhd_minmod`/`mhd_slope`, `DivBNorms`/`compute_divB_norms`, `MhdSolver`/`setup_brio_wu` used identically across tasks.
- **Known risk flagged:** interface L/R indexing in Task 6 Step 4 (implementer note) — the HLL consistency test isolates indexing from flux correctness.
- **Reuse points (API confirmed against source):** `core/boundary.hpp` exposes per-type helpers `apply_outflow_bc(view, Axis)` / `apply_periodic_bc` / `apply_reflective_bc` (no generic dispatcher) — Task 6 calls `apply_outflow_bc` directly. `GridView`/`Grid2D` expose `nx`/`ny` as **fields** (e.g. `m_grid.nx`, `grid.nx`), not methods. `utils/io.hpp` `write_binary<Real,NVars>(file, view, nx, ny, dx, dy, time)`; `utils/config.hpp` `Config` with `get_int/get_double/get_string`; `scripts/io_helper.py` `read_binary`. `MhdNVars` mirrors `EulerNVars=4` (`src/core/eos.hpp:22`).

---

# Part 2 — 2D MHD Machinery + GLM Cleaning (Tasks 11–19, ACTIVE)

> **Reference spec:** [2026-06-17-week12-2d-mhd-glm-design.md](../superpowers/specs/2026-06-17-week12-2d-mhd-glm-design.md). Completes overall.md's Week 12 2D items deferred by Part 1.

**Goal:** Extend the validated 1D `MhdSolver` in place to unified 1D/2D — rotate-and-reuse Y-sweep, canonical Dedner GLM (flux coupling untouched + analytic parabolic damping, full-grid div(B) as diagnostic), 9-var periodic BC + ψ=0-ghost rule for outflow — validated by a 2D Brio-Wu regression and a div(B)-cleaning decay test. 1D Brio-Wu must stay **bit-identical**.

**Key constraints (verified against source):**

- The solver is currently hardwired to `j=0`: `load_cell`/`store_cell` use `gv(i, 0, k)` (`src/mhd/mhd_solver.cpp:17,25`) and `predict_faces` reads the grid directly. Task 13 refactors `predict_faces` to be **state-based** (operate on three passed-in cell states) so x- and y-sweeps both reuse it.
- Existing 1D ctor `MhdSolver(nx, dx, xmin, gamma, cfl, t_end, bc_x=Outflow)` and `m_grid(nx, 1)` (`mhd_solver.cpp:115-117`) must be preserved; Task 14 adds a 2D ctor and makes the 1D ctor delegate with `ny=1, glm_cr=0` (no damping → bit-identical).
- Euler y-sweep precedent: rotate with `swap_momentum`, reuse x-flux, rotate back (`src/euler/euler_solver.cpp:258-264`). MHD swap must rotate **both** momentum and B.
- `Grid2D`/`GridView` expose `dx, dy` fields (`src/core/grid.hpp:14,45`); `view()` captures them by value (set `m_grid.dx/dy` before `view()`).
- `apply_periodic_bc(view, Axis)` / `apply_outflow_bc(view, Axis)` are `NVars`-generic (`src/core/boundary.hpp`).

---

## Task 11: `mhd_swap_xy` rotation (`mhd_flux.hpp`)

**Files:**
- Modify: `src/mhd/mhd_flux.hpp`
- Test: `tests/unit/test_mhd_swap.cpp`

- [ ] **Step 1: Write the failing test**

```cpp
// tests/unit/test_mhd_swap.cpp
#include "catch.hpp"
#include "mhd/mhd_flux.hpp"

using namespace hrsc;

TEST_CASE("mhd_swap_xy swaps MX<->MY and BX<->BY and is self-inverse", "[mhd][swap]") {
    Vec<double, MhdNVars> U;
    for (int k = 0; k < MhdNVars; ++k) U[k] = double(k + 1); // distinct values
    Vec<double, MhdNVars> S = mhd_swap_xy(U);
    REQUIRE(S[MhdIdx::MX] == Approx(U[MhdIdx::MY]));
    REQUIRE(S[MhdIdx::MY] == Approx(U[MhdIdx::MX]));
    REQUIRE(S[MhdIdx::BX] == Approx(U[MhdIdx::BY]));
    REQUIRE(S[MhdIdx::BY] == Approx(U[MhdIdx::BX]));
    REQUIRE(S[MhdIdx::MZ] == Approx(U[MhdIdx::MZ]));
    REQUIRE(S[MhdIdx::BZ] == Approx(U[MhdIdx::BZ]));
    REQUIRE(S[MhdIdx::E]  == Approx(U[MhdIdx::E]));
    REQUIRE(S[MhdIdx::PSI]== Approx(U[MhdIdx::PSI]));
    Vec<double, MhdNVars> back = mhd_swap_xy(S);
    for (int k = 0; k < MhdNVars; ++k) REQUIRE(back[k] == Approx(U[k]));
}

TEST_CASE("rotated x-flux equals the y-physical-flux", "[mhd][swap]") {
    const double gamma = 2.0, ch = 3.0;
    MhdPrim<double> w{};
    w.rho = 1.0; w.vx = 0.3; w.vy = -0.4; w.vz = 0.1;
    w.Bx = 0.75; w.By = 0.9; w.Bz = 0.2; w.p = 1.0;
    Vec<double, MhdNVars> U = prim_to_cons(w, gamma);
    // y-flux via rotation: swap -> x-flux -> swap back
    Vec<double, MhdNVars> Fy = mhd_swap_xy(mhd_flux_x(mhd_swap_xy(U), gamma, ch));
    // hand-check the mass flux component equals rho*vy
    REQUIRE(Fy[MhdIdx::RHO] == Approx(w.rho * w.vy));
    // normal-momentum (MY) flux carries the magnetic pressure - By^2 in y
    const double B2 = w.Bx*w.Bx + w.By*w.By + w.Bz*w.Bz;
    const double ptot = w.p + 0.5*B2;
    REQUIRE(Fy[MhdIdx::MY] == Approx(w.rho*w.vy*w.vy + ptot - w.By*w.By));
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][swap]"`
Expected: FAIL — `mhd_swap_xy` undefined.

- [ ] **Step 3: Write minimal implementation** (append to `src/mhd/mhd_flux.hpp` inside `namespace hrsc`)

```cpp
// Rotate state for the y-sweep: swap x/y momentum and magnetic field.
// Self-inverse. Enables y-sweep to reuse mhd_flux_x / mhd_hll_flux.
template <typename Real>
HD_FUNC Vec<Real, MhdNVars> mhd_swap_xy(const Vec<Real, MhdNVars>& U) {
    Vec<Real, MhdNVars> S = U;
    S[MhdIdx::MX] = U[MhdIdx::MY];
    S[MhdIdx::MY] = U[MhdIdx::MX];
    S[MhdIdx::BX] = U[MhdIdx::BY];
    S[MhdIdx::BY] = U[MhdIdx::BX];
    return S;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][swap]"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/mhd/mhd_flux.hpp tests/unit/test_mhd_swap.cpp
git commit -m "feat(mhd): add mhd_swap_xy rotation for y-sweep reuse"
```

---

## Task 12: GLM parabolic damping (`glm.hpp`)

**Files:**
- Create: `src/mhd/glm.hpp`
- Test: `tests/unit/test_glm.cpp`

- [ ] **Step 1: Write the failing test**

```cpp
// tests/unit/test_glm.cpp
#include "catch.hpp"
#include "core/grid.hpp"
#include "mhd/glm.hpp"

using namespace hrsc;

TEST_CASE("glm_damp decays psi by exp(-dt*ch^2/cp^2), cp^2=ch*cr", "[mhd][glm]") {
    Grid2D<double, MhdNVars> grid(4, 1);
    grid.dx = grid.dy = 0.25;
    auto v = grid.view();
    for (int i = 0; i < 4; ++i) v(i, 0, MhdIdx::PSI) = 2.0;

    const double ch = 3.0, cr = 0.18, dt = 0.01;
    glm_damp<double>(v, 4, 1, ch, cr, dt);

    const double cp2 = ch * cr;
    const double expected = 2.0 * std::exp(-dt * ch * ch / cp2);
    for (int i = 0; i < 4; ++i) REQUIRE(v(i, 0, MhdIdx::PSI) == Approx(expected));
}

TEST_CASE("glm_damp is a no-op when cr<=0", "[mhd][glm]") {
    Grid2D<double, MhdNVars> grid(2, 1);
    grid.dx = grid.dy = 0.5;
    auto v = grid.view();
    v(0, 0, MhdIdx::PSI) = 1.0; v(1, 0, MhdIdx::PSI) = -1.0;
    glm_damp<double>(v, 2, 1, /*ch=*/2.0, /*cr=*/0.0, /*dt=*/0.1);
    REQUIRE(v(0, 0, MhdIdx::PSI) == Approx(1.0));
    REQUIRE(v(1, 0, MhdIdx::PSI) == Approx(-1.0));
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][glm]"`
Expected: FAIL — `mhd/glm.hpp` not found.

- [ ] **Step 3: Write minimal implementation**

```cpp
// src/mhd/glm.hpp
#pragma once
#include "core/grid.hpp"
#include "mhd/mhd_state.hpp"
#include <cmath>

namespace hrsc {

// Parabolic GLM damping (Dedner mixed-GLM): psi *= exp(-dt * ch^2 / cp^2),
// with cp^2 = ch * cr. The divergence SOURCE is delivered by the summed
// x/y sweep fluxes (F[PSI]=ch^2*Bn); this stage only adds the decay.
// No-op when cr <= 0 (used by the 1D path to stay bit-identical).
template <typename Real, typename Ptr>
void glm_damp(GridViewBase<Real, MhdNVars, Ptr> gv, int nx, int ny,
              Real ch, Real cr, Real dt) {
    if (!(cr > Real(0)) || !(ch > Real(0))) return;
    const Real cp2 = ch * cr;
    const Real factor = std::exp(-dt * ch * ch / cp2);
    for (int j = 0; j < ny; ++j)
        for (int i = 0; i < nx; ++i)
            gv(i, j, MhdIdx::PSI) *= factor;
}

} // namespace hrsc
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][glm]"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/mhd/glm.hpp tests/unit/test_glm.cpp
git commit -m "feat(mhd): add GLM parabolic damping stage (glm_damp)"
```

---

## Task 13: Refactor solver internals to state-based, dimension-agnostic (1D bit-preserved)

**Files:**
- Modify: `src/mhd/mhd_solver.cpp`
- Test: existing `tests/unit/test_mhd_solver.cpp` (regression gate — must stay green)

- [ ] **Step 1: Generalize the cell accessors to (i, j)**

Replace the `j=0`-hardwired helpers:

```cpp
template <typename Real, typename Ptr>
Vec<Real, MhdNVars> load_cell(GridViewBase<Real, MhdNVars, Ptr> gv, int i, int j) {
    Vec<Real, MhdNVars> U{};
    for (int k = 0; k < MhdNVars; ++k) U[k] = gv(i, j, k);
    return U;
}
template <typename Real>
void store_cell(GridView<Real, MhdNVars> gv, int i, int j, const Vec<Real, MhdNVars>& U) {
    for (int k = 0; k < MhdNVars; ++k) gv(i, j, k) = U[k];
}
```

- [ ] **Step 2: Make `predict_faces` state-based (no grid reads)**

```cpp
// Pure function of the three cells along the sweep direction and the
// direction spacing h. Returns the limited+predicted left/right face states.
template <typename Real>
void predict_faces(const Vec<Real, MhdNVars>& Um, const Vec<Real, MhdNVars>& U0,
                   const Vec<Real, MhdNVars>& Up, Real dt, Real gamma, Real ch, Real h,
                   Vec<Real, MhdNVars>& left, Vec<Real, MhdNVars>& right) {
    const Vec<Real, MhdNVars> slope = mhd_slope(Um, U0, Up);
    left  = U0 - Real(0.5) * slope;
    right = U0 + Real(0.5) * slope;
    if (!is_physical_state(left, gamma) || !is_physical_state(right, gamma)) {
        left = U0; right = U0; return;
    }
    const Vec<Real, MhdNVars> FL = mhd_flux_x(left, gamma, ch);
    const Vec<Real, MhdNVars> FR = mhd_flux_x(right, gamma, ch);
    const Real half_dtdx = Real(0.5) * dt / h;
    for (int k = 0; k < MhdNVars; ++k) {
        const Real predictor = half_dtdx * (FR[k] - FL[k]);
        left[k] -= predictor; right[k] -= predictor;
    }
    if (!is_physical_state(left, gamma) || !is_physical_state(right, gamma)) {
        left = U0; right = U0;
    }
}
```

> Note: `predict_faces` always works in the local "x-like" frame. The y-sweep (Task 15) passes already-rotated states, so `mhd_flux_x` is the correct normal flux there too.

- [ ] **Step 3: Rewrite `step()` to call an x_sweep over all rows**

Replace the body of `step()` to delegate to `x_sweep(dt)` (Task 15 adds `y_sweep` + glm). For now `x_sweep` loops `j` over every physical row and runs the existing interface loop per row using `load_cell(gv,i,j)` and `predict_faces(...)` with `h = gv.dx`. Keep the flux/update math identical to the current `step()` so `ny=1` reproduces Part-1 results exactly.

- [ ] **Step 4: Run the regression gate**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][solver]"`
Expected: PASS — the 1D Brio-Wu solver test is unchanged (bit-identical evolution).

- [ ] **Step 5: Verify 1D end-to-end is still bit-identical**

Run: `./build-double/hrsc_mhd tests/cases/brio_wu_1d/brio_wu.cfg`
Expected: same stderr line as Part 1 (`steps=759 divB_max≈4.441e-14`).

- [ ] **Step 6: Commit**

```bash
git add src/mhd/mhd_solver.cpp
git commit -m "refactor(mhd): make solver internals state-based and (i,j)-general"
```

---

## Task 14: 2D constructor + fields (`mhd_solver.{hpp,cpp}`)

**Files:**
- Modify: `src/mhd/mhd_solver.hpp`, `src/mhd/mhd_solver.cpp`
- Test: `tests/unit/test_mhd_solver.cpp` (add a 2D-construction case)

- [ ] **Step 1: Write the failing test**

```cpp
TEST_CASE("MhdSolver 2D constructor builds an ny>1 grid", "[mhd][solver2d]") {
    MhdSolver<double> s(16, 4, 1.0/16, 1.0/4, 0.0, 0.0,
                        /*gamma=*/2.0, /*cfl=*/0.4, /*t_end=*/0.0,
                        BoundaryType::Periodic, BoundaryType::Periodic, /*glm_cr=*/0.18);
    auto gv = s.grid_view();
    REQUIRE(gv.nx == 16);
    REQUIRE(gv.ny == 4);
}
```

- [ ] **Step 2: Add fields + 2D ctor declaration to the header**

In `mhd_solver.hpp`, add `int m_ny; Real m_dy; Real m_ymin; BoundaryType m_bc_y; Real m_glm_cr;` and declare `void y_sweep(TimeReal dt);` plus:

```cpp
// 2D constructor
MhdSolver(int nx, int ny, Real dx, Real dy, Real xmin, Real ymin,
          Real gamma, Real cfl, TimeReal t_end,
          BoundaryType bc_x = BoundaryType::Outflow,
          BoundaryType bc_y = BoundaryType::Outflow,
          Real glm_cr = Real(0.18));
```

- [ ] **Step 3: Implement the 2D ctor; make the 1D ctor delegate**

```cpp
template <typename Real>
MhdSolver<Real>::MhdSolver(int nx, int ny, Real dx, Real dy, Real xmin, Real ymin,
                           Real gamma, Real cfl, TimeReal t_end,
                           BoundaryType bc_x, BoundaryType bc_y, Real glm_cr)
    : m_grid(nx, ny), m_xmin(xmin), m_ymin(ymin), m_dx(dx), m_dy(dy),
      m_gamma(gamma), m_cfl(cfl), m_t_end(t_end), m_time(TimeReal(0)),
      m_step(0), m_bc_x(bc_x), m_ny(ny), m_bc_y(bc_y), m_glm_cr(glm_cr) {
    m_grid.dx = dx; m_grid.dy = dy;
}

// 1D convenience ctor: ny=1, glm_cr=0 -> no y-sweep, no damping -> bit-identical.
template <typename Real>
MhdSolver<Real>::MhdSolver(int nx, Real dx, Real xmin, Real gamma, Real cfl,
                           TimeReal t_end, BoundaryType bc_x)
    : MhdSolver(nx, 1, dx, dx, xmin, Real(0), gamma, cfl, t_end,
                bc_x, BoundaryType::Outflow, Real(0)) {}
```

> Declare member init order to match the header field order to avoid `-Wreorder`. Adjust the field declaration order if needed so the initializer list is in-order.

- [ ] **Step 4: Run test to verify it passes**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][solver2d]"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/mhd/mhd_solver.hpp src/mhd/mhd_solver.cpp tests/unit/test_mhd_solver.cpp
git commit -m "feat(mhd): add 2D MhdSolver constructor; 1D ctor delegates"
```

---

## Task 15: Y-sweep + GLM damping + 2D compute_ch (`mhd_solver.cpp`)

**Files:**
- Modify: `src/mhd/mhd_solver.cpp`
- Test: `tests/unit/test_mhd_solver.cpp` (2D Brio-Wu-reproduces-1D smoke)

- [ ] **Step 1: Write the failing test**

```cpp
TEST_CASE("2D Brio-Wu (ny=4, periodic-y) reproduces 1D row-wise", "[mhd][solver2d]") {
    const int nx = 128, ny = 4;
    const double dx = 1.0/nx, t_end = 0.05;
    // 1D reference
    MhdSolver<double> s1(nx, dx, 0.0, 2.0, 0.4, t_end);
    setup_brio_wu(s1.grid_view(), nx, dx, 0.0, 2.0, 0.5);
    s1.run();
    // 2D run, identical IC on every row, periodic in y, GLM on
    MhdSolver<double> s2(nx, ny, dx, dx, 0.0, 0.0, 2.0, 0.4, t_end,
                         BoundaryType::Outflow, BoundaryType::Periodic, 0.18);
    auto gv2 = s2.grid_view();
    for (int j = 0; j < ny; ++j) setup_brio_wu_row(gv2, nx, dx, 0.0, 2.0, 0.5, j);
    s2.run();
    auto gv1 = s1.grid_view();
    for (int j = 0; j < ny; ++j)
        for (int i = 0; i < nx; ++i)
            REQUIRE(gv2(i, j, MhdIdx::RHO) == Approx(gv1(i, 0, MhdIdx::RHO)).margin(1e-10));
}
```

> `setup_brio_wu_row` is a thin per-row variant of `setup_brio_wu`; add it next to `setup_brio_wu` in Step 3 (it writes the same x-profile into row `j`). The existing `setup_brio_wu` keeps writing row 0 for the 1D path.

- [ ] **Step 2: Run test to verify it fails**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][solver2d]"`
Expected: FAIL — `y_sweep` not yet wired (2D rows diverge or `setup_brio_wu_row` undefined).

- [ ] **Step 3: Implement `y_sweep`, 2D `compute_ch`, `apply_bc` per axis, and wire `step()`**

```cpp
// y_sweep: for each column i, run the interface loop in j on ROTATED states,
// then rotate the HLL flux back before applying the y-difference.
template <typename Real>
void MhdSolver<Real>::y_sweep(TimeReal dt_time) {
    if (m_ny <= 1) return;
    const Real dt = static_cast<Real>(dt_time);
    auto gv = m_grid.view();
    const Real ch = compute_ch();
    const int nx = gv.nx, ny = gv.ny;
    for (int i = 0; i < nx; ++i) {
        std::vector<Vec<Real, MhdNVars>> flux(static_cast<std::size_t>(ny + 1));
        for (int jf = 0; jf <= ny; ++jf) {
            const int jL = jf - 1, jR = jf;
            Vec<Real, MhdNVars> a{}, lcl{}, lcr{}, rcl{}, rcr{};
            // rotate the 3-cell stencils into the x-like frame
            predict_faces(mhd_swap_xy(load_cell(gv,i,jL-1)), mhd_swap_xy(load_cell(gv,i,jL)),
                          mhd_swap_xy(load_cell(gv,i,jL+1)), dt, m_gamma, ch, m_dy, lcl, lcr);
            predict_faces(mhd_swap_xy(load_cell(gv,i,jR-1)), mhd_swap_xy(load_cell(gv,i,jR)),
                          mhd_swap_xy(load_cell(gv,i,jR+1)), dt, m_gamma, ch, m_dy, rcl, rcr);
            flux[static_cast<std::size_t>(jf)] =
                mhd_swap_xy(mhd_hll_flux(lcr, rcl, m_gamma, ch)); // rotate flux back
        }
        const Real dtdy = dt / m_dy;
        for (int j = 0; j < ny; ++j) {
            Vec<Real, MhdNVars> U = load_cell(gv, i, j);
            const auto& fL = flux[static_cast<std::size_t>(j)];
            const auto& fR = flux[static_cast<std::size_t>(j + 1)];
            for (int k = 0; k < MhdNVars; ++k) U[k] -= dtdy * (fR[k] - fL[k]);
            store_cell(gv, i, j, U);
        }
    }
    validate_physical_grid(gv, m_gamma);
}
```

Extend `compute_ch` to scan both directions:

```cpp
// inside compute_ch, per cell, after computing the x fast speed:
ch = std::max(ch, std::abs(w.vx) + fast_speed_x(w, m_gamma));
ch = std::max(ch, std::abs(w.vy) + fast_speed_x(mhd_swap_xy_prim(w), m_gamma));
```

> Add a tiny `mhd_swap_xy_prim` (swap vx/vy, Bx/By in an `MhdPrim`) OR compute the y fast speed by swapping the conserved state; the simplest is to reuse `fast_speed_x` on the swapped primitive. Define it next to `mhd_swap_xy` in `mhd_flux.hpp`.

Make `apply_bc` cover both axes and the ψ rule:

```cpp
template <typename Real>
void MhdSolver<Real>::apply_bc() {
    auto gv = m_grid.view();
    apply_axis_bc(gv, Axis::X, m_bc_x);
    if (m_ny > 1) apply_axis_bc(gv, Axis::Y, m_bc_y);
}
// helper in the anonymous namespace:
template <typename Real>
void apply_axis_bc(GridView<Real, MhdNVars> gv, Axis axis, BoundaryType bc) {
    if (bc == BoundaryType::Outflow) {
        apply_outflow_bc(gv, axis);
        zero_psi_ghosts(gv, axis);          // psi=0 at ghosts: no divergence reflection
    } else if (bc == BoundaryType::Periodic) {
        apply_periodic_bc(gv, axis);         // psi wraps naturally
    } else {
        throw std::logic_error("MhdSolver supports only outflow/periodic BCs");
    }
}
```

Wire `step()` to: `apply_bc()` → `ch=compute_ch()` → `dt=compute_dt(ch)` → `x_sweep(dt)` → `y_sweep(dt)` → `glm_damp(gv, nx, ny, ch, m_glm_cr, (Real)dt)` → `validate_physical_grid`. (`x_sweep` keeps its own `apply_bc`-free body; BCs are applied once per step at the top.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][solver2d]"`
Expected: PASS — every 2D row matches the 1D density to 1e-10.

- [ ] **Step 5: Re-run the 1D regression gate**

Run: `./build-double/unit_tests "[mhd][solver]" && ./build-double/hrsc_mhd tests/cases/brio_wu_1d/brio_wu.cfg`
Expected: 1D unchanged (`steps=759`, divB_max ≈ 4.441e-14).

- [ ] **Step 6: Commit**

```bash
git add src/mhd/mhd_solver.cpp src/mhd/mhd_flux.hpp tests/unit/test_mhd_solver.cpp
git commit -m "feat(mhd): add y-sweep, 2D CFL, periodic/psi BCs, GLM damping step"
```

---

## Task 16: `hrsc_mhd` 2D cfg parsing + IO; 2D cfgs

**Files:**
- Modify: `src/mhd_main.cpp`, `src/mhd/mhd_config.hpp`
- Create: `tests/cases/brio_wu_1d/brio_wu_2d.cfg`, `tests/cases/mhd_divb_clean/divb_blob.cfg`
- Test: `tests/unit/test_mhd_config.cpp` (periodic accepted)

- [ ] **Step 1: Accept `periodic` in `parse_mhd_boundary` (+ failing test)**

```cpp
// tests/unit/test_mhd_config.cpp (add)
TEST_CASE("parse_mhd_boundary accepts periodic", "[mhd][config]") {
    REQUIRE(parse_mhd_boundary("periodic") == BoundaryType::Periodic);
    REQUIRE(parse_mhd_boundary("outflow")  == BoundaryType::Outflow);
}
```

Then in `mhd_config.hpp`:

```cpp
inline BoundaryType parse_mhd_boundary(const std::string& value) {
    if (value == "outflow")  return BoundaryType::Outflow;
    if (value == "periodic") return BoundaryType::Periodic;
    throw std::invalid_argument("unsupported MHD boundary condition: " + value);
}
```

- [ ] **Step 2: Extend `mhd_main.cpp` for 2D**

Parse `ny` (default 1), `ymin`/`ymax` (default 0/0), `bc_y` (default = `bc`), `glm_cr` (default 0.18), and add a `divb_blob` test case to `MhdTestCase`. Build the 2D solver when `ny>1`:

```cpp
const int ny = cfg.get_int("ny", 1);
const double ymin = cfg.get_double("ymin", 0.0);
const double ymax = cfg.get_double("ymax", ny > 1 ? 1.0 : 0.0);
const double glm_cr = cfg.get_double("glm_cr", 0.18);
const hrsc::BoundaryType bc_y =
    hrsc::parse_mhd_boundary(cfg.get_string("bc_y", cfg.get_string("bc", "outflow")));
const Real dy = ny > 1 ? static_cast<Real>((ymax - ymin) / ny) : dx;
hrsc::MhdSolver<Real> solver(nx, ny, dx, dy, (Real)xmin, (Real)ymin,
                             (Real)gamma, (Real)cfl, t_end, bc, bc_y, (Real)glm_cr);
// setup per test case (brio_wu fills all rows; divb_blob seeds the Gaussian Bx bump)
...
hrsc::write_binary<Real, hrsc::MhdNVars>(out, gv, nx, ny, dx, dy, (Real)solver.time());
```

Validate `ny>0`, `glm_cr>=0`, and `ymax>ymin` when `ny>1` in `validate_cfg`.

- [ ] **Step 3: Write the cfgs**

```ini
# tests/cases/brio_wu_1d/brio_wu_2d.cfg — Brio-Wu replicated across 4 rows (periodic-y)
test = brio_wu
nx = 800
ny = 4
xmin = 0.0
xmax = 1.0
ymin = 0.0
ymax = 0.005
x0 = 0.5
gamma = 2.0
cfl = 0.4
t_end = 0.1
bc = outflow
bc_y = periodic
glm_cr = 0.18
```

```ini
# tests/cases/mhd_divb_clean/divb_blob.cfg — Gaussian Bx bump, doubly periodic
test = divb_blob
nx = 128
ny = 128
xmin = 0.0
xmax = 1.0
ymin = 0.0
ymax = 1.0
gamma = 2.0
cfl = 0.4
t_end = 0.5
bc = periodic
bc_y = periodic
glm_cr = 0.18
```

- [ ] **Step 4: Build + smoke run both**

Run:
```bash
cmake --build build-double --target hrsc_mhd
./build-double/hrsc_mhd tests/cases/brio_wu_1d/brio_wu_2d.cfg
./build-double/hrsc_mhd tests/cases/mhd_divb_clean/divb_blob.cfg
```
Expected: both finish with a `[mhd]` diagnostic line; brio_wu_2d divB_max at round-off.

- [ ] **Step 5: Commit**

```bash
git add src/mhd_main.cpp src/mhd/mhd_config.hpp tests/unit/test_mhd_config.cpp \
        tests/cases/brio_wu_1d/brio_wu_2d.cfg tests/cases/mhd_divb_clean/divb_blob.cfg
git commit -m "feat(mhd): 2D cfg parsing + Brio-Wu-2D and divb-blob cases"
```

---

## Task 17: 2D Brio-Wu regression validation

**Files:**
- Create: `scripts/regression/mhd_2d_week12.py`

- [ ] **Step 1: Write the regression driver**

A driver mirroring `scripts/regression/mhd_brio_wu_1d.py`'s provenance discipline (generated cfg, stdout/stderr, metadata.json, summary.{md,json}). For Brio-Wu-2D: run the cfg, read the binary, assert every row's density equals row 0 within 1e-10 (transverse invariance) and that the row-0 profile matches the committed 1D `bw_800.bin` density within 1e-10, and that `divB_max` from stderr ≤ 1e-12. Write `experiments/week12/mhd_2d/brio_wu_2d/summary.{md,json}`.

- [ ] **Step 2: Run it**

Run: `python scripts/regression/mhd_2d_week12.py --case brio_wu_2d`
Expected: `transverse_invariance: True`, `matches_1d: True`, `divB_max_ok: True`.

- [ ] **Step 3: Commit**

```bash
git add scripts/regression/mhd_2d_week12.py experiments/week12/mhd_2d/brio_wu_2d/summary.md
git commit -m "test(mhd): 2D Brio-Wu regression (transverse invariance + 1D match)"
```

---

## Task 18: div(B)-cleaning decay validation

**Files:**
- Modify: `scripts/regression/mhd_2d_week12.py` (add the cleaning case)

- [ ] **Step 1: Add the cleaning driver path**

For `divb_blob`: run the case at `glm_cr ∈ {0.0, 0.18, 0.36}` (override via generated cfgs), capturing `divB_max` at several checkpoints (use `output_times` if available, else short t_end runs at increasing times). Assert:
- `glm_cr=0.18` and `0.36`: `max|div(B)|` strictly decreasing over checkpoints;
- decay with `0.36` faster than `0.18` (smaller final `max|div(B)|`);
- `glm_cr=0.0` (control): not decaying (final ≥ ~initial up to advection).

Write `experiments/week12/mhd_2d/divb_clean/summary.{md,json}` with the per-cr decay table.

> If per-checkpoint output is not yet supported by `hrsc_mhd`, run the same case at increasing `t_end` values and read the final `divB_max` from each run's stderr — keep it simple, no solver changes.

- [ ] **Step 2: Run it**

Run: `python scripts/regression/mhd_2d_week12.py --case divb_clean`
Expected: monotonic decay for cr>0, faster for larger cr, flat control.

- [ ] **Step 3: Commit**

```bash
git add scripts/regression/mhd_2d_week12.py experiments/week12/mhd_2d/divb_clean/summary.md
git commit -m "test(mhd): div(B)-cleaning decay validation across glm_cr"
```

---

## Task 19: Docs addendum + green gates

**Files:**
- Modify: `docs/week12/week12-summary.md`, `docs/INDEX.md`

- [ ] **Step 1: Confirm all suites green**

Run: `./build-double/unit_tests -r compact`
Expected: PASS — Part-1 MHD, new `[mhd][swap]/[glm]/[solver2d]/[config]`, boundary, and all Euler cases; no Euler regressions.

- [ ] **Step 2: Confirm 1D still bit-identical**

Run: `./build-double/hrsc_mhd tests/cases/brio_wu_1d/brio_wu.cfg`
Expected: `steps=759`, `divB_max ≈ 4.441e-14` (unchanged from Part 1).

- [ ] **Step 3: Write the 2D addendum**

Append a "## Week 12 Part 2 — 2D machinery + GLM" section to `week12-summary.md`: delivered files (`mhd_swap_xy`, `glm.hpp`, 2D solver, periodic/ψ BCs), the 2D Brio-Wu transverse-invariance result, the div(B)-cleaning decay table, and the carried-forward gaps (Orszag-Tang/KH physics, HLLD, GPU MHD, reflective BC, **2D figures**) for the Week-13 plan.

- [ ] **Step 4: Commit**

```bash
git add docs/week12/week12-summary.md docs/INDEX.md
git commit -m "docs(mhd): record Week 12 Part 2 (2D MHD + GLM cleaning)"
```

---

## Self-Review (writing-plans, Part 2)

- **Spec coverage:** mhd_swap_xy (T11) · glm_damp + cfg c_r (T12) · state-based (i,j) refactor, 1D bit-preserved (T13) · 2D ctor, 1D delegates (T14) · y-sweep + 2D CFL + periodic/ψ BC + glm wiring (T15) · 2D cfg parsing + IO + cfgs (T16) · 2D Brio-Wu regression (T17) · div(B)-cleaning decay (T18) · docs + green gates (T19). All design-spec sections mapped.
- **Out of scope (named):** Orszag-Tang/KH physics, HLLD, GPU MHD, reflective MHD BC, run_matrix MHD-awareness, 2D figures, Strang 2nd-order splitting — all carried to Week 13.
- **Type consistency:** `mhd_swap_xy`/`mhd_swap_xy_prim`, `glm_damp`, `load_cell(gv,i,j)`/`store_cell(gv,i,j,U)`, state-based `predict_faces(Um,U0,Up,dt,gamma,ch,h,left,right)`, 2D `MhdSolver(nx,ny,dx,dy,xmin,ymin,gamma,cfl,t_end,bc_x,bc_y,glm_cr)`, `apply_axis_bc`/`zero_psi_ghosts`, `setup_brio_wu_row` used identically across tasks.
- **1D-preservation gate** is explicit and repeated (T13 S4-S5, T15 S5, T19 S2): 1D ctor delegates with `glm_cr=0`, `ny=1` skips `y_sweep`, so Part-1 Brio-Wu stays bit-identical (`steps=759`, divB_max ≈ 4.441e-14).
- **Known risks flagged:** member-init order vs `-Wreorder` (T14 S3); per-checkpoint output may be unavailable → fall back to increasing-`t_end` runs (T18 S1) with no solver change.
- **Reuse points (confirmed):** Euler rotate-and-reuse precedent (`euler_solver.cpp:258`); `apply_periodic_bc`/`apply_outflow_bc` generic on NVars; `Grid2D.dx/dy` fields set before `view()`; `compute_divB_norms` already 2D-capable (`error_norms.hpp`).
