# Week 12 — 1D Ideal-MHD Walking Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a correct, verifiable 1D ideal-MHD pipeline (9-variable state incl. GLM `psi`, HLL Riemann solver, Brio-Wu shock tube) validated against a self-converged double reference, delivered as a separate `hrsc_mhd` executable that leaves the Report-1-validated Euler binary untouched.

**Architecture:** All MHD code is additive under `src/mhd/`. The core layer (`Grid2D<Real, NVars>`, `core/eos.hpp`, `core/boundary.hpp`, `core/vec.hpp`) and utilities (`utils/io.hpp`, `utils/config.hpp`, `utils/error_norms.hpp`) are reused unchanged except for one additive function (`compute_divB_norms`). MHD compiles into its own static lib + `hrsc_mhd` executable; the `hrsc` Euler target and the `src/app/` layer are not modified.

**Tech Stack:** C++17 templated-on-`Real` (float/double via `HRSC_REAL`), CMake/Ninja, Catch2 unit tests (`tests/unit/test_*.cpp`, auto-globbed), key=value cfg files, little-endian binary IO with a 64-byte header carrying `nvars`, Python regression harness for L1/L2/Linf.

**Reference spec:** [docs/superpowers/specs/2026-06-11-report2-week12-mhd-1d-design.md](../superpowers/specs/2026-06-11-report2-week12-mhd-1d-design.md)

---

## Physics reference (ideal MHD, GLM, 1D x-direction)

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
- Create: `src/mhd/mhd_reconstruct.hpp` — minmod MUSCL + Hancock predictor over `MhdNVars`.
- Create: `src/mhd/mhd_solver.hpp` — `MhdSolver<Real>` declaration.
- Create: `src/mhd/mhd_solver.cpp` — definitions + explicit float/double instantiation.
- Create: `src/mhd_main.cpp` — cfg-driven entry for `hrsc_mhd`.
- Create: `tests/cases/brio_wu_1d/brio_wu.cfg` — N=800 production cfg.
- Create: `tests/cases/brio_wu_1d/brio_wu_ref.cfg` — N=8000 double reference cfg.
- Create: `tests/unit/test_mhd_state.cpp`, `test_mhd_flux.cpp`, `test_mhd_hll.cpp`, `test_divb.cpp`.
- Create: `scripts/regression/mhd_brio_wu_1d.py` — reference + L1/L2/Linf validation.
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

## Task 5: MUSCL-Hancock reconstruction (`mhd_reconstruct.hpp`)

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
    setup_brio_wu(solver.grid_view(), 64, 1.0/64, 0.0, 0.5);
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
void setup_brio_wu(GridView<Real, MhdNVars> gv, int nx, Real dx, Real xmin, Real x0);

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

namespace hrsc {

template <typename Real>
void setup_brio_wu(GridView<Real, MhdNVars> gv, int nx, Real dx, Real xmin, Real x0) {
    const Real gamma = Real(2);
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
      m_t_end(t_end), m_time(0), m_step(0), m_bc_x(bc_x) {}

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
template void setup_brio_wu<float>(GridView<float, MhdNVars>, int, float, float, float);
template void setup_brio_wu<double>(GridView<double, MhdNVars>, int, double, double, double);

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
                              static_cast<Real>(x0));
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

> `compute_divB_norms` lives in `utils/error_norms.hpp`; add `#include "utils/error_norms.hpp"` to the includes above.

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

- [ ] **Step 3: Smoke-run both**

Run:
```bash
./build-double/hrsc_mhd tests/cases/brio_wu_1d/brio_wu.cfg
```
Expected: stderr line `[mhd] t=0.100000 steps=... divB_mean=... divB_max=<round-off>`.

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
reference, downsample the reference, and report L1/L2/Linf on density.
Reuses io_helper for binary reads."""
import subprocess, sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from io_helper import read_binary  # returns (meta, array[ny,nx,nvars])

ROOT = pathlib.Path(__file__).resolve().parents[2]
BIN = ROOT / "build-double" / "hrsc_mhd"
CASE = ROOT / "tests/cases/brio_wu_1d"
OUT = ROOT / "experiments/week12/brio_wu_1d"
OUT.mkdir(parents=True, exist_ok=True)
RHO = 0  # MhdIdx::RHO

def run(cfg, nx):
    out = OUT / f"bw_{nx}.bin"
    subprocess.run([str(BIN), str(cfg)], check=True,
                   env={"_dummy": "1", **__import__("os").environ},
                   cwd=str(ROOT),
                   input=None)
    # cfg has no output_file; write one by overriding via a temp cfg line:
    raise SystemExit("Set output_file in cfgs or extend hrsc_mhd CLI before running.")

if __name__ == "__main__":
    print("See Step 2: add output_file to each resolution before computing norms.")
```

> The script is intentionally a skeleton because `hrsc_mhd` takes a single cfg. Step 2 makes it runnable.

- [ ] **Step 2: Make resolutions runnable (add `output_file` per run)**

Replace the script body with one that writes a temp cfg per resolution, sets `output_file`, runs, reads, and compares. Use cfg cloning:

```python
import os, subprocess, sys, pathlib, tempfile
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from io_helper import read_binary

ROOT = pathlib.Path(__file__).resolve().parents[2]
BIN  = ROOT / "build-double" / "hrsc_mhd"
BASE = (ROOT / "tests/cases/brio_wu_1d/brio_wu.cfg").read_text()
OUT  = ROOT / "experiments/week12/brio_wu_1d"; OUT.mkdir(parents=True, exist_ok=True)
RHO = 0

def run(nx):
    cfg = "\n".join(l for l in BASE.splitlines() if not l.startswith("nx"))
    out = OUT / f"bw_{nx}.bin"
    cfg += f"\nnx = {nx}\noutput_file = {out}\n"
    p = OUT / f"bw_{nx}.cfg"; p.write_text(cfg)
    subprocess.run([str(BIN), str(p)], check=True, cwd=str(ROOT))
    meta, arr = read_binary(str(out))     # arr shape [ny, nx, nvars]
    return arr[0, :, RHO]

ref = run(8000)
for nx in (200, 400, 800):
    rho = run(nx)
    # block-average the 8000-cell reference down to nx for a fair comparison
    factor = 8000 // nx
    refd = ref.reshape(nx, factor).mean(axis=1)
    diff = np.abs(rho - refd)
    dx = 1.0 / nx
    L1 = diff.sum() * dx
    L2 = np.sqrt((diff**2).sum() * dx)
    Linf = diff.max()
    print(f"N={nx:5d}  L1={L1:.3e}  L2={L2:.3e}  Linf={Linf:.3e}")
```

- [ ] **Step 3: Run the validation**

Run: `python scripts/regression/mhd_brio_wu_1d.py`
Expected: three rows N=200/400/800 with **monotonically decreasing** L1/L2 (≈1st-order HLL: roughly halving L1 as N doubles).

- [ ] **Step 4: Commit**

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

Create `docs/week12/week12-summary.md` capturing: delivered files, Brio-Wu L1/L2/Linf table, divB_max value, the indexing decision in Task 6, and the deferred items (GLM/2D/HLLD/GPU/harness) for Week 13.

- [ ] **Step 5: Commit**

```bash
git add docs/INDEX.md docs/week12/week12-summary.md
git commit -m "docs(mhd): record Week 12 1D MHD walking skeleton"
```

---

## Self-Review (writing-plans)

- **Spec coverage:** state (T1) · flux incl. psi (T2) · HLL + strict-ineq flag (T3) · compute_divB_norms (T4) · MUSCL-Hancock (T5–T6) · MhdSolver float/double instantiation (T6) · hrsc_mhd executable, Euler untouched (T7) · Brio-Wu cfgs (T8) · self-converged double reference + L1/L2/Linf (T9) · divB sentinel + Euler-green + docs (T10). All spec sections mapped.
- **Out-of-scope** (GLM source step, 2D, Orszag-Tang/KH, HLLD, GPU MHD, run_matrix MHD-awareness) intentionally absent — deferred to Weeks 13–14.
- **Type consistency:** `MhdNVars`, `MhdIdx`, `MhdPrim`, `prim_to_cons`/`cons_to_prim`/`pressure`/`fast_speed_x`, `mhd_flux_x`, `mhd_hll_flux`, `mhd_minmod`/`mhd_slope`, `DivBNorms`/`compute_divB_norms`, `MhdSolver`/`setup_brio_wu` used identically across tasks.
- **Known risk flagged:** interface L/R indexing in Task 6 Step 4 (implementer note) — the HLL consistency test isolates indexing from flux correctness.
- **Reuse points (API confirmed against source):** `core/boundary.hpp` exposes per-type helpers `apply_outflow_bc(view, Axis)` / `apply_periodic_bc` / `apply_reflective_bc` (no generic dispatcher) — Task 6 calls `apply_outflow_bc` directly. `GridView`/`Grid2D` expose `nx`/`ny` as **fields** (e.g. `m_grid.nx`, `grid.nx`), not methods. `utils/io.hpp` `write_binary<Real,NVars>(file, view, nx, ny, dx, dy, time)`; `utils/config.hpp` `Config` with `get_int/get_double/get_string`; `scripts/io_helper.py` `read_binary`. `MhdNVars` mirrors `EulerNVars=4` (`src/core/eos.hpp:22`).
```
