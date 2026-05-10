# Week 6 Implementation Plan — GPU Euler Solver + CSC Migration

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land a CUDA Euler GPU solver (BC / CFL / MUSCL / Hancock / Rusanov / HLLC / update / orchestration), wire it through `main.cpp` cfg dispatch, prove CPU↔GPU same-precision agreement under strict-IEEE flags, and migrate the resulting smoke matrix to the CSC GPU partition — all by 2026-05-10 (Sun) EOD.

**Architecture:** `EulerGpuSolver<Real>` mirrors `EulerSolver<Real>`; `main.cpp` selects via `std::variant` (no vtable, no host/device boundary). Kernels reuse the host CPU functions in `src/euler/*.hpp` (already `__host__ __device__`-friendly). The inner step loop closes on the device — D2H copies happen only at IO / regression sample / progress boundaries. CFL reduction uses `atomicMin` on bit-reinterpret of positive floats (deterministic). Default stream throughout Week 6.

**Tech stack:** C++17, CUDA (host-side host_device functions reused), CMake ≥ 3.18 (CUDA ≥ 3.24 prefers `native` arch), Catch2, Ninja, OpenMP (CPU baseline), Python (regression report), SLURM (CSC).

**Reference docs:**
- [`docs/week6/archive/week6-design.md`](archive/week6-design.md) — design + decisions (read this first)
- [`docs/week6/archive/week5_to_week6_bridge.md`](archive/week5_to_week6_bridge.md) — what is already in place
- [`docs/HARNESS.md`](../HARNESS.md) — `run_matrix.py` schema
- [`AGENTS.md`](../../AGENTS.md) — solver-numerics + cfg-default invariants

**Branch:** `week4-implementation` (continues from Week 5 per bridge `§header`).

**Conventions used in this plan:**
- `CPU oracle` means the existing `__host__ __device__`-friendly free function in `src/euler/*.hpp`. Port the algebra line-for-line; do not re-derive.
- Verification commands assume PowerShell on Windows host; Bash invocations work in WSL or via `bash -c`.
- All commits go on `week4-implementation`. Push at end of each day.

---

## File layout (locked here, referenced from each task)

### Sources

| Path | Action | Owner task |
|---|---|---|
| `cmake/CompilerFlags.cmake` | extend (new helpers + STRICT_IEEE option) | T4 |
| `cmake/CUDASetup.cmake` | extend (separable compilation) | T4 |
| `CMakeLists.txt` | extend (STRICT_IEEE wire-up + new sources) | T4, T16 |
| `src/main.cpp` | extend (`device` cfg key, variant dispatch) | T1, T17 |
| `src/utils/profiling.hpp` | extend (5-phase split: + `flux`, + `update`) | T9 |
| `src/euler/euler_solver.cpp` | minor (emit `flux` / `update` phase markers) | T9 |
| `src/gpu/euler_kernels.cuh` | new (all kernels declared) | T6, T8, T10, T11, T13, T14, T15, T18 |
| `src/gpu/euler_kernels.cu` | new (kernel definitions + explicit instantiation) | same as above |
| `src/gpu/euler_gpu_solver.hpp` | new (class declaration) | T2, T16 |
| `src/gpu/euler_gpu_solver.cu` | new (orchestration + explicit instantiation) | T2, T16 |
| `tests/cases/liska_wendroff_2d/lw_tests.hpp` | extend (Config 4 / 12 IC) | T19, T22 |
| `tests/cases/liska_wendroff_2d/config4_n{200,400}.cfg` | new | T19 |
| `tests/cases/liska_wendroff_2d/config12_n{200,400}.cfg` | new | T22 |
| `tests/unit/test_dispatch_device_key.cpp` | new (cfg key parsing) | T1 |
| `tests/unit/test_gpu_grid_layout.cpp` | new (3 cases) | T5 |
| `tests/unit/test_gpu_bc.cpp` | new (6 cases) | T6, T7, T8 |
| `tests/unit/test_gpu_cfl.cpp` | new (4 cases) | T10 |
| `tests/unit/test_gpu_reconstruct.cpp` | new (3 cases) | T11 |
| `tests/unit/test_gpu_hancock.cpp` | new (3 cases) | T12 |
| `tests/unit/test_gpu_update.cpp` | new (3 cases) | T13 |
| `tests/unit/test_gpu_rusanov.cpp` | new (4 cases) | T14 |
| `tests/unit/test_gpu_hllc.cpp` | new (5 cases) | T20 |
| `tests/unit/test_gpu_solver_e2e.cpp` | new (4 cases) | T18 |
| `tests/unit/test_lw_config4.cpp` | new (2 cases) | T19 |
| `tests/unit/test_lw_config12.cpp` | new (2 cases) | T22 |
| `tests/py/test_float_regression_report_device_mode.py` | new | T21 |
| `scripts/build_all.sh` | extend (probes + 4 strict variants) | T4 |
| `scripts/regression/float_regression_report.py` | extend (`--mode {fp,device}`) | T21 |
| `scripts/cluster/build_gpu_csc.sh` | new | T26 |
| `scripts/cluster/run_gpu_smoke.slurm` | new | T26 |
| `experiments/week6/smoke/matrix.json` | new | T17 |
| `experiments/week6/regression/matrix.json` | new | T23 |
| `experiments/week6/csc_smoke/matrix.json` | new | T26 |

### Docs

| Path | Action | Owner task |
|---|---|---|
| `docs/week6/csc_gpu_environment.md` | new (D1 probe results) | T3 |
| `docs/week6/week6-verification.md` | new (D7 reproduction recipe) | T29 |
| `docs/week6/week6-summary.md` | new (D7 closeout) | T30 |
| `docs/INDEX.md` | edit (Week 6 row → live links) | T30 |

---

## Task index (34 tasks, 7 calendar days)

| Day | Tasks | Theme |
|---|---|---|
| D1 Mon 05-04 | T1–T4 | cfg dispatch, strict-IEEE CMake, build matrix |
| D1 Mon 05-04 | T3 (parallel) | CSC SSH probe |
| D2 Tue 05-05 | T5, T6, T7, T8 | layout safety + BC kernels |
| D3 Wed 05-06 | T9, T10 | Timer 5-phase + CFL kernel |
| D4 Thu 05-07 | T11, T12 | reconstruct + predict |
| D5 Fri 05-08 | T13–T19 | Rusanov, update, orchestration, dispatch wire, GPU timing, e2e smoke, LW Config 4 |
| D6 Sat 05-09 | T20–T23 | HLLC, regression `--mode device`, regression matrix run, LW Config 12 |
| D7 Sun 05-10 | T24–T30 | CSC build / submit / rsync / regression / docs / closeout |

---

## D1 (Mon 2026-05-04) — cfg dispatch + strict-IEEE CMake + CSC probe

### Task 1: `device` cfg key and stub dispatch in `main.cpp`

**Why:** Every later GPU task assumes the cfg path is wired. The default-`cpu` invariant must be byte-for-byte identical to Week 5 (G5 in design) — verified at the end.

**Files:**
- Modify: `src/main.cpp` (parse `device` key; stub `gpu` branch with a friendly error)
- Test: `tests/unit/test_dispatch_device_key.cpp` (new)

- [ ] **Step 1: Write the failing dispatch test**

Create `tests/unit/test_dispatch_device_key.cpp`:

```cpp
#include "catch.hpp"
#include "utils/config.hpp"
#include <stdexcept>

using namespace hrsc;

TEST_CASE("device cfg key defaults to cpu when absent", "[dispatch]") {
    Config cfg;
    REQUIRE(cfg.get_string("device", "cpu") == "cpu");
}

TEST_CASE("device cfg key accepts cpu and gpu", "[dispatch]") {
    Config cfg;
    cfg.set("device", "gpu");
    REQUIRE(cfg.get_string("device", "cpu") == "gpu");
    cfg.set("device", "cpu");
    REQUIRE(cfg.get_string("device", "cpu") == "cpu");
}
```

- [ ] **Step 2: Run, expect FAIL (compile-only — `Config::set` may not exist)**

```bash
cmake --build build-double --target unit_tests
./build-double/unit_tests "[dispatch]" -r compact
```

Expected: compile error or test failure. If `Config` has no `set()` helper, add a one-liner setter (or use the existing parsing path if present); the goal is to verify cfg round-trips this key.

- [ ] **Step 3: In `src/main.cpp`, parse the key and stub the `gpu` branch**

Inside `main()`, after the existing cfg parsing block, add:

```cpp
const std::string device = cfg.get_string("device", "cpu");
if (device != "cpu" && device != "gpu") {
    throw std::runtime_error("Invalid device='" + device + "'; expected 'cpu' or 'gpu'");
}
if (device == "gpu") {
#ifndef HRSC_HAS_CUDA
    throw std::runtime_error("device=gpu requires building with -DENABLE_CUDA=ON");
#else
    // T17 wires this to EulerGpuSolver. For now: bail loudly.
    throw std::runtime_error("device=gpu dispatch not yet implemented (Week 6 D5)");
#endif
}
// device == "cpu" → fall through to existing EulerSolver path (UNCHANGED).
```

- [ ] **Step 4: Run, expect PASS for `[dispatch]`**

```bash
cmake --build build-double --target unit_tests
./build-double/unit_tests "[dispatch]" -r compact
```

Expected: 2 cases / N assertions, all PASS.

- [ ] **Step 5: Run G5 byte-identity regression (proves CPU default unchanged)**

```bash
./build-double/hrsc tests/cases/toro_1d/sod.cfg
# Compute md5 of the produced binary or stdout-table and diff against a
# pre-D1 snapshot. If the cfg writes binary to a fixed path, md5sum it.
md5sum experiments/.../sod_output_or_stdout_capture
```

Expected: hash matches the Week 5 baseline (commit `cda04f3` snapshot — re-record as the "Week 5 reference" in `docs/week6/week6-verification.md` once at D7).

- [ ] **Step 6: Commit**

```bash
git add src/main.cpp tests/unit/test_dispatch_device_key.cpp
git commit -m "feat(week6): parse device cfg key; stub gpu branch with clear error"
```

---

### Task 2: `EulerGpuSolver<Real>` skeleton (declaration + empty .cu instantiation)

**Why:** The orchestration class is referenced by main.cpp variant dispatch (T17). Making it compile in D1 unblocks parallel work later.

**Files:**
- Create: `src/gpu/euler_gpu_solver.hpp`
- Create: `src/gpu/euler_gpu_solver.cu`

- [ ] **Step 1: Write the header skeleton**

Create `src/gpu/euler_gpu_solver.hpp`:

```cpp
// src/gpu/euler_gpu_solver.hpp
//
// EulerGpuSolver<Real>: device-resident analogue of EulerSolver<Real>.
// Same public surface (constructor, step, run, current_time, grid view) so
// std::variant<EulerSolver<Real>, EulerGpuSolver<Real>> can dispatch via
// std::visit. See docs/week6/week6-design.md §3.2 for rationale.
//
// This file declares only. Method bodies and explicit instantiations live
// in euler_gpu_solver.cu.

#pragma once

#ifdef HRSC_HAS_CUDA

#include "core/grid.hpp"
#include "core/types.hpp"
#include "core/boundary.hpp"
#include "euler/euler_solver.hpp"  // FluxScheme enum reuse
#include "gpu/gpu_grid.cuh"

namespace hrsc {

template <typename Real>
class EulerGpuSolver {
public:
    EulerGpuSolver(Grid2D<Real, EulerNVars> grid,
                   Real xmin, Real ymin,
                   Real gamma, Real cfl,
                   TimeReal t_end,
                   FluxScheme flux,
                   BoundaryType bc_x, BoundaryType bc_y);

    // step(dt): advance by exactly one MUSCL-Hancock-Lie step.
    void step(TimeReal dt);

    // run(): time-loop until t_end; returns final wall-clock seconds.
    double run();

    // For IO / regression: D2H copy to host grid; refreshes m_host_grid in place.
    Grid2D<Real, EulerNVars> download_host_grid() const;

    TimeReal current_time() const { return m_time; }
    int      step_count()   const { return m_step; }

private:
    Grid2D<Real, EulerNVars> m_host_grid;   // shape mirror; data D2H-refreshed lazily
    GpuGrid<Real, EulerNVars> m_dev_grid;
    Real         m_xmin, m_ymin;
    Real         m_gamma, m_cfl;
    TimeReal     m_t_end;
    TimeReal     m_time;
    int          m_step;
    FluxScheme   m_flux;
    BoundaryType m_bc_x, m_bc_y;
};

extern template class EulerGpuSolver<float>;
extern template class EulerGpuSolver<double>;

} // namespace hrsc

#endif // HRSC_HAS_CUDA
```

- [ ] **Step 2: Write the empty `.cu` with explicit instantiation**

Create `src/gpu/euler_gpu_solver.cu`:

```cpp
// src/gpu/euler_gpu_solver.cu
//
// Body lives here for two reasons:
// (1) explicit instantiation for {float, double} keeps a single TU paying
//     the kernel-launch boilerplate cost;
// (2) header stays free of <cuda_runtime.h> so non-CUDA TUs that only see
//     the std::variant declaration via main.cpp do not need nvcc.

#include "gpu/euler_gpu_solver.hpp"
#include "gpu/euler_kernels.cuh"

namespace hrsc {

template <typename Real>
EulerGpuSolver<Real>::EulerGpuSolver(
    Grid2D<Real, EulerNVars> grid, Real xmin, Real ymin,
    Real gamma, Real cfl, TimeReal t_end,
    FluxScheme flux, BoundaryType bc_x, BoundaryType bc_y)
    : m_host_grid(std::move(grid)),
      m_dev_grid(m_host_grid),
      m_xmin(xmin), m_ymin(ymin),
      m_gamma(gamma), m_cfl(cfl),
      m_t_end(t_end), m_time(0.0), m_step(0),
      m_flux(flux), m_bc_x(bc_x), m_bc_y(bc_y) {}

template <typename Real>
void EulerGpuSolver<Real>::step(TimeReal /*dt*/) {
    // Wired in T16. Skeleton is empty so the build links.
}

template <typename Real>
double EulerGpuSolver<Real>::run() {
    return 0.0;  // wired in T16
}

template <typename Real>
Grid2D<Real, EulerNVars> EulerGpuSolver<Real>::download_host_grid() const {
    Grid2D<Real, EulerNVars> out = m_host_grid;
    m_dev_grid.download_to(out);
    return out;
}

template class EulerGpuSolver<float>;
template class EulerGpuSolver<double>;

} // namespace hrsc
```

- [ ] **Step 3: Stub `src/gpu/euler_kernels.cuh` so `#include` above resolves**

Create `src/gpu/euler_kernels.cuh`:

```cpp
// src/gpu/euler_kernels.cuh
//
// Forward declarations for Euler GPU kernels and their host-side launchers.
// Each kernel has a typed launcher accepting a GpuGrid + parameters; tests
// call the launcher, never the raw kernel.
//
// Kernels are filled in across D2..D6 (BC, CFL, reconstruct, predict, flux,
// update). The header is intentionally minimal to keep build-time short.

#pragma once

#ifdef HRSC_HAS_CUDA

#include "core/boundary.hpp"   // Axis, BoundaryType
#include "core/grid.hpp"       // EulerNVars
#include "gpu/gpu_grid.cuh"

namespace hrsc {

// (no kernels yet — D2 starts adding them)

} // namespace hrsc

#endif // HRSC_HAS_CUDA
```

- [ ] **Step 4: Wire into CMake (T4 will revisit; this is the minimal hook)**

Edit `CMakeLists.txt`. Inside the existing `if(ENABLE_CUDA) ... endif()` block (after `target_sources(unit_tests PRIVATE tests/unit/gpu_roundtrip_kernel.cu)`), append:

```cmake
    # Week 6: GPU Euler solver bodies + kernels (single TU each).
    target_sources(hrsc_euler PRIVATE
        src/gpu/euler_gpu_solver.cu)
    set_source_files_properties(src/gpu/euler_gpu_solver.cu
        PROPERTIES LANGUAGE CUDA)
    set_target_properties(hrsc_euler PROPERTIES
        CUDA_SEPARABLE_COMPILATION ON
        CUDA_ARCHITECTURES "${CMAKE_CUDA_ARCHITECTURES}")
    target_link_libraries(hrsc_euler PUBLIC CUDA::cudart)
    target_compile_definitions(hrsc_euler PUBLIC HRSC_HAS_CUDA)
```

- [ ] **Step 5: Configure + build a CUDA build dir, expect SUCCESS**

```bash
cmake -B build-cuda-double -G Ninja \
    -DFLOAT_PRECISION=double -DENABLE_CUDA=ON \
    -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake --build build-cuda-double
```

Expected: clean build; `unit_tests` and `hrsc` link successfully.

- [ ] **Step 6: Verify Week 5 `[gpu]` roundtrip still passes**

```bash
./build-cuda-double/unit_tests "[gpu]" -r compact
```

Expected: 2 cases / 400 assertions PASS (Week 5 baseline).

- [ ] **Step 7: Commit**

```bash
git add src/gpu/euler_gpu_solver.hpp src/gpu/euler_gpu_solver.cu \
        src/gpu/euler_kernels.cuh CMakeLists.txt
git commit -m "feat(week6): add EulerGpuSolver skeleton; wire into CUDA build"
```

---

### Task 3: CSC SSH probe → `csc_gpu_environment.md`

**Why:** D7 cannot proceed without CSC partition / `--gres` / `module load` truths. Doing this on D1 surfaces toolchain mismatches before they block the calendar.

**Files:**
- Create: `docs/week6/csc_gpu_environment.md`

- [ ] **Step 1: SSH to CSC and capture probe output**

```bash
ssh csc-login
# On CSC login node:
hostname
module avail cuda  2>&1 | tee /tmp/csc_modules.txt
module load cuda/12.4   # or whichever version is current
nvcc --version
which nvcc
sinfo -o "%P %G %D %t" | grep -i gpu
sinfo --json | python -c "import sys,json; d=json.load(sys.stdin); ..." # or skip
echo "----- gres syntax test -----"
srun --partition=ampere --gres=gpu:1 --time=00:01:00 --pty nvidia-smi
```

(Replace `csc-login`, `cuda/12.4`, `ampere` with the real hostname / module / partition encountered. Capture the full output to a local scratch file.)

- [ ] **Step 2: Populate `docs/week6/csc_gpu_environment.md`**

Create `docs/week6/csc_gpu_environment.md` with the table from `docs/week6/week6-design.md` §8.1, replacing every "(D1)" placeholder with the captured value. Header:

```markdown
# CSC GPU Environment Probe

**Captured:** 2026-05-04 by user @beren

| Item | Value |
|---|---|
| Cluster login host | <fill> |
| GPU partition name | <fill> |
| `module avail cuda` candidates | <fill, comma-separated> |
| Selected module | <fill, e.g. cuda/12.4> |
| nvcc version | <fill, e.g. 12.4.131> |
| Driver version | <fill, e.g. 550.54.15> |
| GPU model | <fill, e.g. A100 / V100 / A40> |
| Compute capability | <fill, e.g. sm_80> |
| Default wall-clock limit | <fill> |
| `--gres` syntax | <fill, e.g. `--gres=gpu:1` or `--gres=gpu:a100:1`> |
| Node home filesystem | <fill> |
| Build-artefact location | <fill, e.g. `$HOME/floatpoint`> |

## Notes & gotchas observed
- `nvidia-smi` on login node: <available / unavailable>
- module purge required before module load? <yes/no>
- (anything else surprising)
```

- [ ] **Step 3: Update SLURM template default in design doc references**

If the probe selected `--partition=ampere` and `--gres=gpu:1`, no changes are needed yet (T26 will pick these up). If different, edit T26's slurm-script step to use the probed values.

- [ ] **Step 4: Commit**

```bash
git add docs/week6/csc_gpu_environment.md
git commit -m "docs(week6): record CSC GPU environment probe (D1)"
```

---

### Task 4: Strict-IEEE CMake helpers + `build_all.sh` probes + 4 strict variants

**Why:** §4.1 of the design names this matrix as the sole Week 6 baseline. Without the build dirs we cannot run the regression matrix on D6.

**Files:**
- Modify: `cmake/CompilerFlags.cmake`
- Modify: `cmake/CUDASetup.cmake`
- Modify: `CMakeLists.txt`
- Modify: `scripts/build_all.sh`
- Modify: `.gitignore`

- [ ] **Step 1: Extend `cmake/CompilerFlags.cmake`**

Append to `cmake/CompilerFlags.cmake`:

```cmake
# --- Week 6: strict-IEEE pathway ---
#
# STRICT_IEEE=ON is opt-in. It pins the FP rounding model on both CPU and
# (when ENABLE_CUDA=ON) on nvcc, so CPU-vs-GPU same-precision diffs
# stay within the K·ULP bounds of docs/week6/week6-design.md §4.5.
#
# Explicit semantics:
#   -ffp-contract=off      : forbid the compiler from fusing a*b+c into FMA
#   -fno-fast-math         : disable the fast-math umbrella
#   -fexcess-precision=standard : prevent x87 80-bit intermediate widening
#   -fno-unsafe-math-optimizations : kills associativity tricks
#   -fno-strict-aliasing   : protects bit-pattern punning paths in regression
#   nvcc --fmad=false      : forbid implicit single-rounding FMA
#   nvcc --ftz=false       : keep denormals (no flush-to-zero)
#   nvcc --prec-div=true   : IEEE-compliant divide
#   nvcc --prec-sqrt=true  : IEEE-compliant sqrt
#
# Existing OPT_LEVEL / FAST_MATH behaviour is unchanged.

option(STRICT_IEEE "Force strict-IEEE FP flags on CPU (and CUDA if enabled)" OFF)

function(hrsc_apply_strict_ieee_cpu target)
    target_compile_options(${target} PRIVATE
        -O2
        -ffp-contract=off
        -fno-fast-math
        -fexcess-precision=standard
        -fno-unsafe-math-optimizations
        -fno-strict-aliasing
    )
endfunction()

function(hrsc_apply_strict_ieee_cuda target)
    target_compile_options(${target} PRIVATE
        $<$<COMPILE_LANGUAGE:CUDA>:
            --fmad=false
            --ftz=false
            --prec-div=true
            --prec-sqrt=true
            -Xcompiler=-O2
            -Xcompiler=-ffp-contract=off
            -Xcompiler=-fno-fast-math
            -Xcompiler=-fno-strict-aliasing
        >
    )
endfunction()
```

- [ ] **Step 2: Wire `STRICT_IEEE` into `CMakeLists.txt`**

In `CMakeLists.txt`, after the `include(${CMAKE_SOURCE_DIR}/cmake/CompilerFlags.cmake)` line and after `add_library(hrsc_core INTERFACE)`, add:

```cmake
if(STRICT_IEEE)
    hrsc_apply_strict_ieee_cpu(hrsc_core)
    if(ENABLE_CUDA)
        hrsc_apply_strict_ieee_cuda(hrsc_core)
    endif()
    message(STATUS "HRSC STRICT_IEEE: ON")
endif()
```

(Note: applying to `hrsc_core` cascades to `hrsc_euler` and `hrsc` via PUBLIC link — confirms with `cmake --build ... -- -v`.)

- [ ] **Step 3: Create the 4 strict build dirs and verify they configure clean**

```bash
cmake -B build-cpu-strict-double -G Ninja \
    -DFLOAT_PRECISION=double -DSTRICT_IEEE=ON \
    -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake -B build-cpu-strict-float  -G Ninja \
    -DFLOAT_PRECISION=float  -DSTRICT_IEEE=ON \
    -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake -B build-cuda-double-strict -G Ninja \
    -DFLOAT_PRECISION=double -DSTRICT_IEEE=ON -DENABLE_CUDA=ON \
    -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake -B build-cuda-float-strict  -G Ninja \
    -DFLOAT_PRECISION=float  -DSTRICT_IEEE=ON -DENABLE_CUDA=ON \
    -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON

for D in build-cpu-strict-double build-cpu-strict-float \
         build-cuda-double-strict build-cuda-float-strict; do
    cmake --build "$D" || { echo "FAIL: $D"; exit 1; }
done
```

Expected: 4 dirs build clean. `objdump -d build-cpu-strict-double/hrsc | grep -c vfmadd` should return `0` (proof FMA is genuinely disabled — capture this in T29's verification doc).

- [ ] **Step 4: Extend `scripts/build_all.sh`**

Open `scripts/build_all.sh`. Near the top (after the existing flag-axis arrays), add the probe helpers:

```bash
# --- Week 6: strict-IEEE probe ---
SKIP_STRICT=0
SKIP_CUDA_STRICT=0

if ! echo 'int main(){return 0;}' | "${CXX:-c++}" -ffp-contract=off -xc++ -c -o /dev/null - 2>/dev/null; then
    echo "WARN: ${CXX:-c++} does not accept -ffp-contract=off; STRICT_IEEE builds disabled" >&2
    SKIP_STRICT=1
fi

if command -v nvcc >/dev/null 2>&1; then
    if ! echo 'int main(){return 0;}' | nvcc --fmad=false -xc -c -o /dev/null - 2>/dev/null; then
        echo "WARN: nvcc does not accept --fmad=false; CUDA STRICT builds disabled" >&2
        SKIP_CUDA_STRICT=1
    fi
else
    SKIP_CUDA_STRICT=1
fi
```

Then, where `BUILD_VARIANTS+=(...)` is appended (or wherever your existing axis loop appends to the variant list), add:

```bash
if [ "$SKIP_STRICT" -eq 0 ]; then
    BUILD_VARIANTS+=(
        "build-cpu-strict-double|-DFLOAT_PRECISION=double -DSTRICT_IEEE=ON -DENABLE_OPENMP=ON"
        "build-cpu-strict-float |-DFLOAT_PRECISION=float  -DSTRICT_IEEE=ON -DENABLE_OPENMP=ON"
    )
    if [ "$SKIP_CUDA_STRICT" -eq 0 ]; then
        BUILD_VARIANTS+=(
            "build-cuda-double-strict|-DFLOAT_PRECISION=double -DSTRICT_IEEE=ON -DENABLE_CUDA=ON -DENABLE_OPENMP=ON"
            "build-cuda-float-strict |-DFLOAT_PRECISION=float  -DSTRICT_IEEE=ON -DENABLE_CUDA=ON -DENABLE_OPENMP=ON"
        )
    fi
fi
```

(Preserve the exact format of pre-existing entries — match the `dir|flags` separator pattern in the existing file.)

- [ ] **Step 5: Run `build_all.sh` once locally; verify probe + new variants land**

```bash
bash scripts/build_all.sh
ls -d build-* | sort
```

Expected: existing variants plus the 4 new ones. No silent failure.

- [ ] **Step 6: Update `.gitignore`**

Append to `.gitignore`:

```
# Week 6 strict-IEEE build dirs (covered by build-*/ but listed for clarity)
build-cpu-strict-*/
build-cuda-*-strict/
```

- [ ] **Step 7: Commit**

```bash
git add cmake/CompilerFlags.cmake CMakeLists.txt scripts/build_all.sh .gitignore
git commit -m "feat(week6): STRICT_IEEE pathway + build_all.sh probes for 4 strict variants"
```

---

## D2 (Tue 2026-05-05) — layout safety + BC kernels

### Task 5: `test_gpu_grid_layout.cpp` — stride / alignment safety net

**Why:** Per design §R2, mismatched `Grid2D` ↔ `GpuGrid` row stride would surface as silent ULP garbage across every later kernel. This must pass before any BC kernel goes in.

**Files:**
- Create: `tests/unit/test_gpu_grid_layout.cpp`
- Create: `tests/unit/gpu_layout_kernel.cu` (small kernel that writes a known pattern)

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_gpu_grid_layout.cpp`:

```cpp
#include "catch.hpp"
#include "core/grid.hpp"
#include "core/types.hpp"
#include "gpu/gpu_grid.cuh"

#include <cstring>
#include <vector>

using namespace hrsc;

constexpr int NV = 4;  // EulerNVars

// Forward decl: defined in tests/unit/gpu_layout_kernel.cu
extern "C" void launch_layout_writer(double* dev, int nx_total, int ny_total,
                                     int nvars, double base);

TEST_CASE("Grid2D and GpuGrid agree on row-stride bytes for awkward nx", "[gpu][layout]") {
    for (int nx : {7, 17, 33, 64, 257, 1024}) {
        Grid2D<double, NV> host(nx, 1, 1.0/nx, 1.0);
        GpuGrid<double, NV> dev(host);
        // Total cells incl ghost cells: (nx + 2*Ng) * (1 + 2*Ng) * NV elements.
        REQUIRE(dev.element_count() == host.data.size());
    }
}

TEST_CASE("Round-trip with known pattern is byte-identical", "[gpu][layout]") {
    Grid2D<double, NV> host(33, 17, 1.0/33, 1.0/17);
    for (std::size_t i = 0; i < host.data.size(); ++i) {
        host.data[i] = static_cast<double>(i) * 1.5 + 0.25;
    }
    GpuGrid<double, NV> dev(host);

    Grid2D<double, NV> back(33, 17, 1.0/33, 1.0/17);
    dev.download_to(back);

    REQUIRE(host.data.size() == back.data.size());
    REQUIRE(std::memcmp(host.data.data(), back.data.data(),
                        host.data.size() * sizeof(double)) == 0);
}

TEST_CASE("Kernel write to mid-row offset lands at the correct linear index",
          "[gpu][layout]") {
    Grid2D<double, NV> host(16, 16, 1.0/16, 1.0/16);
    for (auto& v : host.data) v = -1.0;

    GpuGrid<double, NV> dev(host);

    // Kernel writes value (i * 1000 + j * 10 + var) at every interior cell.
    launch_layout_writer(dev.data(), host.nx + 2 * Grid2D<double, NV>::ng_static(),
                         host.ny + 2 * Grid2D<double, NV>::ng_static(),
                         NV, 0.0);
    Grid2D<double, NV> back(16, 16, 1.0/16, 1.0/16);
    dev.download_to(back);

    // Sample a known cell (i=3, j=5, var=2) — value should be 3*1000 + 5*10 + 2 = 3052.
    constexpr int Ng = Grid2D<double, NV>::ng_static();
    const int nx_total = 16 + 2 * Ng;
    const int idx = ((5 + Ng) * nx_total + (3 + Ng)) * NV + 2;
    REQUIRE(back.data[idx] == Approx(3052.0));
}
```

If `Grid2D::ng_static()` does not exist, replace with the literal `NgHost` from `core/types.hpp`.

- [ ] **Step 2: Write `tests/unit/gpu_layout_kernel.cu`**

Create:

```cpp
#include "core/grid.hpp"

extern "C" __global__ void layout_writer_kernel(double* g, int nx_total,
                                                int ny_total, int nvars) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    int j = blockIdx.y * blockDim.y + threadIdx.y;
    if (i >= nx_total || j >= ny_total) return;
    for (int var = 0; var < nvars; ++var) {
        // Same linear index formula as Grid2D row-major / variable-last:
        int idx = (j * nx_total + i) * nvars + var;
        g[idx] = static_cast<double>(i) * 1000.0 +
                 static_cast<double>(j) * 10.0 +
                 static_cast<double>(var);
    }
}

extern "C" void launch_layout_writer(double* dev, int nx_total, int ny_total,
                                     int nvars, double /*base*/) {
    dim3 block(16, 16);
    dim3 grid((nx_total + 15) / 16, (ny_total + 15) / 16);
    layout_writer_kernel<<<grid, block>>>(dev, nx_total, ny_total, nvars);
    (void)cudaDeviceSynchronize();
}
```

- [ ] **Step 3: Wire the new `.cu` into `CMakeLists.txt`**

In the `if(ENABLE_CUDA) ... endif()` block, alongside `gpu_roundtrip_kernel.cu`, add:

```cmake
    target_sources(unit_tests PRIVATE tests/unit/gpu_layout_kernel.cu)
    set_source_files_properties(tests/unit/gpu_layout_kernel.cu
        PROPERTIES LANGUAGE CUDA)
```

- [ ] **Step 4: Run, expect FAIL (kernel not yet linked / extern decl missing)**

```bash
cmake --build build-cuda-double-strict --target unit_tests
./build-cuda-double-strict/unit_tests "[gpu][layout]" -r compact
```

If everything compiled cleanly, expect 3 cases PASS — the layout was already correct. If it fails, this is exactly the bug R2 was guarding against; investigate stride alignment in `GpuGrid` before continuing to T6.

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_gpu_grid_layout.cpp tests/unit/gpu_layout_kernel.cu CMakeLists.txt
git commit -m "test(week6): GpuGrid stride / alignment safety net (R2 mitigation)"
```

---

### Task 6: GPU outflow BC kernel + tests

**Why:** Simplest kernel; validates BC pipeline shape (kernel signature, launcher, oracle comparison) before periodic / reflective extend the pattern.

**Files:**
- Modify: `src/gpu/euler_kernels.cuh` (declare `apply_outflow_bc_gpu`)
- Modify: `src/gpu/euler_kernels.cu` (define + explicit instantiate)
- Create: `tests/unit/test_gpu_bc.cpp` (initial: 2 outflow cases, X and Y axis)

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_gpu_bc.cpp`:

```cpp
#include "catch.hpp"
#include "core/grid.hpp"
#include "core/boundary.hpp"
#include "gpu/euler_kernels.cuh"
#include "gpu/gpu_grid.cuh"

#include <cstring>
#include <random>

using namespace hrsc;
constexpr int NV = EulerNVars;

namespace {
template <typename Real>
Grid2D<Real, NV> make_random_grid(int nx, int ny, unsigned seed) {
    Grid2D<Real, NV> g(nx, ny, 1.0/nx, 1.0/ny);
    std::mt19937 rng(seed);
    std::uniform_real_distribution<Real> d(-1.0, 1.0);
    for (auto& v : g.data) v = d(rng);
    return g;
}
}  // namespace

TEST_CASE("GPU outflow BC matches CPU oracle on X axis", "[gpu][bc]") {
    auto host = make_random_grid<double>(31, 13, 1234);

    Grid2D<double, NV> cpu_out = host;
    apply_outflow_bc<double, NV>(cpu_out.view(), Axis::X);

    GpuGrid<double, NV> dev(host);
    apply_outflow_bc_gpu<double>(dev, Axis::X);
    Grid2D<double, NV> gpu_out = host;
    dev.download_to(gpu_out);

    REQUIRE(std::memcmp(cpu_out.data.data(), gpu_out.data.data(),
                        cpu_out.data.size() * sizeof(double)) == 0);
}

TEST_CASE("GPU outflow BC matches CPU oracle on Y axis", "[gpu][bc]") {
    auto host = make_random_grid<double>(31, 13, 5678);

    Grid2D<double, NV> cpu_out = host;
    apply_outflow_bc<double, NV>(cpu_out.view(), Axis::Y);

    GpuGrid<double, NV> dev(host);
    apply_outflow_bc_gpu<double>(dev, Axis::Y);
    Grid2D<double, NV> gpu_out = host;
    dev.download_to(gpu_out);

    REQUIRE(std::memcmp(cpu_out.data.data(), gpu_out.data.data(),
                        cpu_out.data.size() * sizeof(double)) == 0);
}
```

If `Grid2D::view()` is not the exact accessor name, look up the existing accessor in `src/core/grid.hpp` and substitute (BC primitives in `src/core/boundary.hpp:32-60` show the pattern).

- [ ] **Step 2: Run, expect FAIL (linker — `apply_outflow_bc_gpu` not defined)**

```bash
cmake --build build-cuda-double-strict --target unit_tests
./build-cuda-double-strict/unit_tests "[gpu][bc]" -r compact 2>&1 | head -20
```

Expected: undefined symbol error.

- [ ] **Step 3: Declare in `src/gpu/euler_kernels.cuh`**

Inside the `namespace hrsc { ... }` block, add:

```cpp
// Outflow (transmissive) BC. Mirrors src/core/boundary.hpp::apply_outflow_bc.
// Fills ghost cells on `axis` only; corner ghosts pick up correct values
// when X-pass runs before Y-pass (matches CPU contract).
template <typename Real>
void apply_outflow_bc_gpu(GpuGrid<Real, EulerNVars>& g, Axis axis);

extern template void apply_outflow_bc_gpu<float >(GpuGrid<float , EulerNVars>&, Axis);
extern template void apply_outflow_bc_gpu<double>(GpuGrid<double, EulerNVars>&, Axis);
```

- [ ] **Step 4: Define in `src/gpu/euler_kernels.cu` (new file)**

Create `src/gpu/euler_kernels.cu`:

```cpp
// src/gpu/euler_kernels.cu — kernel definitions + explicit instantiation.

#include "gpu/euler_kernels.cuh"
#include "core/types.hpp"

namespace hrsc {
namespace gpu_detail {

template <typename Real>
__global__ void outflow_x_kernel(Real* g, int nx, int ny, int ng) {
    int j = blockIdx.y * blockDim.y + threadIdx.y - ng;  // includes ghost rows
    if (j < -ng || j >= ny + ng) return;
    int js = (j < 0) ? 0 : (j >= ny ? ny - 1 : j);
    int nx_total = nx + 2 * ng;

    auto idx = [&](int i, int jj, int var) {
        return ((jj + ng) * nx_total + (i + ng)) * EulerNVars + var;
    };
    for (int var = 0; var < EulerNVars; ++var) {
        for (int gh = 1; gh <= ng; ++gh) {
            g[idx(-gh,        j, var)] = g[idx(0,        js, var)];
            g[idx(nx - 1 + gh, j, var)] = g[idx(nx - 1, js, var)];
        }
    }
}

template <typename Real>
__global__ void outflow_y_kernel(Real* g, int nx, int ny, int ng) {
    int i = blockIdx.x * blockDim.x + threadIdx.x - ng;
    if (i < -ng || i >= nx + ng) return;
    int nx_total = nx + 2 * ng;

    auto idx = [&](int ii, int jj, int var) {
        return ((jj + ng) * nx_total + (ii + ng)) * EulerNVars + var;
    };
    for (int var = 0; var < EulerNVars; ++var) {
        for (int gh = 1; gh <= ng; ++gh) {
            g[idx(i, -gh,        var)] = g[idx(i, 0,        var)];
            g[idx(i, ny - 1 + gh, var)] = g[idx(i, ny - 1, var)];
        }
    }
}
} // namespace gpu_detail

template <typename Real>
void apply_outflow_bc_gpu(GpuGrid<Real, EulerNVars>& g, Axis axis) {
    constexpr int Ng = NgHost;
    const int nx = g.nx();
    const int ny = g.ny();
    if (axis == Axis::X) {
        dim3 block(1, 64);
        dim3 grid(1, ((ny + 2 * Ng) + 63) / 64);
        gpu_detail::outflow_x_kernel<Real><<<grid, block>>>(g.data(), nx, ny, Ng);
    } else {
        dim3 block(64, 1);
        dim3 grid(((nx + 2 * Ng) + 63) / 64, 1);
        gpu_detail::outflow_y_kernel<Real><<<grid, block>>>(g.data(), nx, ny, Ng);
    }
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());
}

template void apply_outflow_bc_gpu<float >(GpuGrid<float , EulerNVars>&, Axis);
template void apply_outflow_bc_gpu<double>(GpuGrid<double, EulerNVars>&, Axis);

} // namespace hrsc
```

- [ ] **Step 5: Wire `euler_kernels.cu` into `CMakeLists.txt`**

In the `if(ENABLE_CUDA) ... endif()` block, alongside `euler_gpu_solver.cu`, add:

```cmake
    target_sources(hrsc_euler PRIVATE src/gpu/euler_kernels.cu)
    set_source_files_properties(src/gpu/euler_kernels.cu
        PROPERTIES LANGUAGE CUDA)
```

- [ ] **Step 6: Run, expect PASS**

```bash
cmake --build build-cuda-double-strict --target unit_tests
./build-cuda-double-strict/unit_tests "[gpu][bc]" -r compact
```

Expected: 2 cases PASS; `memcmp` is bit-exact.

- [ ] **Step 7: Commit**

```bash
git add src/gpu/euler_kernels.cuh src/gpu/euler_kernels.cu \
        tests/unit/test_gpu_bc.cpp CMakeLists.txt
git commit -m "feat(week6): GPU outflow BC kernel + bit-exact CPU oracle test"
```

---

### Task 7: GPU periodic BC kernel + tests

**Files:**
- Modify: `src/gpu/euler_kernels.cuh` (declare)
- Modify: `src/gpu/euler_kernels.cu` (define + instantiate)
- Modify: `tests/unit/test_gpu_bc.cpp` (add 2 cases)

- [ ] **Step 1: Add 2 failing tests** (X and Y) to `tests/unit/test_gpu_bc.cpp` modeled on the outflow cases — replace `apply_outflow_bc` with `apply_periodic_bc` (CPU side, in `src/core/boundary.hpp`) and `apply_outflow_bc_gpu` with `apply_periodic_bc_gpu`.

- [ ] **Step 2: Run, expect FAIL** (linker error). `cmake --build build-cuda-double-strict && ./build-cuda-double-strict/unit_tests "[gpu][bc]"`.

- [ ] **Step 3: Declare `apply_periodic_bc_gpu` in `euler_kernels.cuh`** (mirror outflow declaration).

- [ ] **Step 4: Define in `euler_kernels.cu`.** The CPU oracle is in `src/core/boundary.hpp` (look at `apply_periodic_bc<Real, NVars>`); periodic copies wrap from `[nx-Ng, nx)` to `[-Ng, 0)` (and similarly on Y). Port the loop bodies into `__global__` kernels; the launcher uses the same `dim3` shape as outflow.

- [ ] **Step 5: Run, expect PASS.**

- [ ] **Step 6: Commit**

```bash
git add src/gpu/euler_kernels.cuh src/gpu/euler_kernels.cu tests/unit/test_gpu_bc.cpp
git commit -m "feat(week6): GPU periodic BC kernel + bit-exact tests"
```

---

### Task 8: GPU reflective BC kernel + tests

**Files:**
- Modify: `src/gpu/euler_kernels.cuh` (declare)
- Modify: `src/gpu/euler_kernels.cu` (define + instantiate)
- Modify: `tests/unit/test_gpu_bc.cpp` (add 2 cases — bringing total to 6)

- [ ] **Step 1: Add 2 failing tests** for reflective BC (X and Y) modeled on the outflow / periodic cases. Use the CPU oracle `apply_reflective_bc<Real, NVars, FlipList>` from `src/core/boundary.hpp`. For Euler the flip list on X is `{RHOU}` and on Y is `{RHOV}` (consult the existing CPU usage site in `src/euler/euler_solver.cpp` to confirm the indices).

- [ ] **Step 2: Run, expect FAIL.**

- [ ] **Step 3: Declare `apply_reflective_bc_gpu<Real>(GpuGrid&, Axis)`** in `euler_kernels.cuh`. Hard-code the Euler flip list (RHOU on X, RHOV on Y) inside the kernel — Week 6 does not need MHD's compile-time flip-list flexibility.

- [ ] **Step 4: Define in `euler_kernels.cu`.** Reflective is mirror-then-flip: ghost cell at `i = -gh` reads from `i = gh - 1`, then the chosen normal-momentum component is sign-flipped. Match the CPU loop ordering exactly.

- [ ] **Step 5: Run, expect PASS — all 6 [gpu][bc] cases green.**

- [ ] **Step 6: Smoke against LW Config 3 IC**

```bash
# Build a tiny driver test that loads LW Config 3 IC, applies all three BCs
# in turn (outflow x, periodic x, reflective x — same drill on Y), compares
# with CPU oracle. Or fold this into a single Catch case under [gpu][bc][lw3].
```

(Acceptable to defer this drill into T18's e2e suite if time-pressed.)

- [ ] **Step 7: Commit**

```bash
git add src/gpu/euler_kernels.cuh src/gpu/euler_kernels.cu tests/unit/test_gpu_bc.cpp
git commit -m "feat(week6): GPU reflective BC kernel + bit-exact tests; BC matrix complete"
```

---

## D3 (Wed 2026-05-06) — Timer 5-phase + CFL kernel

### Task 9: ScopedTimer 5-phase split — add `flux` and `update`

**Why:** Acceptance gate G6. The CPU side ships first; the GPU side hooks in T16.

**Files:**
- Modify: `src/utils/profiling.hpp` (or wherever the named-phase enum lives)
- Modify: `src/euler/euler_solver.cpp` (emit two more `ScopedTimer` regions)

- [ ] **Step 1: Identify the current 3 phases**

```bash
grep -n "ScopedTimer" src/euler/euler_solver.cpp src/utils/profiling.hpp 2>/dev/null
```

You should see scopes named `bc`, `cfl`, `sweep`. The Week 6 goal is to split `sweep` into `flux` and `update`.

- [ ] **Step 2: Add unit-level test for the new phase names**

Open or create `tests/unit/test_profiling_phases.cpp`. Write a Catch case that builds a tiny `EulerSolver`, runs 1 step under `HRSC_ENABLE_PROFILING`, and asserts the registry contains keys `{"bc", "cfl", "flux", "update"}` (and optionally still `"sweep"` if you want backwards compat).

```cpp
#ifdef HRSC_ENABLE_PROFILING
TEST_CASE("ScopedTimer emits 5-phase split", "[profiling]") {
    // Construct tiny solver, run 1 step, snapshot registry, assert keys present.
    // (Adapt to whatever public API exists in profiling.hpp.)
}
#endif
```

- [ ] **Step 3: Run with profiling enabled, expect FAIL**

```bash
cmake -B build-prof -G Ninja -DFLOAT_PRECISION=double \
    -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON \
    -DHRSC_ENABLE_PROFILING=ON
cmake --build build-prof
./build-prof/unit_tests "[profiling]" -r compact
```

- [ ] **Step 4: Split `sweep` into `flux` and `update` in `euler_solver.cpp`**

Find the existing `ScopedTimer sweep_timer("sweep", ...);` region. Inside the per-step body, replace with two narrower scopes:

```cpp
{
    ScopedTimer t_flux("flux", reg);
    // existing flux-computation block (reconstruct, predict, riemann)
}
{
    ScopedTimer t_update("update", reg);
    // existing conservative-update block
}
```

Keep the outer `sweep` scope if you want a "total of flux+update" reading; otherwise drop it. The bridge currently lists 3 phases; we're going to 5 (`bc`, `cfl`, `flux`, `update`, plus an optional aggregate `sweep`).

- [ ] **Step 5: Run, expect PASS**

```bash
cmake --build build-prof
./build-prof/unit_tests "[profiling]" -r compact
```

- [ ] **Step 6: Confirm cfg-default byte-identity (G5)**

`HRSC_ENABLE_PROFILING=OFF` is the default. With it off, the binary should be byte-identical to D1's output:

```bash
md5sum build-double/hrsc                    # before this commit
md5sum build-double-rebuilt-after-T9/hrsc   # after rebuild
```

(If you didn't snapshot the pre-T9 binary md5, just confirm `./build-double/hrsc tests/cases/toro_1d/sod.cfg` produces the same Sod output as D1.)

- [ ] **Step 7: Commit**

```bash
git add src/euler/euler_solver.cpp src/utils/profiling.hpp tests/unit/test_profiling_phases.cpp
git commit -m "feat(week6): ScopedTimer 5-phase split (flux/update); CPU side"
```

---

### Task 10: GPU CFL reduction kernel (deterministic `atomicMin` on bit-reinterpret)

**Why:** This is the trickiest determinism contract in Week 6. The kernel must be bit-equivalent to CPU `compute_dt` regardless of grid size or block shape. Run-to-run identity is also required (catches any sneaky non-determinism).

**Files:**
- Modify: `src/gpu/euler_kernels.cuh` (declare `compute_dt_gpu`)
- Modify: `src/gpu/euler_kernels.cu` (define + instantiate)
- Create: `tests/unit/test_gpu_cfl.cpp` (4 cases)

- [ ] **Step 1: Write 4 failing tests**

Create `tests/unit/test_gpu_cfl.cpp`:

```cpp
#include "catch.hpp"
#include "core/grid.hpp"
#include "core/types.hpp"
#include "core/eos.hpp"
#include "euler/euler_solver.hpp"
#include "gpu/euler_kernels.cuh"
#include "gpu/gpu_grid.cuh"

#include <random>

using namespace hrsc;
constexpr int NV = EulerNVars;

namespace {
template <typename Real>
Grid2D<Real, NV> random_physical_grid(int nx, int ny, unsigned seed) {
    Grid2D<Real, NV> g(nx, ny, 1.0/nx, 1.0/ny);
    std::mt19937 rng(seed);
    std::uniform_real_distribution<Real> rho_d(0.5, 3.0);
    std::uniform_real_distribution<Real> u_d(-2.0, 2.0);
    std::uniform_real_distribution<Real> p_d(0.5, 3.0);
    constexpr int Ng = NgHost;
    int nx_total = nx + 2 * Ng;
    for (int j = -Ng; j < ny + Ng; ++j)
    for (int i = -Ng; i < nx + Ng; ++i) {
        Real rho = rho_d(rng), u = u_d(rng), v = u_d(rng), p = p_d(rng);
        Real E = p / (1.4 - 1) + 0.5 * rho * (u*u + v*v);
        int idx = ((j+Ng) * nx_total + (i+Ng)) * NV;
        g.data[idx + RHO]  = rho;
        g.data[idx + RHOU] = rho * u;
        g.data[idx + RHOV] = rho * v;
        g.data[idx + ENER] = E;
    }
    return g;
}
}  // namespace

TEST_CASE("GPU CFL bit-equivalent to CPU on awkward grid sizes", "[gpu][cfl]") {
    for (auto sz : {std::pair{7, 3}, std::pair{16, 16},
                    std::pair{257, 129}, std::pair{1024, 1024}}) {
        auto host = random_physical_grid<double>(sz.first, sz.second, 42);
        const double gamma = 1.4, cfl = 0.4;

        double dt_cpu = compute_dt_cpu_oracle<double>(host, gamma, cfl);

        GpuGrid<double, NV> dev(host);
        double dt_gpu = compute_dt_gpu<double>(dev, gamma, cfl);

        REQUIRE(dt_cpu == dt_gpu);   // bit-exact
    }
}

TEST_CASE("GPU CFL is run-to-run bit-identical (100x)", "[gpu][cfl]") {
    auto host = random_physical_grid<double>(257, 129, 7);
    GpuGrid<double, NV> dev(host);

    double first = compute_dt_gpu<double>(dev, 1.4, 0.4);
    for (int i = 0; i < 99; ++i) {
        double next = compute_dt_gpu<double>(dev, 1.4, 0.4);
        REQUIRE(next == first);   // bit-exact across 100 invocations
    }
}
```

If `compute_dt_cpu_oracle` is not the existing CPU helper name, find the right one in `src/euler/euler_solver.cpp` and create a small `extern` shim or in-test helper that mimics the CPU per-cell `dt = cfl * min(dx/(|u|+a), dy/(|v|+a))` reduction.

- [ ] **Step 2: Run, expect FAIL** (link error: `compute_dt_gpu` not defined).

- [ ] **Step 3: Declare in `src/gpu/euler_kernels.cuh`**

```cpp
// Compute global dt = cfl * min over all interior cells of
// min(dx / (|u| + a), dy / (|v| + a)).
//
// Determinism: per-block deterministic tree-reduce in shared memory;
// per-block winner committed via atomicMin on bit-reinterpret of positive
// floats (positive-float bit pattern is monotonic in the integer ordering,
// so atomicMin on integers is the same as min on floats — and atomicMin on
// integers is order-independent, unlike atomicAdd).
//
// See docs/week6/week6-design.md §4.3 for full derivation.
template <typename Real>
TimeReal compute_dt_gpu(GpuGrid<Real, EulerNVars>& g, Real gamma, Real cfl);

extern template TimeReal compute_dt_gpu<float >(GpuGrid<float , EulerNVars>&, float , float );
extern template TimeReal compute_dt_gpu<double>(GpuGrid<double, EulerNVars>&, double, double);
```

- [ ] **Step 4: Define in `src/gpu/euler_kernels.cu`**

```cpp
namespace gpu_detail {

// Bit-reinterpret helpers (positive-float-only, monotonic).
__device__ inline int  pos_float_to_int (float  d) { return __float_as_int(d); }
__device__ inline float pos_int_to_float(int    i) { return __int_as_float(i); }
__device__ inline long long pos_double_to_ll(double d) { return __double_as_longlong(d); }
__device__ inline double    pos_ll_to_double(long long l) { return __longlong_as_double(l); }

// Single-threaded per-block tree reduce (deterministic), then atomicMin
// on the global bit-pattern accumulator.
template <typename Real, int BX, int BY>
__global__ void cfl_kernel(const Real* g, int nx, int ny, int ng,
                           Real dx, Real dy, Real gamma, Real cfl,
                           int* g_min_bits)  // pretends int for clarity; cast to long long for double
{
    __shared__ Real candidates[BX * BY];
    int i = blockIdx.x * BX + threadIdx.x;
    int j = blockIdx.y * BY + threadIdx.y;
    int t = threadIdx.y * BX + threadIdx.x;
    int nx_total = nx + 2 * ng;

    Real my_dt = (Real)1e30;
    if (i < nx && j < ny) {
        int idx = ((j + ng) * nx_total + (i + ng)) * EulerNVars;
        Real rho = g[idx + RHO];
        Real u   = g[idx + RHOU] / rho;
        Real v   = g[idx + RHOV] / rho;
        Real E   = g[idx + ENER];
        Real ke  = (Real)0.5 * rho * (u*u + v*v);
        Real p   = (gamma - (Real)1) * (E - ke);
        Real a   = sqrt(gamma * p / rho);
        Real dt_x = dx / (fabs(u) + a);
        Real dt_y = dy / (fabs(v) + a);
        my_dt    = cfl * fmin(dt_x, dt_y);
    }
    candidates[t] = my_dt;
    __syncthreads();

    // Deterministic reverse-halving tree reduce.
    for (int stride = (BX * BY) / 2; stride > 0; stride >>= 1) {
        if (t < stride) {
            Real a = candidates[t], b = candidates[t + stride];
            candidates[t] = fmin(a, b);
        }
        __syncthreads();
    }

    if (t == 0) {
        // Single thread per block performs atomicMin on the bit pattern.
        // For float, reinterpret to int; for double, reinterpret to long long.
        // (Two specialisations below; pick the right one at compile time.)
        if constexpr (sizeof(Real) == 4) {
            int my_bits = __float_as_int(candidates[0]);
            atomicMin(g_min_bits, my_bits);
        } else {
            long long my_bits = __double_as_longlong(candidates[0]);
            atomicMin(reinterpret_cast<unsigned long long*>(g_min_bits),
                      static_cast<unsigned long long>(my_bits));
            // Note: positive doubles' bit patterns ARE monotonic when
            // interpreted as unsigned long long; atomicMin on uint64
            // is supported by sm_35+ via atomicCAS in the CUDA runtime.
        }
    }
}

} // namespace gpu_detail

template <typename Real>
TimeReal compute_dt_gpu(GpuGrid<Real, EulerNVars>& g, Real gamma, Real cfl) {
    constexpr int BX = 16, BY = 16;
    dim3 block(BX, BY);
    dim3 grid((g.nx() + BX - 1) / BX, (g.ny() + BY - 1) / BY);

    // Initialise device accumulator to the integer pattern of +Inf.
    using BitsT = std::conditional_t<sizeof(Real) == 4, int, long long>;
    BitsT pos_inf_bits = (sizeof(Real) == 4)
        ? __builtin_bit_cast(int, std::numeric_limits<float>::infinity())
        : __builtin_bit_cast(long long, std::numeric_limits<double>::infinity());

    DeviceArray<BitsT> dev_min(1);
    HRSC_CUDA_CHECK(cudaMemcpy(dev_min.data(), &pos_inf_bits, sizeof(BitsT),
                               cudaMemcpyHostToDevice));

    gpu_detail::cfl_kernel<Real, BX, BY><<<grid, block>>>(
        g.data(), g.nx(), g.ny(), NgHost, g.dx(), g.dy(), gamma, cfl,
        reinterpret_cast<int*>(dev_min.data()));
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());

    BitsT host_bits;
    HRSC_CUDA_CHECK(cudaMemcpy(&host_bits, dev_min.data(), sizeof(BitsT),
                               cudaMemcpyDeviceToHost));

    Real dt = (sizeof(Real) == 4)
        ? __builtin_bit_cast(float,  static_cast<int>(host_bits))
        : __builtin_bit_cast(double, host_bits);
    return static_cast<TimeReal>(dt);
}

template TimeReal compute_dt_gpu<float >(GpuGrid<float , EulerNVars>&, float , float );
template TimeReal compute_dt_gpu<double>(GpuGrid<double, EulerNVars>&, double, double);
```

(The `atomicMin(unsigned long long*, ...)` overload is available on sm_35+; verify against the CSC GPU compute capability captured in `csc_gpu_environment.md`. If a compute cap < sm_35 is encountered, fall back to a CAS loop.)

- [ ] **Step 5: Run, expect PASS — all 4 cases bit-equivalent**

```bash
cmake --build build-cuda-double-strict
./build-cuda-double-strict/unit_tests "[gpu][cfl]" -r compact
```

If any case fails by 1+ ULP: do **not** widen the threshold. The most likely fix-points are: forgot `__syncthreads()` between halving rounds; used `cuda::std::min` with an order-dependent intrinsic; used `atomicAdd` instead of `atomicMin`; or per-cell algebra differs from CPU oracle.

- [ ] **Step 6: Run once under `compute-sanitizer` to catch UB**

```bash
compute-sanitizer --tool=racecheck --error-exitcode=1 \
    ./build-cuda-double-strict/unit_tests "[gpu][cfl]"
compute-sanitizer --tool=memcheck --error-exitcode=1 \
    ./build-cuda-double-strict/unit_tests "[gpu][cfl]"
```

Expected: no errors. If `compute-sanitizer` is not available locally, defer to D7 on CSC.

- [ ] **Step 7: Commit**

```bash
git add src/gpu/euler_kernels.cuh src/gpu/euler_kernels.cu tests/unit/test_gpu_cfl.cpp
git commit -m "feat(week6): GPU deterministic CFL reduction (atomicMin on bits) + 4 tests"
```

---

## D4 (Thu 2026-05-07) — reconstruct + predict

### Task 11: GPU MUSCL reconstruction kernel (minmod limiter)

**Why:** Reconstruction is a per-cell stencil-of-3 operation with no reduction → embarrassingly parallel. Reusing the `__host__ __device__`-friendly `muscl_reconstruct` from `src/euler/muscl.hpp` keeps the algebra identical to CPU.

**Files:**
- Modify: `src/gpu/euler_kernels.cuh` (declare `muscl_reconstruct_gpu`)
- Modify: `src/gpu/euler_kernels.cu` (define + instantiate)
- Create: `tests/unit/test_gpu_reconstruct.cpp` (3 cases)

- [ ] **Step 1: Write the 3 failing tests**

Create `tests/unit/test_gpu_reconstruct.cpp` with the same scaffolding as `test_gpu_bc.cpp`. Cases:

1. Single-cell trivial gradient (constant data → slope = 0; qL == qR == cell value).
2. 16×16 with strong shock-like jump halfway across; compare every face-state against CPU `muscl_reconstruct` from `src/euler/muscl.hpp`.
3. 33×17 (non-power-of-two) full-grid reconstruction.

Each comparison uses `memcmp` on the device-side qL / qR buffers vs CPU output (bit-exact under strict-IEEE).

- [ ] **Step 2: Run, expect FAIL.**

- [ ] **Step 3: Declare `muscl_reconstruct_gpu<Real>(...)` in `euler_kernels.cuh`**

The signature should produce two device buffers (qL on every face, qR on every face), shaped to match the CPU layout used in `euler_solver.cpp`. Mirror whatever buffer arrangement the CPU sweep uses — easiest is a `DeviceArray<Vec<Real, EulerNVars>>` per-face buffer, sized `(nx+1) * ny` for X-faces.

- [ ] **Step 4: Define in `euler_kernels.cu`**

The kernel body is essentially:

```cpp
template <typename Real>
__global__ void muscl_reconstruct_x_kernel(const Real* g, int nx, int ny, int ng,
                                           Vec<Real, EulerNVars>* qL,
                                           Vec<Real, EulerNVars>* qR) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    int j = blockIdx.y * blockDim.y + threadIdx.y;
    if (i > nx || j >= ny) return;  // (nx+1) X-faces

    // Read 4 neighbour cells; call existing host_device muscl_reconstruct.
    // Write qL[face_idx], qR[face_idx].
}
```

Reuse `muscl_reconstruct` from `src/euler/muscl.hpp` directly (it's already `HD_FUNC`). The bit-exact requirement is only realistic if CPU and GPU evaluate the exact same expression tree — confirm by running the test suite under `--fmad=false`.

- [ ] **Step 5: Run, expect PASS — all 3 cases bit-exact.**

- [ ] **Step 6: Commit**

```bash
git add src/gpu/euler_kernels.cuh src/gpu/euler_kernels.cu tests/unit/test_gpu_reconstruct.cpp
git commit -m "feat(week6): GPU MUSCL reconstruction kernel (minmod) + 3 bit-exact tests"
```

---

### Task 12: GPU Hancock predictor kernel

**Files:**
- Modify: `src/gpu/euler_kernels.cuh` (declare `hancock_predict_gpu`)
- Modify: `src/gpu/euler_kernels.cu` (define + instantiate)
- Create: `tests/unit/test_gpu_hancock.cpp` (3 cases)

- [ ] **Step 1: Write 3 failing tests** mirroring the reconstruct test layout — single cell, 16×16 with sub/super/sonic-point states, 33×17. Oracle: `hancock_predict` from `src/euler/hancock.hpp`.

- [ ] **Step 2: Run, expect FAIL.**

- [ ] **Step 3: Declare + define** the kernel using `hancock_predict` (which is HD_FUNC) inside the kernel body.

- [ ] **Step 4: Run, expect PASS.**

- [ ] **Step 5: Commit**

```bash
git add src/gpu/euler_kernels.cuh src/gpu/euler_kernels.cu tests/unit/test_gpu_hancock.cpp
git commit -m "feat(week6): GPU Hancock predictor kernel + 3 bit-exact tests"
```

---

## D5 (Fri 2026-05-08) — Rusanov flux, update, orchestration, dispatch wire, GPU timing, e2e, LW Config 4

### Task 13: GPU conservative-update kernel

**Files:**
- Modify: `src/gpu/euler_kernels.cuh` (declare `apply_update_gpu`)
- Modify: `src/gpu/euler_kernels.cu` (define + instantiate)
- Create: `tests/unit/test_gpu_update.cpp` (3 cases)

- [ ] **Step 1: Write the 3 failing tests** (1-step update with synthetic flux input; BC-then-update; Lie-splitting half-step). Oracle is the CPU update block in `src/euler/euler_solver.cpp` — extract its algebra into a small `__host__ __device__` helper if it isn't already, so both sides call the same code.

- [ ] **Step 2: Run, expect FAIL.**

- [ ] **Step 3: Declare + define** the kernel. The update is `U[i,j] -= (dt/dx) * (F[i+1/2] - F[i-1/2]) - (dt/dy) * (G[j+1/2] - G[j-1/2])`; per-cell, no reduction.

- [ ] **Step 4: Run, expect PASS — all 3 cases bit-exact.**

- [ ] **Step 5: Commit**

```bash
git add src/gpu/euler_kernels.cuh src/gpu/euler_kernels.cu tests/unit/test_gpu_update.cpp
git commit -m "feat(week6): GPU conservative-update kernel + 3 bit-exact tests"
```

---

### Task 14: GPU Rusanov flux kernel + tests

**Files:**
- Modify: `src/gpu/euler_kernels.cuh` (declare `rusanov_flux_gpu`)
- Modify: `src/gpu/euler_kernels.cu` (define + instantiate)
- Create: `tests/unit/test_gpu_rusanov.cpp` (4 cases)

- [ ] **Step 1: Write 4 failing tests** — single face; sonic point; stationary contact face; 16×16 full sweep. Oracle: `rusanov_flux` from `src/euler/rusanov.hpp`.

- [ ] **Step 2: Run, expect FAIL.**

- [ ] **Step 3: Declare + define** the kernel using `rusanov_flux` (HD_FUNC). The kernel reads qL[face], qR[face] from device buffers and writes flux[face]. One face per thread.

- [ ] **Step 4: Run, expect PASS.**

- [ ] **Step 5: Commit**

```bash
git add src/gpu/euler_kernels.cuh src/gpu/euler_kernels.cu tests/unit/test_gpu_rusanov.cpp
git commit -m "feat(week6): GPU Rusanov flux kernel + 4 bit-exact tests"
```

---

### Task 15: GPU sweep launcher (X / Y orchestration of reconstruct + predict + flux + update)

**Why:** Bundles the 4 kernels into a single per-axis sweep launch sequence — the unit `step` work item that `EulerGpuSolver::step` will call.

**Files:**
- Modify: `src/gpu/euler_kernels.cuh` (declare `sweep_x_gpu` / `sweep_y_gpu`)
- Modify: `src/gpu/euler_kernels.cu` (define + instantiate; allocate transient face buffers internally)

- [ ] **Step 1: Write a one-step sweep test** in a new `tests/unit/test_gpu_sweep.cpp`. IC is LW Config 3 64×64; run 1 X-sweep + 1 Y-sweep on GPU; compare against the CPU `euler_solver.step` output bit-equivalent (under strict-IEEE this MUST hold).

- [ ] **Step 2: Run, expect FAIL.**

- [ ] **Step 3: Implement `sweep_x_gpu<Real>(GpuGrid&, Real dt, Real gamma, FluxScheme)`** that:
  1. Allocates a face-state buffer (qL, qR) — `DeviceArray<Vec<Real,NV>>` of size `(nx+1)*ny`.
  2. Launches `muscl_reconstruct_x_kernel`.
  3. Launches `hancock_predict_x_kernel`.
  4. Launches a flux kernel — Rusanov by default in this task; T20 swaps in HLLC behind a `FluxScheme` enum branch.
  5. Launches `apply_update_x_kernel` consuming the flux buffer.

`sweep_y_gpu` is the symmetric Y-axis version.

- [ ] **Step 4: Run, expect PASS — bit-exact against CPU.**

- [ ] **Step 5: Commit**

```bash
git add src/gpu/euler_kernels.cuh src/gpu/euler_kernels.cu tests/unit/test_gpu_sweep.cpp
git commit -m "feat(week6): GPU per-axis sweep launcher (reconstruct→predict→flux→update)"
```

---

### Task 16: `EulerGpuSolver::step()` and `::run()` orchestration + GPU ScopedTimer hooks

**Files:**
- Modify: `src/gpu/euler_gpu_solver.cu` (fill in `step` / `run`)

- [ ] **Step 1: Implement `step(dt)`**

Replace the empty body in `src/gpu/euler_gpu_solver.cu`:

```cpp
template <typename Real>
void EulerGpuSolver<Real>::step(TimeReal dt) {
#ifdef HRSC_ENABLE_PROFILING
    extern ProfilingRegistry& global_registry();  // or however the project exposes it
    auto& reg = global_registry();
#endif

    // Alternating Lie splitting: even step → X then Y; odd → Y then X.
    auto sweep_x = [&]() {
#ifdef HRSC_ENABLE_PROFILING
        ScopedTimer t_bc("bc",      reg);
#endif
        if (m_bc_x == BoundaryType::Outflow)    apply_outflow_bc_gpu(m_dev_grid, Axis::X);
        else if (m_bc_x == BoundaryType::Periodic) apply_periodic_bc_gpu(m_dev_grid, Axis::X);
        else                                       apply_reflective_bc_gpu(m_dev_grid, Axis::X);
#ifdef HRSC_ENABLE_PROFILING
        // sweep_x_gpu internally calls reconstruct/predict/flux/update; for
        // GPU we measure the whole device-side sweep as one block (per design
        // §3.2(d) we use default stream + sync at boundaries — finer cudaEvent
        // probes are deferred to Week 7 perf work).
        { ScopedTimer t_sw("flux",  reg); /* see below */ }
#endif
        sweep_x_gpu(m_dev_grid, static_cast<Real>(dt), m_gamma, m_flux);
    };
    auto sweep_y = [&]() { /* symmetric */ };

    if ((m_step % 2) == 0) { sweep_x(); sweep_y(); }
    else                   { sweep_y(); sweep_x(); }

    m_time += dt;
    m_step += 1;
}
```

(The exact ScopedTimer placement: emit `bc`, `flux`, `update` markers to match T9's CPU-side semantics. Inside `sweep_x_gpu` the reconstruct→predict→flux are bundled as `flux`; the conservative update is `update`. Keep this aligned with what `euler_solver.cpp` does so a CPU/GPU side-by-side timing report is meaningful.)

- [ ] **Step 2: Implement `run()`**

```cpp
template <typename Real>
double EulerGpuSolver<Real>::run() {
    Timer wall;
    wall.start();
    while (m_time < m_t_end) {
#ifdef HRSC_ENABLE_PROFILING
        ScopedTimer t_cfl("cfl", reg);
#endif
        TimeReal dt = compute_dt_gpu<Real>(m_dev_grid, m_gamma, m_cfl);
        if (m_time + dt > m_t_end) dt = m_t_end - m_time;
        step(dt);
    }
    wall.stop();
    return wall.elapsed_seconds();
}
```

- [ ] **Step 3: Smoke run a single step end-to-end on a tiny grid**

Add a Catch case to `tests/unit/test_gpu_solver_e2e.cpp` (T18 will fully populate the file):

```cpp
TEST_CASE("EulerGpuSolver runs 1 step on Sod 1D bit-exact to CPU", "[gpu][e2e]") {
    // Build CPU solver and GPU solver from same Sod IC.
    // Run 1 step on each. download_host_grid(); memcmp.
}
```

Run, expect PASS.

- [ ] **Step 4: Commit**

```bash
git add src/gpu/euler_gpu_solver.cu tests/unit/test_gpu_solver_e2e.cpp
git commit -m "feat(week6): EulerGpuSolver::step + run; 1-step Sod e2e bit-exact to CPU"
```

---

### Task 17: Wire `device=gpu` in `main.cpp` via `std::variant`

**Files:**
- Modify: `src/main.cpp`
- Create: `experiments/week6/smoke/matrix.json`

- [ ] **Step 1: Replace the D1 stub `throw` with variant dispatch**

In `src/main.cpp`, replace the `throw std::runtime_error("device=gpu dispatch not yet implemented...");` with:

```cpp
#ifdef HRSC_HAS_CUDA
    using SolverV = std::variant<EulerSolver<Real>, EulerGpuSolver<Real>>;
    SolverV solver = (device == "gpu")
        ? SolverV(std::in_place_type<EulerGpuSolver<Real>>,
                  std::move(grid), xmin, ymin, gamma, cfl, t_end, flux, bc_x, bc_y)
        : SolverV(std::in_place_type<EulerSolver<Real>>,
                  std::move(grid), xmin, ymin, gamma, cfl, t_end, flux, bc_x, bc_y);

    double total_s = std::visit([](auto& s) { return s.run(); }, solver);
    std::cerr << "[timing] total_s=" << total_s << "\n";

    // For IO: download to host grid (only D2H of the run).
    Grid2D<Real, EulerNVars> final_grid =
        std::visit([](auto& s) -> Grid2D<Real, EulerNVars> {
            if constexpr (std::is_same_v<std::decay_t<decltype(s)>, EulerGpuSolver<Real>>) {
                return s.download_host_grid();
            } else {
                return s.grid_copy();   // or whatever CPU accessor exposes the host grid
            }
        }, solver);

    // ... existing IO path operates on `final_grid` ...
#else
    // Existing CPU-only path unchanged.
#endif
```

(Adapt to the actual constructor and IO patterns in main.cpp. The CPU `EulerSolver` accessor for the final grid is whatever `main.cpp` already calls today.)

- [ ] **Step 2: Create the WSL smoke matrix**

Create `experiments/week6/smoke/matrix.json` (8 runs):

```json
{
  "experiment": "week6-gpu-smoke-wsl",
  "output_root": "experiments/week6/smoke",
  "runs": [
    {"name": "sod-cpu-strict-d", "binary": "build-cpu-strict-double/hrsc",
     "config": "tests/cases/toro_1d/sod.cfg",
     "extra_cfg": {"device": "cpu", "output_format": "binary"},
     "build": "cpu-strict-double", "output_file": "sod.bin"},
    {"name": "sod-gpu-strict-d", "binary": "build-cuda-double-strict/hrsc",
     "config": "tests/cases/toro_1d/sod.cfg",
     "extra_cfg": {"device": "gpu", "output_format": "binary"},
     "build": "cuda-strict-double", "output_file": "sod.bin"},
    {"name": "sod-cpu-strict-f", "binary": "build-cpu-strict-float/hrsc",
     "config": "tests/cases/toro_1d/sod.cfg",
     "extra_cfg": {"device": "cpu", "output_format": "binary"},
     "build": "cpu-strict-float", "output_file": "sod.bin"},
    {"name": "sod-gpu-strict-f", "binary": "build-cuda-float-strict/hrsc",
     "config": "tests/cases/toro_1d/sod.cfg",
     "extra_cfg": {"device": "gpu", "output_format": "binary"},
     "build": "cuda-strict-float", "output_file": "sod.bin"},
    {"name": "lw3-cpu-strict-d", "binary": "build-cpu-strict-double/hrsc",
     "config": "tests/cases/liska_wendroff_2d/config3_n200.cfg",
     "extra_cfg": {"device": "cpu", "output_format": "binary"},
     "build": "cpu-strict-double", "output_file": "lw3.bin"},
    {"name": "lw3-gpu-strict-d", "binary": "build-cuda-double-strict/hrsc",
     "config": "tests/cases/liska_wendroff_2d/config3_n200.cfg",
     "extra_cfg": {"device": "gpu", "output_format": "binary"},
     "build": "cuda-strict-double", "output_file": "lw3.bin"},
    {"name": "lw3-cpu-strict-f", "binary": "build-cpu-strict-float/hrsc",
     "config": "tests/cases/liska_wendroff_2d/config3_n200.cfg",
     "extra_cfg": {"device": "cpu", "output_format": "binary"},
     "build": "cpu-strict-float", "output_file": "lw3.bin"},
    {"name": "lw3-gpu-strict-f", "binary": "build-cuda-float-strict/hrsc",
     "config": "tests/cases/liska_wendroff_2d/config3_n200.cfg",
     "extra_cfg": {"device": "gpu", "output_format": "binary"},
     "build": "cuda-strict-float", "output_file": "lw3.bin"}
  ]
}
```

- [ ] **Step 3: Run the smoke matrix; verify all 8 runs succeed**

```bash
python scripts/run_matrix.py experiments/week6/smoke/matrix.json
ls experiments/week6/smoke/runs/
```

Expected: 8 dirs, each with `metadata.json` `return_code: 0`.

- [ ] **Step 4: Manually `md5sum` CPU vs GPU same-precision pairs**

```bash
md5sum experiments/week6/smoke/runs/sod-cpu-strict-d/sod.bin \
       experiments/week6/smoke/runs/sod-gpu-strict-d/sod.bin
md5sum experiments/week6/smoke/runs/lw3-cpu-strict-d/lw3.bin \
       experiments/week6/smoke/runs/lw3-gpu-strict-d/lw3.bin
```

Expected: Sod hashes may differ (allowed under §4.5 ULP gate); LW3 hashes same. The proper gate is run via `float_regression_report.py --mode device` in T23 — md5 here is just a quick first read.

- [ ] **Step 5: Verify G5 — default cpu path is byte-identical to a Week 5 reference**

Pick a stable cfg that existed in Week 5 (e.g. `tests/cases/toro_1d/sod.cfg`), run `./build-double/hrsc <cfg>` (the *non-strict* legacy build), and confirm md5 of output matches the Week 5 commit `cda04f3` reference. Record the reference md5 in `docs/week6/week6-verification.md` (T29).

- [ ] **Step 6: Commit**

```bash
git add src/main.cpp experiments/week6/smoke/matrix.json
git commit -m "feat(week6): main.cpp variant dispatch device=gpu; WSL smoke matrix"
```

---

### Task 18: `tests/unit/test_gpu_solver_e2e.cpp` — full 4-case end-to-end

**Files:**
- Modify: `tests/unit/test_gpu_solver_e2e.cpp` (expand from T16's stub to 4 cases)

- [ ] **Step 1: Add the 4 cases** (Sod 1D 1 step, Sod 1D 10 step, LW Config 3 n=64 5 step, LW Config 3 n=200 1 step). Each compares CPU vs GPU `download_host_grid()` under strict-IEEE; threshold is per design §4.5 (16 ULP for general cases, 4 ULP for stationary-contact-only).

- [ ] **Step 2: Run, expect PASS.**

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_gpu_solver_e2e.cpp
git commit -m "test(week6): GPU solver e2e 4-case suite (Sod + LW3, 1 / 5 / 10 steps)"
```

---

### Task 19: LW Config 4 IC + cfg + Catch test

**Files:**
- Modify: `tests/cases/liska_wendroff_2d/lw_tests.hpp` (add `setup_liska_wendroff_config4`)
- Create: `tests/cases/liska_wendroff_2d/config4_n200.cfg`
- Create: `tests/cases/liska_wendroff_2d/config4_n400.cfg`
- Create: `tests/unit/test_lw_config4.cpp` (2 cases)

- [ ] **Step 1: Look up LW Config 4 IC values** in Liska & Wendroff (2003) — quadrant initial states (ρ, u, v, p). Reuse the same template structure already used by `setup_liska_wendroff_config3` and `..._config6` in `lw_tests.hpp`. (`overall.md` and the Week-5 implementation of Config 6 are the obvious references.)

- [ ] **Step 2: Add the IC function** (mirrors `setup_liska_wendroff_config6`).

- [ ] **Step 3: Add the cfg files** (mirror `config6_n200.cfg`):

```ini
test = lw_config4
solver = hllc
nx = 200
ny = 200
xmin = 0.0
xmax = 1.0
ymin = 0.0
ymax = 1.0
t_end = 0.25       # check Liska & Wendroff for the canonical end time
cfl = 0.4
gamma = 1.4
bc_x = outflow
bc_y = outflow
output_format = binary
output_file = experiments/week6/lw4_n200.bin
```

(Adjust `t_end` to the Liska & Wendroff convention; `bc_x` / `bc_y` likewise.)

- [ ] **Step 4: Add `tests/unit/test_lw_config4.cpp` with 2 cases**

```cpp
TEST_CASE("LW Config 4 IC sample cells match published values", "[lw][lw4]") {
    // Build a small 4x4 grid; setup_liska_wendroff_config4(view, 1.4);
    // assert cell (0,0) is in quadrant III with the published rho/u/v/p
    // ... etc for all four quadrants.
}
TEST_CASE("LW Config 4 runs 1 step without NaN", "[lw][lw4]") {
    // Run EulerSolver<double> for 1 step on n=64; assert no NaN/Inf in grid.
}
```

- [ ] **Step 5: Wire `main.cpp setup_ic` to dispatch `"lw_config4"`**

Add the `else if (test == "lw_config4")` branch alongside the existing `lw_config3` / `lw_config6`.

- [ ] **Step 6: Build + run, expect PASS**

```bash
cmake --build build-cpu-strict-double --target unit_tests
./build-cpu-strict-double/unit_tests "[lw4]" -r compact
./build-cpu-strict-double/hrsc tests/cases/liska_wendroff_2d/config4_n200.cfg
```

- [ ] **Step 7: Commit**

```bash
git add tests/cases/liska_wendroff_2d/lw_tests.hpp \
        tests/cases/liska_wendroff_2d/config4_n200.cfg \
        tests/cases/liska_wendroff_2d/config4_n400.cfg \
        tests/unit/test_lw_config4.cpp \
        src/main.cpp
git commit -m "feat(week6): LW Config 4 IC + cfgs + unit tests"
```

---

## D6 (Sat 2026-05-09) — HLLC, regression mode device, regression matrix run, LW Config 12

### Task 20: GPU HLLC flux kernel + tests (incl. stationary contact)

**Why:** Replaces Rusanov as the default flux scheme inside `sweep_x_gpu` / `sweep_y_gpu`. The kernel itself is a one-line port of `hllc_flux` (already HD_FUNC). The risk is the `S* = 0` stationary-contact edge case (R5).

**Files:**
- Modify: `src/gpu/euler_kernels.cuh` (declare `hllc_flux_gpu_kernel` launcher)
- Modify: `src/gpu/euler_kernels.cu` (define + instantiate)
- Modify: `src/gpu/euler_kernels.cu` `sweep_x_gpu` / `sweep_y_gpu` to dispatch on `FluxScheme::HLLC`
- Create: `tests/unit/test_gpu_hllc.cpp` (5 cases)

- [ ] **Step 1: Write the 5 failing tests**

`tests/unit/test_gpu_hllc.cpp`:

1. Single face (sub-sonic LR states, generic).
2. Sonic point (qL right-going sonic; qR right-going subsonic).
3. **Stationary contact**: `pL == pR`, `uL == uR == 0`, `rhoL != rhoR` → `S* = 0` exact. Compare GPU against CPU bit-equivalent.
4. SL & SR both positive (full left-going fan).
5. 16×16 full-grid sweep using LW Config 3 IC after one step.

- [ ] **Step 2: Run, expect FAIL.**

- [ ] **Step 3: Define the HLLC flux kernel** (mirrors Rusanov from T14 — only the `__device__` callee changes). Important: do not re-derive HLLC; the algebra is in `src/euler/hllc.hpp:17-` and is HD_FUNC-friendly. Just wrap the pure function call inside the kernel.

- [ ] **Step 4: Update `sweep_x_gpu` / `sweep_y_gpu` to branch on `FluxScheme`**

```cpp
if (flux == FluxScheme::HLLC) {
    hllc_flux_gpu_kernel<Real><<<grid, block>>>(qL, qR, flux_out, gamma, ...);
} else {
    rusanov_flux_gpu_kernel<Real><<<grid, block>>>(qL, qR, flux_out, gamma, ...);
}
```

- [ ] **Step 5: Run, expect PASS — all 5 cases bit-exact**

```bash
cmake --build build-cuda-double-strict
./build-cuda-double-strict/unit_tests "[gpu][hllc]" -r compact
```

If the stationary-contact case fails: §4.5 says do not widen the threshold. The two most likely fixes are (a) compiler reordered `<=` vs `<` somewhere — re-check with `objdump` on a CPU strict binary; (b) the HD_FUNC dispatch missed `RIEMANN_STRICT_INEQUALITY` — make sure the GPU build inherits the same `target_compile_definitions` as the CPU build.

- [ ] **Step 6: Commit**

```bash
git add src/gpu/euler_kernels.cuh src/gpu/euler_kernels.cu tests/unit/test_gpu_hllc.cpp
git commit -m "feat(week6): GPU HLLC flux kernel (incl. S*=0) + 5 bit-exact tests"
```

---

### Task 21: `float_regression_report.py --mode {fp,device}`

**Files:**
- Modify: `scripts/regression/float_regression_report.py` (add `--mode` flag + device-mode columns)
- Create: `tests/py/test_float_regression_report_device_mode.py` (3 pytest cases)

- [ ] **Step 1: Write the 3 failing pytest cases**

Create `tests/py/test_float_regression_report_device_mode.py`:

```python
import json
import struct
from pathlib import Path
import numpy as np
import pytest


def _write_dummy_bin(path: Path, arr: np.ndarray) -> None:
    """Write a dummy HRSC binary header + payload mimicking io_helper expectations."""
    # Replace with whatever io_helper.write_binary expects; this is a template.
    raise NotImplementedError("adapt to project's binary header conventions")


def test_device_mode_passes_when_diff_is_8_eps(tmp_path):
    nx = 64
    base = np.linspace(0.5, 1.5, nx, dtype=np.float64)
    cpu_path = tmp_path / "cpu_sod.bin"
    gpu_path = tmp_path / "gpu_sod.bin"
    _write_dummy_bin(cpu_path, base)
    _write_dummy_bin(gpu_path, base + 8 * np.finfo(np.float64).eps * np.abs(base))

    from scripts.regression.float_regression_report import _report_device_pair
    result = _report_device_pair(cpu_path, gpu_path, precision="double")
    assert result["gate_passed"] is True
    assert result["ulp_max"] <= 16


def test_device_mode_fails_when_diff_is_64_eps(tmp_path):
    # ... same scaffolding, larger diff → expect gate_passed=False
    pass


def test_device_mode_csv_columns_complete(tmp_path):
    # Run the CLI end-to-end, parse the produced summary.csv, assert no None
    # in any device-mode column.
    pass
```

(Replace `_write_dummy_bin` with the project's actual `io_helper.write_binary` signature — see `scripts/io_helper.py`.)

- [ ] **Step 2: Run, expect FAIL** (`_report_device_pair` not defined yet).

```bash
pytest tests/py/test_float_regression_report_device_mode.py -v
```

- [ ] **Step 3: Implement `--mode` and `_report_device_pair` in `float_regression_report.py`**

Add `--mode {fp,device}` to the existing argparse setup. When `mode == "device"`, route to a new `_report_device_pair(cpu_path, gpu_path, precision)` function that:

1. Reads both binaries via `io_helper.read_binary`.
2. Computes `linf = max|cpu - gpu|`, `l1 = sum|cpu - gpu| / N`, `linf_a = max|cpu|`, `eps = np.finfo(precision_dtype).eps`.
3. Computes `ulp_max = linf / (eps * linf_a)` (with a divide-by-zero guard mirroring `_safe_ratio`).
4. Computes `philip_ratio = l1 / l1_cpu_minus_exact` (caller-supplied or computed if `--reference exact` is passed).
5. Sets `gate_passed = (ulp_max <= 16.0)` (or `4.0` for stationary-contact, detected via case name).
6. Returns the row dict.

The CSV writer extends columns to: `pair_a, pair_b, precision, l1_a_minus_b, linf_a_minus_b, philip_ratio, ulp_max, gate_passed, notes`.

- [ ] **Step 4: Run, expect PASS — all 3 pytest cases.**

- [ ] **Step 5: Commit**

```bash
git add scripts/regression/float_regression_report.py \
        tests/py/test_float_regression_report_device_mode.py
git commit -m "feat(week6): float_regression_report --mode {fp,device} + 3 pytest cases"
```

---

### Task 22: LW Config 12 IC + cfg + Catch test (mirrors T19)

**Files:** same shape as T19 — `lw_tests.hpp`, two `config12_n*.cfg`, `test_lw_config12.cpp`, `main.cpp setup_ic` dispatch, commit.

- [ ] **Step 1: Add IC + cfgs + unit test + main dispatch + build + run + commit**

(Same step skeleton as T19; replace "config4" with "config12" everywhere; consult Liska & Wendroff Config 12 quadrant states.)

```bash
git add tests/cases/liska_wendroff_2d/lw_tests.hpp \
        tests/cases/liska_wendroff_2d/config12_n200.cfg \
        tests/cases/liska_wendroff_2d/config12_n400.cfg \
        tests/unit/test_lw_config12.cpp src/main.cpp
git commit -m "feat(week6): LW Config 12 IC + cfgs + unit tests"
```

---

### Task 23: D6 regression matrix run + summary

**Files:**
- Create: `experiments/week6/regression/matrix.json` (8 runs — same as smoke but without `output_format` overrides if smoke already produced bins)
- Run: `python scripts/run_matrix.py experiments/week6/regression/matrix.json`
- Run: `python scripts/regression/float_regression_report.py --mode device ... → summary.{md,json,csv}`

- [ ] **Step 1: Author `experiments/week6/regression/matrix.json`** — mirror `experiments/week6/smoke/matrix.json` from T17 but pointed at `output_root: experiments/week6/regression`.

- [ ] **Step 2: Run the matrix**

```bash
python scripts/run_matrix.py experiments/week6/regression/matrix.json
ls experiments/week6/regression/runs/
```

- [ ] **Step 3: Run the regression report**

```bash
python scripts/regression/float_regression_report.py \
    --mode device \
    --inputs experiments/week6/regression/runs/*-cpu-strict-*/[sl]*.bin \
             experiments/week6/regression/runs/*-gpu-strict-*/[sl]*.bin \
    --reference exact \
    --output experiments/week6/regression/summary
```

(Adjust the input glob to whatever the script's CLI expects; pair-up logic likely comes from filenames.)

- [ ] **Step 4: Verify gate_passed = True for all 4 pairs**

```bash
cat experiments/week6/regression/summary.md
# All rows should have gate_passed=✓.
```

- [ ] **Step 5: Commit**

```bash
git add experiments/week6/regression/matrix.json \
        experiments/week6/regression/summary.{md,json,csv}
git commit -m "exp(week6): WSL CPU-vs-GPU regression matrix (4 pairs all gate_passed)"
```

---

## D7 (Sun 2026-05-10) — CSC migration + closeout

### Task 24: Push branch to remote

- [ ] **Step 1: Push**

```bash
git push origin week4-implementation
```

Expected: 30+ commits land on remote.

---

### Task 25: SSH to CSC, pull, run `build_gpu_csc.sh`

(Assumes `scripts/cluster/build_gpu_csc.sh` was authored on D1 OR is created here as part of T26. If T26 hasn't run, do T26 Step 1 first locally, commit, push, then come back here.)

---

### Task 26: `scripts/cluster/build_gpu_csc.sh` + `run_gpu_smoke.slurm` + `csc_smoke/matrix.json`

**Files:**
- Create: `scripts/cluster/build_gpu_csc.sh`
- Create: `scripts/cluster/run_gpu_smoke.slurm`
- Create: `experiments/week6/csc_smoke/matrix.json`

- [ ] **Step 1: Author `scripts/cluster/build_gpu_csc.sh`** (verbatim from `docs/week6/week6-design.md` §8.2; replace `cuda/12.4`, `gcc/11`, etc. with the modules captured in `csc_gpu_environment.md`).

- [ ] **Step 2: Author `scripts/cluster/run_gpu_smoke.slurm`** (verbatim from §8.3; replace `--partition=ampere` with the probed `--partition=csc-mphil-gpu`; keep `--gres=gpu:1`, which was confirmed by the D1 allocation probe).

- [ ] **Step 3: Author `experiments/week6/csc_smoke/matrix.json`** (4 GPU rows from §8.4).

- [ ] **Step 4: Make scripts executable**

```bash
chmod +x scripts/cluster/build_gpu_csc.sh
```

- [ ] **Step 5: Commit**

```bash
git add scripts/cluster/build_gpu_csc.sh scripts/cluster/run_gpu_smoke.slurm \
        experiments/week6/csc_smoke/matrix.json
git commit -m "feat(week6): CSC GPU build + SLURM smoke scripts; csc_smoke matrix"
git push origin week4-implementation
```

---

### Task 27: Execute on CSC — build, sbatch, watch

- [ ] **Step 1: SSH + pull + build**

```bash
ssh csc-login
cd ~/floatpoint && git pull
bash scripts/cluster/build_gpu_csc.sh both
ls -d build-cuda-*-strict/
```

- [ ] **Step 2: Login-node sanity (non-GPU portion of the test suite)**

```bash
./build-cuda-double-strict/unit_tests "[gpu][layout]" -r compact || true
# Expected: layout test runs OK on login (no GPU ops on host CPU). If a [gpu]
# tag triggers a CUDA call, it'll fail loudly — note the failure in the
# closeout summary; this is informative, not a blocker.
```

- [ ] **Step 3: Submit smoke matrix**

```bash
mkdir -p experiments/week6/csc_smoke/slurm_logs
sbatch scripts/cluster/run_gpu_smoke.slurm
squeue -u $USER
```

- [ ] **Step 4: Wait for completion** (use `squeue -u $USER` polling; do not block calendar — meanwhile drafting `week6-summary.md`).

If the queue does not drain by D7 EOD: do not block on it. Mark `csc_run_pending` and proceed to T29 / T30 — design §8.6 / G4-fallback explicitly permits this.

- [ ] **Step 5: On completion, inspect logs**

```bash
cat experiments/week6/csc_smoke/slurm_logs/*.out | head -60
ls experiments/week6/csc_smoke/runs/
```

Each of the 4 runs should have its `metadata.json` `return_code: 0` and a `*.bin` payload.

---

### Task 28: rsync CSC artefacts to laptop, run regression report

- [ ] **Step 1: rsync from CSC to laptop**

```bash
# On laptop:
rsync -avz csc-login:~/floatpoint/experiments/week6/csc_smoke/ \
           experiments/week6/csc_smoke/
ls experiments/week6/csc_smoke/runs/
```

- [ ] **Step 2: Run regression report — CSC GPU vs WSL CPU strict**

```bash
python scripts/regression/float_regression_report.py \
    --mode device \
    --cpu  experiments/week6/regression/runs/sod-cpu-strict-d/sod.bin \
    --gpu  experiments/week6/csc_smoke/runs/sod-gpu-csc-d/sod.bin \
    --reference exact --precision double \
    --output experiments/week6/csc_smoke/summary_sod_d
# Repeat for sod-f, lw3-d, lw3-f.
# Or wrap into a small driver shim that loops over the 4 pairs and writes
# experiments/week6/csc_smoke/summary.{md,json,csv}.
```

- [ ] **Step 3: Inspect CSC-vs-WSL diff**

```bash
cat experiments/week6/csc_smoke/summary.md
```

Expected: each row shows `host=csc-gpu` vs `host=wsl-cpu`, `arch=sm_XX`, with `ulp_max` value populated. **Per design R7, a non-zero `ulp_max` here is a research data point, not a bug.** Do not force gate_passed; record the actual value.

- [ ] **Step 4: Commit the artefacts**

```bash
git add experiments/week6/csc_smoke/runs/  # only if not gitignored
git add experiments/week6/csc_smoke/summary*
git commit -m "exp(week6): CSC GPU smoke summary (4 runs CSC vs local CPU strict)"
```

If `experiments/week6/csc_smoke/runs/` is gitignored (large bins), commit only `summary.{md,json,csv}` plus `slurm_logs/*.out`.

---

### Task 29: `docs/week6/week6-verification.md`

**Files:**
- Create: `docs/week6/week6-verification.md`

- [ ] **Step 1: Author the doc** modeled on `docs/week5/week5-verification.md`. Sections:

```markdown
# Week 6 Verification Recipe

## Phase A: Build matrix (CPU strict + CUDA strict)

```bash
# Local WSL:
cmake -B build-cpu-strict-double  -G Ninja -DFLOAT_PRECISION=double -DSTRICT_IEEE=ON ...
cmake -B build-cpu-strict-float   -G Ninja -DFLOAT_PRECISION=float  -DSTRICT_IEEE=ON ...
cmake -B build-cuda-double-strict -G Ninja -DFLOAT_PRECISION=double -DSTRICT_IEEE=ON -DENABLE_CUDA=ON ...
cmake -B build-cuda-float-strict  -G Ninja -DFLOAT_PRECISION=float  -DSTRICT_IEEE=ON -DENABLE_CUDA=ON ...

for D in build-cpu-strict-double build-cpu-strict-float \
         build-cuda-double-strict build-cuda-float-strict; do
    cmake --build "$D" -j
done

# CSC:
ssh csc-login && cd ~/floatpoint
bash scripts/cluster/build_gpu_csc.sh both
```

Expected end-state: 4 local + 2 CSC build dirs all green.

## Phase B: Unit tests

```bash
./build-cpu-strict-double/unit_tests   -r compact
./build-cuda-double-strict/unit_tests  "[gpu]"  -r compact
./build-cuda-float-strict/unit_tests   "[gpu]"  -r compact
```

Expected: all green; including the 39 new `[gpu]` cases.

## Phase C: Local WSL smoke matrix

```bash
python scripts/run_matrix.py experiments/week6/smoke/matrix.json
python scripts/regression/float_regression_report.py --mode device ... \
    --output experiments/week6/regression/summary
cat experiments/week6/regression/summary.md
```

Expected: 4 pairs, all gate_passed=✓.

## Phase D: CSC smoke matrix

```bash
ssh csc-login
cd ~/floatpoint && git pull
sbatch scripts/cluster/run_gpu_smoke.slurm
squeue -u $USER

# After completion, on laptop:
rsync -avz csc-login:~/floatpoint/experiments/week6/csc_smoke/ \
           experiments/week6/csc_smoke/
python scripts/regression/float_regression_report.py --mode device ... \
    --output experiments/week6/csc_smoke/summary
cat experiments/week6/csc_smoke/summary.md
```

Expected: 4 pairs CSC-vs-WSL, ulp_max recorded.

## Reference md5s (G5 byte-identity)

```
<recorded at D1>  build-double/hrsc                 (Week 5 baseline binary)
<recorded at D7>  output of `./build-double/hrsc tests/cases/toro_1d/sod.cfg`
```

## Phase E: G6 timing emit

```bash
HRSC_ENABLE_PROFILING=ON ./build-prof/hrsc tests/cases/toro_1d/sod.cfg 2>&1 | grep timing
```

Expected: 5 phase lines (`bc`, `cfl`, `flux`, `update`, total).
```

- [ ] **Step 2: Commit**

```bash
git add docs/week6/week6-verification.md
git commit -m "docs(week6): Week 6 manual verification recipe (Phase A-E)"
```

---

### Task 30: `docs/week6/week6-summary.md` + `docs/INDEX.md` update

**Files:**
- Create: `docs/week6/week6-summary.md`
- Modify: `docs/INDEX.md` (Week 6 row → live links)

- [ ] **Step 1: Author `week6-summary.md`** — modeled on `docs/week5/week5-summary.md`. Sections:

```markdown
# Week 6 Summary

**Calendar:** 2026-05-04 → 2026-05-10
**Branch:** `week4-implementation`

## Acceptance gates (G1-G8)

| Gate | Status | Evidence |
|---|---|---|
| G1. Strict + CUDA builds clean | ✅ | `build-{cpu,cuda}-*-strict/` × 4 |
| G2. Unit tests green        | ✅ | 39 new [gpu] cases + Week 5 [gpu] roundtrip; total NN cases / NN assertions |
| G3. Local WSL smoke green   | ✅ | `experiments/week6/regression/summary.md`: 4/4 gate_passed |
| G4. CSC smoke executed      | ✅ or csc_run_pending → Week 7 D1 |
| G5. cfg-default byte-id     | ✅ | md5 ref in `week6-verification.md` |
| G6. Timer 5-phase split     | ✅ | `[timing] phase=bc/cfl/flux/update/total` |
| G7. LW Config 4 / 12 landed | ✅ | unit tests + cfgs + IC samples |
| G8. Documentation closed    | ✅ | this doc + verification + csc env + INDEX |

## Deliverables (commit summary)

| Day | Tasks | Commits (oneline) |
|---|---|---|
| D1 | T1-T4 | (paste `git log --oneline 5c5109b..HEAD` filtered to D1) |
| D2 | T5-T8 | ... |
| ... |

## Risk register — actuals

| ID | Outcome |
|---|---|
| R1 WSL CUDA driver | (no issue / fixed by ...) |
| R2 GpuGrid stride  | (test_gpu_grid_layout green) |
| R3 atomicMin UB    | compute-sanitizer clean |
| R4 OpenMP FMA leak | objdump confirmed no vfmadd in cpu-strict-double |
| R5 HLLC S*=0 GPU   | stationary-contact case green |
| R6 CSC config drift | (probe matched) |
| R7 CSC vs WSL diff  | recorded as data point: ulp_max=NN for sod-d, NN for lw3-d |
| R8 Tests on CI     | n/a (single-developer) |

## Carry-forward

- HLLC `<=` vs `<` GPU toggle → Week 7 systematic study
- Fast-math GPU matrix → Week 7
- Verificarlo `vfc_precexp` / unstable-branch → Week 14
- Shock-bubble GPU → Week 7
- GPU MHD → Week 14
```

- [ ] **Step 2: Update `docs/INDEX.md` Week 6 row**

In §2 of `docs/INDEX.md`, change the line:
```
| 6 | (pending) | (pending) | (none) |
```
to:
```
| 6 | [week6-plan.md](week6/week6-plan.md) | [week6-summary.md](week6/week6-summary.md) | (none) |
```

Also add to §2 below the Week 5 / Week 6 bridge listings:

```markdown
Week 6 deliverables:
- [week6-design.md](week6/archive/week6-design.md) — design + decisions
- [week6-verification.md](week6/archive/week6-verification.md) — Phase A-E reproduction recipe
- [csc_gpu_environment.md](week6/archive/csc_gpu_environment.md) — D1 CSC probe
```

Update the footer date stamp.

- [ ] **Step 3: Final commit**

```bash
git add docs/week6/week6-summary.md docs/INDEX.md
git commit -m "docs(week6): closeout — summary + INDEX live links"
git push origin week4-implementation
```

- [ ] **Step 4: (optional) Tag the closeout**

```bash
git tag week6-complete-2026-05-10
git push origin week6-complete-2026-05-10
```

---

## Self-review

1. **Spec coverage:**
   - §1.1 In-scope items 1-9 → Tasks T1-T30 (matrix above maps each); ✅
   - §2 calendar D1-D7 → grouped tasks present; ✅
   - §3 architecture → reflected in T2, T16, T17 file structure & class shape; ✅
   - §4 determinism → T4 (build flags), T10 (CFL atomicMin), T20 (HLLC S*=0), T21 (gate threshold in CSV); ✅
   - §5 build → T2 + T4 cover CMake + build_all.sh; ✅
   - §6 regression schema → T21 + T23; ✅
   - §7 test plan (39 cases) → T5 (3) + T6/T7/T8 (6) + T10 (4) + T11 (3) + T12 (3) + T13 (3) + T14 (4) + T20 (5) + T18 (4) + T19 (2) + T22 (2) = 39 ✓; ✅
   - §8 CSC → T3 (probe), T26-T28 (build / submit / rsync); ✅
   - §9 risk register & gates → T29 (verification doc) + T30 (summary records gate outcomes); ✅

2. **Placeholder scan:** No `TBD` / `TODO` placeholders in plan text. Ports of long algebra (HLLC, MUSCL) reference exact source file + line range rather than re-deriving inline — acceptable per "DRY" rule. The `<fill>` markers in §T3 csc_gpu_environment.md template are intentional probe slots filled at runtime, not plan placeholders.

3. **Type consistency:** Function names cross-checked: `apply_outflow_bc_gpu` (T6), `apply_periodic_bc_gpu` (T7), `apply_reflective_bc_gpu` (T8), `compute_dt_gpu` (T10), `muscl_reconstruct_gpu` (T11), `hancock_predict_gpu` (T12), `apply_update_gpu` (T13), `rusanov_flux_gpu` (T14), `sweep_x_gpu` / `sweep_y_gpu` (T15), `hllc_flux_gpu_kernel` (T20). All consistent. `EulerGpuSolver<Real>` shape matches T2 declaration through T16 implementation.

4. **Test count consistency:** 39 [gpu] cases promised in design §7.1; plan delivers 39 ✓.

5. **One issue spotted and fixed:** T17 Step 1 CSC-vs-WSL md5 claim was over-strong (md5 of binaries with even 1-ULP diff will differ). Reworded to "first read; proper gate is T23".

---
