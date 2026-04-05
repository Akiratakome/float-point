# Week 2: 1D Euler Solver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete 1D MUSCL-Hancock + HLLC Euler solver that passes the Sod shock tube test.

**Architecture:** Cell-interface pipeline — per cell MUSCL reconstruct + Hancock half-step evolve, then per interface HLLC Riemann solve, then conservative update. All functions are `HD_FUNC` templated on `<Real>` in header-only files under `src/euler/`.

**Tech Stack:** C++17, Catch2 v2 (vendored at `external/catch2/`), CMake 3.18+, Ninja generator.

**Build & test commands:**
```bash
cmake -B build -S . -G Ninja && cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests
```

**Existing API you will use:**
- `Vec<Real, 4>` — fixed-size array with `+`, `-`, `*`, `/`, scalar `*`, `+=`, `-=` (all `HD_FUNC`)
- `Grid2D<Real, 4>` — owning container. Set `dx`/`dy` before calling `view()`.
- `GridView<Real, 4>` / `ConstGridView<Real, 4>` — lightweight view. Access: `gv(i, j, var)`. 1D mode: `ny=1`, `j=0`.
- `EulerVar` enum: `RHO=0, RHOU=1, RHOV=2, EN=3`
- `pressure(cons, gamma)`, `sound_speed(rho, p, gamma)`, `cons_to_prim(cons, gamma)`, `prim_to_cons(prim, gamma)`
- `apply_outflow_bc(grid_view)` — fills ghost cells from outermost physical cells
- `Config` — reads `key=value` files. Methods: `get_int()`, `get_double()`, `get_string()`, `get_bool()`

---

## Task 1: Add PrimVar Enum to EOS

**Files:**
- Modify: `src/core/eos.hpp:13` (insert after `EulerVar` enum)
- Test: `tests/unit/test_eos.cpp`

- [ ] **Step 1: Add PrimVar enum**

In `src/core/eos.hpp`, insert after line 13 (`enum EulerVar : int { RHO = 0, RHOU = 1, RHOV = 2, EN = 3 };`):

```cpp
// Primitive variable indexing: {rho, u, v, p}
enum PrimVar : int { PRHO = 0, VX = 1, VY = 2, PRES = 3 };
```

- [ ] **Step 2: Add a test verifying PrimVar access on cons_to_prim output**

Append to `tests/unit/test_eos.cpp`:

```cpp
TEST_CASE("PrimVar enum accesses cons_to_prim output correctly", "[eos]") {
    // Sod left state: rho=1, u=0, v=0, p=1 → cons = {1, 0, 0, 2.5}
    Vec<double, 4> cons = {1.0, 0.0, 0.0, 2.5};
    Vec<double, 4> prim = cons_to_prim(cons, 1.4);

    REQUIRE(prim[PrimVar::PRHO] == Approx(1.0));
    REQUIRE(prim[PrimVar::VX]   == Approx(0.0));
    REQUIRE(prim[PrimVar::VY]   == Approx(0.0));
    REQUIRE(prim[PrimVar::PRES] == Approx(1.0));
}
```

- [ ] **Step 3: Build and run tests**

```bash
cmake -B build -S . -G Ninja && cmake --build build && PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[eos]"
```

Expected: All eos tests PASS, including the new `PrimVar enum accesses` test.

- [ ] **Step 4: Commit**

```bash
git add src/core/eos.hpp tests/unit/test_eos.cpp
git commit -m "feat(eos): add PrimVar enum for semantic primitive variable access"
```

---

## Task 2: Euler Flux

**Files:**
- Create: `src/euler/euler_flux.hpp`
- Test: `tests/unit/test_euler.cpp` (new file)

- [ ] **Step 1: Create the test file with flux tests**

Create `tests/unit/test_euler.cpp`:

```cpp
#include "catch.hpp"
#include "euler/euler_flux.hpp"

using namespace hrsc;

// --- euler_flux_x tests ---

TEST_CASE("euler_flux_x: stationary gas returns {0, p, 0, 0}", "[flux]") {
    // rho=1, u=0, v=0, p=1 → cons = {1, 0, 0, 2.5}
    Vec<double, 4> cons = {1.0, 0.0, 0.0, 2.5};
    Vec<double, 4> f = euler_flux_x(cons, 1.4);

    REQUIRE(f[0] == Approx(0.0).margin(1e-15));  // rho*u = 0
    REQUIRE(f[1] == Approx(1.0).epsilon(1e-12));  // rho*u^2 + p = p = 1
    REQUIRE(f[2] == Approx(0.0).margin(1e-15));  // rho*u*v = 0
    REQUIRE(f[3] == Approx(0.0).margin(1e-15));  // u*(E+p) = 0
}

TEST_CASE("euler_flux_x: uniform rightward flow", "[flux]") {
    // rho=2, u=3, v=1, p=4, gamma=1.4
    // cons: rho=2, rho*u=6, rho*v=2, E = p/(gamma-1) + 0.5*rho*(u^2+v^2)
    //     = 4/0.4 + 0.5*2*(9+1) = 10 + 10 = 20
    Vec<double, 4> cons = {2.0, 6.0, 2.0, 20.0};
    Vec<double, 4> f = euler_flux_x(cons, 1.4);

    // F = {rho*u, rho*u^2+p, rho*u*v, u*(E+p)}
    //   = {6, 2*9+4, 6*1, 3*(20+4)} = {6, 22, 6, 72}
    REQUIRE(f[0] == Approx(6.0).epsilon(1e-12));
    REQUIRE(f[1] == Approx(22.0).epsilon(1e-12));
    REQUIRE(f[2] == Approx(6.0).epsilon(1e-12));
    REQUIRE(f[3] == Approx(72.0).epsilon(1e-12));
}
```

- [ ] **Step 2: Build and verify tests fail**

```bash
cmake -B build -S . -G Ninja && cmake --build build
```

Expected: Compilation fails — `euler/euler_flux.hpp` not found.

- [ ] **Step 3: Implement euler_flux_x**

Create `src/euler/euler_flux.hpp`:

```cpp
#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/eos.hpp"

namespace hrsc {

// Physical flux F(U) in x-direction for 2D Euler equations.
// cons = {rho, rho*u, rho*v, E}
// F    = {rho*u, rho*u^2 + p, rho*u*v, u*(E + p)}
template <typename Real>
HD_FUNC Vec<Real, 4> euler_flux_x(const Vec<Real, 4>& cons, Real gamma) {
    Real rho   = cons[RHO];
    Real rho_u = cons[RHOU];
    Real rho_v = cons[RHOV];
    Real E     = cons[EN];
    Real u     = rho_u / rho;
    Real p     = pressure(cons, gamma);

    return {rho_u,
            rho_u * u + p,
            rho_v * u,
            u * (E + p)};
}

} // namespace hrsc
```

- [ ] **Step 4: Build and run tests**

```bash
cmake -B build -S . -G Ninja && cmake --build build && PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[flux]"
```

Expected: Both flux tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/euler/euler_flux.hpp tests/unit/test_euler.cpp
git commit -m "feat(euler): add euler_flux_x with unit tests"
```

---

## Task 3: MUSCL Reconstruction with Minmod

**Files:**
- Create: `src/euler/muscl.hpp`
- Modify: `tests/unit/test_euler.cpp`

- [ ] **Step 1: Write failing tests for minmod and muscl_reconstruct_x**

Append to `tests/unit/test_euler.cpp`:

```cpp
#include "euler/muscl.hpp"
#include "core/grid.hpp"

// --- minmod tests ---

TEST_CASE("minmod: same sign values", "[muscl]") {
    REQUIRE(minmod(2.0, 3.0) == Approx(2.0));
    REQUIRE(minmod(3.0, 2.0) == Approx(2.0));
    REQUIRE(minmod(-2.0, -3.0) == Approx(-2.0));
}

TEST_CASE("minmod: opposite signs returns zero", "[muscl]") {
    REQUIRE(minmod(2.0, -1.0) == Approx(0.0));
    REQUIRE(minmod(-2.0, 1.0) == Approx(0.0));
}

TEST_CASE("minmod: one zero returns zero", "[muscl]") {
    REQUIRE(minmod(0.0, 3.0) == Approx(0.0));
    REQUIRE(minmod(3.0, 0.0) == Approx(0.0));
}

// --- muscl_reconstruct_x tests ---

TEST_CASE("muscl_reconstruct_x: uniform field gives no reconstruction", "[muscl]") {
    // 10-cell 1D grid, uniform rho=1, u=0, v=0, p=1 → cons={1,0,0,2.5}
    Grid2D<double, 4> grid(10, 1);
    grid.dx = 0.1;
    grid.dy = 0.1;
    auto gv = grid.view();

    for (int i = -2; i < 12; ++i) {
        gv(i, 0, RHO)  = 1.0;
        gv(i, 0, RHOU) = 0.0;
        gv(i, 0, RHOV) = 0.0;
        gv(i, 0, EN)   = 2.5;
    }

    Vec<double, 4> qL{}, qR{};
    muscl_reconstruct_x(grid.view(), 5, 0, qL, qR);

    // Uniform field: left face == right face == cell value
    for (int v = 0; v < 4; ++v) {
        Vec<double, 4> cell = {1.0, 0.0, 0.0, 2.5};
        REQUIRE(qL[v] == Approx(cell[v]).margin(1e-15));
        REQUIRE(qR[v] == Approx(cell[v]).margin(1e-15));
    }
}

TEST_CASE("muscl_reconstruct_x: linear field recovers exact gradient", "[muscl]") {
    // 10-cell 1D grid, rho varies linearly: rho_i = 1 + 0.1*i
    // All other variables uniform
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
    muscl_reconstruct_x(grid.view(), 5, 0, qL, qR);

    // Cell 5 center value: rho = 1.5
    // Slope: (rho_{i+1} - rho_{i-1}) / 2 is not used; minmod uses forward/backward
    // backward diff: rho_5 - rho_4 = 0.1
    // forward diff:  rho_6 - rho_5 = 0.1
    // minmod(0.1, 0.1) = 0.1
    // qL (left face) = 1.5 - 0.5 * 0.1 = 1.45
    // qR (right face) = 1.5 + 0.5 * 0.1 = 1.55
    REQUIRE(qL[RHO] == Approx(1.45).epsilon(1e-12));
    REQUIRE(qR[RHO] == Approx(1.55).epsilon(1e-12));
}

TEST_CASE("muscl_reconstruct_x: discontinuity triggers limiter", "[muscl]") {
    // 10-cell grid: cells 0-4 have rho=1, cells 5-9 have rho=2
    Grid2D<double, 4> grid(10, 1);
    grid.dx = 0.1;
    grid.dy = 0.1;
    auto gv = grid.view();

    for (int i = -2; i < 12; ++i) {
        double rho = (i < 5) ? 1.0 : 2.0;
        gv(i, 0, RHO)  = rho;
        gv(i, 0, RHOU) = 0.0;
        gv(i, 0, RHOV) = 0.0;
        gv(i, 0, EN)   = 2.5;
    }

    // Cell 4: backward = 1-1=0, forward = 2-1=1 → minmod(0,1)=0
    Vec<double, 4> qL4{}, qR4{};
    muscl_reconstruct_x(grid.view(), 4, 0, qL4, qR4);
    REQUIRE(qL4[RHO] == Approx(1.0).epsilon(1e-12));
    REQUIRE(qR4[RHO] == Approx(1.0).epsilon(1e-12));

    // Cell 5: backward = 2-1=1, forward = 2-2=0 → minmod(1,0)=0
    Vec<double, 4> qL5{}, qR5{};
    muscl_reconstruct_x(grid.view(), 5, 0, qL5, qR5);
    REQUIRE(qL5[RHO] == Approx(2.0).epsilon(1e-12));
    REQUIRE(qR5[RHO] == Approx(2.0).epsilon(1e-12));
}
```

- [ ] **Step 2: Build and verify compilation fails**

```bash
cmake -B build -S . -G Ninja && cmake --build build
```

Expected: Fails — `euler/muscl.hpp` not found.

- [ ] **Step 3: Implement minmod and muscl_reconstruct_x**

Create `src/euler/muscl.hpp`:

```cpp
#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/grid.hpp"
#include "core/eos.hpp"

#include <algorithm>
#include <cmath>

namespace hrsc {

// Minmod slope limiter: returns the value with smaller magnitude
// if both have the same sign, otherwise zero.
template <typename Real>
HD_FUNC Real minmod(Real a, Real b) {
    if (a * b <= Real(0)) return Real(0);
    return (std::abs(a) < std::abs(b)) ? a : b;
}

// MUSCL piecewise-linear reconstruction for cell i in x-direction.
// Returns boundary-extrapolated values at left face (i-1/2) and right face (i+1/2).
// Uses minmod limiter, component-wise on conserved variables.
// Stencil: cells i-1, i, i+1 (within NgHost=2 ghost layers).
template <typename Real>
HD_FUNC void muscl_reconstruct_x(
    ConstGridView<Real, 4> grid, int i, int j,
    Vec<Real, 4>& q_left, Vec<Real, 4>& q_right)
{
    for (int v = 0; v < 4; ++v) {
        Real u_im1 = grid(i - 1, j, v);
        Real u_i   = grid(i,     j, v);
        Real u_ip1 = grid(i + 1, j, v);

        Real backward = u_i - u_im1;
        Real forward  = u_ip1 - u_i;
        Real slope    = minmod(backward, forward);

        q_left[v]  = u_i - Real(0.5) * slope;
        q_right[v] = u_i + Real(0.5) * slope;
    }
}

} // namespace hrsc
```

- [ ] **Step 4: Build and run tests**

```bash
cmake -B build -S . -G Ninja && cmake --build build && PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[muscl]"
```

Expected: All 6 muscl/minmod tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/euler/muscl.hpp tests/unit/test_euler.cpp
git commit -m "feat(euler): add MUSCL reconstruction with minmod limiter"
```

---

## Task 4: Hancock Half-Step Predictor

**Files:**
- Create: `src/euler/hancock.hpp`
- Modify: `tests/unit/test_euler.cpp`

- [ ] **Step 1: Write failing test for muscl_hancock_x**

Append to `tests/unit/test_euler.cpp`:

```cpp
#include "euler/hancock.hpp"

// --- muscl_hancock_x tests ---

TEST_CASE("muscl_hancock_x: uniform field unchanged after half-step", "[hancock]") {
    Grid2D<double, 4> grid(10, 1);
    grid.dx = 0.1;
    grid.dy = 0.1;
    auto gv = grid.view();

    // Uniform state: rho=1, u=0, v=0, p=1 → cons={1, 0, 0, 2.5}
    for (int i = -2; i < 12; ++i) {
        gv(i, 0, RHO)  = 1.0;
        gv(i, 0, RHOU) = 0.0;
        gv(i, 0, RHOV) = 0.0;
        gv(i, 0, EN)   = 2.5;
    }

    Vec<double, 4> qL{}, qR{};
    muscl_hancock_x(grid.view(), 5, 0, 0.001, 1.4, qL, qR);

    // Uniform → slope=0 → q_left=q_right=cell value → F(qL)=F(qR) → no evolution
    REQUIRE(qL[RHO]  == Approx(1.0).epsilon(1e-12));
    REQUIRE(qL[RHOU] == Approx(0.0).margin(1e-15));
    REQUIRE(qL[RHOV] == Approx(0.0).margin(1e-15));
    REQUIRE(qL[EN]   == Approx(2.5).epsilon(1e-12));

    REQUIRE(qR[RHO]  == Approx(1.0).epsilon(1e-12));
    REQUIRE(qR[RHOU] == Approx(0.0).margin(1e-15));
    REQUIRE(qR[RHOV] == Approx(0.0).margin(1e-15));
    REQUIRE(qR[EN]   == Approx(2.5).epsilon(1e-12));
}

TEST_CASE("muscl_hancock_x: linear density field evolves symmetrically", "[hancock]") {
    // Linear rho field with u=0: the Hancock predictor should produce
    // symmetric left/right states around the cell center because the
    // flux difference F(qL)-F(qR) is identical for momentum and energy
    // when velocity is zero (only pressure flux, which is symmetric in rho
    // for a linear profile).
    Grid2D<double, 4> grid(10, 1);
    grid.dx = 0.1;
    grid.dy = 0.1;
    auto gv = grid.view();

    for (int i = -2; i < 12; ++i) {
        double rho = 1.0 + 0.1 * i;
        double p   = 1.0;
        double E   = p / 0.4;  // gamma-1 = 0.4, u=v=0
        gv(i, 0, RHO)  = rho;
        gv(i, 0, RHOU) = 0.0;
        gv(i, 0, RHOV) = 0.0;
        gv(i, 0, EN)   = E;
    }

    Vec<double, 4> qL{}, qR{};
    muscl_hancock_x(grid.view(), 5, 0, 0.001, 1.4, qL, qR);

    // With u=0, flux F={0, p, 0, 0}.
    // qL has lower rho → lower p (if p varied), but here p is uniform (only rho varies,
    // E varies to keep p constant? No — E = p/(gamma-1) is constant, but rho varies,
    // so pressure = (gamma-1)*(E - 0) = p is constant across cells.
    // F(qL) = {0, p, 0, 0} = F(qR) → no Hancock correction.
    // So the result is just the MUSCL reconstruction.
    // Cell 5: rho=1.5, slope=0.1
    REQUIRE(qL[RHO] == Approx(1.45).epsilon(1e-10));
    REQUIRE(qR[RHO] == Approx(1.55).epsilon(1e-10));
}
```

- [ ] **Step 2: Build and verify compilation fails**

```bash
cmake -B build -S . -G Ninja && cmake --build build
```

Expected: Fails — `euler/hancock.hpp` not found.

- [ ] **Step 3: Implement muscl_hancock_x**

Create `src/euler/hancock.hpp`:

```cpp
#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/grid.hpp"
#include "euler/muscl.hpp"
#include "euler/euler_flux.hpp"

namespace hrsc {

// MUSCL-Hancock predictor for cell i in x-direction.
// 1. Calls muscl_reconstruct_x to get boundary-extrapolated (q_left, q_right)
// 2. Computes fluxes at both faces
// 3. Evolves both states by dt/2 using the flux difference
//
// q_left  = value at left face  (i - 1/2)
// q_right = value at right face (i + 1/2)
template <typename Real>
HD_FUNC void muscl_hancock_x(
    ConstGridView<Real, 4> grid, int i, int j,
    Real dt, Real gamma,
    Vec<Real, 4>& q_left, Vec<Real, 4>& q_right)
{
    // Step 1: MUSCL reconstruction
    muscl_reconstruct_x(grid, i, j, q_left, q_right);

    // Step 2: Compute fluxes at left and right faces
    Vec<Real, 4> fL = euler_flux_x(q_left,  gamma);
    Vec<Real, 4> fR = euler_flux_x(q_right, gamma);

    // Step 3: Half-step evolution
    // q += 0.5 * (dt/dx) * (F(q_left) - F(q_right))
    Real half_dtdx = Real(0.5) * dt / grid.dx;
    Vec<Real, 4> df = fL - fR;

    q_left  += df * half_dtdx;
    q_right += df * half_dtdx;
}

} // namespace hrsc
```

- [ ] **Step 4: Build and run tests**

```bash
cmake -B build -S . -G Ninja && cmake --build build && PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[hancock]"
```

Expected: Both hancock tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/euler/hancock.hpp tests/unit/test_euler.cpp
git commit -m "feat(euler): add Hancock half-step predictor"
```

---

## Task 5: HLLC Riemann Solver

**Files:**
- Create: `src/euler/hllc.hpp`
- Modify: `tests/unit/test_euler.cpp`
- Modify: `CMakeLists.txt`

- [ ] **Step 1: Add RIEMANN_STRICT_INEQUALITY to CMake**

In `CMakeLists.txt`, insert after the `FLOAT_PRECISION` line (after line 12):

```cmake
# Riemann solver inequality variant: <= (default) vs < (strict)
option(RIEMANN_STRICT_INEQUALITY "Use strict < instead of <= in HLLC/HLLD" OFF)
if(RIEMANN_STRICT_INEQUALITY)
    target_compile_definitions(hrsc_core INTERFACE RIEMANN_STRICT_INEQUALITY)
endif()
```

- [ ] **Step 2: Write failing tests for hllc_flux**

Append to `tests/unit/test_euler.cpp`:

```cpp
#include "euler/hllc.hpp"

// --- hllc_flux tests ---

TEST_CASE("hllc_flux: identical states returns physical flux", "[hllc]") {
    // If qL == qR, any Riemann solver must return F(q)
    Vec<double, 4> cons = {1.0, 0.0, 0.0, 2.5}; // rho=1, u=0, v=0, p=1
    Vec<double, 4> f_hllc = hllc_flux(cons, cons, 1.4);
    Vec<double, 4> f_phys = euler_flux_x(cons, 1.4);

    for (int v = 0; v < 4; ++v) {
        REQUIRE(f_hllc[v] == Approx(f_phys[v]).margin(1e-14));
    }
}

TEST_CASE("hllc_flux: identical states with nonzero velocity", "[hllc]") {
    // rho=2, u=3, v=1, p=4 → cons = {2, 6, 2, 20}
    Vec<double, 4> cons = {2.0, 6.0, 2.0, 20.0};
    Vec<double, 4> f_hllc = hllc_flux(cons, cons, 1.4);
    Vec<double, 4> f_phys = euler_flux_x(cons, 1.4);

    for (int v = 0; v < 4; ++v) {
        REQUIRE(f_hllc[v] == Approx(f_phys[v]).margin(1e-12));
    }
}

TEST_CASE("hllc_flux: Sod interface gives reasonable flux", "[hllc]") {
    // Left: rho=1, u=0, v=0, p=1 → cons={1, 0, 0, 2.5}
    // Right: rho=0.125, u=0, v=0, p=0.1 → cons={0.125, 0, 0, 0.25}
    Vec<double, 4> qL = {1.0, 0.0, 0.0, 2.5};
    Vec<double, 4> qR = {0.125, 0.0, 0.0, 0.25};
    Vec<double, 4> f = hllc_flux(qL, qR, 1.4);

    // The Sod shock tube has a right-going shock and contact.
    // At the interface, there should be a positive mass flux (flow goes right).
    REQUIRE(f[RHO] > 0.0);
    // Momentum flux should be positive (pressure pushes right)
    REQUIRE(f[RHOU] > 0.0);
}

TEST_CASE("hllc_flux: symmetry test", "[hllc]") {
    // Symmetric states: qL = (rho=2, u=1, v=0.5, p=3), qR = (rho=2, u=-1, v=0.5, p=3)
    // By symmetry: mass flux should be zero, momentum flux = 2*p_star region
    double gamma = 1.4;
    Vec<double, 4> primL = {2.0, 1.0, 0.5, 3.0};
    Vec<double, 4> primR = {2.0, -1.0, 0.5, 3.0};
    Vec<double, 4> qL = prim_to_cons(primL, gamma);
    Vec<double, 4> qR = prim_to_cons(primR, gamma);

    Vec<double, 4> f = hllc_flux(qL, qR, gamma);

    // Mass flux = 0 by symmetry (u=-u)
    REQUIRE(f[RHO] == Approx(0.0).margin(1e-12));
    // Energy flux = 0 by symmetry
    REQUIRE(f[EN] == Approx(0.0).margin(1e-12));
}
```

- [ ] **Step 3: Build and verify compilation fails**

```bash
cmake -B build -S . -G Ninja && cmake --build build
```

Expected: Fails — `euler/hllc.hpp` not found.

- [ ] **Step 4: Implement hllc_flux**

Create `src/euler/hllc.hpp`:

```cpp
#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/eos.hpp"
#include "euler/euler_flux.hpp"

#include <algorithm>
#include <cmath>

namespace hrsc {

// HLLC approximate Riemann solver (Toro 2009, Chapter 10).
// Takes left/right conserved states, returns intercell flux.
// Wave speed estimates: Davis (simplest, robust).
// Compile flag RIEMANN_STRICT_INEQUALITY controls <= vs < in flux selection.
template <typename Real>
HD_FUNC Vec<Real, 4> hllc_flux(
    const Vec<Real, 4>& qL, const Vec<Real, 4>& qR, Real gamma)
{
    // --- Primitive variables ---
    Real rhoL = qL[RHO];
    Real uL   = qL[RHOU] / rhoL;
    Real vL   = qL[RHOV] / rhoL;
    Real pL   = pressure(qL, gamma);
    Real aL   = sound_speed(rhoL, pL, gamma);

    Real rhoR = qR[RHO];
    Real uR   = qR[RHOU] / rhoR;
    Real vR   = qR[RHOV] / rhoR;
    Real pR   = pressure(qR, gamma);
    Real aR   = sound_speed(rhoR, pR, gamma);

    // --- Wave speed estimates (Davis) ---
    Real SL = std::min(uL - aL, uR - aR);
    Real SR = std::max(uL + aL, uR + aR);

    // --- Contact wave speed S* ---
    Real S_star = (pR - pL
                   + rhoL * uL * (SL - uL)
                   - rhoR * uR * (SR - uR))
                / (rhoL * (SL - uL) - rhoR * (SR - uR));

    // --- Physical fluxes ---
    Vec<Real, 4> FL = euler_flux_x(qL, gamma);
    Vec<Real, 4> FR = euler_flux_x(qR, gamma);

    // --- Flux selection ---
    if (SL >= Real(0)) {
        return FL;
    }

#ifdef RIEMANN_STRICT_INEQUALITY
    if (SL < Real(0) && Real(0) < S_star) {
#else
    if (SL <= Real(0) && Real(0) <= S_star) {
#endif
        // Left star state
        Real coeff = rhoL * (SL - uL) / (SL - S_star);
        Vec<Real, 4> U_starL = {
            coeff,
            coeff * S_star,
            coeff * vL,
            coeff * (qL[EN] / rhoL
                     + (S_star - uL) * (S_star + pL / (rhoL * (SL - uL))))
        };
        return FL + (U_starL - qL) * SL;
    }

#ifdef RIEMANN_STRICT_INEQUALITY
    if (S_star < Real(0) && Real(0) < SR) {
#else
    if (S_star <= Real(0) && Real(0) <= SR) {
#endif
        // Right star state
        Real coeff = rhoR * (SR - uR) / (SR - S_star);
        Vec<Real, 4> U_starR = {
            coeff,
            coeff * S_star,
            coeff * vR,
            coeff * (qR[EN] / rhoR
                     + (S_star - uR) * (S_star + pR / (rhoR * (SR - uR))))
        };
        return FR + (U_starR - qR) * SR;
    }

    // SR <= 0
    return FR;
}

} // namespace hrsc
```

- [ ] **Step 5: Build and run tests**

```bash
cmake -B build -S . -G Ninja && cmake --build build && PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[hllc]"
```

Expected: All 4 HLLC tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/euler/hllc.hpp tests/unit/test_euler.cpp CMakeLists.txt
git commit -m "feat(euler): add HLLC Riemann solver with configurable inequality"
```

---

## Task 6: Sod Test IC and Config File

**Files:**
- Create: `tests/cases/toro_1d/toro_tests.hpp`
- Create: `tests/cases/toro_1d/sod.cfg`

- [ ] **Step 1: Create toro_tests.hpp with setup_sod**

Create `tests/cases/toro_1d/toro_tests.hpp`:

```cpp
#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/grid.hpp"
#include "core/eos.hpp"

namespace hrsc {

// Sod shock tube IC (Toro Test 1).
// Domain [0, 1], discontinuity at x = 0.5.
// Left:  rho=1.0,   u=0, v=0, p=1.0
// Right: rho=0.125, u=0, v=0, p=0.1
// grid.dx must be set before calling this function.
template <typename Real>
void setup_sod(GridView<Real, 4> grid, Real gamma) {
    Real xmin = Real(0);

    for (int i = 0; i < grid.nx; ++i) {
        Real x = xmin + (Real(i) + Real(0.5)) * grid.dx;

        Vec<Real, 4> prim;
        if (x < Real(0.5)) {
            prim = {Real(1.0), Real(0), Real(0), Real(1.0)};
        } else {
            prim = {Real(0.125), Real(0), Real(0), Real(0.1)};
        }

        Vec<Real, 4> cons = prim_to_cons(prim, gamma);
        for (int v = 0; v < 4; ++v) {
            grid(i, 0, v) = cons[v];
        }
    }
}

} // namespace hrsc
```

- [ ] **Step 2: Create sod.cfg**

Create `tests/cases/toro_1d/sod.cfg`:

```ini
# Sod Shock Tube (Toro Test 1)
# Domain [0, 1], t_end = 0.25
test   = sod
nx     = 200
xmin   = 0.0
xmax   = 1.0
gamma  = 1.4
cfl    = 0.8
t_end  = 0.25
bc     = outflow
```

- [ ] **Step 3: Write a test verifying Sod IC is correct**

Append to `tests/unit/test_euler.cpp`:

```cpp
#include "toro_tests.hpp"

// --- Sod IC test ---

TEST_CASE("setup_sod: left and right states set correctly", "[sod]") {
    Grid2D<double, 4> grid(200, 1);
    grid.dx = 1.0 / 200;
    grid.dy = 1.0;
    auto gv = grid.view();

    setup_sod(gv, 1.4);

    // Cell 10 is at x = (10+0.5)*0.005 = 0.0525 → left state
    REQUIRE(gv(10, 0, RHO)  == Approx(1.0));
    REQUIRE(gv(10, 0, RHOU) == Approx(0.0));
    REQUIRE(gv(10, 0, RHOV) == Approx(0.0));
    // E = p/(gamma-1) = 1.0/0.4 = 2.5
    REQUIRE(gv(10, 0, EN)   == Approx(2.5));

    // Cell 150 is at x = (150+0.5)*0.005 = 0.7525 → right state
    REQUIRE(gv(150, 0, RHO)  == Approx(0.125));
    REQUIRE(gv(150, 0, RHOU) == Approx(0.0));
    REQUIRE(gv(150, 0, RHOV) == Approx(0.0));
    // E = p/(gamma-1) = 0.1/0.4 = 0.25
    REQUIRE(gv(150, 0, EN)   == Approx(0.25));
}
```

- [ ] **Step 4: Build and run test**

```bash
cmake -B build -S . -G Ninja && cmake --build build && PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[sod]"
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/cases/toro_1d/toro_tests.hpp tests/cases/toro_1d/sod.cfg tests/unit/test_euler.cpp
git commit -m "feat(toro): add Sod shock tube IC and config file"
```

---

## Task 7: EulerSolver Class

**Files:**
- Create: `src/euler/euler_solver.hpp`
- Modify: `tests/unit/test_euler.cpp`

- [ ] **Step 1: Write failing integration tests for EulerSolver**

Append to `tests/unit/test_euler.cpp`:

```cpp
#include "euler/euler_solver.hpp"
#include "core/boundary.hpp"

// --- EulerSolver integration tests ---

TEST_CASE("EulerSolver: Sod density stays in physical range", "[solver]") {
    int nx = 200;
    double dx = 1.0 / nx;
    EulerSolver<double> solver(nx, dx, 1.4, 0.8, 0.25);

    setup_sod(solver.grid_view(), 1.4);
    solver.run();

    auto gv = solver.grid_view();
    for (int i = 0; i < nx; ++i) {
        double rho = gv(i, 0, RHO);
        REQUIRE(rho >= 0.1);
        REQUIRE(rho <= 1.1);
    }
}

TEST_CASE("EulerSolver: Sod mass is conserved", "[solver]") {
    int nx = 200;
    double dx = 1.0 / nx;
    EulerSolver<double> solver(nx, dx, 1.4, 0.8, 0.25);

    setup_sod(solver.grid_view(), 1.4);

    // Compute initial total mass
    double mass_init = 0.0;
    {
        auto gv = solver.grid_view();
        for (int i = 0; i < nx; ++i) {
            mass_init += gv(i, 0, RHO) * dx;
        }
    }

    solver.run();

    // Compute final total mass
    double mass_final = 0.0;
    {
        auto gv = solver.grid_view();
        for (int i = 0; i < nx; ++i) {
            mass_final += gv(i, 0, RHO) * dx;
        }
    }

    // Mass should be conserved to ~machine epsilon * nsteps
    // Outflow BCs can leak mass, so allow ~1% tolerance
    REQUIRE(mass_final == Approx(mass_init).epsilon(0.01));
}

TEST_CASE("EulerSolver: Sod shock position is approximately correct", "[solver]") {
    int nx = 200;
    double dx = 1.0 / nx;
    EulerSolver<double> solver(nx, dx, 1.4, 0.8, 0.25);

    setup_sod(solver.grid_view(), 1.4);
    solver.run();

    // Find the rightmost cell where density drops below 0.3
    // (the shock front). Exact position at t=0.25 is ~x=0.85
    auto gv = solver.grid_view();
    int shock_cell = -1;
    for (int i = nx - 1; i >= 0; --i) {
        if (gv(i, 0, RHO) > 0.3) {
            shock_cell = i;
            break;
        }
    }

    double shock_x = (shock_cell + 0.5) * dx;
    REQUIRE(shock_x > 0.75);
    REQUIRE(shock_x < 0.95);
}
```

- [ ] **Step 2: Build and verify compilation fails**

```bash
cmake -B build -S . -G Ninja && cmake --build build
```

Expected: Fails — `euler/euler_solver.hpp` not found.

- [ ] **Step 3: Implement EulerSolver**

Create `src/euler/euler_solver.hpp`:

```cpp
#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/grid.hpp"
#include "core/eos.hpp"
#include "core/boundary.hpp"
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
    Real m_gamma;
    Real m_cfl;
    Real m_t_end;
    Real m_time;
    int  m_step;

public:
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

    GridView<Real, 4> grid_view() {
        return m_grid.view();
    }

    Real time() const { return m_time; }
    int  step_count() const { return m_step; }

    // Compute stable time step from CFL condition.
    // dt = CFL * dx / max_all(|u| + a)
    Real compute_dt() const {
        auto gv = m_grid.view();
        int nx = gv.nx;
        Real max_speed = std::numeric_limits<Real>::min();

        for (int i = 0; i < nx; ++i) {
            Vec<Real, 4> cons;
            for (int v = 0; v < 4; ++v) cons[v] = gv(i, 0, v);

            Real rho = cons[RHO];
            Real u   = cons[RHOU] / rho;
            Real p   = pressure(cons, m_gamma);
            Real a   = sound_speed(rho, p, m_gamma);

            max_speed = std::max(max_speed, std::abs(u) + a);
        }

        Real dt = m_cfl * gv.dx / max_speed;

        // Clip to reach t_end exactly
        if (m_time + dt > m_t_end) {
            dt = m_t_end - m_time;
        }

        return dt;
    }

    // Execute one time step (x-sweep only, 1D).
    void step() {
        auto gv = m_grid.view();
        int nx = gv.nx;

        // 1. Apply boundary conditions
        apply_outflow_bc(gv);

        // 2. Compute dt
        Real dt = compute_dt();
        if (dt <= Real(0)) return;

        // 3. Compute interface fluxes
        //    Interface k is between cell k-1 and cell k.
        //    We need nx+1 interfaces: k = 0 (left of cell 0) to k = nx (right of cell nx-1).
        int n_interfaces = nx + 1;
        std::vector<Vec<Real, 4>> flux(n_interfaces);

        ConstGridView<Real, 4> cgv = m_grid.view();

        for (int k = 0; k < n_interfaces; ++k) {
            // Interface k is between cell (k-1) and cell k.
            // Left cell = k-1, right cell = k.
            int iL = k - 1;  // cell to the left of interface
            int iR = k;      // cell to the right of interface

            Vec<Real, 4> qL_left{}, qL_right{};  // MUSCL-Hancock for left cell
            Vec<Real, 4> qR_left{}, qR_right{};  // MUSCL-Hancock for right cell

            muscl_hancock_x(cgv, iL, 0, dt, m_gamma, qL_left, qL_right);
            muscl_hancock_x(cgv, iR, 0, dt, m_gamma, qR_left, qR_right);

            // At interface k: use right face of left cell, left face of right cell
            flux[k] = hllc_flux(qL_right, qR_left, m_gamma);
        }

        // 4. Conservative update: U_i -= (dt/dx) * (flux[i+1] - flux[i])
        //    flux[i] is the flux at interface i (left of cell i)
        //    flux[i+1] is the flux at interface i+1 (right of cell i)
        Real dtdx = dt / gv.dx;
        for (int i = 0; i < nx; ++i) {
            for (int v = 0; v < 4; ++v) {
                gv(i, 0, v) -= dtdx * (flux[i + 1][v] - flux[i][v]);
            }
        }

        // 5. Advance time
        m_time += dt;
        m_step++;
    }

    // Run until t >= t_end.
    void run() {
        while (m_time < m_t_end) {
            step();
        }
    }
};

} // namespace hrsc
```

- [ ] **Step 4: Build and run tests**

```bash
cmake -B build -S . -G Ninja && cmake --build build && PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[solver]"
```

Expected: All 3 solver tests PASS.

- [ ] **Step 5: Run all tests to check for regressions**

```bash
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests
```

Expected: ALL tests PASS (existing + new).

- [ ] **Step 6: Commit**

```bash
git add src/euler/euler_solver.hpp tests/unit/test_euler.cpp
git commit -m "feat(euler): add EulerSolver class with CFL, stepping, and run loop"
```

---

## Task 8: Wire Up main.cpp

**Files:**
- Rewrite: `src/main.cpp`
- Modify: `CMakeLists.txt` (add include path for test cases)

- [ ] **Step 1: Add test cases include path to CMakeLists.txt**

In `CMakeLists.txt`, after the `target_link_libraries(hrsc PRIVATE hrsc_core)` line, add:

```cmake
target_include_directories(hrsc PRIVATE ${CMAKE_SOURCE_DIR}/tests/cases)
```

Also add the same for `unit_tests`, after the `external/catch2` include line:

```cmake
target_include_directories(unit_tests PRIVATE ${CMAKE_SOURCE_DIR}/tests/cases)
```

- [ ] **Step 2: Rewrite main.cpp**

Replace the contents of `src/main.cpp` with:

```cpp
#include "utils/config.hpp"
#include "core/eos.hpp"
#include "euler/euler_solver.hpp"
#include "toro_1d/toro_tests.hpp"

#include <iostream>
#include <iomanip>
#include <string>
#include <stdexcept>

using namespace hrsc;

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: hrsc <config_file>\n";
        return 1;
    }

    Config cfg(argv[1]);

    std::string test = cfg.get_string("test");
    int    nx    = cfg.get_int("nx", 200);
    double xmin  = cfg.get_double("xmin", 0.0);
    double xmax  = cfg.get_double("xmax", 1.0);
    double gamma = cfg.get_double("gamma", 1.4);
    double cfl   = cfg.get_double("cfl", 0.8);
    double t_end = cfg.get_double("t_end", 0.25);

    double dx = (xmax - xmin) / nx;

    EulerSolver<double> solver(nx, dx, gamma, cfl, t_end);

    // Set initial conditions
    if (test == "sod") {
        setup_sod(solver.grid_view(), gamma);
    } else {
        throw std::runtime_error("Unknown test: " + test);
    }

    // Run solver
    solver.run();

    std::cerr << "Finished: " << solver.step_count() << " steps, t = "
              << solver.time() << "\n";

    // Output: x  rho  u  v  p  (one cell per line)
    auto gv = solver.grid_view();
    std::cout << std::setprecision(12);
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

    return 0;
}
```

- [ ] **Step 3: Build the main executable**

```bash
cmake -B build -S . -G Ninja && cmake --build build
```

Expected: Compiles successfully.

- [ ] **Step 4: Run the Sod test**

```bash
PATH="/c/Strawberry/c/bin:$PATH" ./build/hrsc tests/cases/toro_1d/sod.cfg > output/sod_result.txt 2>output/sod_log.txt
```

Expected: `sod_log.txt` shows step count and final time ~0.25. `sod_result.txt` has 200 lines of `x rho u v p`.

- [ ] **Step 5: Verify output looks physically correct**

```bash
head -5 output/sod_result.txt && echo "..." && tail -5 output/sod_result.txt
```

Expected:
- First few lines: `rho` near 1.0, `u` near 0, `p` near 1.0 (left state, slightly modified by rarefaction)
- Last few lines: `rho` near 0.125, `u` near 0, `p` near 0.1 (right state, unperturbed)

- [ ] **Step 6: Run all unit tests to confirm no regressions**

```bash
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests
```

Expected: ALL tests PASS.

- [ ] **Step 7: Commit**

```bash
git add src/main.cpp CMakeLists.txt
git commit -m "feat: wire main.cpp to config-driven Sod solver with text output"
```

---

## Task 9: Final Validation and Cleanup

**Files:** No new files. Verification only.

- [ ] **Step 1: Run full test suite**

```bash
cmake -B build -S . -G Ninja && cmake --build build && PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests
```

Expected: ALL tests PASS. Note the total count (should be ~65+ assertions).

- [ ] **Step 2: Run Sod test and spot-check key values**

```bash
PATH="/c/Strawberry/c/bin:$PATH" ./build/hrsc tests/cases/toro_1d/sod.cfg > output/sod_result.txt 2>output/sod_log.txt
```

Spot-check the output against known Sod solution at t=0.25 (Toro 2009, Table 4.1):

| Region | x range | rho | u | p |
|--------|---------|-----|---|---|
| Left undisturbed | 0 - 0.26 | 1.0 | 0.0 | 1.0 |
| Rarefaction fan | 0.26 - 0.49 | decreasing | increasing | decreasing |
| Contact left | 0.49 - 0.69 | ~0.426 | ~0.927 | ~0.303 |
| Contact right | 0.69 - 0.85 | ~0.265 | ~0.927 | ~0.303 |
| Shock right | 0.85+ | 0.125 | 0.0 | 0.1 |

```bash
# Check a cell in the left undisturbed region (cell ~20, x≈0.1)
sed -n '20p' output/sod_result.txt
# Check a cell in the contact region (cell ~120, x≈0.6)
sed -n '120p' output/sod_result.txt
# Check a cell in the right undisturbed region (cell ~190, x≈0.95)
sed -n '190p' output/sod_result.txt
```

Expected: Values should qualitatively match the table above. Exact match requires exact Riemann solver (Week 3).

- [ ] **Step 3: Verify build works with RIEMANN_STRICT_INEQUALITY=ON**

```bash
cmake -B build_strict -S . -G Ninja -DRIEMANN_STRICT_INEQUALITY=ON && cmake --build build_strict
PATH="/c/Strawberry/c/bin:$PATH" ./build_strict/unit_tests
PATH="/c/Strawberry/c/bin:$PATH" ./build_strict/hrsc tests/cases/toro_1d/sod.cfg > /dev/null 2>&1
```

Expected: Compiles, tests pass, Sod runs without error.

- [ ] **Step 4: Commit any fixes if needed, then tag completion**

If everything passes with no changes needed:
```bash
echo "Week 2 milestone complete: 1D MUSCL-Hancock + HLLC Euler solver passing Sod test"
```

If fixes were needed, commit them:
```bash
git add -A && git commit -m "fix: address Week 2 validation issues"
```
