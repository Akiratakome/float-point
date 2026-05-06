# Week 6 Summary

**Calendar:** 2026-05-04 to 2026-05-10  
**Branch:** `week5-implementation`  
**Closeout checked:** 2026-05-06

Week 6 landed the opt-in CUDA Euler path, strict-IEEE CPU/CUDA build helpers,
GPU kernel/unit coverage, local CPU-vs-GPU regression summaries, CSC replay
scripts, and the Week 6 verification recipe. The default CPU path remains the
compatibility baseline: `device` defaults to `cpu`, `ENABLE_CUDA` defaults to
OFF, `STRICT_IEEE` defaults to OFF, and profiling is behind
`HRSC_ENABLE_PROFILING`.

## Acceptance Gates

| Gate | Status | Evidence |
|---|---|---|
| G1. CPU-strict + CUDA builds clean | Pass locally | `build-cpu-strict-{double,float}` and `build-cuda-{double,float}-strict` exist; rebuilds complete locally. |
| G2. Unit tests green | Pass locally | CUDA strict `[gpu]` tests pass for double and float; CPU strict non-GPU test binaries run locally. |
| G3. Local smoke/regression green | Pass | `experiments/week6/regression/summary.md`: 4/4 CPU-vs-GPU pairs `gate_passed=True`, `ulp_max=0`. |
| G4. CSC smoke | Pending on current GitHub branch | `scripts/cluster/build_gpu_csc.sh`, `scripts/cluster/run_gpu_smoke.slurm`, and `experiments/week6/csc_smoke/matrix.json` are committed. No `experiments/week6/csc_smoke/summary.{md,json,csv}` is present on `origin/week5-implementation` as of this closeout. |
| G5. cfg-default byte identity | Pass | `docs/week6/week6-verification.md` records identical default CPU stdout md5s across Week 6 changes. |
| G6. Timer phase split | Pass | Profiling recipe in `docs/week6/week6-verification.md`; phase probes are gated by `HRSC_ENABLE_PROFILING`. |
| G7. LW Config 4 / 12 landed | Pass | `tests/unit/test_lw_config4.cpp`, `tests/unit/test_lw_config12.cpp`, and cfgs at n200/n400. |
| G8. Documentation closed | Pass with G4 caveat | This summary, verification recipe, CSC environment probe, and INDEX links are present. |

## Deliverables

| Area | Evidence |
|---|---|
| Device dispatch | `src/main.cpp`, `tests/unit/test_dispatch_device_key.cpp` |
| CUDA solver orchestration | `src/gpu/euler_gpu_solver.hpp`, `src/gpu/euler_gpu_solver.cu` |
| CUDA kernels | `src/gpu/euler_kernels.cuh`, `src/gpu/euler_kernels.cu` |
| Strict build matrix | `cmake/CompilerFlags.cmake`, `scripts/build_all.sh` |
| GPU unit tests | `tests/unit/test_gpu_*.cpp`, `tests/unit/gpu_layout_kernel.cu` |
| Device regression report | `scripts/regression/float_regression_report.py`, `tests/py/test_float_regression_report_device_mode.py` |
| Local regression artefacts | `experiments/week6/regression/summary.{md,json,csv}` |
| CSC replay artefacts | `docs/week6/csc_gpu_environment.md`, `scripts/cluster/build_gpu_csc.sh`, `scripts/cluster/run_gpu_smoke.slurm`, `experiments/week6/csc_smoke/matrix.json` |
| Verification docs | `docs/week6/week6-verification.md` |

## Commit Inventory

| Task range | Commits |
|---|---|
| T1-T4 | `45e9eb5`, `66213a2`, `d7e3d4c`, `77db97e` |
| T5-T8 | `e445c50`, `19c0767`, `3aa4530`, `ed8b076` |
| T9-T10 | `b9668b6`, `e446169` |
| T11-T12 | `669146f`, `8cb615d`, `5b94ab0` |
| T13-T19 | `e976ff8`, `039d6f9`, `6a9af9b`, `d6f0e6a`, `02ff6ea`, `26bcd04`, `0b0ccf6`, `958a1c9`, `c24df58`, `09dc956`, `6071854` |
| T20-T23 | `2f0d662`, `ab102d0`, `6018079`, `2ba72dd`, `d0d4121` |
| T26-T29 | `b87909c`, `6dacaa3` |
| Closeout review | Fixes after review remove the stale HLLC GPU CLI guard and add this summary/INDEX update. |

## Review Notes

- Local device regression summary shows exact CPU-vs-GPU agreement for Sod and
  LW Config 3 in float and double.
- The HLLC GPU kernels and unit tests exist. A stale `main.cpp` guard blocking
  `device=gpu` with `solver=hllc` was removed during closeout review so cfg
  dispatch matches the available kernel path.
- CSC execution evidence is not visible in the current GitHub branch. If CSC
  results were produced elsewhere, copy `summary.{md,json,csv}` into
  `experiments/week6/csc_smoke/` and commit them as a follow-up.

## Carry-Forward

- Replay CSC smoke if the result summary remains absent from GitHub.
- Extend the Week 7 experiment matrix to fast-math and HLLC-vs-Rusanov GPU
  comparisons.
- Keep large `.bin` grids transient; commit summaries, metadata, and figures
  only when they are deliverable artefacts.
