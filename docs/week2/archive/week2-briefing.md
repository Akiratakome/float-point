# Week 2 Briefing: 1D Euler Solver

## What Was Built in Week 1

### File Map

| File | Role |
|------|------|
| `src/core/types.hpp` | `HD_FUNC` macro, `NgHost = 2`, `Constants<Real>::Gamma / GammaM1` |
| `src/core/vec.hpp` | `Vec<Real, N>` POD aggregate with element-wise arithmetic, `dot()`, `norm_sq()` |
| `src/core/grid.hpp` | `Grid2D<Real, NVars>` (owning, host) + `GridView` / `ConstGridView` (trivially copyable, GPU-portable) |
| `src/core/eos.hpp` | `EulerVar` enum, `pressure()`, `sound_speed()`, `cons_to_prim()`, `prim_to_cons()` |
| `src/core/boundary.hpp` | `apply_outflow_bc()` — transmissive BCs with ghost cell filling |
| `src/utils/config.hpp` | Key=value parser, stream-injectable for testing |
| `src/main.cpp` | Stub — not yet wired to anything |

### Test Coverage

51 test cases, 788 assertions across 6 test files (`tests/unit/test_*.cpp`).  
Framework: Catch2 v2 single-header, vendored at `external/catch2/`.

### Build

```bash
cmake -B build -S . -G Ninja
cmake --build build
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests
```

Note: on this machine the MinGW `libstdc++-6.dll` requires `/c/Strawberry/c/bin` in PATH for the test executable.

---

## API Surface Available for Week 2

### Vec<Real, N> (`core/vec.hpp`)

```cpp
Vec<Real, 4> q = {rho, rho_u, rho_v, E};
q[EulerVar::RHO];                       // subscript
Vec<Real, 4> sum = a + b;               // element-wise +, -, *, /
Vec<Real, 4> scaled = q * Real(0.5);    // scalar *, /
q += delta;                             // compound assignment
Real d = dot(a, b);                     // inner product
```

All operations are `HD_FUNC` and work on GPU.

### Grid2D / GridView (`core/grid.hpp`)

```cpp
Grid2D<Real, 4> grid(nx, ny);    // allocates (nx+2*ng)*(ny+2*ng)*4 Reals, zero-init
grid.dx = Lx / nx;               // set before calling view()
grid.dy = Ly / ny;

GridView<Real, 4> gv = grid.view();  // lightweight value type
gv(i, j, var) = value;               // physical: i in [0, nx), j in [0, ny)
gv(-1, j, var);                       // ghost cell access: up to ng layers
```

**1D mode**: set `ny = 1`, loop `i` only. Ghost cells and BCs work unchanged.

Index layout: `((j+ng) * nx_total + (i+ng)) * NVars + var` — contiguous in `var`, then `i`, then `j`.

### EOS (`core/eos.hpp`)

```cpp
Real p = pressure(cons, gamma);
Real a = sound_speed(rho, p, gamma);
Vec<Real,4> prim = cons_to_prim(cons, gamma);
Vec<Real,4> cons = prim_to_cons(prim, gamma);
```

`EulerVar` enum: `RHO=0, RHOU=1, RHOV=2, EN=3`.

### Boundary (`core/boundary.hpp`)

```cpp
apply_outflow_bc(grid.view());  // fills all ghost layers, handles corners
```

Host-only. Operates on `GridView<Real, NVars>`.

### Config (`utils/config.hpp`)

```cpp
Config cfg(input_stream);             // or Config cfg("filename.ini")
int nx   = cfg.get_int("nx", 100);
double g = cfg.get_double("gamma", 1.4);
std::string s = cfg.get_string("output_dir", "output/");
bool b = cfg.get_bool("verbose", false);
```

**Not yet wired to `main.cpp`** — Week 2 should connect this.

### Constants (`core/types.hpp`)

```cpp
Constants<Real>::Gamma    // 1.4
Constants<Real>::GammaM1  // 0.4
NgHost                     // 2 (ghost cell count, used by Grid2D and GridView)
```

---

## Naming Conventions (CSC Guidelines)

| Category | Convention | Example |
|----------|-----------|---------|
| Namespace | lowercase | `hrsc` |
| Class / struct | PascalCase | `Grid2D`, `GridView`, `Config` |
| Template params | `Real`, `NVars`, `N`, `Ptr` | |
| Functions | snake_case | `cons_to_prim()`, `apply_outflow_bc()` |
| Constants | PascalCase (in struct) | `Constants<Real>::Gamma` |
| Global constexpr | PascalCase | `NgHost` |
| Private members | `m_` prefix | `m_entries` |
| Enums | PascalCase values | `EulerVar::RHO`, `EulerVar::RHOU` |
| Files | snake_case `.hpp` / `.cpp` | `grid.hpp`, `test_grid.cpp` |
| Macros | ALL_CAPS | `HD_FUNC` |

---

## Known Issues / Recommendations for Week 2

### 1. `PrimVar` enum needed

`cons_to_prim()` returns `{rho, u, v, p}` but there is no `PrimVar` enum — code currently reuses `EulerVar` indices to access primitive variables, which is numerically correct but semantically misleading (`prim[RHOU]` reads velocity `u`, not momentum). Before implementing flux or Riemann solver, add:

```cpp
enum PrimVar : int { PRHO = 0, VX = 1, VY = 2, PRES = 3 };
```

### 2. Config not connected

`main.cpp` is a stub. Week 2 should wire `Config` to read simulation parameters (nx, gamma, CFL, t_end, etc.) and drive the solver loop.

### 3. `view()` captures by value

`GridView` is a snapshot of `{data pointer, nx, ny, dx, dy}`. If you resize `Grid2D` or change `dx`/`dy` after calling `view()`, the view is stale. Always set `dx`/`dy` before `view()`.

### 4. Ghost cell count

`NgHost = 2` supports up to 2nd-order reconstruction. If higher-order stencils are needed later, only `types.hpp` needs to change.

---

## Extension Points for Week 2 (1D Euler Solver)

New files to create:

| File | Purpose |
|------|---------|
| `src/core/flux.hpp` | Physical flux `F(U)` for Euler equations |
| `src/core/riemann.hpp` | Approximate Riemann solver (HLL / HLLC / Rusanov) |
| `src/core/reconstruct.hpp` | Piecewise-linear reconstruction with slope limiters |
| `src/core/solver.hpp` | Time-stepping loop (forward Euler or SSP-RK2) |

Suggested function signatures (all `HD_FUNC`, templated on `<Real>`):

```cpp
// Physical flux in x-direction
Vec<Real,4> euler_flux_x(const Vec<Real,4>& cons, Real gamma);

// Riemann solver at interface
Vec<Real,4> hll_flux(const Vec<Real,4>& qL, const Vec<Real,4>& qR, Real gamma);

// Slope-limited reconstruction: returns (qL, qR) at cell interface i+1/2
std::pair<Vec<Real,4>, Vec<Real,4>> reconstruct(
    ConstGridView<Real,4> grid, int i, int j, int axis);

// Single time step
void step(GridView<Real,4> grid, Real dt, Real gamma);
```

The existing `Grid2D` with `ny=1` gives a ready-made 1D domain. Use `ConstGridView` for read-only access in reconstruction and flux computation.
