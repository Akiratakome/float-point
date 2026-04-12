# Week 3 Implementation Plan: Complete 1D Tools + 2D Extension

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the exact Riemann solver, slope limiters, error norms, binary IO, grid convergence study, y-direction functions, 2D solver, and Verificarlo analysis scripts — completing the Week 3 deliverables for the HRSC floating-point precision project.

**Architecture:** Bottom-up dependency chain. Foundation modules (exact Riemann, limiters, error norms, binary IO) are independent and feed into the convergence study. Y-direction functions enable the 2D solver. Verificarlo scripts are independent of all C++ changes.

**Tech Stack:** C++17, CMake + Ninja, Catch2 (single-header), Python 3 (matplotlib, numpy), Verificarlo (Docker)

**Spec:** `docs/week3/week3-design.md`

**Build command:** `cmake -B build -S . -G Ninja && cmake --build build`

**Test command:** `PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests`

**Test with tag:** `PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[tag]"`

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| **CREATE** | `src/euler/exact_riemann.hpp` | Newton-Raphson pressure iteration + self-similar sampling |
| **CREATE** | `src/utils/error_norms.hpp` | L1/L2/Linf error norm computation |
| **CREATE** | `src/utils/io.hpp` | Binary output (64-byte header + raw data) |
| **CREATE** | `tests/cases/toro_1d/convergence_sod.cfg` | Config file for convergence study |
| **CREATE** | `tests/cases/toro_1d/stationary_contact.cfg` | Config file for stationary contact test |
| **CREATE** | `scripts/convergence.py` | Log-log convergence plot from solver output |
| **CREATE** | `analysis/compare.py` | Binary output loader + exact Riemann error norms |
| **CREATE** | `analysis/plot_1d.py` | Numerical vs exact overlay plots |
| **CREATE** | `analysis/requirements.txt` | Python dependencies (numpy, matplotlib) |
| **MODIFY** | `src/euler/muscl.hpp` | Rename minmod→minbee, add van Leer/superbee/van Albada + functors, add `_y` |
| **MODIFY** | `src/euler/hancock.hpp` | Thread limiter template param, add `muscl_hancock_y` |
| **MODIFY** | `src/euler/euler_flux.hpp` | Add `euler_flux_y` |
| **MODIFY** | `src/euler/euler_solver.hpp` | 2D constructor, per-direction CFL, x/y sweeps, alternating Godunov |
| **MODIFY** | `src/utils/config.hpp` | Add `get_int_list` |
| **MODIFY** | `src/main.cpp` | Convergence mode, 2D support, pass xmin, stationary contact |
| **MODIFY** | `tests/cases/toro_1d/toro_tests.hpp` | Add `setup_stationary_contact` IC |
| **MODIFY** | `tests/unit/test_euler.cpp` | Tests for all new modules |
| **MODIFY** | `CMakeLists.txt` | Add include paths for new test configs if needed |
| **MODIFY** | `scripts/verificarlo_run.sh` | VPREC 40-bit + branch detection |
| **MODIFY** | `scripts/verificarlo_analysis.py` | Branch flip analysis |

---

## Task 1: Slope Limiters — Rename minmod to minbee + Add Limiter Functions

**Files:**
- Modify: `src/euler/muscl.hpp`
- Modify: `tests/unit/test_euler.cpp`

This task renames the existing `minmod` to `minbee` (Toro nomenclature), adds three new limiter free functions, and creates functor wrappers. The `muscl_reconstruct_x` signature change happens in Task 2.

- [ ] **Step 1: Rename `minmod` to `minbee` in `muscl.hpp`**

In `src/euler/muscl.hpp`, rename the function and update the call site inside `muscl_reconstruct_x`:

```cpp
// Old:
template <typename Real>
HD_FUNC Real minmod(Real a, Real b) {

// New:
template <typename Real>
HD_FUNC Real minbee(Real a, Real b) {
```

And inside `muscl_reconstruct_x`, change:
```cpp
// Old:
Real slope = minmod(backward, forward);
// New:
Real slope = minbee(backward, forward);
```

- [ ] **Step 2: Rename `minmod` to `minbee` in test file**

In `tests/unit/test_euler.cpp`, rename all `minmod(` calls to `minbee(`:

```cpp
// Old:
REQUIRE(minmod(2.0, 3.0) == Approx(2.0));
// New:
REQUIRE(minbee(2.0, 3.0) == Approx(2.0));
```

Update all three existing minmod TEST_CASE names and bodies:
- `"minmod: same sign values"` → `"minbee: same sign values"`
- `"minmod: opposite signs returns zero"` → `"minbee: opposite signs returns zero"`
- `"minmod: one zero returns zero"` → `"minbee: one zero returns zero"`

Change the tag from `[muscl]` to `[limiter]` for all three.

- [ ] **Step 3: Build and run existing tests — verify rename is clean**

```bash
cmake -B build -S . -G Ninja && cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[limiter]"
```

Expected: All 3 renamed tests pass. All other tests pass unchanged (the default code path is identical).

- [ ] **Step 4: Add van Leer, superbee, van Albada free functions**

In `src/euler/muscl.hpp`, after the `minbee` function, add:

```cpp
// Van Leer limiter: smooth, moderate dissipation (Toro Ch. 13)
template <typename Real>
HD_FUNC Real vanleer(Real a, Real b) {
    if (a * b <= Real(0)) return Real(0);
    return Real(2) * a * b / (a + b);
}

// Superbee limiter: least dissipative symmetric TVD (Toro Ch. 13)
template <typename Real>
HD_FUNC Real superbee(Real a, Real b) {
    if (a * b <= Real(0)) return Real(0);
    Real s = (a > Real(0)) ? Real(1) : Real(-1);
    Real abs_a = std::abs(a);
    Real abs_b = std::abs(b);
    return s * std::max(std::min(abs_a, Real(2) * abs_b),
                        std::min(Real(2) * abs_a, abs_b));
}

// Van Albada limiter: C1-smooth (Toro Ch. 13)
template <typename Real>
HD_FUNC Real vanalbada(Real a, Real b) {
    if (a * b <= Real(0)) return Real(0);
    return a * b * (a + b) / (a * a + b * b);
}
```

- [ ] **Step 5: Add functor wrappers**

In `src/euler/muscl.hpp`, after the free functions and before `muscl_reconstruct_x`, add:

```cpp
struct MinbeeLimiter {
    template <typename Real>
    HD_FUNC Real operator()(Real a, Real b) const { return minbee(a, b); }
};

struct VanLeerLimiter {
    template <typename Real>
    HD_FUNC Real operator()(Real a, Real b) const { return vanleer(a, b); }
};

struct SuperbeeLimiter {
    template <typename Real>
    HD_FUNC Real operator()(Real a, Real b) const { return superbee(a, b); }
};

struct VanAlbadaLimiter {
    template <typename Real>
    HD_FUNC Real operator()(Real a, Real b) const { return vanalbada(a, b); }
};
```

- [ ] **Step 6: Write tests for new limiter functions**

In `tests/unit/test_euler.cpp`, add after the existing minbee tests:

```cpp
// --- vanleer tests ---

TEST_CASE("vanleer: same sign values", "[limiter]") {
    REQUIRE(vanleer(2.0, 3.0) == Approx(2.4));       // 2*2*3/(2+3) = 2.4
    REQUIRE(vanleer(-2.0, -3.0) == Approx(-2.4));
}

TEST_CASE("vanleer: opposite signs returns zero", "[limiter]") {
    REQUIRE(vanleer(2.0, -1.0) == Approx(0.0));
}

TEST_CASE("vanleer: equal values recover gradient", "[limiter]") {
    REQUIRE(vanleer(1.5, 1.5) == Approx(1.5));       // 2*1.5*1.5/(1.5+1.5) = 1.5
    REQUIRE(vanleer(-0.7, -0.7) == Approx(-0.7));
}

// --- superbee tests ---

TEST_CASE("superbee: same sign values", "[limiter]") {
    // superbee(2,3) = max(min(2, 6), min(4, 3)) = max(2, 3) = 3
    REQUIRE(superbee(2.0, 3.0) == Approx(3.0));
    REQUIRE(superbee(-2.0, -3.0) == Approx(-3.0));
}

TEST_CASE("superbee: opposite signs returns zero", "[limiter]") {
    REQUIRE(superbee(2.0, -1.0) == Approx(0.0));
}

TEST_CASE("superbee: returns larger slope than minbee", "[limiter]") {
    double a = 1.0, b = 2.0;
    REQUIRE(std::abs(superbee(a, b)) >= std::abs(minbee(a, b)));
}

// --- vanalbada tests ---

TEST_CASE("vanalbada: same sign values", "[limiter]") {
    // vanalbada(2,3) = 2*3*(2+3)/(4+9) = 30/13 ≈ 2.3077
    REQUIRE(vanalbada(2.0, 3.0) == Approx(30.0 / 13.0).epsilon(1e-12));
}

TEST_CASE("vanalbada: opposite signs returns zero", "[limiter]") {
    REQUIRE(vanalbada(2.0, -1.0) == Approx(0.0));
}

TEST_CASE("vanalbada: equal values recover gradient", "[limiter]") {
    // vanalbada(a,a) = a*a*(2a)/(2a^2) = a
    REQUIRE(vanalbada(1.5, 1.5) == Approx(1.5));
}
```

- [ ] **Step 7: Build and run limiter tests**

```bash
cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[limiter]"
```

Expected: All 12 limiter tests pass.

- [ ] **Step 8: Run full test suite to verify no regressions**

```bash
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests
```

Expected: All existing tests still pass (muscl_reconstruct, hancock, hllc, solver tests all use the default minbee path).

- [ ] **Step 9: Commit**

```bash
git add src/euler/muscl.hpp tests/unit/test_euler.cpp
git commit -m "feat(muscl): rename minmod to minbee, add van Leer/superbee/van Albada limiters

Add four slope limiters following Toro Ch. 13 nomenclature with functor
wrappers for template parameter use. Existing code unchanged via default
MinbeeLimiter parameter."
```

---

## Task 2: Parameterize MUSCL Reconstruct and Hancock with Limiter Template

**Files:**
- Modify: `src/euler/muscl.hpp`
- Modify: `src/euler/hancock.hpp`
- Modify: `tests/unit/test_euler.cpp`

- [ ] **Step 1: Update `muscl_reconstruct_x` signature and body**

In `src/euler/muscl.hpp`, change `muscl_reconstruct_x`:

```cpp
// Old:
template <typename Real, typename Ptr>
HD_FUNC void muscl_reconstruct_x(
    GridViewBase<Real, 4, Ptr> grid, int i, int j,
    Vec<Real, 4>& q_left, Vec<Real, 4>& q_right)
{
    for (int v = 0; v < 4; ++v) {
        Real u_im1 = grid(i - 1, j, v);
        Real u_i   = grid(i,     j, v);
        Real u_ip1 = grid(i + 1, j, v);

        Real backward = u_i - u_im1;
        Real forward  = u_ip1 - u_i;
        Real slope    = minbee(backward, forward);

        q_left[v]  = u_i - Real(0.5) * slope;
        q_right[v] = u_i + Real(0.5) * slope;
    }
}

// New:
template <typename Real, typename Ptr, typename Limiter = MinbeeLimiter>
HD_FUNC void muscl_reconstruct_x(
    GridViewBase<Real, 4, Ptr> grid, int i, int j,
    Vec<Real, 4>& q_left, Vec<Real, 4>& q_right,
    Limiter lim = {})
{
    for (int v = 0; v < 4; ++v) {
        Real u_im1 = grid(i - 1, j, v);
        Real u_i   = grid(i,     j, v);
        Real u_ip1 = grid(i + 1, j, v);

        Real backward = u_i - u_im1;
        Real forward  = u_ip1 - u_i;
        Real slope    = lim(backward, forward);

        q_left[v]  = u_i - Real(0.5) * slope;
        q_right[v] = u_i + Real(0.5) * slope;
    }
}
```

- [ ] **Step 2: Update `muscl_hancock_x` signature and body**

In `src/euler/hancock.hpp`, change `muscl_hancock_x`:

```cpp
// Old:
template <typename Real, typename Ptr>
HD_FUNC void muscl_hancock_x(
    GridViewBase<Real, 4, Ptr> grid, int i, int j,
    Real dt, Real gamma,
    Vec<Real, 4>& q_left, Vec<Real, 4>& q_right)
{
    // Step 1: MUSCL reconstruction
    muscl_reconstruct_x(grid, i, j, q_left, q_right);

// New:
template <typename Real, typename Ptr, typename Limiter = MinbeeLimiter>
HD_FUNC void muscl_hancock_x(
    GridViewBase<Real, 4, Ptr> grid, int i, int j,
    Real dt, Real gamma,
    Vec<Real, 4>& q_left, Vec<Real, 4>& q_right,
    Limiter lim = {})
{
    // Step 1: MUSCL reconstruction
    muscl_reconstruct_x(grid, i, j, q_left, q_right, lim);
```

The rest of the function body is unchanged.

- [ ] **Step 3: Write test for MUSCL reconstruct with van Leer limiter**

In `tests/unit/test_euler.cpp`, add:

```cpp
TEST_CASE("muscl_reconstruct_x: van Leer on linear field", "[muscl]") {
    Grid2D<double, 4> grid(10, 1);
    grid.dx = 0.1;
    grid.dy = 0.1;
    auto gv = grid.view();

    for (int i = -2; i < 12; ++i) {
        gv(i, 0, RHO)  = 1.0 + 0.1 * i;
        gv(i, 0, RHOU) = 0.0;
        gv(i, 0, RHOV) = 0.0;
        gv(i, 0, EN)   = 2.5;
    }

    Vec<double, 4> qL{}, qR{};
    muscl_reconstruct_x(grid.view(), 5, 0, qL, qR, VanLeerLimiter{});

    // Cell 5: rho=1.5, backward=forward=0.1
    // vanleer(0.1, 0.1) = 0.1 (exact gradient recovery)
    REQUIRE(qL[RHO] == Approx(1.45).epsilon(1e-12));
    REQUIRE(qR[RHO] == Approx(1.55).epsilon(1e-12));
}
```

- [ ] **Step 4: Build and run all tests**

```bash
cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests
```

Expected: All tests pass. Existing muscl/hancock/solver tests use default `MinbeeLimiter` and are identical to before.

- [ ] **Step 5: Commit**

```bash
git add src/euler/muscl.hpp src/euler/hancock.hpp tests/unit/test_euler.cpp
git commit -m "feat(muscl): parameterize reconstruct/hancock with Limiter template

Default MinbeeLimiter preserves backward compatibility. All existing call
sites compile unchanged."
```

---

## Task 3: Exact Riemann Solver — Pressure Iteration

**Files:**
- Create: `src/euler/exact_riemann.hpp`
- Modify: `tests/unit/test_euler.cpp`

- [ ] **Step 1: Write the failing test for `exact_riemann_solve`**

In `tests/unit/test_euler.cpp`, add at the top with other includes:

```cpp
#include "euler/exact_riemann.hpp"
```

Add the test:

```cpp
TEST_CASE("exact_riemann_solve: Sod p_star and u_star", "[exact]") {
    double gamma = 1.4;
    double p_star = 0.0, u_star = 0.0;

    exact_riemann_solve(gamma,
        1.0, 0.0, 1.0,      // rhoL, uL, pL
        0.125, 0.0, 0.1,    // rhoR, uR, pR
        p_star, u_star);

    REQUIRE(p_star == Approx(0.30313).epsilon(1e-4));
    REQUIRE(u_star == Approx(0.92745).epsilon(1e-4));
}
```

- [ ] **Step 2: Verify test fails (file does not exist yet)**

```bash
cmake --build build 2>&1 | head -20
```

Expected: Compilation error — `exact_riemann.hpp` not found.

- [ ] **Step 3: Implement `exact_riemann.hpp` — helper functions + pressure iteration**

Create `src/euler/exact_riemann.hpp`:

```cpp
#pragma once

#include "core/types.hpp"
#include "core/eos.hpp"

#include <cmath>
#include <algorithm>

namespace hrsc {

// --- Internal helpers (Toro Ch. 4) ---

// Pressure function f_K for one side (K = L or R)
template <typename Real>
HD_FUNC Real riemann_fK(Real p, Real rhoK, Real pK, Real aK, Real gamma) {
    if (p > pK) {
        // Shock wave
        Real AK = Real(2) / ((gamma + Real(1)) * rhoK);
        Real BK = pK * (gamma - Real(1)) / (gamma + Real(1));
        return (p - pK) * std::sqrt(AK / (p + BK));
    } else {
        // Rarefaction wave
        Real gm1 = gamma - Real(1);
        Real exp = gm1 / (Real(2) * gamma);
        return (Real(2) * aK / gm1) * (std::pow(p / pK, exp) - Real(1));
    }
}

// Derivative df_K/dp for one side
template <typename Real>
HD_FUNC Real riemann_fK_deriv(Real p, Real rhoK, Real pK, Real aK, Real gamma) {
    if (p > pK) {
        // Shock wave
        Real AK = Real(2) / ((gamma + Real(1)) * rhoK);
        Real BK = pK * (gamma - Real(1)) / (gamma + Real(1));
        Real sqrtAB = std::sqrt(AK / (p + BK));
        return sqrtAB * (Real(1) - (p - pK) / (Real(2) * (p + BK)));
    } else {
        // Rarefaction wave
        Real gm1 = gamma - Real(1);
        Real exp = -(gamma + Real(1)) / (Real(2) * gamma);
        return (Real(1) / (rhoK * aK)) * std::pow(p / pK, exp);
    }
}

// Pressure iteration: Newton-Raphson for p_star, then compute u_star
template <typename Real>
HD_FUNC void exact_riemann_solve(
    Real gamma,
    Real rhoL, Real uL, Real pL,
    Real rhoR, Real uR, Real pR,
    Real& p_star, Real& u_star)
{
    Real aL = sound_speed(rhoL, pL, gamma);
    Real aR = sound_speed(rhoR, pR, gamma);
    Real gm1 = gamma - Real(1);

    // Vacuum check: if velocity difference exceeds critical value,
    // no star state exists
    if (Real(2) * aL / gm1 + Real(2) * aR / gm1 <= uR - uL) {
        p_star = Real(0);
        u_star = Real(0.5) * (uL + uR);
        return;
    }

    // Initial guess: PVRS (two-rarefaction approximation, Toro eq. 4.46)
    Real p0 = std::max(
        Real(0.5) * (pL + pR) - Real(0.125) * (uR - uL) * (rhoL + rhoR) * (aL + aR),
        Real(1e-14));

    // Newton-Raphson iteration
    Real p_scale = Real(0.5) * (pL + pR);
    Real tol = std::max(Real(1e-8) * p_scale, Real(1e-15));
    Real p_old = p0;

    for (int iter = 0; iter < 50; ++iter) {
        Real fL = riemann_fK(p_old, rhoL, pL, aL, gamma);
        Real fR = riemann_fK(p_old, rhoR, pR, aR, gamma);
        Real f  = fL + fR + (uR - uL);

        if (std::abs(f) < tol) break;

        Real dfL = riemann_fK_deriv(p_old, rhoL, pL, aL, gamma);
        Real dfR = riemann_fK_deriv(p_old, rhoR, pR, aR, gamma);
        Real df  = dfL + dfR;

        Real p_new = p_old - f / df;
        p_new = std::max(p_new, Real(1e-14));  // positivity clamp
        p_old = p_new;
    }

    p_star = p_old;

    // Contact velocity (Toro eq. 4.9)
    Real fL = riemann_fK(p_star, rhoL, pL, aL, gamma);
    Real fR = riemann_fK(p_star, rhoR, pR, aR, gamma);
    u_star = Real(0.5) * (uL + uR) + Real(0.5) * (fR - fL);
}

} // namespace hrsc
```

- [ ] **Step 4: Build and run the test**

```bash
cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[exact]"
```

Expected: Sod p_star/u_star test passes.

- [ ] **Step 5: Add tests for Toro Tests 2–5 p_star/u_star**

In `tests/unit/test_euler.cpp`, add:

```cpp
TEST_CASE("exact_riemann_solve: Toro Test 2 (123 problem)", "[exact]") {
    double gamma = 1.4;
    double p_star = 0.0, u_star = 0.0;
    exact_riemann_solve(gamma,
        1.0, -2.0, 0.4,
        1.0,  2.0, 0.4,
        p_star, u_star);
    REQUIRE(p_star == Approx(0.00189).epsilon(1e-2));
    REQUIRE(u_star == Approx(0.0).margin(1e-6));
}

TEST_CASE("exact_riemann_solve: Toro Test 3 (blast wave)", "[exact]") {
    double gamma = 1.4;
    double p_star = 0.0, u_star = 0.0;
    exact_riemann_solve(gamma,
        1.0, 0.0, 1000.0,
        1.0, 0.0, 0.01,
        p_star, u_star);
    REQUIRE(p_star == Approx(460.894).epsilon(1e-3));
    REQUIRE(u_star == Approx(19.5975).epsilon(1e-3));
}

TEST_CASE("exact_riemann_solve: Toro Test 4 (Lax)", "[exact]") {
    double gamma = 1.4;
    double p_star = 0.0, u_star = 0.0;
    exact_riemann_solve(gamma,
        0.445, 0.698, 3.528,
        0.5,   0.0,   0.571,
        p_star, u_star);
    REQUIRE(p_star == Approx(1.12838).epsilon(1e-3));
    REQUIRE(u_star == Approx(0.51058).epsilon(1e-3));
}

TEST_CASE("exact_riemann_solve: vacuum check", "[exact]") {
    double gamma = 1.4;
    double p_star = -1.0, u_star = -1.0;
    // Two flows diverging fast enough to generate vacuum
    exact_riemann_solve(gamma,
        1.0, -100.0, 0.4,
        1.0,  100.0, 0.4,
        p_star, u_star);
    REQUIRE(p_star == Approx(0.0).margin(1e-12));
    REQUIRE(u_star == Approx(0.0).margin(1e-6));
}
```

- [ ] **Step 6: Build and run all exact tests**

```bash
cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[exact]"
```

Expected: All 5 exact Riemann tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/euler/exact_riemann.hpp tests/unit/test_euler.cpp
git commit -m "feat(euler): add exact Riemann solver pressure iteration

Newton-Raphson with PVRS initial guess, positivity clamp, absolute
tolerance floor, and vacuum check. Verified against Toro Tests 1-4."
```

---

## Task 4: Exact Riemann Solver — Sampling Function

**Files:**
- Modify: `src/euler/exact_riemann.hpp`
- Modify: `tests/unit/test_euler.cpp`

- [ ] **Step 1: Write the failing test for `exact_riemann_sample`**

In `tests/unit/test_euler.cpp`, add:

```cpp
TEST_CASE("exact_riemann_sample: Sod at multiple points", "[exact]") {
    double gamma = 1.4;
    double rho, u, p;

    // Left of all waves: x/t = -1.0 → undisturbed left state
    exact_riemann_sample(gamma, -1.0,
        1.0, 0.0, 1.0,  0.125, 0.0, 0.1,
        rho, u, p);
    REQUIRE(rho == Approx(1.0).epsilon(1e-6));
    REQUIRE(u   == Approx(0.0).margin(1e-10));
    REQUIRE(p   == Approx(1.0).epsilon(1e-6));

    // Right of all waves: x/t = 2.0 → undisturbed right state
    exact_riemann_sample(gamma, 2.0,
        1.0, 0.0, 1.0,  0.125, 0.0, 0.1,
        rho, u, p);
    REQUIRE(rho == Approx(0.125).epsilon(1e-6));
    REQUIRE(u   == Approx(0.0).margin(1e-10));
    REQUIRE(p   == Approx(0.1).epsilon(1e-6));

    // At the contact: x/t ≈ u_star = 0.92745, rho should be left-star or right-star
    exact_riemann_sample(gamma, 0.5,
        1.0, 0.0, 1.0,  0.125, 0.0, 0.1,
        rho, u, p);
    REQUIRE(rho > 0.1);
    REQUIRE(rho < 1.0);
    REQUIRE(p == Approx(0.30313).epsilon(1e-3));
    REQUIRE(u == Approx(0.92745).epsilon(1e-3));
}
```

- [ ] **Step 2: Implement `exact_riemann_sample`**

In `src/euler/exact_riemann.hpp`, add after `exact_riemann_solve`:

```cpp
// Sample the exact Riemann solution at a given x/t value
template <typename Real>
HD_FUNC void exact_riemann_sample(
    Real gamma, Real x_over_t,
    Real rhoL, Real uL, Real pL,
    Real rhoR, Real uR, Real pR,
    Real& rho, Real& u, Real& p)
{
    Real aL = sound_speed(rhoL, pL, gamma);
    Real aR = sound_speed(rhoR, pR, gamma);
    Real gm1 = gamma - Real(1);
    Real gp1 = gamma + Real(1);

    // Get star-state pressure and velocity
    Real p_star, u_star;
    exact_riemann_solve(gamma, rhoL, uL, pL, rhoR, uR, pR, p_star, u_star);

    // Vacuum state
    if (p_star < Real(1e-14)) {
        rho = Real(0);
        u   = Real(0.5) * (uL + uR);
        p   = Real(0);
        return;
    }

    if (x_over_t <= u_star) {
        // Left of contact — left wave
        if (p_star > pL) {
            // Left shock
            Real SL = uL - aL * std::sqrt((gp1 * p_star / pL + gm1) / (Real(2) * gamma));
            if (x_over_t <= SL) {
                // Undisturbed left
                rho = rhoL; u = uL; p = pL;
            } else {
                // Left star state
                Real rho_starL = rhoL * ((p_star / pL + gm1 / gp1) /
                                         (gm1 / gp1 * p_star / pL + Real(1)));
                rho = rho_starL; u = u_star; p = p_star;
            }
        } else {
            // Left rarefaction
            Real aL_star = aL * std::pow(p_star / pL, gm1 / (Real(2) * gamma));
            Real SHL = uL - aL;          // head speed
            Real STL = u_star - aL_star;  // tail speed

            if (x_over_t <= SHL) {
                // Undisturbed left
                rho = rhoL; u = uL; p = pL;
            } else if (x_over_t <= STL) {
                // Inside left rarefaction fan
                Real ratio = (Real(2) / gp1) + (gm1 / (gp1 * aL)) * (uL - x_over_t);
                rho = rhoL * std::pow(ratio, Real(2) / gm1);
                u   = (Real(2) / gp1) * (aL + gm1 * Real(0.5) * uL + x_over_t);
                p   = pL * std::pow(ratio, Real(2) * gamma / gm1);
            } else {
                // Left star state (behind rarefaction tail)
                Real rho_starL = rhoL * std::pow(p_star / pL, Real(1) / gamma);
                rho = rho_starL; u = u_star; p = p_star;
            }
        }
    } else {
        // Right of contact — right wave
        if (p_star > pR) {
            // Right shock
            Real SR = uR + aR * std::sqrt((gp1 * p_star / pR + gm1) / (Real(2) * gamma));
            if (x_over_t >= SR) {
                // Undisturbed right
                rho = rhoR; u = uR; p = pR;
            } else {
                // Right star state
                Real rho_starR = rhoR * ((p_star / pR + gm1 / gp1) /
                                         (gm1 / gp1 * p_star / pR + Real(1)));
                rho = rho_starR; u = u_star; p = p_star;
            }
        } else {
            // Right rarefaction
            Real aR_star = aR * std::pow(p_star / pR, gm1 / (Real(2) * gamma));
            Real SHR = uR + aR;          // head speed
            Real STR = u_star + aR_star;  // tail speed

            if (x_over_t >= SHR) {
                // Undisturbed right
                rho = rhoR; u = uR; p = pR;
            } else if (x_over_t >= STR) {
                // Inside right rarefaction fan
                Real ratio = (Real(2) / gp1) - (gm1 / (gp1 * aR)) * (uR - x_over_t);
                rho = rhoR * std::pow(ratio, Real(2) / gm1);
                u   = (Real(2) / gp1) * (-aR + gm1 * Real(0.5) * uR + x_over_t);
                p   = pR * std::pow(ratio, Real(2) * gamma / gm1);
            } else {
                // Right star state
                Real rho_starR = rhoR * std::pow(p_star / pR, Real(1) / gamma);
                rho = rho_starR; u = u_star; p = p_star;
            }
        }
    }
}
```

- [ ] **Step 3: Build and run sample tests**

```bash
cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[exact]"
```

Expected: All exact Riemann tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/euler/exact_riemann.hpp tests/unit/test_euler.cpp
git commit -m "feat(euler): add exact Riemann solution sampling function

Samples the self-similar solution at x/t. Handles left/right shock and
rarefaction waves, star regions, and vacuum state."
```

---

## Task 5: Error Norms

**Files:**
- Create: `src/utils/error_norms.hpp`
- Modify: `tests/unit/test_euler.cpp`

- [ ] **Step 1: Write the failing tests**

In `tests/unit/test_euler.cpp`, add include:

```cpp
#include "utils/error_norms.hpp"
```

Add tests:

```cpp
TEST_CASE("compute_error: zero error for identical arrays", "[norms]") {
    double a[] = {1.0, 2.0, 3.0};
    double b[] = {1.0, 2.0, 3.0};
    auto err = compute_error(a, b, 3, 1.0);
    REQUIRE(err.L1   == Approx(0.0).margin(1e-15));
    REQUIRE(err.L2   == Approx(0.0).margin(1e-15));
    REQUIRE(err.Linf == Approx(0.0).margin(1e-15));
}

TEST_CASE("compute_error: known error values", "[norms]") {
    double num[]   = {1.0, 2.0, 3.0};
    double exact[] = {1.1, 2.2, 3.3};
    // |diff| = {0.1, 0.2, 0.3}, dV = 0.5
    auto err = compute_error(num, exact, 3, 0.5);
    // L1 = (0.1 + 0.2 + 0.3) * 0.5 = 0.3
    REQUIRE(err.L1 == Approx(0.3).epsilon(1e-12));
    // L2 = sqrt((0.01 + 0.04 + 0.09) * 0.5) = sqrt(0.07)
    REQUIRE(err.L2 == Approx(std::sqrt(0.07)).epsilon(1e-12));
    // Linf = 0.3
    REQUIRE(err.Linf == Approx(0.3).epsilon(1e-12));
}

TEST_CASE("compute_error: norm inequality L1 <= sqrt(n*dV)*L2", "[norms]") {
    double num[]   = {1.0, 3.0, 5.0, 7.0};
    double exact[] = {1.1, 2.5, 5.3, 6.8};
    double dV = 0.25;
    auto err = compute_error(num, exact, 4, dV);
    REQUIRE(err.L1 <= std::sqrt(4.0 * dV) * err.L2 + 1e-12);
}
```

- [ ] **Step 2: Implement `error_norms.hpp`**

Create `src/utils/error_norms.hpp`:

```cpp
#pragma once

#include <cmath>
#include <algorithm>

namespace hrsc {

template <typename Real>
struct ErrorNorms { Real L1, L2, Linf; };

// Dimension-agnostic error norm computation.
// dV = dx for 1D, dx*dy for 2D.
template <typename Real>
ErrorNorms<Real> compute_error(const Real* numerical, const Real* exact,
                               int total_cells, Real dV)
{
    Real sum_L1  = Real(0);
    Real sum_L2  = Real(0);
    Real max_err = Real(0);

    for (int i = 0; i < total_cells; ++i) {
        Real diff = std::abs(numerical[i] - exact[i]);
        sum_L1  += diff;
        sum_L2  += diff * diff;
        max_err  = std::max(max_err, diff);
    }

    return {sum_L1 * dV, std::sqrt(sum_L2 * dV), max_err};
}

} // namespace hrsc
```

- [ ] **Step 3: Build and run norms tests**

```bash
cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[norms]"
```

Expected: All 3 tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/utils/error_norms.hpp tests/unit/test_euler.cpp
git commit -m "feat(utils): add dimension-agnostic L1/L2/Linf error norms

Single-pass computation. Uses dV parameter for 1D (dx) or 2D (dx*dy)."
```

---

## Task 6: Binary IO

**Files:**
- Create: `src/utils/io.hpp`
- Modify: `tests/unit/test_euler.cpp`

- [ ] **Step 1: Write the failing round-trip test**

In `tests/unit/test_euler.cpp`, add include:

```cpp
#include "utils/io.hpp"
```

Add test:

```cpp
TEST_CASE("binary IO: write and read back match", "[io]") {
    // Create a small 4x3 grid with known values
    Grid2D<double, 4> grid(4, 3);
    grid.dx = 0.25;
    grid.dy = 0.5;
    auto gv = grid.view();

    for (int j = 0; j < 3; ++j)
        for (int i = 0; i < 4; ++i)
            for (int v = 0; v < 4; ++v)
                gv(i, j, v) = 100.0 * j + 10.0 * i + v + 0.1;

    std::string fname = "test_io_roundtrip.hrsc";
    write_binary<double, 4>(fname, grid.view(), 4, 3, 0.25, 0.5, 1.234);

    // Read header
    int nx2, ny2, nvars2, prec2;
    double time2, dx2, dy2;
    read_binary_header(fname, nx2, ny2, nvars2, prec2, time2, dx2, dy2);
    REQUIRE(nx2 == 4);
    REQUIRE(ny2 == 3);
    REQUIRE(nvars2 == 4);
    REQUIRE(prec2 == 8);  // sizeof(double)
    REQUIRE(time2 == Approx(1.234));
    REQUIRE(dx2 == Approx(0.25));
    REQUIRE(dy2 == Approx(0.5));

    // Read data
    Grid2D<double, 4> grid2(4, 3);
    grid2.dx = dx2;
    grid2.dy = dy2;
    read_binary_data<double, 4>(fname, grid2.view(), 4, 3);

    auto gv2 = grid2.view();
    for (int j = 0; j < 3; ++j)
        for (int i = 0; i < 4; ++i)
            for (int v = 0; v < 4; ++v)
                REQUIRE(gv2(i, j, v) == Approx(gv(i, j, v)).margin(1e-15));

    std::remove(fname.c_str());
}
```

- [ ] **Step 2: Implement `io.hpp`**

Create `src/utils/io.hpp`:

```cpp
#pragma once

#include "core/grid.hpp"

#include <string>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <stdexcept>

// Ensure little-endian (both x86 Windows and x86_64 Linux satisfy this)
#if defined(__BYTE_ORDER__) && __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
    #error "Binary IO assumes little-endian architecture"
#endif

namespace hrsc {

template <typename Real, int NVars>
void write_binary(const std::string& filename,
                  ConstGridView<Real, NVars> grid,
                  int nx, int ny, Real dx, Real dy, Real time)
{
    FILE* fp = std::fopen(filename.c_str(), "wb");
    if (!fp) throw std::runtime_error("Cannot open file for writing: " + filename);

    // --- 64-byte header ---
    char header[64];
    std::memset(header, 0, 64);

    // Magic
    std::memcpy(header + 0, "HRSC", 4);
    // nx, ny, nvars, precision_tag as int32
    int32_t inx = static_cast<int32_t>(nx);
    int32_t iny = static_cast<int32_t>(ny);
    int32_t invars = static_cast<int32_t>(NVars);
    int32_t iprec = static_cast<int32_t>(sizeof(Real));
    std::memcpy(header + 4,  &inx, 4);
    std::memcpy(header + 8,  &iny, 4);
    std::memcpy(header + 12, &invars, 4);
    std::memcpy(header + 16, &iprec, 4);
    // time, dx, dy as float64
    double dtime = static_cast<double>(time);
    double ddx   = static_cast<double>(dx);
    double ddy   = static_cast<double>(dy);
    std::memcpy(header + 20, &dtime, 8);
    std::memcpy(header + 28, &ddx, 8);
    std::memcpy(header + 36, &ddy, 8);

    std::fwrite(header, 1, 64, fp);

    // --- Row-by-row data write (no buffer allocation) ---
    for (int j = 0; j < ny; ++j) {
        const Real* row_start = grid.data
            + (static_cast<size_t>(j + grid.ng) * grid.nx_total() + grid.ng) * NVars;
        std::fwrite(row_start, sizeof(Real), static_cast<size_t>(nx) * NVars, fp);
    }

    std::fclose(fp);
}

inline void read_binary_header(const std::string& filename,
                               int& nx, int& ny, int& nvars, int& precision_tag,
                               double& time, double& dx, double& dy)
{
    FILE* fp = std::fopen(filename.c_str(), "rb");
    if (!fp) throw std::runtime_error("Cannot open file for reading: " + filename);

    char header[64];
    if (std::fread(header, 1, 64, fp) != 64) {
        std::fclose(fp);
        throw std::runtime_error("Failed to read 64-byte header from: " + filename);
    }

    // Verify magic
    if (std::memcmp(header, "HRSC", 4) != 0) {
        std::fclose(fp);
        throw std::runtime_error("Invalid magic in binary file: " + filename);
    }

    int32_t inx, iny, invars, iprec;
    std::memcpy(&inx,    header + 4,  4);
    std::memcpy(&iny,    header + 8,  4);
    std::memcpy(&invars, header + 12, 4);
    std::memcpy(&iprec,  header + 16, 4);
    std::memcpy(&time,   header + 20, 8);
    std::memcpy(&dx,     header + 28, 8);
    std::memcpy(&dy,     header + 36, 8);

    nx = static_cast<int>(inx);
    ny = static_cast<int>(iny);
    nvars = static_cast<int>(invars);
    precision_tag = static_cast<int>(iprec);

    std::fclose(fp);
}

template <typename Real, int NVars>
void read_binary_data(const std::string& filename,
                      GridView<Real, NVars> grid,
                      int nx, int ny)
{
    FILE* fp = std::fopen(filename.c_str(), "rb");
    if (!fp) throw std::runtime_error("Cannot open file for reading: " + filename);

    // Skip 64-byte header
    std::fseek(fp, 64, SEEK_SET);

    // Read row-by-row into grid (filling physical cells, skipping ghosts)
    for (int j = 0; j < ny; ++j) {
        Real* row_start = grid.data
            + (static_cast<size_t>(j + grid.ng) * grid.nx_total() + grid.ng) * NVars;
        if (std::fread(row_start, sizeof(Real), static_cast<size_t>(nx) * NVars, fp)
                != static_cast<size_t>(nx) * NVars) {
            std::fclose(fp);
            throw std::runtime_error("Failed to read data row from: " + filename);
        }
    }

    std::fclose(fp);
}

} // namespace hrsc
```

- [ ] **Step 3: Build and run IO test**

```bash
cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[io]"
```

Expected: Round-trip test passes.

- [ ] **Step 4: Add file-size verification test**

In `tests/unit/test_euler.cpp`, add:

```cpp
TEST_CASE("binary IO: file size is correct", "[io]") {
    Grid2D<double, 4> grid(10, 5);
    grid.dx = 0.1;
    grid.dy = 0.2;
    auto gv = grid.view();
    for (int j = 0; j < 5; ++j)
        for (int i = 0; i < 10; ++i)
            for (int v = 0; v < 4; ++v)
                gv(i, j, v) = 1.0;

    std::string fname = "test_io_size.hrsc";
    write_binary<double, 4>(fname, grid.view(), 10, 5, 0.1, 0.2, 0.0);

    FILE* fp = std::fopen(fname.c_str(), "rb");
    std::fseek(fp, 0, SEEK_END);
    long size = std::ftell(fp);
    std::fclose(fp);

    // 64 header + 10 * 5 * 4 * 8 bytes = 64 + 1600 = 1664
    REQUIRE(size == 1664);
    std::remove(fname.c_str());
}
```

- [ ] **Step 5: Build, run, commit**

```bash
cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[io]"
git add src/utils/io.hpp tests/unit/test_euler.cpp
git commit -m "feat(utils): add binary IO with 64-byte header

Row-by-row write avoids buffer allocation. Header includes nx, ny, nvars,
precision tag, time, dx, dy. Little-endian enforced via static assert."
```

---

## Task 7: Config `get_int_list` + Convergence Config

**Files:**
- Modify: `src/utils/config.hpp`
- Create: `tests/cases/toro_1d/convergence_sod.cfg`
- Modify: `tests/unit/test_euler.cpp`

- [ ] **Step 1: Write the failing test for `get_int_list`**

In `tests/unit/test_euler.cpp`, add:

```cpp
TEST_CASE("Config::get_int_list parses comma-separated values", "[config]") {
    std::istringstream ss("resolutions = 50,100,200,400,800\n");
    Config cfg(ss);
    auto list = cfg.get_int_list("resolutions");
    REQUIRE(list.size() == 5);
    REQUIRE(list[0] == 50);
    REQUIRE(list[1] == 100);
    REQUIRE(list[2] == 200);
    REQUIRE(list[3] == 400);
    REQUIRE(list[4] == 800);
}

TEST_CASE("Config::get_int_list handles spaces", "[config]") {
    std::istringstream ss("vals = 10 , 20 , 30\n");
    Config cfg(ss);
    auto list = cfg.get_int_list("vals");
    REQUIRE(list.size() == 3);
    REQUIRE(list[0] == 10);
    REQUIRE(list[1] == 20);
    REQUIRE(list[2] == 30);
}
```

- [ ] **Step 2: Implement `get_int_list` in `config.hpp`**

In `src/utils/config.hpp`, add inside the `Config` class (after `get_bool`), plus add `#include <vector>` at the top of the file:

```cpp
    std::vector<int> get_int_list(const std::string& key) const {
        auto it = m_entries.find(key);
        if (it == m_entries.end()) return {};
        std::vector<int> result;
        std::istringstream iss(it->second);
        std::string token;
        while (std::getline(iss, token, ',')) {
            std::string t = trim(token);
            if (!t.empty()) {
                result.push_back(std::stoi(t));
            }
        }
        return result;
    }
```

Also add `#include <vector>` to the includes at the top of the file.

- [ ] **Step 3: Create convergence config file**

Create `tests/cases/toro_1d/convergence_sod.cfg`:

```ini
# Grid convergence study — Sod shock tube
test = sod
mode = convergence
resolutions = 50,100,200,400,800
xmin = 0.0
xmax = 1.0
gamma = 1.4
cfl = 0.8
t_end = 0.25
x0 = 0.5
```

- [ ] **Step 4: Build, run, commit**

```bash
cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[config]"
git add src/utils/config.hpp tests/cases/toro_1d/convergence_sod.cfg tests/unit/test_euler.cpp
git commit -m "feat(config): add get_int_list for comma-separated integers

Needed for configurable convergence study resolutions."
```

---

## Task 8: Grid Convergence Mode in main.cpp

**Files:**
- Modify: `src/main.cpp`
- Modify: `src/euler/euler_solver.hpp` (1D constructor adds `xmin`)

This task updates the 1D constructor to accept `xmin`, updates existing call sites, and adds the `mode = convergence` path.

- [ ] **Step 1: Update `EulerSolver` 1D constructor to accept `xmin`**

In `src/euler/euler_solver.hpp`, change the constructor:

```cpp
// Old:
    EulerSolver(int nx, Real dx, Real gamma, Real cfl, Real t_end)
        : m_grid(nx, 1),
          m_gamma(gamma),
          m_cfl(cfl),
          m_t_end(t_end),
          m_time(Real(0)),
          m_step(0)
    {
        m_grid.dx = dx;
        m_grid.dy = dx;  // dummy for 1D
    }

// New:
    EulerSolver(int nx, Real dx, Real xmin, Real gamma, Real cfl, Real t_end)
        : m_grid(nx, 1),
          m_xmin(xmin),
          m_ymin(Real(0)),
          m_gamma(gamma),
          m_cfl(cfl),
          m_t_end(t_end),
          m_time(Real(0)),
          m_step(0)
    {
        m_grid.dx = dx;
        m_grid.dy = dx;  // dummy for 1D
    }
```

Add the new member variables to the private section:

```cpp
    Real m_xmin;
    Real m_ymin;
```

Add accessors:

```cpp
    Real xmin() const { return m_xmin; }
    Real ymin() const { return m_ymin; }
```

- [ ] **Step 2: Update test_euler.cpp constructor calls**

In `tests/unit/test_euler.cpp`, find all three `EulerSolver<double>` construction sites and add `0.0` for xmin:

```cpp
// Old (appears 3 times):
    EulerSolver<double> solver(nx, dx, 1.4, 0.8, 0.25);
// New:
    EulerSolver<double> solver(nx, dx, 0.0, 1.4, 0.8, 0.25);
```

- [ ] **Step 3: Build and run — verify no regressions**

```bash
cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests
```

Expected: All existing tests pass.

- [ ] **Step 4: Update `main.cpp` — add xmin to normal mode, add convergence mode**

Replace `src/main.cpp` with:

```cpp
#include "utils/config.hpp"
#include "core/eos.hpp"
#include "euler/euler_solver.hpp"
#include "euler/exact_riemann.hpp"
#include "utils/error_norms.hpp"
#include "toro_tests.hpp"

#include <iostream>
#include <iomanip>
#include <string>
#include <stdexcept>
#include <vector>
#include <cmath>

using namespace hrsc;

static void setup_ic(GridView<double, 4> gv, const std::string& test, double gamma) {
    if (test == "sod") {
        setup_sod(gv, gamma);
    } else if (test == "toro2") {
        setup_toro2(gv, gamma);
    } else if (test == "toro3") {
        setup_toro3(gv, gamma);
    } else if (test == "toro4") {
        setup_toro4(gv, gamma);
    } else if (test == "toro5") {
        setup_toro5(gv, gamma);
    } else {
        throw std::runtime_error("Unknown test: " + test);
    }
}

// Get left/right primitive states for a given test (for exact solver)
static void get_riemann_ic(const std::string& test,
                           double& rhoL, double& uL, double& pL,
                           double& rhoR, double& uR, double& pR,
                           double& x0) {
    x0 = 0.5;
    if (test == "sod") {
        rhoL = 1.0; uL = 0.0; pL = 1.0;
        rhoR = 0.125; uR = 0.0; pR = 0.1;
    } else if (test == "toro2") {
        rhoL = 1.0; uL = -2.0; pL = 0.4;
        rhoR = 1.0; uR =  2.0; pR = 0.4;
    } else if (test == "toro3") {
        rhoL = 1.0; uL = 0.0; pL = 1000.0;
        rhoR = 1.0; uR = 0.0; pR = 0.01;
    } else if (test == "toro4") {
        rhoL = 0.445; uL = 0.698; pL = 3.528;
        rhoR = 0.5;   uR = 0.0;   pR = 0.571;
    } else if (test == "toro5") {
        rhoL = 5.99924; uL = 19.5975;  pL = 460.894;
        rhoR = 5.99242; uR = -6.19633; pR = 46.0950;
    } else {
        throw std::runtime_error("Unknown test for convergence: " + test);
    }
}

static void run_convergence(const Config& cfg) {
    std::string test = cfg.get_string("test");
    double gamma = cfg.get_double("gamma", 1.4);
    double cfl   = cfg.get_double("cfl", 0.8);
    double t_end = cfg.get_double("t_end", 0.25);
    double xmin  = cfg.get_double("xmin", 0.0);
    double xmax  = cfg.get_double("xmax", 1.0);
    auto resolutions = cfg.get_int_list("resolutions");

    double rhoL, uL, pL, rhoR, uR, pR, x0;
    get_riemann_ic(test, rhoL, uL, pL, rhoR, uR, pR, x0);
    // Allow config override for x0
    x0 = cfg.get_double("x0", x0);

    std::cout << std::setprecision(6) << std::scientific;
    std::cout << "# N        dx            L1_rho        L2_rho        Linf_rho"
              << "      L1_u          L2_u          Linf_u"
              << "        L1_p          L2_p          Linf_p\n";

    for (int nx : resolutions) {
        double dx = (xmax - xmin) / nx;
        EulerSolver<double> solver(nx, dx, xmin, gamma, cfl, t_end);
        setup_ic(solver.grid_view(), test, gamma);
        solver.run();

        // Extract numerical solution and compute exact solution
        std::vector<double> num_rho(nx), num_u(nx), num_p(nx);
        std::vector<double> ext_rho(nx), ext_u(nx), ext_p(nx);

        auto gv = solver.grid_view();
        for (int i = 0; i < nx; ++i) {
            Vec<double, 4> cons;
            for (int v = 0; v < 4; ++v) cons[v] = gv(i, 0, v);
            Vec<double, 4> prim = cons_to_prim(cons, gamma);
            num_rho[i] = prim[PRHO];
            num_u[i]   = prim[VX];
            num_p[i]   = prim[PRES];

            double x = xmin + (i + 0.5) * dx;
            double xi = (x - x0) / t_end;
            double erho, eu, ep;
            exact_riemann_sample(gamma, xi,
                rhoL, uL, pL, rhoR, uR, pR,
                erho, eu, ep);
            ext_rho[i] = erho;
            ext_u[i]   = eu;
            ext_p[i]   = ep;
        }

        auto err_rho = compute_error(num_rho.data(), ext_rho.data(), nx, dx);
        auto err_u   = compute_error(num_u.data(),   ext_u.data(),   nx, dx);
        auto err_p   = compute_error(num_p.data(),   ext_p.data(),   nx, dx);

        std::cout << std::setw(6) << nx
                  << "  " << dx
                  << "  " << err_rho.L1 << "  " << err_rho.L2 << "  " << err_rho.Linf
                  << "  " << err_u.L1   << "  " << err_u.L2   << "  " << err_u.Linf
                  << "  " << err_p.L1   << "  " << err_p.L2   << "  " << err_p.Linf
                  << "\n";
    }
}

static void run_normal(const Config& cfg) {
    std::string test = cfg.get_string("test");
    int    nx    = cfg.get_int("nx", 200);
    double xmin  = cfg.get_double("xmin", 0.0);
    double xmax  = cfg.get_double("xmax", 1.0);
    double gamma = cfg.get_double("gamma", 1.4);
    double cfl   = cfg.get_double("cfl", 0.8);
    double t_end = cfg.get_double("t_end", 0.25);

    double dx = (xmax - xmin) / nx;

    EulerSolver<double> solver(nx, dx, xmin, gamma, cfl, t_end);
    setup_ic(solver.grid_view(), test, gamma);
    solver.run();

    std::cerr << "Finished: " << solver.step_count() << " steps, t = "
              << solver.time() << "\n";

    auto gv = solver.grid_view();
    std::cout << std::setprecision(17);
    for (int i = 0; i < nx; ++i) {
        double x = xmin + (i + 0.5) * dx;
        Vec<double, 4> cons;
        for (int v = 0; v < 4; ++v) cons[v] = gv(i, 0, v);
        Vec<double, 4> prim = cons_to_prim(cons, gamma);

        std::cout << x          << "\t"
                  << prim[PRHO] << "\t"
                  << prim[VX]   << "\t"
                  << prim[VY]   << "\t"
                  << prim[PRES] << "\n";
    }
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: hrsc <config_file>\n";
        return 1;
    }

    Config cfg(argv[1]);
    std::string mode = cfg.get_string("mode", "normal");

    if (mode == "convergence") {
        run_convergence(cfg);
    } else {
        run_normal(cfg);
    }

    return 0;
}
```

- [ ] **Step 5: Build and run convergence study**

```bash
cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/hrsc tests/cases/toro_1d/convergence_sod.cfg
```

Expected: Table of error norms at 5 resolutions. L1_rho should decrease roughly by factor ~2 between successive doublings.

- [ ] **Step 6: Verify normal mode still works**

```bash
PATH="/c/Strawberry/c/bin:$PATH" ./build/hrsc tests/cases/toro_1d/sod.cfg > /dev/null 2>&1
echo $?
```

Expected: Exit code 0. Normal output unchanged.

- [ ] **Step 7: Run full test suite**

```bash
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests
```

Expected: All tests pass.

- [ ] **Step 8: Commit**

```bash
git add src/euler/euler_solver.hpp src/main.cpp tests/unit/test_euler.cpp
git commit -m "feat: add grid convergence study mode in main.cpp

EulerSolver constructor now accepts xmin. Convergence mode reads
resolutions from config, runs solver at each, computes L1/L2/Linf
against exact Riemann solution."
```

---

## Task 9: Convergence Plotting Script

**Files:**
- Create: `scripts/convergence.py`

- [ ] **Step 1: Create `scripts/convergence.py`**

```python
#!/usr/bin/env python3
"""Grid convergence study: reads error norm table from stdin, produces log-log plot."""

import sys
import numpy as np
import matplotlib.pyplot as plt

def main():
    lines = []
    for line in sys.stdin:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        lines.append(line.split())

    if not lines:
        print("No data read from stdin. Pipe convergence output to this script.", file=sys.stderr)
        sys.exit(1)

    data = np.array(lines, dtype=float)
    N    = data[:, 0].astype(int)
    dx   = data[:, 1]
    # Columns: N, dx, L1_rho, L2_rho, Linf_rho, L1_u, L2_u, Linf_u, L1_p, L2_p, Linf_p
    L1_rho = data[:, 2]

    # Compute convergence order between successive resolutions
    print("Convergence orders (L1_rho):")
    for i in range(1, len(N)):
        order = np.log(L1_rho[i-1] / L1_rho[i]) / np.log(dx[i-1] / dx[i])
        print(f"  N={N[i-1]:4d} -> {N[i]:4d}:  p = {order:.3f}")

    # Fit global slope
    coeffs = np.polyfit(np.log(dx), np.log(L1_rho), 1)
    slope = coeffs[0]
    print(f"\nGlobal fit: L1_rho ~ dx^{slope:.3f}")

    # Plot
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.loglog(dx, L1_rho, 'bo-', label=f'L1 rho (slope={slope:.2f})')

    # Reference lines
    dx_ref = np.array([dx[0], dx[-1]])
    ax.loglog(dx_ref, L1_rho[0] * (dx_ref / dx[0])**1, 'k--', alpha=0.3, label='O(1)')
    ax.loglog(dx_ref, L1_rho[0] * (dx_ref / dx[0])**2, 'k:',  alpha=0.3, label='O(2)')

    ax.set_xlabel('dx')
    ax.set_ylabel('L1 error (density)')
    ax.set_title('Grid Convergence — Sod Shock Tube')
    ax.legend()
    ax.grid(True, which='both', alpha=0.3)

    plt.tight_layout()
    plt.savefig('output/convergence_sod.png', dpi=150)
    print(f"\nPlot saved to output/convergence_sod.png")
    plt.show()

if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Test the convergence pipeline end-to-end**

```bash
mkdir -p output
PATH="/c/Strawberry/c/bin:$PATH" ./build/hrsc tests/cases/toro_1d/convergence_sod.cfg | python scripts/convergence.py
```

Expected: Prints convergence orders (~1.0-1.5 for Sod), saves plot to `output/convergence_sod.png`.

- [ ] **Step 3: Commit**

```bash
git add scripts/convergence.py
git commit -m "feat(scripts): add convergence.py for log-log error plots

Reads error norm table from stdin, computes convergence orders, fits
global slope, produces publication-ready log-log plot."
```

---

## Task 10: Stationary Contact Discontinuity Test

**Files:**
- Modify: `tests/cases/toro_1d/toro_tests.hpp`
- Create: `tests/cases/toro_1d/stationary_contact.cfg`
- Modify: `src/main.cpp`
- Modify: `tests/unit/test_euler.cpp`

This test targets the `S_M = 0` FP edge case in HLLC. With `p_L = p_R` and `u_L = u_R = 0`, the contact wave speed is analytically zero — exactly on the boundary between the two star-region branches. FP round-off may produce `S_M = ±epsilon`, causing different code paths under `<` vs `<=`.

- [ ] **Step 1: Add `setup_stationary_contact` IC**

In `tests/cases/toro_1d/toro_tests.hpp`, add after `setup_toro5`:

```cpp
// Stationary contact discontinuity: S_M = 0 exactly
// Domain [0,1], x0=0.5, t_end=0.5
template <typename Real>
void setup_stationary_contact(GridView<Real, 4> grid, Real gamma) {
    setup_riemann(grid, gamma, Real(0.5),
                  Real(1.0), Real(0), Real(1.0),    // left: rho=1, u=0, p=1
                  Real(0.5), Real(0), Real(1.0));   // right: rho=0.5, u=0, p=1
}
```

- [ ] **Step 2: Create `stationary_contact.cfg`**

Create `tests/cases/toro_1d/stationary_contact.cfg`:

```ini
# Stationary contact discontinuity: S_M = 0, FP edge case
test = stationary_contact
nx = 200
xmin = 0.0
xmax = 1.0
gamma = 1.4
cfl = 0.8
t_end = 0.5
```

- [ ] **Step 3: Add `stationary_contact` to main.cpp test selection**

In `src/main.cpp`, add an `else if` branch after the `toro5` case:

```cpp
    } else if (test == "stationary_contact") {
        setup_stationary_contact(solver.grid_view(), gamma);
    } else {
```

- [ ] **Step 4: Write the failing tests**

In `tests/unit/test_euler.cpp`, add:

```cpp
TEST_CASE("Stationary contact IC", "[stationary_contact]") {
    using Real = double;
    Real gamma = 1.4;
    Grid2D<Real, 4> grid(200, 1);
    grid.dx = 1.0 / 200;
    grid.dy = grid.dx;
    auto gv = grid.view();

    setup_stationary_contact(gv, gamma);

    // Cell at i=50 (left side): rho=1, p=1
    Vec<Real, 4> cons_L;
    for (int v = 0; v < 4; ++v) cons_L[v] = gv(50, 0, v);
    auto prim_L = cons_to_prim(cons_L, gamma);
    REQUIRE(prim_L[PRHO] == Approx(1.0));
    REQUIRE(prim_L[PRES] == Approx(1.0));
    REQUIRE(prim_L[VX]   == Approx(0.0).margin(1e-15));

    // Cell at i=150 (right side): rho=0.5, p=1
    Vec<Real, 4> cons_R;
    for (int v = 0; v < 4; ++v) cons_R[v] = gv(150, 0, v);
    auto prim_R = cons_to_prim(cons_R, gamma);
    REQUIRE(prim_R[PRHO] == Approx(0.5));
    REQUIRE(prim_R[PRES] == Approx(1.0));
    REQUIRE(prim_R[VX]   == Approx(0.0).margin(1e-15));
}

TEST_CASE("Stationary contact: pressure stays uniform", "[stationary_contact]") {
    using Real = double;
    Real gamma = 1.4;
    int nx = 200;
    Real dx = 1.0 / nx;
    EulerSolver<Real> solver(nx, dx, gamma, 0.8, 0.5);
    setup_stationary_contact(solver.grid_view(), gamma);

    solver.run();

    auto gv = solver.grid_view();
    for (int i = 0; i < nx; ++i) {
        Vec<Real, 4> cons;
        for (int v = 0; v < 4; ++v) cons[v] = gv(i, 0, v);
        Real p = pressure(cons, gamma);
        // Pressure should stay ~1.0 everywhere (no spurious waves)
        REQUIRE(p == Approx(1.0).epsilon(0.05));
    }
}
```

- [ ] **Step 5: Run tests to verify they fail**

Run: `PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[stationary_contact]" -v`

Expected: FAIL — `setup_stationary_contact` not defined yet (or compile error).

- [ ] **Step 6: Build and run tests**

```bash
cmake -B build -S . -G Ninja && cmake --build build && PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[stationary_contact]" -v
```

Expected: All stationary contact tests PASS.

- [ ] **Step 7: Commit**

```bash
git add tests/cases/toro_1d/toro_tests.hpp tests/cases/toro_1d/stationary_contact.cfg src/main.cpp tests/unit/test_euler.cpp
git commit -m "feat: add stationary contact discontinuity test (S_M=0 edge case)

Targets the <= vs < FP sensitivity in HLLC flux selection.
Density jump 1.0→0.5 with uniform p=1, u=0 gives S_M=0 analytically."
```

---

## Task 11: Python Analysis Scripts

**Files:**
- Create: `analysis/compare.py`
- Create: `analysis/plot_1d.py`
- Create: `analysis/requirements.txt`

These scripts load binary output from the C++ solver and produce error norms and publication-ready plots. They reuse the exact Riemann solver logic from `scripts/verify_toro.py`.

- [ ] **Step 1: Create `analysis/requirements.txt`**

Create `analysis/requirements.txt`:

```
numpy>=1.21
matplotlib>=3.5
```

- [ ] **Step 2: Create `analysis/compare.py`**

Create `analysis/compare.py`:

```python
#!/usr/bin/env python3
"""
Load binary output files and compute error norms against exact Riemann solutions.
Usage: python analysis/compare.py output/sod.bin --gamma 1.4 --x0 0.5 --t-end 0.25 \
       --rhoL 1.0 --uL 0.0 --pL 1.0 --rhoR 0.125 --uR 0.0 --pR 0.1
"""
import argparse
import struct
import numpy as np
import sys
from pathlib import Path

# Add project root so we can import from scripts
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.verify_toro import exact_riemann


def read_binary(filename):
    """Read binary file with 64-byte HRSC header."""
    with open(filename, 'rb') as f:
        header = f.read(64)
        magic = header[0:4].decode('ascii')
        if magic != 'HRSC':
            raise ValueError(f"Bad magic: {magic!r}, expected 'HRSC'")
        nx, ny, nvars, prec_tag = struct.unpack('<4i', header[4:20])
        time, dx, dy = struct.unpack('<3d', header[20:44])
        dtype = '<f4' if prec_tag == 4 else '<f8'
        data = np.fromfile(f, dtype=dtype).reshape(ny, nx, nvars)
    return data, nx, ny, nvars, time, dx, dy


def compute_norms(numerical, exact, dx):
    """Compute L1, L2, Linf error norms."""
    diff = np.abs(numerical - exact)
    L1 = np.sum(diff) * dx
    L2 = np.sqrt(np.sum(diff**2) * dx)
    Linf = np.max(diff)
    return L1, L2, Linf


def main():
    parser = argparse.ArgumentParser(description="Compare binary output to exact Riemann solution")
    parser.add_argument("binfile", help="Path to .bin output file")
    parser.add_argument("--gamma", type=float, default=1.4)
    parser.add_argument("--x0", type=float, default=0.5)
    parser.add_argument("--t-end", type=float, required=True)
    parser.add_argument("--rhoL", type=float, required=True)
    parser.add_argument("--uL", type=float, required=True)
    parser.add_argument("--pL", type=float, required=True)
    parser.add_argument("--rhoR", type=float, required=True)
    parser.add_argument("--uR", type=float, required=True)
    parser.add_argument("--pR", type=float, required=True)
    args = parser.parse_args()

    data, nx, ny, nvars, time, dx, dy = read_binary(args.binfile)

    # Extract 1D slice (row 0 for 1D data)
    rho_num = data[0, :, 0]
    # cons_to_prim: rhou/rho = u, p = (gamma-1)*(E - 0.5*rho*(u^2+v^2))
    rhou = data[0, :, 1]
    rhov = data[0, :, 2]
    E    = data[0, :, 3]
    rho  = data[0, :, 0]
    u_num = rhou / rho
    v_num = rhov / rho
    p_num = (args.gamma - 1.0) * (E - 0.5 * rho * (u_num**2 + v_num**2))

    # Cell centers
    x = np.array([(i + 0.5) * dx for i in range(nx)])

    # Exact solution
    rho_ex, u_ex, p_ex, _ = exact_riemann(
        x, args.t_end, args.gamma, args.x0,
        args.rhoL, args.uL, args.pL,
        args.rhoR, args.uR, args.pR)

    # Compute norms
    print(f"{'Variable':>8s}  {'L1':>12s}  {'L2':>12s}  {'Linf':>12s}")
    print(f"{'--------':>8s}  {'---':>12s}  {'---':>12s}  {'----':>12s}")
    for name, num, ex in [("rho", rho_num, rho_ex),
                           ("u", u_num, u_ex),
                           ("p", p_num, p_ex)]:
        L1, L2, Linf = compute_norms(num, ex, dx)
        print(f"{name:>8s}  {L1:12.6e}  {L2:12.6e}  {Linf:12.6e}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Create `analysis/plot_1d.py`**

Create `analysis/plot_1d.py`:

```python
#!/usr/bin/env python3
"""
Plot 1D numerical vs exact Riemann solution.
Usage: python analysis/plot_1d.py output/sod.bin --gamma 1.4 --x0 0.5 --t-end 0.25 \
       --rhoL 1.0 --uL 0.0 --pL 1.0 --rhoR 0.125 --uR 0.0 --pR 0.1 \
       --title "Sod Shock Tube" -o output/sod_plot.png
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.verify_toro import exact_riemann
from analysis.compare import read_binary


def main():
    parser = argparse.ArgumentParser(description="Plot 1D numerical vs exact Riemann solution")
    parser.add_argument("binfile", help="Path to .bin output file")
    parser.add_argument("--gamma", type=float, default=1.4)
    parser.add_argument("--x0", type=float, default=0.5)
    parser.add_argument("--t-end", type=float, required=True)
    parser.add_argument("--rhoL", type=float, required=True)
    parser.add_argument("--uL", type=float, required=True)
    parser.add_argument("--pL", type=float, required=True)
    parser.add_argument("--rhoR", type=float, required=True)
    parser.add_argument("--uR", type=float, required=True)
    parser.add_argument("--pR", type=float, required=True)
    parser.add_argument("--title", type=str, default="1D Riemann Problem")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Output PNG path (default: show interactively)")
    args = parser.parse_args()

    data, nx, ny, nvars, time, dx, dy = read_binary(args.binfile)

    # Extract primitives from conservative variables
    rho = data[0, :, 0]
    rhou = data[0, :, 1]
    rhov = data[0, :, 2]
    E    = data[0, :, 3]
    u_num = rhou / rho
    p_num = (args.gamma - 1.0) * (E - 0.5 * rho * (u_num**2 + (rhov/rho)**2))

    x = np.array([(i + 0.5) * dx for i in range(nx)])

    # Exact solution (1000 points for smooth curve)
    x_exact = np.linspace(x[0], x[-1], 1000)
    rho_ex, u_ex, p_ex, _ = exact_riemann(
        x_exact, args.t_end, args.gamma, args.x0,
        args.rhoL, args.uL, args.pL,
        args.rhoR, args.uR, args.pR)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    fig.suptitle(f"{args.title}  (N={nx}, t={time:.4f})", fontsize=12, fontweight="bold")

    for ax, title, num, ex in [
        (axes[0], "Density", rho, rho_ex),
        (axes[1], "Velocity", u_num, u_ex),
        (axes[2], "Pressure", p_num, p_ex),
    ]:
        ax.plot(x_exact, ex, "k-", lw=1.2, label="Exact")
        ax.plot(x, num, "ro", ms=2.0, alpha=0.5, label="Numerical")
        ax.set_title(title)
        ax.set_xlabel("x")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    if args.output:
        plt.savefig(args.output, dpi=150, bbox_inches="tight")
        print(f"Saved: {args.output}")
    else:
        plt.show()
    plt.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Verify scripts parse correctly**

```bash
python -c "import ast; ast.parse(open('analysis/compare.py').read()); print('compare.py: OK')"
python -c "import ast; ast.parse(open('analysis/plot_1d.py').read()); print('plot_1d.py: OK')"
```

Expected: Both print OK (syntax-valid Python).

- [ ] **Step 5: Commit**

```bash
git add analysis/requirements.txt analysis/compare.py analysis/plot_1d.py
git commit -m "feat(analysis): add compare.py and plot_1d.py for binary output analysis

compare.py: loads HRSC binary files, computes L1/L2/Linf norms vs exact Riemann.
plot_1d.py: numerical vs exact overlay plots for rho, u, p."
```

---

## Task 12: Y-Direction — `euler_flux_y` + `swap_momentum`

**Files:**
- Modify: `src/euler/euler_flux.hpp`
- Modify: `tests/unit/test_euler.cpp`

- [ ] **Step 1: Write failing tests**

In `tests/unit/test_euler.cpp`, add:

```cpp
TEST_CASE("euler_flux_y: stationary gas returns {0, 0, p, 0}", "[flux]") {
    Vec<double, 4> cons = {1.0, 0.0, 0.0, 2.5};
    Vec<double, 4> g = euler_flux_y(cons, 1.4);

    REQUIRE(g[0] == Approx(0.0).margin(1e-15));
    REQUIRE(g[1] == Approx(0.0).margin(1e-15));
    REQUIRE(g[2] == Approx(1.0).epsilon(1e-12));  // p = 1
    REQUIRE(g[3] == Approx(0.0).margin(1e-15));
}

TEST_CASE("euler_flux_y: uniform upward flow", "[flux]") {
    // rho=2, u=1, v=3, p=4, gamma=1.4
    // cons: rho=2, rho*u=2, rho*v=6, E = 4/0.4 + 0.5*2*(1+9) = 10+10=20
    Vec<double, 4> cons = {2.0, 2.0, 6.0, 20.0};
    Vec<double, 4> g = euler_flux_y(cons, 1.4);

    // G = {rho*v, rho*u*v, rho*v^2+p, v*(E+p)}
    //   = {6, 2*1*3, 2*9+4, 3*(20+4)} = {6, 6, 22, 72}
    REQUIRE(g[0] == Approx(6.0).epsilon(1e-12));
    REQUIRE(g[1] == Approx(6.0).epsilon(1e-12));
    REQUIRE(g[2] == Approx(22.0).epsilon(1e-12));
    REQUIRE(g[3] == Approx(72.0).epsilon(1e-12));
}

TEST_CASE("swap_momentum: swaps RHOU and RHOV", "[flux]") {
    Vec<double, 4> q = {1.0, 2.0, 3.0, 4.0};
    Vec<double, 4> s = swap_momentum(q);
    REQUIRE(s[RHO]  == Approx(1.0));
    REQUIRE(s[RHOU] == Approx(3.0));  // was RHOV
    REQUIRE(s[RHOV] == Approx(2.0));  // was RHOU
    REQUIRE(s[EN]   == Approx(4.0));
}
```

- [ ] **Step 2: Implement `euler_flux_y` and `swap_momentum`**

In `src/euler/euler_flux.hpp`, add after `euler_flux_x`:

```cpp
// Physical flux G(U) in y-direction for 2D Euler equations.
// cons = {rho, rho*u, rho*v, E}
// G    = {rho*v, rho*u*v, rho*v^2 + p, v*(E + p)}
template <typename Real>
HD_FUNC Vec<Real, 4> euler_flux_y(const Vec<Real, 4>& cons, Real gamma) {
    Real rho   = cons[RHO];
    Real rho_u = cons[RHOU];
    Real rho_v = cons[RHOV];
    Real E     = cons[EN];
    Real v     = rho_v / rho;
    Real p     = pressure(cons, gamma);

    return {rho_v,
            rho_u * v,
            rho_v * v + p,
            v * (E + p)};
}

// Swap momentum components for y-interface HLLC rotation.
// HLLC treats index 1 as normal velocity. For y-interfaces,
// swap RHOU <-> RHOV so v becomes the normal velocity.
template <typename Real>
HD_FUNC Vec<Real, 4> swap_momentum(const Vec<Real, 4>& q) {
    return {q[RHO], q[RHOV], q[RHOU], q[EN]};
}
```

- [ ] **Step 3: Build, run tests, commit**

```bash
cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[flux]"
git add src/euler/euler_flux.hpp tests/unit/test_euler.cpp
git commit -m "feat(euler): add euler_flux_y and swap_momentum helper

Y-direction physical flux G(U) = {rho*v, rho*u*v, rho*v^2+p, v*(E+p)}.
swap_momentum enables HLLC reuse for y-interfaces via rotation."
```

---

## Task 13: Y-Direction — `muscl_reconstruct_y` + `muscl_hancock_y`

**Files:**
- Modify: `src/euler/muscl.hpp`
- Modify: `src/euler/hancock.hpp`
- Modify: `tests/unit/test_euler.cpp`

- [ ] **Step 1: Write failing tests for `muscl_reconstruct_y`**

In `tests/unit/test_euler.cpp`, add:

```cpp
TEST_CASE("muscl_reconstruct_y: uniform field gives no reconstruction", "[muscl]") {
    Grid2D<double, 4> grid(5, 10);
    grid.dx = 0.1;
    grid.dy = 0.1;
    auto gv = grid.view();

    for (int j = -2; j < 12; ++j)
        for (int i = -2; i < 7; ++i) {
            gv(i, j, RHO)  = 1.0;
            gv(i, j, RHOU) = 0.0;
            gv(i, j, RHOV) = 0.0;
            gv(i, j, EN)   = 2.5;
        }

    Vec<double, 4> qB{}, qT{};
    muscl_reconstruct_y(grid.view(), 2, 5, qB, qT);

    REQUIRE(qB[RHO] == Approx(1.0).epsilon(1e-12));
    REQUIRE(qT[RHO] == Approx(1.0).epsilon(1e-12));
}

TEST_CASE("muscl_reconstruct_y: linear field in j-direction", "[muscl]") {
    Grid2D<double, 4> grid(5, 10);
    grid.dx = 0.1;
    grid.dy = 0.1;
    auto gv = grid.view();

    for (int j = -2; j < 12; ++j)
        for (int i = -2; i < 7; ++i) {
            gv(i, j, RHO)  = 1.0 + 0.1 * j;
            gv(i, j, RHOU) = 0.0;
            gv(i, j, RHOV) = 0.0;
            gv(i, j, EN)   = 2.5;
        }

    Vec<double, 4> qB{}, qT{};
    muscl_reconstruct_y(grid.view(), 2, 5, qB, qT);

    // Cell (2,5): rho=1.5, backward=forward=0.1
    // minbee(0.1, 0.1) = 0.1
    REQUIRE(qB[RHO] == Approx(1.45).epsilon(1e-12));
    REQUIRE(qT[RHO] == Approx(1.55).epsilon(1e-12));
}
```

- [ ] **Step 2: Implement `muscl_reconstruct_y`**

In `src/euler/muscl.hpp`, add after `muscl_reconstruct_x`:

```cpp
// MUSCL piecewise-linear reconstruction for cell (i,j) in y-direction.
// Returns boundary-extrapolated values at bottom face (j-1/2) and top face (j+1/2).
// Stencil: cells j-1, j, j+1 (within NgHost=2 ghost layers).
template <typename Real, typename Ptr, typename Limiter = MinbeeLimiter>
HD_FUNC void muscl_reconstruct_y(
    GridViewBase<Real, 4, Ptr> grid, int i, int j,
    Vec<Real, 4>& q_bottom, Vec<Real, 4>& q_top,
    Limiter lim = {})
{
    for (int v = 0; v < 4; ++v) {
        Real u_jm1 = grid(i, j - 1, v);
        Real u_j   = grid(i, j,     v);
        Real u_jp1 = grid(i, j + 1, v);

        Real backward = u_j - u_jm1;
        Real forward  = u_jp1 - u_j;
        Real slope    = lim(backward, forward);

        q_bottom[v] = u_j - Real(0.5) * slope;
        q_top[v]    = u_j + Real(0.5) * slope;
    }
}
```

- [ ] **Step 3: Build and run muscl_reconstruct_y tests**

```bash
cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[muscl]"
```

Expected: All muscl tests pass (x and y).

- [ ] **Step 4: Write failing test for `muscl_hancock_y`**

In `tests/unit/test_euler.cpp`, add:

```cpp
TEST_CASE("muscl_hancock_y: uniform field unchanged after half-step", "[hancock]") {
    Grid2D<double, 4> grid(5, 10);
    grid.dx = 0.1;
    grid.dy = 0.1;
    auto gv = grid.view();

    for (int j = -2; j < 12; ++j)
        for (int i = -2; i < 7; ++i) {
            gv(i, j, RHO)  = 1.0;
            gv(i, j, RHOU) = 0.0;
            gv(i, j, RHOV) = 0.0;
            gv(i, j, EN)   = 2.5;
        }

    Vec<double, 4> qB{}, qT{};
    muscl_hancock_y(grid.view(), 2, 5, 0.001, 1.4, qB, qT);

    REQUIRE(qB[RHO]  == Approx(1.0).epsilon(1e-12));
    REQUIRE(qB[RHOU] == Approx(0.0).margin(1e-15));
    REQUIRE(qB[RHOV] == Approx(0.0).margin(1e-15));
    REQUIRE(qB[EN]   == Approx(2.5).epsilon(1e-12));

    REQUIRE(qT[RHO]  == Approx(1.0).epsilon(1e-12));
    REQUIRE(qT[RHOU] == Approx(0.0).margin(1e-15));
    REQUIRE(qT[RHOV] == Approx(0.0).margin(1e-15));
    REQUIRE(qT[EN]   == Approx(2.5).epsilon(1e-12));
}
```

- [ ] **Step 5: Implement `muscl_hancock_y`**

In `src/euler/hancock.hpp`, add the include for `euler_flux.hpp` (already present) and add after `muscl_hancock_x`:

```cpp
// MUSCL-Hancock predictor for cell (i,j) in y-direction.
// q_bottom = value at bottom face (j - 1/2)
// q_top    = value at top face    (j + 1/2)
template <typename Real, typename Ptr, typename Limiter = MinbeeLimiter>
HD_FUNC void muscl_hancock_y(
    GridViewBase<Real, 4, Ptr> grid, int i, int j,
    Real dt, Real gamma,
    Vec<Real, 4>& q_bottom, Vec<Real, 4>& q_top,
    Limiter lim = {})
{
    // Step 1: MUSCL reconstruction in y
    muscl_reconstruct_y(grid, i, j, q_bottom, q_top, lim);

    // Step 2: Compute y-fluxes at bottom and top faces
    Vec<Real, 4> gB = euler_flux_y(q_bottom, gamma);
    Vec<Real, 4> gT = euler_flux_y(q_top,    gamma);

    // Step 3: Half-step evolution using dy (NOT dx)
    Real half_dtdy = Real(0.5) * dt / grid.dy;
    Vec<Real, 4> dg = gB - gT;

    q_bottom += dg * half_dtdy;
    q_top    += dg * half_dtdy;
}
```

Also add `#include "euler/euler_flux.hpp"` to hancock.hpp if not already present (it is — euler_flux.hpp is already included, and euler_flux_y was added to that file in Task 10).

- [ ] **Step 6: Build, run tests, commit**

```bash
cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[muscl]" && PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[hancock]"
git add src/euler/muscl.hpp src/euler/hancock.hpp tests/unit/test_euler.cpp
git commit -m "feat(euler): add muscl_reconstruct_y and muscl_hancock_y

Y-direction reconstruction and Hancock predictor. Uses grid.dy for
spatial derivative. Same limiter template pattern as x-direction."
```

---

## Task 14: 2D Euler Solver

**Files:**
- Modify: `src/euler/euler_solver.hpp`
- Modify: `tests/unit/test_euler.cpp`

- [ ] **Step 1: Write failing test for 2D uniform field**

In `tests/unit/test_euler.cpp`, add:

```cpp
TEST_CASE("EulerSolver 2D: uniform field no evolution", "[solver]") {
    int nx = 20, ny = 20;
    double dx = 0.05, dy = 0.05;
    EulerSolver<double> solver(nx, ny, dx, dy, 0.0, 0.0, 1.4, 0.8, 0.01);

    auto gv = solver.grid_view();
    // Uniform state: rho=1, u=0, v=0, p=1 → cons={1, 0, 0, 2.5}
    for (int j = 0; j < ny; ++j)
        for (int i = 0; i < nx; ++i) {
            gv(i, j, RHO)  = 1.0;
            gv(i, j, RHOU) = 0.0;
            gv(i, j, RHOV) = 0.0;
            gv(i, j, EN)   = 2.5;
        }

    solver.run();

    auto gv2 = solver.grid_view();
    for (int j = 0; j < ny; ++j)
        for (int i = 0; i < nx; ++i) {
            REQUIRE(gv2(i, j, RHO)  == Approx(1.0).epsilon(1e-12));
            REQUIRE(gv2(i, j, RHOU) == Approx(0.0).margin(1e-12));
            REQUIRE(gv2(i, j, RHOV) == Approx(0.0).margin(1e-12));
            REQUIRE(gv2(i, j, EN)   == Approx(2.5).epsilon(1e-12));
        }
}
```

- [ ] **Step 2: Rewrite `euler_solver.hpp` with 2D support**

Replace the full contents of `src/euler/euler_solver.hpp`:

```cpp
#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/grid.hpp"
#include "core/eos.hpp"
#include "core/boundary.hpp"
#include "euler/euler_flux.hpp"
#include "euler/hancock.hpp"
#include "euler/hllc.hpp"

#include <vector>
#include <cmath>
#include <algorithm>
#include <limits>

namespace hrsc {

template <typename Real>
class EulerSolver {
    Grid2D<Real, 4> m_grid;
    Real m_xmin;
    Real m_ymin;
    Real m_gamma;
    Real m_cfl;
    Real m_t_end;
    Real m_time;
    int  m_step;

    // X-direction sweep: compute x-interface fluxes and update conserved variables.
    void x_sweep(Real dt) {
        auto gv = m_grid.view();
        int nx = gv.nx;
        int ny = gv.ny;
        int n_interfaces = nx + 1;

        for (int j = 0; j < ny; ++j) {
            std::vector<Vec<Real, 4>> flux(n_interfaces);

            for (int k = 0; k < n_interfaces; ++k) {
                int iL = k - 1;
                int iR = k;

                Vec<Real, 4> qL_left{}, qL_right{};
                Vec<Real, 4> qR_left{}, qR_right{};

                muscl_hancock_x(gv, iL, j, dt, m_gamma, qL_left, qL_right);
                muscl_hancock_x(gv, iR, j, dt, m_gamma, qR_left, qR_right);

                flux[k] = hllc_flux(qL_right, qR_left, m_gamma);
            }

            Real dtdx = dt / gv.dx;
            for (int i = 0; i < nx; ++i) {
                for (int v = 0; v < 4; ++v) {
                    gv(i, j, v) -= dtdx * (flux[i + 1][v] - flux[i][v]);
                }
            }
        }
    }

    // Y-direction sweep: compute y-interface fluxes and update conserved variables.
    void y_sweep(Real dt) {
        auto gv = m_grid.view();
        int nx = gv.nx;
        int ny = gv.ny;
        int n_interfaces = ny + 1;

        for (int i = 0; i < nx; ++i) {
            std::vector<Vec<Real, 4>> flux(n_interfaces);

            for (int k = 0; k < n_interfaces; ++k) {
                int jB = k - 1;  // cell below interface
                int jT = k;      // cell above interface

                Vec<Real, 4> qB_bot{}, qB_top{};
                Vec<Real, 4> qT_bot{}, qT_top{};

                muscl_hancock_y(gv, i, jB, dt, m_gamma, qB_bot, qB_top);
                muscl_hancock_y(gv, i, jT, dt, m_gamma, qT_bot, qT_top);

                // Rotate → HLLC → rotate back
                flux[k] = swap_momentum(
                    hllc_flux(swap_momentum(qB_top), swap_momentum(qT_bot), m_gamma));
            }

            Real dtdy = dt / gv.dy;
            for (int j = 0; j < ny; ++j) {
                for (int v = 0; v < 4; ++v) {
                    gv(i, j, v) -= dtdy * (flux[j + 1][v] - flux[j][v]);
                }
            }
        }
    }

public:
    // 2D constructor
    EulerSolver(int nx, int ny, Real dx, Real dy,
                Real xmin, Real ymin,
                Real gamma, Real cfl, Real t_end)
        : m_grid(nx, ny),
          m_xmin(xmin),
          m_ymin(ymin),
          m_gamma(gamma),
          m_cfl(cfl),
          m_t_end(t_end),
          m_time(Real(0)),
          m_step(0)
    {
        m_grid.dx = dx;
        m_grid.dy = dy;
    }

    // 1D convenience constructor
    EulerSolver(int nx, Real dx, Real xmin, Real gamma, Real cfl, Real t_end)
        : EulerSolver(nx, 1, dx, dx, xmin, Real(0), gamma, cfl, t_end)
    {}

    GridView<Real, 4> grid_view() {
        return m_grid.view();
    }

    Real time() const { return m_time; }
    int  step_count() const { return m_step; }
    Real xmin() const { return m_xmin; }
    Real ymin() const { return m_ymin; }

    // Compute stable time step: dt = CFL * min(dx/Sx, dy/Sy)
    Real compute_dt() const {
        auto gv = m_grid.view();
        int nx = gv.nx;
        int ny = gv.ny;
        Real max_Sx = std::numeric_limits<Real>::min();
        Real max_Sy = std::numeric_limits<Real>::min();

        for (int j = 0; j < ny; ++j) {
            for (int i = 0; i < nx; ++i) {
                Vec<Real, 4> cons;
                for (int v = 0; v < 4; ++v) cons[v] = gv(i, j, v);

                Real rho = cons[RHO];
                Real u   = cons[RHOU] / rho;
                Real vel_v = cons[RHOV] / rho;
                Real p   = pressure(cons, m_gamma);
                Real a   = sound_speed(rho, p, m_gamma);

                max_Sx = std::max(max_Sx, std::abs(u) + a);
                max_Sy = std::max(max_Sy, std::abs(vel_v) + a);
            }
        }

        Real dt = m_cfl * std::min(gv.dx / max_Sx, gv.dy / max_Sy);

        if (m_time + dt > m_t_end) {
            dt = m_t_end - m_time;
        }

        return dt;
    }

    void step() {
        auto gv = m_grid.view();

        apply_outflow_bc(gv);

        Real dt = compute_dt();
        if (dt <= Real(0)) return;

        if (m_grid.ny == 1) {
            // 1D path: x-sweep only, exact backward compatibility
            x_sweep(dt);
        } else {
            // 2D path: alternating Godunov splitting
            if (m_step % 2 == 0) {
                x_sweep(dt);
                apply_outflow_bc(gv);
                y_sweep(dt);
            } else {
                y_sweep(dt);
                apply_outflow_bc(gv);
                x_sweep(dt);
            }
        }

        m_time += dt;
        m_step++;
    }

    void run() {
        while (m_time < m_t_end) {
            step();
        }
    }
};

} // namespace hrsc
```

- [ ] **Step 3: Build and run 2D uniform test**

```bash
cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[solver]"
```

Expected: 2D uniform field test passes. All 1D solver tests still pass.

- [ ] **Step 4: Add 2D Sod-along-x test**

In `tests/unit/test_euler.cpp`, add:

```cpp
TEST_CASE("EulerSolver 2D: Sod along x matches 1D", "[solver]") {
    double gamma = 1.4;
    int nx = 100;
    double dx = 1.0 / nx;

    // 1D reference
    EulerSolver<double> solver1d(nx, dx, 0.0, gamma, 0.8, 0.25);
    setup_sod(solver1d.grid_view(), gamma);
    solver1d.run();

    // 2D: 4 rows, same Sod IC replicated in each row
    int ny = 4;
    EulerSolver<double> solver2d(nx, ny, dx, dx, 0.0, 0.0, gamma, 0.8, 0.25);
    auto gv2d = solver2d.grid_view();
    for (int j = 0; j < ny; ++j)
        for (int i = 0; i < nx; ++i) {
            double x = (i + 0.5) * dx;
            Vec<double, 4> prim;
            if (x < 0.5) {
                prim = {1.0, 0.0, 0.0, 1.0};
            } else {
                prim = {0.125, 0.0, 0.0, 0.1};
            }
            Vec<double, 4> cons = prim_to_cons(prim, gamma);
            for (int v = 0; v < 4; ++v)
                gv2d(i, j, v) = cons[v];
        }
    solver2d.run();

    // Compare row 0 of 2D with 1D solution
    auto gv1d = solver1d.grid_view();
    auto gv2d_final = solver2d.grid_view();
    for (int i = 0; i < nx; ++i) {
        REQUIRE(gv2d_final(i, 0, RHO) == Approx(gv1d(i, 0, RHO)).epsilon(0.01));
        REQUIRE(gv2d_final(i, 0, EN)  == Approx(gv1d(i, 0, EN)).epsilon(0.01));
    }
}
```

- [ ] **Step 5: Build, run all tests, commit**

```bash
cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests
git add src/euler/euler_solver.hpp tests/unit/test_euler.cpp
git commit -m "feat(euler): extend EulerSolver to 2D with alternating Godunov splitting

2D constructor with per-direction CFL. x_sweep and y_sweep extracted as
private methods. Y-sweep uses momentum rotation for HLLC reuse. 1D path
preserved via ny==1 check."
```

---

## Task 15: Verificarlo Scripts

**Files:**
- Modify: `scripts/verificarlo_run.sh`
- Modify: `scripts/verificarlo_analysis.py`

- [ ] **Step 1: Read existing scripts**

Read `scripts/verificarlo_run.sh` and `scripts/verificarlo_analysis.py` to understand current structure before extending.

- [ ] **Step 2: Extend `scripts/verificarlo_run.sh`**

Add a new section at the end of the file for unstable branch detection at reduced precision:

```bash
# ============================================================
# Unstable Branch Detection (Week 3)
# Runs VPREC at 40-bit precision for 30 MCA samples to identify
# floating-point sensitive branch conditions in HLLC and MUSCL.
# ============================================================

BRANCH_DIR="output/branch_detection"
mkdir -p "$BRANCH_DIR"

echo "=== Unstable Branch Detection: VPREC 40-bit, 30 samples ==="

# Compile with verificarlo wrapper + FMA instrumentation
verificarlo-c++ --inst-fma -O2 -std=c++17 \
    -I src -I tests/cases/toro_1d \
    src/main.cpp -o hrsc_vfc_branch -lm

export VFC_BACKENDS="libinterflop_vprec.so --precision-binary64=40"

N_SAMPLES=30
for i in $(seq 1 $N_SAMPLES); do
    echo "  Sample $i/$N_SAMPLES"
    ./hrsc_vfc_branch tests/cases/toro_1d/sod.cfg \
        > "$BRANCH_DIR/sample_${i}.txt" 2>&1
done

echo "Branch detection samples saved to $BRANCH_DIR/"
```

- [ ] **Step 3: Extend `scripts/verificarlo_analysis.py`**

Add a new function at the end for branch flip analysis:

```python
def analyze_branch_flips(branch_dir="output/branch_detection", n_cells=200):
    """Compare MCA samples to detect branch flips across FP perturbations."""
    import glob

    sample_files = sorted(glob.glob(f"{branch_dir}/sample_*.txt"))
    if not sample_files:
        print(f"No samples found in {branch_dir}/")
        return

    print(f"\n=== Unstable Branch Detection ({len(sample_files)} samples) ===")

    # Parse each sample: columns are x, rho, u, v, p
    all_data = []
    for sf in sample_files:
        data = np.loadtxt(sf)
        all_data.append(data)

    all_data = np.array(all_data)  # shape: (n_samples, n_cells, 5)
    n_samples = all_data.shape[0]

    # For each cell, compute std deviation across samples
    rho_std = np.std(all_data[:, :, 1], axis=0)  # rho is column 1
    u_std   = np.std(all_data[:, :, 2], axis=0)  # u is column 2
    p_std   = np.std(all_data[:, :, 4], axis=0)  # p is column 4

    # Flag cells where variability is high (potential branch flips)
    rho_mean = np.mean(np.abs(all_data[:, :, 1]), axis=0)
    relative_var = np.where(rho_mean > 1e-10, rho_std / rho_mean, 0.0)

    # Top 10 most variable cells
    top_cells = np.argsort(relative_var)[-10:][::-1]

    print("\nTop 10 cells with highest relative density variation (40-bit VPREC):")
    print(f"{'Cell':>6}  {'x':>10}  {'rel_std_rho':>12}  {'std_u':>12}  {'std_p':>12}")
    x_coords = all_data[0, :, 0]
    for c in top_cells:
        print(f"{c:6d}  {x_coords[c]:10.5f}  {relative_var[c]:12.4e}"
              f"  {u_std[c]:12.4e}  {p_std[c]:12.4e}")

    # Save summary
    summary_file = f"{branch_dir}/branch_flip_summary.txt"
    with open(summary_file, 'w') as f:
        f.write("# Unstable branch detection summary (VPREC 40-bit)\n")
        f.write(f"# {n_samples} MCA samples, {n_cells} cells\n")
        f.write(f"# cell  x  rel_std_rho  std_u  std_p\n")
        for c in range(len(x_coords)):
            f.write(f"{c}  {x_coords[c]:.6f}  {relative_var[c]:.6e}"
                    f"  {u_std[c]:.6e}  {p_std[c]:.6e}\n")

    print(f"\nFull summary saved to {summary_file}")
```

- [ ] **Step 4: Commit**

```bash
git add scripts/verificarlo_run.sh scripts/verificarlo_analysis.py
git commit -m "feat(scripts): add Verificarlo unstable branch detection

VPREC at 40-bit precision with 30 MCA samples. Analysis identifies cells
with highest FP-induced variability near shocks and contacts."
```

---

## Summary

| Task | Module | Files | Estimated Effort |
|------|--------|-------|-----------------|
| 1 | Slope limiters (functions + functors) | muscl.hpp, test_euler.cpp | 30 min |
| 2 | Limiter template parameterization | muscl.hpp, hancock.hpp, test_euler.cpp | 15 min |
| 3 | Exact Riemann — pressure iteration | exact_riemann.hpp, test_euler.cpp | 45 min |
| 4 | Exact Riemann — sampling | exact_riemann.hpp, test_euler.cpp | 30 min |
| 5 | Error norms | error_norms.hpp, test_euler.cpp | 15 min |
| 6 | Binary IO | io.hpp, test_euler.cpp | 30 min |
| 7 | Config get_int_list + convergence cfg | config.hpp, convergence_sod.cfg, test_euler.cpp | 15 min |
| 8 | Convergence mode in main.cpp | main.cpp, euler_solver.hpp, test_euler.cpp | 30 min |
| 9 | Convergence plotting script | convergence.py | 15 min |
| 10 | Stationary contact test | toro_tests.hpp, stationary_contact.cfg, main.cpp, test_euler.cpp | 20 min |
| 11 | Python analysis scripts | compare.py, plot_1d.py, requirements.txt | 20 min |
| 12 | euler_flux_y + swap_momentum | euler_flux.hpp, test_euler.cpp | 15 min |
| 13 | muscl_reconstruct_y + muscl_hancock_y | muscl.hpp, hancock.hpp, test_euler.cpp | 20 min |
| 14 | 2D Euler solver | euler_solver.hpp, test_euler.cpp | 45 min |
| 15 | Verificarlo scripts | verificarlo_run.sh, verificarlo_analysis.py | 15 min |

**Total: ~6 hours of implementation work across 15 tasks.**

Tier 1 (Tasks 1–11): Foundation — must complete.
Tier 3 (Tasks 12–14): 2D extension — if time permits.
Tier 2 (Task 15): Verificarlo — independent, can slot in anytime.
