# GPU HLL MHD Solver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a GPU HLL MHD solver (`MhdGpuSolver<Real>`) that runs Brio-Wu 1D and Orszag-Tang 2D in float and double and reproduces the CPU HLL result within a same-precision CPU-vs-GPU agreement gate, adding the hardware axis to the Week-15 precision study.

**Architecture:** Mirror the Week-6 Euler GPU path exactly. GPU kernels are **thin thread-indexing wrappers that call the existing `HD_FUNC` (`__host__ __device__`) MHD building blocks** (`mhd_slope`, `mhd_flux_x`, `mhd_hll_flux`, `HllFlux`, GLM helpers) — the per-cell arithmetic is *shared* with the CPU, not re-ported, which is what makes bit-exact CPU-vs-GPU attainable. `MhdGpuSolver<Real>` mirrors `EulerGpuSolver<Real>` (host IC → device residency → step/run → download), adding the GLM multi-dimensional source step. `--fmad=false` on the kernel TU keeps device multiply-adds matching MSVC `/fp:precise`.

**Tech Stack:** C++17/CUDA (nvcc), CMake ≥3.24 (`native` CUDA arch), Catch2 (`[gpu]` tag), MSVC host compiler. RTX 5070 (Blackwell sm_120), CUDA Toolkit 12.8+/13.x.

## Global Constraints

- **HLL only.** HLLD-on-GPU, Kelvin-Helmholtz, 512², the full 48-variant GPU sweep, GPU-side MCA, and Lyapunov are OUT of scope. (spec §1)
- Do **not** change `src/mhd/*` CPU numerics, any existing cfg file/default, the `io.hpp` output format, or the Euler `hrsc`/`gpu` path. All new code is GPU-only. (spec §1)
- **All GPU code is behind `ENABLE_CUDA` / `HRSC_HAS_CUDA`.** The default CPU-only build must stay byte-identical and the full existing CPU test suite must stay green at every task. (spec §1)
- **G-GPU gate (hard):** for each (case, precision), GPU output matches CPU output; target `ulp_max=0` (enforced by `--fmad=false`); if the 9-var+GLM path cannot reach bit-exact, fall back to a **documented tight relative tolerance** and investigate any exceedance — never widen the tolerance to hide a diff. (spec §4)
- GPU kernels use the **default limiter** (limiter selection stays cpu-only), 16×16 thread blocks, **deterministic tree reduction** for CFL (no atomics). (spec §3.2)
- Reuse `src/gpu/cuda_utils.cuh` (error-check macro, DeviceArray) and `src/gpu/gpu_grid.cuh` (device Grid2D mirror, H↔D transfer) — do not reinvent them. (spec §2)
- Windows build: MSVC via `VsDevCmd.bat`; CUDA configure needs `--allow-unsupported-compiler` (already in the CMake CUDA block). Python env (for any harness): `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe"`.
- The CPU MHD solver interface being mirrored: `MhdSolver<Real, Flux>` with 1D/2D constructors, `step()`/`run()`/`grid_view()`/`time()`/`step_count()`, GLM `glm_cr` (c_h/c_p). (spec §2)

---

### Task 1: CUDA toolkit install + toolchain validation (environment prerequisite)

**Files:** none committed (environment + a build-config verification). This task gates all others.

**Interfaces:**
- Produces: a working `nvcc` (12.8+/13.x, sm_120) and a green `gpu_smoke` build+run under `-DENABLE_CUDA=ON`.

- [ ] **Step 1: Install CUDA Toolkit** 12.8+ or 13.x (must support sm_120 / Blackwell). Confirm:

```powershell
nvcc --version   # expect release 12.8+ or 13.x
```

- [ ] **Step 2: Configure + build the existing toolchain validator** (from a `VsDevCmd.bat`-loaded console):

```powershell
cmake -B build-cuda -G Ninja -DENABLE_CUDA=ON -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release
cmake --build build-cuda --target gpu_smoke
```

Expected: configure prints `CUDA Toolkit: <ver>` and `CUDA architectures: native` (or `120`); `gpu_smoke` links. If `native` fails on sm_120, reconfigure with `-DCMAKE_CUDA_ARCHITECTURES=120`.

- [ ] **Step 3: Run the validator**

```powershell
.\build-cuda\gpu_smoke.exe
```

Expected: exit 0, prints a device-detected line. If the toolkit cannot target sm_120, STOP and report — do not proceed to solver work on a broken toolchain.

- [ ] **Step 4: Confirm the default CPU build is untouched**

```powershell
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release
cmake --build build-double --target unit_tests hrsc_mhd
.\build-double\unit_tests.exe -r compact
```

Expected: all existing tests pass (no CUDA in this build). No commit for this task; record the toolkit version in the Task 2 commit message.

---

### Task 2: GPU MHD skeleton + CMake wiring (compilable stubs, CPU build green)

**Files:**
- Create: `src/gpu/mhd_kernels.cuh`, `src/gpu/mhd_kernels.cu`, `src/gpu/mhd_gpu_solver.hpp`, `src/gpu/mhd_gpu_solver.cu`
- Modify: `CMakeLists.txt` (add MHD GPU sources to `hrsc_mhd_lib` under `if(ENABLE_CUDA)`, mirroring the `hrsc_euler` block at lines 160-179)

**Interfaces:**
- Produces: `hrsc::MhdGpuSolver<Real>` (declared, stub bodies) mirroring `EulerGpuSolver<Real>`; `extern template` for float/double. Compiles under `-DENABLE_CUDA=ON`; absent from CPU-only builds.

- [ ] **Step 1: Create the solver header** `src/gpu/mhd_gpu_solver.hpp` (mirror `euler_gpu_solver.hpp`, MhdNVars=9, add `glm_cr`):

```cpp
// src/gpu/mhd_gpu_solver.hpp
#pragma once
#ifdef HRSC_HAS_CUDA
#include "core/grid.hpp"
#include "core/types.hpp"
#include "core/boundary.hpp"
#include "mhd/mhd_state.hpp"   // MhdNVars
#include "gpu/gpu_grid.cuh"

namespace hrsc {

template <typename Real>
class MhdGpuSolver {
public:
    MhdGpuSolver(Grid2D<Real, MhdNVars> grid,
                 Real xmin, Real ymin, Real gamma, Real cfl,
                 TimeReal t_end, Real glm_cr,
                 BoundaryType bc_x, BoundaryType bc_y);
    void step(TimeReal dt);
    double run();
    Grid2D<Real, MhdNVars> download_host_grid() const;
    TimeReal current_time() const { return m_time; }
    int      step_count()   const { return m_step; }
private:
    Grid2D<Real, MhdNVars>  m_host_grid;
    GpuGrid<Real, MhdNVars> m_dev_grid;
    Real m_xmin, m_ymin, m_gamma, m_cfl, m_glm_cr;
    TimeReal m_t_end, m_time;
    int m_step;
    BoundaryType m_bc_x, m_bc_y;
};

extern template class MhdGpuSolver<float>;
extern template class MhdGpuSolver<double>;

} // namespace hrsc
#endif
```

- [ ] **Step 2: Create stub bodies** `src/gpu/mhd_gpu_solver.cu` (constructor stores members + uploads grid via `GpuGrid`; `step`/`run`/`download_host_grid` minimal-but-real: `run` loops calling `step`; `step` is an empty body for now; explicit template instantiations for float/double). Create `src/gpu/mhd_kernels.cuh` (kernel declarations, empty) and `src/gpu/mhd_kernels.cu` (`#include` guard + empty TU). Keep everything under `#ifdef HRSC_HAS_CUDA`.

- [ ] **Step 3: Wire CMake** — in `CMakeLists.txt` inside `if(ENABLE_CUDA)`, after the `hrsc_euler` GPU block, add (mirroring lines 160-179):

```cmake
    # GPU MHD solver bodies + kernels (single TU each).
    target_sources(hrsc_mhd_lib PRIVATE
        src/gpu/mhd_gpu_solver.cu
        src/gpu/mhd_kernels.cu)
    set_source_files_properties(
        src/gpu/mhd_gpu_solver.cu
        src/gpu/mhd_kernels.cu
        PROPERTIES LANGUAGE CUDA)
    # Match MSVC /fp:precise (no x64 FMA) so CPU-vs-GPU is bit-exact.
    set_source_files_properties(
        src/gpu/mhd_kernels.cu
        PROPERTIES COMPILE_OPTIONS "--fmad=false")
    set_target_properties(hrsc_mhd_lib PROPERTIES
        CUDA_SEPARABLE_COMPILATION ON
        CUDA_ARCHITECTURES "${CMAKE_CUDA_ARCHITECTURES}")
    target_link_libraries(hrsc_mhd_lib PUBLIC CUDA::cudart)
```

- [ ] **Step 4: Build both configurations**

```powershell
cmake --build build-cuda --target hrsc_mhd          # links with GPU MHD TU
cmake --build build-double --target unit_tests hrsc_mhd   # CPU-only, unchanged
.\build-double\unit_tests.exe -r compact             # all green
```

Expected: CUDA build links; CPU build + tests unchanged.

- [ ] **Step 5: Commit**

```bash
git add src/gpu/mhd_kernels.cuh src/gpu/mhd_kernels.cu src/gpu/mhd_gpu_solver.hpp src/gpu/mhd_gpu_solver.cu CMakeLists.txt
git commit -m "feat(gpu): MHD GPU skeleton + CMake wiring (CUDA <ver>, --fmad=false)"
```

---

### Task 3: Device grid upload/download for MhdNVars=9 (roundtrip test)

**Files:**
- Modify: `src/gpu/mhd_gpu_solver.cu` (implement `download_host_grid`)
- Test: `tests/unit/test_mhd_gpu_roundtrip.cpp` + `tests/unit/mhd_gpu_roundtrip_kernel.cu` (mirror the Euler `gpu_roundtrip_kernel.cu` pattern registered at CMakeLists.txt:148-150)

**Interfaces:**
- Consumes: `GpuGrid<Real, MhdNVars>` (upload in ctor, D2H in `download_host_grid`).
- Produces: an H→D→H roundtrip that preserves all 9 MHD variables bit-exactly.

- [ ] **Step 1: Write the failing `[gpu]` test** — build a 9-variable Grid2D with known values, construct `MhdGpuSolver`, `download_host_grid()`, assert every cell/var equals the input bit-exactly (`==`, not approx — H↔D copy must be lossless). Register the `.cu` half in CMakeLists `unit_tests` GPU sources (mirror lines 148-154).

```cpp
// tests/unit/test_mhd_gpu_roundtrip.cpp  (excerpt)
TEST_CASE("MHD GPU host<->device roundtrip is lossless", "[gpu][mhd]") {
    using Real = double;
    hrsc::Grid2D<Real, hrsc::MhdNVars> g(8, 4, /*nghost=*/2);
    for (int j = 0; j < g.ny(); ++j)
      for (int i = 0; i < g.nx(); ++i)
        for (int v = 0; v < hrsc::MhdNVars; ++v)
          g.at(i, j)[v] = Real(1 + v) + Real(0.5) * (i + 8 * j);
    hrsc::MhdGpuSolver<Real> solver(g, 0.0, 0.0, 5.0/3.0, 0.4, 0.0, 0.18,
                                    hrsc::BoundaryType::Outflow, hrsc::BoundaryType::Outflow);
    auto back = solver.download_host_grid();
    for (int j = 0; j < g.ny(); ++j)
      for (int i = 0; i < g.nx(); ++i)
        for (int v = 0; v < hrsc::MhdNVars; ++v)
          REQUIRE(back.at(i, j)[v] == g.at(i, j)[v]);
}
```

- [ ] **Step 2: Run to verify it fails** (`.\build-cuda\unit_tests.exe "[gpu][mhd]"`) — FAILS (download not implemented / values differ).
- [ ] **Step 3: Implement `download_host_grid`** (D2H copy from `m_dev_grid` into a host `Grid2D` copy, via `gpu_grid.cuh`).
- [ ] **Step 4: Run to verify it passes.**
- [ ] **Step 5: Commit** (`feat(gpu): MHD device grid roundtrip (9 vars)`).

---

### Task 4: X-sweep kernels (reconstruct → Hancock → HLL flux → update)

**Files:**
- Modify: `src/gpu/mhd_kernels.cuh` / `.cu` (kernels), `src/gpu/mhd_gpu_solver.cu` (call them in a 1D `step`)
- Test: `tests/unit/test_mhd_gpu_xsweep.cpp` + kernel `.cu` glue

**Interfaces:**
- Consumes the shared `HD_FUNC` building blocks (do NOT re-port arithmetic): `mhd_slope`/`mhd_minmod` (`src/mhd/mhd_reconstruct.hpp`), `mhd_flux_x` (`src/mhd/mhd_flux.hpp`), `mhd_hll_flux`/`HllFlux` (`src/mhd/hll.hpp`), matching the CPU `MhdSolver::x_sweep` (`src/mhd/mhd_solver.cpp`).
- Produces: `__global__` kernels `mhd_reconstruct_x`, `mhd_hancock_x`, `mhd_hll_flux_x`, `mhd_update_x` (16×16 blocks) whose composed one-step x-sweep matches the CPU x-sweep to ULP.

- [ ] **Step 1: Write the failing `[gpu]` oracle test** — set up a small 2D grid (e.g. 16×1 for a pure x-sweep, plus a 16×4), run **one** CPU `MhdSolver::x_sweep` step and one `MhdGpuSolver` x-sweep step with identical `dt`, `ch`, gamma; assert every cell/var matches. Target bit-exact (`==`); if not reachable, use `Approx(...).ulp(N)` with the smallest N that passes and record N in the test + report.

```cpp
// tests/unit/test_mhd_gpu_xsweep.cpp  (excerpt)
TEST_CASE("MHD GPU x-sweep matches CPU x-sweep to ULP", "[gpu][mhd]") {
    // build identical Brio-Wu-like IC into a CPU MhdSolver<Real,HllFlux> and a
    // MhdGpuSolver<Real>; advance both by one x-sweep with the same dt/ch;
    // REQUIRE field-by-field equality (== target; documented ULP fallback).
}
```

- [ ] **Step 2: Run to verify it fails.**
- [ ] **Step 3: Implement the x-sweep kernels** — each kernel indexes cells with 16×16 blocks and **calls the shared `HD_FUNC` helpers** for the per-cell math (reconstruction slopes, Hancock half-step, `mhd_hll_flux`, conservative update). Ghost handling + psi hyperbolic transport at `ch` mirror `MhdSolver::x_sweep`. Wire them into `MhdGpuSolver::step` for the 1D (ny==1) path.
- [ ] **Step 4: Run to verify it passes** (record ULP if not 0).
- [ ] **Step 5: Commit** (`feat(gpu): MHD GPU x-sweep kernels (reuse HD_FUNC numerics)`).

---

### Task 5: GLM multi-dimensional source step kernel

**Files:**
- Modify: `src/gpu/mhd_kernels.cuh` / `.cu`, `src/gpu/mhd_gpu_solver.cu`
- Test: `tests/unit/test_mhd_gpu_glm.cpp` + glue

**Interfaces:**
- Consumes: the CPU GLM helpers (`src/mhd/glm.hpp`) — full-grid `div(B) = ∂Bx/∂x + ∂By/∂y`, then integrate `∂ψ/∂t = -c_h²∇·B - (c_h/c_p)ψ`; matches the CPU GLM source step in `mhd_solver.cpp`.
- Produces: `__global__ mhd_glm_source` over the full 2D grid.

- [ ] **Step 1: Write the failing `[gpu]` test** — 2D grid with a nonzero B field; run one CPU GLM source step and one GPU `mhd_glm_source`; assert psi + energy fields match (`==` target / documented ULP).
- [ ] **Step 2: Run to verify it fails.**
- [ ] **Step 3: Implement `mhd_glm_source`** — central differences for div(B) reusing the CPU stencil arithmetic, source integration with `m_glm_cr` (c_h/c_p). Wire into `step` after both sweeps.
- [ ] **Step 4: Run to verify it passes.**
- [ ] **Step 5: Commit** (`feat(gpu): MHD GLM multi-dimensional source-step kernel`).

---

### Task 6: CFL deterministic tree reduction

**Files:**
- Modify: `src/gpu/mhd_kernels.cuh` / `.cu`, `src/gpu/mhd_gpu_solver.cu`
- Test: `tests/unit/test_mhd_gpu_cfl.cpp` + glue

**Interfaces:**
- Consumes: the CPU max-wave-speed helper used by `MhdSolver` for its CFL dt.
- Produces: `__global__ mhd_cfl_reduce` — **deterministic tree reduction (no atomics)** returning the same max wave speed / dt the CPU computes, so the two solvers take identical timestep sequences.

- [ ] **Step 1: Write the failing `[gpu]` test** — grid with a known max signal speed; assert GPU-reduced dt equals CPU dt bit-exactly (identical dt is what keeps the whole run in lockstep).
- [ ] **Step 2: Run to verify it fails.**
- [ ] **Step 3: Implement the deterministic tree reduction** (shared-memory block reduction + a fixed-order second pass; no atomics — reproducible). Use it to drive `MhdGpuSolver::run`'s dt.
- [ ] **Step 4: Run to verify it passes.**
- [ ] **Step 5: Commit** (`feat(gpu): MHD deterministic CFL tree reduction`).

---

### Task 7: MhdGpuSolver orchestration + Brio-Wu 1D CPU-vs-GPU end-to-end

**Files:**
- Modify: `src/gpu/mhd_gpu_solver.cu` (`step` = x-sweep [+ y-sweep in Task 8] + GLM; `run` = dt loop to `t_end`)
- Test: `tests/unit/test_mhd_gpu_brio_wu.cpp`

**Interfaces:**
- Produces: a full 1D Brio-Wu GPU run matching the CPU HLL run within the G-GPU gate, float + double.

- [ ] **Step 1: Write the failing `[gpu]` end-to-end test** — construct Brio-Wu 1D in both `MhdSolver<Real,HllFlux>` and `MhdGpuSolver<Real>`, `run()` both to the Brio-Wu `t_end`; assert `step_count()` equal and every field matches within the G-GPU gate; run for `Real=float` and `Real=double`.
- [ ] **Step 2: Run to verify it fails.**
- [ ] **Step 3: Complete `step`/`run` orchestration** so the composed pipeline matches CPU.
- [ ] **Step 4: Run to verify it passes** (both precisions; record ULP).
- [ ] **Step 5: Commit** (`feat(gpu): GPU HLL MHD Brio-Wu 1D matches CPU (float+double)`).

---

### Task 8: 2D (y-sweep + Lie splitting) + Orszag-Tang CPU-vs-GPU end-to-end

**Files:**
- Modify: `src/gpu/mhd_kernels.cuh` / `.cu` (y-sweep via `mhd_swap_xy` reuse), `src/gpu/mhd_gpu_solver.cu` (alternating Lie splitting)
- Test: `tests/unit/test_mhd_gpu_orszag_tang.cpp`

**Interfaces:**
- Consumes: `mhd_swap_xy` / `mhd_swap_xy_prim` (`src/mhd/mhd_flux.hpp`) so the y-sweep reuses the x-sweep kernels on swapped state (the CPU pattern).
- Produces: full 2D OT GPU run matching CPU within G-GPU, float + double.

- [ ] **Step 1: Write the failing `[gpu]` test** — OT 2D (small grid, e.g. 64², short t) in CPU and GPU solvers; assert step count + fields match within G-GPU, both precisions.
- [ ] **Step 2: Run to verify it fails.**
- [ ] **Step 3: Implement y-sweep + alternating Lie splitting** in `step` (reuse x-sweep kernels via swap).
- [ ] **Step 4: Run to verify it passes.**
- [ ] **Step 5: Commit** (`feat(gpu): GPU HLL MHD Orszag-Tang 2D matches CPU (float+double)`).

---

### Task 9: `mhd_main.cpp` device=gpu dispatch

**Files:**
- Modify: `src/mhd_main.cpp`
- Test: `tests/unit/test_mhd_device_key.cpp` (mirror `test_dispatch_device_key.cpp`)

**Interfaces:**
- Produces: `device = cpu|gpu` cfg dispatch mirroring `src/main.cpp:409-421`; `device=gpu` builds IC → `MhdGpuSolver` → download → existing divB-norm + `write_binary` path; `device=gpu` in a non-CUDA build throws `"device=gpu requires building with -DENABLE_CUDA=ON"`; default `cpu` path unchanged.

- [ ] **Step 1: Write the failing test** — parse `device` key; invalid value throws; `gpu` without `HRSC_HAS_CUDA` throws the exact message. (Mirror the Euler device-key test.)
- [ ] **Step 2: Run to verify it fails.**
- [ ] **Step 3: Implement dispatch** under `#ifdef HRSC_HAS_CUDA`, reusing the existing output path so the binary format is identical to CPU.
- [ ] **Step 4: Run to verify it passes**; also run one `device=gpu` Brio-Wu cfg end-to-end and confirm output matches a `device=cpu` run within G-GPU.
- [ ] **Step 5: Commit** (`feat(gpu): device=gpu dispatch in mhd_main`).

---

### Task 10: Docs registration + final non-regression sweep

**Files:**
- Modify: `docs/INDEX.md` (GPU MHD entry), `scripts/regression/README.md` if a regression driver is added, and add `docs/week*/` note that the hardware axis GPU HLL path is available.

- [ ] **Step 1: Final non-regression** — CPU-only build + full `unit_tests` green; CUDA build `[gpu]` tests green (record any ULP fallbacks).

```powershell
.\build-double\unit_tests.exe -r compact          # CPU: all green
.\build-cuda\unit_tests.exe "[gpu]" -r compact     # GPU: all green
```

- [ ] **Step 2: Register docs** — INDEX §GPU: `device=gpu` for `hrsc_mhd` (HLL, float+double), CPU-vs-GPU gate result (ulp_max or documented tolerance), build flag `-DENABLE_CUDA=ON`, out-of-scope note (HLLD/KH deferred).
- [ ] **Step 3: Commit** (`docs(gpu): register GPU HLL MHD hardware-axis path`).

---

## Final Reporting

After Task 10, report: the CUDA toolkit version; `gpu_smoke` result; per-kernel `[gpu]` test results; Brio-Wu 1D + OT 2D CPU-vs-GPU agreement (ulp_max=0 or the documented tolerance) for float and double; confirmation the default CPU build + full suite stayed green; and the explicit boundary — HLL only; HLLD-on-GPU, KH, GPU precision sweep, and Lyapunov remain follow-ups.
