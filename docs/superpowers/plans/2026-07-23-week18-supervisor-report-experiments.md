# Week 18 Supervisor Report and Experiments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate three focused Week 18 robustness evidence packets and matching English/Chinese supervisor-meeting documents in the exact content form used by the Week 14 English meeting report.

**Architecture:** A single Python driver owns planning, execution, measurement, aggregation, and plotting for three independent suites. Each suite writes a stable evidence packet below `experiments/week18/supplemental/`; a combined manifest and bilingual meeting documents consume only passed machine-readable summaries and existing W16/W17 authorities. CSC shell scripts invoke the same Python entry points, so local and Slurm runs use one analysis implementation.

**Tech Stack:** Python 3.11, NumPy, Matplotlib, existing `_mhd_harness` and binary I/O helpers, pytest, Bash, Slurm, CMake/Ninja, CUDA for the hardware suite.

## Global Constraints

- Do not change solver numerics or existing cfg defaults.
- Keep existing output formats stable.
- Every experiment follows `config -> build -> run -> measure -> aggregate -> plot`.
- Generated configs, logs, metadata, `summary.json`, `summary.csv`, `summary.md`, and figures are retained.
- Transient `grid.bin` files are removed after measurement.
- The English and Chinese documents must use the Week 14 section order and contain matching evidence, boundaries, and references.
- Full 256-squared, t=1.0, N=30 Kelvin-Helmholtz MCA remains unclaimed until the existing CSC job completes.

---

### Task 1: Define Week 18 Matrices and Generated Configs

**Files:**
- Create: `scripts/regression/mhd_week18_supplemental.py`
- Create: `tests/py/test_mhd_week18_supplemental.py`

**Interfaces:**
- Consumes: `replace_or_append_cfg(text, key, value)` from `scripts/regression/_mhd_harness.py`.
- Produces: `hardware_plan(repeats)`, `thread_plan(threads)`, `cfl_plan(cfl_values)`, and `generated_cfg(base_text, overrides, output_file, device)`.

- [ ] **Step 1: Write failing matrix and cfg tests**

```python
from scripts.regression import mhd_week18_supplemental as w18


def test_hardware_plan_has_five_repeats_for_each_covered_pair():
    rows = w18.hardware_plan(repeats=5)
    assert len(rows) == 40
    assert {row["case"] for row in rows} == {"brio_wu_1d", "orszag_tang_2d"}
    assert {row["precision"] for row in rows} == {"float", "double"}
    assert {row["device"] for row in rows} == {"cpu", "gpu"}
    assert {row["repeat"] for row in rows} == {1, 2, 3, 4, 5}


def test_thread_plan_covers_two_2d_cases_both_precisions_and_four_threads():
    rows = w18.thread_plan(threads=(1, 2, 4, 8))
    assert len(rows) == 16
    assert {row["omp_num_threads"] for row in rows} == {1, 2, 4, 8}


def test_cfl_plan_covers_hll_hlld_float_double_and_four_values():
    rows = w18.cfl_plan(cfl_values=(0.2, 0.4, 0.6, 0.8))
    assert len(rows) == 16
    assert {row["solver"] for row in rows} == {"hll", "hlld"}


def test_generated_cfg_changes_only_requested_run_keys(tmp_path):
    text = "test = kelvin_helmholtz\ncfl = 0.4\nt_end = 1.0\n"
    result = w18.generated_cfg(
        text,
        {"cfl": 0.6, "riemann": "hlld"},
        tmp_path / "grid.bin",
        "cpu",
    )
    assert "cfl = 0.6\n" in result
    assert "riemann = hlld\n" in result
    assert "test = kelvin_helmholtz\n" in result
    assert f"output_file = {tmp_path / 'grid.bin'}\n" in result
```

- [ ] **Step 2: Run the tests and confirm import failure**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_week18_supplemental.py -q
```

Expected: collection fails because `mhd_week18_supplemental` does not exist.

- [ ] **Step 3: Implement matrix and cfg functions**

```python
CASES_2D = ("orszag_tang_2d", "kelvin_helmholtz_2d")
PRECISIONS = ("double", "float")


def hardware_plan(repeats: int = 5) -> list[dict[str, object]]:
    return [
        {"suite": "hardware_repeats", "case": case, "precision": precision,
         "device": device, "repeat": repeat, "solver": "hll"}
        for case in ("brio_wu_1d", "orszag_tang_2d")
        for precision in PRECISIONS
        for repeat in range(1, repeats + 1)
        for device in ("cpu", "gpu")
    ]


def thread_plan(threads=(1, 2, 4, 8)) -> list[dict[str, object]]:
    return [
        {"suite": "thread_repro", "case": case, "precision": precision,
         "device": "cpu", "solver": "hll", "omp_num_threads": int(thread)}
        for case in CASES_2D for precision in PRECISIONS for thread in threads
    ]


def cfl_plan(cfl_values=(0.2, 0.4, 0.6, 0.8)) -> list[dict[str, object]]:
    return [
        {"suite": "kh_cfl", "case": "kelvin_helmholtz_2d",
         "precision": precision, "device": "cpu", "solver": solver,
         "cfl": float(cfl)}
        for solver in ("hll", "hlld") for precision in PRECISIONS
        for cfl in cfl_values
    ]
```

- [ ] **Step 4: Run the matrix tests**

Run the command from Step 2.

Expected: all four tests pass.

- [ ] **Step 5: Commit Task 1**

```bash
git add scripts/regression/mhd_week18_supplemental.py tests/py/test_mhd_week18_supplemental.py
git commit -m "feat(report2): define Week 18 supplemental matrices"
```

### Task 2: Implement Measurement and Gates

**Files:**
- Modify: `scripts/regression/mhd_week18_supplemental.py`
- Modify: `tests/py/test_mhd_week18_supplemental.py`

**Interfaces:**
- Consumes: arrays and run records generated by Task 3.
- Produces: `aggregate_hardware(rows)`, `aggregate_threads(rows)`, `aggregate_cfl(rows)`, and schema `hrsc.week18-supplemental`, version 1.

- [ ] **Step 1: Add failing aggregation tests**

```python
def test_hardware_gate_requires_repeat_count_and_bit_exact_pairs():
    rows = [
        {"case": "orszag_tang_2d", "precision": "double", "repeat": repeat,
         "device": device, "elapsed_wall_s": 10.0 if device == "cpu" else 2.0,
         "ulp_max": 0, "linf_abs": 0.0, "completed": True}
        for repeat in range(1, 6) for device in ("cpu", "gpu")
    ]
    summary = w18.aggregate_hardware(rows, expected_repeats=5)
    assert summary["gate"]["pass"] is True
    assert summary["groups"][0]["speedup_median"] == 5.0
    assert summary["groups"][0]["cpu_time_iqr_s"] == 0.0


def test_thread_gate_compares_each_row_to_same_precision_one_thread():
    rows = [
        {"case": "kelvin_helmholtz_2d", "precision": "float",
         "omp_num_threads": thread, "completed": True, "ulp_max": 0,
         "linf_abs": 0.0}
        for thread in (1, 2, 4, 8)
    ]
    summary = w18.aggregate_threads(rows)
    assert summary["gate"]["pass"] is True
    assert summary["gate"]["max_ulp"] == 0


def test_cfl_gate_reports_precision_effect_without_temporal_convergence_claim():
    rows = [
        {"solver": solver, "precision": precision, "cfl": cfl,
         "completed": True, "finite_positive": True, "steps": 100,
         "divB_max": 1.0e-3, "Linf_rho_vs_fp64": 0.0 if precision == "double" else 1.0e-6}
        for solver in ("hll", "hlld") for precision in ("double", "float")
        for cfl in (0.2, 0.4, 0.6, 0.8)
    ]
    summary = w18.aggregate_cfl(rows)
    assert summary["gate"]["pass"] is True
    assert summary["claims"]["temporal_convergence"] is False
```

- [ ] **Step 2: Run the new tests and confirm missing functions**

Run the Task 1 pytest command.

Expected: failures name the three absent aggregation functions.

- [ ] **Step 3: Implement deterministic statistics and strict gates**

Implement medians and IQR with NumPy, require every planned row, require
completion and finite states, and compute:

```python
def median_iqr(values):
    arr = np.asarray(values, dtype=np.float64)
    return float(np.median(arr)), float(np.percentile(arr, 75) - np.percentile(arr, 25))
```

Hardware groups are keyed by `(case, precision)` and pair CPU/GPU rows by
repeat. Thread groups are keyed by `(case, precision)` and require
`{1,2,4,8}`. CFL groups are keyed by `(solver, cfl)` and require both
precisions. Every summary includes `gate.pass`, missing-row diagnostics, and
explicit excluded claims.

- [ ] **Step 4: Run the aggregation tests**

Expected: all Task 1 and Task 2 tests pass.

- [ ] **Step 5: Commit Task 2**

```bash
git add scripts/regression/mhd_week18_supplemental.py tests/py/test_mhd_week18_supplemental.py
git commit -m "feat(report2): gate Week 18 robustness evidence"
```

### Task 3: Implement Run, Retention, and Plot Pipelines

**Files:**
- Modify: `scripts/regression/mhd_week18_supplemental.py`
- Modify: `tests/py/test_mhd_week18_supplemental.py`

**Interfaces:**
- Consumes: plans and aggregators from Tasks 1-2; existing binaries
  `build-double/hrsc_mhd`, `build-float/hrsc_mhd`, `build-cuda/hrsc_mhd`, and
  `build-cuda-float/hrsc_mhd`.
- Produces: CLI suites `hardware`, `threads`, `cfl`, `all`, and `aggregate`;
  suite-level `summary.{json,csv,md}` plus figures.

- [ ] **Step 1: Add failing tests for run identity, retention, and CLI**

```python
def test_run_name_contains_every_independent_axis():
    row = {"suite": "hardware_repeats", "case": "orszag_tang_2d",
           "precision": "float", "device": "gpu", "repeat": 3, "solver": "hll"}
    assert w18.run_name(row) == "orszag_tang_2d-float-gpu-hll-r03"


def test_cleanup_refuses_non_grid_paths(tmp_path):
    path = tmp_path / "summary.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="non-grid"):
        w18.cleanup_grids([path])


def test_cli_defaults_to_week18_output():
    args = w18.parse_args(["hardware", "--repeats", "3"])
    assert args.suite == "hardware"
    assert args.repeats == 3
    assert "experiments" in str(args.out)
```

- [ ] **Step 2: Run tests and confirm the new interfaces fail**

Expected: three failures for absent run/cleanup/CLI functions.

- [ ] **Step 3: Implement execution using existing harness contracts**

For each plan row:

1. resolve the source cfg and same-precision binary;
2. write generated cfg text with output under a unique run directory;
3. pass `OMP_NUM_THREADS` only for thread rows;
4. call `run_case`;
5. read the grid with `read_binary`;
6. retain array copies until same-group metrics are computed;
7. delete only recorded files named `grid.bin`.

Write `metadata.json` through the existing harness. Plot:

- hardware median speedup with IQR error bars and a separate zero-ULP panel;
- thread maximum ULP and absolute drift by thread count;
- KH fp32/fp64 density difference and step count by CFL and solver.

- [ ] **Step 4: Run all Week 18 driver tests**

Expected: all tests in `test_mhd_week18_supplemental.py` pass.

- [ ] **Step 5: Commit Task 3**

```bash
git add scripts/regression/mhd_week18_supplemental.py tests/py/test_mhd_week18_supplemental.py
git commit -m "feat(report2): run and plot Week 18 supplemental evidence"
```

### Task 4: Add CSC Slurm Entrypoints

**Files:**
- Create: `scripts/cluster/report2_w16_w17_slurm/run_week18_hardware_repeats.slurm`
- Create: `scripts/cluster/report2_w16_w17_slurm/run_week18_cpu_robustness.slurm`
- Create: `scripts/cluster/report2_w16_w17_slurm/submit_week18.sh`
- Modify: `scripts/cluster/report2_w16_w17_slurm/env.sh`
- Modify: `docs/week17/csc_slurm_w16_w17_execution.md`
- Modify: `tests/py/test_report2_csc_slurm_package.py`

**Interfaces:**
- Consumes: Task 3 CLI and the existing `run_kh_full_mca.slurm`.
- Produces: dependent Slurm submission for hardware repeats, CPU robustness,
  and full KH MCA without Docker.

- [ ] **Step 1: Add failing package tests**

```python
def test_week18_slurm_routes_gpu_and_cpu_suites_without_docker():
    gpu = read("run_week18_hardware_repeats.slurm")
    cpu = read("run_week18_cpu_robustness.slurm")
    assert "--gres=gpu:1" in gpu
    assert "mhd_week18_supplemental.py hardware" in gpu
    assert "mhd_week18_supplemental.py threads" in cpu
    assert "mhd_week18_supplemental.py cfl" in cpu
    assert "docker" not in (gpu + cpu).lower()


def test_week18_submit_includes_existing_full_kh_mca_job():
    submit = read("submit_week18.sh")
    assert "run_kh_full_mca.slurm" in submit
    assert "run_week18_hardware_repeats.slurm" in submit
    assert "run_week18_cpu_robustness.slurm" in submit
```

- [ ] **Step 2: Run CSC package tests and confirm missing scripts**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_report2_csc_slurm_package.py -q
```

Expected: failures name missing Week 18 scripts.

- [ ] **Step 3: Add Slurm scripts and documentation**

The GPU job requests one GPU and invokes:

```bash
"${HRSC_PYTHON}" scripts/regression/mhd_week18_supplemental.py hardware \
  --out experiments/week18/supplemental --repeats "${HRSC_TIMING_REPEATS}"
```

The CPU job invokes `threads` then `cfl`. `submit_week18.sh` submits both and
the existing full MCA array, printing all job IDs. No script uses Docker.

- [ ] **Step 4: Run pytest and Bash syntax checks**

Run:

```bash
bash -n scripts/cluster/report2_w16_w17_slurm/run_week18_hardware_repeats.slurm
bash -n scripts/cluster/report2_w16_w17_slurm/run_week18_cpu_robustness.slurm
bash -n scripts/cluster/report2_w16_w17_slurm/submit_week18.sh
```

Expected: pytest passes and each syntax check exits zero.

- [ ] **Step 5: Commit Task 4**

```bash
git add scripts/cluster/report2_w16_w17_slurm docs/week17/csc_slurm_w16_w17_execution.md tests/py/test_report2_csc_slurm_package.py
git commit -m "feat(cluster): add Week 18 robustness jobs"
```

### Task 5: Execute Available Experiments

**Files:**
- Generate: `experiments/week18/supplemental/hardware_repeats/`
- Generate: `experiments/week18/supplemental/thread_repro/`
- Generate: `experiments/week18/supplemental/kh_cfl/`
- Generate: `experiments/week18/supplemental/summary.json`

**Interfaces:**
- Consumes: Task 3 driver and current local CPU/CUDA binaries.
- Produces: measured evidence when prerequisites are available, otherwise a
  schema-complete blocked packet and ready CSC commands.

- [ ] **Step 1: Verify binary freshness and prerequisites**

Run CUDA and CPU smoke tests, inspect binary timestamps, and verify that the
configured binaries resolve. Rebuild only the needed targets when stale.

- [ ] **Step 2: Run hardware repeats**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_week18_supplemental.py hardware --repeats 5
```

Expected: 40 completed runs, four paired groups, zero missing repeats, and the
same-precision correctness gate passes.

- [ ] **Step 3: Run 2D thread reproducibility**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_week18_supplemental.py threads
```

Expected: 16 completed runs and a complete four-thread comparison for both
cases and precisions.

- [ ] **Step 4: Run KH CFL sensitivity**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_week18_supplemental.py cfl
```

Expected: 16 finite, physically admissible runs with paired fp32/fp64 rows for
each solver and CFL.

- [ ] **Step 5: Aggregate and inspect figures**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_week18_supplemental.py aggregate
```

Expected: combined summary records the state of all suites; inspect every PNG
for readable labels, correct log/linear scales, and non-misleading zero values.

### Task 6: Generate Matching English and Chinese Meeting Documents

**Files:**
- Create: `docs/week18/week18-supervisor-meeting-EN.md`
- Create: `docs/week18/week18-supervisor-meeting-ZH.md`
- Create: `tests/py/test_week18_supervisor_meeting.py`
- Modify: `docs/INDEX.md`

**Interfaces:**
- Consumes: current evidence map, W16/W17 summaries, Task 5 passed summaries,
  and named publication figures.
- Produces: two directly speakable meeting documents with identical evidence
  ordering and claim boundaries.

- [ ] **Step 1: Add failing structural and provenance tests**

```python
def test_bilingual_reports_follow_week14_content_form():
    for path in (ENGLISH, CHINESE):
        text = path.read_text(encoding="utf-8")
        assert "One-line summary" in text or "一句话总结" in text
        assert "What we actually did" in text or "我们实际完成的工作" in text
        assert "how to read" in text.lower() or "如何阅读" in text
        assert "what we won't" in text.lower() or "不能说什么" in text
        assert "References" in text or "参考文献" in text


def test_bilingual_reports_preserve_full_kh_mca_boundary():
    for path in (ENGLISH, CHINESE):
        text = path.read_text(encoding="utf-8")
        assert "256" in text and "N=30" in text
        assert "unclaimed" in text.lower() or "不作结论" in text


def test_reports_reference_only_existing_figures_and_summaries():
    for relative_path in extract_backtick_paths(ENGLISH):
        assert (ROOT / relative_path).exists()
```

- [ ] **Step 2: Run report tests and confirm files are absent**

Expected: tests fail because the Week 18 documents do not exist.

- [ ] **Step 3: Write the English document in Week 14 form**

Use exactly these top-level content sections:

```markdown
## One-line summary
## What we actually did
## The figures: how to read them, what they show
## What we can tell the supervisor (and what we won't)
## Next steps
## References
```

Every numerical statement names its summary source. Supplemental suites that
did not pass are described under `Next steps`, not presented as results.

- [ ] **Step 4: Write a complete Chinese counterpart**

Translate every section, figure explanation, numerical value, boundary, and
reference from the English document. Do not shorten the Chinese version or
introduce evidence absent from the English version.

- [ ] **Step 5: Run report and documentation tests**

Expected: structural, path, boundary, and parity tests pass.

- [ ] **Step 6: Commit Task 6**

```bash
git add docs/week18 docs/INDEX.md tests/py/test_week18_supervisor_meeting.py experiments/week18/supplemental
git commit -m "docs: add bilingual Week 18 supervisor evidence report"
```

### Task 7: Final Verification

**Files:**
- Verify all files created or modified by Tasks 1-6.

**Interfaces:**
- Consumes: complete implementation and experiment outputs.
- Produces: evidence-backed completion status.

- [ ] **Step 1: Run focused tests**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_week18_supplemental.py tests/py/test_report2_csc_slurm_package.py tests/py/test_week18_supervisor_meeting.py -q
```

- [ ] **Step 2: Run the full Python suite**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py -q
```

- [ ] **Step 3: Validate scripts and diffs**

Run Bash syntax checks for every changed shell/Slurm file, run
`git diff --check`, and verify no `grid.bin` is retained below
`experiments/week18/`.

- [ ] **Step 4: Cross-check report numbers**

Programmatically compare all headline values in both meeting documents with
their source summaries, then visually inspect generated figures.

- [ ] **Step 5: Record bounded completion**

Report which supplemental suites passed locally, which remain CSC-dependent,
the test counts, and the exact full-KH-MCA claim boundary.

