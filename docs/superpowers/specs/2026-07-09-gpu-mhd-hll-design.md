# GPU MHD (HLL) Solver — Design

**Date:** 2026-07-09
**Branch base:** `week12-mhd-implementation` (Week-15 CPU precision study report-grade; see [week15-supervisor-report.md](../../week15/week15-supervisor-report.md))
**Requirement:** [overall.md](../../requirement/overall.md) §Week 14 (GPU MHD) + §Week 15 primary axis **hardware (CPU vs GPU)** — the fourth and only uncovered primary axis of the systematic precision study. Report 2 "Computational Results" (40%) needs CPU+GPU MHD validation (float+double).
**Decisions carried forward:** the Week-6 Euler GPU path is the architectural template ([week6-summary.md](../../week6/week6-summary.md)): opt-in `ENABLE_CUDA`, `device=cpu|gpu` cfg key, separate kernels per step, deterministic tree reduction for CFL, and `--fmad=false` on the kernel TU to match MSVC `/fp:precise` so CPU-vs-GPU is bit-exact (Euler achieved `ulp_max=0`).
**Supervisor-approved scope (2026-07-09):** **HLL only** first; HLLD-on-GPU is a planned follow-up, not this deliverable. CUDA toolkit installed locally (RTX 5070, Blackwell sm_120).

---

## 1. Goal & scope boundary

Deliver a **GPU HLL MHD solver** that runs Brio-Wu 1D and Orszag-Tang 2D in
float and double, gated by a **CPU-vs-GPU same-precision agreement check**, thereby
adding the **hardware axis** to the existing report-grade precision packets. The
deliverable is the GPU solver + its validation gate, not new solver physics — the
GPU path must reproduce the already-validated CPU HLL numerics.

### In scope

- Local **CUDA Toolkit install** (sm_120 / Blackwell) + toolchain validation via the existing `gpu_smoke` target.
- `src/gpu/mhd_kernels.{cuh,cu}` + `src/gpu/mhd_gpu_solver.{hpp,cu}` — GPU HLL MHD solver mirroring `EulerGpuSolver`: MUSCL reconstruct → Hancock predict → **HLL** flux (9 MHD vars) → conservative update → **GLM source step** (full-grid div(B)) → CFL deterministic tree reduction.
- `mhd_main.cpp` `device=cpu|gpu` dispatch mirroring `src/main.cpp` (default `cpu`; `device=gpu` without `-DENABLE_CUDA=ON` throws a clear error).
- CMake wiring under `if(ENABLE_CUDA)` with `--fmad=false` on the MHD kernel TU.
- `[gpu]`-tagged Catch2 unit tests per kernel against the CPU oracle, plus an end-to-end CPU-vs-GPU regression (Brio-Wu 1D + OT 2D, float+double).

### Out of scope (stated so the plan cannot quietly grow)

- **HLLD-on-GPU** (planned follow-up within this sub-project, separate plan).
- Kelvin-Helmholtz; 512² runs; the full 48-variant GPU precision sweep; GPU-side MCA (Verificarlo is a CPU tool); temporal-divergence/Lyapunov (Week 16).
- Changing any CPU solver numerics, cfg default, or output format.

### Unchanged surface (hard constraint)

`src/mhd/*` CPU numerics; all existing cfg files and defaults; `io.hpp` output
format; the Euler `hrsc`/`gpu` path; `build_all.sh`. Default CPU-only builds must
be byte-identical to today (all GPU code is behind `ENABLE_CUDA` / `HRSC_HAS_CUDA`).

---

## 2. Verified preconditions (facts this design relies on)

| Fact | Evidence |
|---|---|
| The Euler GPU path is a complete template: `ENABLE_CUDA` option, `cmake/CUDASetup.cmake` + `hrsc_configure_cuda_toolkit()`, kernels compiled as CUDA TUs into `hrsc_euler`, `--fmad=false` on the kernel TU for CPU-vs-GPU bit-exactness, `device` cfg dispatch. | [CMakeLists.txt:115-180](../../../CMakeLists.txt#L115-L180), [src/main.cpp:297-421](../../../src/main.cpp#L297) |
| Euler CPU-vs-GPU same-precision agreement reached `ulp_max=0` for Sod + LW3 in float and double — the bit-exact target for MHD. | [week6-summary.md](../../week6/week6-summary.md) §G3 |
| `CMAKE_CUDA_ARCHITECTURES=native` (CMake ≥3.24) auto-detects the host GPU arch, so the RTX 5070 targets sm_120 automatically once the toolkit supports it; explicit `120` is the fallback. | [cmake/CUDASetup.cmake:13-22](../../../cmake/CUDASetup.cmake#L13) |
| The CPU MHD solver interface to mirror: `MhdSolver<Real, Flux>` (Flux is a template functor), 1D + 2D constructors, `step()`/`run()`/`grid_view()`/`time()`/`step_count()`, internal `x_sweep`/`y_sweep`/GLM; `MhdRiemann{Hll,Hlld}` + `parse_mhd_riemann`. | [src/mhd/mhd_solver.hpp:32-77](../../../src/mhd/mhd_solver.hpp#L32) |
| `hrsc_mhd` is a default target; GPU MHD sources attach to `hrsc_mhd_lib` only under `if(ENABLE_CUDA)`, exactly as Euler GPU sources attach to `hrsc_euler`. | [CMakeLists.txt:89-104,160-179](../../../CMakeLists.txt#L89) |
| Reusable GPU infra exists: `src/gpu/cuda_utils.cuh` (error-check macro, DeviceArray), `src/gpu/gpu_grid.cuh` (device Grid2D mirror, host↔device transfer). | [src/gpu/cuda_utils.cuh](../../../src/gpu/cuda_utils.cuh), [src/gpu/gpu_grid.cuh](../../../src/gpu/gpu_grid.cuh) |
| The driver GPU dispatch precedent: `device=gpu` builds the IC host-side, hands it to the GPU solver, runs, downloads, shares the CPU output path; limiter selection is cpu-only (GPU uses the default limiter). | [src/main.cpp:302-421](../../../src/main.cpp#L302) |
| RTX 5070 present (Blackwell, 8 GB), driver reports CUDA 13.1; `nvcc` not yet installed. | `nvidia-smi` (this workstation) |

---

## 3. Architecture & components

### 3.1 CUDA toolkit + build wiring (prerequisite)

- Install CUDA Toolkit **12.8+ or 13.x** (sm_120 support). Validate `nvcc --version` and the existing `gpu_smoke` target build+run before any solver work.
- CMake: reuse `if(ENABLE_CUDA)` block; add the MHD kernel sources to `hrsc_mhd_lib` as CUDA-language TUs with `--fmad=false` and `CUDA_ARCHITECTURES=${CMAKE_CUDA_ARCHITECTURES}`, mirroring the Euler `hrsc_euler` block verbatim. Default CPU builds untouched (everything behind `ENABLE_CUDA`).
- If `native` arch detection fails on the too-new GPU, fall back to `-DCMAKE_CUDA_ARCHITECTURES=120`.

### 3.2 GPU HLL MHD solver — mirror `EulerGpuSolver`

`src/gpu/mhd_gpu_solver.{hpp,cu}` exposes an `MhdGpuSolver<Real>` with the same
lifecycle as `EulerGpuSolver<Real>`: construct from a host-side IC Grid2D
(`MhdNVars=9`), `run()`/`step()` on device, download to a host grid via
`gpu_grid.cuh`. `src/gpu/mhd_kernels.{cuh,cu}` holds **separate kernels per step**
(not fused — for debugging + precision isolation, per overall.md):

1. `apply_bc` (per-axis; GLM psi BCs: outflow→psi=0 at ghosts, periodic wraps)
2. `reconstruct` (MUSCL, default limiter — matches CPU default; limiter selection stays cpu-only)
3. `hancock_predict` (half-step predictor)
4. `hll_flux` (9-var HLL two-wave, incl. psi hyperbolic transport at c_h)
5. `conservative_update` (x-sweep, y-sweep for 2D via Lie splitting)
6. `glm_source` (full-grid div(B) = ∂Bx/∂x+∂By/∂y, then integrate `∂ψ/∂t = -c_h²∇·B - (c_h/c_p)ψ`)
7. `cfl_reduce` (**deterministic tree reduction**, no atomics — reproducible max wave speed)

16×16 thread blocks (Euler convention). `--fmad=false` on the TU so multiply-adds
match the MSVC `/fp:precise` CPU oracle.

### 3.3 Driver dispatch

`mhd_main.cpp` adds `device = cfg.get_string("device","cpu")`; `device=gpu` under
`#ifdef HRSC_HAS_CUDA` builds the IC, runs `MhdGpuSolver`, downloads, and reuses
the existing divB-norm + binary-write path (so the output format is identical to
CPU). `device=gpu` in a non-CUDA build throws
`"device=gpu requires building with -DENABLE_CUDA=ON"`. Default `device=cpu`
path is unchanged.

---

## 4. Data flow, gates & success criteria

### Validation gate (core)

**G-GPU (hard): CPU-vs-GPU same-precision agreement.** For each
(case, precision) the GPU output must match the CPU output field-by-field. Target
is **`ulp_max=0`** (as Euler achieved), enforced via `--fmad=false`. If bit-exact
proves unreachable for the 9-var + GLM path, the gate falls back to a **tight
relative tolerance** (documented, e.g. ≤ few ULP) and any exceedance is
investigated as a bug — the tolerance is never widened to hide a discrepancy.

- **Per-kernel unit tests** (`[gpu]` tag): reconstruct / predict / HLL flux / update / GLM source / CFL reduction each compared to the CPU oracle on small fixed inputs.
- **End-to-end regression:** Brio-Wu 1D + Orszag-Tang 2D, float + double, CPU vs GPU, reusing the existing MHD binary-read + field-diff tooling. Reuses the G0 anchor gate (steps/divB_max) on the GPU run too.

### Success criteria

GPU HLL MHD builds under `-DENABLE_CUDA=ON`; `gpu_smoke` validates the toolchain;
all `[gpu]` MHD unit tests pass; Brio-Wu 1D + OT 2D run on GPU in float+double and
reproduce the CPU result within the G-GPU gate; default CPU-only build + existing
tests remain green (no regression); docs registered.

---

## 5. Error handling & risks

| Risk / failure | Mitigation |
|---|---|
| sm_120 too new for the installed CUDA/MSVC combo | `--allow-unsupported-compiler` (already in the CMake CUDA block); install CUDA 12.8+/13.x; explicit `CUDA_ARCHITECTURES=120` fallback. |
| GLM multi-dim source-step reduction order breaks CPU-vs-GPU bit-exactness | Deterministic tree reduction (no atomics) + `--fmad=false`; if still not bit-exact, tight documented relative-tolerance gate + investigate. |
| 9-var + GLM more complex than Euler → `ulp_max=0` unreachable | G-GPU degrades to a tight relative tolerance (documented), never widened silently. |
| GPU work destabilises the default CPU build | All GPU code behind `ENABLE_CUDA`/`HRSC_HAS_CUDA`; a no-CUDA build + full CPU test pass is a required gate. |
| Scope creep to HLLD/KH/full sweep | Explicit out-of-scope list (§1); HLLD-on-GPU is a separate follow-up plan. |
| CUDA install churn on the workstation | Prerequisite task gated by `gpu_smoke` before any solver work; if install blocks, stop and report (do not fake GPU evidence). |

---

## 6. Testing strategy

TDD where the unit boundary allows (pure device kernels tested against a CPU
oracle on fixed small inputs, `[gpu]` tag so they no-op on CPU-only builds). The
end-to-end CPU-vs-GPU regression is command-level (build both, run both, diff
fields, assert the G-GPU gate + G0 anchor). The default CPU-only build with the
full existing suite green is a hard non-regression gate at every step.

---

## 7. Follow-ups (explicitly after this deliverable)

1. **HLLD-on-GPU** — add the 5-wave fan kernel, same G-GPU gate.
2. GPU precision packets — re-point the Week-15 Brio-Wu + OT precision packets at `device=gpu` to populate the hardware axis (float+double), producing the CPU-vs-GPU comparison rows for Report 2.
3. Kelvin-Helmholtz 2D; temporal-divergence/Lyapunov (Week 16).

## 8. References

- [week6-summary.md](../../week6/week6-summary.md) — Euler GPU bring-up (template, `ulp_max=0`, `--fmad=false`).
- [overall.md](../../requirement/overall.md) §Week 14/15 — GPU MHD + hardware axis.
- Dedner et al. 2002, *JCP* 175, 645 — GLM divergence cleaning.
- Miyoshi & Kusano 2005, *JCP* 208, 315 — HLLD (follow-up only).
