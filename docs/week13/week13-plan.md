# Week 13 — 2D MHD Benchmarks (HLL) + HLLD Solver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate 2D physical MHD benchmarks (Orszag-Tang, Kelvin-Helmholtz) on the proven HLL solver, and add an HLLD 5-wave solver as a zero-cost, cfg-selectable alternative — all additive, keeping the Week-12 1D Brio-Wu path bit-identical.

**Architecture:** Wrap each Riemann solver in a stateless functor (`HllFlux`, `HlldFlux`) and template the solver `MhdSolver<Real, RiemannFlux = HllFlux>`; the default keeps every existing call site bit-identical. New cases extend the existing cfg-driven `MhdTestCase` registry. HLLD is selected at runtime by a one-time `mhd_main` dispatch on a `riemann` cfg key (no virtuals). Validation reuses the Week-12 self-converged-reference + scalar-summary discipline.

**Tech Stack:** C++17 templated-on-`Real` (float/double via `HRSC_REAL`), CMake/Ninja, Catch2 auto-globbed unit tests (`tests/unit/test_*.cpp`), key=value cfg files, little-endian 64-byte-header binary IO, Python (numpy-only) regression harness.

**Reference spec:** [2026-06-25-week13-mhd-hlld-2d-benchmarks-design.md](../superpowers/specs/2026-06-25-week13-mhd-hlld-2d-benchmarks-design.md)

## Global Constraints

- **Additive only:** do not modify the Euler binary, `src/app/`, or the validated 1D Brio-Wu numerics. Default `riemann = hll` ⇒ `HllFlux` default ⇒ Brio-Wu stays bit-identical (regression anchor: `steps=759`, `divB_max=4.441e-14`, full MHD suite 33 cases / 13944 assertions before new tests are added).
- **Sustain Week-12 interfaces:** Riemann signature `f(UL, UR, gamma, ch) → Vec<Real, MhdNVars>` (`MhdNVars = 9`, enum `RHO,MX,MY,MZ,BX,BY,BZ,E,PSI`); `RIEMANN_STRICT_INEQUALITY` flag; `predict_faces` / `mhd_swap_xy` rotation; cfg registry in `mhd_config.hpp`; GLM (`F[BX]=ψ`, `F[PSI]=ch²·Bx`, `glm_damp`, ψ=0-outflow / periodic BCs); validation discipline (generated cfgs, stdout/stderr, per-run metadata, `summary.{csv,json,md}`; binary grids transient/ignored).
- **Coding guidance** ([coding guidance.md](../requirement/coding%20guidance.md)): no magic numbers — use named `const Real` locals with a `// why / source` comment; project naming (snake_case free functions, `m_`-prefixed members, `PascalCase` types); cfg-driven params (no hardcoded domain/params in source beyond case-defining constants, mirroring `setup_divb_blob`); comments explain *why*; no committed build artifacts or binary grids.
- **Build/run on this workstation:** configure through `cmake -B build-double -G Ninja -DFLOAT_PRECISION=double` (and `build-float`). On bare PowerShell load VS BuildTools via `VsDevCmd.bat` first; Python is `C:\Users\tangy\miniconda3\python.exe`. Executables may have a `.exe` suffix (regression scripts already resolve this).
- **Delivery tiers:** Tasks 1–8 are **Core** (OT + KH on HLL = milestone). Tasks 9–11 are **Enhanced** (HLLD); if HLLD proves too buggy, ship the attempt + a written fallback decision and the precision study proceeds on HLL.

---

## File Structure

**Create (C++):**
- `src/mhd/hlld.hpp` — `mhd_hlld_flux` (MK2005 5-wave + GLM split) and `HlldFlux` functor.

**Create (tests):**
- `tests/unit/test_mhd_orszag_tang.cpp`, `tests/unit/test_mhd_kh.cpp`, `tests/unit/test_mhd_hlld.cpp`.
- `tests/py/test_mhd_harness.py` — pytest for the pure-numeric validation helpers.

**Create (cfgs / scripts / docs):**
- `tests/cases/orszag_tang_2d/{orszag_tang.cfg, orszag_tang_ref.cfg}`
- `tests/cases/kelvin_helmholtz_2d/{kh.cfg, kh_ref.cfg}`
- `scripts/regression/_mhd_harness.py` — shared subprocess runner + pure-numeric helpers.
- `scripts/regression/mhd_orszag_tang_2d.py`, `scripts/regression/mhd_kh_2d.py`
- `scripts/regression/mhd_solver_compare_2d.py` — HLLD-vs-HLL comparison driver.

**Modify:**
- `src/mhd/hll.hpp` — add `HllFlux` functor (keep `mhd_hll_flux`).
- `src/mhd/mhd_solver.hpp` / `.cpp` — template on flux; add `setup_orszag_tang`, `setup_kelvin_helmholtz`; explicit instantiations (4 solver combos).
- `src/mhd/mhd_config.hpp` — `MhdTestCase` (+OrszagTang, +KelvinHelmholtz), `MhdRiemann` enum + parsers.
- `src/mhd_main.cpp` — new case setup branches; `run_mhd<Flux>` dispatch on `riemann`.
- `docs/INDEX.md` — Week 13 row.

---

## Task 1: Functor-templated `MhdSolver` (default `HllFlux`, bit-identical)

**Files:**
- Modify: `src/mhd/hll.hpp`
- Modify: `src/mhd/mhd_solver.hpp`
- Modify: `src/mhd/mhd_solver.cpp`
- Test: `tests/unit/test_mhd_solver.cpp`

**Interfaces:**
- Produces: `struct HllFlux` with `template<typename Real> HD_FUNC Vec<Real,MhdNVars> operator()(const Vec<Real,MhdNVars>&, const Vec<Real,MhdNVars>&, Real, Real) const;` and `template<typename Real, typename RiemannFlux = HllFlux> class MhdSolver`.
- Consumes: existing `mhd_hll_flux`, `predict_faces`, `mhd_swap_xy` (unchanged).

- [ ] **Step 1: Write the failing test** (append to `tests/unit/test_mhd_solver.cpp`)

```cpp
#include "mhd/hll.hpp"  // HllFlux

TEST_CASE("MhdSolver<double, HllFlux> matches default HLL solver", "[mhd][solver][functor]") {
    // Same Brio-Wu short run as the default-parameter solver; the explicit
    // HllFlux instantiation must reproduce it bit-for-bit (the default IS HllFlux).
    MhdSolver<double> a(64, 1.0/64, 0.0, 2.0, 0.4, 0.02);
    setup_brio_wu(a.grid_view(), 64, 1.0/64, 0.0, 2.0, 0.5);
    a.run();
    MhdSolver<double, HllFlux> b(64, 1.0/64, 0.0, 2.0, 0.4, 0.02);
    setup_brio_wu(b.grid_view(), 64, 1.0/64, 0.0, 2.0, 0.5);
    b.run();
    auto ga = a.grid_view();
    auto gb = b.grid_view();
    for (int i = 0; i < 64; ++i)
        for (int k = 0; k < MhdNVars; ++k)
            REQUIRE(gb(i, 0, k) == ga(i, 0, k));  // exact equality
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][solver][functor]"`
Expected: FAIL — `HllFlux` undefined / `MhdSolver` takes one template arg.

- [ ] **Step 3: Add the `HllFlux` functor** (append to `src/mhd/hll.hpp` before the closing `} // namespace hrsc`)

```cpp
// Stateless functor wrapper so MhdSolver can be templated on the Riemann
// solver while mhd_hll_flux stays a free function for direct unit testing.
struct HllFlux {
    template <typename Real>
    HD_FUNC Vec<Real, MhdNVars> operator()(const Vec<Real, MhdNVars>& UL,
                                           const Vec<Real, MhdNVars>& UR,
                                           Real gamma, Real ch) const {
        return mhd_hll_flux(UL, UR, gamma, ch);
    }
};
```

- [ ] **Step 4: Template the solver class** (`src/mhd/mhd_solver.hpp`)

Change the class template line and add the include:

```cpp
#include "mhd/hll.hpp"  // already present; provides HllFlux
// ...
template <typename Real, typename RiemannFlux = HllFlux>
class MhdSolver {
```

The member functions and signatures are otherwise unchanged.

- [ ] **Step 5: Update the solver definitions and call sites** (`src/mhd/mhd_solver.cpp`)

Every `MhdSolver<Real>::` member definition becomes `MhdSolver<Real, RiemannFlux>::`, each preceded by `template <typename Real, typename RiemannFlux>`. In `x_sweep` replace the flux call:

```cpp
            flux[static_cast<std::size_t>(iface)] =
                RiemannFlux{}(left_cell_right, right_cell_left, m_gamma, ch);
```

In `y_sweep` replace the rotated flux call:

```cpp
            flux[static_cast<std::size_t>(jf)] =
                mhd_swap_xy(RiemannFlux{}(lcr, rcl, m_gamma, ch));  // rotate flux back
```

Replace the two explicit instantiations at the bottom with the HLL pair (the HLLD pair is added in Task 9):

```cpp
template class MhdSolver<float, HllFlux>;
template class MhdSolver<double, HllFlux>;
```

> The `setup_*` free functions and their instantiations are unchanged (they do not depend on `RiemannFlux`).

- [ ] **Step 6: Run the new test + full suite + Brio-Wu regression**

Run:
```bash
cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd]" -r compact
./build-double/unit_tests "[mhd][solver][functor]" -v
cmake --build build-double --target hrsc_mhd && ./build-double/hrsc_mhd tests/cases/brio_wu_1d/brio_wu.cfg
```
Expected: all `[mhd]` cases PASS; functor test PASS; Brio-Wu prints `[mhd] t=0.100000 steps=759 ... divB_max=4.441e-14`.

- [ ] **Step 7: Commit**

```bash
git add src/mhd/hll.hpp src/mhd/mhd_solver.hpp src/mhd/mhd_solver.cpp tests/unit/test_mhd_solver.cpp
git commit -m "refactor(mhd): template MhdSolver on Riemann functor (default HllFlux)"
```

---

## Task 2: Orszag-Tang IC (`setup_orszag_tang`)

**Files:**
- Modify: `src/mhd/mhd_solver.hpp`
- Modify: `src/mhd/mhd_solver.cpp`
- Test: `tests/unit/test_mhd_orszag_tang.cpp`

**Interfaces:**
- Produces: `template<typename Real> void setup_orszag_tang(GridView<Real,MhdNVars> gv, int nx, int ny, Real dx, Real dy, Real xmin, Real ymin, Real gamma);`

- [ ] **Step 1: Write the failing test** (`tests/unit/test_mhd_orszag_tang.cpp`)

```cpp
#include "catch.hpp"
#include "core/grid.hpp"
#include "mhd/mhd_solver.hpp"
#include "mhd/mhd_state.hpp"
#include "utils/error_norms.hpp"
#include <cmath>

using namespace hrsc;

TEST_CASE("Orszag-Tang IC matches analytic fields and is divergence-free", "[mhd][ot]") {
    const int n = 32;
    const double L = 1.0, dx = L / n, gamma = 5.0 / 3.0;
    Grid2D<double, MhdNVars> grid(n, n);
    grid.dx = dx; grid.dy = dx;
    setup_orszag_tang<double>(grid.view(), n, n, dx, dx, 0.0, 0.0, gamma);

    auto gv = grid.view();
    const double pi = 3.14159265358979323846;
    const double B0 = 1.0, rho0 = gamma * gamma, p0 = gamma;
    // Spot-check a representative cell against the analytic IC.
    const int i = 7, j = 11;
    const double x = (i + 0.5) * dx, y = (j + 0.5) * dx;
    MhdPrim<double> w = cons_to_prim(load_cell_test(gv, i, j), gamma);
    REQUIRE(w.rho == Approx(rho0));
    REQUIRE(w.p   == Approx(p0));
    REQUIRE(w.vx  == Approx(-std::sin(2 * pi * y)));
    REQUIRE(w.vy  == Approx( std::sin(2 * pi * x)));
    REQUIRE(w.Bx  == Approx(-B0 * std::sin(2 * pi * y)));
    REQUIRE(w.By  == Approx( B0 * std::sin(4 * pi * x)));

    // Cell-centred central-difference div(B) is zero for this field.
    DivBNorms<double> d = compute_divB_norms<double>(gv, n, n, dx, dx);
    REQUIRE(d.max == Approx(0.0).margin(1e-12));
}
```

Add this small test helper at the top of the file (Catch2 lets each TU define helpers; `load_cell` in the solver is in an anonymous namespace and not visible here):

```cpp
namespace {
hrsc::Vec<double, hrsc::MhdNVars> load_cell_test(hrsc::GridView<double, hrsc::MhdNVars> gv,
                                                 int i, int j) {
    hrsc::Vec<double, hrsc::MhdNVars> U{};
    for (int k = 0; k < hrsc::MhdNVars; ++k) U[k] = gv(i, j, k);
    return U;
}
} // namespace
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][ot]"`
Expected: FAIL — `setup_orszag_tang` undefined.

- [ ] **Step 3: Declare the setup** (`src/mhd/mhd_solver.hpp`, near `setup_divb_blob`)

```cpp
template <typename Real>
void setup_orszag_tang(GridView<Real, MhdNVars> gv, int nx, int ny,
                       Real dx, Real dy, Real xmin, Real ymin, Real gamma);
```

- [ ] **Step 4: Define + instantiate** (`src/mhd/mhd_solver.cpp`, after `setup_divb_blob`)

```cpp
// Orszag-Tang vortex (Toth 2000), rationalized units matching the solver's
// ptot = p + 0.5*|B|^2 convention: rho=gamma^2, p=gamma, B0=1. The vector-
// potential construction makes div(B)=0 at t=0 (Bx depends only on y, By only
// on x), so the cell-centred central difference is exactly zero initially.
template <typename Real>
void setup_orszag_tang(GridView<Real, MhdNVars> gv, int nx, int ny,
                       Real dx, Real dy, Real xmin, Real ymin, Real gamma) {
    const Real pi = Real(3.14159265358979323846);
    const Real B0 = Real(1);
    const Real rho0 = gamma * gamma;
    const Real p0 = gamma;
    for (int j = 0; j < ny; ++j)
        for (int i = 0; i < nx; ++i) {
            const Real x = xmin + (Real(i) + Real(0.5)) * dx;
            const Real y = ymin + (Real(j) + Real(0.5)) * dy;
            MhdPrim<Real> w{};
            w.rho = rho0;
            w.p   = p0;
            w.vx  = -std::sin(Real(2) * pi * y);
            w.vy  =  std::sin(Real(2) * pi * x);
            w.Bx  = -B0 * std::sin(Real(2) * pi * y);
            w.By  =  B0 * std::sin(Real(4) * pi * x);
            store_cell(gv, i, j, prim_to_cons(w, gamma));  // vz=Bz=psi=0 from {}
        }
}

template void setup_orszag_tang<float>(GridView<float, MhdNVars>, int, int, float, float, float, float, float);
template void setup_orszag_tang<double>(GridView<double, MhdNVars>, int, int, double, double, double, double, double);
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][ot]" -v`
Expected: PASS — IC matches analytic fields; `divB_max ≈ 0`.

- [ ] **Step 6: Commit**

```bash
git add src/mhd/mhd_solver.hpp src/mhd/mhd_solver.cpp tests/unit/test_mhd_orszag_tang.cpp
git commit -m "feat(mhd): add Orszag-Tang vortex IC (rho=g^2, p=g, B0=1)"
```

---

## Task 3: Orszag-Tang executable wiring + cfgs

**Files:**
- Modify: `src/mhd/mhd_config.hpp`
- Modify: `src/mhd_main.cpp`
- Create: `tests/cases/orszag_tang_2d/orszag_tang.cfg`
- Create: `tests/cases/orszag_tang_2d/orszag_tang_ref.cfg`

**Interfaces:**
- Produces: `MhdTestCase::OrszagTang`; cfg `test = orszag_tang` runs the OT IC on the default (HLL) solver.

- [ ] **Step 1: Extend the test-case registry** (`src/mhd/mhd_config.hpp`)

```cpp
enum class MhdTestCase { BrioWu, DivbBlob, OrszagTang };

inline MhdTestCase parse_mhd_test(const std::string& value) {
    if (value == "brio_wu")     return MhdTestCase::BrioWu;
    if (value == "divb_blob")   return MhdTestCase::DivbBlob;
    if (value == "orszag_tang") return MhdTestCase::OrszagTang;
    throw std::invalid_argument("unsupported MHD test case: " + value);
}
```

- [ ] **Step 2: Add the case branch** (`src/mhd_main.cpp`, in the `test ==` if/else after the `BrioWu` branch)

```cpp
    } else if (test == hrsc::MhdTestCase::OrszagTang) {
        hrsc::setup_orszag_tang<Real>(gv, nx, ny, dx, dy, (Real)xmin, (Real)ymin, (Real)gamma);
    } else {
        hrsc::setup_divb_blob<Real>(gv, nx, ny, dx, dy, (Real)xmin, (Real)ymin, (Real)gamma);
    }
```

- [ ] **Step 3: Write the production cfg** (`tests/cases/orszag_tang_2d/orszag_tang.cfg`)

```ini
# Orszag-Tang vortex (Toth 2000). Doubly periodic, gamma=5/3.
# Rationalized units: rho=gamma^2, p=gamma, B0=1 (set in setup_orszag_tang).
test    = orszag_tang
nx      = 256
ny      = 256
xmin    = 0.0
xmax    = 1.0
ymin    = 0.0
ymax    = 1.0
gamma   = 1.6666666666666667
cfl     = 0.4
t_end   = 0.5
glm_cr  = 0.18
bc      = periodic
bc_y    = periodic
```

- [ ] **Step 4: Write the reference cfg** (`tests/cases/orszag_tang_2d/orszag_tang_ref.cfg`)

```ini
# Self-converged double reference for Orszag-Tang (2x candidate resolution).
test    = orszag_tang
nx      = 512
ny      = 512
xmin    = 0.0
xmax    = 1.0
ymin    = 0.0
ymax    = 1.0
gamma   = 1.6666666666666667
cfl     = 0.4
t_end   = 0.5
glm_cr  = 0.18
bc      = periodic
bc_y    = periodic
```

- [ ] **Step 5: Build + smoke-run (reduced grid for speed)**

Run (overrides nx/ny/t_end inline to keep the smoke fast; the production cfg itself is unchanged):
```bash
cmake --build build-double --target hrsc_mhd
sed -e 's/^nx .*/nx = 64/' -e 's/^ny .*/ny = 64/' -e 's/^t_end .*/t_end = 0.1/' \
    tests/cases/orszag_tang_2d/orszag_tang.cfg > /tmp/ot_smoke.cfg
./build-double/hrsc_mhd /tmp/ot_smoke.cfg
```
Expected: prints `[mhd] t=0.100000 steps=... divB_mean=... divB_max=...` with finite values and no `[error]` (no nonphysical state).

- [ ] **Step 6: Commit**

```bash
git add src/mhd/mhd_config.hpp src/mhd_main.cpp tests/cases/orszag_tang_2d/
git commit -m "feat(mhd): wire orszag_tang case + cfgs (HLL)"
```

---

## Task 4: Shared validation harness module

**Files:**
- Create: `scripts/regression/_mhd_harness.py`
- Test: `tests/py/test_mhd_harness.py`

**Interfaces:**
- Produces: `block_average_2d(arr, ny_c, nx_c)`, `point_symmetry_residual(field)`, `reflect_y_residual(field)`, `conserved_totals(arr, gamma)`, plus subprocess helpers `run_case(...)`, `replace_or_append_cfg(...)`, `git_commit()`, `sha256_file(...)`, `resolve_binary(...)`, `parse_mhd_diagnostics(...)`, and re-exported `read_binary`.

- [ ] **Step 1: Write the failing test** (`tests/py/test_mhd_harness.py`)

```python
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts" / "regression"))
from _mhd_harness import block_average_2d, point_symmetry_residual, reflect_y_residual


def test_block_average_halves_resolution():
    # 4x4 of known blocks -> 2x2 means.
    arr = np.array([[1, 1, 2, 2],
                    [1, 1, 2, 2],
                    [3, 3, 4, 4],
                    [3, 3, 4, 4]], dtype=float)
    out = block_average_2d(arr, 2, 2)
    assert out.shape == (2, 2)
    np.testing.assert_allclose(out, [[1, 2], [3, 4]])


def test_block_average_requires_integer_factor():
    arr = np.ones((5, 4))
    try:
        block_average_2d(arr, 2, 2)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_point_symmetry_residual_zero_for_symmetric_field():
    base = np.arange(16, dtype=float).reshape(4, 4)
    sym = base + base[::-1, ::-1]  # invariant under 180-deg rotation
    assert point_symmetry_residual(sym) < 1e-12


def test_reflect_y_residual_zero_for_y_symmetric_field():
    col = np.array([0.0, 1.0, 1.0, 0.0])
    field = np.tile(col[:, None], (1, 3))  # symmetric under y -> Ny-1-y
    assert reflect_y_residual(field) < 1e-12
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "C:\Users\tangy\miniconda3\python.exe" -m pytest tests/py/test_mhd_harness.py -q`
Expected: FAIL — module `_mhd_harness` not found.

- [ ] **Step 3: Write the harness module** (`scripts/regression/_mhd_harness.py`)

```python
#!/usr/bin/env python3
"""Shared helpers for Week 13 2D MHD validation drivers.

Pure-numeric helpers (block_average_2d, point_symmetry_residual,
reflect_y_residual, conserved_totals) are unit-tested in
tests/py/test_mhd_harness.py. The subprocess runner mirrors the Week-12
mhd_2d_week12.py provenance discipline (generated cfg, stdout/stderr,
metadata.json per run).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

import numpy as np

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from io_helper import read_binary  # noqa: E402  (re-exported)

ROOT = pathlib.Path(__file__).resolve().parents[2]
RHO, MX, MY, MZ, BX, BY, BZ, E, PSI = range(9)

_DIAG_RE = re.compile(
    r"\[mhd\]\s+t=(?P<t>\S+)\s+steps=(?P<steps>\d+)\s+"
    r"divB_mean=(?P<divB_mean>\S+)\s+divB_max=(?P<divB_max>\S+)"
)


# --- pure-numeric helpers (unit-tested) ------------------------------------

def block_average_2d(arr: np.ndarray, ny_c: int, nx_c: int) -> np.ndarray:
    """Block-mean a (ny, nx) array down to (ny_c, nx_c). Requires integer factors."""
    ny, nx = arr.shape
    if ny % ny_c != 0 or nx % nx_c != 0:
        raise ValueError(f"non-integer downsample factor: ({ny},{nx}) -> ({ny_c},{nx_c})")
    fy, fx = ny // ny_c, nx // nx_c
    return arr.reshape(ny_c, fy, nx_c, fx).mean(axis=(1, 3))


def point_symmetry_residual(field: np.ndarray) -> float:
    """Relative residual under 180-deg rotation about the grid centre (OT invariant)."""
    rot = field[::-1, ::-1]
    denom = float(np.abs(field).max()) or 1.0
    return float(np.abs(field - rot).max() / denom)


def reflect_y_residual(field: np.ndarray) -> float:
    """Relative residual under y -> Ny-1-y reflection (KH shear-layer invariant)."""
    refl = field[::-1, :]
    denom = float(np.abs(field).max()) or 1.0
    return float(np.abs(field - refl).max() / denom)


def conserved_totals(arr: np.ndarray, gamma: float) -> dict[str, float]:
    """Domain sums of conserved mass and total energy (periodic-domain invariants)."""
    return {"mass": float(arr[..., RHO].sum()), "energy": float(arr[..., E].sum())}


# --- subprocess / provenance helpers ---------------------------------------

def resolve_binary(path: pathlib.Path) -> pathlib.Path:
    if path.is_file():
        return path
    exe = pathlib.Path(str(path) + ".exe")
    if exe.is_file():
        return exe
    raise FileNotFoundError(f"missing MHD binary: {path} (or {exe})")


def replace_or_append_cfg(text: str, key: str, value: str) -> str:
    out, replaced = [], False
    for line in text.splitlines():
        if line.strip().startswith("#") or "=" not in line:
            out.append(line)
            continue
        if line.split("=", 1)[0].strip() == key:
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
            ["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True,
            stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unknown"


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_mhd_diagnostics(stderr_text: str) -> dict[str, Any]:
    for line in reversed(stderr_text.splitlines()):
        m = _DIAG_RE.search(line)
        if m:
            return {"t": float(m.group("t")), "steps": int(m.group("steps")),
                    "divB_mean": float(m.group("divB_mean")),
                    "divB_max": float(m.group("divB_max")), "line": line}
    return {}


def run_case(label, cfg_text, run_dir, bin_path, source_cfg, commit, binary_sha256,
             *, output_bin=None, experiment="week13-mhd-2d"):
    run_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = run_dir / "config.cfg"
    cfg_path.write_text(cfg_text, encoding="utf-8")
    stdout_path, stderr_path = run_dir / "stdout.txt", run_dir / "stderr.txt"
    command = [str(bin_path), str(cfg_path)]
    start = time.time()
    t0 = time.perf_counter()
    with stdout_path.open("w", encoding="utf-8") as fo, stderr_path.open("w", encoding="utf-8") as fe:
        result = subprocess.run(command, cwd=str(ROOT), stdout=fo, stderr=fe, check=False)
    elapsed = time.perf_counter() - t0
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
    meta = {
        "experiment": experiment, "name": label,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": commit, "binary": str(bin_path), "binary_sha256": binary_sha256,
        "source_config": str(source_cfg), "source_config_sha256": sha256_file(source_cfg),
        "run_config": str(cfg_path), "run_config_sha256": sha256_file(cfg_path),
        "run_config_text": cfg_text, "command": command,
        "returncode": result.returncode, "elapsed_wall_s": elapsed,
        "stdout": str(stdout_path), "stderr": str(stderr_path),
        "stderr_diagnostics": parse_mhd_diagnostics(stderr_text),
    }
    (run_dir / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"run '{label}' failed (rc={result.returncode}); see {stderr_path}")
    if output_bin is not None:
        if not output_bin.is_file() or output_bin.stat().st_mtime < start:
            raise RuntimeError(f"run '{label}' did not (re)produce {output_bin}; see {stderr_path}")
    return result, meta, stderr_text
```

- [ ] **Step 4: Run test to verify it passes**

Run: `& "C:\Users\tangy\miniconda3\python.exe" -m pytest tests/py/test_mhd_harness.py -q`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/regression/_mhd_harness.py tests/py/test_mhd_harness.py
git commit -m "test(mhd): add shared 2D MHD validation harness + pure-fn tests"
```

---

## Task 5: Orszag-Tang validation driver

**Files:**
- Create: `scripts/regression/mhd_orszag_tang_2d.py`

**Interfaces:**
- Consumes: `_mhd_harness` helpers; `build-double/hrsc_mhd`; OT cfgs.
- Produces: `experiments/week13/orszag_tang/summary.{csv,json,md}`; nonzero exit on gate failure.

- [ ] **Step 1: Write the validation driver** (`scripts/regression/mhd_orszag_tang_2d.py`)

```python
#!/usr/bin/env python3
"""Orszag-Tang 2D MHD validation (Week 13).

Gates:
  1. Self-converged reference: L1/L2/Linf on density (candidate 256^2 vs the
     512^2 double reference block-averaged to 256^2). Must be finite and the
     L1 must be below a coarse sanity ceiling.
  2. Conservation: |mass(t_end) - mass(t0)| / mass(t0) at round-off level.
  3. div(B) floor: glm_cr=0.18 run has divB_max below the glm_cr=0 control.
  4. Symmetry (reported, not gated): point-symmetry residual of density.
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _mhd_harness import (ROOT, RHO, block_average_2d, conserved_totals, git_commit,
                          point_symmetry_residual, read_binary, replace_or_append_cfg,
                          resolve_binary, run_case, sha256_file)

BIN = ROOT / "build-double" / "hrsc_mhd"
CFG = ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg"
CFG_REF = ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang_ref.cfg"
OUT = ROOT / "experiments" / "week13" / "orszag_tang"
GAMMA = 5.0 / 3.0
L1_CEILING = 0.5  # coarse sanity ceiling on L1(rho); real value is far smaller


def run_grid(label, cfg_path, out_bin, bin_path, commit, sha, extra=None):
    out_bin.parent.mkdir(parents=True, exist_ok=True)
    if out_bin.exists():
        out_bin.unlink()
    text = cfg_path.read_text(encoding="utf-8")
    text = replace_or_append_cfg(text, "output_format", "binary")
    text = replace_or_append_cfg(text, "output_file", str(out_bin))
    for k, v in (extra or {}).items():
        text = replace_or_append_cfg(text, k, str(v))
    _, meta, _ = run_case(label, text, OUT / "runs" / label, bin_path, cfg_path,
                          commit, sha, output_bin=out_bin)
    return meta


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bin_path = resolve_binary(BIN)
    sha, commit = sha256_file(bin_path), git_commit()

    cand_bin = OUT / "ot_256.bin"
    ref_bin = OUT / "ot_512_ref.bin"
    meta_c = run_grid("ot_256", CFG, cand_bin, bin_path, commit, sha)
    meta_r = run_grid("ot_512_ref", CFG_REF, ref_bin, bin_path, commit, sha)
    meta_ctrl = run_grid("ot_256_cr0", CFG, OUT / "ot_256_cr0.bin", bin_path,
                         commit, sha, extra={"glm_cr": 0.0})

    _, cand = read_binary(cand_bin)
    _, ref = read_binary(ref_bin)
    rho_c = cand[..., RHO].astype(np.float64)
    rho_ref = block_average_2d(ref[..., RHO].astype(np.float64), rho_c.shape[0], rho_c.shape[1])

    diff = rho_c - rho_ref
    n = diff.size
    l1 = float(np.abs(diff).sum() / n)
    l2 = float(np.sqrt((diff ** 2).sum() / n))
    linf = float(np.abs(diff).max())

    # Conservation: re-read t0 mass by re-running candidate to t_end=0 is wasteful;
    # instead compare candidate total mass to the analytic IC mass (rho0 * ncells).
    rho0 = GAMMA * GAMMA
    mass_now = conserved_totals(cand, GAMMA)["mass"]
    mass_ic = rho0 * rho_c.size
    mass_rel = abs(mass_now - mass_ic) / mass_ic

    divb_cand = meta_c["stderr_diagnostics"]["divB_max"]
    divb_ctrl = meta_ctrl["stderr_diagnostics"]["divB_max"]
    sym = point_symmetry_residual(rho_c)

    gate_norms = np.isfinite([l1, l2, linf]).all() and l1 < L1_CEILING
    gate_mass = mass_rel < 1e-10
    gate_divb = divb_cand <= divb_ctrl * 1.02

    results = {"L1_rho": l1, "L2_rho": l2, "Linf_rho": linf, "mass_rel": mass_rel,
               "divB_max_cr018": divb_cand, "divB_max_cr0": divb_ctrl,
               "symmetry_residual": sym, "gate_norms": bool(gate_norms),
               "gate_mass": bool(gate_mass), "gate_divb": bool(gate_divb)}

    with (OUT / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results))
        w.writeheader(); w.writerow(results)
    (OUT / "summary.json").write_text(json.dumps(
        {"experiment": "week13-orszag-tang", "git_commit": commit,
         "binary_sha256": sha, "results": results,
         "runs": {"cand": meta_c, "ref": meta_r, "ctrl": meta_ctrl}}, indent=2) + "\n",
        encoding="utf-8")
    md = [
        "# Week 13 Orszag-Tang 2D Validation", "",
        "256^2 candidate vs 512^2 double reference (block-averaged), gamma=5/3, t=0.5.", "",
        "| metric | value | gate | pass? |", "|---|---:|---|---:|",
        f"| L1(rho) | {l1:.3e} | < {L1_CEILING} | {gate_norms} |",
        f"| L2(rho) | {l2:.3e} | finite | {gate_norms} |",
        f"| Linf(rho) | {linf:.3e} | finite | {gate_norms} |",
        f"| mass_rel | {mass_rel:.3e} | < 1e-10 | {gate_mass} |",
        f"| divB_max (cr=0.18 vs cr=0 ctrl {divb_ctrl:.3e}) | {divb_cand:.3e} | <= ctrl*1.02 | {gate_divb} |",
        f"| symmetry_residual (reported) | {sym:.3e} | n/a | n/a |",
    ]
    (OUT / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))

    failures = [name for name, ok in
                [("norms", gate_norms), ("mass", gate_mass), ("divB", gate_divb)] if not ok]
    if failures:
        raise SystemExit(f"GATE FAIL: {failures}")
    print("[orszag_tang] ALL GATES PASSED")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Build double + run the driver**

Run:
```bash
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double && cmake --build build-double --target hrsc_mhd
& "C:\Users\tangy\miniconda3\python.exe" scripts/regression/mhd_orszag_tang_2d.py
```
Expected: prints the summary table; `[orszag_tang] ALL GATES PASSED`; writes `experiments/week13/orszag_tang/summary.{csv,json,md}`. (The 512² reference run may take a few minutes.)

- [ ] **Step 3: Commit (scripts + scalar summaries only; binary grids stay ignored)**

```bash
git add scripts/regression/mhd_orszag_tang_2d.py experiments/week13/orszag_tang/summary.md experiments/week13/orszag_tang/summary.json experiments/week13/orszag_tang/summary.csv
git commit -m "test(mhd): Orszag-Tang 2D validation (reference + invariants, HLL)"
```

---

## Task 6: Kelvin-Helmholtz IC (`setup_kelvin_helmholtz`)

**Files:**
- Modify: `src/mhd/mhd_solver.hpp`
- Modify: `src/mhd/mhd_solver.cpp`
- Test: `tests/unit/test_mhd_kh.cpp`

**Interfaces:**
- Produces: `template<typename Real> void setup_kelvin_helmholtz(GridView<Real,MhdNVars> gv, int nx, int ny, Real dx, Real dy, Real xmin, Real ymin, Real gamma);`

- [ ] **Step 1: Write the failing test** (`tests/unit/test_mhd_kh.cpp`)

```cpp
#include "catch.hpp"
#include "core/grid.hpp"
#include "mhd/mhd_solver.hpp"
#include "mhd/mhd_state.hpp"
#include "utils/error_norms.hpp"
#include <cmath>

using namespace hrsc;

namespace {
Vec<double, MhdNVars> load_kh(GridView<double, MhdNVars> gv, int i, int j) {
    Vec<double, MhdNVars> U{};
    for (int k = 0; k < MhdNVars; ++k) U[k] = gv(i, j, k);
    return U;
}
} // namespace

TEST_CASE("KH IC has flow-aligned B, uniform rho/p, and divB=0", "[mhd][kh]") {
    const int n = 64;
    const double L = 1.0, dx = L / n, gamma = 5.0 / 3.0;
    Grid2D<double, MhdNVars> grid(n, n);
    grid.dx = dx; grid.dy = dx;
    setup_kelvin_helmholtz<double>(grid.view(), n, n, dx, dx, 0.0, 0.0, gamma);
    auto gv = grid.view();

    // Mid-band cell (0.25<y<0.75) should carry +U0 streaming; outside, -U0.
    MhdPrim<double> mid = cons_to_prim(load_kh(gv, 10, n / 2), gamma);
    MhdPrim<double> out = cons_to_prim(load_kh(gv, 10, 2), gamma);
    REQUIRE(mid.rho == Approx(1.0));
    REQUIRE(mid.p   == Approx(1.0));
    REQUIRE(mid.Bx  == Approx(0.1));      // flow-aligned B0
    REQUIRE(mid.By  == Approx(0.0));
    REQUIRE(mid.vx > 0.4);                // ~+U0 in the band
    REQUIRE(out.vx < -0.4);              // ~-U0 outside

    DivBNorms<double> d = compute_divB_norms<double>(gv, n, n, dx, dx);
    REQUIRE(d.max == Approx(0.0).margin(1e-12));  // uniform Bx, zero By
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][kh]"`
Expected: FAIL — `setup_kelvin_helmholtz` undefined.

- [ ] **Step 3: Declare the setup** (`src/mhd/mhd_solver.hpp`, near `setup_orszag_tang`)

```cpp
template <typename Real>
void setup_kelvin_helmholtz(GridView<Real, MhdNVars> gv, int nx, int ny,
                            Real dx, Real dy, Real xmin, Real ymin, Real gamma);
```

- [ ] **Step 4: Define + instantiate** (`src/mhd/mhd_solver.cpp`, after `setup_orszag_tang`)

```cpp
// Doubly-periodic double shear layer with a flow-aligned magnetic field
// (periodic-shear-layer KH benchmark). Two interfaces (y=0.25, y=0.75) keep
// the profile periodic in y. Parameters are pinned (no single MHD-KH standard):
// U0 shear half-amplitude, a shear width, delta/s the seeded vy perturbation,
// B0 flow-aligned field (Alfven Mach M_A = U0/(B0/sqrt(rho)) = 5, weak).
template <typename Real>
void setup_kelvin_helmholtz(GridView<Real, MhdNVars> gv, int nx, int ny,
                            Real dx, Real dy, Real xmin, Real ymin, Real gamma) {
    const Real pi = Real(3.14159265358979323846);
    const Real U0 = Real(0.5), a = Real(0.025);
    const Real delta = Real(0.01), s = Real(0.05);
    const Real B0 = Real(0.1);
    const Real y1 = Real(0.25), y2 = Real(0.75);
    for (int j = 0; j < ny; ++j)
        for (int i = 0; i < nx; ++i) {
            const Real x = xmin + (Real(i) + Real(0.5)) * dx;
            const Real y = ymin + (Real(j) + Real(0.5)) * dy;
            MhdPrim<Real> w{};
            w.rho = Real(1);
            w.p   = Real(1);
            // +U0 for y1<y<y2, -U0 outside; tanh-smoothed at both interfaces.
            w.vx  = U0 * (std::tanh((y - y1) / a) - std::tanh((y - y2) / a) - Real(1));
            // Symmetric vy seed localised at both interfaces.
            w.vy  = delta * std::sin(Real(2) * pi * x)
                    * (std::exp(-((y - y1) * (y - y1)) / (s * s))
                     + std::exp(-((y - y2) * (y - y2)) / (s * s)));
            w.Bx  = B0;  // flow-aligned; By=Bz=0 => div(B)=0
            store_cell(gv, i, j, prim_to_cons(w, gamma));
        }
}

template void setup_kelvin_helmholtz<float>(GridView<float, MhdNVars>, int, int, float, float, float, float, float);
template void setup_kelvin_helmholtz<double>(GridView<double, MhdNVars>, int, int, double, double, double, double, double);
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][kh]" -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/mhd/mhd_solver.hpp src/mhd/mhd_solver.cpp tests/unit/test_mhd_kh.cpp
git commit -m "feat(mhd): add Kelvin-Helmholtz double-shear-layer IC"
```

---

## Task 7: Kelvin-Helmholtz executable wiring + cfgs

**Files:**
- Modify: `src/mhd/mhd_config.hpp`
- Modify: `src/mhd_main.cpp`
- Create: `tests/cases/kelvin_helmholtz_2d/kh.cfg`
- Create: `tests/cases/kelvin_helmholtz_2d/kh_ref.cfg`

**Interfaces:**
- Produces: `MhdTestCase::KelvinHelmholtz`; cfg `test = kelvin_helmholtz`.

- [ ] **Step 1: Extend the registry** (`src/mhd/mhd_config.hpp`)

```cpp
enum class MhdTestCase { BrioWu, DivbBlob, OrszagTang, KelvinHelmholtz };

inline MhdTestCase parse_mhd_test(const std::string& value) {
    if (value == "brio_wu")          return MhdTestCase::BrioWu;
    if (value == "divb_blob")        return MhdTestCase::DivbBlob;
    if (value == "orszag_tang")      return MhdTestCase::OrszagTang;
    if (value == "kelvin_helmholtz") return MhdTestCase::KelvinHelmholtz;
    throw std::invalid_argument("unsupported MHD test case: " + value);
}
```

- [ ] **Step 2: Add the case branch** (`src/mhd_main.cpp`, before the `divb_blob` else)

```cpp
    } else if (test == hrsc::MhdTestCase::KelvinHelmholtz) {
        hrsc::setup_kelvin_helmholtz<Real>(gv, nx, ny, dx, dy, (Real)xmin, (Real)ymin, (Real)gamma);
```

- [ ] **Step 3: Write the production cfg** (`tests/cases/kelvin_helmholtz_2d/kh.cfg`)

```ini
# MHD Kelvin-Helmholtz, doubly-periodic double shear layer (Week 13 design).
# Pinned params live in setup_kelvin_helmholtz (U0=0.5, a=0.025, delta=0.01,
# s=0.05, B0=0.1, M_A=5). gamma=5/3.
test    = kelvin_helmholtz
nx      = 256
ny      = 256
xmin    = 0.0
xmax    = 1.0
ymin    = 0.0
ymax    = 1.0
gamma   = 1.6666666666666667
cfl     = 0.4
t_end   = 1.0
glm_cr  = 0.18
bc      = periodic
bc_y    = periodic
```

- [ ] **Step 4: Write the reference cfg** (`tests/cases/kelvin_helmholtz_2d/kh_ref.cfg`)

```ini
# Self-converged double reference for KH (2x candidate resolution).
test    = kelvin_helmholtz
nx      = 512
ny      = 512
xmin    = 0.0
xmax    = 1.0
ymin    = 0.0
ymax    = 1.0
gamma   = 1.6666666666666667
cfl     = 0.4
t_end   = 1.0
glm_cr  = 0.18
bc      = periodic
bc_y    = periodic
```

- [ ] **Step 5: Build + smoke-run (reduced grid)**

Run:
```bash
cmake --build build-double --target hrsc_mhd
sed -e 's/^nx .*/nx = 64/' -e 's/^ny .*/ny = 64/' -e 's/^t_end .*/t_end = 0.2/' \
    tests/cases/kelvin_helmholtz_2d/kh.cfg > /tmp/kh_smoke.cfg
./build-double/hrsc_mhd /tmp/kh_smoke.cfg
```
Expected: prints a finite `[mhd]` diagnostic line; no `[error]`.

- [ ] **Step 6: Commit**

```bash
git add src/mhd/mhd_config.hpp src/mhd_main.cpp tests/cases/kelvin_helmholtz_2d/
git commit -m "feat(mhd): wire kelvin_helmholtz case + cfgs (HLL)"
```

---

## Task 8: Kelvin-Helmholtz validation driver

**Files:**
- Create: `scripts/regression/mhd_kh_2d.py`

**Interfaces:**
- Consumes: `_mhd_harness`; `build-double/hrsc_mhd`; KH cfgs.
- Produces: `experiments/week13/kelvin_helmholtz/summary.{csv,json,md}`.

- [ ] **Step 1: Write the validation driver** (`scripts/regression/mhd_kh_2d.py`)

```python
#!/usr/bin/env python3
"""Kelvin-Helmholtz 2D MHD validation (Week 13).

Gates: self-converged reference L1/L2/Linf on density (256^2 vs 512^2
block-averaged), mass conservation, div(B) floor (cr=0.18 vs cr=0 control).
Reported: y-reflection symmetry residual of density (breaks at nonlinear
rollup, so reported not gated).
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _mhd_harness import (ROOT, RHO, block_average_2d, conserved_totals, git_commit,
                          read_binary, reflect_y_residual, replace_or_append_cfg,
                          resolve_binary, run_case, sha256_file)

BIN = ROOT / "build-double" / "hrsc_mhd"
CFG = ROOT / "tests" / "cases" / "kelvin_helmholtz_2d" / "kh.cfg"
CFG_REF = ROOT / "tests" / "cases" / "kelvin_helmholtz_2d" / "kh_ref.cfg"
OUT = ROOT / "experiments" / "week13" / "kelvin_helmholtz"
GAMMA = 5.0 / 3.0
L1_CEILING = 0.2  # coarse sanity ceiling on L1(rho) (rho0=1)


def run_grid(label, cfg_path, out_bin, bin_path, commit, sha, extra=None):
    out_bin.parent.mkdir(parents=True, exist_ok=True)
    if out_bin.exists():
        out_bin.unlink()
    text = cfg_path.read_text(encoding="utf-8")
    text = replace_or_append_cfg(text, "output_format", "binary")
    text = replace_or_append_cfg(text, "output_file", str(out_bin))
    for k, v in (extra or {}).items():
        text = replace_or_append_cfg(text, k, str(v))
    _, meta, _ = run_case(label, text, OUT / "runs" / label, bin_path, cfg_path,
                          commit, sha, output_bin=out_bin)
    return meta


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bin_path = resolve_binary(BIN)
    sha, commit = sha256_file(bin_path), git_commit()

    cand_bin, ref_bin = OUT / "kh_256.bin", OUT / "kh_512_ref.bin"
    meta_c = run_grid("kh_256", CFG, cand_bin, bin_path, commit, sha)
    meta_r = run_grid("kh_512_ref", CFG_REF, ref_bin, bin_path, commit, sha)
    meta_ctrl = run_grid("kh_256_cr0", CFG, OUT / "kh_256_cr0.bin", bin_path,
                         commit, sha, extra={"glm_cr": 0.0})

    _, cand = read_binary(cand_bin)
    _, ref = read_binary(ref_bin)
    rho_c = cand[..., RHO].astype(np.float64)
    rho_ref = block_average_2d(ref[..., RHO].astype(np.float64), rho_c.shape[0], rho_c.shape[1])

    diff = rho_c - rho_ref
    n = diff.size
    l1 = float(np.abs(diff).sum() / n)
    l2 = float(np.sqrt((diff ** 2).sum() / n))
    linf = float(np.abs(diff).max())

    mass_now = conserved_totals(cand, GAMMA)["mass"]
    mass_ic = 1.0 * rho_c.size  # uniform rho0=1
    mass_rel = abs(mass_now - mass_ic) / mass_ic

    divb_cand = meta_c["stderr_diagnostics"]["divB_max"]
    divb_ctrl = meta_ctrl["stderr_diagnostics"]["divB_max"]
    sym = reflect_y_residual(rho_c)

    gate_norms = np.isfinite([l1, l2, linf]).all() and l1 < L1_CEILING
    gate_mass = mass_rel < 1e-10
    gate_divb = divb_cand <= divb_ctrl * 1.02

    results = {"L1_rho": l1, "L2_rho": l2, "Linf_rho": linf, "mass_rel": mass_rel,
               "divB_max_cr018": divb_cand, "divB_max_cr0": divb_ctrl,
               "symmetry_residual": sym, "gate_norms": bool(gate_norms),
               "gate_mass": bool(gate_mass), "gate_divb": bool(gate_divb)}

    with (OUT / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results))
        w.writeheader(); w.writerow(results)
    (OUT / "summary.json").write_text(json.dumps(
        {"experiment": "week13-kelvin-helmholtz", "git_commit": commit,
         "binary_sha256": sha, "results": results,
         "runs": {"cand": meta_c, "ref": meta_r, "ctrl": meta_ctrl}}, indent=2) + "\n",
        encoding="utf-8")
    md = [
        "# Week 13 Kelvin-Helmholtz 2D Validation", "",
        "256^2 candidate vs 512^2 double reference (block-averaged), gamma=5/3, t=1.0.", "",
        "| metric | value | gate | pass? |", "|---|---:|---|---:|",
        f"| L1(rho) | {l1:.3e} | < {L1_CEILING} | {gate_norms} |",
        f"| L2(rho) | {l2:.3e} | finite | {gate_norms} |",
        f"| Linf(rho) | {linf:.3e} | finite | {gate_norms} |",
        f"| mass_rel | {mass_rel:.3e} | < 1e-10 | {gate_mass} |",
        f"| divB_max (cr=0.18 vs cr=0 ctrl {divb_ctrl:.3e}) | {divb_cand:.3e} | <= ctrl*1.02 | {gate_divb} |",
        f"| symmetry_residual (reported) | {sym:.3e} | n/a | n/a |",
    ]
    (OUT / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))

    failures = [name for name, ok in
                [("norms", gate_norms), ("mass", gate_mass), ("divB", gate_divb)] if not ok]
    if failures:
        raise SystemExit(f"GATE FAIL: {failures}")
    print("[kelvin_helmholtz] ALL GATES PASSED")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the driver**

Run: `& "C:\Users\tangy\miniconda3\python.exe" scripts/regression/mhd_kh_2d.py`
Expected: summary table; `[kelvin_helmholtz] ALL GATES PASSED`; writes `experiments/week13/kelvin_helmholtz/summary.{csv,json,md}`.

- [ ] **Step 3: Commit (script + scalar summaries only)**

```bash
git add scripts/regression/mhd_kh_2d.py experiments/week13/kelvin_helmholtz/summary.md experiments/week13/kelvin_helmholtz/summary.json experiments/week13/kelvin_helmholtz/summary.csv
git commit -m "test(mhd): Kelvin-Helmholtz 2D validation (reference + invariants, HLL)"
```

> **CORE DELIVERABLE COMPLETE.** Tasks 9–11 (HLLD) are enhancement; if they slip, the milestone is already met.

---

## Task 9: HLLD 5-wave solver (`hlld.hpp`)

**Files:**
- Create: `src/mhd/hlld.hpp`
- Modify: `src/mhd/mhd_solver.cpp` (add HLLD instantiations)
- Test: `tests/unit/test_mhd_hlld.cpp`

**Interfaces:**
- Consumes: `mhd_flux_x`, `mhd_hll_flux`, `cons_to_prim`, `fast_speed_x`, `Vec` arithmetic operators.
- Produces: `template<typename Real> Vec<Real,MhdNVars> mhd_hlld_flux(const Vec<Real,MhdNVars>&, const Vec<Real,MhdNVars>&, Real gamma, Real ch);` and `struct HlldFlux` (same call shape as `HllFlux`).

- [ ] **Step 1: Write the failing tests** (`tests/unit/test_mhd_hlld.cpp`)

```cpp
#include "catch.hpp"
#include "mhd/hlld.hpp"
#include "mhd/hll.hpp"
#include "mhd/mhd_solver.hpp"
#include <cmath>

using namespace hrsc;

TEST_CASE("HLLD with identical states returns the physical flux", "[mhd][hlld]") {
    const double gamma = 2.0, ch = 2.0;
    MhdPrim<double> w{};
    w.rho = 1.0; w.vx = 0.3; w.vy = 0.1; w.Bx = 0.75; w.By = 1.0; w.p = 1.0;
    Vec<double, MhdNVars> U = prim_to_cons(w, gamma);
    Vec<double, MhdNVars> F = mhd_hlld_flux(U, U, gamma, ch);
    Vec<double, MhdNVars> Fphys = mhd_flux_x(U, gamma, ch);
    for (int k = 0; k < MhdNVars; ++k) REQUIRE(F[k] == Approx(Fphys[k]).margin(1e-12));
}

TEST_CASE("HLLD GLM (Bx,psi) split is exact in the supersonic branch", "[mhd][hlld]") {
    const double gamma = 2.0, ch = 3.0;
    // Supersonic to the right so SL>=0 -> the FL branch is taken; only the
    // GLM-split BX/PSI components are overwritten and are checkable by hand.
    MhdPrim<double> wl{}, wr{};
    wl.rho = 1.0; wl.vx = 10.0; wl.Bx = 0.8; wl.By = 0.5; wl.p = 1.0; wl.psi = 0.2;
    wr.rho = 1.0; wr.vx = 10.0; wr.Bx = 0.6; wr.By = 0.5; wr.p = 1.0; wr.psi = -0.1;
    Vec<double, MhdNVars> UL = prim_to_cons(wl, gamma), UR = prim_to_cons(wr, gamma);
    Vec<double, MhdNVars> F = mhd_hlld_flux(UL, UR, gamma, ch);
    const double Bxs = 0.5 * (wl.Bx + wr.Bx) - 0.5 * (wr.psi - wl.psi) / ch;
    const double psis = 0.5 * (wl.psi + wr.psi) - 0.5 * ch * (wr.Bx - wl.Bx);
    REQUIRE(F[MhdIdx::BX]  == Approx(psis));
    REQUIRE(F[MhdIdx::PSI] == Approx(ch * ch * Bxs));
    REQUIRE(F[MhdIdx::RHO] == Approx(wl.rho * wl.vx));  // upwind physical mass flux
}

TEST_CASE("HLLD produces finite, conservative flux on Brio-Wu states", "[mhd][hlld]") {
    const double gamma = 2.0, ch = 3.0;
    MhdPrim<double> wl{}, wr{};
    wl.rho = 1.0;   wl.Bx = 0.75; wl.By = 1.0;  wl.p = 1.0;
    wr.rho = 0.125; wr.Bx = 0.75; wr.By = -1.0; wr.p = 0.1;
    Vec<double, MhdNVars> UL = prim_to_cons(wl, gamma), UR = prim_to_cons(wr, gamma);
    Vec<double, MhdNVars> F = mhd_hlld_flux(UL, UR, gamma, ch);
    for (int k = 0; k < MhdNVars; ++k) REQUIRE(std::isfinite(F[k]));
}

TEST_CASE("HLLD solver advances Brio-Wu with no nonphysical state", "[mhd][hlld][solver]") {
    MhdSolver<double, HlldFlux> s(128, 1.0 / 128, 0.0, 2.0, 0.4, 0.05);
    setup_brio_wu(s.grid_view(), 128, 1.0 / 128, 0.0, 2.0, 0.5);
    s.run();  // throws if any nonphysical state is produced
    auto gv = s.grid_view();
    for (int i = 0; i < 128; ++i) {
        REQUIRE(std::isfinite(gv(i, 0, MhdIdx::RHO)));
        REQUIRE(gv(i, 0, MhdIdx::BX) == Approx(0.75).margin(1e-6));  // psi~0 in 1D
    }
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][hlld]"`
Expected: FAIL — `mhd_hlld_flux` / `HlldFlux` undefined.

- [ ] **Step 3: Implement HLLD** (`src/mhd/hlld.hpp`)

```cpp
#pragma once

#include "mhd/hll.hpp"  // mhd_flux_x, mhd_hll_flux, cons_to_prim, fast_speed_x

#include <algorithm>
#include <cmath>
#include <limits>

namespace hrsc {

// HLLD 5-wave Riemann solver (Miyoshi & Kusano 2005) for GLM-MHD.
// The (Bx, psi) GLM pair is decoupled and solved exactly (Dedner/Mignone):
//   Bx*  = 0.5*(BxL+BxR) - 0.5*(psiR-psiL)/ch
//   psi* = 0.5*(psiL+psiR) - 0.5*ch*(BxR-BxL)
// giving F[BX]=psi*, F[PSI]=ch^2*Bx*; the 5-wave fan uses Bn=Bx* as the
// constant normal field everywhere else. Degenerate intermediate states fall
// back to HLL (already GLM-consistent via its +-ch wave-speed clamp).
template <typename Real>
HD_FUNC Vec<Real, MhdNVars> mhd_hlld_flux(const Vec<Real, MhdNVars>& UL,
                                          const Vec<Real, MhdNVars>& UR,
                                          Real gamma, Real ch) {
    const Real Bxs  = Real(0.5) * (UL[MhdIdx::BX] + UR[MhdIdx::BX])
                    - Real(0.5) * (UR[MhdIdx::PSI] - UL[MhdIdx::PSI]) / ch;
    const Real psis = Real(0.5) * (UL[MhdIdx::PSI] + UR[MhdIdx::PSI])
                    - Real(0.5) * ch * (UR[MhdIdx::BX] - UL[MhdIdx::BX]);
    const Real Bn = Bxs;

    const MhdPrim<Real> wl = cons_to_prim(UL, gamma);
    const MhdPrim<Real> wr = cons_to_prim(UR, gamma);
    const Real cfL = fast_speed_x(wl, gamma);
    const Real cfR = fast_speed_x(wr, gamma);
    const Real SL = std::min(wl.vx - cfL, wr.vx - cfR);
    const Real SR = std::max(wr.vx + cfR, wl.vx + cfL);

    auto with_glm = [&](Vec<Real, MhdNVars> F) {
        F[MhdIdx::BX] = psis;
        F[MhdIdx::PSI] = ch * ch * Bxs;
        return F;
    };

#ifdef RIEMANN_STRICT_INEQUALITY
    if (SL > Real(0)) return with_glm(mhd_flux_x(UL, gamma, ch));
    if (SR < Real(0)) return with_glm(mhd_flux_x(UR, gamma, ch));
#else
    if (SL >= Real(0)) return with_glm(mhd_flux_x(UL, gamma, ch));
    if (SR <= Real(0)) return with_glm(mhd_flux_x(UR, gamma, ch));
#endif

    const Real rhoL = wl.rho, rhoR = wr.rho;
    const Real EL = UL[MhdIdx::E], ER = UR[MhdIdx::E];
    const Real ptL = wl.p + Real(0.5) * (Bn*Bn + wl.By*wl.By + wl.Bz*wl.Bz);
    const Real ptR = wr.p + Real(0.5) * (Bn*Bn + wr.By*wr.By + wr.Bz*wr.Bz);
    const Real mL = SL - wl.vx, mR = SR - wr.vx;
    const Real denomSM = mR*rhoR - mL*rhoL;
    const Real SM = (mR*rhoR*wr.vx - mL*rhoL*wl.vx - ptR + ptL) / denomSM;
    const Real pts = (mR*rhoR*ptL - mL*rhoL*ptR
                      + rhoL*rhoR*mR*mL*(wr.vx - wl.vx)) / denomSM;

    // Build one single-star state; returns false on a degenerate denominator.
    auto build_star = [&](const MhdPrim<Real>& w, Real Ek, Real ptk, Real Sk,
                          Real& rhos, Vec<Real, MhdNVars>& Us) -> bool {
        const Real m = Sk - w.vx;
        rhos = w.rho * m / (Sk - SM);
        const Real denom = w.rho * m * (Sk - SM) - Bn*Bn;
        const Real scale = w.rho * m * m + Bn*Bn;
        if (!(std::abs(denom) > std::numeric_limits<Real>::epsilon() * scale * Real(64)))
            return false;
        const Real fac = Bn * (SM - w.vx) / denom;
        const Real vys = w.vy - w.By * fac;
        const Real vzs = w.vz - w.Bz * fac;
        const Real coef = (w.rho * m * m - Bn*Bn) / denom;
        const Real Bys = w.By * coef;
        const Real Bzs = w.Bz * coef;
        const Real vdotB  = w.vx*Bn + w.vy*w.By + w.vz*w.Bz;
        const Real vsdotBs = SM*Bn + vys*Bys + vzs*Bzs;
        const Real Es = (m*Ek - ptk*w.vx + pts*SM + Bn*(vdotB - vsdotBs)) / (Sk - SM);
        Us[MhdIdx::RHO] = rhos;   Us[MhdIdx::MX] = rhos*SM;
        Us[MhdIdx::MY]  = rhos*vys; Us[MhdIdx::MZ] = rhos*vzs;
        Us[MhdIdx::BX]  = Bn;     Us[MhdIdx::BY] = Bys; Us[MhdIdx::BZ] = Bzs;
        Us[MhdIdx::E]   = Es;     Us[MhdIdx::PSI] = Real(0);
        return true;
    };

    Real rhosL = Real(0), rhosR = Real(0);
    Vec<Real, MhdNVars> UsL{}, UsR{};
    if (!build_star(wl, EL, ptL, SL, rhosL, UsL) ||
        !build_star(wr, ER, ptR, SR, rhosR, UsR))
        return with_glm(mhd_hll_flux(UL, UR, gamma, ch));  // degenerate -> HLL

    const Vec<Real, MhdNVars> FL = mhd_flux_x(UL, gamma, ch);
    const Vec<Real, MhdNVars> FR = mhd_flux_x(UR, gamma, ch);
    const Real SsL = SM - std::abs(Bn) / std::sqrt(rhosL);
    const Real SsR = SM + std::abs(Bn) / std::sqrt(rhosR);

    Vec<Real, MhdNVars> F;
    if (SsL >= Real(0)) {
        F = FL + SL * (UsL - UL);                       // F*L
    } else if (SsR <= Real(0)) {
        F = FR + SR * (UsR - UR);                       // F*R
    } else {
        // Double-star region: combine the two single-star states across the
        // rotational (Alfven) waves, contact at SM.
        const Real sgn = (Bn >= Real(0)) ? Real(1) : Real(-1);
        const Real sqL = std::sqrt(rhosL), sqR = std::sqrt(rhosR);
        const Real inv = Real(1) / (sqL + sqR);
        const Real vyL = UsL[MhdIdx::MY]/rhosL, vzL = UsL[MhdIdx::MZ]/rhosL;
        const Real vyR = UsR[MhdIdx::MY]/rhosR, vzR = UsR[MhdIdx::MZ]/rhosR;
        const Real ByL = UsL[MhdIdx::BY], BzL = UsL[MhdIdx::BZ];
        const Real ByR = UsR[MhdIdx::BY], BzR = UsR[MhdIdx::BZ];
        const Real vyss = (sqL*vyL + sqR*vyR + (ByR - ByL)*sgn) * inv;
        const Real vzss = (sqL*vzL + sqR*vzR + (BzR - BzL)*sgn) * inv;
        const Real Byss = (sqL*ByR + sqR*ByL + sqL*sqR*(vyR - vyL)*sgn) * inv;
        const Real Bzss = (sqL*BzR + sqR*BzL + sqL*sqR*(vzR - vzL)*sgn) * inv;
        const Real vssdotBss = SM*Bn + vyss*Byss + vzss*Bzss;

        auto build_dstar = [&](Real rhos, const Vec<Real, MhdNVars>& Us,
                               Real vy, Real vz, Real By, Real Bz, Real sq, Real sign) {
            Vec<Real, MhdNVars> Uss = Us;
            Uss[MhdIdx::MX] = rhos*SM; Uss[MhdIdx::MY] = rhos*vyss; Uss[MhdIdx::MZ] = rhos*vzss;
            Uss[MhdIdx::BY] = Byss; Uss[MhdIdx::BZ] = Bzss;
            const Real vsdotBs = SM*Bn + vy*By + vz*Bz;
            Uss[MhdIdx::E] = Us[MhdIdx::E] + sign * sq * (vsdotBs - vssdotBss);
            return Uss;
        };
        const Vec<Real, MhdNVars> UssL = build_dstar(rhosL, UsL, vyL, vzL, ByL, BzL, sqL, -sgn);
        const Vec<Real, MhdNVars> UssR = build_dstar(rhosR, UsR, vyR, vzR, ByR, BzR, sqR, +sgn);

        if (SM >= Real(0))
            F = FL + SsL * UssL - (SsL - SL) * UsL - SL * UL;   // F**L
        else
            F = FR + SsR * UssR - (SsR - SR) * UsR - SR * UR;   // F**R
    }
    return with_glm(F);
}

// Functor wrapper (mirrors HllFlux) so MhdSolver can select HLLD.
struct HlldFlux {
    template <typename Real>
    HD_FUNC Vec<Real, MhdNVars> operator()(const Vec<Real, MhdNVars>& UL,
                                           const Vec<Real, MhdNVars>& UR,
                                           Real gamma, Real ch) const {
        return mhd_hlld_flux(UL, UR, gamma, ch);
    }
};

} // namespace hrsc
```

- [ ] **Step 4: Add HLLD solver instantiations** (`src/mhd/mhd_solver.cpp`)

Add the include near the top (after `#include "mhd/mhd_solver.hpp"`):

```cpp
#include "mhd/hlld.hpp"
```

Add the two instantiations next to the HLL pair at the bottom:

```cpp
template class MhdSolver<float, HlldFlux>;
template class MhdSolver<double, HlldFlux>;
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd][hlld]" -v`
Expected: PASS — identical-state→physical, GLM split exact, finite on Brio-Wu states, solver run produces no nonphysical state.

- [ ] **Step 6: Commit**

```bash
git add src/mhd/hlld.hpp src/mhd/mhd_solver.cpp tests/unit/test_mhd_hlld.cpp
git commit -m "feat(mhd): add HLLD 5-wave solver (MK2005) with GLM split + HLL fallback"
```

---

## Task 10: Runtime `riemann` selection in `hrsc_mhd`

**Files:**
- Modify: `src/mhd/mhd_config.hpp`
- Modify: `src/mhd_main.cpp`

**Interfaces:**
- Consumes: `HllFlux`, `HlldFlux`, all four `MhdSolver` instantiations.
- Produces: cfg key `riemann = hll | hlld` (default `hll`); a `run_mhd<Flux>` dispatch.

- [ ] **Step 1: Add the `MhdRiemann` enum + parser** (`src/mhd/mhd_config.hpp`)

```cpp
enum class MhdRiemann { Hll, Hlld };

inline MhdRiemann parse_mhd_riemann(const std::string& value) {
    if (value == "hll")  return MhdRiemann::Hll;
    if (value == "hlld") return MhdRiemann::Hlld;
    throw std::invalid_argument("unsupported MHD Riemann solver: " + value);
}
```

- [ ] **Step 2: Refactor `mhd_main.cpp` into a flux-templated runner**

Add the include:

```cpp
#include "mhd/hll.hpp"
#include "mhd/hlld.hpp"
```

Move the solver construction, IC dispatch, `run()`, diagnostics, and output into a function template (place it above `main`, after the anonymous-namespace helpers):

```cpp
namespace {

template <typename Flux>
int run_mhd(const hrsc::Config& cfg, int nx, int ny, double xmin, double ymin,
            double gamma, double cfl, double t_end, double x0, double glm_cr,
            hrsc::MhdTestCase test, hrsc::BoundaryType bc, hrsc::BoundaryType bc_y,
            Real dx, Real dy, const std::string& out) {
    hrsc::MhdSolver<Real, Flux> solver(nx, ny, dx, dy, (Real)xmin, (Real)ymin,
                                       (Real)gamma, (Real)cfl, t_end, bc, bc_y, (Real)glm_cr);
    auto gv = solver.grid_view();
    if (test == hrsc::MhdTestCase::BrioWu) {
        for (int j = 0; j < ny; ++j)
            hrsc::setup_brio_wu_row<Real>(gv, nx, dx, (Real)xmin, (Real)gamma, (Real)x0, j);
    } else if (test == hrsc::MhdTestCase::OrszagTang) {
        hrsc::setup_orszag_tang<Real>(gv, nx, ny, dx, dy, (Real)xmin, (Real)ymin, (Real)gamma);
    } else if (test == hrsc::MhdTestCase::KelvinHelmholtz) {
        hrsc::setup_kelvin_helmholtz<Real>(gv, nx, ny, dx, dy, (Real)xmin, (Real)ymin, (Real)gamma);
    } else {
        hrsc::setup_divb_blob<Real>(gv, nx, ny, dx, dy, (Real)xmin, (Real)ymin, (Real)gamma);
    }
    solver.run();
    gv = solver.grid_view();
    hrsc::DivBNorms<Real> db = hrsc::compute_divB_norms<Real>(gv, nx, ny, dx, dy);
    std::fprintf(stderr, "[mhd] t=%.6f steps=%d divB_mean=%.3e divB_max=%.3e\n",
                 solver.time(), solver.step_count(), (double)db.mean, (double)db.max);
    if (!out.empty())
        hrsc::write_binary<Real, hrsc::MhdNVars>(out, gv, nx, ny, dx, dy, (Real)solver.time());
    return 0;
}

} // namespace
```

In `main`, after parsing the existing keys, parse the solver and dispatch (replacing the old inline construction/run/output block):

```cpp
    const hrsc::MhdRiemann riemann = hrsc::parse_mhd_riemann(cfg.get_string("riemann", "hll"));
    validate_cfg(nx, ny, xmin, xmax, ymin, ymax, gamma, cfl, t_end, x0, glm_cr);
    const Real dx = static_cast<Real>((xmax - xmin) / nx);
    const Real dy = (ny > 1) ? static_cast<Real>((ymax - ymin) / ny) : dx;

    if (riemann == hrsc::MhdRiemann::Hlld)
        return run_mhd<hrsc::HlldFlux>(cfg, nx, ny, xmin, ymin, gamma, cfl, t_end,
                                       x0, glm_cr, test, bc, bc_y, dx, dy, out);
    return run_mhd<hrsc::HllFlux>(cfg, nx, ny, xmin, ymin, gamma, cfl, t_end,
                                  x0, glm_cr, test, bc, bc_y, dx, dy, out);
```

- [ ] **Step 3: Build both precisions + verify default is unchanged + HLLD runs**

Run:
```bash
cmake --build build-double --target hrsc_mhd
./build-double/hrsc_mhd tests/cases/brio_wu_1d/brio_wu.cfg                 # default hll
sed 's/^bc .*/bc = outflow/' tests/cases/brio_wu_1d/brio_wu.cfg > /tmp/bw_hlld.cfg
echo "riemann = hlld" >> /tmp/bw_hlld.cfg
./build-double/hrsc_mhd /tmp/bw_hlld.cfg
```
Expected: default run prints `steps=759 ... divB_max=4.441e-14` (bit-identical regression intact); HLLD run prints a finite `[mhd]` line.

- [ ] **Step 4: Run the full MHD unit suite**

Run: `cmake --build build-double --target unit_tests && ./build-double/unit_tests "[mhd]" -r compact`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/mhd/mhd_config.hpp src/mhd_main.cpp
git commit -m "feat(mhd): add cfg-selectable riemann=hll|hlld (default hll)"
```

---

## Task 11: HLLD-vs-HLL comparison + Week-13 decision + docs

**Files:**
- Create: `scripts/regression/mhd_solver_compare_2d.py`
- Modify: `docs/INDEX.md`

**Interfaces:**
- Consumes: `_mhd_harness`; `build-double/hrsc_mhd`; OT cfg.
- Produces: `experiments/week13/solver_compare/summary.{json,md}` quantifying HLL vs HLLD on Orszag-Tang, and the recorded milestone decision.

- [ ] **Step 1: Write the comparison driver** (`scripts/regression/mhd_solver_compare_2d.py`)

```python
#!/usr/bin/env python3
"""HLLD-vs-HLL comparison on Orszag-Tang (Week 13 decision point).

Runs the OT candidate grid with riemann=hll and riemann=hlld, then reports
the density difference between the two solvers and each solver's divB floor.
HLLD is expected to be less diffusive (nonzero difference is normal); the gate
is only that HLLD stays finite and physical. Informs the HLLD-or-HLL decision.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _mhd_harness import (ROOT, RHO, git_commit, read_binary, replace_or_append_cfg,
                          resolve_binary, run_case, sha256_file)

BIN = ROOT / "build-double" / "hrsc_mhd"
CFG = ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg"
OUT = ROOT / "experiments" / "week13" / "solver_compare"


def run_solver(riemann, bin_path, commit, sha):
    out_bin = OUT / f"ot_256_{riemann}.bin"
    out_bin.parent.mkdir(parents=True, exist_ok=True)
    if out_bin.exists():
        out_bin.unlink()
    text = CFG.read_text(encoding="utf-8")
    text = replace_or_append_cfg(text, "output_format", "binary")
    text = replace_or_append_cfg(text, "output_file", str(out_bin))
    text = replace_or_append_cfg(text, "riemann", riemann)
    _, meta, _ = run_case(f"ot_{riemann}", text, OUT / "runs" / riemann, bin_path, CFG,
                          commit, sha, output_bin=out_bin)
    _, arr = read_binary(out_bin)
    return meta, arr


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bin_path = resolve_binary(BIN)
    sha, commit = sha256_file(bin_path), git_commit()

    meta_hll, a_hll = run_solver("hll", bin_path, commit, sha)
    meta_hlld, a_hlld = run_solver("hlld", bin_path, commit, sha)

    rho_hll = a_hll[..., RHO].astype(np.float64)
    rho_hlld = a_hlld[..., RHO].astype(np.float64)
    diff = rho_hlld - rho_hll
    linf = float(np.abs(diff).max())
    l1 = float(np.abs(diff).sum() / diff.size)
    finite = bool(np.isfinite(rho_hlld).all())

    results = {
        "L1_rho_hlld_vs_hll": l1, "Linf_rho_hlld_vs_hll": linf,
        "divB_max_hll": meta_hll["stderr_diagnostics"]["divB_max"],
        "divB_max_hlld": meta_hlld["stderr_diagnostics"]["divB_max"],
        "hlld_finite": finite,
        "steps_hll": meta_hll["stderr_diagnostics"]["steps"],
        "steps_hlld": meta_hlld["stderr_diagnostics"]["steps"],
    }
    (OUT / "summary.json").write_text(json.dumps(
        {"experiment": "week13-solver-compare", "git_commit": commit,
         "binary_sha256": sha, "results": results}, indent=2) + "\n", encoding="utf-8")
    md = [
        "# Week 13 HLLD-vs-HLL Comparison (Orszag-Tang 256^2, t=0.5)", "",
        "| metric | value |", "|---|---:|",
        f"| L1(rho) HLLD-HLL | {l1:.3e} |",
        f"| Linf(rho) HLLD-HLL | {linf:.3e} |",
        f"| divB_max HLL | {results['divB_max_hll']:.3e} |",
        f"| divB_max HLLD | {results['divB_max_hlld']:.3e} |",
        f"| HLLD finite/physical | {finite} |", "",
        "## Decision", "",
        "- [ ] HLLD validated and adopted for remaining MHD work, OR",
        "- [ ] HLLD deferred; HLL remains the production solver (fallback per overall.md).",
        "",
        "Record the chosen option and rationale here and in week13-summary.md.",
    ]
    (OUT / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    if not finite:
        raise SystemExit("GATE FAIL: HLLD produced a non-finite Orszag-Tang field")
    print("[solver_compare] HLLD finite; comparison written.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the comparison**

Run: `& "C:\Users\tangy\miniconda3\python.exe" scripts/regression/mhd_solver_compare_2d.py`
Expected: prints comparison table + decision checklist; writes `experiments/week13/solver_compare/summary.{json,md}`. Record the HLLD-or-HLL decision in `summary.md`.

- [ ] **Step 3: Add the Week 13 row to `docs/INDEX.md`** (in the per-week table, after the Week 12 row)

```markdown
| 13 | [week13-plan.md](week13/week13-plan.md) | [week13-summary.md](week13/week13-summary.md) | (none) |
```

- [ ] **Step 4: Commit**

```bash
git add scripts/regression/mhd_solver_compare_2d.py docs/INDEX.md experiments/week13/solver_compare/summary.md experiments/week13/solver_compare/summary.json
git commit -m "test(mhd): HLLD-vs-HLL Orszag-Tang comparison + Week 13 decision record"
```

---

## Verification Strategy

1. **Unit:** every new C++ component is TDD'd (Catch2 `[mhd]` tags); the full suite runs green in `build-double` (and `build-float` after Step builds).
2. **Regression anchor:** Brio-Wu stays bit-identical (`steps=759`, `divB_max=4.441e-14`) through Tasks 1 and 10 — the proof the additive work did not perturb the validated path.
3. **Benchmark validation:** OT and KH gated on self-converged double-reference L1/L2/Linf + mass conservation + div(B) floor; symmetry residual reported.
4. **HLLD validation:** property-based unit tests + no-nonphysical integration + finite Orszag-Tang field; HLLD-vs-HLL difference quantified for the decision.
5. **Provenance:** every run writes generated cfg + stdout/stderr + metadata.json; only scalar `summary.*` are committed (binary grids stay ignored).
```
