# Week 6 Summary

**Calendar:** 2026-05-04 to 2026-05-10
**Development branch:** `week5-implementation`
**Integrated to main:** `ba118da` (`merge: week4/week5 implementation into main`)
**Final checked:** 2026-05-06

Week 6 completed the CUDA Euler solver bring-up and CSC smoke replay while
preserving the CPU compatibility baseline. New CUDA, strict-IEEE, and profiling
paths are opt-in:

- `device` defaults to `cpu`.
- `ENABLE_CUDA` defaults to `OFF`.
- `STRICT_IEEE` defaults to `OFF`.
- `HRSC_ENABLE_PROFILING` defaults to `OFF`.

The harness shape remains `config -> build -> run -> measure -> aggregate ->
plot`. Large Week 6 run grids were cleaned after summaries were generated; no
Week 6 `.bin` files are tracked.

## Acceptance Gates

| Gate | Status | Evidence |
|---|---|---|
| G1. CPU-strict + CUDA builds clean | Pass | Local strict CPU/CUDA builds were exercised; CSC strict CUDA builds ran through `scripts/cluster/build_gpu_csc.sh`. |
| G2. Unit tests green | Pass | CPU double/float default tests, CUDA double/float `[gpu]` tests, and profiling tests pass. |
| G3. Local CPU-vs-GPU smoke/regression | Pass | `experiments/week6/regression/summary.md`: 4/4 pairs `gate_passed=True`, all `ulp_max=0`. |
| G4. CSC smoke | Pass | `experiments/week6/csc_smoke/summary.{md,json,csv}`, `matrix_summary.json`, `slurm_logs/10414.{out,err}`, and 4 generated run cfg/metadata/stderr sets. |
| G5. Default CPU byte identity | Pass | Default Sod stdout MD5 remains `FD58E1A9398178E54E5B761AE9D87959`. |
| G6. Timer phase split | Pass | Profiling build emits `[timing] total_s=...` plus `phase=bc/cfl/flux/sweep/update`. |
| G7. LW Config 4 / 12 | Pass | `config4_n{200,400}.cfg`, `config12_n{200,400}.cfg`, IC dispatch, and unit tests are present. |
| G8. Documentation closed | Pass | `week6-plan.md`, `week6-design.md`, `week6-verification.md`, `csc_gpu_environment.md`, this summary, CSC artefacts, and `docs/INDEX.md` links are present. |

## Delivered

| Area | Files / Artefacts |
|---|---|
| GPU dispatch | `src/main.cpp`, `tests/unit/test_dispatch_device_key.cpp` |
| GPU solver orchestration | `src/gpu/euler_gpu_solver.hpp`, `src/gpu/euler_gpu_solver.cu` |
| CUDA kernels | `src/gpu/euler_kernels.cuh`, `src/gpu/euler_kernels.cu` |
| GPU data structures | `src/gpu/cuda_utils.cuh`, `src/gpu/gpu_grid.cuh` |
| Strict-IEEE build path | `cmake/CompilerFlags.cmake`, `cmake/CUDASetup.cmake`, `scripts/build_all.sh` |
| GPU unit coverage | `tests/unit/test_gpu_*.cpp`, `tests/unit/gpu_layout_kernel.cu`, `tests/unit/gpu_roundtrip_kernel.cu` |
| Device regression report | `scripts/regression/float_regression_report.py`, `tests/py/test_float_regression_report_device_mode.py` |
| Local regression summaries | `experiments/week6/regression/summary.{md,json,csv}` |
| CSC smoke artefacts | `experiments/week6/csc_smoke/summary.{md,json,csv}`, `matrix_summary.json`, `slurm_logs/10414.{out,err}`, run cfg/metadata/stderr |
| New 2D cases | `tests/cases/liska_wendroff_2d/config4_*`, `config12_*`, `tests/unit/test_lw_config4.cpp`, `tests/unit/test_lw_config12.cpp` |
| Profiling phase output | `src/utils/timer.hpp`, `src/main.cpp`, `tests/unit/test_profiling_phases.cpp` |

## Verification Record

Final verification on integrated `main`:

```text
cmake -B build-final-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=OFF
cmake --build build-final-double --target unit_tests hrsc
.\build-final-double\unit_tests.exe -r compact
Passed all 128 test cases with 11925 assertions.

cmake -B build-final-float -G Ninja -DFLOAT_PRECISION=float -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=OFF
cmake --build build-final-float --target unit_tests hrsc
.\build-final-float\unit_tests.exe -r compact
Passed all 128 test cases with 11925 assertions.

python -m pytest tests/py -q
53 passed, 4 skipped

.\build-cuda-double-strict\unit_tests.exe "[gpu]" -r compact
Passed all 43 test cases with 63741 assertions.

.\build-cuda-float-strict\unit_tests.exe "[gpu]" -r compact
Passed all 38 test cases with 63729 assertions.
```

Default CPU compatibility check:

```text
.\build-final-double\hrsc.exe tests/cases/toro_1d/sod.cfg
stdout MD5: FD58E1A9398178E54E5B761AE9D87959
stderr: [timing] total_s=...
stderr: Finished: 137 steps, t = 0.25
```

CSC smoke evidence:

```text
lw3-gpu-csc-d  returncode=0
lw3-gpu-csc-f  returncode=0
sod-gpu-csc-d  returncode=0
sod-gpu-csc-f  returncode=0
```

Both local and CSC device-regression summaries report `ulp_max=0` for Sod and
LW Config 3 in double and float.

## Compatibility Notes

- The default solver/cfg path remains CPU and non-CUDA.
- Existing output formats are unchanged for normal runs. Timing remains on
  stderr; profiling phase detail appears only in profiling-enabled builds.
- `scripts/run_matrix.py` continues to copy source cfgs and writes generated
  per-run cfgs/metadata rather than editing source cfgs in place.
- Week 6 run-directory `.bin` payloads are transient. Summaries, generated cfgs,
  metadata, stderr, and SLURM logs are the retained artefacts.

## CSC Environment Notes

- Real GPU partition observed: `csc-mphil-gpu`.
- Do not use the stale plan default `ampere`.
- Non-interactive CSC SSH did not consistently expose `module` or `nvcc`.
  `scripts/cluster/build_gpu_csc.sh` therefore probes `/lsc/opt/cuda-12.9` and
  accepts `HRSC_CUDA_HOME` / `HRSC_CUDA_ARCH` overrides.

## Carry-Forward

- Week 7 should extend the experiment matrix to fast-math and HLLC-vs-Rusanov
  GPU comparisons.
- HLLC `<=` vs `<` GPU systematic study remains part of the Week 7/Report 1
  matrix.
- Keep future large grids transient unless explicitly promoted to reference
  data needed to reproduce a metric.
