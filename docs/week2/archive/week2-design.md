# Week 2 Design: 1D Euler Solver

## Overview

Build a complete 1D Euler solver using the MUSCL-Hancock method with HLLC Riemann solver, capable of running the Sod shock tube test. All new Euler-specific code lives in `src/euler/`, following the master plan's directory structure.

## Architecture: Cell-Interface Pipeline

Each time step follows a cell-interface pipeline:

1. **Per cell `i`:** MUSCL reconstruct boundary-extrapolated values → Hancock half-step evolve
2. **Per interface `i+1/2`:** Feed evolved right-face of cell `i` and left-face of cell `i+1` into HLLC → intercell flux
3. **Conservative update:** `U_i^{n+1} = U_i^n - dt/dx * (F_{i+1/2} - F_{i-1/2})`

This mirrors the GPU kernel separation planned for Weeks 5-6 — each function becomes a kernel.

## File Structure

| File | Type | Responsibility |
|------|------|----------------|
| `src/core/eos.hpp` | Modify | Add `PrimVar` enum (`PRHO=0, VX=1, VY=2, PRES=3`) |
| `src/euler/euler_flux.hpp` | New | `euler_flux_x(cons, gamma)` → physical flux F(U) |
| `src/euler/muscl.hpp` | New | `minmod(a, b)`, `muscl_reconstruct_x(grid, i, j, qL, qR)` |
| `src/euler/hancock.hpp` | New | `muscl_hancock_x(grid, i, j, dt, gamma, qL, qR)` — calls `muscl_reconstruct_x` internally |
| `src/euler/hllc.hpp` | New | `hllc_flux(qL, qR, gamma)` with `RIEMANN_STRICT_INEQUALITY` compile flag |
| `src/euler/euler_solver.hpp` | New | `EulerSolver<Real>` class: CFL computation, time stepping, run loop |
| `tests/cases/toro_1d/toro_tests.hpp` | New | `setup_sod(grid, gamma)` IC function |
| `tests/cases/toro_1d/sod.cfg` | New | Sod test configuration |
| `src/main.cpp` | Rewrite | Config-driven: read cfg → select IC → run solver → text output |
| `tests/unit/test_euler.cpp` | New | Unit tests for all new components |
| `CMakeLists.txt` | Modify | Add `RIEMANN_STRICT_INEQUALITY` option |

### Dependency Chain

```
vec.hpp, eos.hpp
  ← euler_flux.hpp
      ← muscl.hpp (+ grid.hpp)
      ← hancock.hpp (calls muscl_reconstruct_x + euler_flux_x)
      ← hllc.hpp
          ← euler_solver.hpp (+ boundary.hpp)
              ← main.cpp
              ← toro_tests.hpp
```

All new Euler files are header-only templates. No `.cpp` with explicit instantiation until Week 4 (float/double templating).

## Component Details

### 1. PrimVar Enum (modify `src/core/eos.hpp`)

```cpp
enum PrimVar : int { PRHO = 0, VX = 1, VY = 2, PRES = 3 };
```

Resolves the semantic mismatch where `prim[RHOU]` reads velocity, not momentum.

### 2. Euler Flux (`src/euler/euler_flux.hpp`)

```cpp
template <typename Real>
HD_FUNC Vec<Real, 4> euler_flux_x(const Vec<Real, 4>& cons, Real gamma);
```

Computes `F(U) = { rho*u, rho*u² + p, rho*u*v, u*(E + p) }`.
Calls `pressure()` internally. X-direction only (y-direction added in Week 4).

### 3. MUSCL Reconstruction (`src/euler/muscl.hpp`)

```cpp
template <typename Real>
HD_FUNC Real minmod(Real a, Real b);

template <typename Real>
HD_FUNC void muscl_reconstruct_x(
    ConstGridView<Real, 4> grid, int i, int j,
    Vec<Real, 4>& q_left, Vec<Real, 4>& q_right);
```

- Reconstructs boundary-extrapolated values at left face (`i-1/2`) and right face (`i+1/2`) of cell `i`
- Component-wise on conserved variables
- Reads cells `i-1, i, i+1` → needs stencil width of 1 (within `NgHost=2`)
- Week 2: minmod only. Van Leer and MC limiters added in Week 3.

### 4. Hancock Predictor (`src/euler/hancock.hpp`)

```cpp
template <typename Real>
HD_FUNC void muscl_hancock_x(
    ConstGridView<Real, 4> grid, int i, int j,
    Real dt, Real gamma,
    Vec<Real, 4>& q_left, Vec<Real, 4>& q_right);
```

1. Calls `muscl_reconstruct_x` → raw `(q_left, q_right)`
2. Computes `F(q_left)` and `F(q_right)` via `euler_flux_x`
3. Evolves both by half-step: `q += 0.5 * (dt/dx) * (F(q_left) - F(q_right))`
4. Returns evolved `(q_left, q_right)`

Note: reads `grid.dx` from the view for the `dt/dx` ratio.

### 5. HLLC Riemann Solver (`src/euler/hllc.hpp`)

```cpp
template <typename Real>
HD_FUNC Vec<Real, 4> hllc_flux(const Vec<Real, 4>& qL, const Vec<Real, 4>& qR, Real gamma);
```

**Wave speed estimates (Davis):**
```
SL = min(uL - aL, uR - aR)
SR = max(uL + aL, uR + aR)
```

**Contact wave speed:**
```
S* = (pR - pL + rhoL*uL*(SL - uL) - rhoR*uR*(SR - uR))
     / (rhoL*(SL - uL) - rhoR*(SR - uR))
```

**Flux selection — matches master plan snippet exactly:**
```cpp
#ifdef RIEMANN_STRICT_INEQUALITY
if (SL < Real(0) && Real(0) < S_star)
#else
if (SL <= Real(0) && Real(0) <= S_star)
#endif
```

Star-state flux: `F*K = FK + SK * (U*K - UK)`.

### 6. Euler Solver (`src/euler/euler_solver.hpp`)

```cpp
template <typename Real>
class EulerSolver {
    Grid2D<Real, 4> m_grid;
    Real m_gamma, m_cfl, m_t_end;
    Real m_time;
    int m_step;

public:
    EulerSolver(int nx, Real dx, Real gamma, Real cfl, Real t_end);
    GridView<Real, 4> grid_view();
    Real compute_dt() const;
    void step();
    void run();
};
```

**`compute_dt()`:** Scans all physical cells, returns `CFL * dx / max_all(|u| + a)`. Last step clipped to `t_end`.

**`step()` flow:**
1. `apply_outflow_bc(grid_view())`
2. `dt = compute_dt()`
3. Allocate `std::vector<Vec<Real,4>> flux(nx+1)` for interface fluxes
4. For each interface `i+1/2` (interface index `0` to `nx`, i.e., `nx+1` interfaces spanning from left boundary to right boundary):
   - `muscl_hancock_x(grid, i, 0, ...)` → `q_i_right`
   - `muscl_hancock_x(grid, i+1, 0, ...)` → `q_{i+1}_left`
   - `hllc_flux(q_i_right, q_{i+1}_left, gamma)` → `flux[i+1]`
5. Conservative update: `U_i -= (dt/dx) * (flux[i+1] - flux[i])`
6. `m_time += dt; m_step++`

### 7. Test IC & Config

**`toro_tests.hpp`:**
```cpp
template <typename Real>
void setup_sod(GridView<Real, 4> grid, Real gamma);
```

Sod IC: discontinuity at `x = 0.5`, domain `[0, 1]`.
- Left: `rho=1.0, u=0, p=1.0`
- Right: `rho=0.125, u=0, p=0.1`

Uses `prim_to_cons` to fill conserved variables.

**`sod.cfg`:**
```ini
test = sod
nx = 200
xmin = 0.0
xmax = 1.0
gamma = 1.4
cfl = 0.8
t_end = 0.25
bc = outflow
```

### 8. Main (`src/main.cpp`)

Reads `argv[1]` as config file path. Parses parameters, creates `EulerSolver`, calls IC setup function based on `test` field, runs solver, outputs `x rho u p` per cell line to stdout.

No binary IO this week — text output sufficient for validation.

### 9. CMake Changes

```cmake
option(RIEMANN_STRICT_INEQUALITY "Use strict < instead of <= in HLLC/HLLD" OFF)
if(RIEMANN_STRICT_INEQUALITY)
    target_compile_definitions(hrsc_core INTERFACE RIEMANN_STRICT_INEQUALITY)
endif()
```

## Unit Tests (`tests/unit/test_euler.cpp`)

| Component | Test | Assertion |
|-----------|------|-----------|
| `euler_flux_x` | Stationary gas (`u=0`) | Flux = `{0, p, 0, 0}` |
| `euler_flux_x` | Known uniform flow | Matches analytic flux |
| `hllc_flux` | Identical left/right | Returns `euler_flux_x` result |
| `hllc_flux` | Symmetric states | Flux symmetry holds |
| `muscl_reconstruct_x` | Uniform field | `q_left == q_right == U_i` |
| `muscl_reconstruct_x` | Linear field | Exact gradient recovery |
| `muscl_reconstruct_x` | Discontinuity | Limiter activates (slope compressed) |
| `muscl_hancock_x` | Uniform field | No change after half-step |
| `EulerSolver` (Sod) | Run to t=0.25 | Density in `[0.125, 1.0]`, mass conserved |

## Out of Scope (Week 2)

- Binary IO (`io.hpp`) → Week 3
- Y-sweep / 2D → Week 4
- Float template instantiation → Week 4
- Van Leer / MC limiters → Week 3
- Exact Riemann solver → Week 3
- Error norm computation → Week 3

## Validation Milestone

Sod shock tube on 200 cells at `t=0.25` produces density/velocity/pressure profiles showing a clean shock, contact discontinuity, and rarefaction fan with no spurious oscillations.
