# Week 3 Design Spec: Complete 1D Tools + 2D Extension

**Date:** 2026-04-12  
**Branch:** main (`8460931`)  
**Timeframe:** 6 days remaining (04/12 – 04/17)  
**Approach:** Bottom-up dependency chain  
**Excluded:** SLIC flux solver (deferred)

---

## Scope & Priority

**Tier 1 — Foundation (must-complete):**
1. Exact Riemann solver (C++)
2. Additional slope limiters (minbee, van Leer, superbee, van Albada)
3. Error norms (L1/L2/Linf)
4. Binary IO (numpy-compatible)
5. Grid convergence study
9. Stationary contact discontinuity test (S_M=0 FP edge case)
10. Python analysis scripts (compare.py, plot_1d.py)

**Tier 2 — Verificarlo analysis:**
6. Unstable branch detection (scripts only, no C++ changes)

**Tier 3 — 2D extension (if time permits):**
7. Y-direction functions (flux, MUSCL, Hancock)
8. 2D Euler solver (Godunov alternating splitting)

---

## 1. Exact Riemann Solver

**File:** `src/euler/exact_riemann.hpp`

### Algorithm (Toro Ch. 4)

1. **Vacuum check** — evaluate `2*aL/(gamma-1) + 2*aR/(gamma-1) <= uR - uL` before iteration. If true, return vacuum state (`rho=0, p=0, u=0.5*(uL+uR)`) as an early exit. This prevents NaN propagation from negative pressures in the Newton-Raphson iteration. Note: none of the 5 standard Toro tests trigger this condition, but it guards against user-provided diverging ICs.

2. **Pressure iteration** — Newton-Raphson on `f(p) = f_L(p) + f_R(p) + (uR - uL) = 0`:
   - `f_K(p)` has different expressions depending on wave type:
     - Shock (`p > p_K`): `f_K = (p - p_K) * [A_K / (p + B_K)]^{1/2}` where `A_K = 2/((gamma+1)*rho_K)`, `B_K = p_K*(gamma-1)/(gamma+1)`
     - Rarefaction (`p <= p_K`): `f_K = (2*a_K/(gamma-1)) * [(p/p_K)^{(gamma-1)/(2*gamma)} - 1]`
   - Initial guess: two-rarefaction approximation (PVRS, Toro eq. 4.46) — robust for all 5 Toro tests
   - After each NR update, clamp pressure: `p_new = std::max(p_new, Real(1e-14))` to prevent negative pressure causing NaN in subsequent sqrt computations
   - Convergence tolerance: `abs(f) < std::max(Real(1e-8) * p_scale, Real(1e-15))` — the absolute floor `1e-15` prevents stalled iteration in near-vacuum regions where `p_scale` is tiny
   - Max 50 iterations

3. **Contact velocity** — `u_star = 0.5*(uL + uR) + 0.5*(f_R(p_star) - f_L(p_star))`

4. **Sampling** — Given `xi = (x - x0) / t_end` (must use `t_end`, NOT `t=0`), determine which wave region the sample point falls in and compute `(rho, u, p)`.

### Interface

```cpp
namespace hrsc {

// Pressure iteration: finds p_star, u_star for the star region
template <typename Real>
HD_FUNC void exact_riemann_solve(
    Real gamma,
    Real rhoL, Real uL, Real pL,
    Real rhoR, Real uR, Real pR,
    Real& p_star, Real& u_star);

// Full solver: iterates for p*, u*, then samples at x/t
template <typename Real>
HD_FUNC void exact_riemann_sample(
    Real gamma, Real x_over_t,
    Real rhoL, Real uL, Real pL,
    Real rhoR, Real uR, Real pR,
    Real& rho, Real& u, Real& p);

} // namespace hrsc
```

### Implementation Notes

- All internal helper functions (`f_K`, `f_K_derivative`, wave sampling) are template functions (implicit inline linkage). No `static` at namespace scope — avoids per-TU code duplication.
- All helpers are `HD_FUNC` for future GPU compatibility.
- Vacuum check is an early-return, not a throw (GPU functions cannot throw).

### Tests

- Compare `p_star`, `u_star` against known values:
  - Sod: `p_star ≈ 0.30313`, `u_star ≈ 0.92745`
  - Toro 2-5: published values from Toro Ch. 4
- Sample at 5+ points per test (left state, left fan, contact, right fan, right state)
- Verify vacuum check path with a synthetic diverging IC

---

## 2. Slope Limiters

**File:** `src/euler/muscl.hpp` (extend existing)

### Limiter Functions

Four limiters following Toro Ch. 13 nomenclature:

```cpp
// Minbee (= minmod): most dissipative TVD limiter
template <typename Real>
HD_FUNC Real minbee(Real a, Real b) {
    if (a * b <= Real(0)) return Real(0);
    return (std::abs(a) < std::abs(b)) ? a : b;
}

// Van Leer: smooth, moderate dissipation
template <typename Real>
HD_FUNC Real vanleer(Real a, Real b) {
    if (a * b <= Real(0)) return Real(0);
    return Real(2) * a * b / (a + b);
}

// Superbee: least dissipative symmetric TVD limiter
template <typename Real>
HD_FUNC Real superbee(Real a, Real b) {
    if (a * b <= Real(0)) return Real(0);
    Real s = (a > Real(0)) ? Real(1) : Real(-1);
    Real abs_a = std::abs(a);
    Real abs_b = std::abs(b);
    return s * std::max(std::min(abs_a, Real(2) * abs_b),
                        std::min(Real(2) * abs_a, abs_b));
}

// Van Albada: C1-smooth, good for smooth flows
template <typename Real>
HD_FUNC Real vanalbada(Real a, Real b) {
    if (a * b <= Real(0)) return Real(0);
    return a * b * (a + b) / (a * a + b * b);
}
```

### Functor Wrappers (for template parameter use)

```cpp
struct MinbeeLimiter {
    template <typename Real>
    HD_FUNC Real operator()(Real a, Real b) const { return minbee(a, b); }
};
struct VanLeerLimiter { /* ... */ };
struct SuperbeeLimiter { /* ... */ };
struct VanAlbadaLimiter { /* ... */ };
```

### Reconstruct Signature Change

```cpp
// Default = MinbeeLimiter preserves backward compatibility
template <typename Real, typename Ptr, typename Limiter = MinbeeLimiter>
HD_FUNC void muscl_reconstruct_x(
    GridViewBase<Real, 4, Ptr> grid, int i, int j,
    Vec<Real, 4>& q_left, Vec<Real, 4>& q_right,
    Limiter lim = {});
```

The existing `minmod` function is renamed to `minbee`. The function body of `muscl_reconstruct_x` changes from `minmod(backward, forward)` to `lim(backward, forward)` to use the template limiter. All existing call sites compile unchanged due to the default template parameter (`MinbeeLimiter` produces identical results to the old hardcoded `minmod`).

The same `Limiter` template parameter is threaded through `muscl_hancock_x` (and later `_y`).

### Naming Migration

| Old name | New name | Action |
|----------|----------|--------|
| `minmod(a, b)` | `minbee(a, b)` | Rename |
| (implicit minmod) | `MinbeeLimiter` | New functor, default |

### Tests

- Each limiter: same-sign, opposite-sign, zero-input cases
- Property tests:
  - `vanleer(a, a) == a` (exact gradient recovery)
  - `superbee` returns larger slopes than minbee for compatible gradients
  - `vanalbada(a, a) == a`
- Integration: run Sod with each limiter, verify density stays physical

---

## 3. Error Norms

**File:** `src/utils/error_norms.hpp`

### Interface

```cpp
namespace hrsc {

template <typename Real>
struct ErrorNorms { Real L1, L2, Linf; };

// Dimension-agnostic: pass dV = dx (1D) or dx*dy (2D)
template <typename Real>
ErrorNorms<Real> compute_error(const Real* numerical, const Real* exact,
                               int total_cells, Real dV);

} // namespace hrsc
```

### Implementation

Single-pass accumulation:
- `L1 = sum(|num_i - exact_i|) * dV`
- `L2 = sqrt(sum((num_i - exact_i)^2) * dV)`
- `Linf = max(|num_i - exact_i|)`

Pure host function (no `HD_FUNC`), templated on `Real`.

### Tests

- Zero error for identical arrays
- Known error: `{1,2,3}` vs `{1.1, 2.2, 3.3}` with dx=1 → verify exact L1, L2, Linf
- Norm inequality: `L1 <= sqrt(n*dV) * L2 <= n*dV * Linf`

---

## 4. Binary IO

**File:** `src/utils/io.hpp`

### Header Format (64 bytes, little-endian)

| Offset | Type | Field |
|--------|------|-------|
| 0–3 | char[4] | magic = `"HRSC"` |
| 4–7 | int32 | nx |
| 8–11 | int32 | ny |
| 12–15 | int32 | nvars |
| 16–19 | int32 | precision_tag (4=float, 8=double) |
| 20–27 | float64 | time |
| 28–35 | float64 | dx |
| 36–43 | float64 | dy |
| 44–63 | — | reserved (zero-padded) |

### Endianness

C++17 constraint — no `std::endian`. Use compile-time static assert:
```cpp
static_assert(__BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__,
              "Binary IO assumes little-endian architecture");
```
Both target platforms (x86 Windows, x86_64 Linux CSC cluster) are little-endian. If a big-endian platform ever appears, the assert fires and byte-swap helpers (`__builtin_bswap*`) are added then.

### Interface

```cpp
namespace hrsc {

template <typename Real, int NVars>
void write_binary(const std::string& filename,
                  ConstGridView<Real, NVars> grid,
                  int nx, int ny, Real dx, Real dy, Real time);

// Read header only (to learn nx/ny for allocation)
void read_binary_header(const std::string& filename,
                        int& nx, int& ny, int& nvars, int& precision_tag,
                        double& time, double& dx, double& dy);

// Read data into pre-allocated grid (caller must allocate Grid2D after reading header)
template <typename Real, int NVars>
void read_binary_data(const std::string& filename,
                      GridView<Real, NVars> grid,
                      int nx, int ny);

} // namespace hrsc
```

Usage pattern: call `read_binary_header` first to learn dimensions, allocate `Grid2D`, then call `read_binary_data` to fill it.

### Ghost Cell Handling

Physical cells in `GridView` are NOT contiguous in memory (ghost cell padding separates rows). `write_binary` copies physical cells to a contiguous buffer before writing:

```cpp
std::vector<Real> buf(nx * ny * NVars);
for (int j = 0; j < ny; ++j)
    for (int i = 0; i < nx; ++i)
        for (int v = 0; v < NVars; ++v)
            buf[(j * nx + i) * NVars + v] = grid(i, j, v);
fwrite(buf.data(), sizeof(Real), buf.size(), fp);
```

Data layout in file: row-major, variable-last: `[j * nx * NVars + i * NVars + var]`.

### Row-by-Row Direct Write (no buffer allocation)

Physical rows ARE contiguous within the ghost-padded layout. Row `j` starts at `data + ((j+ng) * nx_total + ng) * NVars` and spans `nx * NVars` elements. Write directly from each row pointer:

```cpp
for (int j = 0; j < ny; ++j) {
    const Real* row_start = grid.data + ((j + grid.ng) * grid.nx_total() + grid.ng) * NVars;
    fwrite(row_start, sizeof(Real), nx * NVars, fp);
}
```

No buffer allocation — simpler, zero memory overhead, works for any grid size.

### Python Reading

```python
with open(filename, 'rb') as f:
    header = f.read(64)
    # ... parse nx, ny, nvars, precision_tag, time, dx, dy
    dtype = '<f4' if precision_tag == 4 else '<f8'  # dynamic from header
    data = np.fromfile(f, dtype=dtype).reshape(ny, nx, nvars)
```

Dynamic `dtype` selection from `precision_tag` ensures the same script handles both float and double binary files (needed for Week 7 float/double comparison experiments).

### Tests

- Round-trip: write a grid, read it back, compare cell-by-cell
- Verify header magic and precision tag
- Verify file size = 64 + nx * ny * NVars * sizeof(Real)

---

## 5. Grid Convergence Study

### Config Extension

Add `get_int_list` to `src/utils/config.hpp`:
```cpp
std::vector<int> get_int_list(const std::string& key) const;
// Parses "50,100,200,400,800" → {50, 100, 200, 400, 800}
```

### Config File

```ini
# tests/cases/toro_1d/convergence_sod.cfg
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

### Main.cpp Extension

When `mode = convergence`:
1. Read config (test case, gamma, CFL, t_end, x0, resolutions list)
2. For each resolution N:
   - Create solver with `nx = N`, `dx = (xmax - xmin) / N`
   - Set IC, run to `t_end`
   - Generate exact solution at each cell center: `xi = (x_cell - x0) / t_end` (NOT `t=0`)
   - Compute `ErrorNorms` for rho, u, p via `compute_error`
3. Output table to stdout:
   ```
   N    dx          L1_rho        L2_rho        Linf_rho      L1_u  ...
   50   2.0000e-02  1.234e-02     5.678e-03     9.012e-02     ...
   100  1.0000e-02  6.543e-03     2.876e-03     4.567e-02     ...
   ...
   ```
4. Compute observed convergence order between successive resolutions:
   `p = log(E_coarse / E_fine) / log(2)`

### Python Companion

`scripts/convergence.py`:
- Reads the table from stdout (or piped to file)
- Produces log-log plot of L1 vs dx
- Fits slope to verify order ~1.5–2.0 (limited by minbee + discontinuities)
- Generates publication-ready figure

### Expected Results

With minbee limiter on Sod: global L1 convergence ~1.0–1.5 (first-order at discontinuities, second-order in smooth regions). Superbee should give slightly better rates.

---

## 6. Y-Direction Extension

**Files modified:** `src/euler/euler_flux.hpp`, `src/euler/muscl.hpp`, `src/euler/hancock.hpp`

### 6a. euler_flux_y — `euler_flux.hpp`

```cpp
// G(U) = {rho*v, rho*u*v, rho*v^2 + p, v*(E+p)}
template <typename Real>
HD_FUNC Vec<Real, 4> euler_flux_y(const Vec<Real, 4>& cons, Real gamma);
```

Note: `G[1] = rho*u*v` (transverse momentum flux), `G[2] = rho*v^2 + p` (normal momentum + pressure). Compare with `F[1] = rho*u^2 + p`, `F[2] = rho*u*v`.

### 6b. muscl_reconstruct_y — `muscl.hpp`

```cpp
template <typename Real, typename Ptr, typename Limiter = MinbeeLimiter>
HD_FUNC void muscl_reconstruct_y(
    GridViewBase<Real, 4, Ptr> grid, int i, int j,
    Vec<Real, 4>& q_bottom, Vec<Real, 4>& q_top,
    Limiter lim = {});
```

Stencil: `j-1, j, j+1`. Same limiter logic as `_x`, applied along y-axis.

### 6c. muscl_hancock_y — `hancock.hpp`

```cpp
template <typename Real, typename Ptr, typename Limiter = MinbeeLimiter>
HD_FUNC void muscl_hancock_y(
    GridViewBase<Real, 4, Ptr> grid, int i, int j,
    Real dt, Real gamma,
    Vec<Real, 4>& q_bottom, Vec<Real, 4>& q_top,
    Limiter lim = {});
```

Uses `euler_flux_y` for the half-step evolution and **`grid.dy`** (not `grid.dx`) for the spatial derivative:
```cpp
Real half_dtdy = Real(0.5) * dt / grid.dy;  // NOT grid.dx
```

### 6d. HLLC for Y-Interfaces — Rotation Approach

No new `hllc_flux_y`. At y-interfaces, swap momentum components before/after calling the existing `hllc_flux`:

```cpp
template <typename Real>
HD_FUNC Vec<Real, 4> swap_momentum(const Vec<Real, 4>& q) {
    return {q[RHO], q[RHOV], q[RHOU], q[EN]};
}

// At y-interface: swap → solve → swap back
auto flux = swap_momentum(
    hllc_flux(swap_momentum(qB_top), swap_momentum(qT_bot), gamma));
```

This avoids code duplication. The HLLC solver always treats index 1 as normal velocity and index 2 as transverse — the rotation makes this work for y-interfaces.

### Tests

- `euler_flux_y`: stationary gas → `{0, 0, p, 0}`, uniform flow verification
- `muscl_reconstruct_y`: uniform field, linear field, discontinuity (mirrors x-tests in j-direction)
- `muscl_hancock_y`: uniform field unchanged after half-step
- HLLC y-rotation: identical left/right states → physical flux G(U)

---

## 7. 2D Euler Solver

**File:** `src/euler/euler_solver.hpp` (modify existing)

### Constructor

```cpp
// 2D constructor
EulerSolver(int nx, int ny, Real dx, Real dy,
            Real xmin, Real ymin,
            Real gamma, Real cfl, Real t_end);

// 1D convenience constructor (backward compatible)
EulerSolver(int nx, Real dx, Real xmin,
            Real gamma, Real cfl, Real t_end);
// Internally calls: EulerSolver(nx, 1, dx, dx, xmin, Real(0), gamma, cfl, t_end)
```

New private members: `m_xmin`, `m_ymin`.

### CFL Condition (2D)

```cpp
Real max_Sx = 0, max_Sy = 0;  // max wave speeds per direction
for (int j = 0; j < ny; ++j)
    for (int i = 0; i < nx; ++i) {
        // extract rho, u, v, p, a ...
        max_Sx = std::max(max_Sx, std::abs(u) + a);
        max_Sy = std::max(max_Sy, std::abs(v) + a);
    }
Real dt = m_cfl * std::min(m_grid.dx / max_Sx, m_grid.dy / max_Sy);
```

This is less conservative than `min(dx,dy) / max(|u|+a, |v|+a)` — on non-square grids it allows larger timesteps. On square grids with uniform flow the result is identical.

### Dimensional Splitting — Alternating Godunov

```cpp
void step() {
    auto gv = m_grid.view();
    apply_outflow_bc(gv);
    Real dt = compute_dt();
    if (dt <= Real(0)) return;

    if (m_grid.ny == 1) {
        x_sweep(dt);  // 1D path, exact backward compatibility
    } else {
        if (m_step % 2 == 0) {
            x_sweep(dt);
            apply_outflow_bc(gv);  // refresh BCs between sweeps
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
```

### Private Methods

- `x_sweep(Real dt)` — the current `step()` body (interface flux loop + conservative update), extracted as-is
- `y_sweep(Real dt)` — mirrors x_sweep:
  - Loop over y-interfaces (between rows k-1 and k)
  - `muscl_hancock_y` for reconstruction + prediction
  - `swap_momentum` → `hllc_flux` → `swap_momentum` for flux
  - Conservative update: `U(i,j) -= (dt/dy) * (flux_top - flux_bottom)`

### 1D Constructor Compatibility

The old 1D constructor signature `EulerSolver(int nx, Real dx, Real gamma, Real cfl, Real t_end)` changes to `EulerSolver(int nx, Real dx, Real xmin, Real gamma, Real cfl, Real t_end)`. Breaking change — requires updating:
- `src/main.cpp` — pass `xmin` from config
- `tests/unit/test_euler.cpp` — all `EulerSolver` construction sites (add `xmin = 0.0`)

### Tests

- 2D Sod along x-axis (`ny > 1` but uniform in y): must match 1D results
- 2D uniform field: no evolution over multiple steps
- Mass conservation on 2D grid

---

## 8. Verificarlo Unstable Branch Detection

**No C++ code changes.** Verificarlo instruments the existing code automatically at compile time.

### `scripts/verificarlo_run.sh` (extend existing)

```bash
# Compile with verificarlo wrapper
verificarlo-c++ --inst-fma -O2 -o hrsc_vfc ...

# Configure VPREC backend at ~40 bits
export VFC_BACKENDS="libinterflop_vprec.so --precision-binary64=40"

# Run 30 MCA samples for Sod
for i in $(seq 1 30); do
    ./hrsc_vfc tests/cases/toro_1d/sod.cfg > output/mca_sample_${i}.txt 2>&1
done
```

Key settings:
- VPREC at 40 bits (reduced from 53-bit double) to amplify FP sensitivity
- `--inst-fma` to instrument fused multiply-add operations
- 30 samples: sufficient for statistical significance on branch flip rates

### `scripts/verificarlo_analysis.py` (extend existing)

- Parse Verificarlo branch detection output (source file, line number, sample outcomes)
- Flag branches where True/False ratio across samples deviates from 100%/0%
- Expected hot spots:
  1. `hllc.hpp` — `SL >= 0` near rarefaction wave head
  2. `hllc.hpp` — `S_star >= 0` near contact discontinuity
  3. `muscl.hpp` — minbee sign check `a * b <= 0` in flat regions
- Output: table of unstable branches ranked by flip frequency, with cell index and time step

### Deliverable

A summary table showing which code branches are precision-sensitive at 40-bit, directly supporting the mixed-precision argument for the thesis.

---

## 9. Stationary Contact Discontinuity Test

**Files:** `tests/cases/toro_1d/toro_tests.hpp` (add IC), `tests/cases/toro_1d/stationary_contact.cfg` (new)

### Purpose

Targeted FP edge case for the `<=` vs `<` investigation. With `p_L = p_R` and `u_L = u_R = 0`, the HLLC contact wave speed `S_M` is analytically zero. This is the exact boundary between the two star-region branches — FP round-off may produce `S_M = ±epsilon`, causing different code paths under strict `<` vs non-strict `<=`.

### IC

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

### Config

```ini
# tests/cases/toro_1d/stationary_contact.cfg
test = stationary_contact
nx = 200
xmin = 0.0
xmax = 1.0
gamma = 1.4
cfl = 0.8
t_end = 0.5
```

### Expected Behavior

- The contact should remain stationary at `x = 0.5`
- Density jumps from 1.0 to 0.5, pressure and velocity uniform
- With `<=`: both star regions cover `S_M = 0`, left star selected
- With strict `<`: `S_M = 0` excluded from both star regions, falls through to `FR`
- FP perturbation of `S_M` around zero may cause different cells to take different branches

### Tests

- Verify pressure stays uniform (no spurious waves)
- Verify contact position doesn't drift
- Compare `RIEMANN_STRICT_INEQUALITY` ON vs OFF output

### main.cpp Update

Add `"stationary_contact"` to the test selection `if/else` chain.

---

## 10. Python Analysis Scripts

**Directory:** `analysis/` (following staged plan convention, separate from `scripts/`)

### 10a. `analysis/compare.py`

Loads binary output files and computes error norms:

```python
# Usage: python analysis/compare.py output/sod.bin --exact-args "sod 1.4 0.5 0.25"
# Outputs: L1, L2, Linf for rho, u, p
```

- Reads binary header (nx, ny, nvars, precision_tag, time, dx, dy)
- Dynamic dtype selection: `'<f4'` if precision_tag=4, `'<f8'` if precision_tag=8
- Generates exact solution using the Python exact Riemann solver (already in `scripts/verify_toro.py`)
- Computes L1/L2/Linf norms
- Iterative processing: one file at a time, appends to CSV, suitable for batch use

### 10b. `analysis/plot_1d.py`

Plots 1D numerical vs exact solution profiles:

```python
# Usage: python analysis/plot_1d.py output/sod.bin --exact-args "sod 1.4 0.5 0.25"
# Outputs: PNG with rho, u, p subplots, exact solution overlay
```

- Reads binary output
- Overlays exact Riemann solution (dashed line) on numerical result (solid line/markers)
- Subplots for rho, u, p
- Publication-ready: axis labels, legend, title with test name + resolution

### 10c. `analysis/requirements.txt`

```
numpy>=1.21
matplotlib>=3.5
```

Minimal — no heavy dependencies. `scipy` added later if needed (Week 7 convergence fitting).

---

## Dependency Chain (Implementation Order)

```
1. Exact Riemann solver ──┐
2. Slope limiters ────────┤
3. Error norms ───────────┼── 5. Grid convergence study
4. Binary IO ─────────────┤
9. Stationary contact IC ─┘── 10. Python analysis scripts (compare.py, plot_1d.py)
                          ┌── 7. 2D Euler solver
6. Y-direction functions ─┘
8. Verificarlo scripts (independent, can run anytime after existing code compiles)
```

## Files Changed/Created Summary

| Action | File |
|--------|------|
| **NEW** | `src/euler/exact_riemann.hpp` |
| **NEW** | `src/utils/error_norms.hpp` |
| **NEW** | `src/utils/io.hpp` |
| **NEW** | `tests/cases/toro_1d/convergence_sod.cfg` |
| **NEW** | `tests/cases/toro_1d/stationary_contact.cfg` |
| **NEW** | `analysis/compare.py` |
| **NEW** | `analysis/plot_1d.py` |
| **NEW** | `analysis/requirements.txt` |
| **NEW** | `scripts/convergence.py` |
| **MODIFIED** | `src/euler/muscl.hpp` — rename minmod→minbee, add limiters + functors, add `_y` |
| **MODIFIED** | `src/euler/hancock.hpp` — add limiter template param, add `_y` |
| **MODIFIED** | `src/euler/euler_flux.hpp` — add `euler_flux_y` |
| **MODIFIED** | `src/euler/euler_solver.hpp` — 2D constructor, x/y sweeps, alternating split |
| **MODIFIED** | `src/utils/config.hpp` — add `get_int_list` |
| **MODIFIED** | `src/main.cpp` — convergence mode, 2D support, xmin param, stationary_contact |
| **MODIFIED** | `tests/cases/toro_1d/toro_tests.hpp` — add `setup_stationary_contact` |
| **MODIFIED** | `tests/unit/test_euler.cpp` — new tests for all modules |
| **MODIFIED** | `scripts/verificarlo_run.sh` — VPREC 40-bit + branch detection |
| **MODIFIED** | `scripts/verificarlo_analysis.py` — branch flip analysis |
| **MODIFIED** | `CMakeLists.txt` — include paths for new files if needed |

---

## Deferred Enhancements (not in Week 3 scope)

Items reviewed and intentionally deferred. Recorded here for future weeks.

| Item | Target Week | Rationale |
|------|-------------|-----------|
| **Kahan summation** in `compute_error` | Week 7 | At 200-800 cells naive sum is fine. At 1600 cells (convergence study), roundoff accumulation may mask precision differences. Add compensated summation then. |
| **Gaussian quadrature** for exact solution cell-averages | Week 7 | Point-value comparison limits observed convergence order for smooth problems. 3-point Gauss per cell recovers clean O(2). Not needed for Sod (discontinuities → O(1) anyway). |
| **`hrsc::min/max`** device-safe wrappers | Week 5-6 | Two-argument `std::min/max` works on NVCC since CUDA 9+. Only add if GPU compilation fails. |
| **Periodic/reflective BCs** | Week 5 | Needed for Liska-Wendroff 2D and MHD. Not required for outflow-only tests in Week 3. |
