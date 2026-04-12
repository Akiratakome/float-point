# Week 3 Briefing: 2D Euler Solver Extension

**Date:** 2026-04-11 (updated)  
**Prior:** Week 1 (core infrastructure) + Week 2 (1D MUSCL-Hancock + HLLC + Verificarlo analysis)  
**Branch:** main (`8460931`)

---

## 1. Week 2 Deliverables Summary

### 1.1 What Was Built

| Module | File | Status |
|--------|------|--------|
| PrimVar enum | `src/core/eos.hpp` | Done |
| Physical flux F(U) | `src/euler/euler_flux.hpp` | Done, x-direction only |
| MUSCL reconstruction | `src/euler/muscl.hpp` | Done, minmod limiter, x-direction |
| Hancock predictor | `src/euler/hancock.hpp` | Done, x-direction |
| HLLC Riemann solver | `src/euler/hllc.hpp` | Done, with `RIEMANN_STRICT_INEQUALITY` flag |
| Solver class | `src/euler/euler_solver.hpp` | Done, 1D x-sweep only |
| Test ICs | `tests/cases/toro_1d/toro_tests.hpp` | Toro Tests 1-5 |
| Main program | `src/main.cpp` | Config-driven, `setprecision(17)` output |
| Verification | `scripts/verify_toro.py` | Exact Riemann solver + plots |
| Verificarlo MCA | `scripts/verificarlo_run.sh` | MCA sampling (Docker-based) |
| Verificarlo analysis | `scripts/verificarlo_analysis.py` | Sig digits heatmaps + overlays |
| Error budget | `scripts/verificarlo_vs_exact.py` | FP noise vs discretisation error |

### 1.2 Test Coverage

- **Unit tests:** 70 cases, 1254 assertions, all passing
- **Verified:** Toro Tests 1-5 against exact Riemann solution (L1 norms O(10^-3) for standard cases)

### 1.3 Verificarlo Findings (Week 2)

- **MCA at double precision (53-bit):** rho maintains ≥11.7 significant digits; pressure drops to ~12 near strong shocks (HLLC S_star cancellation). Velocity shows negative sig digits in zero-velocity regions (MCA relative metric limitation, not a scheme defect).
- **FMA instrumentation:** ±0.06-0.18 sig digit impact — negligible. FMA is not the precision bottleneck.
- **VPREC precision sweep (Sod):** Error scales smoothly from 6.5×10⁻¹⁵ (48 bit) to 1.9×10⁻⁵ (16 bit). Float32 (24 bit) gives L1 error ~10⁻⁸ — viable for this problem. No catastrophic failure at any precision level.
- **Error budget:** The solver is overwhelmingly discretisation-limited at 200 cells in double precision. FP noise is 12-13 orders of magnitude below discretisation error near discontinuities.
- **`setprecision(17)` is now permanent** (was 12, which truncated MCA perturbations below visibility).

### 1.4 Known Deviations from Original Plan

1. **`GridViewBase<Real, 4, Ptr>` pattern**: MUSCL/Hancock functions accept both `GridView` and `ConstGridView` via a `Ptr` template parameter, instead of requiring `ConstGridView<Real, 4>`. This resolved template deduction failures and should be continued in all new grid-accessing functions.

2. **Toro Tests 2-5 added ahead of schedule**: Originally scoped for Week 3, already implemented with a generic `setup_riemann()` helper.

---

## 2. API Surface Available for Week 3

### 2.1 Core Types (`core/types.hpp`)

```cpp
HD_FUNC                           // __host__ __device__ under NVCC, empty otherwise
constexpr int NgHost = 2;         // ghost cell layers
Constants<Real>::Gamma             // 1.4
Constants<Real>::GammaM1           // 0.4
```

### 2.2 Vec<Real, N> (`core/vec.hpp`)

```cpp
Vec<Real, 4> q = {rho, rho_u, rho_v, E};
q[RHO];                              // subscript via EulerVar or PrimVar enum
Vec<Real, 4> sum = a + b;            // element-wise +, -, *, /
Vec<Real, 4> scaled = q * Real(0.5); // scalar *, /
q += delta;                          // compound assignment
Real d = dot(a, b);                  // inner product
```

### 2.3 Grid (`core/grid.hpp`)

```cpp
Grid2D<Real, NVars> grid(nx, ny);    // owning container, zero-init
grid.dx = Lx / nx;  grid.dy = Ly / ny;

GridView<Real, NVars> gv = grid.view();       // mutable
ConstGridView<Real, NVars> cgv = grid.view();  // const overload

gv(i, j, var) = value;     // i in [0, nx), j in [0, ny)
gv(-1, j, var);             // ghost: up to ng=2 layers
gv.nx; gv.ny; gv.dx; gv.dy; // metadata captured by value
```

**Layout:** `((j+ng) * nx_total + (i+ng)) * NVars + var` (AoS, row-major)

**1D mode:** `ny=1`, `j=0` throughout.

### 2.4 EOS (`core/eos.hpp`)

```cpp
enum EulerVar : int { RHO = 0, RHOU = 1, RHOV = 2, EN = 3 };
enum PrimVar  : int { PRHO = 0, VX = 1, VY = 2, PRES = 3 };

Real p = pressure(cons, gamma);
Real a = sound_speed(rho, p, gamma);
Vec<Real,4> prim = cons_to_prim(cons, gamma);   // returns {rho, u, v, p}
Vec<Real,4> cons = prim_to_cons(prim, gamma);   // returns {rho, rho*u, rho*v, E}
```

### 2.5 Boundary (`core/boundary.hpp`)

```cpp
apply_outflow_bc(grid.view());  // fills all ghost layers, handles corners
```

Host-only. Operates on `GridView<Real, NVars>`.

### 2.6 Euler Flux (`euler/euler_flux.hpp`)

```cpp
Vec<Real, 4> f = euler_flux_x(cons, gamma);
// F = {rho*u, rho*u^2+p, rho*u*v, u*(E+p)}
```

**Week 3 extension point:** Add `euler_flux_y(cons, gamma)`.

### 2.7 MUSCL Reconstruction (`euler/muscl.hpp`)

```cpp
template <typename Real>
HD_FUNC Real minmod(Real a, Real b);

template <typename Real, typename Ptr>
HD_FUNC void muscl_reconstruct_x(
    GridViewBase<Real, 4, Ptr> grid, int i, int j,
    Vec<Real, 4>& q_left, Vec<Real, 4>& q_right);
```

Component-wise on conserved variables. Stencil: `i-1, i, i+1`.

**Week 3 extension point:** Add `muscl_reconstruct_y` (stencil: `j-1, j, j+1`), and additional limiters (van Leer, MC).

### 2.8 Hancock Predictor (`euler/hancock.hpp`)

```cpp
template <typename Real, typename Ptr>
HD_FUNC void muscl_hancock_x(
    GridViewBase<Real, 4, Ptr> grid, int i, int j,
    Real dt, Real gamma,
    Vec<Real, 4>& q_left, Vec<Real, 4>& q_right);
```

MUSCL + flux-difference half-step evolution.

**Week 3 extension point:** Add `muscl_hancock_y`.

### 2.9 HLLC Solver (`euler/hllc.hpp`)

```cpp
template <typename Real>
HD_FUNC Vec<Real, 4> hllc_flux(
    const Vec<Real, 4>& qL, const Vec<Real, 4>& qR, Real gamma);
```

Direction-independent (operates on reconstructed face states). Can be called for both x- and y-interfaces directly.

### 2.10 Euler Solver (`euler/euler_solver.hpp`)

```cpp
template <typename Real>
class EulerSolver {
public:
    EulerSolver(int nx, Real dx, Real gamma, Real cfl, Real t_end);
    GridView<Real, 4> grid_view();
    Real compute_dt() const;
    void step();              // BC -> CFL -> interface fluxes -> update
    void run();               // loop step() until t >= t_end
    Real time() const;
    int  step_count() const;
};
```

**Current limitation:** 1D only (ny=1, x-sweep only). Week 3 must extend to 2D.

### 2.11 Config (`utils/config.hpp`)

```cpp
Config cfg("path/to/file.cfg");
int nx       = cfg.get_int("nx", 200);
double gamma = cfg.get_double("gamma", 1.4);
std::string s = cfg.get_string("test", "sod");
bool b       = cfg.get_bool("verbose", false);
```

### 2.12 Test ICs (`tests/cases/toro_1d/toro_tests.hpp`)

```cpp
setup_riemann(grid, gamma, x0, rhoL, uL, pL, rhoR, uR, pR);  // generic
setup_sod(grid, gamma);     // Toro 1
setup_toro2(grid, gamma);   // Toro 2 (123 problem)
setup_toro3(grid, gamma);   // Toro 3 (blast wave)
setup_toro4(grid, gamma);   // Toro 4 (Lax)
setup_toro5(grid, gamma);   // Toro 5 (slow contact)
```

---

## 3. Build & Test Commands

```bash
# Build
cmake -B build -S . -G Ninja && cmake --build build

# Run unit tests (Windows MinGW needs Strawberry in PATH)
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests

# Run specific test tag
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests "[hllc]"

# Run Sod shock tube (output is setprecision(17) by default)
PATH="/c/Strawberry/c/bin:$PATH" ./build/hrsc tests/cases/toro_1d/sod.cfg > output/sod_result.txt 2>/dev/null

# Verify all Toro tests + generate plots
python scripts/verify_toro.py

# Verificarlo analysis (Docker required)
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd):/work" -w /work \
    verificarlo/verificarlo bash scripts/verificarlo_run.sh
python scripts/verificarlo_analysis.py
python scripts/verificarlo_vs_exact.py
```

---

## 4. Naming Conventions

| Category | Convention | Example |
|----------|-----------|---------|
| Namespace | lowercase | `hrsc` |
| Class/struct | PascalCase | `EulerSolver`, `Grid2D`, `GridViewBase` |
| Template params | PascalCase | `Real`, `NVars`, `Ptr` |
| Free functions | snake_case | `euler_flux_x`, `muscl_hancock_x`, `hllc_flux` |
| Constants | PascalCase | `NgHost`, `Constants<Real>::Gamma` |
| Private members | `m_` prefix | `m_grid`, `m_gamma` |
| Enums | PascalCase values | `EulerVar::RHO`, `PrimVar::VX` |
| Files | snake_case `.hpp` | `euler_flux.hpp`, `euler_solver.hpp` |
| Macros | ALL_CAPS | `HD_FUNC`, `RIEMANN_STRICT_INEQUALITY` |
| Direction suffix | `_x` / `_y` | `euler_flux_x`, `muscl_reconstruct_y` |

---

## 5. Week 3 Objectives

Based on the Week 2 report's findings and supervisor feedback, Week 3 should cover:

### 5.1 Exact Riemann Solver (C++)

**Goal:** Implement an exact Riemann solver in C++ (not just the Python verification script) for reference solution generation and potential use as a fallback solver.

**Suggested file:** `src/euler/exact_riemann.hpp`

**Interface:**
```cpp
template <typename Real>
HD_FUNC void exact_riemann_sample(
    Real gamma, Real x_over_t,
    Real rhoL, Real uL, Real pL,
    Real rhoR, Real uR, Real pR,
    Real& rho, Real& u, Real& p);
```

**Key algorithms:**
- Newton-Raphson iteration on pressure function (Toro Ch.4)
- Left/right wave type determination (shock vs rarefaction)
- Sampling along x/t characteristic

**Testing:** Compare against Python exact solver results for all 5 Toro tests.

### 5.2 Additional Slope Limiters

**Goal:** Add van Leer and MC (monotonized central) limiters alongside minmod.

**Suggested approach:** Add to `src/euler/muscl.hpp`:

```cpp
template <typename Real> HD_FUNC Real vanleer(Real a, Real b);
template <typename Real> HD_FUNC Real mc_limiter(Real a, Real b);
```

Then parameterize `muscl_reconstruct_x` (and `_y`) to accept a limiter function, or use a compile-time/config option.

**Testing:** Rerun Toro Tests 1-5 with each limiter, compare L1 errors. Van Leer should reduce dissipation at contacts; MC should be sharpest but may show oscillations near strong shocks.

### 5.3 Y-Direction Extension

**Goal:** Add y-direction flux, reconstruction, and Hancock predictor.

**New functions:**
```cpp
// euler/euler_flux.hpp
template <typename Real>
HD_FUNC Vec<Real, 4> euler_flux_y(const Vec<Real, 4>& cons, Real gamma);
// G = {rho*v, rho*u*v, rho*v^2+p, v*(E+p)}

// euler/muscl.hpp
template <typename Real, typename Ptr>
HD_FUNC void muscl_reconstruct_y(
    GridViewBase<Real, 4, Ptr> grid, int i, int j,
    Vec<Real, 4>& q_bottom, Vec<Real, 4>& q_top);

// euler/hancock.hpp
template <typename Real, typename Ptr>
HD_FUNC void muscl_hancock_y(
    GridViewBase<Real, 4, Ptr> grid, int i, int j,
    Real dt, Real gamma,
    Vec<Real, 4>& q_bottom, Vec<Real, 4>& q_top);
```

**Note:** `hllc_flux` is already direction-independent. For y-interfaces, rotate the input states (swap `RHOU`/`RHOV`), call `hllc_flux`, then rotate the output flux back. Alternatively, write `hllc_flux_y` that uses v instead of u internally.

### 5.4 2D Euler Solver

**Goal:** Extend `EulerSolver` (or create `EulerSolver2D`) to perform dimensional splitting: x-sweep then y-sweep per time step.

**Suggested approach — Strang splitting:**
```
half-step y-sweep → full-step x-sweep → half-step y-sweep
```
Or simpler Godunov splitting:
```
full x-sweep → full y-sweep (alternating order each step)
```

**New constructor parameters:** `ny`, `dy`, `xmin`, `xmax`, `ymin`, `ymax`.

**CFL condition update:** `dt = CFL * min(dx, dy) / max(|u|+a, |v|+a)`.

### 5.5 Binary IO

**Goal:** Add binary output for large 2D data (text output becomes impractical).

**Suggested file:** `src/utils/io.hpp`

**Minimal interface:**
```cpp
template <typename Real, int NVars>
void write_binary(const std::string& filename, ConstGridView<Real, NVars> grid,
                  int nx, int ny, Real dx, Real dy, Real time);

template <typename Real, int NVars>
void read_binary(const std::string& filename, GridView<Real, NVars> grid,
                 int& nx, int& ny, Real& dx, Real& dy, Real& time);
```

**Format suggestion:** Simple header (nx, ny, dx, dy, time) + raw `Real` array. Keep it simple; VTK/HDF5 can come later if needed.

### 5.6 Error Norm Computation (C++)

**Goal:** Move L1/L2/Linf error computation from Python into C++ for use in convergence studies.

**Suggested file:** `src/utils/error_norms.hpp`

```cpp
template <typename Real>
struct ErrorNorms { Real L1, L2, Linf; };

template <typename Real>
ErrorNorms<Real> compute_error(const Real* numerical, const Real* exact,
                               int n, Real dx);
```

### 5.7 Grid Convergence Study

**Goal:** Run Sod on 50/100/200/400/800 cells, compute L1 error at each resolution, verify convergence order ~1.5-2.0 (limited by minmod limiter and discontinuities).

**Output:** Convergence table and log-log plot showing `L1 ~ dx^p`.

### 5.8 SLIC Flux Solver (Precision Comparison)

**Goal:** Implement the SLIC (Slope LImiter Centred) flux as an alternative to HLLC. SLIC uses a simpler centred formula that avoids the catastrophic cancellation in HLLC's S_star computation:

```
F_SLIC = 0.5 * (FL + FR) - 0.5 * |lambda_max| * (UR - UL)
```

**Suggested file:** `src/euler/slic.hpp`

**Interface:**
```cpp
template <typename Real>
HD_FUNC Vec<Real, 4> slic_flux(
    const Vec<Real, 4>& qL, const Vec<Real, 4>& qR, Real gamma);
```

**Purpose:** Run the same Verificarlo analysis on SLIC and compare sig digits / VPREC tolerance against HLLC. Expected result: SLIC tolerates lower precision (no S_star subtraction) but has worse physical accuracy (smeared contacts).

### 5.9 Unstable Branch Detection

**Goal:** Identify branch conditions in the HLLC solver that flip under floating-point perturbation.

**Method:** Run the solver at reduced precision (~40 bits via VPREC) and log which branch conditions (`if (SL >= 0)`, `if (S_star >= 0)`, etc.) produce different outcomes across MCA samples.

**Expected hot spots:**
1. `hllc.hpp` — `SL >= 0` when SL ≈ 0 (rarefaction wave head)
2. `hllc.hpp` — `S_star >= 0` when S_star ≈ 0 (contact discontinuity)
3. `muscl.hpp` — minmod sign check in flat regions

---

## 6. Suggested Task Priority

| Priority | Task | Rationale |
|----------|------|-----------|
| 1 | SLIC flux solver (5.8) | Direct precision comparison with HLLC; validates VPREC findings |
| 2 | Y-direction functions (5.3) | Foundation for all 2D work |
| 3 | 2D Euler Solver (5.4) | Enables 2D test cases |
| 4 | Unstable branch detection (5.9) | Identifies precision hot spots at reduced bit-width |
| 5 | Additional limiters (5.2) | Quick to add, useful for comparison |
| 6 | Grid convergence (5.7) | Validation milestone, combines with error norms |
| 7 | Binary IO (5.5) | Needed once 2D data gets large |
| 8 | Exact Riemann C++ (5.1) | Reference solver, already have Python version |
| 9 | Error norms C++ (5.6) | Convergence study support |

---

## 7. 2D Test Cases (Target Validation)

Once the 2D solver is operational:

| Test | Description | Reference |
|------|-------------|-----------|
| 2D Sod | 1D Sod along x-axis on 2D grid | Should match 1D results exactly |
| Oblique Sod | 1D Sod along diagonal | Tests dimensional splitting accuracy |
| 2D Riemann (Config 3) | Lax-Liu 2D Riemann problem | 4-quadrant IC, complex wave interactions |
| Sedov blast | Point explosion, cylindrical symmetry | Tests isotropy of the scheme |

---

## 8. Design Patterns to Follow

1. **`GridViewBase<Real, NVars, Ptr>` template pattern**: All grid-accessing functions should template on `Ptr` to accept both mutable and const views.

2. **`_x` / `_y` suffix convention**: Direction-specific functions use `_x` or `_y` suffix. Direction-independent functions (like `hllc_flux`) have no suffix.

3. **`HD_FUNC` on all numerical kernels**: Every function that will eventually run on GPU must be marked `HD_FUNC`.

4. **Header-only templates**: No `.cpp` files for templated code until Week 4 explicit instantiation.

5. **Test incrementally**: Write tests before or alongside each new function. Tag tests with Catch2 tags (`[flux]`, `[muscl]`, `[hllc]`, `[solver]`) for selective running.

---

## 9. File Structure After Week 3 (Expected)

```
src/
  core/
    types.hpp               # HD_FUNC, NgHost, Constants<Real>
    vec.hpp                 # Vec<Real, N>
    grid.hpp                # Grid2D, GridView, ConstGridView
    eos.hpp                 # EulerVar, PrimVar, pressure, sound_speed, cons/prim
    boundary.hpp            # apply_outflow_bc
  euler/
    euler_flux.hpp          # euler_flux_x, euler_flux_y        [NEW: _y]
    muscl.hpp               # minmod, vanleer, mc_limiter       [NEW: limiters]
                            # muscl_reconstruct_x, _y           [NEW: _y]
    hancock.hpp             # muscl_hancock_x, _y               [NEW: _y]
    hllc.hpp                # hllc_flux (direction-independent)
    slic.hpp                # slic_flux (centred scheme)          [NEW]
    euler_solver.hpp        # EulerSolver (1D+2D)               [MODIFIED]
    exact_riemann.hpp       # exact_riemann_sample               [NEW]
  utils/
    config.hpp              # Config parser
    io.hpp                  # Binary IO                          [NEW]
    error_norms.hpp         # L1/L2/Linf computation             [NEW]
  main.cpp                  # Config-driven entry point          [MODIFIED]
tests/
  unit/
    test_euler.cpp          # Extended with y-direction + 2D tests
  cases/
    toro_1d/                # Existing 1D test configs
    riemann_2d/             # 2D Riemann problem configs         [NEW]
scripts/
  verify_toro.py            # Existing 1D verification
  convergence.py            # Grid convergence analysis          [NEW]
```

---

## 10. Risks & Considerations

1. **Dimensional splitting order matters**: For strong 2D interactions, simple Godunov splitting introduces O(dt) splitting error. Strang splitting reduces this to O(dt^2) but doubles the y-sweep cost. Start with Godunov, switch to Strang if artifacts appear.

2. **CFL in 2D**: Must use `min(dx, dy)` in the denominator, not just `dx`. With a square grid (`dx=dy`) this is automatic, but non-square grids need care.

3. **Boundary conditions in 2D**: Current `apply_outflow_bc` already handles 2D grids correctly (tested in Week 1). No changes needed.

4. **HLLC for y-direction**: The HLLC solver operates on normal velocity (u). For y-interfaces, either (a) rotate states before calling `hllc_flux` (swap `RHOU`/`RHOV`), or (b) write a separate `hllc_flux_y` that uses v as normal velocity. Option (a) is cleaner and avoids code duplication.

5. **Memory**: 2D grids at higher resolution (e.g., 400x400) need `~400^2 * 4 * 8 bytes = 5 MB` for double precision. Not a concern for CPU; relevant when moving to GPU shared memory in Week 5.
