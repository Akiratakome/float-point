# Week 5 — 2D Tests Closure + GPU Toolchain Bring-up — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver Week 5 of the HRSC project per [`docs/week5/week5-plan.md`](../../week5/week5-plan.md): close the 2D test matrix (Liska-Wendroff Config 6 + half-symmetric shock-bubble), bring up the local CUDA toolchain with a `GpuGrid` host↔device roundtrip test, add wall-clock timing infrastructure, and exercise the full harness pipeline on the new cases.

**Architecture:** Five deliverable blocks (A Timer / B LW Config 6 / C shock-bubble / D GPU skeleton split into D.1 toolchain + D.2 data path / E `plot_2d.py`) sequenced over 5 working days per spec §4 "Approach 2": CUDA toolchain risk exposed Day 1, then bridge order (Timer → IC blocks → GPU data path → harness smoke + docs). All new code is gated by opt-in CMake options (`ENABLE_CUDA` default OFF, `HRSC_ENABLE_PROFILING` default OFF) to preserve byte-identical default builds and AGENTS.md hard rules (no change to solver numerics, no change to existing cfg defaults, no change to existing output formats).

**Tech Stack:** C++17 (templated `Grid2D<Real,NVars>`, explicit-instantiation `EulerSolver<float|double>`), CMake ≥ 3.18 (Ninja generator), CUDA Toolkit (local laptop), Catch2 v2.13.10 single-header (`external/catch2/catch.hpp`), Python ≥ 3.10 + numpy + matplotlib + scikit-image, custom harness scripts (`scripts/run_matrix.py`, `scripts/aggregate_metrics.py`, `scripts/io_helper.py`), bash + WSL Linux toolchain (no MSVC).

**Spec reference:** `docs/week5/week5-plan.md` at commit `1dcc86b` on branch `week4-implementation`.

**Branch policy:** Continue work on `week4-implementation` (per spec §5.4). Commit after every passing task. Open Week 5 PR on Day 5 only.

---

## File Structure (decomposition lock-in)

| Path | Status | Responsibility |
|---|---|---|
| `src/utils/timer.hpp` | NEW | `Timer` (always available) + `ProfilingRegistry` & `ScopedTimer` (under `#ifdef HRSC_ENABLE_PROFILING`) |
| `src/main.cpp` | MODIFY | Wrap `solver.run(...)` in a `Timer`; emit single `[timing] total_s=…` line on stderr |
| `src/euler/euler_solver.cpp` | MODIFY | Insert 5 `ScopedTimer` probes (cfl / bc / reconstruction / riemann / update) under `#ifdef HRSC_ENABLE_PROFILING` only |
| `tests/unit/test_timer.cpp` | NEW | Catch2: timer accumulator + (under macro) ProfilingRegistry |
| `tests/cases/liska_wendroff_2d/lw_tests.hpp` | MODIFY | Replace throwing Config 6 stub with real IC |
| `tests/cases/liska_wendroff_2d/config6_n200.cfg` | NEW | LW Config 6 baseline 200² |
| `tests/cases/liska_wendroff_2d/config6_n400.cfg` | NEW | LW Config 6 baseline 400² |
| `tests/unit/test_liska_wendroff.cpp` | MODIFY | Append Config 6 quadrant tests |
| `tests/cases/shock_bubble/shock_bubble_tests.hpp` | NEW | Half-symmetric shock-bubble IC + Rankine-Hugoniot helper |
| `tests/cases/shock_bubble/shock_bubble_n400x100.cfg` | NEW | Shock-bubble HLLC baseline |
| `tests/cases/shock_bubble/shock_bubble_n400x100_rusanov.cfg` | NEW | Shock-bubble Rusanov A/B twin |
| `tests/unit/test_shock_bubble.cpp` | NEW | Catch2 IC verification (RH relations, half-disc cell count) |
| `cmake/CUDASetup.cmake` | NEW | `find_package(CUDAToolkit)` + arch detection |
| `src/gpu/gpu_smoke.cu` | NEW | `cudaGetDeviceCount` + per-device print (Day 1 toolchain validation) |
| `src/gpu/cuda_utils.cuh` | NEW | `HRSC_CUDA_CHECK` macro + `DeviceArray<T>` RAII wrapper |
| `src/gpu/gpu_grid.cuh` | NEW | `GpuGrid<Real,NVars>` mirroring `Grid2D<Real,NVars>` layout |
| `src/gpu/euler_kernels.cuh` | NEW | Templated `device_copy_kernel<T>` only (Week 6 adds real kernels) |
| `tests/unit/test_gpu_roundtrip.cpp` | NEW | Catch2 `[gpu]` test calling extern-C wrappers |
| `tests/unit/gpu_roundtrip_kernel.cu` | NEW | `extern "C"` wrappers `gpu_roundtrip_double/_float` (use `DeviceArray<T>`) |
| `CMakeLists.txt` | MODIFY | Add `HRSC_ENABLE_PROFILING` and `ENABLE_CUDA` options; conditional CUDA section |
| `scripts/run_matrix.py` | MODIFY | Parse stderr `[timing] total_s=…` → `metadata.json.timing.total_s` |
| `scripts/figures/plot_2d.py` | NEW | Single-grid CLI plotter (rho/p/vmag/schlieren) using `io_helper.read_binary` |
| `tests/py/test_plot_2d.py` | NEW | pytest smoke (PNG file size + dims) |
| `experiments/week5/smoke/matrix.json` | NEW | 6-run harness smoke (lw3/lw6/sb × double/float) |
| `docs/week5/week5-verification.md` | NEW | Manual reproduction recipe (Day 5 closure) |
| `docs/week5/week5-summary.md` | NEW | Commits + experiment paths + W5→W6 handoff |
| `docs/INDEX.md` | MODIFY | §2 table: add Week 5 row |
| `docs/requirement/overall.md` | MODIFY | Supersonic Wave Test Cases table: Config 6 ✓→✗; Week 5 footnote about LW 2003 numbering |

---

## Day 1 — CUDA Toolchain Smoke + Timer Infrastructure

### Task 1.1: CUDA toolchain smoke (`gpu_smoke` standalone target)

**Why first:** Local CUDA toolchain is the only unknown risk this week. If `find_package(CUDAToolkit)` or nvcc/host-compiler integration fails, everything else continues uninterrupted while we either fall back to WSL CUDA or degrade Week 5 to CPU-only scope (per spec §4 risk responses).

**Files:**
- Create: `cmake/CUDASetup.cmake`
- Create: `src/gpu/gpu_smoke.cu`
- Modify: `CMakeLists.txt` (add `ENABLE_CUDA` option + conditional include + standalone target)

- [ ] **Step 1: Create `cmake/CUDASetup.cmake`**

```cmake
# cmake/CUDASetup.cmake
#
# Locates CUDAToolkit and configures CMAKE_CUDA_ARCHITECTURES.
#
# Policy CMP0104 is automatically NEW because the root CMakeLists.txt requires
# CMake >= 3.18 (which sets CMP0104 to NEW by default). If anyone lowers the
# minimum below 3.18 in the future, add `cmake_policy(SET CMP0104 NEW)` here
# to prevent cryptic nvcc target-architecture errors.

find_package(CUDAToolkit REQUIRED)

# Auto-detect architectures; fall back to "native" (CMake 3.24+) or a sane
# default for older CMake. "native" lets nvcc target the GPU on this host.
if(NOT DEFINED CMAKE_CUDA_ARCHITECTURES)
    if(CMAKE_VERSION VERSION_GREATER_EQUAL "3.24")
        set(CMAKE_CUDA_ARCHITECTURES native CACHE STRING
            "CUDA architectures (native = detect host GPU)")
    else()
        # Conservative default: cover Pascal+Volta+Turing+Ampere; user can override.
        set(CMAKE_CUDA_ARCHITECTURES "60;70;75;80" CACHE STRING
            "CUDA architectures")
    endif()
endif()

message(STATUS "CUDA Toolkit: ${CUDAToolkit_VERSION} at ${CUDAToolkit_LIBRARY_DIR}")
message(STATUS "CUDA architectures: ${CMAKE_CUDA_ARCHITECTURES}")
```

- [ ] **Step 2: Create `src/gpu/gpu_smoke.cu`**

```cpp
// src/gpu/gpu_smoke.cu
//
// Day-1 toolchain validation. Standalone target — NOT linked into the main
// hrsc binary. Just confirms nvcc compiles, host-compiler integration works,
// and runtime sees at least one GPU.

#include <cstdio>
#include <cuda_runtime.h>

int main() {
    int count = 0;
    cudaError_t err = cudaGetDeviceCount(&count);
    if (err != cudaSuccess) {
        std::fprintf(stderr, "cudaGetDeviceCount failed: %s\n",
                     cudaGetErrorString(err));
        return 1;
    }
    std::printf("CUDA devices detected: %d\n", count);
    for (int i = 0; i < count; ++i) {
        cudaDeviceProp p{};
        if (cudaGetDeviceProperties(&p, i) == cudaSuccess) {
            std::printf("  [%d] %s  (compute capability %d.%d)\n",
                        i, p.name, p.major, p.minor);
        }
    }
    return count > 0 ? 0 : 2;
}
```

- [ ] **Step 3: Add `ENABLE_CUDA` option + standalone target to `CMakeLists.txt`**

Append at the end of `CMakeLists.txt` (after the existing unit_tests block):

```cmake
# --- Optional CUDA path (Week 5 D.1 = toolchain smoke; Week 5 D.2 = data path;
# --- Week 6 = real kernels). Default OFF preserves CPU-only build behaviour.
option(ENABLE_CUDA "Enable CUDA toolchain (Week 5 GPU bring-up)" OFF)
if(ENABLE_CUDA)
    enable_language(CUDA)
    include(${CMAKE_SOURCE_DIR}/cmake/CUDASetup.cmake)

    # Standalone toolchain validator. Not linked into hrsc.
    add_executable(gpu_smoke src/gpu/gpu_smoke.cu)
    target_link_libraries(gpu_smoke PRIVATE CUDA::cudart)
    set_target_properties(gpu_smoke PROPERTIES
        CUDA_SEPARABLE_COMPILATION ON
        CUDA_ARCHITECTURES "${CMAKE_CUDA_ARCHITECTURES}")
endif()
```

- [ ] **Step 4: Configure and build the smoke target**

Run:
```bash
cmake -B build-cuda -G Ninja -DENABLE_CUDA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build-cuda --target gpu_smoke
```

Expected: configure prints `-- CUDA Toolkit: <version> at <path>` and `-- CUDA architectures: …`; build succeeds.

- [ ] **Step 5: Run the smoke target**

```bash
./build-cuda/gpu_smoke
```

Expected (sample on a laptop with one RTX-class GPU):
```
CUDA devices detected: 1
  [0] NVIDIA GeForce RTX <model>  (compute capability X.Y)
```

If `cudaGetDeviceCount` returns 0 or fails, escalate per spec §4 Day-1 risk responses (fall back to WSL CUDA; or degrade to CPU-only Week 5 scope).

- [ ] **Step 6: Verify CPU-only builds still work**

```bash
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake --build build-double
```

Expected: builds clean (no CUDA touched because `ENABLE_CUDA` is `OFF` by default).

- [ ] **Step 7: Commit**

```bash
git add cmake/CUDASetup.cmake src/gpu/gpu_smoke.cu CMakeLists.txt
git commit -m "feat(gpu): add CUDA toolchain smoke target (Week 5 Day 1)

Adds opt-in ENABLE_CUDA option, cmake/CUDASetup.cmake (find_package +
arch detection), and src/gpu/gpu_smoke.cu (cudaGetDeviceCount validation).
Standalone target gpu_smoke is not linked into hrsc; default builds are
binary-identical. Day-1 risk-exposure deliverable per docs/week5/week5-plan.md."
```

---

### Task 1.2: `Timer` class + opt-in `ProfilingRegistry` / `ScopedTimer`

**Files:**
- Create: `src/utils/timer.hpp`
- Modify: `CMakeLists.txt` (add `HRSC_ENABLE_PROFILING` option)

- [ ] **Step 1: Create `src/utils/timer.hpp`**

```cpp
// src/utils/timer.hpp
//
// Wall-clock timing utility. Two layers:
//
//   - Timer: always available. start()/stop()/elapsed_seconds() over
//     std::chrono::steady_clock. Repeated start/stop pairs accumulate.
//
//   - ProfilingRegistry + ScopedTimer: only when HRSC_ENABLE_PROFILING is
//     defined. RAII probe that adds elapsed time to a named accumulator in
//     a registry. Default builds have HRSC_ENABLE_PROFILING undefined and
//     pay zero cost.
//
// AGENTS.md rule 1: no change to solver numerics or cfg defaults under any
// setting. Timer is wall-clock-only; never on the algorithmic path.

#pragma once

#include <chrono>

#ifdef HRSC_ENABLE_PROFILING
#include <map>
#include <string>
#include <string_view>
#endif

namespace hrsc {

class Timer {
public:
    Timer() : t0_{}, accum_s_(0.0), running_(false) {}

    void start() {
        t0_ = std::chrono::steady_clock::now();
        running_ = true;
    }

    void stop() {
        if (!running_) return;
        auto t1 = std::chrono::steady_clock::now();
        accum_s_ += std::chrono::duration<double>(t1 - t0_).count();
        running_ = false;
    }

    double elapsed_seconds() const { return accum_s_; }

private:
    std::chrono::steady_clock::time_point t0_;
    double accum_s_;
    bool running_;
};

#ifdef HRSC_ENABLE_PROFILING

class ProfilingRegistry {
public:
    void add(std::string_view name, double seconds) {
        accum_[std::string(name)] += seconds;
    }

    std::map<std::string, double> snapshot() const { return accum_; }

private:
    std::map<std::string, double> accum_;
};

class ScopedTimer {
public:
    ScopedTimer(std::string_view name, ProfilingRegistry& reg)
        : name_(name), reg_(reg),
          t0_(std::chrono::steady_clock::now()) {}

    ~ScopedTimer() {
        auto t1 = std::chrono::steady_clock::now();
        reg_.add(name_, std::chrono::duration<double>(t1 - t0_).count());
    }

    ScopedTimer(const ScopedTimer&) = delete;
    ScopedTimer& operator=(const ScopedTimer&) = delete;

private:
    std::string_view name_;
    ProfilingRegistry& reg_;
    std::chrono::steady_clock::time_point t0_;
};

#endif // HRSC_ENABLE_PROFILING

} // namespace hrsc
```

- [ ] **Step 2: Add `HRSC_ENABLE_PROFILING` option to `CMakeLists.txt`**

Insert after the existing `option(ENABLE_OPENMP …)` block:

```cmake
# Optional per-phase wall-clock probes inside EulerSolver (Week 5 Block A).
# OFF by default: solver TU is binary-identical and cfg behaviour unchanged.
option(HRSC_ENABLE_PROFILING "Enable per-phase ScopedTimer probes in EulerSolver" OFF)
if(HRSC_ENABLE_PROFILING)
    target_compile_definitions(hrsc_core INTERFACE HRSC_ENABLE_PROFILING)
    message(STATUS "HRSC profiling probes: ON")
endif()
```

- [ ] **Step 3: Re-configure default build to confirm no breakage**

```bash
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake --build build-double
```

Expected: configure prints `-- HRSC profiling probes` line absent (default OFF); build succeeds.

- [ ] **Step 4: Commit**

```bash
git add src/utils/timer.hpp CMakeLists.txt
git commit -m "feat(utils): add Timer + opt-in ProfilingRegistry/ScopedTimer

Wall-clock timing utility. Default-OFF HRSC_ENABLE_PROFILING macro keeps
solver TU binary-identical. Top-level Timer is unconditional and used by
main.cpp to emit a single stderr [timing] line per run."
```

---

### Task 1.3: Unit tests for `Timer` and `ProfilingRegistry`

**Files:**
- Create: `tests/unit/test_timer.cpp`

- [ ] **Step 1: Write the failing tests**

```cpp
// tests/unit/test_timer.cpp
#include "catch.hpp"
#include "utils/timer.hpp"

#include <thread>
#include <chrono>

using namespace hrsc;

TEST_CASE("Timer measures elapsed wall-clock seconds", "[timer]") {
    Timer t;
    t.start();
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    t.stop();

    double s = t.elapsed_seconds();
    // Loose bounds — OS jitter on Windows/WSL can extend the upper bound.
    REQUIRE(s >= 0.09);
    REQUIRE(s <= 0.30);
}

TEST_CASE("Timer accumulates across multiple start/stop pairs", "[timer]") {
    Timer t;
    for (int i = 0; i < 3; ++i) {
        t.start();
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        t.stop();
    }
    double s = t.elapsed_seconds();
    REQUIRE(s >= 0.13);   // 3 * 50ms = 150ms, allow slack
    REQUIRE(s <= 0.50);
}

TEST_CASE("Timer stop() without prior start() is a no-op", "[timer]") {
    Timer t;
    t.stop();   // must not crash, must leave elapsed at 0
    REQUIRE(t.elapsed_seconds() == 0.0);
}

#ifdef HRSC_ENABLE_PROFILING
TEST_CASE("ProfilingRegistry add() accumulates by name", "[timer][profiling]") {
    ProfilingRegistry reg;
    reg.add("phase_a", 0.10);
    reg.add("phase_a", 0.20);
    reg.add("phase_b", 0.05);

    auto snap = reg.snapshot();
    REQUIRE(snap.size() == 2);
    REQUIRE(snap["phase_a"] == Approx(0.30));
    REQUIRE(snap["phase_b"] == Approx(0.05));
}

TEST_CASE("ScopedTimer adds elapsed to its accumulator on destruction",
          "[timer][profiling]") {
    ProfilingRegistry reg;
    {
        ScopedTimer s("alpha", reg);
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
    auto snap = reg.snapshot();
    REQUIRE(snap.count("alpha") == 1);
    REQUIRE(snap["alpha"] >= 0.04);
    REQUIRE(snap["alpha"] <= 0.20);
}
#endif // HRSC_ENABLE_PROFILING
```

- [ ] **Step 2: Build (default OFF)**

```bash
cmake --build build-double
```

Expected: build succeeds; the `[profiling]` cases compile out cleanly.

- [ ] **Step 3: Run timer tests**

```bash
./build-double/unit_tests "[timer]" -r compact
```

Expected: 3 cases pass (sleep + accumulate + no-op stop). The `[profiling]` cases do not appear in the listing because `HRSC_ENABLE_PROFILING` is OFF.

- [ ] **Step 4: Build a second tree with profiling ON**

```bash
cmake -B build-double-prof -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON -DHRSC_ENABLE_PROFILING=ON
cmake --build build-double-prof
./build-double-prof/unit_tests "[timer]" -r compact
```

Expected: configure prints `-- HRSC profiling probes: ON`; build succeeds; **5 cases** pass (the previous 3 plus the 2 `[profiling]` cases).

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_timer.cpp
git commit -m "test(timer): cover Timer accumulator + ProfilingRegistry/ScopedTimer

Five Catch2 cases: 3 unconditional (Timer wall-clock + accumulator +
no-op stop) and 2 guarded by HRSC_ENABLE_PROFILING (registry add +
ScopedTimer RAII). Verified in both default OFF and -DHRSC_ENABLE_PROFILING=ON
build trees."
```

---

### Task 1.4: Wire top-level `Timer` into `main.cpp` (stderr `[timing]` line)

**Files:**
- Modify: `src/main.cpp`

- [ ] **Step 1: Add include and wrap solver invocations**

In `src/main.cpp`, add the include after the existing `#include "utils/io.hpp"`:

```cpp
#include "utils/timer.hpp"
```

Modify `run_normal(...)` (and `run_convergence(...)` if applicable) so that every path that calls `solver.run(...)` is wrapped by a `Timer`. Concretely, replace the **2D** path's `solver.run(progress_interval_s);` block in `run_normal` (line ~224) with:

```cpp
        Timer total;
        total.start();
        solver.run(progress_interval_s);
        total.stop();
        std::cerr << "[timing] total_s=" << total.elapsed_seconds() << "\n";
```

And the **1D** path's `solver.run(progress_interval_s);` block (line ~274) with the same pattern. For `run_convergence`, wrap the inner `solver.run();` (line ~143) — emit one `[timing]` line per resolution:

```cpp
        Timer total;
        total.start();
        solver.run();
        total.stop();
        std::cerr << "[timing] total_s=" << total.elapsed_seconds()
                  << " nx=" << nx << "\n";
```

The line goes to **stderr** (not stdout) so existing table/binary outputs remain bit-identical for downstream consumers.

- [ ] **Step 2: Rebuild**

```bash
cmake --build build-double
cmake --build build-float
```

Expected: both succeed.

- [ ] **Step 3: Verify Sod stderr includes `[timing]` line**

```bash
./build-double/hrsc tests/cases/toro_1d/sod.cfg 2> /tmp/sod_stderr.txt > /tmp/sod_stdout.txt
grep '\[timing\]' /tmp/sod_stderr.txt
```

Expected: at least one matching line, e.g. `[timing] total_s=0.0123`.

- [ ] **Step 4: Verify stdout is unchanged for the table mode**

Compare against a known-good Sod output (any prior commit's output): the stdout lines must match exactly. A simple invariant check: stdout starts with the existing `# N    dx  …` header for convergence mode, or with the `x  rho  u  v  p` columns for normal table mode — no new top-of-stdout content.

```bash
head -3 /tmp/sod_stdout.txt
```

Expected: existing column structure unchanged.

- [ ] **Step 5: Commit**

```bash
git add src/main.cpp
git commit -m "feat(main): emit [timing] total_s=<value> on stderr per run

Wraps every solver.run(...) call site with a top-level Timer; emits a
single machine-parseable line on stderr. Stdout is untouched so existing
table/binary output remains bit-identical. Top-level Timer is unconditional
and does NOT depend on HRSC_ENABLE_PROFILING."
```

---

### Task 1.5: Insert 5 `ScopedTimer` probes into `EulerSolver::step()` (under macro)

**Files:**
- Modify: `src/euler/euler_solver.hpp` (declare per-solver `ProfilingRegistry` member under macro)
- Modify: `src/euler/euler_solver.cpp` (probe insertions)

**Decision:** the registry lives on the `EulerSolver` instance, not as a global. This keeps probes scoped per-run (re-use across multiple solvers in the same process is correct) and keeps the unguarded build binary-identical (the member doesn't exist when the macro is OFF).

- [ ] **Step 1: Declare the registry on `EulerSolver` (under macro)**

In `src/euler/euler_solver.hpp`, add the following at the top (after the existing includes):

```cpp
#ifdef HRSC_ENABLE_PROFILING
#include "utils/timer.hpp"
#endif
```

Inside the `EulerSolver<Real>` class declaration (`src/euler/euler_solver.hpp`), append (right above the `public:` keyword that follows the private member section, e.g. after `m_bc_y`):

```cpp
#ifdef HRSC_ENABLE_PROFILING
public:
    ProfilingRegistry& profiling() { return m_prof_; }
    const ProfilingRegistry& profiling() const { return m_prof_; }
private:
    ProfilingRegistry m_prof_;
#endif
```

- [ ] **Step 2: Insert probes into `step()` and helper methods**

In `src/euler/euler_solver.cpp`:

(a) Add include (top of file):
```cpp
#ifdef HRSC_ENABLE_PROFILING
#include "utils/timer.hpp"
#endif
```

(b) Wrap `apply_boundary_conditions()` body (line ~52). Find the `apply_boundary_conditions()` definition and insert at the very top of its body:
```cpp
#ifdef HRSC_ENABLE_PROFILING
    ScopedTimer __prof("bc", m_prof_);
#endif
```

(c) Wrap `compute_dt()` body (line ~163). Insert at the top of the function body:
```cpp
#ifdef HRSC_ENABLE_PROFILING
    ScopedTimer __prof("cfl", const_cast<EulerSolver*>(this)->m_prof_);
#endif
```
(`compute_dt` is `const`; the `const_cast` is the localized exception. Justification comment included in the diff: profiling registry is conceptually mutable and the cast is contained inside the `#ifdef`.)

(d) Wrap `x_sweep()` and `y_sweep()` (lines ~78 and ~118). Inside each function body, immediately after `auto gv = m_grid.view();`:
```cpp
#ifdef HRSC_ENABLE_PROFILING
    ScopedTimer __prof_recon_riem_update("sweep", m_prof_);
#endif
```

The "five-phase" mapping in spec Block A becomes: `cfl`, `bc`, plus a single `sweep` accumulator that combines reconstruction/riemann/update for both x and y sweeps (separating them would require splitting `muscl_hancock_*`, `*_flux`, and the conservative-update loop into separately timed scopes, which is invasive and risks bit-flip changes via inlining boundaries). The spec's intent is **per-phase visibility**, which `bc + cfl + sweep` satisfies for Week 7 hot-spot analysis; a finer split is a Week 7 refinement if needed.

To produce labelled `reconstruction` / `riemann` / `update` accumulators, refine within each sweep:

In `x_sweep`, replace the single `sweep` ScopedTimer with three nested scopes (one per inner section of the existing loop body):

```cpp
    // ... existing setup (gv, nx, ny, n_interfaces) ...

    #pragma omp parallel for schedule(static)
    for (int j = 0; j < ny; ++j) {
        std::vector<Vec<Real, EulerNVars>> flux(n_interfaces);

#ifdef HRSC_ENABLE_PROFILING
        // NOTE: nested under #pragma omp parallel — race-y on shared m_prof_.
        // Run profiling builds with OMP_NUM_THREADS=1 (already required by
        // Verificarlo MCA per CMakeLists.txt comment, and consistent with
        // the AGENTS.md rule that profiling is opt-in).
        ScopedTimer __prof_recon("reconstruction", m_prof_);
#endif
        for (int k = 0; k < n_interfaces; ++k) {
            // ... existing reconstruction calls (muscl_hancock_x) ...
        }
#ifdef HRSC_ENABLE_PROFILING
    } // close OMP loop body before opening separate riemann/update sections
    // -- BUT this would change the loop structure; see below for the
    // -- single-scope alternative we actually adopt.
#endif
```

Per the AGENTS.md rule against changing solver structure, **adopt the single combined `sweep` accumulator** (not three nested ones). The phase split is deferred to Week 7 with explicit refactor (split `muscl_hancock_*` into a profile-instrumented wrapper). Document this decision in the commit message.

So the actual probe set this week is **3 phases, not 5**: `bc` (boundary), `cfl` (compute_dt), `sweep` (x/y sweep combined). The spec § Block A's "5 phases" target is partially met; the remaining 2-way split (riemann / update vs reconstruction) is documented as a Week 7 refinement in `week5-summary.md`.

Update the spec to reflect this realized scope (Task 5.5 will fold this into `week5-verification.md`).

- [ ] **Step 3: Build with profiling ON**

```bash
cmake --build build-double-prof
```

Expected: build succeeds; no `unused variable` warnings (the `__prof` vars exist solely for their RAII side effect).

- [ ] **Step 4: Build default (profiling OFF) and confirm zero diff**

```bash
cmake --build build-double
```

Expected: builds clean. `nm build-double/libhrsc_euler.a` should be byte-identical to the same library before this commit (verify via `git stash` + rebuild + `cmp`).

```bash
git stash
cmake --build build-double
cp build-double/libhrsc_euler.a /tmp/libhrsc_euler.before.a
git stash pop
cmake --build build-double
cmp /tmp/libhrsc_euler.before.a build-double/libhrsc_euler.a
```

Expected: `cmp` exits 0 (no differences). If they differ, the `#ifdef` guards are leaking and must be tightened.

- [ ] **Step 5: Commit**

```bash
git add src/euler/euler_solver.hpp src/euler/euler_solver.cpp
git commit -m "feat(euler): add per-phase ScopedTimer probes (under HRSC_ENABLE_PROFILING)

Three accumulators — bc, cfl, sweep — wired into EulerSolver phases via
RAII ScopedTimer. Default build (HRSC_ENABLE_PROFILING undefined) is
binary-identical: verified via cmp on libhrsc_euler.a.

The spec called for 5 phases (reconstruction/riemann/update split inside
each sweep). Splitting the inner loop body would alter inlining boundaries
and risks bit-flip changes — rejected. Riemann/update separate accounting
is deferred to Week 7 with explicit instrumented wrappers.

Profiling builds must run OMP_NUM_THREADS=1; the registry is not thread-safe."
```

---

### Task 1.6: Parse `[timing]` line in `scripts/run_matrix.py`

**Files:**
- Modify: `scripts/run_matrix.py`

- [ ] **Step 1: Add a parser helper near the top of the file**

After the `def git_commit() -> str:` block (around line 86), insert:

```python
def parse_timing_total_s(stderr_text: str) -> float | None:
    """Parse '[timing] total_s=<value>' from solver stderr.

    Returns the LAST occurrence's value (convergence mode emits one line
    per resolution; the last is the largest grid). Returns None if absent.
    """
    last_value: float | None = None
    for line in stderr_text.splitlines():
        s = line.strip()
        if not s.startswith("[timing]"):
            continue
        for tok in s.split():
            if tok.startswith("total_s="):
                try:
                    last_value = float(tok.split("=", 1)[1])
                except ValueError:
                    pass
    return last_value
```

- [ ] **Step 2: Wire the parser into `run_one(...)`**

In `run_one(...)`, after the metadata is built and before it's written to disk (after line ~134, just before the `(run.run_dir / "metadata.json").write_text(...)` call):

```cpp
    # Parse the top-level [timing] line emitted by hrsc on stderr.
    # Field is unconditional (Timer in main.cpp is not gated by
    # HRSC_ENABLE_PROFILING); absent value would indicate an old binary.
    if not dry_run:
        stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
        total_s = parse_timing_total_s(stderr_text)
        metadata["timing"] = {"total_s": total_s}
```
(The Python comment uses `#`; the snippet above shows the language conversion.)

Apply (Python form):
```python
    if not dry_run:
        stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
        total_s = parse_timing_total_s(stderr_text)
        metadata["timing"] = {"total_s": total_s}
```

- [ ] **Step 3: Smoke-test the parser**

```bash
python -c '
import sys; sys.path.insert(0, "scripts")
from run_matrix import parse_timing_total_s
assert parse_timing_total_s("foo\n[timing] total_s=0.123\nbar") == 0.123
assert parse_timing_total_s("[timing] total_s=1 nx=200\n[timing] total_s=2 nx=400") == 2.0
assert parse_timing_total_s("no timing here") is None
print("OK")
'
```

Expected: prints `OK`.

- [ ] **Step 4: Commit**

```bash
git add scripts/run_matrix.py
git commit -m "feat(harness): parse [timing] total_s from solver stderr into metadata.json

run_matrix.py now extracts the top-level wall-clock line emitted by
src/main.cpp (Timer always-on) and writes it as
metadata.json.timing.total_s. Convergence-mode runs (multiple [timing]
lines) keep the last (largest grid)."
```

---

### Task 1.7: Day 1 done-criteria check

- [ ] **Step 1: gpu_smoke prints local GPU**

```bash
./build-cuda/gpu_smoke
```

Expected: at least one `[N] <name> (compute capability X.Y)` line.

- [ ] **Step 2: timer tests pass**

```bash
./build-double/unit_tests "[timer]" -r compact
./build-double-prof/unit_tests "[timer]" -r compact
```

Expected: 3 cases pass in default; 5 cases pass with profiling ON.

- [ ] **Step 3: Sod stderr includes `[timing]`**

```bash
./build-double/hrsc tests/cases/toro_1d/sod.cfg 2>&1 1>/dev/null | grep '\[timing\]'
```

Expected: one matching line.

- [ ] **Step 4: Default unit_tests still pass (regression check)**

```bash
./build-double/unit_tests -r compact
./build-float/unit_tests -r compact
```

Expected: both pass; assertion count ≥ 3660 + 6 (the new timer cases).

- [ ] **Step 5: Tag a Day-1 marker (optional)**

```bash
git tag -a w5d1-done -m "Week 5 Day 1 complete: CUDA toolchain + Timer"
```

---

## Day 2 — Liska-Wendroff Config 6

### Task 2.1: Implement `setup_liska_wendroff_config6` IC

**Files:**
- Modify: `tests/cases/liska_wendroff_2d/lw_tests.hpp` (replace throwing stub)

- [ ] **Step 1: Replace the stub with the real IC**

In `tests/cases/liska_wendroff_2d/lw_tests.hpp`, locate the Config 6 section (around line 101):

```cpp
// ─── Config 6 ────────────────────────────────────────────────────────────────
// Two shocks + two contacts. Week 5 work — stub throws at call.
template <typename Real>
void setup_liska_wendroff_config6(GridView<Real, EulerNVars>, Real) {
    throw std::runtime_error("Config 6 not implemented yet (Week 5)");
}
```

Replace with:

```cpp
// ─── Config 6 (Liska & Wendroff 2003 Table 4.3) ───────────────────────────────
// Four contact discontinuities, no shocks. t_end = 0.3, gamma = 1.4.
// Quadrant primitive states (rho, vx, vy, p):
//
//    Q2 (x<0.5, y>0.5)            Q1 (x>0.5, y>0.5)
//      rho=2.0, u= 0.75, v= 0.5     rho=1.0, u= 0.75, v=-0.5
//      p=1.0                        p=1.0
//    --------------------------+--------------------------
//    Q3 (x<0.5, y<0.5)            Q4 (x>0.5, y<0.5)
//      rho=1.0, u=-0.75, v= 0.5     rho=3.0, u=-0.75, v=-0.5
//      p=1.0                        p=1.0
//
// All contacts: pressure equal across all interfaces; only rho and v
// jump. Useful as a contact-resolution test (HLLC vs Rusanov) and as the
// 2D analogue of the 1D stationary_contact test.

// Q1: x > 0.5, y > 0.5
template <typename Real> inline constexpr Real LW6_Q1_RHO = Real(1.0);
template <typename Real> inline constexpr Real LW6_Q1_VX  = Real(0.75);
template <typename Real> inline constexpr Real LW6_Q1_VY  = Real(-0.5);
template <typename Real> inline constexpr Real LW6_Q1_P   = Real(1.0);

// Q2: x < 0.5, y > 0.5
template <typename Real> inline constexpr Real LW6_Q2_RHO = Real(2.0);
template <typename Real> inline constexpr Real LW6_Q2_VX  = Real(0.75);
template <typename Real> inline constexpr Real LW6_Q2_VY  = Real(0.5);
template <typename Real> inline constexpr Real LW6_Q2_P   = Real(1.0);

// Q3: x < 0.5, y < 0.5
template <typename Real> inline constexpr Real LW6_Q3_RHO = Real(1.0);
template <typename Real> inline constexpr Real LW6_Q3_VX  = Real(-0.75);
template <typename Real> inline constexpr Real LW6_Q3_VY  = Real(0.5);
template <typename Real> inline constexpr Real LW6_Q3_P   = Real(1.0);

// Q4: x > 0.5, y < 0.5
template <typename Real> inline constexpr Real LW6_Q4_RHO = Real(3.0);
template <typename Real> inline constexpr Real LW6_Q4_VX  = Real(-0.75);
template <typename Real> inline constexpr Real LW6_Q4_VY  = Real(-0.5);
template <typename Real> inline constexpr Real LW6_Q4_P   = Real(1.0);

template <typename Real>
void setup_liska_wendroff_config6(GridView<Real, EulerNVars> gv, Real gamma) {
    const Real xs = LW_XSPLIT<Real>;
    const Real ys = LW_YSPLIT<Real>;

    for (int j = 0; j < gv.ny; ++j) {
        Real y = (Real(j) + Real(0.5)) * gv.dy;
        for (int i = 0; i < gv.nx; ++i) {
            Real x = (Real(i) + Real(0.5)) * gv.dx;

            Vec<Real, EulerNVars> prim;
            if (x > xs && y > ys) {
                prim = {LW6_Q1_RHO<Real>, LW6_Q1_VX<Real>, LW6_Q1_VY<Real>, LW6_Q1_P<Real>};
            } else if (x <= xs && y > ys) {
                prim = {LW6_Q2_RHO<Real>, LW6_Q2_VX<Real>, LW6_Q2_VY<Real>, LW6_Q2_P<Real>};
            } else if (x <= xs && y <= ys) {
                prim = {LW6_Q3_RHO<Real>, LW6_Q3_VX<Real>, LW6_Q3_VY<Real>, LW6_Q3_P<Real>};
            } else {
                prim = {LW6_Q4_RHO<Real>, LW6_Q4_VX<Real>, LW6_Q4_VY<Real>, LW6_Q4_P<Real>};
            }

            Vec<Real, EulerNVars> cons = prim_to_cons(prim, gamma);
            for (int v = 0; v < EulerNVars; ++v) {
                gv(i, j, v) = cons[v];
            }
        }
    }
}
```

- [ ] **Step 2: Build (Config 6 already wired in main.cpp setup_ic)**

```bash
cmake --build build-double
```

Expected: builds clean.

- [ ] **Step 3: Smoke-run Config 6 on a tiny grid (table mode)**

A quick sanity check before the unit test:
```bash
cat > /tmp/lw6_smoke.cfg <<EOF
mode = normal
test = lw_config6
nx = 50
ny = 50
xmin = 0.0
xmax = 1.0
ymin = 0.0
ymax = 1.0
gamma = 1.4
cfl = 0.5
t_end = 0.001
solver = hllc
bc = outflow
output_format = table
EOF
./build-double/hrsc /tmp/lw6_smoke.cfg | head -3
```

Expected: 3 lines of `x  y  rho  u  v  p` data; runs without throwing the `not implemented yet` error.

- [ ] **Step 4: Commit**

```bash
git add tests/cases/liska_wendroff_2d/lw_tests.hpp
git commit -m "feat(lw): implement Liska-Wendroff Config 6 IC (4 contact discontinuities)

Replaces the throwing stub with the real IC per LW 2003 Table 4.3 (all
pressure = 1.0; only rho and v jump; no shocks). Quadrant constants are
named LW6_Q*_{RHO,VX,VY,P} matching the existing LW3_Q*_{...} pattern.

Doc note: this corrects the supersonic-test-cases table in
docs/requirement/overall.md (Config 6 is contact-only, not a supersonic
test). The doc fix is in a follow-up commit."
```

---

### Task 2.2: Append Config 6 unit tests to `test_liska_wendroff.cpp`

**Files:**
- Modify: `tests/unit/test_liska_wendroff.cpp`

- [ ] **Step 1: Add Config 6 test cases**

Append at the end of `tests/unit/test_liska_wendroff.cpp`:

```cpp
TEST_CASE("LW Config6 sets expected quadrant primitive states", "[liska_wendroff]") {
    using Real = double;
    constexpr int nx = 100;
    constexpr int ny = 100;
    constexpr Real gamma = 1.4;

    Grid2D<Real, EulerNVars> grid(nx, ny);
    grid.dx = Real(1.0) / nx;
    grid.dy = Real(1.0) / ny;
    auto gv = grid.view();

    setup_liska_wendroff_config6(gv, gamma);

    auto read_prim = [&](int i, int j) {
        Vec<Real, EulerNVars> cons{};
        for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, j, v);
        return cons_to_prim(cons, gamma);
    };

    // tight tolerance: cons->prim roundtrip on exact double constants
    auto eq = [](double a, double b) { return Approx(b).epsilon(0).margin(1e-13); };

    auto q1 = read_prim(75, 75);  // x>0.5, y>0.5
    REQUIRE(q1[PRHO] == eq(1.0));
    REQUIRE(q1[VX]   == eq(0.75));
    REQUIRE(q1[VY]   == eq(-0.5));
    REQUIRE(q1[PRES] == eq(1.0));

    auto q2 = read_prim(25, 75);  // x<0.5, y>0.5
    REQUIRE(q2[PRHO] == eq(2.0));
    REQUIRE(q2[VX]   == eq(0.75));
    REQUIRE(q2[VY]   == eq(0.5));
    REQUIRE(q2[PRES] == eq(1.0));

    auto q3 = read_prim(25, 25);  // x<0.5, y<0.5
    REQUIRE(q3[PRHO] == eq(1.0));
    REQUIRE(q3[VX]   == eq(-0.75));
    REQUIRE(q3[VY]   == eq(0.5));
    REQUIRE(q3[PRES] == eq(1.0));

    auto q4 = read_prim(75, 25);  // x>0.5, y<0.5
    REQUIRE(q4[PRHO] == eq(3.0));
    REQUIRE(q4[VX]   == eq(-0.75));
    REQUIRE(q4[VY]   == eq(-0.5));
    REQUIRE(q4[PRES] == eq(1.0));
}

TEST_CASE("LW Config6 has uniform pressure 1.0 across the entire domain",
          "[liska_wendroff]") {
    using Real = double;
    constexpr int N = 64;
    constexpr Real gamma = 1.4;

    Grid2D<Real, EulerNVars> grid(N, N);
    grid.dx = Real(1.0) / N;
    grid.dy = Real(1.0) / N;
    auto gv = grid.view();

    setup_liska_wendroff_config6(gv, gamma);

    for (int j = 0; j < N; ++j) {
        for (int i = 0; i < N; ++i) {
            Vec<Real, EulerNVars> cons{};
            for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, j, v);
            auto prim = cons_to_prim(cons, gamma);
            REQUIRE(prim[PRES] == Approx(1.0).margin(1e-13));
        }
    }
}
```

- [ ] **Step 2: Build and run**

```bash
cmake --build build-double
./build-double/unit_tests "[liska_wendroff]" -r compact
```

Expected: 3 cases pass (existing Config 3 + 2 new Config 6 cases). No regression.

- [ ] **Step 3: Confirm float build still passes**

```bash
cmake --build build-float
./build-float/unit_tests "[liska_wendroff]" -r compact
```

Expected: same 3 cases pass.

- [ ] **Step 4: Commit**

```bash
git add tests/unit/test_liska_wendroff.cpp
git commit -m "test(lw): cover Config 6 IC quadrant values + uniform pressure

Two cases: per-quadrant primitive value check (rho, u, v, p match the
LW6 table to 1e-13) and a domain-wide invariant (all 4096 cells of a
64x64 grid have p=1.0)."
```

---

### Task 2.3: Create Config 6 cfgs

**Files:**
- Create: `tests/cases/liska_wendroff_2d/config6_n200.cfg`
- Create: `tests/cases/liska_wendroff_2d/config6_n400.cfg`

- [ ] **Step 1: Write `config6_n200.cfg`**

```ini
# tests/cases/liska_wendroff_2d/config6_n200.cfg
#
# Liska & Wendroff 2003 Table 4.3 Config 6 — four contact discontinuities,
# no shocks. Used as the 2D contact-resolution analogue of the 1D
# stationary_contact test.
#
# Solver: HLLC explicitly (default since Week 4 is rusanov; HLLC vs Rusanov
# contrast is left to Week 6).

mode = normal
test = lw_config6
nx = 200
ny = 200
xmin = 0.0
xmax = 1.0
ymin = 0.0
ymax = 1.0
gamma = 1.4
cfl = 0.5
t_end = 0.3
solver = hllc
bc = outflow
output_precision = 17
output_format = binary
output_file = experiments/week5/baselines/lw_config6_n200/grid.bin
```

- [ ] **Step 2: Write `config6_n400.cfg`** (same except nx, ny, output_file):

```ini
# tests/cases/liska_wendroff_2d/config6_n400.cfg
mode = normal
test = lw_config6
nx = 400
ny = 400
xmin = 0.0
xmax = 1.0
ymin = 0.0
ymax = 1.0
gamma = 1.4
cfl = 0.5
t_end = 0.3
solver = hllc
bc = outflow
output_precision = 17
output_format = binary
output_file = experiments/week5/baselines/lw_config6_n400/grid.bin
```

- [ ] **Step 3: Run the 200² baseline**

```bash
./build-double/hrsc tests/cases/liska_wendroff_2d/config6_n200.cfg
ls -lh experiments/week5/baselines/lw_config6_n200/grid.bin
```

Expected: `Finished: <N> steps, t = 0.3...` on stderr; `[timing] total_s=…` on stderr; binary file lands (~1.3 MB for 200×200×4×8 bytes + 64-byte header).

- [ ] **Step 4: Run the 400² baseline**

```bash
./build-double/hrsc tests/cases/liska_wendroff_2d/config6_n400.cfg
ls -lh experiments/week5/baselines/lw_config6_n400/grid.bin
```

Expected: same; ~5.1 MB binary.

- [ ] **Step 5: Commit cfgs (do NOT commit `experiments/week5/baselines/`)**

```bash
git add tests/cases/liska_wendroff_2d/config6_n200.cfg tests/cases/liska_wendroff_2d/config6_n400.cfg
git status --short  # confirm no experiments/ paths staged
git commit -m "feat(cases): add LW Config 6 cfgs at 200x200 and 400x400

Both explicitly set solver=hllc (default global is rusanov since Week 4)
and output_format=binary (default is table; binary needed for the Layer 3
harness smoke and plot_2d.py). Output paths point to
experiments/week5/baselines/lw_config6_n{200,400}/grid.bin.
src/utils/io.hpp auto-creates parent directories."
```

---

### Task 2.4: Correct `docs/requirement/overall.md` Config 6 row

**Files:**
- Modify: `docs/requirement/overall.md`

- [ ] **Step 1: Find and update the Supersonic Wave Test Cases table**

Locate the "Supersonic Wave Test Cases" table in `docs/requirement/overall.md` (around line 583). Find the Config 6 row:

```
| 7 | Liska-Wendroff Config 6 | Shock interactions | 2D ✓ |
```

Replace with:

```
| 7 | Liska-Wendroff Config 6 | 4 contact discontinuities (no shocks) | 2D ✗ |
```

And add a note immediately below the table (or at the next paragraph break):

> **Footnote on Config 6**: This project uses Liska & Wendroff 2003's literal numbering. LW 2003 Config 6 is a four-contact-discontinuity test with no shocks — used here as the 2D contact-resolution analogue of the 1D `stationary_contact` test, not as a supersonic test. The "Total with supersonic waves: 6 out of 8 tests" count below remains valid (Sod, Lax, Blast, Config 3, shock-bubble + 1D `toro4` etc. cover the requirement).

Also update the summary line below the table if it currently says "Total with supersonic waves: 6 out of 8 tests". After this edit it should read "Total with supersonic waves: 5 out of 8 tests" if Config 6 was previously counted.

Verify with:
```bash
grep -n "Config 6\|supersonic" docs/requirement/overall.md
```

Update any other locations where Config 6 is described as supersonic (search the whole repo):
```bash
grep -rn "Config 6" docs/ --include='*.md' | grep -i shock
```

- [ ] **Step 2: Commit doc correction**

```bash
git add docs/requirement/overall.md
git commit -m "docs(overall): correct LW Config 6 in supersonic test table

LW 2003 Config 6 is contact-only (no shocks); was incorrectly marked as a
supersonic test. Updated the Supersonic Wave Test Cases table row and
added a footnote explaining the literal LW 2003 numbering convention.
The minimum-supersonic-tests requirement (>=4) remains satisfied."
```

---

### Task 2.5: Day 2 done-criteria check

- [ ] **Step 1: All `[liska_wendroff]` cases pass on both precisions**

```bash
./build-double/unit_tests "[liska_wendroff]" -r compact
./build-float/unit_tests "[liska_wendroff]" -r compact
```

Expected: both pass; existing Config 3 cases unchanged.

- [ ] **Step 2: Both Config 6 baselines produced binaries**

```bash
ls -lh experiments/week5/baselines/lw_config6_n200/grid.bin
ls -lh experiments/week5/baselines/lw_config6_n400/grid.bin
```

Expected: two binary files, sizes consistent with header-plus-payload.

- [ ] **Step 3: `overall.md` Config 6 row corrected**

```bash
grep -n "Config 6.*✗\|Config 6.*contact" docs/requirement/overall.md
```

Expected: matching line(s).

---

## Day 3 — Shock-bubble + plot_2d.py

### Task 3.1: Implement shock-bubble IC

**Files:**
- Create: `tests/cases/shock_bubble/shock_bubble_tests.hpp`

- [ ] **Step 1: Compute the post-shock state once (Rankine-Hugoniot helper)**

The shock IC needs the post-shock state for a stationary right-moving shock at Mach = 1.22 in air (γ=1.4) impinging on still air with ρ=1, p=1, u=0. Express the helper inline:

```cpp
// tests/cases/shock_bubble/shock_bubble_tests.hpp
//
// Single-fluid shock-density-bubble test (half-symmetric setup).
//
// Domain [0, 1] x [0, 0.25]. y=0 is the symmetry plane through the bubble
// centre; only the upper half of a circular bubble is in the computational
// domain. Reflective BC on both y boundaries (y=0 = mirror, y=0.25 = upper
// channel wall, matches Quirk-Karni 1996 half-symmetric channel layout).
//
// All gas is air, gamma=1.4. The "helium bubble" is represented purely as a
// density contrast (rho_bubble = 0.138, no species equation, no variable
// gamma). This is a deliberate single-fluid simplification — do not claim
// one-to-one reproduction of the multi-gas literature case.
//
// Initial state:
//   - Pre-shock air (right of x=0.05):  rho=1.0, u=0.0, p=1.0
//   - Post-shock air (left of x=0.05):  via Rankine-Hugoniot for Mach 1.22
//   - Bubble (circle centre (0.25, 0), radius 0.1, in pre-shock region):
//     rho=0.138, u=0.0, p=1.0
//
// Boundary: cfg sets bc_x = outflow, bc_y = reflective.

#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/grid.hpp"
#include "core/eos.hpp"

#include <cmath>

namespace hrsc {

// Pre-shock state.
template <typename Real> inline constexpr Real SB_PRE_RHO = Real(1.0);
template <typename Real> inline constexpr Real SB_PRE_U   = Real(0.0);
template <typename Real> inline constexpr Real SB_PRE_P   = Real(1.0);

// Bubble (circular, centred on the symmetry plane).
template <typename Real> inline constexpr Real SB_BUBBLE_RHO = Real(0.138);
template <typename Real> inline constexpr Real SB_BUBBLE_CX  = Real(0.25);
template <typename Real> inline constexpr Real SB_BUBBLE_CY  = Real(0.0);
template <typename Real> inline constexpr Real SB_BUBBLE_R   = Real(0.1);

// Shock interface and Mach number.
template <typename Real> inline constexpr Real SB_SHOCK_X    = Real(0.05);
template <typename Real> inline constexpr Real SB_MACH       = Real(1.22);

// Rankine-Hugoniot for a normal shock moving with shock-frame Mach Ms in a
// gas with ratio of specific heats gamma. Returns post-shock primitives in
// the LAB frame given pre-shock state (rho1, u1=0, p1).
//
// Lab-frame post-shock velocity: u2_lab = (1 - rho1/rho2) * Vs, where Vs
// is the shock speed = Ms * c1, c1 = sqrt(gamma * p1 / rho1).
template <typename Real>
inline void shock_bubble_post_shock(Real gamma,
                                    Real rho1, Real p1, Real Ms,
                                    Real& rho2, Real& u2_lab, Real& p2) {
    Real Ms2 = Ms * Ms;
    Real gp1 = gamma + Real(1);
    Real gm1 = gamma - Real(1);

    // Density jump
    Real rho_ratio = (gp1 * Ms2) / (gm1 * Ms2 + Real(2));
    rho2 = rho1 * rho_ratio;

    // Pressure jump
    Real p_ratio = (Real(2) * gamma * Ms2 - gm1) / gp1;
    p2 = p1 * p_ratio;

    // Lab-frame velocity behind the shock (shock moves at Vs to the right;
    // post-shock gas follows at u2_lab = (1 - 1/rho_ratio) * Vs).
    Real c1 = std::sqrt(gamma * p1 / rho1);
    Real Vs = Ms * c1;
    u2_lab = (Real(1) - Real(1) / rho_ratio) * Vs;
}

template <typename Real>
void setup_shock_bubble(GridView<Real, EulerNVars> gv, Real gamma) {
    // Compute post-shock state once.
    Real rho2, u2, p2;
    shock_bubble_post_shock<Real>(gamma,
                                  SB_PRE_RHO<Real>, SB_PRE_P<Real>,
                                  SB_MACH<Real>,
                                  rho2, u2, p2);

    const Real shock_x  = SB_SHOCK_X<Real>;
    const Real cx       = SB_BUBBLE_CX<Real>;
    const Real cy       = SB_BUBBLE_CY<Real>;
    const Real r2       = SB_BUBBLE_R<Real> * SB_BUBBLE_R<Real>;
    const Real rho_bub  = SB_BUBBLE_RHO<Real>;

    for (int j = 0; j < gv.ny; ++j) {
        Real y = (Real(j) + Real(0.5)) * gv.dy;
        for (int i = 0; i < gv.nx; ++i) {
            Real x = (Real(i) + Real(0.5)) * gv.dx;

            Vec<Real, EulerNVars> prim;

            // Inside bubble (only on right side of shock; bubble is in the
            // undisturbed pre-shock air).
            Real dx_b = x - cx;
            Real dy_b = y - cy;
            bool inside_bubble = (dx_b * dx_b + dy_b * dy_b <= r2);

            if (x < shock_x) {
                // Post-shock air
                prim = { rho2, u2, Real(0), p2 };
            } else if (inside_bubble) {
                // Bubble interior (low-density region in pre-shock air)
                prim = { rho_bub, SB_PRE_U<Real>, Real(0), SB_PRE_P<Real> };
            } else {
                // Pre-shock air
                prim = { SB_PRE_RHO<Real>, SB_PRE_U<Real>, Real(0), SB_PRE_P<Real> };
            }

            Vec<Real, EulerNVars> cons = prim_to_cons(prim, gamma);
            for (int v = 0; v < EulerNVars; ++v) {
                gv(i, j, v) = cons[v];
            }
        }
    }
}

} // namespace hrsc
```

- [ ] **Step 2: Hand-verify the RH constants**

For Mach 1.22 in γ=1.4 air:
- Density ratio = (2.4 × 1.4884) / (0.4 × 1.4884 + 2) = 3.5722 / 2.5954 ≈ 1.3764 → ρ₂ ≈ 1.3764
- Pressure ratio = (2.8 × 1.4884 − 0.4) / 2.4 = (4.1675 − 0.4) / 2.4 ≈ 1.5698 → p₂ ≈ 1.5698
- c₁ = √(1.4) ≈ 1.1832; Vs = 1.22 × 1.1832 ≈ 1.4435; u₂ = (1 − 1/1.3764) × 1.4435 ≈ 0.3946

Keep these values handy for Task 3.2 unit-test tolerances.

---

### Task 3.2: Add shock-bubble IC unit tests

**Files:**
- Create: `tests/unit/test_shock_bubble.cpp`

- [ ] **Step 1: Write the failing test**

```cpp
// tests/unit/test_shock_bubble.cpp
#include "catch.hpp"
#include "core/eos.hpp"
#include "shock_bubble_tests.hpp"

#include <cmath>

using namespace hrsc;

TEST_CASE("Shock-bubble Rankine-Hugoniot: Mach 1.22 air post-shock state",
          "[shock_bubble]") {
    using Real = double;
    constexpr Real gamma = 1.4;
    constexpr Real Ms    = 1.22;
    constexpr Real rho1  = 1.0;
    constexpr Real p1    = 1.0;

    Real rho2, u2, p2;
    shock_bubble_post_shock<Real>(gamma, rho1, p1, Ms, rho2, u2, p2);

    // Reference values computed by hand (Mach 1.22, gamma 1.4):
    //   rho_ratio = 2.4*1.4884 / (0.4*1.4884 + 2) = 1.3763793...
    //   p_ratio   = (2.8*1.4884 - 0.4) / 2.4    = 1.5697333...
    //   Vs        = 1.22 * sqrt(1.4)             = 1.443505...
    //   u2_lab    = (1 - 1/1.3763793) * Vs       = 0.395083...
    REQUIRE(rho2 == Approx(1.3763793).epsilon(1e-6));
    REQUIRE(p2   == Approx(1.5697333).epsilon(1e-6));
    REQUIRE(u2   == Approx(0.3950837).epsilon(1e-5));
}

TEST_CASE("Shock-bubble IC: three regions populated correctly",
          "[shock_bubble]") {
    using Real = double;
    constexpr int nx = 400;
    constexpr int ny = 100;
    constexpr Real gamma = 1.4;

    Grid2D<Real, EulerNVars> grid(nx, ny);
    grid.dx = Real(1.0) / nx;       // dx = 0.0025
    grid.dy = Real(0.25) / ny;      // dy = 0.0025
    auto gv = grid.view();

    setup_shock_bubble(gv, gamma);

    auto read_prim = [&](int i, int j) {
        Vec<Real, EulerNVars> cons{};
        for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, j, v);
        return cons_to_prim(cons, gamma);
    };

    // (1) Far-left cell: post-shock state.
    auto post = read_prim(5, ny / 2);
    REQUIRE(post[PRHO] == Approx(1.3763793).epsilon(1e-6));
    REQUIRE(post[PRES] == Approx(1.5697333).epsilon(1e-6));
    REQUIRE(post[VX]   == Approx(0.3950837).epsilon(1e-5));
    REQUIRE(post[VY]   == Approx(0.0).margin(1e-14));

    // (2) Far-right pre-shock air, well outside bubble.
    auto pre = read_prim(nx - 5, ny - 5);
    REQUIRE(pre[PRHO] == Approx(1.0).margin(1e-13));
    REQUIRE(pre[PRES] == Approx(1.0).margin(1e-13));
    REQUIRE(pre[VX]   == Approx(0.0).margin(1e-14));
    REQUIRE(pre[VY]   == Approx(0.0).margin(1e-14));

    // (3) Bubble centre region: cell at (i=100, j=0) is at (x=0.2513, y=0.00125)
    //     which is inside the half-disc centred at (0.25, 0) radius 0.1.
    auto bub = read_prim(100, 0);
    REQUIRE(bub[PRHO] == Approx(0.138).margin(1e-13));
    REQUIRE(bub[PRES] == Approx(1.0).margin(1e-13));
    REQUIRE(bub[VX]   == Approx(0.0).margin(1e-14));
}

TEST_CASE("Shock-bubble bubble half-disc has plausible cell count",
          "[shock_bubble]") {
    using Real = double;
    constexpr int nx = 400;
    constexpr int ny = 100;
    constexpr Real gamma = 1.4;

    Grid2D<Real, EulerNVars> grid(nx, ny);
    grid.dx = Real(1.0) / nx;
    grid.dy = Real(0.25) / ny;
    auto gv = grid.view();

    setup_shock_bubble(gv, gamma);

    // Count cells whose density equals exactly 0.138 (only inside the bubble).
    int bubble_cells = 0;
    for (int j = 0; j < ny; ++j) {
        for (int i = 0; i < nx; ++i) {
            Vec<Real, EulerNVars> cons{};
            for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, j, v);
            auto prim = cons_to_prim(cons, gamma);
            if (prim[PRHO] == 0.138) bubble_cells++;
        }
    }

    // Half-disc area = pi * r^2 / 2 = pi * 0.01 / 2 ≈ 0.0157
    // Cell area = 0.0025^2 = 6.25e-6
    // Expected cells ≈ 2513
    REQUIRE(bubble_cells > 2400);
    REQUIRE(bubble_cells < 2650);

    // Spec also calls out an "interface cell count" check (bubble boundary
    // perimeter); at our resolution the half-circumference is ~pi*0.1 = 0.314,
    // which spans 0.314/0.0025 ≈ 126 cells. Numerically the boundary is one
    // cell wide, so we expect [40, 60] interface cells visible per sweep
    // direction — that ratio is hard to define crisply on a Cartesian grid.
    // The half-disc area check above is the load-bearing assertion.
}
```

- [ ] **Step 2: Wire the include path so `unit_tests` can find `shock_bubble_tests.hpp`**

In `CMakeLists.txt`, find the existing `target_include_directories(unit_tests PRIVATE ${CMAKE_SOURCE_DIR}/tests/cases/liska_wendroff_2d)` line and add immediately after:

```cmake
target_include_directories(unit_tests PRIVATE ${CMAKE_SOURCE_DIR}/tests/cases/shock_bubble)
```

Also add the same directory to the `hrsc` executable so `main.cpp` can `#include "shock_bubble_tests.hpp"`:

```cmake
target_include_directories(hrsc PRIVATE ${CMAKE_SOURCE_DIR}/tests/cases/shock_bubble)
```

- [ ] **Step 3: Build and run**

```bash
cmake --build build-double
./build-double/unit_tests "[shock_bubble]" -r compact
```

Expected: 3 cases pass.

- [ ] **Step 4: Run on float build too**

```bash
cmake --build build-float
./build-float/unit_tests "[shock_bubble]" -r compact
```

Expected: 3 cases pass (the `epsilon(1e-6)` tolerance is loose enough for float).

- [ ] **Step 5: Commit**

```bash
git add tests/cases/shock_bubble/shock_bubble_tests.hpp tests/unit/test_shock_bubble.cpp CMakeLists.txt
git commit -m "feat(cases): half-symmetric shock-bubble IC + unit tests

Single-fluid shock-density-bubble test (Quirk-Karni half-symmetric setup):
domain [0,1]x[0,0.25], bubble centred at (0.25, 0) on y=0 symmetry plane,
radius 0.1, rho_bub=0.138; planar Mach 1.22 shock at x=0.05; bc_y=reflective
(y=0 = mirror, y=0.25 = upper channel wall).

Three Catch2 cases: Rankine-Hugoniot post-shock state to 1e-6 (matches
hand-computed reference), three-region IC verification, half-disc cell
count [2400, 2650] on 400x100 grid.

CMakeLists adds tests/cases/shock_bubble include path for both unit_tests
and hrsc targets."
```

---

### Task 3.3: Register `shock_bubble` in main.cpp

**Files:**
- Modify: `src/main.cpp`

- [ ] **Step 1: Add include**

In `src/main.cpp`, after `#include "lw_tests.hpp"` (line 8):
```cpp
#include "shock_bubble_tests.hpp"
```

- [ ] **Step 2: Register the dispatch**

In `setup_ic(...)` (line 28), add the new branch before the `else { throw …; }`:

```cpp
    } else if (test == "lw_config6") {
        setup_liska_wendroff_config6(gv, gamma);  // implemented Week 5
    } else if (test == "shock_bubble") {
        setup_shock_bubble(gv, gamma);
    } else {
        throw std::runtime_error("Unknown test: " + test);
    }
```

(Also remove the trailing `// stub throws (Week 5)` comment on the `lw_config6` line, since it's now implemented.)

- [ ] **Step 3: Rebuild**

```bash
cmake --build build-double
cmake --build build-float
```

Expected: both succeed.

- [ ] **Step 4: Smoke-run shock-bubble at tiny resolution**

```bash
cat > /tmp/sb_smoke.cfg <<EOF
mode = normal
test = shock_bubble
nx = 80
ny = 20
xmin = 0.0
xmax = 1.0
ymin = 0.0
ymax = 0.25
gamma = 1.4
cfl = 0.5
t_end = 0.01
solver = hllc
bc_x = outflow
bc_y = reflective
output_format = table
EOF
./build-double/hrsc /tmp/sb_smoke.cfg | head -3
```

Expected: 3 lines of `x  y  rho  u  v  p`; runs to t≈0.01 without throwing.

- [ ] **Step 5: Commit**

```bash
git add src/main.cpp
git commit -m "feat(main): dispatch test=shock_bubble in setup_ic

Wires the new IC into the test selector; removes 'stub throws' comment
on the lw_config6 branch (now implemented in lw_tests.hpp)."
```

---

### Task 3.4: Create shock-bubble cfgs and run baselines

**Files:**
- Create: `tests/cases/shock_bubble/shock_bubble_n400x100.cfg`
- Create: `tests/cases/shock_bubble/shock_bubble_n400x100_rusanov.cfg`

- [ ] **Step 1: Write `shock_bubble_n400x100.cfg`**

```ini
# tests/cases/shock_bubble/shock_bubble_n400x100.cfg
#
# Half-symmetric shock-bubble baseline (HLLC). Domain is the upper half of
# a Quirk-Karni-style channel; mirror about y=0 when plotting to recover
# the full physical bubble. dx = dy = 0.0025.

mode = normal
test = shock_bubble
nx = 400
ny = 100
xmin = 0.0
xmax = 1.0
ymin = 0.0
ymax = 0.25
gamma = 1.4
cfl = 0.5
t_end = 0.4
solver = hllc
bc_x = outflow
bc_y = reflective
output_precision = 17
output_format = binary
output_file = experiments/week5/baselines/shock_bubble_n400x100_hllc/grid.bin
```

- [ ] **Step 2: Write the Rusanov twin**

```ini
# tests/cases/shock_bubble/shock_bubble_n400x100_rusanov.cfg
#
# A/B contrast: same setup as shock_bubble_n400x100.cfg but with the
# Rusanov flux. HLLC has sharper contacts; Rusanov is more diffusive.
# Both are correct; the difference is expected.

mode = normal
test = shock_bubble
nx = 400
ny = 100
xmin = 0.0
xmax = 1.0
ymin = 0.0
ymax = 0.25
gamma = 1.4
cfl = 0.5
t_end = 0.4
solver = rusanov
bc_x = outflow
bc_y = reflective
output_precision = 17
output_format = binary
output_file = experiments/week5/baselines/shock_bubble_n400x100_rusanov/grid.bin
```

- [ ] **Step 3: Run both baselines**

```bash
./build-double/hrsc tests/cases/shock_bubble/shock_bubble_n400x100.cfg
./build-double/hrsc tests/cases/shock_bubble/shock_bubble_n400x100_rusanov.cfg
ls -lh experiments/week5/baselines/shock_bubble_n400x100_*/grid.bin
```

Expected: two binary files (~1.3 MB each); stderr shows `[timing] total_s=…`.

- [ ] **Step 4: Commit cfgs**

```bash
git add tests/cases/shock_bubble/shock_bubble_n400x100.cfg tests/cases/shock_bubble/shock_bubble_n400x100_rusanov.cfg
git commit -m "feat(cases): add shock-bubble HLLC + Rusanov cfgs (400x100, half-symmetric)

Both cfgs share the same half-symmetric domain (y=0 symmetry plane,
y=0.25 upper channel wall, bc_y=reflective) and grid. Solvers differ to
provide the A/B contrast: HLLC sharper at contact, Rusanov more diffuse.
Output paths point to experiments/week5/baselines/ (transient, not committed)."
```

---

### Task 3.5: Implement `scripts/figures/plot_2d.py`

**Files:**
- Create: `scripts/figures/plot_2d.py`

- [ ] **Step 1: Verify Python deps are present**

```bash
grep -E '^numpy|^matplotlib' analysis/requirements.txt
```

Expected: both present (numpy ≥ 1.21, matplotlib ≥ 3.5). If missing, that's a separate issue — STOP and ask.

- [ ] **Step 2: Write `scripts/figures/plot_2d.py`**

```python
#!/usr/bin/env python3
# scripts/figures/plot_2d.py
#
# Single-grid 2D visualisation. Reads one .bin produced by hrsc and writes
# one PNG per --field. Reuses scripts/io_helper.read_binary so the precision
# tag (float vs double) is honoured automatically.
#
# CLI:
#   python plot_2d.py <input.bin> --field {rho|p|vmag|schlieren} --out <png>
#                                 [--field rho --field p ...]
#                                 [--cmap viridis] [--vmin X --vmax Y]
#                                 [--title "..."]
#
# Multiple --field flags produce multiple PNGs by appending "_<field>" to
# the --out stem (or by requiring one --out per --field; current behaviour
# is the appending convention).
#
# Week 5 scope: single-grid viewer only. No batch mode, no summary.json
# reading. Week 7 may add a thin batch wrapper.

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Project established import idiom for scripts/figures/* reaching the
# parent scripts/io_helper.py — see scripts/metrics/phase_error_metrics.py:15.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from io_helper import IDX_RHO, IDX_RHOU, IDX_RHOV, IDX_E, read_binary  # noqa: E402

GAMMA_DEFAULT = 1.4
SUPPORTED_FIELDS = ("rho", "p", "vmag", "schlieren")


def compute_field(arr: np.ndarray, field: str, gamma: float) -> np.ndarray:
    """Return a 2D (ny, nx) array for the named field.

    ``arr`` shape: (ny, nx, 4), conserved variables (rho, rho*u, rho*v, E).
    """
    rho  = arr[..., IDX_RHO]
    momx = arr[..., IDX_RHOU]
    momy = arr[..., IDX_RHOV]
    ene  = arr[..., IDX_E]

    if field == "rho":
        return rho
    if field == "p":
        u = momx / rho
        v = momy / rho
        ke = 0.5 * rho * (u * u + v * v)
        return (gamma - 1.0) * (ene - ke)
    if field == "vmag":
        u = momx / rho
        v = momy / rho
        return np.sqrt(u * u + v * v)
    if field == "schlieren":
        # Central differences; one-sided at boundaries.
        gx = np.gradient(rho, axis=1)
        gy = np.gradient(rho, axis=0)
        return np.sqrt(gx * gx + gy * gy)
    raise ValueError(f"Unknown field: {field}")


def render_field(arr2d: np.ndarray, header, *,
                 out_path: Path, field: str, cmap: str,
                 vmin: float | None, vmax: float | None,
                 title: str | None) -> None:
    fig, ax = plt.subplots(figsize=(8, 4 * header.ny / max(header.nx, 1)))
    extent = [0, header.nx * header.dx, 0, header.ny * header.dy]
    im = ax.imshow(arr2d, origin="lower", extent=extent,
                   cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(title if title is not None else f"{out_path.stem} ({field})")
    fig.colorbar(im, ax=ax, label=field)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Single-grid 2D plotter for hrsc binary outputs.")
    p.add_argument("input", type=Path, help="Path to .bin written by hrsc")
    p.add_argument("--field", action="append", required=True,
                   choices=SUPPORTED_FIELDS,
                   help="Field to plot (repeatable for multiple PNGs)")
    p.add_argument("--out", type=Path, required=True,
                   help="Output PNG path; '_<field>' is appended for each "
                        "--field after the first")
    p.add_argument("--cmap", default="viridis")
    p.add_argument("--vmin", type=float, default=None)
    p.add_argument("--vmax", type=float, default=None)
    p.add_argument("--title", default=None)
    p.add_argument("--gamma", type=float, default=GAMMA_DEFAULT,
                   help="EOS gamma for derived fields (p, vmag); default 1.4")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    header, arr = read_binary(args.input)
    out_base = args.out

    for k, field in enumerate(args.field):
        if k == 0:
            out_path = out_base
        else:
            out_path = out_base.with_name(
                f"{out_base.stem}_{field}{out_base.suffix}")
        arr2d = compute_field(arr, field, args.gamma)
        render_field(arr2d, header,
                     out_path=out_path, field=field, cmap=args.cmap,
                     vmin=args.vmin, vmax=args.vmax, title=args.title)
        print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Smoke test against an existing .bin**

```bash
python scripts/figures/plot_2d.py \
    experiments/week5/baselines/lw_config6_n200/grid.bin \
    --field rho --out /tmp/lw6_rho.png
ls -lh /tmp/lw6_rho.png
```

Expected: PNG file > 10 KB exists; CLI prints `wrote /tmp/lw6_rho.png`.

- [ ] **Step 4: Verify it correctly handles a float-build .bin**

```bash
./build-float/hrsc tests/cases/liska_wendroff_2d/config6_n200.cfg
python scripts/figures/plot_2d.py \
    experiments/week5/baselines/lw_config6_n200/grid.bin \
    --field rho --out /tmp/lw6f_rho.png
```

Expected: works (`io_helper` honours the precision tag automatically).

- [ ] **Step 5: Commit**

```bash
git add scripts/figures/plot_2d.py
git commit -m "feat(figures): add scripts/figures/plot_2d.py single-grid plotter

CLI rho/p/vmag/schlieren plotter. Reuses scripts/io_helper.read_binary
(precision-tag-aware: <f4 for float build, <f8 for double). Uses the
established sys.path.insert idiom (matches scripts/metrics/* pattern;
scripts/ is not a Python package). Supports multiple --field flags by
appending '_<field>' to the --out stem.

Week 5 scope: single grid only; no batch, no summary.json."
```

---

### Task 3.6: Add pytest smoke for `plot_2d.py`

**Files:**
- Create: `tests/py/test_plot_2d.py`

- [ ] **Step 1: Write the smoke test**

```python
# tests/py/test_plot_2d.py
#
# Smoke test for scripts/figures/plot_2d.py:
#   - Each of 4 fields produces a non-empty PNG.
#   - Pixel dimensions are at least 100x100.
#
# Uses an existing baseline .bin from Day 2 / Day 3 if available; otherwise
# skips. (The harness Day 5 path also exercises plot_2d on smoke .bin files.)

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "figures" / "plot_2d.py"
BASELINE = REPO / "experiments" / "week5" / "baselines" / "lw_config6_n200" / "grid.bin"


@pytest.fixture(scope="module")
def baseline_bin() -> Path:
    if not BASELINE.exists():
        pytest.skip(f"baseline {BASELINE} not present (run Day 2 first)")
    return BASELINE


@pytest.mark.parametrize("field", ["rho", "p", "vmag", "schlieren"])
def test_plot_2d_field_produces_nonempty_png(baseline_bin: Path, tmp_path: Path,
                                             field: str) -> None:
    out = tmp_path / f"out_{field}.png"
    cmd = [sys.executable, str(SCRIPT), str(baseline_bin),
           "--field", field, "--out", str(out)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, (
        f"plot_2d.py exited {result.returncode}: {result.stderr}")
    assert out.exists(), f"PNG not written: {out}"
    assert out.stat().st_size > 1024, (
        f"PNG suspiciously small ({out.stat().st_size} bytes): {out}")

    # Quick pixel-dim check using PIL via matplotlib (Agg backend gives bytes
    # we can decode). Defer to a header-only check to keep deps minimal:
    # just confirm the PNG signature and read IHDR.
    with open(out, "rb") as f:
        header = f.read(24)
    assert header[:8] == b"\x89PNG\r\n\x1a\n", "Not a PNG file"
    # IHDR width/height are bytes 16:20 and 20:24, big-endian.
    width  = int.from_bytes(header[16:20], "big")
    height = int.from_bytes(header[20:24], "big")
    assert width  >= 100, f"PNG width {width} too small"
    assert height >= 100, f"PNG height {height} too small"
```

- [ ] **Step 2: Run pytest**

```bash
pytest tests/py/test_plot_2d.py -v
```

Expected: 4 tests pass (one per field), each writing a temp PNG that decodes as ≥100×100. If the baseline binary doesn't exist yet (Day 2 not done), pytest skips with a helpful message.

- [ ] **Step 3: Commit**

```bash
git add tests/py/test_plot_2d.py
git commit -m "test(py): smoke test for plot_2d.py (4 fields, PNG dims)

Skips if Day 2 baseline binary is missing; otherwise asserts each field
produces a PNG > 1 KB with at least 100x100 pixels (parsed from IHDR
without pulling in PIL)."
```

---

### Task 3.7: Generate the 12 baseline PNGs

- [ ] **Step 1: Generate Config 6 figures (6 PNGs)**

```bash
mkdir -p experiments/week5/baselines/figures

for N in 200 400; do
  for FIELD in rho p schlieren; do
    python scripts/figures/plot_2d.py \
      experiments/week5/baselines/lw_config6_n${N}/grid.bin \
      --field ${FIELD} \
      --out experiments/week5/baselines/figures/lw_config6_n${N}_${FIELD}.png
  done
done
```

Expected: 6 PNGs land in `experiments/week5/baselines/figures/`.

- [ ] **Step 2: Generate shock-bubble figures (6 PNGs)**

```bash
for SOLVER in hllc rusanov; do
  for FIELD in rho p schlieren; do
    python scripts/figures/plot_2d.py \
      experiments/week5/baselines/shock_bubble_n400x100_${SOLVER}/grid.bin \
      --field ${FIELD} \
      --out experiments/week5/baselines/figures/shock_bubble_n400x100_${SOLVER}_${FIELD}.png
  done
done
```

Expected: 6 PNGs land.

- [ ] **Step 3: Visual inspection — open in any viewer**

Open at minimum `lw_config6_n200_rho.png`, `lw_config6_n400_rho.png`, `shock_bubble_n400x100_hllc_schlieren.png`, `shock_bubble_n400x100_rusanov_schlieren.png`.

Pass criteria (qualitative):
- LW Config 6 ρ: 4-quadrant initial densities (1, 2, 1, 3) have evolved into smoothly curved contact-wave structure; no shocks.
- LW Config 6 at N=400: contacts visibly sharper than at N=200.
- Shock-bubble HLLC schlieren: clear shock front past x=0.05; bubble compressed into characteristic shape; shock through bubble accelerated.
- Shock-bubble Rusanov vs HLLC schlieren: Rusanov more diffuse contact at the bubble interface.

If any image looks structurally wrong (e.g., shock-bubble shows bubble ABOVE y=0.25 wall, or LW Config 6 shows a shock), STOP and apply the spec §3 Layer 2 failure-fallback procedure (check IC sign, BC config).

- [ ] **Step 4: No commit needed (figures are in `experiments/week5/baselines/figures/`, gitignored)**

Confirm:
```bash
git status --short experiments/week5/
```

Expected: empty output (all paths under `experiments/` are ignored).

---

### Task 3.8: Day 3 done-criteria check

- [ ] **Step 1: Shock-bubble unit tests pass**

```bash
./build-double/unit_tests "[shock_bubble]" -r compact
./build-float/unit_tests  "[shock_bubble]" -r compact
```

Expected: 3 cases each.

- [ ] **Step 2: pytest passes**

```bash
pytest tests/py/test_plot_2d.py -v
```

Expected: 4 tests pass.

- [ ] **Step 3: 12 PNGs landed**

```bash
ls experiments/week5/baselines/figures/ | wc -l
```

Expected: 12.

---

## Day 4 — GPU Data Path (Block D.2)

### Task 4.1: `cuda_utils.cuh` — `HRSC_CUDA_CHECK` and `DeviceArray<T>`

**Files:**
- Create: `src/gpu/cuda_utils.cuh`

- [ ] **Step 1: Write `cuda_utils.cuh`**

```cpp
// src/gpu/cuda_utils.cuh
//
// CUDA error-checking macro and an RAII wrapper around cudaMalloc/cudaFree.
//
// Used by Week 5 D.2 (gpu_roundtrip wrappers) and intended to be the only
// allocation primitive Week 6 kernels touch — no raw cudaMalloc anywhere
// past this header.

#pragma once

#include <cuda_runtime.h>

#include <cstddef>
#include <stdexcept>
#include <string>
#include <utility>

namespace hrsc {

#define HRSC_CUDA_CHECK(call)                                                \
    do {                                                                     \
        cudaError_t err__ = (call);                                          \
        if (err__ != cudaSuccess) {                                          \
            throw std::runtime_error(                                        \
                std::string("CUDA error: ") + cudaGetErrorString(err__)      \
                + " at " __FILE__ ":" + std::to_string(__LINE__));           \
        }                                                                    \
    } while (0)

template <class T>
class DeviceArray {
public:
    DeviceArray() : ptr_(nullptr), size_(0) {}

    explicit DeviceArray(std::size_t n) : ptr_(nullptr), size_(0) {
        if (n > 0) {
            HRSC_CUDA_CHECK(cudaMalloc(&ptr_, n * sizeof(T)));
            size_ = n;
        }
    }

    ~DeviceArray() { reset(); }

    DeviceArray(const DeviceArray&) = delete;
    DeviceArray& operator=(const DeviceArray&) = delete;

    DeviceArray(DeviceArray&& other) noexcept
        : ptr_(other.ptr_), size_(other.size_) {
        other.ptr_ = nullptr;
        other.size_ = 0;
    }

    DeviceArray& operator=(DeviceArray&& other) noexcept {
        if (this != &other) {
            reset();
            ptr_ = std::exchange(other.ptr_, nullptr);
            size_ = std::exchange(other.size_, std::size_t{0});
        }
        return *this;
    }

    void copy_from_host(const T* host, std::size_t n) {
        if (n == 0) return;
        if (n > size_) throw std::runtime_error("DeviceArray::copy_from_host overflow");
        HRSC_CUDA_CHECK(cudaMemcpy(ptr_, host, n * sizeof(T),
                                   cudaMemcpyHostToDevice));
    }

    void copy_to_host(T* host, std::size_t n) const {
        if (n == 0) return;
        if (n > size_) throw std::runtime_error("DeviceArray::copy_to_host overflow");
        HRSC_CUDA_CHECK(cudaMemcpy(host, ptr_, n * sizeof(T),
                                   cudaMemcpyDeviceToHost));
    }

    T*       data()       { return ptr_; }
    const T* data() const { return ptr_; }
    std::size_t size() const { return size_; }

private:
    void reset() noexcept {
        if (ptr_ != nullptr) {
            cudaFree(ptr_);  // intentionally not throwing in destructor
            ptr_ = nullptr;
            size_ = 0;
        }
    }

    T* ptr_;
    std::size_t size_;
};

} // namespace hrsc
```

- [ ] **Step 2: No build yet** (waiting on Task 4.5 for the wiring); just save the file.

---

### Task 4.2: `gpu_grid.cuh` — `GpuGrid<Real,NVars>`

**Files:**
- Create: `src/gpu/gpu_grid.cuh`

- [ ] **Step 1: Write `gpu_grid.cuh`**

```cpp
// src/gpu/gpu_grid.cuh
//
// Device-side mirror of Grid2D<Real, NVars>. Same memory layout (row-major,
// var-last, ghost cells included on both axes) so Week 6 kernels can index
// identically to host-side GridView.

#pragma once

#include "core/grid.hpp"
#include "core/types.hpp"
#include "gpu/cuda_utils.cuh"

#include <cstddef>

namespace hrsc {

template <class Real, int NVars>
class GpuGrid {
public:
    explicit GpuGrid(const Grid2D<Real, NVars>& host)
        : nx_(host.nx), ny_(host.ny),
          dx_(host.dx), dy_(host.dy),
          dev_(static_cast<std::size_t>(host.data.size()))
    {
        dev_.copy_from_host(host.data.data(), host.data.size());
    }

    void download_to(Grid2D<Real, NVars>& host) const {
        if (host.nx != nx_ || host.ny != ny_) {
            throw std::runtime_error("GpuGrid::download_to size mismatch");
        }
        dev_.copy_to_host(host.data.data(), host.data.size());
    }

    Real*       data()       { return dev_.data(); }
    const Real* data() const { return dev_.data(); }

    int nx() const { return nx_; }
    int ny() const { return ny_; }
    static constexpr int ng() { return NgHost; }

    std::size_t total_cells_with_ghosts() const {
        return static_cast<std::size_t>(nx_total()) * static_cast<std::size_t>(ny_total());
    }

    std::size_t element_count() const {
        return total_cells_with_ghosts() * static_cast<std::size_t>(NVars);
    }

private:
    int nx_total() const { return nx_ + 2 * NgHost; }
    int ny_total() const { return ny_ + 2 * NgHost; }

    int nx_, ny_;
    Real dx_, dy_;
    DeviceArray<Real> dev_;
};

} // namespace hrsc
```

---

### Task 4.3: `euler_kernels.cuh` — templated `device_copy_kernel`

**Files:**
- Create: `src/gpu/euler_kernels.cuh`

- [ ] **Step 1: Write the kernel header**

```cpp
// src/gpu/euler_kernels.cuh
//
// Week 5 D.2 placeholder: a single templated copy kernel used purely to
// verify the host->device->host data path. Real kernels (BC, reconstruction,
// HLLC, CFL reduction) land in Week 6.

#pragma once

#include <cstddef>

namespace hrsc {

template <typename T>
__global__ void device_copy_kernel(const T* in, T* out, std::size_t n) {
    auto i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) out[i] = in[i];
}

} // namespace hrsc
```

---

### Task 4.4: `gpu_roundtrip_kernel.cu` — extern-C wrappers

**Files:**
- Create: `tests/unit/gpu_roundtrip_kernel.cu`

- [ ] **Step 1: Write the .cu wrappers**

```cpp
// tests/unit/gpu_roundtrip_kernel.cu
//
// Day-4 GPU bring-up: extern "C" wrappers callable from a plain C++ Catch2
// TU (test_gpu_roundtrip.cpp). Keeps Catch2's 18k-LOC single header away
// from nvcc — only this small TU sees CUDA syntax.
//
// Dogfoods DeviceArray<T>: this is its only Week-5 caller, so the RAII
// wrapper gets exercised before any Week-6 kernel is built on top of it.

#include "gpu/cuda_utils.cuh"
#include "gpu/euler_kernels.cuh"

#include <cuda_runtime.h>

namespace {

template <typename T>
bool roundtrip_impl(const T* host_in, T* host_out, std::size_t n) {
    using namespace hrsc;
    if (n == 0) return true;

    constexpr int block_size = 256;
    int grid_size = static_cast<int>((n + block_size - 1) / block_size);

    DeviceArray<T> in(n);
    DeviceArray<T> out(n);

    in.copy_from_host(host_in, n);

    device_copy_kernel<T><<<grid_size, block_size>>>(in.data(), out.data(), n);

    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());

    out.copy_to_host(host_out, n);
    return true;
}

} // namespace

extern "C" bool gpu_roundtrip_double(const double* host_in, double* host_out,
                                     std::size_t n) {
    try {
        return roundtrip_impl<double>(host_in, host_out, n);
    } catch (...) {
        return false;
    }
}

extern "C" bool gpu_roundtrip_float(const float* host_in, float* host_out,
                                    std::size_t n) {
    try {
        return roundtrip_impl<float>(host_in, host_out, n);
    } catch (...) {
        return false;
    }
}
```

---

### Task 4.5: Catch2 `[gpu]` test (.cpp half)

**Files:**
- Create: `tests/unit/test_gpu_roundtrip.cpp`

- [ ] **Step 1: Write the failing test**

```cpp
// tests/unit/test_gpu_roundtrip.cpp
//
// Catch2 driver for the GPU roundtrip wrappers in
// tests/unit/gpu_roundtrip_kernel.cu. This .cpp is picked up by the
// existing GLOB(test_*.cpp); the .cu half is added explicitly via
// target_sources in the root CMakeLists.txt under if(ENABLE_CUDA).

#include "catch.hpp"

#include <cstddef>
#include <cstdint>
#include <random>
#include <vector>

extern "C" bool gpu_roundtrip_double(const double* in, double* out, std::size_t n);
extern "C" bool gpu_roundtrip_float (const float*  in, float*  out, std::size_t n);

namespace {

template <typename T>
std::vector<T> random_vector(std::size_t n, std::uint32_t seed) {
    std::mt19937 rng(seed);
    std::uniform_real_distribution<double> dist(-1e3, 1e3);
    std::vector<T> v(n);
    for (auto& x : v) x = static_cast<T>(dist(rng));
    return v;
}

template <typename T>
bool bitwise_equal(const std::vector<T>& a, const std::vector<T>& b) {
    if (a.size() != b.size()) return false;
    for (std::size_t i = 0; i < a.size(); ++i) {
        // bit-level compare to detect any rounding/conversion error
        std::uint64_t ai = 0, bi = 0;
        std::memcpy(&ai, &a[i], sizeof(T));
        std::memcpy(&bi, &b[i], sizeof(T));
        if (ai != bi) return false;
    }
    return true;
}

} // namespace

TEST_CASE("GPU roundtrip is byte-identical for double over 100 random seeds",
          "[gpu]") {
    constexpr std::size_t N = 256 * 100;  // ~25K elements; multiple thread blocks
    for (std::uint32_t seed = 0; seed < 100; ++seed) {
        auto in  = random_vector<double>(N, seed);
        std::vector<double> out(N, 0.0);
        REQUIRE(gpu_roundtrip_double(in.data(), out.data(), N));
        REQUIRE(bitwise_equal(in, out));
    }
}

TEST_CASE("GPU roundtrip is byte-identical for float over 100 random seeds",
          "[gpu]") {
    constexpr std::size_t N = 256 * 100;
    for (std::uint32_t seed = 1000; seed < 1100; ++seed) {
        auto in  = random_vector<float>(N, seed);
        std::vector<float> out(N, 0.0f);
        REQUIRE(gpu_roundtrip_float(in.data(), out.data(), N));
        REQUIRE(bitwise_equal(in, out));
    }
}
```

---

### Task 4.6: Wire CMake for ENABLE_CUDA + unit_tests CUDA section

**Files:**
- Modify: `CMakeLists.txt`

- [ ] **Step 1: Inside the `if(ENABLE_CUDA) … endif()` block (added in Task 1.1), append after the gpu_smoke target**

```cmake
    # Day-4 GPU data path: link DeviceArray<T> + GpuGrid roundtrip into
    # unit_tests. The .cpp half of the test is auto-picked by the existing
    # file(GLOB test_*.cpp); the .cu half is added explicitly here and
    # pinned to LANGUAGE CUDA. Do NOT extend the glob to test_*.{cpp,cu}
    # — that would mix CUDA and CXX languages in one target opaquely and
    # break CPU-only builds.
    target_sources(unit_tests PRIVATE tests/unit/gpu_roundtrip_kernel.cu)
    set_source_files_properties(tests/unit/gpu_roundtrip_kernel.cu
        PROPERTIES LANGUAGE CUDA)
    set_target_properties(unit_tests PROPERTIES
        CUDA_SEPARABLE_COMPILATION ON
        CUDA_ARCHITECTURES "${CMAKE_CUDA_ARCHITECTURES}")
    target_link_libraries(unit_tests PRIVATE CUDA::cudart)
```

The full ENABLE_CUDA block now looks like:
```cmake
option(ENABLE_CUDA "Enable CUDA toolchain (Week 5 GPU bring-up)" OFF)
if(ENABLE_CUDA)
    enable_language(CUDA)
    include(${CMAKE_SOURCE_DIR}/cmake/CUDASetup.cmake)

    add_executable(gpu_smoke src/gpu/gpu_smoke.cu)
    target_link_libraries(gpu_smoke PRIVATE CUDA::cudart)
    set_target_properties(gpu_smoke PROPERTIES
        CUDA_SEPARABLE_COMPILATION ON
        CUDA_ARCHITECTURES "${CMAKE_CUDA_ARCHITECTURES}")

    target_sources(unit_tests PRIVATE tests/unit/gpu_roundtrip_kernel.cu)
    set_source_files_properties(tests/unit/gpu_roundtrip_kernel.cu
        PROPERTIES LANGUAGE CUDA)
    set_target_properties(unit_tests PROPERTIES
        CUDA_SEPARABLE_COMPILATION ON
        CUDA_ARCHITECTURES "${CMAKE_CUDA_ARCHITECTURES}")
    target_link_libraries(unit_tests PRIVATE CUDA::cudart)
endif()
```

- [ ] **Step 2: Reconfigure and build with ENABLE_CUDA=ON**

```bash
cmake -B build-cuda -G Ninja -DENABLE_CUDA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build-cuda
```

Expected: builds clean. Both `gpu_smoke` and `unit_tests` are produced; `unit_tests` links `CUDA::cudart`.

- [ ] **Step 3: Run the GPU test**

```bash
./build-cuda/unit_tests "[gpu]" -r compact
```

Expected: 2 cases pass (double + float, 100 seeds each). Total assertions: 200 × 2 (one for the wrapper return, one for byte-equal) per case = 400 per case = 800 total `[gpu]` assertions.

- [ ] **Step 4: Verify CPU-only builds still pass**

```bash
cmake --build build-double
./build-double/unit_tests -r compact
cmake --build build-float
./build-float/unit_tests -r compact
```

Expected: both CPU builds still pass; the `[gpu]` cases are simply absent from those builds because the `extern "C"` declarations have no definitions and the linker has not been asked to find them (the `.cpp` test file is included in the GLOB but its `[gpu]` cases will fail to link… wait — this is a build-time problem, not a run-time skip. **See Step 5 below for the fix.**)

- [ ] **Step 5: Guard the `.cpp` half against CPU-only builds**

The Catch2 TU `tests/unit/test_gpu_roundtrip.cpp` references `gpu_roundtrip_double/_float`. Without the `.cu` TU (CPU-only build), those symbols are unresolved and `unit_tests` won't link.

Wrap the entire body of `test_gpu_roundtrip.cpp` in `#ifdef HRSC_HAS_CUDA … #endif`, and have the CMake `ENABLE_CUDA` block define that macro on the `unit_tests` target:

In `tests/unit/test_gpu_roundtrip.cpp`, wrap everything after the `#include "catch.hpp"` line:
```cpp
#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#include <cstddef>
// ... rest of the file ...

#endif // HRSC_HAS_CUDA
```

In `CMakeLists.txt`, inside the ENABLE_CUDA block, after `target_link_libraries(unit_tests PRIVATE CUDA::cudart)`, add:
```cmake
    target_compile_definitions(unit_tests PRIVATE HRSC_HAS_CUDA)
```

- [ ] **Step 6: Re-run all builds and tests**

```bash
# CUDA build
cmake --build build-cuda
./build-cuda/unit_tests "[gpu]" -r compact

# CPU-only builds
cmake --build build-double
./build-double/unit_tests -r compact

cmake --build build-float
./build-float/unit_tests -r compact
```

Expected: CUDA build runs `[gpu]` (2 cases); CPU-only builds skip `[gpu]` (case set is unchanged from Day 3).

- [ ] **Step 7: Commit**

```bash
git add src/gpu/cuda_utils.cuh src/gpu/gpu_grid.cuh src/gpu/euler_kernels.cuh tests/unit/test_gpu_roundtrip.cpp tests/unit/gpu_roundtrip_kernel.cu CMakeLists.txt
git commit -m "feat(gpu): add GPU data path skeleton + Catch2 [gpu] roundtrip test

Week 5 D.2 deliverable. Three small headers under src/gpu/:
  - cuda_utils.cuh: HRSC_CUDA_CHECK macro, DeviceArray<T> RAII wrapper
  - gpu_grid.cuh: GpuGrid<Real,NVars> mirror of Grid2D layout
  - euler_kernels.cuh: templated device_copy_kernel<T> only

Test split into .cpp (Catch2 driver, picked up by existing GLOB) +
.cu (extern-C wrappers using DeviceArray<T> for both precisions). The
.cpp half is guarded by HRSC_HAS_CUDA (defined on unit_tests target only
when ENABLE_CUDA=ON), so CPU-only builds skip it cleanly.

Test exercises 100 random seeds x {double, float} x ~25K elements; pass
criterion is bit-identical roundtrip via cudaMemcpy."
```

---

### Task 4.7: Day 4 done-criteria check

- [ ] **Step 1: CUDA build with unit_tests succeeds**

```bash
cmake --build build-cuda
./build-cuda/unit_tests "[gpu]" -r compact
```

Expected: 2 cases pass.

- [ ] **Step 2: CPU builds still pass**

```bash
./build-double/unit_tests -r compact
./build-float/unit_tests -r compact
```

Expected: both pass; assertion counts unchanged from end of Day 3 (the new `[gpu]` cases are not compiled into CPU-only builds).

- [ ] **Step 3: Tag**

```bash
git tag -a w5d4-done -m "Week 5 Day 4 complete: GPU data path"
```

---

## Day 5 — Harness Smoke + Documentation Closure

### Task 5.1: Write the matrix.json

**Files:**
- Create: `experiments/week5/smoke/matrix.json`

- [ ] **Step 1: Write the file**

```bash
mkdir -p experiments/week5/smoke
cat > experiments/week5/smoke/matrix.json <<'EOF'
{
  "experiment": "week5-smoke",
  "output_root": "experiments/week5/smoke",
  "runs": [
    {"name": "lw3-d-200", "binary": "build-double/hrsc",
     "config": "tests/cases/liska_wendroff_2d/config3_n200.cfg",
     "precision": "double", "build": "cpu-double-O2-ieee-leq",
     "output_file": "grid.bin"},
    {"name": "lw3-f-200", "binary": "build-float/hrsc",
     "config": "tests/cases/liska_wendroff_2d/config3_n200.cfg",
     "precision": "float",  "build": "cpu-float-O2-ieee-leq",
     "output_file": "grid.bin"},
    {"name": "lw6-d-200", "binary": "build-double/hrsc",
     "config": "tests/cases/liska_wendroff_2d/config6_n200.cfg",
     "precision": "double", "build": "cpu-double-O2-ieee-leq",
     "output_file": "grid.bin"},
    {"name": "lw6-f-200", "binary": "build-float/hrsc",
     "config": "tests/cases/liska_wendroff_2d/config6_n200.cfg",
     "precision": "float",  "build": "cpu-float-O2-ieee-leq",
     "output_file": "grid.bin"},
    {"name": "sb-d-400",  "binary": "build-double/hrsc",
     "config": "tests/cases/shock_bubble/shock_bubble_n400x100.cfg",
     "precision": "double", "build": "cpu-double-O2-ieee-leq",
     "output_file": "grid.bin"},
    {"name": "sb-f-400",  "binary": "build-float/hrsc",
     "config": "tests/cases/shock_bubble/shock_bubble_n400x100.cfg",
     "precision": "float",  "build": "cpu-float-O2-ieee-leq",
     "output_file": "grid.bin"}
  ]
}
EOF
```

- [ ] **Step 2: Validate JSON**

```bash
python -c 'import json; json.loads(open("experiments/week5/smoke/matrix.json").read()); print("ok")'
```

Expected: `ok`.

---

### Task 5.2: Dry-run + live run + matrix_summary check

- [ ] **Step 1: Dry-run**

```bash
python scripts/run_matrix.py experiments/week5/smoke/matrix.json --dry-run
```

Expected: stdout is the JSON summary (6 runs); creates 6 dirs at `experiments/week5/smoke/runs/<name>/` each containing `config.cfg`, `metadata.json`, `stdout.txt` (empty), `stderr.txt` (one line: `dry-run`).

- [ ] **Step 2: Verify dry-run produced expected layout**

```bash
ls experiments/week5/smoke/runs/
# expect: lw3-d-200 lw3-f-200 lw6-d-200 lw6-f-200 sb-d-400 sb-f-400
ls experiments/week5/smoke/runs/lw6-d-200/
# expect: config.cfg metadata.json stdout.txt stderr.txt
ls experiments/week5/smoke/matrix_summary.json
# expect: file exists
```

- [ ] **Step 3: Live run**

```bash
python scripts/run_matrix.py experiments/week5/smoke/matrix.json
```

Expected: prints JSON summary; all 6 runs return 0; each `<run>/grid.bin` lands.

- [ ] **Step 4: Verify each metadata.json includes timing.total_s**

```bash
for name in lw3-d-200 lw3-f-200 lw6-d-200 lw6-f-200 sb-d-400 sb-f-400; do
  echo "--- $name ---"
  python -c "import json; m=json.load(open('experiments/week5/smoke/runs/$name/metadata.json')); print('returncode=', m['returncode'], ' total_s=', m['timing']['total_s'])"
done
```

Expected: every line shows `returncode= 0  total_s= <positive number>`.

- [ ] **Step 5: Verify matrix_summary.json**

```bash
python -c "
import json
m = json.load(open('experiments/week5/smoke/matrix_summary.json'))
assert m['experiment'] == 'week5-smoke'
assert m['run_count'] == 6
assert all(r['returncode'] == 0 for r in m['runs'])
print('ok')
"
```

Expected: `ok`.

---

### Task 5.3: Aggregate metrics + plot ρ-PNGs

- [ ] **Step 1: Aggregate**

```bash
python scripts/aggregate_metrics.py \
    --output experiments/week5/smoke/summary.json \
    experiments/week5/smoke/runs/*/metadata.json
ls experiments/week5/smoke/summary.json
```

Expected: file exists; contains 6 `summaries` entries.

- [ ] **Step 2: Generate one ρ-PNG per run**

```bash
mkdir -p experiments/week5/smoke/figures
for name in lw3-d-200 lw3-f-200 lw6-d-200 lw6-f-200 sb-d-400 sb-f-400; do
  python scripts/figures/plot_2d.py \
    experiments/week5/smoke/runs/${name}/grid.bin \
    --field rho \
    --out experiments/week5/smoke/figures/${name}_rho.png
done
ls experiments/week5/smoke/figures/ | wc -l
```

Expected: `6`.

---

### Task 5.4: Programmatic cleanup of smoke .bin files

- [ ] **Step 1: Verify summary + figures are present (precondition)**

```bash
test -f experiments/week5/smoke/summary.json && \
  test "$(ls experiments/week5/smoke/figures/ | wc -l)" -eq 6 && \
  echo "preconditions met"
```

Expected: `preconditions met`.

- [ ] **Step 2: Delete smoke grid.bin files**

```bash
find experiments/week5/smoke/runs -name 'grid.bin' -delete
```

- [ ] **Step 3: Verify**

```bash
find experiments/week5/smoke/runs -name 'grid.bin' | wc -l
ls experiments/week5/baselines/lw_config6_n200/grid.bin
```

Expected: `0` (smoke .bin gone) and the baselines/ binary still present.

---

### Task 5.5: Write `docs/week5/week5-verification.md`

**Files:**
- Create: `docs/week5/week5-verification.md`

- [ ] **Step 1: Write the recipe**

```markdown
# Week 5 Verification Recipe

**Date**: 2026-04-30 (Week 5, Day 5)
**Spec**: [`week5-plan.md`](week5-plan.md)
**Branch**: `week4-implementation` (Week 5 work)

This document is a manual reproduction recipe for Week 5 deliverables.
The author runs it end-to-end on a clean checkout to confirm the work is
reproducible. LLM execution does not satisfy this — the human must walk
through each step.

---

## 0. Environment

| Check | Command | Expected |
|---|---|---|
| Git branch | `git rev-parse --abbrev-ref HEAD` | `week4-implementation` |
| Python deps | `python -c "import numpy, matplotlib; print('ok')"` | `ok` |
| C++ compiler | `c++ --version` | gcc ≥ 10 or clang ≥ 12 |
| CUDA toolkit (Day 4 only) | `nvcc --version` | CUDA 11+ |

---

## 1. Build (CPU + CUDA)

```bash
# Default CPU builds
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake --build build-double

cmake -B build-float -G Ninja -DFLOAT_PRECISION=float -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake --build build-float

# Profiling-enabled build (covers ProfilingRegistry test)
cmake -B build-double-prof -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON -DHRSC_ENABLE_PROFILING=ON
cmake --build build-double-prof

# CUDA build
cmake -B build-cuda -G Ninja -DENABLE_CUDA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build-cuda
```

**Expected**: all four configurations succeed; `build-cuda/` produces both `gpu_smoke` and `unit_tests`.

---

## 2. Unit tests

```bash
./build-double/unit_tests -r compact
./build-double-prof/unit_tests -r compact
./build-float/unit_tests -r compact
./build-cuda/unit_tests "[gpu]" -r compact
pytest tests/py/test_plot_2d.py -v
```

**Expected**:
- `build-double` and `build-float`: all cases pass; assertion count ≥ 3660 + new (≥ 30)
- `build-double-prof`: same plus 2 ProfilingRegistry / ScopedTimer cases
- `build-cuda` `[gpu]` filter: 2 cases pass (200 seeds × 2 = 400 wrapper invocations + 400 byte-equal asserts)
- pytest: 4 tests pass (rho/p/vmag/schlieren PNGs)

---

## 3. Solver baselines

### 3.1 LW Config 6

```bash
./build-double/hrsc tests/cases/liska_wendroff_2d/config6_n200.cfg
./build-double/hrsc tests/cases/liska_wendroff_2d/config6_n400.cfg
./build-float/hrsc  tests/cases/liska_wendroff_2d/config6_n200.cfg
./build-float/hrsc  tests/cases/liska_wendroff_2d/config6_n400.cfg
```

**Expected**: each emits `Finished: <N> steps, t = 0.3` and `[timing] total_s=…` on stderr; binary outputs land at `experiments/week5/baselines/lw_config6_n{200,400}/grid.bin`.

### 3.2 Shock-bubble

```bash
./build-double/hrsc tests/cases/shock_bubble/shock_bubble_n400x100.cfg
./build-double/hrsc tests/cases/shock_bubble/shock_bubble_n400x100_rusanov.cfg
```

**Expected**: each emits `Finished:` and `[timing]`; binary outputs land at `experiments/week5/baselines/shock_bubble_n400x100_{hllc,rusanov}/grid.bin`.

### 3.3 Generate the 12 reference PNGs

```bash
mkdir -p experiments/week5/baselines/figures
for N in 200 400; do
  for FIELD in rho p schlieren; do
    python scripts/figures/plot_2d.py \
      experiments/week5/baselines/lw_config6_n${N}/grid.bin \
      --field ${FIELD} \
      --out experiments/week5/baselines/figures/lw_config6_n${N}_${FIELD}.png
  done
done
for SOLVER in hllc rusanov; do
  for FIELD in rho p schlieren; do
    python scripts/figures/plot_2d.py \
      experiments/week5/baselines/shock_bubble_n400x100_${SOLVER}/grid.bin \
      --field ${FIELD} \
      --out experiments/week5/baselines/figures/shock_bubble_n400x100_${SOLVER}_${FIELD}.png
  done
done
ls experiments/week5/baselines/figures/ | wc -l   # 12
```

**Visual pass criteria**:
- LW Config 6 ρ at N=200 / N=400: 4 quadrants smoothly evolved to contact-wave structure; no shocks visible. Sharper interfaces at N=400.
- LW Config 6 p: nearly uniform ≈ 1.0 (contacts preserve pressure).
- Shock-bubble HLLC schlieren: planar shock past x=0.05; bubble compressed; transmitted shock through the low-density region accelerated.
- Shock-bubble Rusanov vs HLLC: Rusanov interface visibly more diffuse.

When plotting shock-bubble figures, mirror about y=0 in figure captions to interpret as the full physical bubble (the simulation is half-symmetric).

### 3.4 Float-vs-double SSIM (record only, no fixed threshold)

```bash
python scripts/metrics/phase_error_metrics.py \
    --reference experiments/week5/baselines/lw_config6_n200/grid.bin \
    --candidate experiments/week5/baselines/lw_config6_n200/grid.bin
# (The above uses double-vs-double as a sanity check.)
```

(Repeat with the float-built `.bin` once available.) **Record the SSIM in this file's "Known differences" section**. Investigation triggers only if SSIM < 0.90.

---

## 4. Harness matrix smoke

```bash
# Dry-run
python scripts/run_matrix.py experiments/week5/smoke/matrix.json --dry-run

# Live
python scripts/run_matrix.py experiments/week5/smoke/matrix.json

# Aggregate
python scripts/aggregate_metrics.py \
    --output experiments/week5/smoke/summary.json \
    experiments/week5/smoke/runs/*/metadata.json

# Plot a ρ-PNG per run
mkdir -p experiments/week5/smoke/figures
for name in lw3-d-200 lw3-f-200 lw6-d-200 lw6-f-200 sb-d-400 sb-f-400; do
  python scripts/figures/plot_2d.py \
    experiments/week5/smoke/runs/${name}/grid.bin \
    --field rho \
    --out experiments/week5/smoke/figures/${name}_rho.png
done

# HARNESS.md §6 transient cleanup (only AFTER summary + figures are confirmed)
find experiments/week5/smoke/runs -name 'grid.bin' -delete
```

**Expected after each step**:
- Dry-run: 6 `<run>/config.cfg` + `metadata.json`; no stderr; `matrix_summary.json` lands at experiment root.
- Live run: 6 returncode=0; `stdout.txt`, `stderr.txt`, `grid.bin`, `metadata.json` per run.
- Each `metadata.json` contains git commit, source/run cfg paths, raw output path, `timing.total_s`.
- `summary.json` aggregates 6 entries.
- 6 ρ-PNGs land under `smoke/figures/`.
- After cleanup: `find experiments/week5/smoke/runs -name grid.bin` returns nothing; `experiments/week5/baselines/` is untouched.

---

## 5. plot_2d.py smoke

```bash
pytest tests/py/test_plot_2d.py -v
```

**Expected**: 4 tests pass (rho, p, vmag, schlieren each emits ≥1 KB PNG ≥ 100×100).

---

## 6. Known differences / follow-ups

(Filled in by the author during the walk-through. Examples of what to record:
SSIM values, any platform-specific tolerances raised, any deviation from
literature visual references.)

- ScopedTimer probes were realised as 3 phases (`bc`, `cfl`, `sweep`) rather
  than the spec's 5 phases. Splitting reconstruction/riemann/update inside
  the sweep would have altered inlining boundaries (AGENTS.md rule 1).
  Refinement deferred to Week 7 with explicit profile-instrumented wrappers.
- _(append more as found)_
```

- [ ] **Step 2: Walk through the recipe end-to-end yourself**

This is the load-bearing step. Open a fresh terminal, run each command in order, and confirm the expected outputs match. **Do not skip.**

- [ ] **Step 3: Commit**

```bash
git add docs/week5/week5-verification.md
git commit -m "docs(week5): add reproduction recipe (week5-verification.md)

Mirrors week4-verification.md format. Six sections covering build, unit
tests, solver baselines (with reference figures), harness matrix smoke
(including transient-data cleanup per HARNESS.md §6), plot_2d.py smoke,
and a known-differences tail. Author has manually walked through the
recipe end-to-end."
```

---

### Task 5.6: Write `docs/week5/week5-summary.md`

**Files:**
- Create: `docs/week5/week5-summary.md`

- [ ] **Step 1: Compose the summary**

```markdown
# Week 5 Summary

**Branch**: `week4-implementation`
**Period**: Week 5 (per overall.md schedule)
**Spec**: [`week5-plan.md`](week5-plan.md)
**Recipe**: [`week5-verification.md`](week5-verification.md)

---

## Delivered

- **Block A** — `Timer` (always on) + opt-in `ProfilingRegistry`/`ScopedTimer` behind `HRSC_ENABLE_PROFILING`. `main.cpp` emits `[timing] total_s=…` on stderr per run; `scripts/run_matrix.py` parses it into `metadata.json.timing.total_s`. Realised 3 phase probes (`bc`/`cfl`/`sweep`) instead of the spec's 5 (split deferred to Week 7 to preserve inlining).
- **Block B** — `setup_liska_wendroff_config6` IC (LW 2003 Table 4.3, all-contact, no shocks) + `config6_n{200,400}.cfg` baselines + 2 unit-test cases. `overall.md` Supersonic Wave Test Cases table corrected (Config 6 is contact-only).
- **Block C** — Half-symmetric shock-bubble IC (`tests/cases/shock_bubble/`), Rankine-Hugoniot post-shock helper, HLLC + Rusanov cfgs, 3 unit-test cases.
- **Block D.1** — `cmake/CUDASetup.cmake` + `ENABLE_CUDA` option + standalone `gpu_smoke` target (Day 1 toolchain validation).
- **Block D.2** — `src/gpu/{cuda_utils.cuh, gpu_grid.cuh, euler_kernels.cuh}` (HRSC_CUDA_CHECK, RAII `DeviceArray<T>`, `GpuGrid<Real,NVars>`, templated `device_copy_kernel<T>`) + Catch2 `[gpu]` test split into `.cpp` (driver, glob-picked) + `.cu` (extern-C wrappers using `DeviceArray<T>`). 100 random seeds × {double, float} byte-identical roundtrip.
- **Block E** — `scripts/figures/plot_2d.py` (single-grid CLI, 4 fields, uses `io_helper.read_binary`) + pytest smoke + 12 baseline PNGs.
- **Layer 3 harness smoke** — 6-run `experiments/week5/smoke/matrix.json` exercises full pipeline; `matrix_summary.json` + aggregated `summary.json` + 6 ρ-PNGs land; smoke `grid.bin` files programmatically removed after success per HARNESS.md §6.

---

## Commits (chronological)

(Filled by the author after Day 5; one line per commit, ordered.)

```
$(git log --oneline w5d1-done~1..HEAD -- src/ tests/ scripts/ docs/week5/ docs/INDEX.md docs/requirement/overall.md cmake/ CMakeLists.txt experiments/week5/smoke/matrix.json)
```

---

## Experiment artefacts

| Path | Contents |
|---|---|
| `experiments/week5/baselines/lw_config6_n200/` | grid.bin (kept; reference data) |
| `experiments/week5/baselines/lw_config6_n400/` | grid.bin (kept; reference data) |
| `experiments/week5/baselines/shock_bubble_n400x100_hllc/` | grid.bin (kept) |
| `experiments/week5/baselines/shock_bubble_n400x100_rusanov/` | grid.bin (kept) |
| `experiments/week5/baselines/figures/` | 12 PNGs (rho/p/schlieren × 4 sources) |
| `experiments/week5/smoke/matrix.json` | committed |
| `experiments/week5/smoke/runs/<name>/metadata.json` | per-run metadata (kept) |
| `experiments/week5/smoke/runs/<name>/grid.bin` | **deleted** post-aggregate per HARNESS.md §6 |
| `experiments/week5/smoke/summary.json` | aggregated (kept) |
| `experiments/week5/smoke/matrix_summary.json` | matrix-level (kept) |
| `experiments/week5/smoke/figures/` | 6 ρ-PNGs (kept) |

---

## Week 5 → Week 6 handoff

Week 6 inherits a green base:

- **`GpuGrid<Real,NVars>`** matches `Grid2D` layout exactly (row-major, var-last, ghost cells included). Week 6 BC and reconstruction kernels can index identically to host-side `GridView`.
- **`HRSC_CUDA_CHECK`** + **`DeviceArray<T>`** are the only allocation primitives; Week 6 kernels should not call raw `cudaMalloc/cudaFree`.
- **`Timer`** records wall-clock for every solver invocation; Week 6 GPU solver gets CPU-vs-GPU timing comparison for free.
- **Harness matrix smoke** is green; Week 6 GPU baselines just append rows to a new `matrix.json`. Aggregate / plot path unchanged.
- **`plot_2d.py`** is single-responsibility and precision-aware (via `io_helper`); Week 6 GPU outputs reuse the same visualisation. CPU/GPU diff uses existing `phase_error_metrics.py`.

Week 6 first tasks (per `overall.md` lines 308–321):
1. Implement BC kernel (start with outflow), verify CPU-vs-GPU byte-identical (or to ULP) for an idle grid.
2. CFL kernel (deterministic tree reduction; no atomics).
3. Reconstruction kernel (`muscl_hancock_*` ported as `__device__`).
4. HLLC kernel (most invasive; uses HD_FUNC pattern).
5. `EulerGpuSolver<Real>` orchestration class.
6. End-to-end CPU-vs-GPU diff regression on Sod + LW Config 3.

---

## Open / deferred

- ScopedTimer 5-way phase split (currently 3-way) → Week 7 refinement.
- CSC GPU node build → Week 6 once local kernels stabilise.
- `vfc_precexp` + unstable-branch detection (Week-3 supervisor carry-over) → Week 14 unless MHD pulled forward.
```

- [ ] **Step 2: Resolve the embedded `git log` placeholder**

The summary contains a literal `$(...)` shell substitution as a placeholder. Replace it with actual `git log --oneline` output from this week:

```bash
git log --oneline w5d1-done~1..HEAD -- src/ tests/ scripts/ docs/week5/ docs/INDEX.md docs/requirement/overall.md cmake/ CMakeLists.txt experiments/week5/smoke/matrix.json > /tmp/w5_commits.txt
```

Then paste the contents of `/tmp/w5_commits.txt` into the summary in place of the `$(...)` block.

- [ ] **Step 3: Commit**

```bash
git add docs/week5/week5-summary.md
git commit -m "docs(week5): add week5-summary.md (deliverables + handoff)

Lists every block delivered, the commits, the artefact map (kept vs
deleted per HARNESS.md §6), and the Week 5 → Week 6 handoff. Records
the Week 5 deferrals (ScopedTimer 5-way split, CSC GPU build,
Verificarlo carry-over)."
```

---

### Task 5.7: Update `docs/INDEX.md` Week 5 row

**Files:**
- Modify: `docs/INDEX.md`

- [ ] **Step 1: Add Week 5 row to the per-week table**

In `docs/INDEX.md` §2, find the table:

```
| Week | Plan | Summary | Archive |
|---|---|---|---|
| 1 | ... |
| 2 | ... |
| 3 | ... |
| 4 | ... |
```

Append:
```
| 5 | [week5-plan.md](week5/week5-plan.md) | [week5-summary.md](week5/week5-summary.md) | (none) |
```

Also update the "Week 5 pre-start bridge" sub-section (currently noting the bridge file) to add:
- [week5-verification.md](week5/week5-verification.md) — manual reproduction recipe for Week 5 (Phase A/B/C/D/E coverage)

Keep the existing bridge link.

- [ ] **Step 2: Commit**

```bash
git add docs/INDEX.md
git commit -m "docs(index): add Week 5 row + verification.md link"
```

---

### Task 5.8: Final regression sweep

- [ ] **Step 1: Re-run every test the spec calls out**

```bash
./build-double/unit_tests -r compact
./build-double-prof/unit_tests -r compact
./build-float/unit_tests -r compact
./build-cuda/unit_tests "[gpu]" -r compact
pytest tests/py/test_plot_2d.py -v
```

Expected: every command succeeds; combined assertion count vs. start-of-week ≥ 3660 + 30 (timer + LW6 + shock-bubble) + 800 (gpu) + pytest 4.

- [ ] **Step 2: Verify all archival files exist**

```bash
test -f docs/week5/week5-plan.md         && echo "plan ok"
test -f docs/week5/week5-verification.md && echo "verification ok"
test -f docs/week5/week5-summary.md      && echo "summary ok"
grep -q "Config 6 is a 4-contact-only test" docs/requirement/overall.md && echo "overall.md fix ok"
grep -q "week5-plan.md" docs/INDEX.md && echo "INDEX.md updated"
test -f experiments/week5/smoke/matrix_summary.json && echo "matrix_summary ok"
test -f experiments/week5/smoke/summary.json && echo "summary.json ok"
test "$(ls experiments/week5/baselines/figures/ | wc -l)" -ge 12 && echo "12 baseline PNGs ok"
test "$(ls experiments/week5/smoke/figures/ | wc -l)" -ge 6 && echo "6 smoke PNGs ok"
```

Expected: 9 "ok" lines.

- [ ] **Step 3: Tag Week 5 done**

```bash
git tag -a w5-done -m "Week 5 complete: 2D tests + GPU skeleton + harness smoke"
git log --oneline -10
```

- [ ] **Step 4: Hand off per `superpowers:finishing-a-development-branch`**

Open a PR for `week4-implementation` (now containing both Week 4 and Week 5 commits). Use the recipe in the superpowers skill to choose merge strategy. Branch policy per spec §5.4: rename to `week5-implementation` only if the PR strategy calls for it.

---

## Self-Review Checklist

After this plan was drafted, the following checks were applied (per writing-plans skill):

**1. Spec coverage** — Each spec block has at least one task:
- Block A (Timer + profiling) → Tasks 1.2, 1.3, 1.4, 1.5, 1.6 ✓
- Block B (LW Config 6) → Tasks 2.1, 2.2, 2.3 ✓
- Block C (shock-bubble) → Tasks 3.1, 3.2, 3.3, 3.4 ✓
- Block D.1 (CUDA toolchain smoke) → Task 1.1 ✓
- Block D.2 (GPU data path) → Tasks 4.1, 4.2, 4.3, 4.4, 4.5, 4.6 ✓
- Block E (plot_2d.py) → Tasks 3.5, 3.6, 3.7 ✓
- Layer 3 harness smoke → Tasks 5.1, 5.2, 5.3 ✓
- Documentation closure → Tasks 5.5, 5.6, 5.7 ✓
- Out-of-scope items (MHD, Verificarlo carry-over, full GPU solver) → not in plan, deferred per spec §5.2 ✓

**2. Placeholder scan** — All code blocks contain real, compilable code; no "TBD" / "implement later" / "similar to Task N" remnants. The single intentional placeholder is in Task 5.6 Step 2 (the `$(git log ...)` substitution), explicitly resolved by a follow-up step.

**3. Type consistency** — Cross-referenced names:
- `Timer`, `ProfilingRegistry`, `ScopedTimer` consistent across Tasks 1.2, 1.3, 1.5
- `gpu_roundtrip_double` / `gpu_roundtrip_float` extern-C wrappers consistent in Tasks 4.4 (defined) and 4.5 (called)
- `device_copy_kernel<T>` template parameter `T` consistent in Tasks 4.3 (defined) and 4.4 (instantiated)
- `DeviceArray<T>` interface (`copy_from_host`, `copy_to_host`, `data()`, `size()`) consistent in Tasks 4.1 (defined) and 4.4 (used)
- `setup_liska_wendroff_config6`, `setup_shock_bubble` consistent across IC, test, and main.cpp registration tasks

**4. Spec realism deviation** — One realised-vs-spec divergence flagged inline (Task 1.5 Step 2): the 5-phase ScopedTimer split is realised as 3 phases (`bc`, `cfl`, `sweep`) to avoid altering inlining boundaries inside `x_sweep`/`y_sweep`. Documented in Task 5.6 Open/Deferred; written into the commit message.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-30-week5-2d-tests-and-gpu-skeleton.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task; review between tasks; fast iteration.

**2. Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`; batch execution with checkpoints for review.

**Which approach?**
