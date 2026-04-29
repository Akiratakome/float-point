# Week 5 Plan — 2D Tests Closure + GPU Toolchain Bring-up

**Date drafted**: 2026-04-29
**Active branch**: `week4-implementation` (Week 5 work继续在此 branch；merge 时机见 §5.4)
**Target phase**: `overall.md` Week 5 (lines 278–296)
**Pre-context**: [`week4_to_week5_bridge.md`](week4_to_week5_bridge.md)

This plan is the design spec produced by the brainstorming process; it will be turned into an executable implementation plan by `superpowers:writing-plans` after user approval.

---

## 0. Locked Decisions

| # | Decision | Choice |
|---|---|---|
| Q1 | Scope vs "time plentiful" | **Strict overall.md Week 5 boundary**; "time plentiful" → completeness, not Week 6 absorption |
| Q2 | GPU toolchain target | **Local CUDA laptop**; CSC GPU nodes deferred to Week 6 |
| Q3 | Verification depth | **Three-layer (unit + solver + harness) + `week5-verification.md`** |
| Q4 | Liska-Wendroff Config 6 | **Faithful to LW 2003 (4 contact discontinuities, no shocks)**; correct overall.md table |
| Q5 | Shock-bubble version | **Single-fluid shock-density-bubble test, half-symmetric Toro/Quirk-Karni setup**, domain `[0,1]×[0,0.25]`, grid `400×100`, bubble centred at (0.25, 0) on symmetry plane, Mach 1.22 |
| Q6 | GPU skeleton depth | **Toolchain + `GpuGrid` host↔device roundtrip + Catch2 `[gpu]` test** |
| Q7 | `plot_2d.py` shape | **`scripts/figures/plot_2d.py`, single-grid → image, CLI** (no batch, no multi-panel) |
| Q8 | `timer.hpp` granularity | **`Timer` + opt-in `ScopedTimer` profiling, `HRSC_ENABLE_PROFILING` macro, default OFF** |
| Approach | Execution ordering | **Approach 2 — GPU toolchain risk exposed Day 1; rest follows bridge order** |

---

## 1. Documentation & Archival Layout

Per `INDEX.md` §2 convention (`docs/weekN/weekN-plan.md`), Week 5 produces three docs in `docs/week5/`:

```
docs/week5/
├── week4_to_week5_bridge.md    # already exists, untouched
├── week5-plan.md                # THIS FILE (spec)
├── week5-verification.md        # produced Day 5 (manual reproduction recipe)
└── week5-summary.md             # produced Day 5 (commits + experiment dirs + W5→W6 handoff)
```

Cross-doc edits also in scope:

- `docs/INDEX.md` §2 table — add Week 5 row
- `docs/requirement/overall.md` — Supersonic Wave Test Cases table: change Config 6 row ✓ → ✗ with note "LW 2003 Config 6 is a 4-contact-only test, used for contact resolution rather than supersonic capture"
- `docs/requirement/overall.md` Week 5 section — footnote confirming the project uses LW 2003 literal Config 6 numbering

The brainstorming-skill default spec path (`docs/superpowers/specs/...`) is overridden in this project by INDEX.md convention.

---

## 2. Code Implementation Plan (5 Deliverable Blocks)

### Block A — `Timer` + opt-in profiling

**New files**

- `src/utils/timer.hpp`
  - `class Timer` with `start()` / `stop()` / `elapsed_seconds()` over `std::chrono::steady_clock`; accumulator semantics for repeated `start/stop` pairs
  - Under `#ifdef HRSC_ENABLE_PROFILING`:
    - `class ProfilingRegistry` with `void add(std::string_view, double)` and `std::map<std::string,double> snapshot() const`
    - `class ScopedTimer` (RAII; ctor records start, dtor adds elapsed to a named accumulator in the registry)

**Modifications**

- `src/main.cpp` — time the call to `solver.run(...)` at the call site; do **not** change cfg defaults or numerical behaviour
- `src/main.cpp` — after `solver.run(...)` returns, print a single machine-parseable line to **stderr**: `[timing] total_s=<value>` (stdout remains reserved for existing table/convergence output). The top-level `Timer` is unconditional (not gated by `HRSC_ENABLE_PROFILING`), so this line appears in every build.
- `src/euler/euler_solver.cpp` — under `#ifdef HRSC_ENABLE_PROFILING`, wrap the five solver phases (`reconstruction`, `riemann`, `update`, `bc`, `cfl`) with `ScopedTimer`; default build (macro OFF) leaves the file binary-identical to current. No change to algorithmic path or cfg defaults under any setting.
- `scripts/run_matrix.py` — parse the `[timing]` line from stderr, write `metadata.json.timing.total_s`
- `CMakeLists.txt` — new option `HRSC_ENABLE_PROFILING` default `OFF`

**Unit test** `tests/unit/test_timer.cpp` — see §3 Layer 1

---

### Block B — Liska-Wendroff Config 6 IC

**Modify** `tests/cases/liska_wendroff_2d/lw_tests.hpp`: replace the throwing stub `setup_liska_wendroff_config6(...)` with the real IC.

LW 2003 Config 6 (γ = 1.4, domain `[0,1]²`, t_end = 0.3, four-quadrant initial state, **all contact discontinuities, no shocks**):

| Quadrant | Region | ρ | u | v | p |
|---|---|---|---|---|---|
| QI  | x>0.5, y>0.5 | 1.0 |  0.75 | -0.5 | 1.0 |
| QII | x<0.5, y>0.5 | 2.0 |  0.75 |  0.5 | 1.0 |
| QIII| x<0.5, y<0.5 | 1.0 | -0.75 |  0.5 | 1.0 |
| QIV | x>0.5, y<0.5 | 3.0 | -0.75 | -0.5 | 1.0 |

Boundary: outflow on all four sides.

**New cfgs**
- `tests/cases/liska_wendroff_2d/config6_n200.cfg` — `solver=hllc`, `output_format=binary`, `output_file=experiments/week5/baselines/lw_config6_n200/grid.bin`, `bc=outflow`
- `tests/cases/liska_wendroff_2d/config6_n400.cfg` — same, `output_file=experiments/week5/baselines/lw_config6_n400/grid.bin`

(Both explicitly set `solver=hllc`; do not rely on the global default, which is `rusanov` since Week 4. Both explicitly set `output_format=binary`; the default falls back to `table` and would not produce the `.bin` files Layer 2/3 expect. HLLC vs Rusanov contrast is left to Week 6. `src/utils/io.hpp` auto-creates parent dirs, so no `mkdir -p` needed.)

**Unit test additions** in the existing LW test file: 4-quadrant ρ assignment, p ≡ 1.0, u/v sign symmetry; use tight `Approx` tolerances (`~1e-14` for double pressure after conserved→primitive roundtrip, wider for float builds).

---

### Block C — Shock-bubble (single-fluid shock-density-bubble test)

**New directory** `tests/cases/shock_bubble/`

- `shock_bubble_tests.hpp`
  - Domain: `[0,1] × [0, 0.25]` (**half-symmetric**: y = 0 is the symmetry plane through the bubble centre; the full physical bubble is recovered by mirroring about y = 0 when plotting). γ = 1.4 throughout. This is a **single-fluid approximation** inspired by the Mach-1.22 shock/helium-bubble benchmark (Quirk-Karni 1996; Toro 2009 §17.1.4): the bubble is represented by a density contrast only, with no species equation and no variable γ. Do not claim one-to-one reproduction of the multi-gas literature case.
  - Planar shock at x = 0.05, Mach 1.22 moving right; left = post-shock state from Rankine-Hugoniot, right = pre-shock (ρ=1, p=1, u=0)
  - Helium bubble: centre (0.25, 0), radius 0.1 — i.e. only the upper half of the bubble lies in the computational domain; the lower half is provided implicitly by the y = 0 symmetry BC.
  - Boundary: cfg sets `bc_x = outflow` (both x sides outflow) and `bc_y = reflective` (y = 0 acts as symmetry mirror for the bubble; y = 0.25 is the upper channel wall, also reflective — matches Quirk-Karni half-symmetric channel). The parser at `src/main.cpp:100` (`parse_boundary`) takes a single value per axis, applied to both sides of that axis; do not write `bc_x = outflow,outflow`.
  - Register `test=shock_bubble` in `main.cpp` `select_test(...)`
- `shock_bubble_n400x100.cfg` — `t_end=0.4`, `cfl=0.5`, `nx=400`, `ny=100` (preserves dx = dy = 0.0025), `xmax=1.0`, `ymax=0.25`, `solver=hllc`, `output_format=binary`, `bc_x=outflow`, `bc_y=reflective`, `output_file=experiments/week5/baselines/shock_bubble_n400x100_hllc/grid.bin`
- `shock_bubble_n400x100_rusanov.cfg` — same axes/grid/bc, `solver=rusanov`, `output_format=binary`, `output_file=experiments/week5/baselines/shock_bubble_n400x100_rusanov/grid.bin`

**Unit test** `tests/unit/test_shock_bubble.cpp` — see §3 Layer 1

---

### Block D — GPU skeleton (two sub-deliverables)

#### D.1 — Toolchain smoke (Day 1, risk exposure)

**New files**

- `cmake/CUDASetup.cmake` — `find_package(CUDAToolkit REQUIRED)`; auto-detect `CMAKE_CUDA_ARCHITECTURES` (fallback: `native`); coexist with OpenMP. Policy CMP0104 is automatically NEW because root `CMakeLists.txt:1` already requires CMake ≥ 3.18, so no explicit `cmake_policy(SET CMP0104 NEW)` is needed; if the minimum is ever lowered, add the explicit policy line back to prevent cryptic nvcc target-architecture errors
- `src/gpu/gpu_smoke.cu` — minimal program calling `cudaGetDeviceCount()` and printing each device name + compute capability

**Modifications**

- `CMakeLists.txt` — new option `ENABLE_CUDA` default `OFF`; when `ON`, `enable_language(CUDA)`, include `CUDASetup.cmake`, build standalone target `gpu_smoke`. **Not linked into the main `hrsc` binary.**

**Verification**:
```bash
cmake -B build-cuda -G Ninja -DENABLE_CUDA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build-cuda --target gpu_smoke
./build-cuda/gpu_smoke      # prints local GPU name + compute capability
```

#### D.2 — Data path + Catch2 `[gpu]` test (Days 3–4)

**New files**

- `src/gpu/cuda_utils.cuh`
  ```cpp
  #define HRSC_CUDA_CHECK(call) /* wraps cudaError_t; throws std::runtime_error on failure */

  template <class T>
  class DeviceArray {
   public:
    explicit DeviceArray(std::size_t n);
    ~DeviceArray();
    DeviceArray(const DeviceArray&) = delete;
    DeviceArray(DeviceArray&&) noexcept;
    void copy_from_host(const T* host, std::size_t n);
    void copy_to_host(T* host, std::size_t n) const;
    T* data();
    std::size_t size() const;
  };
  ```

- `src/gpu/gpu_grid.cuh`
  ```cpp
  template <class Real, int NVars>
  class GpuGrid {
    // mirrors Grid2D<Real,NVars> data layout (row-major, var-last, ghost cells included)
   public:
    explicit GpuGrid(const Grid2D<Real,NVars>& host);   // allocate + upload
    void download_to(Grid2D<Real,NVars>& host) const;
    Real* data();
    int nx() const; int ny() const; int ng() const;
  };
  ```

- `src/gpu/euler_kernels.cuh` — single kernel `__global__ void device_copy_kernel(const Real* in, Real* out, std::size_t n)` performing `out[i] = in[i]`

**Test** — split into two files to avoid compiling Catch2 v2 single-header (~18k LOC, `external/catch2/catch.hpp`) through nvcc:

- `tests/unit/test_gpu_roundtrip.cpp` — Catch2 `TEST_CASE("[gpu] roundtrip", ...)`, picked up by the existing CXX glob. Calls into the wrapper functions below.
- `tests/unit/gpu_roundtrip_kernel.cu` — `device_copy_kernel` definition + two `extern "C"` host-callable wrappers:
  ```cpp
  extern "C" bool gpu_roundtrip_double(const double* host_in, double* host_out,
                                       std::size_t n);
  extern "C" bool gpu_roundtrip_float (const float*  host_in, float*  host_out,
                                       std::size_t n);
  ```
  Each wrapper does: `cudaMalloc` in/out → `cudaMemcpy H→D` → launch `device_copy_kernel` → `cudaMemcpy D→H` → free → return true on success.

Test logic in the `.cpp`: `Grid2D<double,4>` and `Grid2D<float,4>`, each with 100 random seeds; host fill → call `gpu_roundtrip_<T>(...)` → assert byte-identical.

This split keeps `external/catch2/catch.hpp` away from nvcc entirely (huge compile-time saving and avoids host/device warning noise) and isolates CUDA code in a single small `.cu` TU.

**Build wiring** in the root `CMakeLists.txt` (there is no `tests/unit/CMakeLists.txt` in this repository), placed next to the existing `add_executable(unit_tests ${TEST_SOURCES})`:
```cmake
if(ENABLE_CUDA)
  # The .cpp half is auto-picked by the existing GLOB.
  # Add the .cu half explicitly and pin its language.
  target_sources(unit_tests PRIVATE tests/unit/gpu_roundtrip_kernel.cu)
  set_source_files_properties(tests/unit/gpu_roundtrip_kernel.cu
    PROPERTIES LANGUAGE CUDA)
  set_target_properties(unit_tests PROPERTIES
    CUDA_SEPARABLE_COMPILATION ON
    CUDA_ARCHITECTURES "${CMAKE_CUDA_ARCHITECTURES}")
  target_link_libraries(unit_tests PRIVATE CUDA::cudart)
endif()
```

Note: `cmake_minimum_required(VERSION 3.18)` (root `CMakeLists.txt:1`) automatically sets policy CMP0104 to NEW, so explicit `cmake_policy(SET CMP0104 NEW)` is **not needed**. If anyone lowers the minimum version below 3.18 in the future, add the explicit policy line back. The existing `file(GLOB TEST_SOURCES tests/unit/test_*.cpp)` matches only `.cpp`, so `.cu` files must be added explicitly via `target_sources` as above (do NOT extend the glob to `test_*.{cpp,cu}` — it mixes CUDA and CXX languages opaquely and breaks CPU-only builds).

**Explicitly out of scope (Week 6)**: `__device__` HD_FUNC instantiation of EOS/flux/HLLC, BC kernel, reconstruction kernel, CFL reduction, `EulerGpuSolver` class, CSC GPU node build.

---

### Block E — `plot_2d.py` single-grid visualisation

**New file** `scripts/figures/plot_2d.py`

CLI:
```
python plot_2d.py <input.bin> --field {rho|p|vmag|schlieren} --out <png>
                              [--field rho --field p ...]   # multiple fields → multiple PNGs
                              [--cmap viridis] [--vmin X --vmax Y]
                              [--title "..."]               # default: input basename
```

Field implementations:
- `rho`, `p` — direct read from conserved/derived state
- `vmag` — `sqrt(u² + v²)` where `u = momx / rho`, `v = momy / rho`
- `schlieren` — `|∇ρ|` via simple central differences

Output: single PNG per field, with colorbar and axis labels. **No batch mode**, **no summary.json reading** (Week 7 may add a thin batch wrapper if needed).

Reader: **must** use the existing `scripts/io_helper.py:read_binary` (it parses the 64-byte header's `precision_tag` and returns numpy arrays with explicit dtype `<f4` for float / `<f8` for double). Do **not** call `np.fromfile` or any reader that ignores the precision tag — that silently corrupts data when the binary was written by `build-float/hrsc`.

Python deps: `numpy`, `matplotlib` are already in `analysis/requirements.txt` (numpy ≥ 1.21, matplotlib ≥ 3.5). No new dependencies introduced this week. Verify via `grep matplotlib analysis/requirements.txt` before assuming.

**Smoke test** `tests/py/test_plot_2d.py` — see §3 Layer 1

---

### Cross-block dependency graph

```
D.1 (CUDA toolchain smoke)  ─┐
                              │  no downstream deps; Day-1 risk exposure
A (Timer)  ──────────────────┼─→ subsequent baselines auto-record timing
                              │
B (Config 6 IC)  ────┐         │
                     ├─────────┼─→  E (plot_2d.py) verified against Config 6 / shock-bubble
C (shock-bubble)  ──┘          │
                                │
D.2 (GPU data path) ───────────┘
                                │
F = Layer-3 harness smoke + week5-verification.md  ← collected after all of the above
```

---

## 3. Verification Plan (Three Layers + Reproduction Doc)

### Layer 1 — Unit tests (automated, CI-capable)

| Test | File | Pass criterion | Failure fallback |
|---|---|---|---|
| `Timer` basic | `tests/unit/test_timer.cpp` | `sleep_for(100ms)` → `elapsed_seconds()` ∈ [0.09, 0.20]; multiple `start/stop` accumulate | OS jitter → raise upper bound to 0.30s |
| `ProfilingRegistry` accumulation | same file (guarded by `#ifdef HRSC_ENABLE_PROFILING`) | repeated `add` for same name accumulates; `snapshot()` returns sorted map. Test case is compiled out under default `OFF` build. | — |
| Config 6 IC values | `tests/unit/test_liska_wendroff.cpp` (append cases) | 4 quadrants ρ ∈ {1, 2, 1, 3}; p ≡ 1.0; u/v match table per cell with tight `Approx` tolerance | — |
| Shock-bubble IC | `tests/unit/test_shock_bubble.cpp` | bubble interior ρ ≈ 0.138 ± 1e-12 (cells with y < 0.1 inside half-disc); post-shock RH relations satisfied to 1e-12 (double); bubble interface cell count ∈ [40, 60] on 400×100 (half-bubble arc length is half the full circle) | check RH formula, γ, and the half-symmetric geometry (centre at y=0) |
| GPU roundtrip (`[gpu]`) | `tests/unit/test_gpu_roundtrip.cu` | 100 random seeds × {double, float} × `Grid2D<,4>`, all byte-identical | stop-the-world; review `Grid2D` layout / `HD_FUNC` |
| `plot_2d.py` smoke | `tests/py/test_plot_2d.py` | each of 4 fields → PNG file size > 0, pixel dims ≥ 100×100 | — |

**Aggregate pass criteria**:
- `./build-double/unit_tests -r compact` passes (default `HRSC_ENABLE_PROFILING=OFF`; `ProfilingRegistry` case compiled out) — covers the default code path
- One additional build with `-DHRSC_ENABLE_PROFILING=ON` (e.g. `build-double-prof/`) — `./build-double-prof/unit_tests -r compact` passes; this run exercises the `ProfilingRegistry` case and the 5 ScopedTimer probes in `euler_solver.cpp`
- `./build-float/unit_tests -r compact` passes (default `OFF`)
- `./build-cuda/unit_tests "[gpu]"` passes (when `ENABLE_CUDA=ON`)
- `pytest tests/py/test_plot_2d.py` passes
- Combined assertion count across the default `build-double` run ≥ current 3660 + new (≥ 30)

### Layer 2 — Solver end-to-end (manual + semi-automated)

| Test | Command | Pass criterion |
|---|---|---|
| Config 6 double 200² baseline | `./build-double/hrsc tests/cases/liska_wendroff_2d/config6_n200.cfg` | `.bin` lands; 4-quadrant interfaces evolved into contact-wave structure; visual match to LW 2003 Fig. 6 |
| Config 6 double 400² baseline | analogous with `_n400.cfg` | same; interfaces sharper at higher resolution |
| Config 6 float regression | rerun both cfgs from `build-float/` | SSIM vs double **recorded** via `phase_error_metrics.py` and reported in `week5-verification.md`. **No fixed pass threshold** this week — Week 5 establishes the baseline for float-vs-double contact-resolution behaviour. Investigation triggers only if SSIM < 0.90 (significant structural divergence). |
| Shock-bubble HLLC double baseline | `./build-double/hrsc tests/cases/shock_bubble/shock_bubble_n400x100.cfg` | plausible single-fluid shock/light-bubble interaction at t=0.4 (shock crosses the light-density bubble, transmitted/reflected structures visible); when plotting, mirror about y=0 to get the full bubble; do not require one-to-one match to multi-gas Toro/Quirk-Karni figures |
| Shock-bubble HLLC vs Rusanov | run both cfgs in `build-double/` | qualitative: Rusanov contact more diffused, HLLC sharper. **Expected**, not a bug. |
| Wall-clock visible | observe `[timing] total_s=...` line in stderr for any of the above runs | line present, value > 0 |

For each baseline, generate ρ + p + |∇ρ| PNGs via `plot_2d.py` and embed reference paths in `week5-verification.md`.

(The `metadata.json` `timing.total_s` field check is exercised separately in Layer 3 — it requires `run_matrix.py` to parse the `[timing]` line.)

**Failure fallback**:
- Config 6 evolution doesn't match LW 2003 → check IC table (most common error: u/v sign), then BC (must be outflow on all four sides)
- Shock-bubble mushroom asymmetric about the y=0 symmetry plane (when mirrored) → check reflective BC momentum-flip index at y=0; if asymmetry appears at y=0.25 wall instead, that is the upper channel wall and is expected to develop a separate reflected-shock structure
- Visual differs from literature but wave structure is qualitatively right → accept; record under "known differences" in `week5-verification.md`

### Layer 3 — Harness pipeline smoke

Goal: drive the full `config → build → run → measure → aggregate → plot` pipeline on Week 5 cases to expose harness edge cases on new cases (cheaper to find now than during Week 7 large-scale data collection).

**Matrix file** `experiments/week5/smoke/matrix.json` (new):

```json
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
```

**Pass criteria**:
1. `python scripts/run_matrix.py experiments/week5/smoke/matrix.json --dry-run` produces 6 `runs/<run>/config.cfg` + `runs/<run>/metadata.json`, no stderr
2. Live run: 6 runs all return 0; each run dir under `experiments/week5/smoke/runs/` contains `stdout.txt`, `stderr.txt`, `grid.bin`, `metadata.json`
3. `experiments/week5/smoke/matrix_summary.json` lands at the experiment root (written by `run_matrix.py:162`) — contains experiment name, git commit, output_root, and per-run return codes
4. Each `metadata.json` includes git commit hash, source/run cfg paths, raw output path, and `timing.total_s`; the verbatim generated cfg is stored as sibling `config.cfg`
5. `python scripts/aggregate_metrics.py --output experiments/week5/smoke/summary.json experiments/week5/smoke/runs/*/metadata.json` produces aggregated 6-run summary
6. `plot_2d.py` produces a ρ-PNG for each `grid.bin` under `experiments/week5/smoke/figures/`

**Failure fallback**:
- `run_matrix.py` crashes on shock-bubble (long path / nested dirs) → fix the harness, not the cfg; record in `INDEX.md` §7 pitfalls
- aggregator schema mismatch on new case → fix aggregator, keep backward compatibility

### Reproduction doc — `docs/week5/week5-verification.md`

Mirror `week4-verification.md` format:

```
1. Build (CPU + CUDA)              # full cmake commands + expected build output
2. Unit tests                       # three build dirs + expected case/assertion counts
3. Solver baselines                 # Layer 2 commands + expected stdout/stderr snippets + reference PNGs
4. Harness matrix smoke             # Layer 3 four steps + expected file landings
5. plot_2d.py                       # Python smoke + expected PNG list
6. Known differences / follow-ups   # things to revisit in Week 6
```

### Definition of Done (Week 5 closes when all hold)

1. Layer 1 all tests pass (CPU double + CPU float + CUDA build)
2. Layer 2 baselines each succeeded at least once + reference PNGs embedded in `week5-verification.md`
3. Layer 3 matrix smoke: all 6 runs land + summary aggregated
4. `docs/INDEX.md` Week 5 row added; `docs/requirement/overall.md` Config 6 supersonic row corrected
5. Author has manually executed `week5-verification.md` end-to-end (LLM execution does not count)
6. `week5-summary.md` filled with this week's commits + experiment paths

---

## 4. Execution Order & Timeline (Approach 2, 5 working days)

"Day" = work-day unit; can compress or expand on actual progress, but ordering must not change.

### Day 1 — CUDA toolchain smoke + Timer

**Tasks**: Block D.1 (CUDA toolchain) + Block A (Timer)

**Done criteria**:
- `./build-cuda/gpu_smoke` prints local GPU name + compute capability
- `./build-double/unit_tests "[timer]"` passes
- A Sod run: `./build-double/hrsc tests/cases/toro_1d/sod.cfg` stderr includes `[timing] total_s=...` (top-level `Timer` is unconditional; `HRSC_ENABLE_PROFILING` may stay default OFF for this check)

**Day 1 risk responses**:
- nvcc / host-compiler incompatibility → fall back to WSL CUDA environment (per memory: WSL CUDA stack is in place)
- `find_package(CUDAToolkit)` fails → pass `-DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc` explicitly
- All else fails → escalate before EOD; Day 2 onwards GPU skeleton fully deferred to Week 6, Week 5 reduces to CPU-only scope (degradation, not default)

### Day 2 — Liska-Wendroff Config 6

**Tasks**: Block B + run double-precision baselines for both resolutions + correct `overall.md` Supersonic Wave Test Cases table

**Done criteria**:
- `./build-double/unit_tests "[liska_wendroff]"` passes (Config 3 doesn't regress)
- `./build-double/hrsc tests/cases/liska_wendroff_2d/config6_n200.cfg` runs to completion, `.bin` lands
- `overall.md` Config 6 row corrected

### Day 3 — Shock-bubble + plot_2d.py

**Tasks**: Block C + Block E + run shock-bubble HLLC and Rusanov baselines + generate 12 PNGs (Config 6 × 2 resolutions × 3 fields = 6; shock-bubble × 2 solvers × 3 fields = 6)

**Done criteria**:
- `./build-double/unit_tests "[shock_bubble]"` passes
- `pytest tests/py/test_plot_2d.py` passes
- 12 PNGs land under `experiments/week5/baselines/figures/`; Config 6 visually matches LW 2003 contact-only structure, and shock-bubble shows plausible single-fluid shock/light-bubble interaction (mirror about y=0 in the figure caption to interpret as full bubble)

### Day 4 — GPU data path (Block D.2)

**Tasks**: `cuda_utils.cuh` + `gpu_grid.cuh` + `euler_kernels.cuh` (`device_copy_kernel` only) + `test_gpu_roundtrip.cu` + conditional CMake wiring

**Done criteria**:
- `cmake --build build-cuda` succeeds (with `unit_tests` GPU section)
- `./build-cuda/unit_tests "[gpu]"` passes
- CPU-only builds (`build-double`, `build-float`) still pass — confirms conditional compilation didn't break CPU path

### Day 5 — Harness smoke + documentation closure

**Tasks**:
- Write `experiments/week5/smoke/matrix.json` (6 runs)
- Run dry-run + live + aggregate + plot
- **After `summary.json` and the 6 figures land**, programmatically remove the smoke `grid.bin` files (HARNESS.md §6 transient-data discipline; `baselines/` `.bin` files are kept untouched):
  ```bash
  find experiments/week5/smoke/runs -name 'grid.bin' -delete
  ```
  Run this command from the `week5-verification.md` Section 4 so future reproductions enforce the same discipline rather than relying on manual cleanup.
- Write `docs/week5/week5-verification.md` (Layer 1/2/3, command-by-command, expected outputs; embed the cleanup command as the last step of Section 4)
- Write `docs/week5/week5-summary.md` (commits + experiment paths + W5 → W6 handoff; record the smoke retention policy explicitly)
- Update `docs/INDEX.md` §2 table (add Week 5 row)
- **Author manually walks through `week5-verification.md` from scratch** (cannot be skipped)
- PR / merge per `superpowers:finishing-a-development-branch`

**Done criteria** = Week 5 Definition of Done (§3, six items)

### Cross-day buffer & degradation

If any day overruns, Day 5 docs may be slightly compressed (keep `week5-verification.md`, simplify `week5-summary.md`), but **Layer 3 harness smoke must not be dropped**.

| Trigger | Response |
|---|---|
| Day 1 CUDA toolchain fails and fallback also fails | Move D.1/D.2 to Week 6; Week 5 narrows to A+B+C+E + Layer 1/2/3 (no GPU) |
| Day 2 Config 6 IC physics keeps failing | Skip visual verification (keep impl + unit test + cfg); mark as "Week 6 to revisit"; do not block downstream |
| Day 3 shock-bubble visual differs significantly from literature | As above; record under known-differences; revisit Week 6 |
| Day 4 GPU roundtrip not byte-identical | **Cannot skip**; likely exposes `Grid2D` layout or `HD_FUNC` device-context issue. If unresolved by EOD, mark D.2 "not passing", first item for Week 6 |
| Whole week behind by 1 day | Defer shock-bubble Rusanov twin to Week 6 (HLLC twin is mandatory) |

### Week 5 → Week 6 implicit deliverables (set up this week, used next week)

This week's interfaces are designed so Week 6 doesn't rediscover problems:

- `GpuGrid` layout matches `Grid2D` → Week 6 BC / reconstruction kernels can be written directly on top, no rearrangement
- `HRSC_CUDA_CHECK` defined once, reused by all Week 6 kernels
- `Timer` already records wall-clock → Week 6 GPU solver gets timing-vs-CPU for free
- Harness matrix smoke is green → Week 6 GPU baselines just append rows; aggregate / plot path is unchanged
- `plot_2d.py` single-responsibility → Week 6 GPU outputs reuse the same visualisation; CPU/GPU diff uses existing `phase_error_metrics.py`

---

## 5. Risk Register, Out-of-scope, Archival, Skill Hand-off

### 5.1 Risk register

| # | Risk | P | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Local CUDA toolchain doesn't work (nvcc/host compiler, CMake can't find toolkit) | M | High (blocks Block D) | Day 1 smoke exposes; WSL CUDA fallback; worst-case degradation per §4 |
| R2 | LW Config 6 IC physically wrong (mistyped quadrant table, u/v sign, γ default) | L | M | Per-cell unit test against IC table; visual against LW 2003 Fig. 6 |
| R3 | Shock-bubble physics off (RH post-shock, reflective BC momentum-flip index) | M | M | Unit test RH to 1e-12; HLLC vs Rusanov double-run as sanity |
| R4 | GPU roundtrip not byte-identical (Grid2D padding/alignment, `HD_FUNC` device behaviour) | L | High (memory-model bug) | Day 4 unit test must pass; if not, halt Week 5 GPU progress, first item Week 6 |
| R5 | Harness crashes on new case (long cfg name, nested path) | L | L | Dry-run before live; fix the harness, not the cfg |
| R6 | Timer integration changes solver numeric default (violates AGENTS.md rule 1) | L | High | Timer is wall-clock only, never on algorithmic path; `HRSC_ENABLE_PROFILING` default OFF; CI covers default build |
| R7 | overall.md Config 6 correction triggers inconsistencies elsewhere (Report 1 draft, table-generator comments) | L | L | grep `Config 6` repo-wide and update all supersonic markers in one pass |
| R8 | Scope drift — temptation to write Week 6 BC kernels | L | M | Spec lists out-of-scope explicitly (§5.2); PR self-review against this list |

### 5.2 Out of scope (explicitly NOT in Week 5)

- **GPU**: `__device__` `HD_FUNC` instantiation, BC kernel, reconstruction kernel, HLLC kernel, CFL reduction kernel, `EulerGpuSolver` class, CPU↔GPU baseline diff, CSC GPU node build → all Week 6
- **MHD**: any `src/mhd/` files, Brio-Wu cfg, HLL/HLLD → Week 12+
- **Verificarlo carry-over**: `vfc_precexp`, unstable-branch detection → Week 14 (unless MHD pulled forward)
- **Other Liska-Wendroff configs** (4, 12, 17, …) → Week 6 if needed
- **Batch plotting / publication-grade multi-panel figures** → Week 7+
- **Quad precision (1D)** → Week 17 secondary
- **CFL / limiter / OpenMP thread-count sensitivity** → Week 17 secondary
- **Performance benchmarking / cross-build speed analysis**: this week Timer collects data only; analysis is Week 7

### 5.3 Archival checklist (must exist when Week 5 closes)

```
docs/
├── INDEX.md                             # MODIFIED: §2 table gains Week 5 row
├── requirement/
│   └── overall.md                       # MODIFIED: Supersonic Wave Test Cases Config 6 + Week 5 footnote
└── week5/
    ├── week4_to_week5_bridge.md         # untouched
    ├── week5-plan.md                    # THIS spec
    ├── week5-verification.md            # produced Day 5
    └── week5-summary.md                 # produced Day 5

experiments/week5/
├── baselines/
│   ├── lw_config6_n200/grid.bin
│   ├── lw_config6_n400/grid.bin
│   ├── shock_bubble_n400x100_hllc/grid.bin
│   ├── shock_bubble_n400x100_rusanov/grid.bin
│   └── figures/                         # 12 PNGs (Config6 × 2 res × 3 fields + shock-bubble × 2 solver × 3 fields)
└── smoke/
    ├── matrix.json
    ├── runs/
    │   ├── lw3-d-200/{config.cfg,metadata.json,stdout.txt,stderr.txt,grid.bin}
    │   ├── lw3-f-200/...
    │   ├── lw6-d-200/...
    │   ├── lw6-f-200/...
    │   ├── sb-d-400/...
    │   └── sb-f-400/...
    ├── summary.json
    └── figures/                         # 6 PNGs (one ρ-plot per run)
```

Per HARNESS.md §6: `baselines/` `.bin` files are reference data and are kept; `smoke/` `.bin` files are transient and may be deleted after `summary.json` lands. Retention policy is recorded in `week5-summary.md`.

### 5.4 Skill hand-off after this spec

- `superpowers:writing-plans` — turns this spec into an executable Day 1–5 implementation plan
- During implementation: `superpowers:test-driven-development` (Layer 1 unit tests first), `superpowers:verification-before-completion` (end-of-day self-check)
- At Week 5 closure: `superpowers:finishing-a-development-branch` (merge / PR strategy)

Branch policy: continue work on `week4-implementation` (already open from last week's merge cycle); rename/cut a `week5-implementation` branch only if Day 5 PR strategy calls for it.
