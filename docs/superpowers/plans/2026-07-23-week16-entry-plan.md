# Week 16 Remaining Evidence Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enter the remaining Week 16 evidence work from the current Report 2 state without changing solver numerics, cfg defaults, or existing output formats.

**Architecture:** Treat `docs/experiment_logs/report2_evidence_map.md` as the status authority and execute the remaining Week 16 phases in dependency order. Start with repository and environment gates, then run the existing GPU HLL MHD implementation plan, then produce hardware-axis, Kelvin-Helmholtz, and 512^2 consolidation evidence only after their hard gates pass.

**Tech Stack:** C++17, CUDA, CMake/Ninja, Python 3.11, pytest, PowerShell, Git

## Global Constraints

- Do not change solver numerics, existing cfg defaults, or binary output formats.
- Keep all experiment work in `config -> build -> run -> measure -> aggregate -> plot`.
- Use `docs/experiment_logs/report2_evidence_map.md` as the current status authority.
- Preserve the bounded temporal-divergence result as a `negative-result`.
- Keep Week 15 Brio-Wu and Orszag-Tang deterministic-plus-MCA evidence `provisional` until a unified machine-readable gate exists.
- Keep GPU HLL MHD, hardware-axis evidence, KH report-grade evidence, and OT/KH 512^2 consolidation as the remaining Week 16 scope.
- Do not commit build directories, transient `.bin` grids, `tmp7reev1u0/`, or unrelated `tools/` files.
- Use the project test interpreter: `C:\Users\tangy\miniconda3\envs\floatpoint\python.exe`.

---

## File Map

- Read-only authority: `docs/experiment_logs/report2_evidence_map.md`
- Read-only phase scope: `docs/superpowers/specs/2026-07-21-week15-16-completion-design.md`
- Existing GPU implementation plan: `docs/superpowers/plans/2026-07-09-gpu-mhd-hll.md`
- Existing Week 16 navigation: `docs/week16/week16-plan.md`, `docs/week16/week16-summary.md`
- Expected later evidence roots:
  - `experiments/week16/gpu_hll_mhd_validation/`
  - `experiments/week16/cpu_gpu_hardware_axis/`
  - `experiments/week16/kelvin_helmholtz_precision/`
  - `experiments/week16/ot_kh_512_consolidation/`

### Task 1: Entry gate and workspace hygiene

**Files:**
- Verify only: no planned source edits.

**Interfaces:**
- Consumes: current branch, current tracked docs, current evidence summaries.
- Produces: an explicit go/no-go record for starting the remaining Week 16 work.

- [ ] **Step 1: Confirm the branch and untracked assets**

```powershell
git status --short --branch
git branch --show-current
```

Expected: branch is known before execution starts; untracked `tmp7reev1u0/` and `tools/` are recorded as excluded unless the user separately assigns them.

- [ ] **Step 2: Confirm Week 16 authority files exist**

```powershell
Test-Path docs\experiment_logs\report2_evidence_map.md
Test-Path docs\week16\week16-plan.md
Test-Path docs\week16\week16-summary.md
Test-Path experiments\week15\mhd_temporal_divergence\summary.json
Test-Path docs\superpowers\plans\2026-07-09-gpu-mhd-hll.md
```

Expected: five `True` lines.

- [ ] **Step 3: Run the Report 2 documentation contract**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_report2_documentation.py -q
```

Expected: all documentation contract tests pass.

- [ ] **Step 4: Audit temporal evidence gate**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -c "import json,pathlib; p=pathlib.Path('experiments/week15/mhd_temporal_divergence/summary.json'); d=json.loads(p.read_text()); assert d['gates']['pass']; assert d['gates']['report_grade_pass']; assert {r['case']:len(r['times']) for r in d['records']} == {'brio_wu_1d':15,'orszag_tang_2d':25}; print('temporal gate ok')"
```

Expected: `temporal gate ok`.

### Task 2: Execute the GPU HLL MHD prerequisite

**Files:**
- Follow: `docs/superpowers/plans/2026-07-09-gpu-mhd-hll.md`
- Likely create/modify under `src/gpu/`, `src/mhd_main.cpp`, `CMakeLists.txt`, and `tests/unit/`

**Interfaces:**
- Consumes: existing CPU MHD HLL implementation and existing Euler CUDA patterns.
- Produces: CUDA-enabled `device=gpu` HLL MHD path for Brio-Wu 1D and Orszag-Tang 2D, float and double.

- [ ] **Step 1: Validate CUDA availability**

```powershell
nvcc --version
cmake -B build-cuda -G Ninja -DENABLE_CUDA=ON -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release
cmake --build build-cuda --target gpu_smoke
.\build-cuda\gpu_smoke.exe
```

Expected: CUDA 12.8+ or 13.x can target the local GPU and `gpu_smoke` exits 0. If this fails because CUDA is unavailable, stop Week 16 GPU execution and report the environment blocker.

- [ ] **Step 2: Execute Tasks 2-10 of the existing GPU plan**

```powershell
Get-Content docs\superpowers\plans\2026-07-09-gpu-mhd-hll.md
```

Expected: implement one task at a time with its own test cycle and commit. Do not start hardware-axis evidence until Brio-Wu and Orszag-Tang CPU-vs-GPU gates pass for float and double.

- [ ] **Step 3: Final GPU prerequisite verification**

```powershell
.\build-double\unit_tests.exe -r compact
.\build-cuda\unit_tests.exe "[gpu]" -r compact
git diff --check
```

Expected: CPU-only tests pass, CUDA `[gpu]` tests pass, and whitespace check is clean.

### Task 3: Produce the matched CPU/GPU hardware-axis packet

**Files:**
- Create: `experiments/week16/cpu_gpu_hardware_axis/summary.json`
- Create: `experiments/week16/cpu_gpu_hardware_axis/summary.csv`
- Create: `experiments/week16/cpu_gpu_hardware_axis/summary.md`
- Create: `experiments/week16/cpu_gpu_hardware_axis/figures/`
- Modify or create a harness script only if the existing `scripts/run_matrix.py` and metric scripts cannot express the packet.

**Interfaces:**
- Consumes: validated `device=gpu` MHD HLL path from Task 2.
- Produces: same-precision CPU-vs-GPU error, ULP maxima, step counts, final times, `divB` diagnostics, wall times, speedups, metadata, and figures.

- [ ] **Step 1: Define the matrix without editing source cfgs**

Use generated configs under the experiment root for:

```text
brio_wu_1d: cpu/gpu x float/double
orszag_tang_2d: cpu/gpu x float/double
```

Expected: each run writes copied cfg, stdout, stderr, metadata, and a transient grid.

- [ ] **Step 2: Run a reduced smoke first**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts\run_matrix.py experiments\week16\cpu_gpu_hardware_axis\smoke_matrix.json
```

Expected: all smoke runs return 0, metadata include git commit and binary path, and measured grids are deleted after aggregation.

- [ ] **Step 3: Run the full hardware-axis matrix**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts\run_matrix.py experiments\week16\cpu_gpu_hardware_axis\matrix.json
```

Expected: all runs return 0; same-precision CPU/GPU agreement passes either `ulp_max=0` or a documented tight tolerance from the GPU implementation phase.

- [ ] **Step 4: Aggregate, plot, and audit**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts\aggregate_metrics.py --output experiments\week16\cpu_gpu_hardware_axis\summary.json experiments\week16\cpu_gpu_hardware_axis\runs\*\metadata.json
git diff --check
```

Expected: `summary.{json,csv,md}` and figures exist; no `.bin` files are staged.

### Task 4: Gate Kelvin-Helmholtz before precision runs

**Files:**
- Create: `experiments/week16/kelvin_helmholtz_precision/validation/summary.json`
- Create: `experiments/week16/kelvin_helmholtz_precision/validation/summary.md`

**Interfaces:**
- Consumes: existing KH morphology summary and `mhd_kh_2d.py` configuration.
- Produces: a pass/fail decision for downstream KH deterministic and MCA packets.

- [ ] **Step 1: Run the reduced KH validation smoke**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts\regression\mhd_kh_2d.py --smoke --out experiments\week16\kelvin_helmholtz_precision\validation_smoke
```

Expected: finite states, mass conservation, bounded `divB`, and reference-comparison schema are produced. If the script exposes different current CLI flags, record the exact help output and adjust the command without changing cfg defaults.

- [ ] **Step 2: Run the KH 256^2-versus-512^2 gate**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts\regression\mhd_kh_2d.py --out experiments\week16\kelvin_helmholtz_precision\validation
```

Expected: validation gates pass before any KH 24-variant or MCA evidence starts. If a hard gate fails, document the bounded negative or diagnostic result and stop downstream KH precision work.

### Task 5: Run KH precision evidence only after Task 4 passes

**Files:**
- Create: `experiments/week16/kelvin_helmholtz_precision/hll/summary.{json,csv,md}`
- Create: `experiments/week16/kelvin_helmholtz_precision/hlld/summary.{json,csv,md}`
- Create: `experiments/week16/kelvin_helmholtz_precision/**/figures/`

**Interfaces:**
- Consumes: passed KH validation gate.
- Produces: HLL and HLLD CPU deterministic 24-variant packets plus p53 and p24 MCA N=30 packets where the solver anchor gate passes.

- [ ] **Step 1: Run deterministic HLL and HLLD smokes**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts\regression\mhd_precision_pilot.py --case kelvin_helmholtz_2d --solver hll --smoke --out experiments\week16\kelvin_helmholtz_precision\hll_smoke
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts\regression\mhd_precision_pilot.py --case kelvin_helmholtz_2d --solver hlld --smoke --out experiments\week16\kelvin_helmholtz_precision\hlld_smoke
```

Expected: smoke gates pass or the failing solver is retained only as diagnostic evidence.

- [ ] **Step 2: Run report-depth deterministic and MCA packets**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts\regression\mhd_precision_pilot.py --case kelvin_helmholtz_2d --solver hll --mca-samples 30 --out experiments\week16\kelvin_helmholtz_precision\hll
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts\regression\mhd_precision_pilot.py --case kelvin_helmholtz_2d --solver hlld --mca-samples 30 --out experiments\week16\kelvin_helmholtz_precision\hlld
```

Expected: each accepted solver has 24 deterministic variants and N=30 p53/p24 MCA summaries with configs, logs, and metadata retained according to harness policy.

### Task 6: Consolidate OT/KH 512^2 conclusions and update current status

**Files:**
- Create: `experiments/week16/ot_kh_512_consolidation/summary.json`
- Create: `experiments/week16/ot_kh_512_consolidation/summary.md`
- Modify: `docs/experiment_logs/report2_evidence_map.md`
- Modify: `docs/week16/week16-summary.md`
- Modify: `docs/INDEX.md`

**Interfaces:**
- Consumes: existing Orszag-Tang 512^2 material and the KH 512^2 validation result.
- Produces: a bounded two-resolution sensitivity statement without claiming asymptotic convergence.

- [ ] **Step 1: Aggregate OT and KH reference facts**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts\aggregate_metrics.py --output experiments\week16\ot_kh_512_consolidation\summary.json experiments\week15\orszag_tang_precision_smoke\headline256_p1\summary.json experiments\week16\kelvin_helmholtz_precision\validation\summary.json
```

Expected: the summary distinguishes OT and KH, records which 512^2 assets are available, and states that two resolutions do not establish asymptotic convergence.

- [ ] **Step 2: Update the evidence map and Week 16 summary**

Update only current-routing documents. Historical meeting reports and old experiment summaries are not rewritten.

- [ ] **Step 3: Final verification**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py -q
git diff --check
git status --short
```

Expected: Python tests pass, whitespace check is clean, and status shows only intentional tracked changes plus explicitly excluded untracked assets.

## Self-Review

- Spec coverage: the plan covers the remaining Week 16 phases from `2026-07-21-week15-16-completion-design.md`: GPU HLL MHD, hardware-axis packet, KH report-grade evidence, and OT/KH 512^2 consolidation. Temporal divergence is treated as already complete and bounded.
- Placeholder scan: no unresolved placeholder wording remains.
- Interface consistency: later tasks consume only artifacts produced by earlier tasks or existing documented plans.
