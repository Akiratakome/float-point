# Week 6 Design — GPU Euler Solver + CSC Migration

**Date:** 2026-05-03
**Branch:** `week4-implementation`
**Calendar:** 2026-05-04 (Mon) → 2026-05-10 (Sun)
**Drives:** `week6-plan.md` (next step, via writing-plans skill)
**Supersedes / extends:** [`week5_to_week6_bridge.md`](week5_to_week6_bridge.md)

---

## 0. Decision log

Captured during brainstorming on 2026-05-03. Each decision is referenced from the relevant section.

| # | Question | Decision |
|---|---|---|
| Q1 | CPU↔GPU determinism gate | **B** — sweep / update kernels deterministic; CFL reduction uses `atomicMin` on bit-reinterpret of positive floats (deterministic because positive-float bit pattern is monotonic in integer order). Equivalent to `overall.md` "no atomics" intent. |
| Q2 | GPU flux-scheme scope | **B** — Rusanov first to validate the full reconstruct→predict→CFL→update pipeline; HLLC flux kernel replaces the Rusanov flux kernel afterwards. Pipeline is written once. |
| Q3 | CSC migration scope in Week 6 | **A** — full migration: build script + SLURM script in git, Sod 1D + LW Config 3 same-precision diff actually executed on CSC. Completeness preferred over conserving HLLC time. |
| Q4 | Carry-over closure | **A** — LW Config 4 / 12 ICs + cfgs, ScopedTimer 5-way split (`flux` / `update` added), CPU-vs-GPU regression schema first-class **into Week 6**; Verificarlo `vfc_precexp` and unstable-branch detection **deferred to Week 14**. |
| Q5 | Reference build for the regression gate | **A** — strict-IEEE on both sides (`-ffp-contract=off -fno-fast-math` on CPU; `--fmad=false --use_fast_math=NO --prec-div=true --prec-sqrt=true` on GPU) is the sole Week 6 baseline. Fast-math / FMA matrix is Week 7's systematic study. |
| Sequencing | Implementation order | **Approach 2 + Day-1 CSC probe** — horizontal layers (one kernel at a time, each with a Catch2 `[gpu]` unit test) plus a Day 1 cfg-dispatch stub and a Day 1 CSC SSH/`nvcc` probe to surface toolchain issues immediately. |
| §3.2(a) | Solver dispatch | `std::variant<EulerSolver<Real>, EulerGpuSolver<Real>>` (static polymorphism, no vtable across host/device boundary). |
| §3.2(c) | Host-device data ownership | D2H copy only at IO / regression sample / progress-tick boundaries. Inner step loop closes on device. |
| §3.2(d) | Stream policy | Default stream throughout Week 6. Multi-stream / overlap is a Week 7+ perf optimisation. |
| §5.2 hardening | Strict-aliasing | Add `-fno-strict-aliasing` to both `hrsc_apply_strict_ieee_cpu` and `-Xcompiler=-fno-strict-aliasing` in `hrsc_apply_strict_ieee_cuda`. Protects bit-pattern compare paths in regression code from aggressive `-O2` aliasing assumptions. |
| §5.5 hardening | Compiler probe | `build_all.sh` probes `-ffp-contract=off` (CPU) and `--fmad=false` (nvcc) before adding strict variants; on probe failure, skip with a loud warning rather than silently fall back. |
| §7.1 add-on | Layout test | New file `test_gpu_grid_layout.cpp` (3 cases) sits before any BC kernel work. Catches `Grid2D` vs `GpuGrid` row-stride drift early — a class of bug that would otherwise present as inscrutable ULP diffs. |

---

## 1. Scope & non-goals

### 1.1 In scope (Week 6 must-deliver)

1. CUDA Euler GPU solver: BC, CFL reduction, MUSCL reconstruction, Hancock predictor, Rusanov flux, HLLC flux, conservative update, orchestration.
2. `main.cpp` cfg dispatch: new `device = cpu | gpu` key (defaults to `cpu`; existing builds remain byte-for-byte identical).
3. CMake: `cmake/CUDASetup.cmake` completed; `cmake/CompilerFlags.cmake` gains strict-IEEE helpers; `scripts/build_all.sh` adds `cuda-{double,float}-strict` and `cpu-strict-{double,float}` build labels (gated on `nvcc` and `-ffp-contract=off` probe).
4. Catch2 `[gpu]` per-kernel unit tests (single cell + 16×16 + 33×17 grid; CPU strict-IEEE oracle, bit-equivalent under §4.5 thresholds).
5. CPU-vs-GPU end-to-end regression: Sod 1D + LW Config 3 (n=200) × {float, double}; `scripts/regression/float_regression_report.py` extended with `--mode {fp, device}` (first-class, not a hack).
6. LW Config 4 + LW Config 12: ICs + cfg files + Catch2 unit tests (modeled on Config 3 / 6).
7. `ScopedTimer` 5-way phase split: add `flux` and `update` phases.
8. CSC GPU migration: `scripts/cluster/build_gpu_csc.sh` + `scripts/cluster/run_gpu_smoke.slurm`; Sod + LW Config 3 same-precision diff actually executed on CSC.
9. Outputs landed under `experiments/week6/`: `smoke/`, `regression/`, `csc_smoke/` with `summary.{md,json}`.

### 1.2 Out of scope (Week 6 explicitly does not touch)

- HLLC `<=` vs `<` GPU toggle experiment (Week 7 systematic study).
- Fast-math / `--use_fast_math` matrix on GPU (Week 7).
- Verificarlo `vfc_precexp` / unstable-branch detection (Week 14, per Q4).
- Anything MHD on GPU (Week 14).
- Quad precision on GPU (never, per `overall.md`).
- AMReX or external library benchmarking.
- Shock-bubble GPU validation (Week 7).

### 1.3 Defaults that may be revisited at review

- WSL CUDA architecture: `CMAKE_CUDA_ARCHITECTURES=native` (CMake ≥ 3.24 auto-detect).
- CSC CUDA architecture: placeholder `sm_80` (Ampere); D1 probe overwrites in `csc_gpu_environment.md`.
- Block / grid: `dim3 block(16, 16) = 256` threads/block, `dim3 grid((nx+15)/16, (ny+15)/16)`. Single kernel shape for 1D and 2D (1D degenerates to a one-row grid).
- Ghost cells: 2 layers per side (unchanged from CPU).
- cfg key: `device = cpu | gpu`, default `cpu`.

---

## 2. Calendar (7 days)

Branch continues `week4-implementation` per the Week 5 → Week 6 bridge.

| Day | Date | Main line | Side line | EOD deliverable |
|---|---|---|---|---|
| **D1 Mon** | 05-04 | (a) `device=cpu\|gpu` cfg dispatch + GPU dummy stub + Catch2 dispatch test; (b) `cmake/CompilerFlags.cmake` strict-IEEE preset for CUDA; (c) `build-cuda-{double,float}-strict` compile clean on WSL; Week 5 `[gpu]` roundtrip still passes | **CSC probe**: SSH + `module avail cuda` + `nvcc --version` + login-node hello-world CUDA build + one `srun --gres=gpu:1` to confirm partition / queue name; populate `docs/week6/csc_gpu_environment.md` | Dispatch path live; CSC toolchain documented; GPU build dirs reproducible |
| **D2 Tue** | 05-05 | First: `test_gpu_grid_layout.cpp` (3 cases) — must pass before any BC kernel work (R2 mitigation). Then **BC kernels**: outflow / periodic / reflective × {X, Y}; each kernel paired with a Catch2 `[gpu]` case using `apply_*_bc` as oracle, bit-equivalent | — | Layout safety net green; 6 BC kernels + 6 unit tests; LW Config 3 IC after one BC pass on GPU is byte-identical to CPU |
| **D3 Wed** | 05-06 | **CFL reduction kernel**: block tree-reduce + `atomicMin` on `__float_as_int` of positive floats; Catch2 `[gpu]` case validates against CPU `compute_dt` bit-equivalence on grids 7×3, 16×16, 257×129, 1024×1024 (deliberately non-power-of-two), and a 100-iteration run-to-run identity test | (b) Stub `flux` and `update` phases into `ScopedTimer` (CPU side first; GPU side connects D5) | CFL kernel done; CPU/GPU dt bit-equivalent; Timer 5-phase framework ready |
| **D4 Thu** | 05-07 | **MUSCL reconstruction + Hancock predictor kernels** (minmod limiter only; van Leer / MC follow later). CPU `muscl.hpp` / `hancock.hpp` are already `__host__ __device__`-friendly pure functions — reuse the algebra. Catch2 `[gpu]` cases: single cell + 16×16 + 33×17 | — | reconstruct + predict kernels done; slope / qL / qR triplet bit-equivalent to CPU |
| **D5 Fri** | 05-08 | (a) **Rusanov flux kernel** (no branches) + **conservative update kernel**; (b) **`EulerGpuSolver<Real>` orchestration** (step loop + alternating Lie splitting); (c) `main.cpp` plumbs `device=gpu` to `EulerGpuSolver`; (d) end-to-end Sod 1D + LW Config 3 emit binary; CPU strict-IEEE diff under §4.5 threshold; (e) **wire ScopedTimer GPU-side `bc` / `cfl` / `flux` / `update` phases inside `EulerGpuSolver` step loop** (host-side `cudaDeviceSynchronize()` boundary timing is sufficient — no per-kernel cudaEvent overhead) | LW Config 4 IC + cfg + Catch2 unit test (Config 3 / 6 template) | Rusanov GPU end-to-end; Sod 1D float / double × CPU/GPU diff ≤ 16 ULP; LW Config 4 CPU baseline runs; GPU `[timing] phase=…` lines emit |
| **D6 Sat** | 05-09 | (a) **HLLC flux kernel** (drop-in replacement for Rusanov flux; CPU `hllc.hpp` is `__host__ __device__`-friendly). Catch2 `[gpu]` case includes the stationary-contact `S*=0` edge case. (b) **CPU-vs-GPU regression schema first-class**: `scripts/regression/float_regression_report.py` gains `--mode {fp, device}`; both fp (`float vs double`) and device (`cpu vs gpu`) are first-class row types | LW Config 12 IC + cfg + Catch2 unit test | HLLC GPU runs; regression report emits device mode; CPU/GPU diff table committed under `experiments/week6/regression/` |
| **D7 Sun** | 05-10 | **CSC migration**: (a) `scripts/cluster/build_gpu_csc.sh` builds on CSC into `~/floatpoint/build-cuda-{double,float}-strict/`; (b) `scripts/cluster/run_gpu_smoke.slurm` submits 1 node × 1 GPU running `experiments/week6/csc_smoke/matrix.json` (Sod 1D + LW Config 3 n=200 × {float, double} = 4 runs); (c) rsync binaries back, run regression report, land `experiments/week6/csc_smoke/summary.{md,json}` | Draft `docs/week6/week6-summary.md` (deliverables only, no narrative) | CSC GPU 4 runs done; CPU(local) vs GPU(CSC) and CPU(local) vs GPU(WSL) both in summary; Week 6 closeout |

### 2.1 Buffer / fallback policy

- Any kernel blocked ≥ ½ day → file an entry into the in-doc Risk register immediately; do not silently slip.
- D7 CSC queue not draining → SLURM script + build script must still be committed (replayable when queue clears); `summary.md` carries `csc_run_pending`.
- HLLC GPU not done by D6 EOD → Rusanov GPU already satisfies the "GPU works" milestone (Approach 2's risk-isolation rationale); HLLC slips to Week 7 D1.
- LW Config 4 / 12 not done by D5 / D6 EOD → push to Week 7 (`overall.md` marks them "if needed", non-blocking).

---

## 3. Code organisation

### 3.1 File tree (additions / edits)

```
src/
├── core/                              [unchanged]
├── euler/                             [unchanged]
└── gpu/
    ├── cuda_utils.cuh                 [unchanged — Week 5]
    ├── gpu_grid.cuh                   [unchanged — Week 5]
    ├── gpu_smoke.cu                   [unchanged — Week 5 roundtrip]
    ├── euler_kernels.cuh              [EXTEND]   BC + CFL + reconstruct + predict + flux + update kernels (templated on Real)
    ├── euler_kernels.cu               [NEW]      explicit instantiation for float / double
    ├── euler_gpu_solver.hpp           [NEW]      EulerGpuSolver<Real> interface (mirrors EulerSolver shape)
    └── euler_gpu_solver.cu            [NEW]      orchestration + step loop + explicit instantiation

cmake/
├── CUDASetup.cmake                    [EXTEND]   CMAKE_CUDA_ARCHITECTURES policy; CUDA_SEPARABLE_COMPILATION
├── CompilerFlags.cmake                [EXTEND]   hrsc_apply_strict_ieee_{cpu,cuda}() helpers
└── PrecisionConfig.cmake              [unchanged]

src/main.cpp                           [EXTEND]   parse `device` cfg key; under ENABLE_CUDA, dispatch via std::variant

tests/
├── unit/
│   ├── test_gpu_grid_layout.cpp       [NEW]      stride / alignment safety (3 cases)
│   ├── test_gpu_bc.cpp                [NEW]      BC kernels (6 cases)
│   ├── test_gpu_cfl.cpp               [NEW]      CFL bit-equivalence (4 cases)
│   ├── test_gpu_reconstruct.cpp       [NEW]      MUSCL reconstruction (3 cases)
│   ├── test_gpu_hancock.cpp           [NEW]      Hancock predictor (3 cases)
│   ├── test_gpu_rusanov.cpp           [NEW]      Rusanov flux (4 cases)
│   ├── test_gpu_hllc.cpp              [NEW]      HLLC flux incl. S*=0 (5 cases)
│   ├── test_gpu_update.cpp            [NEW]      conservative update (3 cases)
│   ├── test_gpu_solver_e2e.cpp        [NEW]      end-to-end N-step diff (4 cases)
│   ├── test_lw_config4.cpp            [NEW]      LW Config 4 IC sanity (2 cases)
│   └── test_lw_config12.cpp           [NEW]      LW Config 12 IC sanity (2 cases)
├── cases/
│   └── liska_wendroff_2d/
│       ├── lw_tests.hpp               [EXTEND]   setup_liska_wendroff_config{4,12}
│       ├── config4_n{200,400}.cfg     [NEW]
│       └── config12_n{200,400}.cfg    [NEW]
└── py/
    └── test_float_regression_report_device_mode.py   [NEW]

scripts/
├── build_all.sh                       [EXTEND]   strict variants gated on nvcc + ffp-contract probe
├── regression/
│   └── float_regression_report.py     [EXTEND]   --mode {fp,device}
└── cluster/
    ├── build_gpu_csc.sh               [NEW]      module load + cmake + ninja on CSC
    └── run_gpu_smoke.slurm            [NEW]      SLURM template (1 GPU, 1 hour, Sod + LW3)

experiments/
└── week6/
    ├── smoke/                         local WSL GPU smoke (8 runs)
    │   └── matrix.json
    ├── regression/                    CPU(strict)-vs-GPU(WSL) summary.{csv,md,json}
    └── csc_smoke/                     CSC 4 runs + summary.{md,json}
        ├── matrix.json
        └── slurm_logs/

docs/
└── week6/
    ├── week5_to_week6_bridge.md       [unchanged]
    ├── week6-design.md                [THIS FILE]
    ├── csc_gpu_environment.md         [NEW, D1]
    ├── week6-plan.md                  [NEW, post-design via writing-plans]
    ├── week6-verification.md          [NEW, D7]
    └── week6-summary.md               [NEW, D7]
```

### 3.2 Architectural decisions

**(a) `EulerGpuSolver<Real>` mirrors `EulerSolver<Real>`** — same public surface (`step(dt)`, `run_until(t_end)`, `current_time()`), same construction parameters (grid, cfg, BC config). `main.cpp` chooses between them via `std::variant`. `std::visit` provides static dispatch — no vtable, no host/device boundary issues, mirrors the explicit `Grid2D` / `GpuGrid` separation (rationale per Q-A user response on §3.2(a)).

**(b) Kernel explicit instantiation** — `euler_kernels.cu` ends with `template __global__ void <kernel>(...)` instantiations for `float` and `double`. `euler_gpu_solver.cu` likewise instantiates `EulerGpuSolver<float>` / `EulerGpuSolver<double>`. Matches the existing CPU pattern (split `euler_solver.cpp` for explicit instantiation).

**(c) Data ownership** — `EulerGpuSolver` owns a `GpuGrid<Real, NVars>` (device working set) and holds a host-side reference to `Grid2D` only for D2H copies at step boundaries (IO / regression sampling / progress ticks). The inner step loop closes on the device — no per-step D2H. PCIe bandwidth is the first GPU performance killer; closing the loop on device is the prerequisite for any future perf characterization (rationale per Q-A user response on §3.2(b)).

**(d) Stream strategy** — default stream throughout Week 6. Implicit synchronisation eliminates a class of race conditions that would otherwise undermine the §4.5 ULP gate. Multi-stream / overlap is left to Week 7+ perf work, when the determinism baseline is already proven (rationale per Q-A user response on §3.2(c)).

**(e) Block / grid dims** — single shape: `dim3 block(16, 16)`, `dim3 grid((nx+15)/16, (ny+15)/16)`. 1D cases (`ny=1`) degenerate naturally to a one-row block grid; no 1D-specific kernel.

---

## 4. Determinism contract

This section is the precise specification for "CPU vs GPU same-precision diff ≤ ULP-level".

### 4.1 Build flag matrix (sole Week 6 baseline)

| Build dir | Purpose | Key flags |
|---|---|---|
| `build-cpu-strict-double` | CPU strict-IEEE double reference | `-O2 -ffp-contract=off -fno-fast-math -fexcess-precision=standard -fno-unsafe-math-optimizations -fno-strict-aliasing`; OpenMP enabled (min reduction is associative — safe) |
| `build-cpu-strict-float`  | CPU strict-IEEE float reference | as above with `-DFLOAT_PRECISION=float` |
| `build-cuda-double-strict` | GPU strict-IEEE double | host-side as cpu-strict; nvcc: `--fmad=false --ftz=false --prec-div=true --prec-sqrt=true --use_fast_math=NO`, no implicit `-O3` fast intrinsics; `-Xcompiler="-O2 -ffp-contract=off -fno-fast-math -fno-strict-aliasing"` |
| `build-cuda-float-strict`  | GPU strict-IEEE float | as above with `-DFLOAT_PRECISION=float` |

The pre-existing `build-double` / `build-float` are **not modified** — Week 5 unit tests and Week 4 regression artefacts must remain reproducible. Strict variants are parallel, additive build dirs.

### 4.2 Kernel-writing constraints (enforced by code review and `cmake/CompilerFlags.cmake` comments)

1. No `__sinf` / `__expf` / `__fdividef` and other intrinsic fast-math functions — use standard `sin`, `exp`, regular division.
2. No explicit `__fmaf_rn` / `__fma_rn` — write `a*b + c` and let the compiler honour `--fmad=false`.
3. No `atomicAdd` for reduction — CFL uses `atomicMin` on bit-reinterpret (§4.3).
4. No warp-shuffle reduce + atomic accumulation (order non-deterministic) — use deterministic block tree-reduce + a single `atomicMin`.
5. No cross-block accumulators in `__shared__`. Inter-block communication only via device global buffers.

### 4.3 Deterministic CFL reduction

Positive floats (including `+0`) have IEEE 754 bit patterns whose `int32` (float) / `int64` (double) reinterpretation is monotonically ordered. Therefore:

```cpp
__device__ inline int32_t dt_to_int(float dt)  { return __float_as_int(dt); }
__device__ inline float   int_to_dt(int32_t i) { return __int_as_float(i);   }
// double → int64 via __double_as_longlong / __longlong_as_double
```

Pipeline:

1. Global `__device__ int32_t g_dt_min_bits = INT32_MAX` (or `INT64_MAX` for double).
2. Per-block deterministic tree reduce over shared memory (reverse-halving, fixed iteration order) → `block_min`.
3. One thread per block calls `atomicMin(&g_dt_min_bits, block_min_bits)`.
4. Host reads back, applies `__int_as_float`.

`atomicMin` on integers is deterministic — `min` is associative and commutative on ints, and the hardware CAS loop converges to the same minimum regardless of contention order. This is unlike `atomicAdd` on floats. The result is bit-identical to a single-thread fold.

### 4.4 OpenMP CPU determinism

- Sweep loops: each cell update reads neighbours and writes itself only — embarrassingly parallel; OpenMP does not perturb output bits.
- CFL: `#pragma omp parallel for reduction(min:dt)` — `min` is associative on floats (NaN aside) → bit-deterministic.
- Flux accumulation: per-cell algebra is serial within a single thread (left/right flux ordering fixed) — OpenMP does not enter.
- Result: with strict-IEEE flags applied, a CPU OpenMP build is run-to-run bit-identical at any thread count (consistent with the absence of run-to-run noise observed in Week 5 regression).

### 4.5 Regression-gate thresholds (Week 6 acceptance criteria)

| Comparison | Precision | Threshold |
|---|---|---|
| CPU strict-IEEE vs GPU strict-IEEE, **double** | float64 | `‖cpu - gpu‖_∞ ≤ 16 · ε_double · ‖cpu‖_∞`  (~16 ULP, K = O(stencil depth × sweep count)) |
| Same, **float** | float32 | `‖cpu - gpu‖_∞ ≤ 16 · ε_float  · ‖cpu‖_∞` |
| Stationary-contact special case | both | `‖cpu - gpu‖_∞ ≤  4 · ε · ‖cpu‖_∞`  (tighter; piecewise-constant IC, no truncation accumulation) |

If any case overshoots: do **not** widen the threshold. Surface immediately at the D6 regression run, then escalate via the systematic-debugging skill. Most likely root causes: a forbidden intrinsic slipped in, a `__shared__` accumulator was written cross-block, or a strict-IEEE flag was suppressed by OPT_LEVEL chain.

### 4.6 Verification commands (run at D5 / D6)

```bash
# 1. unit-test layer (per kernel)
./build-cuda-double-strict/unit_tests "[gpu]" -r compact
./build-cuda-float-strict/unit_tests  "[gpu]" -r compact

# 2. end-to-end smoke (single case)
./build-cuda-double-strict/hrsc tests/cases/toro_1d/sod.cfg --device gpu --output sod_gpu_d.bin
./build-cpu-strict-double/hrsc  tests/cases/toro_1d/sod.cfg --device cpu --output sod_cpu_d.bin
python scripts/regression/float_regression_report.py --mode device \
    --cpu sod_cpu_d.bin --gpu sod_gpu_d.bin --reference exact --precision double

# 3. full Week 6 regression
python scripts/run_matrix.py experiments/week6/regression/matrix.json
```

---

## 5. Build system extensions

### 5.1 `cmake/CUDASetup.cmake`

```cmake
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)
set(CMAKE_CUDA_SEPARABLE_COMPILATION ON)

if(NOT DEFINED CMAKE_CUDA_ARCHITECTURES)
    if(DEFINED ENV{HRSC_CUDA_ARCH})
        set(CMAKE_CUDA_ARCHITECTURES $ENV{HRSC_CUDA_ARCH})
    else()
        set(CMAKE_CUDA_ARCHITECTURES native)  # WSL local default
    endif()
endif()

find_package(CUDAToolkit REQUIRED)
message(STATUS "CUDA toolkit: ${CUDAToolkit_VERSION}")
message(STATUS "CUDA arch:    ${CMAKE_CUDA_ARCHITECTURES}")
```

CSC uses `HRSC_CUDA_ARCH=80` (or whatever D1 probe records) injected via env in `build_gpu_csc.sh`.

### 5.2 `cmake/CompilerFlags.cmake`

```cmake
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
```

Existing `OPT_LEVEL` / `FAST_MATH` behaviour is unchanged. Strict-IEEE is an opt-in pathway, applied only when `STRICT_IEEE=ON`.

### 5.3 Top-level `CMakeLists.txt`

```cmake
option(ENABLE_CUDA "Build CUDA GPU solver"      OFF)
option(STRICT_IEEE "Force strict-IEEE FP flags" OFF)

if(ENABLE_CUDA)
    enable_language(CUDA)
    include(cmake/CUDASetup.cmake)
    target_sources(hrsc_lib PRIVATE
        src/gpu/euler_kernels.cu
        src/gpu/euler_gpu_solver.cu
    )
    target_compile_definitions(hrsc_lib PUBLIC HRSC_HAS_CUDA=1)
endif()

if(STRICT_IEEE)
    hrsc_apply_strict_ieee_cpu(hrsc_lib)
    if(ENABLE_CUDA)
        hrsc_apply_strict_ieee_cuda(hrsc_lib)
    endif()
endif()
```

### 5.4 New build dir naming (Week 6 only)

| Build dir | cmake invocation |
|---|---|
| `build-cpu-strict-double` | `cmake -B ... -G Ninja -DFLOAT_PRECISION=double -DSTRICT_IEEE=ON -DENABLE_OPENMP=ON -DCMAKE_BUILD_TYPE=Release` |
| `build-cpu-strict-float`  | as above, `-DFLOAT_PRECISION=float` |
| `build-cuda-double-strict` | as above, `+ -DENABLE_CUDA=ON -DSTRICT_IEEE=ON` |
| `build-cuda-float-strict`  | as above, `+ -DFLOAT_PRECISION=float -DENABLE_CUDA=ON -DSTRICT_IEEE=ON` |

Convention: CUDA variants carry `-strict` as a suffix (so `ls build-cuda-*` lists all GPU builds together); CPU variants prefix `strict` after `cpu-` (so `ls build-cpu-strict-*` lists strict CPU builds together). Both groups are easy to glob for.

### 5.5 `scripts/build_all.sh`

Pre-flight probe:

```bash
if ! echo 'int main(){}' | ${CXX:-cc} -ffp-contract=off -xc++ -c -o /dev/null - 2>/dev/null; then
    echo "WARN: compiler does not support -ffp-contract=off; STRICT_IEEE builds disabled" >&2
    SKIP_STRICT=1
fi

if command -v nvcc >/dev/null 2>&1; then
    if ! echo 'int main(){}' | nvcc --fmad=false -xc -c -o /dev/null - 2>/dev/null; then
        echo "WARN: nvcc does not support --fmad=false; CUDA STRICT builds disabled" >&2
        SKIP_CUDA_STRICT=1
    fi
fi
```

Strict variants are added to `BUILD_VARIANTS` only when their probe succeeds. On any probe failure: a loud warning, never a silent fallback to default rounding.

### 5.6 `.gitignore`

```
build-cpu-strict-*/
build-cuda-*-strict/
```

(Already covered by the `build-*/` glob, but explicit listing aids grepability.)

---

## 6. Regression schema (CPU-vs-GPU first-class)

### 6.1 Current state

`scripts/regression/float_regression_report.py`:
- `_report_1d` — emits `legacy d/f` ratio + Philip `fmd / d_err` ratio columns.
- `_report_2d` — emits `legacy L1/L2/Linf` + `ssim` + Philip ratio columns.

Implicit pairing: file naming `float_NNN.bin` / `double_NNN.bin`.

### 6.2 Week 6 change

Add `--mode {fp, device}` flag. Existing call sites continue to work without modification.

```bash
# fp mode (default; existing behaviour)
python scripts/regression/float_regression_report.py --mode fp \
    --inputs experiments/.../float_*.bin experiments/.../double_*.bin \
    --reference exact

# device mode (new)
python scripts/regression/float_regression_report.py --mode device \
    --inputs experiments/.../cpu_*.bin experiments/.../gpu_*.bin \
    --reference exact \
    --precision double
```

### 6.3 Output schema

| Column | mode=fp | mode=device |
|---|---|---|
| `pair_a` | `float` | `cpu` |
| `pair_b` | `double` | `gpu` |
| `precision` | n/a | `float` or `double` |
| `l1_a_minus_b` | ✓ | ✓ |
| `linf_a_minus_b` | ✓ | ✓ |
| `philip_ratio` | `‖f - d‖₁ / ‖d - exact‖₁` | `‖cpu - gpu‖₁ / ‖cpu - exact‖₁` |
| `ulp_max` | n/a (cross-precision is meaningless) | **new**: `linf_a_minus_b / (ε · ‖a‖_∞)` |
| `gate_passed` | n/a | **new**: bool, per §4.5 |
| `notes` | (existing) | (existing) |

### 6.4 Output files

```
experiments/week6/regression/
├── matrix.json                        # 4 builds × {sod, lw3_n200} = 8 runs
├── runs/                              # standard run_matrix.py layout (run names match matrix.json exactly: `-d` / `-f` precision suffix)
│   ├── sod-cpu-strict-d/{config.cfg, stdout.txt, stderr.txt, metadata.json, sod.bin}
│   ├── sod-gpu-strict-d/...
│   ├── sod-cpu-strict-f/...
│   ├── sod-gpu-strict-f/...
│   ├── lw3-cpu-strict-d/...
│   ├── lw3-gpu-strict-d/...
│   ├── lw3-cpu-strict-f/...
│   └── lw3-gpu-strict-f/...
├── summary.csv                        # device mode, 4 comparison rows
├── summary.json
└── summary.md                         # human table + gate pass/fail icons
```

### 6.5 CSC summary

`experiments/week6/csc_smoke/summary.{md,json}` shares the schema, plus:

| Column | Meaning |
|---|---|
| `host` | `wsl-laptop` or `csc-gpu` |
| `cuda_runtime` | nvcc / driver version |
| `arch` | `sm_75`, `sm_80`, etc. |

These columns enable Report 1's hardware-reproducibility table to be assembled directly from this file.

### 6.6 Pytest

`tests/py/test_float_regression_report_device_mode.py`:
- Construct mock `cpu.bin` / `gpu.bin` differing by `8 · ε`; assert `gate_passed=True`.
- Construct difference `64 · ε`; assert `gate_passed=False`.
- Assert device-mode CSV columns are populated end-to-end (no `None` leaks); assert fp-mode CSV is unaffected.

---

## 7. Test plan

### 7.1 Catch2 `[gpu]` matrix

Each kernel gets a dedicated test file. Oracle is the corresponding CPU strict-IEEE function or kernel run on identical input; comparison threshold is per §4.5 (typically 0 ULP at the unit level since per-cell algebra has no reduction).

| File | Cases | Coverage |
|---|---|---|
| `test_gpu_grid_layout.cpp` | 3 | (i) `Grid2D::row_stride_bytes()` == `GpuGrid::row_stride_bytes()` for nx ∈ {7, 17, 33, 64, 257, 1024} (covers 2/4/8-byte alignment corners); (ii) ghost-cell-inclusive round-trip with known pattern, byte-identical via `memcmp`; (iii) deliberate misaligned mid-row offset, kernel writes, D2H, exact write-position verification |
| `test_gpu_bc.cpp` | 6 | outflow / periodic / reflective × {X, Y}; ghost cells filled with random bits; output bit-equivalent to CPU `apply_*_bc` |
| `test_gpu_cfl.cpp` | 4 | grids 7×3 / 16×16 / 257×129 / 1024×1024; near-zero and near-c_max velocities; one cell as the dt_min carrier; final case repeats 100× to assert run-to-run bit-identity |
| `test_gpu_reconstruct.cpp` | 3 | single cell (slope=0); 16×16 with strong gradient; 33×17 non-power-of-two |
| `test_gpu_hancock.cpp` | 3 | as above; sub-sonic / supersonic / sonic-point predictions |
| `test_gpu_rusanov.cpp` | 4 | single face; sonic point; stationary-contact face; 16×16 full-grid sweep |
| `test_gpu_hllc.cpp` | 5 | single face; sonic; **`S*=0` stationary contact**; SL/SR both-positive and both-negative fans; 16×16 full-grid sweep |
| `test_gpu_update.cpp` | 3 | 1-step conservative update; BC then update; alternating Lie splitting half-step |
| `test_gpu_solver_e2e.cpp` | 4 | Sod 1D × 1 step; Sod 1D × 10 steps; LW Config 3 n=64 × 5 steps; LW Config 3 n=200 × 1 step (largest end-to-end, against §4.5) |
| `test_lw_config4.cpp` | 2 | IC sample-cell values; solver runs 1 step without NaN |
| `test_lw_config12.cpp` | 2 | as above |

Total: 39 new cases, ~650 assertions. Adds little wall-clock to the existing 117 cases / 4060 assertions (most GPU kernels run < 10 ms at these sizes).

### 7.2 Unit-test compilation gating

- `[gpu]` files compile into `unit_tests` only when `ENABLE_CUDA=ON`. CMake guard:
  ```cmake
  if(ENABLE_CUDA)
      target_sources(unit_tests PRIVATE
          tests/unit/test_gpu_grid_layout.cpp
          tests/unit/test_gpu_bc.cpp
          ...
      )
  endif()
  ```
- A CPU-only build dir's `unit_tests` excludes `[gpu]` cases entirely — CSC CPU partitions and GPU-less hosts remain unaffected.

### 7.3 End-to-end smoke matrix (D5 / D6 / D7)

```jsonc
// experiments/week6/smoke/matrix.json (local WSL)
{
  "experiment": "week6-gpu-smoke",
  "output_root": "experiments/week6/smoke",
  "runs": [
    {"name": "sod-cpu-strict-d", "binary": "build-cpu-strict-double/hrsc",
     "config": "tests/cases/toro_1d/sod.cfg", "extra_cfg": {"device": "cpu"},
     "build": "cpu-strict-double", "output_file": "sod.bin"},
    {"name": "sod-gpu-strict-d", "binary": "build-cuda-double-strict/hrsc",
     "config": "tests/cases/toro_1d/sod.cfg", "extra_cfg": {"device": "gpu"},
     "build": "cuda-strict-double", "output_file": "sod.bin"},
    {"name": "sod-cpu-strict-f", "...": "..."},
    {"name": "sod-gpu-strict-f", "...": "..."},
    {"name": "lw3-cpu-strict-d", "config": ".../config3_n200.cfg", "...": "..."},
    {"name": "lw3-gpu-strict-d", "...": "..."},
    {"name": "lw3-cpu-strict-f", "...": "..."},
    {"name": "lw3-gpu-strict-f", "...": "..."}
  ]
}
// 8 runs → 4 comparison pairs
```

`experiments/week6/csc_smoke/matrix.json` carries the GPU 4 rows only (CPU baseline stays local). The SLURM wrapper adds `--gres=gpu:1`.

### 7.4 Pytest matrix

- `tests/py/test_float_regression_report_device_mode.py` (new; §6.6).
- Existing `test_ssim_scalar`, `test_snr_*`, `test_losos_*`, `test_s_req_*`, `test_plot_divergence_marker`, `test_plot_2d` unchanged.
- `tests/py/test_float_regression_report.py` (Week 5) — add one device-mode regression case.

### 7.5 Explicitly out of Week 6 testing

- GPU `--use_fast_math` path (Week 7).
- Cross-arch GPU comparison (sm_75 vs sm_86 vs sm_90) — Week 7 production runs.
- GPU performance regression (throughput, occupancy) — Week 7.
- GPU MHD — Week 14.
- Shock-bubble GPU — Week 7.

### 7.6 Verification doc

`docs/week6/week6-verification.md` (D7), modeled on `week5-verification.md`:
- Phase A: CPU-strict + CUDA build commands.
- Phase B: unit-test pass commands (with `[gpu]` tag filter).
- Phase C: local WSL smoke matrix.
- Phase D: CSC SLURM submission + binary rsync + regression command.
- Each phase ends with the expected output summary (`gate_passed=True`, `ulp_max ≤ 16`, etc.).

---

## 8. CSC migration

### 8.1 D1 probe — fields to land in `docs/week6/csc_gpu_environment.md`

| Item | Value |
|---|---|
| Cluster login host | (D1) |
| GPU partition name | (D1) |
| `module avail cuda` candidates | (D1) |
| Selected module | (D1) |
| nvcc version | (D1) |
| Driver version | (D1) |
| GPU model | (D1) |
| Compute capability | (D1) |
| Default wall-clock limit | (D1) |
| `--gres` syntax | (D1) |
| Node home filesystem | (D1) |
| Build-artefact location | (D1) |

### 8.2 `scripts/cluster/build_gpu_csc.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
# Idempotent build script for CSC GPU node.
# Usage: bash scripts/cluster/build_gpu_csc.sh [double|float|both]

PRECISION="${1:-both}"
ARCH="${HRSC_CUDA_ARCH:-80}"   # default sm_80; override via env

module purge
module load cuda/12.4
module load gcc/11
module load cmake/3.27
module load ninja || true

command -v nvcc >/dev/null || { echo "nvcc not found after module load" >&2; exit 1; }
nvcc --version
nvidia-smi || echo "WARN: nvidia-smi only available on GPU nodes (skip on login)"

build_one() {
    local prec="$1"
    local dir="build-cuda-${prec}-strict"
    cmake -B "${dir}" -G Ninja \
        -DFLOAT_PRECISION="${prec}" \
        -DENABLE_CUDA=ON \
        -DSTRICT_IEEE=ON \
        -DENABLE_OPENMP=ON \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_CUDA_ARCHITECTURES="${ARCH}"
    cmake --build "${dir}" -j
}

case "${PRECISION}" in
    double) build_one double ;;
    float)  build_one float ;;
    both)   build_one double; build_one float ;;
    *)      echo "usage: $0 [double|float|both]" >&2; exit 2 ;;
esac

echo "Build complete: build-cuda-*-strict/hrsc"
```

### 8.3 `scripts/cluster/run_gpu_smoke.slurm`

```bash
#!/bin/bash
#SBATCH --job-name=hrsc-gpu-smoke
#SBATCH --partition=ampere               # placeholder, overwritten after D1 probe
#SBATCH --gres=gpu:1                     # placeholder, overwritten after D1 probe
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=01:00:00
#SBATCH --output=experiments/week6/csc_smoke/slurm_logs/%j.out
#SBATCH --error=experiments/week6/csc_smoke/slurm_logs/%j.err

set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"

module purge
module load cuda/12.4
module load gcc/11

nvidia-smi
nvcc --version

mkdir -p experiments/week6/csc_smoke/slurm_logs
python scripts/run_matrix.py experiments/week6/csc_smoke/matrix.json
```

### 8.4 CSC matrix.json

```jsonc
{
  "experiment": "week6-csc-gpu-smoke",
  "output_root": "experiments/week6/csc_smoke",
  "runs": [
    {"name": "sod-gpu-csc-d", "binary": "build-cuda-double-strict/hrsc",
     "config": "tests/cases/toro_1d/sod.cfg",
     "extra_cfg": {"device": "gpu"},
     "build": "cuda-strict-double-csc", "output_file": "sod.bin"},
    {"name": "sod-gpu-csc-f", "binary": "build-cuda-float-strict/hrsc", "...": "..."},
    {"name": "lw3-gpu-csc-d", "binary": "build-cuda-double-strict/hrsc",
     "config": "tests/cases/liska_wendroff_2d/config3_n200.cfg", "...": "..."},
    {"name": "lw3-gpu-csc-f", "...": "..."}
  ]
}
```

### 8.5 D7 workflow

```bash
# Local (laptop)
1. git push                                           # week4-implementation → remote

# CSC login node
2. ssh csc-login
3. cd ~/floatpoint && git pull
4. bash scripts/cluster/build_gpu_csc.sh both
5. ./build-cuda-double-strict/unit_tests "[gpu]"      # login-node sanity (skips GPU-only cases)
6. sbatch scripts/cluster/run_gpu_smoke.slurm
7. squeue -u $USER                                    # watch
8. cat experiments/week6/csc_smoke/slurm_logs/*.out   # confirm nvidia-smi / nvcc info captured

# Pull back to local (rsync, resumable)
9. rsync -avz csc-login:~/floatpoint/experiments/week6/csc_smoke/ \
              experiments/week6/csc_smoke/

# Local comparison
10. python scripts/regression/float_regression_report.py --mode device \
        --cpu experiments/week6/regression/runs/...-cpu-strict-*/sod.bin \
        --gpu experiments/week6/csc_smoke/runs/...-gpu-csc-*/sod.bin \
        --reference exact \
        --precision double \
        --output experiments/week6/csc_smoke/summary.{md,json}

# Commit
11. git add scripts/cluster/ docs/week6/csc_gpu_environment.md \
            experiments/week6/csc_smoke/{matrix.json,summary.{md,json}}
    git commit -m "feat(week6): CSC GPU smoke (Sod + LW3, double + float)"
```

### 8.6 Failure handling

| Failure | Mitigation |
|---|---|
| Wrong CSC partition / `--gres` syntax | D1 probe catches; reserve D7 morning for re-sbatch. |
| Queue wait > 4 h | `summary.md` carries `csc_run_pending`; commit script + matrix; replay in Week 7 D1. |
| CSC GPU diff > §4.5 threshold | Do not widen the threshold. Record in `week6-summary.md` Risk section; address with systematic-debugging skill in Week 7 (most likely: CSC nvcc 12.4 vs WSL 12.x codegen micro-difference). |
| `nvidia-smi` unavailable on login node | Expected; D1 doc must note this explicitly. |

---

## 9. Risk register & acceptance gates

### 9.1 Risk register

| ID | Risk | Probability | Impact | Mitigation | Owner day |
|---|---|---|---|---|---|
| R1 | WSL CUDA driver / nvcc 12.x mismatch (WSL CUDA forwards to Windows host driver) | M | High (D1 blocker) | First 30 min of D1: `nvidia-smi` + `nvcc --version` + Week 5 `[gpu]` smoke. Failure → consult WSL CUDA setup doc; fallback to native Windows path (WSL2 GPU passthrough requires Win11 + recent NVIDIA driver). | D1 |
| R2 | `Grid2D` vs `GpuGrid` row-stride drift → kernel garbage | M | Fatal (silent ULP diff) | `test_gpu_grid_layout.cpp` runs first thing on D2, blocking BC kernel work on failure. | D2 |
| R3 | CFL `atomicMin` on bit-reinterpret undefined under negative dt or NaN | L | Medium (CFL valid IC always positive) | Kernel-entry assert `dt > 0`; one debug-build pass under `compute-sanitizer`. | D3 |
| R4 | GCC minor version silently ignores `-ffp-contract=off` under OpenMP | L | High (violates §4.5 gate) | §5.5 probe + loud print; additionally `objdump -d` grep for `vfmadd` on a CPU-strict binary to confirm absence. | D1 |
| R5 | HLLC `S*=0` GPU/CPU divergence due to compiler reordering of `<=` vs `<` | L | Medium (one-case fail) | `test_gpu_hllc.cpp` includes the stationary-contact case; fallback: Rusanov GPU baseline already satisfies the milestone. | D6 |
| R6 | CSC partition / `--gres` / module names diverged from D1 probe | L | Medium | sbatch failure on D7 → re-probe; SLURM script + module list versioned in git → next replay ≤ 30 min. | D7 |
| R7 | CSC vs WSL same-precision GPU diff exceeds threshold (sm_XX codegen micro-diff) | M | Low–Medium (a finding, not a bug) | Do not force-pass. `week6-summary.md` records the diff as a Report 1 hardware-reproducibility data point — **this is one of the project's core research targets**, not a failure. | D7 |
| R8 | `[gpu]` unit tests un-runnable elsewhere (single-developer project, but) | L | Low | CMake gate `if(ENABLE_CUDA)`; README notes `[gpu]` requires GPU; CSC login node degrades cleanly to CPU smoke. | D6 |

### 9.2 Acceptance gates ("Week 6 done" — all eight required by D7 EOD)

| Gate | Verification |
|---|---|
| **G1. CPU-strict + CUDA builds clean** | WSL `bash scripts/build_all.sh` produces 4 strict build dirs, all green. CSC `bash scripts/cluster/build_gpu_csc.sh both` likewise. |
| **G2. Unit tests green** | `./build-cuda-double-strict/unit_tests -r compact` passes (incl. 39 new `[gpu]` cases); float build same; CPU-strict builds run non-`[gpu]` cases. |
| **G3. Local WSL smoke matrix green** | `python scripts/run_matrix.py experiments/week6/smoke/matrix.json`: 8 runs succeed; regression report `gate_passed=True` for all 4 pairs (Sod×{f,d}, LW3×{f,d}). |
| **G4. CSC GPU smoke executed _or_ `csc_run_pending` documented** | Preferred: CSC 4 runs succeed; binaries rsynced back; regression report emitted (CSC-vs-local diff recorded regardless of pass/fail). Acceptable fallback: queue did not drain; `week6-summary.md` carries `csc_run_pending` with an explicit Week 7 D1 replay date; `scripts/cluster/{build_gpu_csc.sh, run_gpu_smoke.slurm}` and `experiments/week6/csc_smoke/matrix.json` are committed and reproducible. (This is the only gate with a fallback path; rationale: CSC queue is outside our control.) |
| **G5. cfg-dispatch byte-level regression** | With `device` unset, `./build-double/hrsc tests/cases/toro_1d/sod.cfg` output is byte-identical to the Week 5 commit `cda04f3` snapshot (`md5sum` compare). |
| **G6. Timer 5-phase split** | `[timing] total_s=…` plus `[timing] phase=bc/cfl/flux/update/sweep …` all emit. GPU build also emits per-phase timing (device + H2D/D2H broken out). |
| **G7. LW Config 4 / 12 IC + cfg landed** | `tests/unit/test_lw_config{4,12}.cpp` green; CPU baseline runs `lw_config{4,12}_n200.cfg`; binary header correct (figure validation deferred to Week 7). |
| **G8. Documentation closed** | `docs/week6/week6-plan.md`, `…/week6-summary.md`, `…/csc_gpu_environment.md`, `…/week6-verification.md` all present; `docs/INDEX.md` Week 6 row updated from "(pending)" to live links. |

### 9.3 Stretch goals (only if D7 EOD has slack)

By ROI, none required for closeout:
1. CSC also runs LW Config 4 / 12 GPU baseline (≈ 30 min work, but CSC queue is uncontrollable).
2. With `ENABLE_CUDA=ON` and `--device cpu`, `EulerSolver` output is byte-identical to a CPU-only build (deep-regression insurance).
3. `experiments/week6/regression/summary.md` carries a wall-clock CPU-vs-GPU speedup column (sneak preview of Week 7 perf characterization).

### 9.4 Known carry-forward (recorded at the bottom of `week6-summary.md`)

- HLLC `<=` vs `<` GPU toggle → Week 7.
- Fast-math GPU matrix → Week 7.
- `vfc_precexp` / unstable-branch detection → Week 14.
- Shock-bubble GPU validation → Week 7.
- GPU MHD → Week 14.

---

_Maintained alongside `week5_to_week6_bridge.md`; superseded by `week6-plan.md` (writing-plans output) for day-by-day tracking._
