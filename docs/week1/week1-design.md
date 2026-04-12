# Week 1 Design Spec: Foundation — Core Infrastructure

**Date:** 2026-04-02
**Scope:** Week 1 of 20-week HRSC floating-point precision project
**Approach:** Template on `<Real>` from day one, build `double` only for now
**Toolchain:** WSL / Linux (gcc/g++), targeting CSC cluster later
**Testing:** Catch2 v2 (single-header, vendored)

---

## 1. Project Structure

```
CMakeLists.txt
.gitignore
external/
  catch2/
    catch.hpp                    # Catch2 v2 single header (vendored)
src/
  main.cpp                       # Stub entry point
  core/                          # Core logic (templates -> headers)
    types.hpp                    # HD_FUNC macro, namespace hrsc, Constants<Real>
    vec.hpp                      # Vec<Real,N> aggregate with arithmetic
    grid.hpp                     # GridViewBase, GridView, ConstGridView, Grid2D
    eos.hpp                      # Ideal gas EOS free functions
    boundary.hpp                 # Outflow (transmissive) BCs
  utils/
    config.hpp                   # key=value config parser
  euler/                         # (empty, Week 2)
  mhd/                           # (empty, Week 12)
  gpu/                           # (empty, Week 5)
output/                          # Runtime data output (gitignored)
tests/
  unit/
    test_main.cpp                # #define CATCH_CONFIG_MAIN only
    test_vec.cpp
    test_grid.cpp
    test_eos.cpp
    test_config.cpp
    test_boundary.cpp
  cases/                         # Simulation ICs + config files
    toro_1d/                     # (Week 2+)
    liska_wendroff_2d/           # (Week 5)
    shock_bubble/                # (Week 5)
    orszag_tang/                  # (Week 13)
    kelvin_helmholtz/            # (Week 13)
```

### .gitignore

Ignore: `build/`, `output/`, `*.o`, `*.bin`, `*.dat`, `*.csv`, IDE files, `.vscode/`, `__pycache__/`.

---

## 2. Build System (CMakeLists.txt)

- `cmake_minimum_required(VERSION 3.18)` — good CUDA support later
- C++17 standard, flags: `-Wall -Wextra -Wpedantic -O2`
- Option `FLOAT_PRECISION` defaulting to `double` (variable only, switching in Week 4)
- **INTERFACE library** `hrsc_core`:
  - `add_library(hrsc_core INTERFACE)`
  - `target_include_directories(hrsc_core INTERFACE ${CMAKE_SOURCE_DIR}/src)`
  - Both `hrsc` and `unit_tests` link via `target_link_libraries(... hrsc_core)`
- Target `hrsc`: `src/main.cpp` (stub)
- Target `unit_tests`: all `tests/unit/test_*.cpp`, links `hrsc_core` + Catch2 include path

---

## 3. types.hpp — Namespace & Portability Macro

```cpp
#pragma once

#ifdef __CUDACC__
  #define HD_FUNC __host__ __device__
#else
  #define HD_FUNC
#endif

namespace hrsc {

template <typename Real>
struct Constants {
    static constexpr Real gamma   = static_cast<Real>(1.4);
    static constexpr Real gamma_m1 = static_cast<Real>(0.4);
};

} // namespace hrsc
```

- `HD_FUNC` defined outside the namespace (macro, not a symbol)
- All constants use `static_cast<Real>()` to avoid `-Wconversion` with `Real=float`
- Everything else in the project lives inside `namespace hrsc`

---

## 4. vec.hpp — Vec<Real, N>

**Pure aggregate (structural/POD type)** — no custom constructors, no destructors:

```cpp
namespace hrsc {

template <typename Real, int N>
struct Vec {
    Real data[N];

    HD_FUNC Real& operator[](int i)       { return data[i]; }
    HD_FUNC const Real& operator[](int i) const { return data[i]; }
};

// Free functions (element-wise arithmetic, all HD_FUNC):
// operator+, operator-, operator*, operator/ (Vec-Vec and Vec-scalar)
// operator+=, -=, *=, /=
// dot(a, b), norm_sq(a)

} // namespace hrsc
```

- Aggregate initialization: `Vec<Real, 3> v = {1, 2, 3};`
- No dynamic allocation, no STL — GPU-safe
- All operators return by value (RVO)

### Tests (test_vec.cpp)
- Aggregate initialization
- Element-wise arithmetic correctness with `Approx`
- Scalar multiplication/division
- `dot()` and `norm_sq()` against hand-computed values
- Edge cases: zero vector, negative values
- Epsilon-aware: scale `Approx` tolerance for float vs double

---

## 5. config.hpp — Key=Value Config Parser

**Strictly header-only**, all definitions inline or inside class body.

```cpp
namespace hrsc {

class Config {
    std::unordered_map<std::string, std::string> entries_;

    void parse(std::istream& is);  // core parsing logic

public:
    explicit Config(std::istream& is);          // in-memory (for testing)
    explicit Config(const std::string& filename); // opens ifstream, delegates

    std::string get_string(const std::string& key, const std::string& def = "") const;
    int         get_int(const std::string& key, int def = 0) const;
    double      get_double(const std::string& key, double def = 0.0) const;
    bool        get_bool(const std::string& key, bool def = false) const;
};

} // namespace hrsc
```

### Parsing rules
- Lines starting with `#` → comment, skip
- Blank lines → skip
- Split on first `=`, strip whitespace from key and value
- Lines without `=` → skip silently (or warn)

### Error handling
- Missing file → `std::runtime_error("Cannot open config file: <path>")`
- `get_int` / `get_double` catch `std::invalid_argument` / `std::out_of_range` from `std::stoi`/`std::stod` → rethrow as `std::runtime_error("Failed to parse key '<key>' as <type>")`
- `get_bool` accepts: `"true"`, `"false"`, `"1"`, `"0"` → anything else throws
- Missing key → returns default (no error)

### Tests (test_config.cpp)
- Parse via `std::stringstream` (no temp files)
- Verify all getter types with known values
- Missing key returns default
- Comments, blank lines, extra whitespace handled
- `get_int` with non-numeric value → throws with key name
- `get_bool` with `"true"` / `"1"` / invalid

---

## 6. grid.hpp — Container-View Separation

### GridViewBase<Real, NVars, Ptr> — const-generic accessor

```cpp
namespace hrsc {

template <typename Real, int NVars, typename Ptr>
struct GridViewBase {
    Ptr data;
    int nx, ny;
    Real dx, dy;
    static constexpr int ng = 2;

    HD_FUNC int nx_total() const { return nx + 2 * ng; }
    HD_FUNC int ny_total() const { return ny + 2 * ng; }

    HD_FUNC int index(int i, int j, int var) const {
        return ((j + ng) * nx_total() + (i + ng)) * NVars + var;
    }

    HD_FUNC auto operator()(int i, int j, int var) -> decltype(data[0]) {
        return data[index(i, j, var)];
    }
    HD_FUNC auto operator()(int i, int j, int var) const -> decltype(data[0]) {
        return data[index(i, j, var)];
    }
};

template <typename Real, int NVars>
using GridView = GridViewBase<Real, NVars, Real*>;

template <typename Real, int NVars>
using ConstGridView = GridViewBase<Real, NVars, const Real*>;

} // namespace hrsc
```

- Trivially copyable — pass by value to CUDA kernels
- `i ∈ [-ng, nx+ng)`, `j ∈ [-ng, ny+ng)` — full range including ghosts
- Layout: row-major, variable-last: `((j+ng) * nx_total + (i+ng)) * NVars + var`

### Grid2D<Real, NVars> — owning container

```cpp
namespace hrsc {

template <typename Real, int NVars>
struct Grid2D {
    int nx, ny;
    static constexpr int ng = 2;
    std::vector<Real> data;
    Real dx, dy;

    Grid2D(int nx, int ny);
    // Allocates (nx + 2*ng) * (ny + 2*ng) * NVars elements, zero-fills

    GridView<Real, NVars> view();
    ConstGridView<Real, NVars> view() const;
};

} // namespace hrsc
```

- Strictly host-only — no `HD_FUNC` anywhere
- `view()` / `view() const` bridge to the GPU-compatible accessor

### GPU path (Week 5 preview, not built now)
`gpu/gpu_grid.cuh` will `cudaMalloc` device memory, `cudaMemcpy` from `Grid2D::data`, construct a `GridView` with the device pointer. Solver kernels receive `GridView` — same interface, different pointer.

### Tests (test_grid.cpp)
- Verify allocation size = `nx_total * ny_total * NVars`
- Write/read via `view()` at physical cells and ghost cells
- Verify exact position in raw `data.data()[]` matches expected index formula
- `ConstGridView` from `view() const` — read-only access compiles, write fails to compile
- 1D mode (`ny=1`): y-offset arithmetic correct
- Zero-initialization of all cells

---

## 7. eos.hpp — Ideal Gas Equation of State

All free functions in `namespace hrsc`, templated on `<typename Real>`, all `HD_FUNC`.
Operate on `Vec<Real, 4>` (Euler conserved: rho, rho*u, rho*v, E).

```cpp
// Returns pressure from conserved variables
template <typename Real>
HD_FUNC Real pressure(const Vec<Real, 4>& cons, Real gamma);
// p = (gamma - 1) * (E - 0.5 * (rho_u^2 + rho_v^2) / rho)

// Returns sound speed
template <typename Real>
HD_FUNC Real sound_speed(Real rho, Real p, Real gamma);
// a = sqrt(gamma * p / rho)  — uses std::sqrt from <cmath>

// Conserved -> Primitive: {rho, u, v, p}
template <typename Real>
HD_FUNC Vec<Real, 4> cons_to_prim(const Vec<Real, 4>& cons, Real gamma);

// Primitive -> Conserved: {rho, rho*u, rho*v, E}
template <typename Real>
HD_FUNC Vec<Real, 4> prim_to_cons(const Vec<Real, 4>& prim, Real gamma);
```

### Design rules
- All literals explicitly cast: `Real(0.5)`, `static_cast<Real>(...)`.
- `std::sqrt` from `<cmath>` — NVCC maps to device intrinsic automatically.
- `gamma` passed as argument, not hardcoded.
- Debug near-vacuum assert: `assert(rho > std::numeric_limits<Real>::min())` in kinetic energy division. Zero cost in release builds, catches NaN-producing states during development (critical for the 123 problem in Week 3).
- No pressure clamping — EOS computes faithfully, solver is responsible for positivity.

### Tests (test_eos.cpp)
- **Round-trip:** `prim -> cons -> prim` recovers original within epsilon
- **Sod left state:** rho=1.0, u=0, v=0, p=1.0, gamma=1.4 → verify E = 2.5, a = 1.1832...
- **Sod right state:** rho=0.125, u=0, v=0, p=0.1 → verify known values
- **Zero velocity:** kinetic energy exactly zero
- **Epsilon-aware:** tolerance scaled for float vs double

---

## 8. boundary.hpp — Outflow (Transmissive) BCs

Host-only orchestrator — **no `HD_FUNC`** on the grid-loop function.

```cpp
namespace hrsc {

template <typename Real, int NVars>
void apply_outflow_bc(GridView<Real, NVars> grid);

} // namespace hrsc
```

### Implementation
- **X-boundaries:** For each ghost layer `g ∈ {1, 2}`:
  - Left: copy cell `(0, j, var)` → `(-g, j, var)`
  - Right: copy cell `(nx-1, j, var)` → `(nx-1+g, j, var)`
- **Y-boundaries:** Same pattern in j-direction
- **1D mode (ny=1):** Y-boundaries still filled (copy the single physical row into y-ghost layers). Prevents uninitialized memory surprises.
- Iterates over all `NVars` at each cell

### GPU path (Week 5)
Separate CUDA kernels with `HD_FUNC` per-cell helpers, launched by a host orchestrator. Not built now.

### Tests (test_boundary.cpp)
- Small grid with known interior values, apply outflow, verify ghost cells match outermost physical cells
- All ghost layers (both `ng=1` and `ng=2` depth) filled correctly
- 1D mode: y-ghosts filled, x-data not corrupted

---

## 9. Implementation Order

Dependency graph:
```
types.hpp (no deps)
  -> vec.hpp (uses HD_FUNC)
  -> grid.hpp (uses HD_FUNC — no Vec dependency)
  -> eos.hpp (uses HD_FUNC, Vec<Real,4>)
  -> boundary.hpp (uses GridView)

config.hpp (standalone, no core deps)
```

Build sequence (each step: code -> test -> verify):

| Step | File | Test | Key Verification |
|------|------|------|-----------------|
| 1 | CMakeLists.txt + main.cpp + Catch2 | test_main.cpp compiles | Build system works |
| 2 | types.hpp | (tested via vec) | HD_FUNC, Constants |
| 3 | vec.hpp | test_vec.cpp | Arithmetic, dot, aggregate init |
| 4 | config.hpp | test_config.cpp | Parse, defaults, errors |
| 5 | grid.hpp | test_grid.cpp | Allocation, indexing, view const-correctness |
| 6 | eos.hpp | test_eos.cpp | Round-trip, Sod states, near-vacuum assert |
| 7 | boundary.hpp | test_boundary.cpp | Ghost cell fill, 1D mode |

---

## 10. Milestone Criteria

- `cmake --build build` succeeds with **zero warnings** (`-Wall -Wextra -Wpedantic`)
- `./unit_tests` passes all Catch2 tests
- Grid can be constructed in 1D mode (`ny=1`) ready for Week 2 solver
- All code inside `namespace hrsc`, all templates on `<Real>`
