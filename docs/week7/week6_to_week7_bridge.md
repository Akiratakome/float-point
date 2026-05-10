# Week 6 -> Week 7 Bridge

**Date:** 2026-05-09
**Source docs:** `docs/week6/week6-plan.md`, `docs/week6/week6-summary.md`, `docs/requirement/overall.md`
**Target phase:** Week 7: Report 1 experiments and data collection

本文档用于 Week 6 向 Week 7 交接，重点说明三件事：

- Week 6 已完成哪些工作，哪些不用重做。
- Week 7 可以直接复用哪些代码接口、脚本接口和实验 artefacts。
- Week 7 应如何围绕 Report 1 要求扩展实验矩阵，同时保持 Week 6 的默认兼容性。

---

## 1. Week 6 已完成工作

Week 6 已完成 `overall.md` 中 "Complete GPU Euler Solver" 的核心目标：CUDA Euler solver 已可通过 cfg 选择，CPU/GPU strict same-precision smoke 和 CSC GPU smoke 均有记录，默认 CPU 路径保持不变。

| 项目 | 状态 | 关键证据 |
|---|---|---|
| CUDA Euler solver bring-up | Done | `src/gpu/euler_gpu_solver.{hpp,cu}`, `src/gpu/euler_kernels.{cuh,cu}` |
| cfg 选择 CPU/GPU | Done | `src/main.cpp`, `device=cpu|gpu`, 默认 `cpu` |
| strict-IEEE build path | Done | `cmake/CompilerFlags.cmake`, `cmake/CUDASetup.cmake`, `scripts/build_all.sh` |
| GPU unit coverage | Done | `tests/unit/test_gpu_*.cpp`, CUDA double/float `[gpu]` tests |
| CPU-vs-GPU device regression | Done | `experiments/week6/regression/summary.{md,json,csv}` |
| CSC GPU smoke | Done | `experiments/week6/csc_smoke/summary.{md,json,csv}`, `matrix_summary.json`, SLURM logs |
| Default CPU compatibility | Preserved | Sod stdout MD5 `FD58E1A9398178E54E5B761AE9D87959` |
| Profiling phase split | Done | `[timing] total_s=...`, optional `phase=bc/cfl/flux/sweep/update` |
| LW Config 4 / 12 | Done | cfgs at n200/n400, IC dispatch, unit tests |

Important compatibility outcomes:

- `ENABLE_CUDA` defaults to `OFF`.
- `STRICT_IEEE` defaults to `OFF`.
- `HRSC_ENABLE_PROFILING` defaults to `OFF`.
- `device` defaults to `cpu`.
- Normal stdout/binary output formats are unchanged.
- Week 6 `.bin` run payloads are transient; summaries, cfgs, metadata, stderr and logs are the retained artefacts.

---

## 2. Interfaces Week 7 Can Reuse Directly

### 2.1 Runtime cfg keys

| Key | Values | Week 7 use |
|---|---|---|
| `device` | `cpu`, `gpu` | CPU/GPU same-precision matrix rows |
| `solver` | `hllc`, `rusanov` | HLLC-vs-Rusanov comparisons |
| `bc`, `bc_x`, `bc_y` | `outflow`, `periodic`, `reflective` | 1D/2D case control |
| `output_format` | `table`, `binary` | Use `binary` for metrics and plots |
| `output_file` | path | Harness-generated per-run cfgs should set this |
| `progress_interval_s` | numeric | Keep small/no progress output for matrix runs |

Do not change cfg defaults in Week 7. Add explicit keys in generated cfgs instead.

### 2.2 Build interfaces

| Need | Command shape |
|---|---|
| Default CPU double | `cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release` |
| Default CPU float | `cmake -B build-float -G Ninja -DFLOAT_PRECISION=float -DCMAKE_BUILD_TYPE=Release` |
| Strict CPU/GPU | `-DSTRICT_IEEE=ON`, plus `-DENABLE_CUDA=ON` for GPU |
| Riemann branch variant | `-DRIEMANN_STRICT_INEQUALITY=ON` for `<` instead of `<=` |
| Profiling phase detail | `-DHRSC_ENABLE_PROFILING=ON` |

Week 7 should create new build dirs per axis rather than mutating old dirs. Build dirs are disposable and ignored by git.

### 2.3 Harness and reports

| Interface | Purpose |
|---|---|
| `scripts/run_matrix.py <matrix.json>` | Canonical `config -> build -> run -> measure -> aggregate` runner |
| `scripts/regression/float_regression_report.py --mode fp` | float-vs-double summaries |
| `scripts/regression/float_regression_report.py --mode device` | CPU-vs-GPU same-precision summaries |
| `scripts/figures/plot_2d.py` | 2D density/pressure/velocity/schlieren plots |
| `scripts/cluster/build_gpu_csc.sh` | CSC CUDA strict build |
| `scripts/cluster/run_gpu_smoke.slurm` | CSC GPU smoke template |

Week 7 should extend matrices and scripts around these interfaces. Avoid one-off command sequences that cannot be reproduced through matrix metadata.

### 2.4 Experiment artefacts already available

| Artefact | Use in Week 7 |
|---|---|
| `experiments/week6/regression/summary.md` | strict local CPU/GPU baseline |
| `experiments/week6/csc_smoke/summary.md` | strict CSC GPU smoke baseline |
| `experiments/week6/csc_smoke/matrix_summary.json` | run return codes and metadata |
| `experiments/week6/regression/matrix.json` | template for new device-mode matrices |
| `experiments/week6/csc_smoke/matrix.json` | template for CSC GPU rows |
| `docs/week6/week6-summary.md` | closeout status and carry-forward items |
| `docs/week6/archive/week6-verification.md` | reproduction recipe |

---

## 3. Week 7 Goal From `overall.md`

`overall.md` defines Week 7 as "Experiments + Data Collection for Report 1". The intended milestone is: all experimental data for Report 1 collected and analyzed.

The nominal Week 7 matrix is:

- Euler cases across 1D and 2D.
- `{float, double}`.
- `{CPU, GPU}`.
- `{O2, Ofast}` or the project-equivalent compiler/fast-math axis.
- Grid convergence over `N = 50, 100, 200, 400, 800` where applicable.
- L1/L2/Linf error norms, plots, convergence curves and timing.

Week 6 shifts the starting point: GPU correctness is no longer the blocker. Week 7 should therefore focus on experiment coverage, compiler/implementation variation, and Report 1 evidence quality.

---

## 4. Recommended Week 7 Execution Order

### Step 1. Freeze the strict baseline

Before expanding the matrix, rerun or cite the Week 6 strict evidence:

- Local CPU/GPU strict device summary: `experiments/week6/regression/summary.md`.
- CSC GPU strict smoke summary: `experiments/week6/csc_smoke/summary.md`.
- Default CPU Sod MD5: `FD58E1A9398178E54E5B761AE9D87959`.

This baseline is the "known-good" reference. Any fast-math, Ofast, `<`/`<=`, or solver-branch experiment should be compared against it.

### Step 2. Build the Report 1 experiment matrix

Start with a small matrix, then expand:

1. Sod + LW Config 3.
2. Add Toro 2/3/4/5 and stationary contact.
3. Add LW Config 4/6/12 or shock-bubble only if needed for Report 1 figure coverage.
4. Add GPU rows after the CPU matrix is stable.
5. Add CSC rows after local GPU rows are reproducible.

Keep the matrix file explicit. Each row should record:

- case name and cfg source
- precision
- device
- solver
- build label
- compiler/fast-math flags
- output path
- expected metric/report path

### Step 3. Add compiler and implementation variation carefully

High-priority Week 7 axes:

| Axis | Why it matters |
|---|---|
| strict vs fast-math / Ofast | Report 1 hardware/compiler reproducibility evidence |
| HLLC vs Rusanov | Supervisor-facing interpretation and solver sensitivity |
| HLLC `<=` vs `<` | Directly tied to known branch sensitivity at `S* = 0` |
| CPU vs GPU | Report 1 mandatory hardware comparison |
| float vs double | Report 1 mandatory precision comparison |

Do not widen pass/fail thresholds to make new rows pass. Record actual deltas and classify them as evidence.

### Step 4. Generate Report 1 artefacts, not just raw runs

For every matrix family, produce the artefacts Report 1 can cite:

- `summary.md` for human-readable evidence.
- `summary.json` / `summary.csv` for traceability.
- profile plots for 1D cases.
- 2D pseudocolor/difference maps for LW cases.
- convergence curves where multiple `N` values exist.
- timing tables using `[timing] total_s`.

Large `.bin` files should remain transient unless explicitly promoted to reference data.

### Step 5. Keep synchronized-time comparisons honest

For drift, CPU/GPU, solver-variant, or compiler-variant comparisons:

- Compare outputs at the same physical time.
- Reject or flag mismatched checkpoint times before measuring norms.
- Treat single final-state differences as final-state smoke, not fitted growth rates.
- Only claim a Lyapunov-like rate when there are multiple synchronized output times.

---

## 5. Week 7 Guardrails

1. **Do not change default behaviour.** CPU, non-CUDA, non-strict builds remain the compatibility baseline.
2. **Do not edit source cfgs in place during matrix runs.** Let `run_matrix.py` copy and generate per-run cfgs.
3. **Do not commit large transient grids.** Keep summaries, metadata, logs, figures and small CSVs.
4. **Do not mix strict and fast-math evidence in one gate.** They answer different questions.
5. **Do not treat CSC queue/toolchain issues as numerical failures.** Record them separately.
6. **Do not skip exact/converged references for validation tables.** Report 1 needs interpretable error norms, not only pairwise differences.
7. **Do not overclaim CPU/GPU equality beyond the tested build flags.** Week 6 proves strict same-precision smoke; fast-math and Ofast still need their own rows.

---

## 6. Suggested Week 7 Deliverables

| Deliverable | Suggested location |
|---|---|
| Week 7 operational plan | `docs/week7/week7-plan.md` |
| Report 1 evidence map | `docs/experiment_logs/report1_evidence_index.md` |
| Full experiment matrix | `experiments/week7/<matrix_name>/matrix.json` |
| Precision/device summaries | `experiments/week7/<matrix_name>/summary.{md,json,csv}` |
| Figure outputs | `experiments/week7/<matrix_name>/figures/` or a focused figure directory |
| Supervisor-facing interpretation notes | `docs/experiment_logs/week7_*.md` or, if treated as Week 6 closeout, `week6_*.md` with clear naming |

If the work is intentionally considered Week 6 closeout rather than Week 7, keep the files under Week 6 names, but avoid broken links from `docs/INDEX.md`.

---

## 7. First Commands For Week 7

```powershell
# Confirm clean baseline
git status --short --branch

# Default CPU smoke
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_CUDA=OFF
cmake --build build-double --target unit_tests hrsc
.\build-double\unit_tests.exe -r compact

# Strict CUDA smoke, if local CUDA is available
cmake -B build-cuda-double-strict -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_CUDA=ON -DSTRICT_IEEE=ON
cmake --build build-cuda-double-strict --target unit_tests hrsc
.\build-cuda-double-strict\unit_tests.exe "[gpu]" -r compact

# Matrix execution pattern
python scripts/run_matrix.py experiments/week7/<matrix_name>/matrix.json
python scripts/regression/float_regression_report.py --mode device --output experiments/week7/<matrix_name>/summary ...
```

---

## 8. Carry-Forward Checklist

- [ ] Extend strict baseline to fast-math / Ofast rows.
- [ ] Run HLLC-vs-Rusanov comparisons on at least Sod and LW Config 3.
- [ ] Run HLLC `<=` vs `<` branch study, with stationary contact included.
- [ ] Generate Report 1-ready CPU/GPU and float/double tables.
- [ ] Generate convergence evidence for 1D and at least one 2D case.
- [ ] Generate final plots with captions/metadata sufficient for Report 1.
- [ ] Keep all large grid payloads out of git unless explicitly promoted.

