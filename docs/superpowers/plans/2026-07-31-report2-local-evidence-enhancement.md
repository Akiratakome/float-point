# Report 2 Local Evidence Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a result-neutral, warm-up-controlled Brio--Wu/Orszag--Tang CPU/GPU workload ladder and integrate its reproducibility implications into Report 2 without changing solver numerics, defaults, or output formats.

**Architecture:** A new dedicated Python workflow owns matrix construction, paired execution, resumable scalar records, aggregation, gates, and diagnostic plots while reusing the existing MHD runner, binary reader, physical-state metrics, and ULP implementation. The stored Week-18 packet remains immutable; the new Week-20 summary becomes the audited source for the existing Chapter 5 hardware figure only if its technical and correctness gates pass. Manuscript changes are downstream of the evidence gate.

**Tech Stack:** Python 3.11, NumPy, Matplotlib/Agg, pytest, CMake/Ninja, MSVC 19.51, CUDA 13.3, PowerShell, LaTeX/MiKTeX.

## Global Constraints

- Read `docs/INDEX.md`, `docs/HARNESS.md`, `report2/WRITING_AGENT.md`, the accepted design at `docs/superpowers/specs/2026-07-31-report2-local-evidence-enhancement-design.md`, and `docs/experiment_logs/report2_evidence_map.md` before implementation.
- Do not change solver numerics, existing cfg defaults, binary output layout, or historical experiment summaries.
- Preserve `config -> build -> run -> measure -> aggregate -> plot` and retain generated configs, stdout/stderr, metadata, hashes, scalar records, summaries, and figure provenance.
- Use HLL only; Brio--Wu uses `N=800`, `t_end=0.1`, CFL 0.4; Orszag--Tang uses `N=128,256,512`, `t_end=0.5`, CFL 0.4.
- Use fp64/fp32 and CPU/GPU, one excluded warm-up plus exactly five measured repetitions per device group: 16 warm-ups and 80 measured runs.
- Set and record `OMP_NUM_THREADS=1`; alternate CPU/GPU execution order between odd and even paired repetitions.
- The timer is end-to-end subprocess wall time through required binary output, not kernel time.
- The gate must not require GPU speed-up, a crossover, monotonicity, or a precision ordering.
- Stop after completing the active CPU/GPU pair when cumulative recorded solver time reaches 7,200 seconds.
- Do not substitute another resolution or final time after observing a failure.
- Remove only explicitly resolved `grid.bin` files inside `experiments/week20/hardware_workload_ladder/runs/`; retain reference grids until their repeat group and pair metrics are complete.
- Do not run the full matrix until all in-scope source files are represented by a clean Git commit. If `git status` reports pre-existing changes under `CMakeLists.txt`, `cmake/`, `src/mhd/`, `src/gpu/`, `src/mhd_main.cpp`, or shared harness files, stop and ask the user how to freeze them; never stage unrelated work silently.
- Use new ignored build directories: `build-report2-hw-cpu-double`, `build-report2-hw-cpu-float`, `build-report2-hw-cuda-double`, and `build-report2-hw-cuda-float`.
- Run all Python commands with `C:\Users\tangy\miniconda3\envs\floatpoint\python.exe`.
- Manuscript prose must not contain week numbers, packet labels, build-directory names, or arbitrary cross-axis rankings.

---

## File Structure

| Path | Action | Responsibility |
|---|---|---|
| `scripts/regression/mhd_hardware_workload_ladder.py` | Create | Matrix, schedule, config generation, execution, resume identity, scalar records, aggregation, gates, Markdown/CSV/JSON, and diagnostic PNG/PDF. |
| `tests/py/test_mhd_hardware_workload_ladder.py` | Create | Unit and fake-run integration coverage for every workflow contract. |
| `experiments/week20/hardware_workload_ladder/` | Generate | Configs, logs, metadata, scalar records, summaries, figures, environment record, and lifecycle manifest; no final grids. |
| `tests/py/test_experiment_manifests.py` | Modify | Promote and validate the new lifecycle manifest after evidence generation. |
| `scripts/figures/report2_publication_figures.py` | Modify | Audit the new summary and regenerate the existing `hardware_reproducibility` figure ID from it. |
| `tests/py/test_report2_publication_figures.py` | Modify | Require the new source, gate, three OT resolutions, and audited PNG/PDF hashes. |
| `experiments/week18/report2_publication_figures/` | Regenerate | Audited publication figure and manifest with stable figure ID and new source hash. |
| `report2/phd-thesis-template-2.4/Figs/report2/ch5_hardware_reproducibility.pdf` | Replace after gate | LaTeX asset copied from the audited vector PDF. |
| `tests/py/test_report2_local_evidence_manuscript.py` | Create | Chapter 3/5/6 and Appendix integration, scope language, and approximate C3 budget. |
| `report2/phd-thesis-template-2.4/Chapter3/chapter3.tex` | Modify after gate | Experimental units, uniform new timing protocol, analysis freeze, and compact workload coverage. |
| `report2/phd-thesis-template-2.4/Chapter5/chapter5.tex` | Modify after gate | Replace the hardware paragraph/caption with result-neutral workload-ladder evidence. |
| `report2/phd-thesis-template-2.4/Chapter6/chapter6.tex` | Modify after gate | Add construct, internal, and external validity synthesis. |
| `report2/phd-thesis-template-2.4/Appendix1/appendix1.tex` | Modify after gate | Add environment and evidence traceability for Figure 5.3. |
| `docs/experiment_logs/report2_evidence_map.md` | Modify | Record status, scope, claim, exclusion, provenance, and retention. |
| `docs/INDEX.md`, `scripts/README.md` | Modify | Route the new canonical workflow and evidence packet. |
| `report2/planning/chapter3_writing_plan.md`, `report2/planning/chapter5_writing_plan.md`, `report2/planning/drafting_status.md` | Modify after gate | Record completed or failed status without promoting unsupported evidence. |

## Execution Prerequisite: Source-Freeze Gate

- [ ] **Step 1: Inspect the in-scope source state**

Run:

```powershell
git status --short -- CMakeLists.txt cmake src/mhd src/gpu src/mhd_main.cpp scripts/harness scripts/regression/_mhd_harness.py scripts/io_helper.py
git diff --name-only -- CMakeLists.txt cmake src/mhd src/gpu src/mhd_main.cpp scripts/harness scripts/regression/_mhd_harness.py scripts/io_helper.py
```

Expected: no output before full builds. If either command lists a pre-existing file, stop and ask the user whether to make a scoped source-freeze commit. Do not include that file in a feature commit without approval.

- [ ] **Step 2: Confirm the experiment will use one immutable commit**

Run:

```powershell
git rev-parse HEAD
git status --short -- CMakeLists.txt cmake src/mhd src/gpu src/mhd_main.cpp scripts/harness scripts/regression/_mhd_harness.py scripts/regression/mhd_hardware_workload_ladder.py scripts/io_helper.py
```

Expected: record the 40-character commit in the future `environment.json`; the
listed experiment-affecting source is clean. Record the complete repository
status separately for provenance, but do not block on unrelated user changes.
Generated experiment outputs may become untracked only after the run starts.

---

### Task 1: Define the Result-Neutral Matrix and Execution Schedule

**Files:**
- Create: `scripts/regression/mhd_hardware_workload_ladder.py`
- Create: `tests/py/test_mhd_hardware_workload_ladder.py`

**Interfaces:**
- Produces: `comparison_cells() -> list[dict[str, Any]]`, `run_schedule(repeats: int = 5) -> list[dict[str, Any]]`, and `run_name(row: dict[str, Any]) -> str`.
- Every scheduled row contains `case`, `resolution`, `dimension`, `precision`, `device`, `role`, `repeat`, `pair_id`, `execution_order`, `solver`, `cfl`, `t_end`, and `omp_num_threads`.

- [ ] **Step 1: Write failing matrix and ordering tests**

Add:

```python
from scripts.regression import mhd_hardware_workload_ladder as ladder


def test_matrix_has_eight_comparison_cells_and_sixteen_device_groups():
    cells = ladder.comparison_cells()
    assert len(cells) == 8
    assert {(row["case"], row["resolution"]) for row in cells} == {
        ("brio_wu_1d", 800),
        ("orszag_tang_2d", 128),
        ("orszag_tang_2d", 256),
        ("orszag_tang_2d", 512),
    }
    assert {row["precision"] for row in cells} == {"double", "float"}


def test_schedule_has_sixteen_warmups_and_eighty_measured_runs():
    rows = ladder.run_schedule(repeats=5)
    warmups = [row for row in rows if row["role"] == "warmup"]
    measured = [row for row in rows if row["role"] == "measured"]
    assert len(warmups) == 16
    assert len(measured) == 80
    assert {row["repeat"] for row in warmups} == {0}
    assert {row["repeat"] for row in measured} == {1, 2, 3, 4, 5}


def test_device_order_alternates_inside_each_measured_pair():
    rows = [
        row for row in ladder.run_schedule(repeats=2)
        if row["role"] == "measured"
        and row["case"] == "orszag_tang_2d"
        and row["resolution"] == 128
        and row["precision"] == "double"
    ]
    by_repeat = {
        repeat: [row["device"] for row in rows if row["repeat"] == repeat]
        for repeat in (1, 2)
    }
    assert by_repeat == {1: ["cpu", "gpu"], 2: ["gpu", "cpu"]}
    assert len({row["pair_id"] for row in rows}) == 2
```

- [ ] **Step 2: Run tests and verify collection fails**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_mhd_hardware_workload_ladder.py -q
```

Expected: FAIL during import because `mhd_hardware_workload_ladder.py` does not exist.

- [ ] **Step 3: Add the minimal matrix implementation**

Create the script with these constants and functions:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "experiments" / "week20" / "hardware_workload_ladder"
EXPERIMENT = "report2-hardware-workload-ladder"
PRECISIONS = ("double", "float")
DEVICES = ("cpu", "gpu")
SCOPES = (
    {"case": "brio_wu_1d", "resolution": 800, "dimension": 1,
     "cfl": 0.4, "t_end": 0.1},
    {"case": "orszag_tang_2d", "resolution": 128, "dimension": 2,
     "cfl": 0.4, "t_end": 0.5},
    {"case": "orszag_tang_2d", "resolution": 256, "dimension": 2,
     "cfl": 0.4, "t_end": 0.5},
    {"case": "orszag_tang_2d", "resolution": 512, "dimension": 2,
     "cfl": 0.4, "t_end": 0.5},
)


def comparison_cells() -> list[dict[str, Any]]:
    return [
        dict(scope, precision=precision, solver="hll", omp_num_threads=1)
        for scope in SCOPES
        for precision in PRECISIONS
    ]


def run_schedule(repeats: int = 5) -> list[dict[str, Any]]:
    if repeats < 1:
        raise ValueError("repeats must be positive")
    rows: list[dict[str, Any]] = []
    for cell in comparison_cells():
        for order, device in enumerate(DEVICES, start=1):
            rows.append(dict(cell, device=device, role="warmup", repeat=0,
                             pair_id=None, execution_order=order))
        for repeat in range(1, repeats + 1):
            devices = DEVICES if repeat % 2 else tuple(reversed(DEVICES))
            pair_id = (
                f"{cell['case']}-n{cell['resolution']}-{cell['precision']}-r{repeat:02d}"
            )
            for order, device in enumerate(devices, start=1):
                rows.append(dict(cell, device=device, role="measured", repeat=repeat,
                                 pair_id=pair_id, execution_order=order))
    return rows


def run_name(row: dict[str, Any]) -> str:
    suffix = "warmup" if row["role"] == "warmup" else f"r{int(row['repeat']):02d}"
    return (
        f"{row['case']}-n{int(row['resolution'])}-{row['precision']}-"
        f"{row['device']}-{suffix}"
    )
```

- [ ] **Step 4: Run the targeted tests**

Run the command from Step 2.

Expected: 3 passed.

- [ ] **Step 5: Commit the matrix contract**

```powershell
git add -- scripts/regression/mhd_hardware_workload_ladder.py tests/py/test_mhd_hardware_workload_ladder.py
git commit -m "test(report2): define hardware workload ladder matrix"
```

---

### Task 2: Add Config Generation, Provenance Identity, and Safe Retention

**Files:**
- Modify: `scripts/regression/mhd_hardware_workload_ladder.py`
- Modify: `tests/py/test_mhd_hardware_workload_ladder.py`

**Interfaces:**
- Consumes: scheduled row dictionaries from Task 1.
- Produces: `generated_cfg(base_text: str, row: dict[str, Any], output: Path) -> str`,
  `identity_payload(row: dict[str, Any], source_commit: str,
  binary_sha256: str, config_sha256: str) -> dict[str, Any]`,
  `identity_sha256(payload: dict[str, Any]) -> str`,
  `load_resumable_record(path: Path, identity: dict[str, Any]) ->
  dict[str, Any] | None`, and `cleanup_grid(path: Path, run_root: Path) -> None`.

- [ ] **Step 1: Write failing config, identity, and cleanup tests**

Add tests that assert:

```python
import json
from pathlib import Path

import pytest


def test_generated_ot_cfg_sets_only_declared_runtime_keys(tmp_path):
    base = "test = orszag_tang\nnx = 256\nny = 256\ncfl = 0.4\nt_end = 0.5\n"
    row = next(
        item for item in ladder.run_schedule(1)
        if item["case"] == "orszag_tang_2d"
        and item["resolution"] == 512
        and item["precision"] == "double"
        and item["device"] == "gpu"
        and item["role"] == "measured"
    )
    text = ladder.generated_cfg(base, row, tmp_path / "grid.bin")
    assert "nx = 512\n" in text and "ny = 512\n" in text
    assert "cfl = 0.4\n" in text and "t_end = 0.5\n" in text
    assert "riemann = hll\n" in text and "device = gpu\n" in text
    assert f"output_file = {tmp_path / 'grid.bin'}\n" in text


def test_resume_requires_exact_identity_and_completed_scalar_record(tmp_path):
    identity = {"source_commit": "a" * 40, "binary_sha256": "b" * 64,
                "config_sha256": "c" * 64, "run_id": "cell-r01"}
    path = tmp_path / "record.json"
    path.write_text(json.dumps({"identity_sha256": ladder.identity_sha256(identity),
                                "status": "completed", "role": "measured"}),
                    encoding="utf-8")
    assert ladder.load_resumable_record(path, identity)["status"] == "completed"
    changed = dict(identity, binary_sha256="d" * 64)
    assert ladder.load_resumable_record(path, changed) is None


def test_cleanup_removes_only_named_grid_inside_run_root(tmp_path):
    runs = tmp_path / "runs"
    grid = runs / "cell" / "grid.bin"
    grid.parent.mkdir(parents=True)
    grid.write_bytes(b"grid")
    ladder.cleanup_grid(grid, runs)
    assert not grid.exists()
    outside = tmp_path / "grid.bin"
    outside.write_bytes(b"outside")
    with pytest.raises(ValueError, match="run root"):
        ladder.cleanup_grid(outside, runs)
```

- [ ] **Step 2: Run these tests and verify failure**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_mhd_hardware_workload_ladder.py -q
```

Expected: FAIL because the new functions are undefined.

- [ ] **Step 3: Implement exact config and identity helpers**

Import `hashlib`, `json`, and `replace_or_append_cfg`. Define case configs and build paths:

```python
CASE_CONFIGS = {
    "brio_wu_1d": ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg",
    "orszag_tang_2d": ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg",
}
BINS = {
    ("double", "cpu"): ROOT / "build-report2-hw-cpu-double" / "hrsc_mhd",
    ("float", "cpu"): ROOT / "build-report2-hw-cpu-float" / "hrsc_mhd",
    ("double", "gpu"): ROOT / "build-report2-hw-cuda-double" / "hrsc_mhd",
    ("float", "gpu"): ROOT / "build-report2-hw-cuda-float" / "hrsc_mhd",
}


def generated_cfg(base_text: str, row: dict[str, Any], output: Path) -> str:
    values: list[tuple[str, object]] = [
        ("nx", int(row["resolution"])),
        ("cfl", float(row["cfl"])),
        ("t_end", float(row["t_end"])),
        ("riemann", "hll"),
        ("device", row["device"]),
        ("output_format", "binary"),
        ("output_file", output),
    ]
    if int(row["dimension"]) == 2:
        values.insert(1, ("ny", int(row["resolution"])))
    text = base_text
    for key, value in values:
        text = replace_or_append_cfg(text, key, str(value))
    return text


def identity_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def identity_payload(row: dict[str, Any], source_commit: str,
                     binary_sha256: str, config_sha256: str) -> dict[str, Any]:
    return {
        "source_commit": source_commit,
        "binary_sha256": binary_sha256,
        "config_sha256": config_sha256,
        "run_id": run_name(row),
        "case": row["case"],
        "resolution": int(row["resolution"]),
        "precision": row["precision"],
        "device": row["device"],
        "role": row["role"],
        "repeat": int(row["repeat"]),
        "pair_id": row["pair_id"],
    }


def load_resumable_record(path: Path, identity: dict[str, Any]) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("status") != "completed":
        return None
    if record.get("identity_sha256") != identity_sha256(identity):
        return None
    return record


def cleanup_grid(path: Path, run_root: Path) -> None:
    resolved = path.resolve()
    root = run_root.resolve()
    if resolved.name != "grid.bin" or root not in resolved.parents:
        raise ValueError(f"grid cleanup target is outside run root: {resolved}")
    if resolved.exists():
        resolved.unlink()
```

- [ ] **Step 4: Run tests and verify pass**

Expected: all Task 1--2 tests pass.

- [ ] **Step 5: Commit provenance helpers**

```powershell
git add -- scripts/regression/mhd_hardware_workload_ladder.py tests/py/test_mhd_hardware_workload_ladder.py
git commit -m "feat(report2): add workload ladder provenance contract"
```

---

### Task 3: Aggregate Paired Timings and Separate Technical/Correctness Gates

**Files:**
- Modify: `scripts/regression/mhd_hardware_workload_ladder.py`
- Modify: `tests/py/test_mhd_hardware_workload_ladder.py`

**Interfaces:**
- Consumes: scalar warm-up and measured records containing the schedule keys
  plus `elapsed_wall_s`, `completed`, `completion_attested`, `final_time`,
  `finite_positive`, `required_output`, `metadata_complete`, `precision_bytes`,
  `steps`, `pair_ulp_max`, `pair_linf_abs`, and `repeat_ulp_max`.
- Produces: `median_iqr(values)`, `aggregate_records(records, expected_repeats=5) -> dict[str, Any]` with `device_groups`, `comparison_cells`, `gate.technical_pass`, `gate.correctness_pass`, and `gate.report_grade_pass`.

- [ ] **Step 1: Write failing result-neutral aggregation tests**

Create this `_complete_records()` test helper. It returns all 16 warm-ups and 80
measured rows. CPU time is 4.0 and GPU time is 2.0, except OT/128 where CPU time
is 1.0 and GPU time is 2.0. Every row is complete, finite-positive, correctly
tagged, step-matched, and zero ULP.

```python
def _complete_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for row in ladder.run_schedule(repeats=5):
        is_small_ot = (
            row["case"] == "orszag_tang_2d" and row["resolution"] == 128
        )
        elapsed = 2.0 if row["device"] == "gpu" else (1.0 if is_small_ot else 4.0)
        records.append({
            **row,
            "elapsed_wall_s": elapsed,
            "completed": True,
            "completion_attested": True,
            "final_time": float(row["t_end"]),
            "finite_positive": True,
            "required_output": True,
            "metadata_complete": True,
            "precision_bytes": 8 if row["precision"] == "double" else 4,
            "steps": int(row["resolution"]) * 2,
            "pair_ulp_max": 0,
            "pair_linf_abs": 0.0,
            "repeat_ulp_max": 0,
        })
    return records
```

Assert:

```python
def test_complete_aggregate_has_eight_cells_and_passes_both_gates():
    summary = ladder.aggregate_records(_complete_records(), expected_repeats=5)
    assert len(summary["comparison_cells"]) == 8
    assert len(summary["device_groups"]) == 16
    assert summary["gate"] == {
        "technical_pass": True,
        "correctness_pass": True,
        "report_grade_pass": True,
        "missing_records": [],
    }


def test_gate_is_result_neutral_about_speedup_and_monotonicity():
    summary = ladder.aggregate_records(_complete_records(), expected_repeats=5)
    ratios = [row["speedup_median"] for row in summary["comparison_cells"]]
    assert min(ratios) < 1.0 and max(ratios) > 1.0
    assert summary["gate"]["report_grade_pass"] is True
    assert summary["claims"]["requires_speedup"] is False
    assert summary["claims"]["requires_monotonicity"] is False


def test_correctness_failure_does_not_hide_complete_timing_records():
    records = _complete_records()
    records[0]["pair_ulp_max"] = 1
    summary = ladder.aggregate_records(records, expected_repeats=5)
    assert summary["gate"]["technical_pass"] is True
    assert summary["gate"]["correctness_pass"] is False
    assert summary["gate"]["report_grade_pass"] is False
    assert len(summary["comparison_cells"]) == 8


def test_missing_repeat_fails_only_the_technical_gate():
    summary = ladder.aggregate_records(_complete_records()[:-1], expected_repeats=5)
    assert summary["gate"]["technical_pass"] is False
    assert summary["gate"]["report_grade_pass"] is False
    assert summary["gate"]["missing_records"]
```

- [ ] **Step 2: Run tests and verify failure**

Expected: FAIL because `aggregate_records` is undefined.

- [ ] **Step 3: Implement aggregation with fixed keys**

Group measured rows by `(case, resolution, precision)` and then by device and repeat. For each of the eight comparison cells, require five CPU and five GPU rows, compute paired ratios `cpu.elapsed_wall_s / gpu.elapsed_wall_s`, and emit:

```python
{
    "case": "orszag_tang_2d",
    "resolution": 512,
    "precision": "double",
    "repeats": 5,
    "cpu_time_median_s": 0.0,
    "cpu_time_iqr_s": 0.0,
    "gpu_time_median_s": 0.0,
    "gpu_time_iqr_s": 0.0,
    "speedup_median": 0.0,
    "speedup_iqr": 0.0,
    "max_pair_ulp": 0,
    "max_pair_linf_abs": 0.0,
    "max_repeat_ulp": 0,
    "steps_match": True,
    "status": "complete",
}
```

Replace the zero-valued statistic fields with values computed from the selected
rows. `technical_pass` requires all 16 warm-ups plus the expected measured
records, exactly `expected_repeats` measured rows per device group, completion
attestation at each declared final time, finite-positive measured states,
required output and metadata, correct precision tags, matching paired steps,
and finite positive wall times. `correctness_pass` requires technical pass plus
zero pair ULP, zero pair absolute difference, and zero repeat ULP.
`report_grade_pass` is their conjunction. Add:

```python
"claims": {
    "requires_speedup": False,
    "requires_crossover": False,
    "requires_monotonicity": False,
    "requires_precision_ordering": False,
    "timer_scope": "subprocess wall time including startup and required binary output",
    "portable_performance": False,
}
```

Also emit the fixed protocol declaration used by downstream audits:

```python
"matrix": {
    "comparison_cells": 8,
    "device_groups": 16,
    "warmups": 16,
    "measured_runs": 16 * expected_repeats,
    "measured_repeats_per_device_group": expected_repeats,
}
```

- [ ] **Step 4: Run targeted tests**

Expected: all aggregation tests pass.

- [ ] **Step 5: Commit the aggregation gate**

```powershell
git add -- scripts/regression/mhd_hardware_workload_ladder.py tests/py/test_mhd_hardware_workload_ladder.py
git commit -m "feat(report2): gate workload ladder timing evidence"
```

---

### Task 4: Implement Paired Execution, Scalar Records, Resume, and Stop Budget

**Files:**
- Modify: `scripts/regression/mhd_hardware_workload_ladder.py`
- Modify: `tests/py/test_mhd_hardware_workload_ladder.py`

**Interfaces:**
- Consumes: Task 1 schedule and Task 2 config/identity helpers.
- Produces: `execute_schedule(rows: list[dict[str, Any]], out: Path, *,
  run_one: Callable[[dict[str, Any], Path], dict[str, Any]],
  max_solver_seconds: float) -> list[dict[str, Any]]`, per-run `record.json`,
  per-pair `pair.json`, and CLI subcommands `smoke`, `run`, and `aggregate`.

- [ ] **Step 1: Write failing fake-run integration tests**

Use `monkeypatch` to replace the real runner with a fake that writes a valid small MHD binary fixture or returns staged NumPy arrays. Assert:

```python
from collections import Counter
import json
from pathlib import Path

import numpy as np


class FakeRunner:
    def __init__(self, cpu_seconds: float, gpu_seconds: float) -> None:
        self.cpu_seconds = cpu_seconds
        self.gpu_seconds = gpu_seconds
        self.calls: list[str] = []

    def __call__(self, row: dict[str, object], out: Path) -> dict[str, object]:
        name = ladder.run_name(row)
        self.calls.append(name)
        run_dir = out / "runs" / name
        run_dir.mkdir(parents=True, exist_ok=True)
        grid = run_dir / "grid.bin"
        grid.write_bytes(b"staged fake grid")
        elapsed = self.cpu_seconds if row["device"] == "cpu" else self.gpu_seconds
        dtype = np.float64 if row["precision"] == "double" else np.float32
        array = np.ones((1, 2, 9), dtype=dtype)
        record = {
            **row,
            "run_dir": str(run_dir),
            "grid": str(grid),
            "elapsed_wall_s": elapsed,
            "completed": True,
            "completion_attested": True,
            "final_time": float(row["t_end"]),
            "finite_positive": True,
            "required_output": True,
            "metadata_complete": True,
            "precision_bytes": 8 if row["precision"] == "double" else 4,
            "steps": int(row["resolution"]) * 2,
            "status": "staged",
            "identity_sha256": f"fake-{name}",
        }
        return {"record": record, "array": array, "grid": grid,
                "run_dir": run_dir}


def test_fake_execution_writes_records_and_excludes_warmups_from_summary(tmp_path, monkeypatch):
    fake = FakeRunner(cpu_seconds=2.0, gpu_seconds=1.0)
    records = ladder.execute_schedule(
        ladder.run_schedule(repeats=1), tmp_path, run_one=fake,
        max_solver_seconds=7200.0,
    )
    assert len([row for row in records if row["role"] == "warmup"]) == 16
    assert len([row for row in records if row["role"] == "measured"]) == 16
    assert all((Path(row["run_dir"]) / "record.json").is_file() for row in records)
    summary = ladder.aggregate_records(records, expected_repeats=1)
    assert all(row["repeats"] == 1 for row in summary["comparison_cells"])


def test_execution_stops_after_active_pair_when_budget_is_reached(tmp_path):
    fake = FakeRunner(cpu_seconds=4.0, gpu_seconds=4.0)
    schedule = [
        row for row in ladder.run_schedule(repeats=2)
        if row["case"] == "brio_wu_1d"
        and row["precision"] == "double"
    ]
    records = ladder.execute_schedule(
        schedule, tmp_path, run_one=fake, max_solver_seconds=9.0,
    )
    measured = [row for row in records if row["role"] == "measured"]
    pair_counts = Counter(row["pair_id"] for row in measured)
    assert measured
    assert set(pair_counts.values()) == {2}
    assert sum(row["elapsed_wall_s"] for row in records) >= 9.0


def test_resume_reuses_only_finalised_pairs(tmp_path):
    first = FakeRunner(cpu_seconds=2.0, gpu_seconds=1.0)
    schedule = ladder.run_schedule(repeats=1)
    ladder.execute_schedule(schedule, tmp_path, run_one=first, max_solver_seconds=7200.0)
    second = FakeRunner(cpu_seconds=9.0, gpu_seconds=9.0)
    resumed = ladder.execute_schedule(schedule, tmp_path, run_one=second,
                                      max_solver_seconds=7200.0)
    assert second.calls == []
    assert len(resumed) == 32
```

- [ ] **Step 2: Run tests and verify failure**

Expected: FAIL because execution and fake-run injection interfaces are missing.

- [ ] **Step 3: Implement real run staging**

Reuse:

```python
from typing import Callable

from scripts.io_helper import read_binary
from scripts.regression._mhd_harness import (
    git_commit, replace_or_append_cfg, resolve_binary, run_case, sha256_file,
)
from scripts.regression.mhd_gpu_hardware_axis import max_ulp_distance
from scripts.regression.mhd_week18_supplemental import (
    difference_metrics, environment_override, physical_state,
)
```

`run_one(row, out)` must:

1. resolve the case config and precision/device binary;
2. generate `config.cfg` under a deterministic run directory;
3. set `OMP_NUM_THREADS=1` through `environment_override`;
4. call the harness with every required positional argument:

   ```python
   run_case(
       label=run_name(row),
       cfg_text=cfg_text,
       run_dir=run_dir,
       bin_path=bin_path,
       source_cfg=source_cfg,
       commit=commit,
       binary_sha256=binary_sha256,
       output_bin=grid,
       experiment=EXPERIMENT,
   )
   ```

5. validate header shape and precision tag;
6. compute physical-state fields and scalar diagnostics;
7. write `record.json` with the exact identity hash, completion, timing,
   diagnostics, environment, binary/config hashes, and output SHA-256; and
8. return a staged dictionary containing `record`, `array`, `grid`, and
   `run_dir`.

Warm-up arrays are not aggregated and their grids are removed immediately after
their scalar record is written. For measured pairs, keep both device arrays
until `difference_metrics` and `max_ulp_distance` have populated
`pair_ulp_max` and `pair_linf_abs` in both scalar records. Keep each device's
repeat-1 grid as its within-group reference until repeat 5 is finalised; then
delete all grids in that group. If execution stops or raises, retain the active
pair/reference grids and record the failure.

`execute_schedule` processes warm-ups first and measured rows by complete
`pair_id`. It checks the budget only between pairs. Resume accepts a pair only
when both `record.json` files and `pair.json` match current identity hashes and
contain final pair metrics. A CUDA out-of-memory error, non-finite state,
missing completion, step mismatch, or saved-state drift marks that cell failed,
skips its dependent repetitions, preserves the bounded diagnostic artefacts,
and continues only with independent cells. Any uncaught infrastructure error
stops the schedule after persisting the active record.

- [ ] **Step 4: Add CLI parsing**

Use:

```text
mhd_hardware_workload_ladder.py smoke --out PATH
mhd_hardware_workload_ladder.py run --out PATH --repeats 5 --max-solver-seconds 7200
mhd_hardware_workload_ladder.py aggregate --out PATH --repeats 5
```

`smoke` selects Brio--Wu and OT/128 for both precisions/devices plus OT/512 GPU
for both precisions, one execution each, and writes `smoke_summary.json` without
promoting evidence.

- [ ] **Step 5: Run the fake integration and all targeted tests**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_mhd_hardware_workload_ladder.py -q
```

Expected: all tests pass without invoking solver binaries.

- [ ] **Step 6: Commit the resumable runner**

```powershell
git add -- scripts/regression/mhd_hardware_workload_ladder.py tests/py/test_mhd_hardware_workload_ladder.py
git commit -m "feat(report2): add resumable workload ladder runner"
```

---

### Task 5: Emit Stable Summaries, Diagnostic Figures, and Lifecycle Manifest

**Files:**
- Modify: `scripts/regression/mhd_hardware_workload_ladder.py`
- Modify: `tests/py/test_mhd_hardware_workload_ladder.py`
- Generate after real run: `experiments/week20/hardware_workload_ladder/manifest.json`
- Modify after real run: `tests/py/test_experiment_manifests.py`

**Interfaces:**
- Produces: `write_outputs(summary, out)`, `render_markdown(summary)`, `plot_summary(summary, out, stem="hardware_workload_ladder")`, and `write_manifest(summary, out)`.

- [ ] **Step 1: Write failing output and plot tests**

Assert a complete synthetic summary writes `summary.json`, `summary.csv`,
`summary.md`, `figures/hardware_workload_ladder.png`, and
`figures/hardware_workload_ladder.pdf`. Assert the Markdown includes all four
scope labels, both precisions, the three OT resolutions, warm-up/repeat policy,
timer scope, both gate statuses, and explicit non-portability. Assert PNG width
is at least 1800 pixels and PDF size is at least 5,000 bytes.

Also assert a correctness-failed summary writes a provenance manifest rather
than a canonical one:

```python
def test_manifest_lifecycle_follows_report_grade_gate(tmp_path):
    summary = ladder.aggregate_records(_complete_records(), expected_repeats=5)
    ladder.write_outputs(summary, tmp_path)
    canonical = ladder.write_manifest(summary, tmp_path)
    assert canonical["lifecycle"] == "canonical"
    summary["gate"]["correctness_pass"] = False
    summary["gate"]["report_grade_pass"] = False
    provenance = ladder.write_manifest(summary, tmp_path)
    assert provenance["lifecycle"] == "provenance"
```

- [ ] **Step 2: Run tests and verify failure**

Expected: FAIL because output functions are undefined.

- [ ] **Step 3: Implement stable renderers**

Use schema:

```python
{"name": "hrsc.hardware-workload-ladder", "version": 1}
```

CSV contains one row per comparison cell with case, resolution, precision,
five CPU/GPU timing statistics, ULP/absolute metrics, steps status, and cell
status. Markdown contains the same rows and a claim-boundary section.

The two-panel plot uses:

- panel (a): OT CPU and GPU median seconds with IQR at 128, 256, and 512;
- panel (b): paired CPU/GPU median ratio and IQR at those resolutions for fp64
  and fp32, a horizontal `ratio=1` line, and separately labelled Brio--Wu fp64
  and fp32 anchor markers.

Do not fit a line or exponent. Use log scale only for wall time, not for the
ratio. `plot_summary` accepts a stem so the publication generator can reuse the
same plotting implementation.

`write_manifest` emits schema version 1 with the canonical pipeline paths and
uses lifecycle `canonical` only when `report_grade_pass` is true. Evidence lists
the three summaries and both figure formats. Retention lists configs, logs,
metadata, scalar records, summaries, and figures as kept; grids are transient.

- [ ] **Step 4: Run targeted tests**

Expected: all new workflow tests pass.

- [ ] **Step 5: Commit output support**

```powershell
git add -- scripts/regression/mhd_hardware_workload_ladder.py tests/py/test_mhd_hardware_workload_ladder.py
git commit -m "feat(report2): render workload ladder evidence"
```

---

### Task 6: Build Fresh Binaries, Run Smokes, and Execute the Local Matrix

**Files:**
- Generate: `build-report2-hw-*` ignored directories.
- Generate: `experiments/week20/hardware_workload_ladder/` evidence packet.
- Modify: `tests/py/test_experiment_manifests.py` after manifest exists.

**Interfaces:**
- Consumes: completed workflow from Tasks 1--5 and a clean source commit.
- Produces: real summaries, figures, manifest, and gate outcome used by later tasks.

- [ ] **Step 1: Re-run the source-freeze gate**

Run the two commands under "Execution Prerequisite". Expected: in-scope source
clean. Record `git rev-parse HEAD` in `environment.json`.

- [ ] **Step 2: Configure four new build directories from the VS developer shell**

Run from a `cmd.exe` session initialised by:

```bat
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64
```

Then run:

```bat
cmake -S . -B build-report2-hw-cpu-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON -DENABLE_CUDA=OFF -DFAST_MATH=OFF -DSTRICT_IEEE=OFF -DRIEMANN_STRICT_INEQUALITY=OFF
cmake -S . -B build-report2-hw-cpu-float -G Ninja -DFLOAT_PRECISION=float -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON -DENABLE_CUDA=OFF -DFAST_MATH=OFF -DSTRICT_IEEE=OFF -DRIEMANN_STRICT_INEQUALITY=OFF
cmake -S . -B build-report2-hw-cuda-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON -DENABLE_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=120 -DFAST_MATH=OFF -DSTRICT_IEEE=OFF -DRIEMANN_STRICT_INEQUALITY=OFF
cmake -S . -B build-report2-hw-cuda-float -G Ninja -DFLOAT_PRECISION=float -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON -DENABLE_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=120 -DFAST_MATH=OFF -DSTRICT_IEEE=OFF -DRIEMANN_STRICT_INEQUALITY=OFF
```

Expected: all four configurations succeed and record effective compiler/math
semantics. Do not reuse another build directory if a configure fails.

- [ ] **Step 3: Build binaries and tests**

```bat
cmake --build build-report2-hw-cpu-double --target hrsc_mhd unit_tests
cmake --build build-report2-hw-cpu-float --target hrsc_mhd unit_tests
cmake --build build-report2-hw-cuda-double --target hrsc_mhd unit_tests gpu_smoke
cmake --build build-report2-hw-cuda-float --target hrsc_mhd unit_tests gpu_smoke
```

Expected: all targets build. Confirm `ninja -t deps` reports non-zero header
dependencies for representative MHD objects before trusting incremental state.

- [ ] **Step 4: Run CPU and CUDA correctness tests**

```powershell
& .\build-report2-hw-cpu-double\unit_tests.exe -r compact
& .\build-report2-hw-cpu-float\unit_tests.exe -r compact
& .\build-report2-hw-cuda-double\gpu_smoke.exe
& .\build-report2-hw-cuda-float\gpu_smoke.exe
& .\build-report2-hw-cuda-double\unit_tests.exe "[gpu][mhd]" -r compact
& .\build-report2-hw-cuda-float\unit_tests.exe "[gpu][mhd]" -r compact
```

Expected: every command exits 0 and both smokes identify the RTX 5070.

- [ ] **Step 5: Record the environment**

Write `experiments/week20/hardware_workload_ladder/environment.json` containing
source commit, `git status --porcelain` output, OS, CPU model, GPU name, driver,
CUDA toolkit, CMake, Ninja, MSVC, Python, NumPy, four binary paths/hashes, four
build-semantics JSON objects, and `OMP_NUM_THREADS=1`. Generate values from
commands; do not type version numbers from memory.

- [ ] **Step 6: Run reduced real smokes**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts\regression\mhd_hardware_workload_ladder.py smoke --out experiments\week20\hardware_workload_ladder
```

Expected: Brio--Wu and OT/128 complete for both precisions/devices, OT/512 GPU
completes for both precisions, all states are finite-positive, and every covered
CPU/GPU pair is zero ULP. If any condition fails, stop before the full run and
retain the smoke packet.

- [ ] **Step 7: Execute the full two-hour-bounded matrix**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts\regression\mhd_hardware_workload_ladder.py run --out experiments\week20\hardware_workload_ladder --repeats 5 --max-solver-seconds 7200
```

Expected: 16 warm-ups and 80 measured records, or a clean stop after the active
pair with an explicitly incomplete gate.

- [ ] **Step 8: Re-aggregate only from retained scalar records**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts\regression\mhd_hardware_workload_ladder.py aggregate --out experiments\week20\hardware_workload_ladder --repeats 5
```

Expected: regenerated summaries and figures byte-match the immediately previous
aggregate except for deliberately excluded timestamps.

- [ ] **Step 9: Audit gates and retention**

```powershell
$s = Get-Content -Raw -Encoding UTF8 experiments\week20\hardware_workload_ladder\summary.json | ConvertFrom-Json
$s.gate | ConvertTo-Json -Depth 4
Get-ChildItem experiments\week20\hardware_workload_ladder\runs -Recurse -Filter grid.bin
```

Expected for headline integration: all three gate booleans true and no
`grid.bin` output. If `report_grade_pass` is false, skip Tasks 7--8 manuscript
promotion steps, update only evidence/status documentation with the bounded
failure, and retain the existing Figure 5.3.

- [ ] **Step 10: Promote and validate the lifecycle manifest**

Add `experiments/week20/hardware_workload_ladder/manifest.json` to `MANIFESTS`
in `tests/py/test_experiment_manifests.py`, then run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_mhd_hardware_workload_ladder.py tests\py\test_experiment_manifests.py -q
```

Expected: all pass.

- [ ] **Step 11: Commit the audited evidence packet**

First verify no grids or build artefacts are staged:

```powershell
git status --short -- experiments/week20/hardware_workload_ladder tests/py/test_experiment_manifests.py
git check-ignore -v experiments/week20/hardware_workload_ladder/runs/*/grid.bin
```

Then add summaries, figures, environment, manifest, configs, logs, metadata,
scalar records, and the manifest test. Use `git add -f` only for the explicit
experiment directory after the no-grid audit.

```powershell
git add -f -- experiments/week20/hardware_workload_ladder
git add -- tests/py/test_experiment_manifests.py
git commit -m "exp(report2): add hardware workload ladder evidence"
```

---

### Task 7: Replace the Audited Hardware Figure Source

**Files:**
- Modify: `scripts/figures/report2_publication_figures.py`
- Modify: `tests/py/test_report2_publication_figures.py`
- Regenerate: `experiments/week18/report2_publication_figures/`
- Replace: `report2/phd-thesis-template-2.4/Figs/report2/ch5_hardware_reproducibility.pdf`

**Interfaces:**
- Consumes: new `summary.json` with `report_grade_pass=true`.
- Produces: stable figure ID `hardware_reproducibility`, updated source hashes,
  and unchanged total publication-figure count of seven.

- [ ] **Step 1: Write the failing publication-source test**

Update tests to assert:

```python
def test_hardware_figure_uses_complete_workload_ladder():
    data = publication.load_data()["hardware"]
    assert data["gate"]["report_grade_pass"] is True
    assert len(data["comparison_cells"]) == 8
    assert {
        row["resolution"] for row in data["comparison_cells"]
        if row["case"] == "orszag_tang_2d"
    } == {128, 256, 512}
    descriptor = next(row for row in publication.FIGURES
                      if row["id"] == "hardware_reproducibility")
    assert "workload" in descriptor["claim"].lower()
```

Keep the existing test that exactly seven PNG/PDF pairs and their hashes are
generated.

- [ ] **Step 2: Run test and verify failure**

Expected: FAIL because `SOURCES["hardware"]` still points to the Week-18 summary.

- [ ] **Step 3: Update the source audit and plotting call**

Set:

```python
"hardware": ("experiments/week20/hardware_workload_ladder/summary.json",),
```

Require the new technical/correctness/report-grade gates, 8 comparison cells,
5 repetitions, finite timing statistics, and zero pair/repeat ULP. Import the
new plotting module and call:

```python
workload_ladder.plot_summary(
    summary, out, stem="fig_hardware_reproducibility"
)
```

Update the descriptor claim to workload-dependent HLL timing across the tested
Brio--Wu anchor and OT resolutions. Keep exclusions for kernel attribution,
generic GPU performance, HLLD/KH/GPU-MCA, and portability.

- [ ] **Step 4: Run publication tests**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_report2_publication_figures.py -q
```

Expected: all pass and seven figures generated in the temporary test directory.

- [ ] **Step 5: Regenerate the audited figure set**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts\figures\report2_publication_figures.py --out experiments\week18\report2_publication_figures
Copy-Item -LiteralPath experiments\week18\report2_publication_figures\fig_hardware_reproducibility.pdf -Destination report2\phd-thesis-template-2.4\Figs\report2\ch5_hardware_reproducibility.pdf -Force
Get-FileHash experiments\week18\report2_publication_figures\fig_hardware_reproducibility.pdf, report2\phd-thesis-template-2.4\Figs\report2\ch5_hardware_reproducibility.pdf -Algorithm SHA256
```

Expected: generator gate passes, manifest source hash names the new summary,
and the two displayed SHA-256 hashes match.

- [ ] **Step 6: Commit figure integration**

```powershell
git add -- scripts/figures/report2_publication_figures.py tests/py/test_report2_publication_figures.py experiments/week18/report2_publication_figures report2/phd-thesis-template-2.4/Figs/report2/ch5_hardware_reproducibility.pdf
git commit -m "fig(report2): publish hardware workload ladder"
```

---

### Task 8: Integrate C3/C5/C6, Appendix, and Evidence Routing

**Files:**
- Create: `tests/py/test_report2_local_evidence_manuscript.py`
- Modify: `report2/phd-thesis-template-2.4/Chapter3/chapter3.tex`
- Modify: `report2/phd-thesis-template-2.4/Chapter5/chapter5.tex`
- Modify: `report2/phd-thesis-template-2.4/Chapter6/chapter6.tex`
- Modify: `report2/phd-thesis-template-2.4/Appendix1/appendix1.tex`
- Modify: `docs/experiment_logs/report2_evidence_map.md`
- Modify: `docs/INDEX.md`, `scripts/README.md`
- Modify: `report2/planning/chapter3_writing_plan.md`
- Modify: `report2/planning/chapter5_writing_plan.md`
- Modify: `report2/planning/drafting_status.md`
- Modify: `tests/py/test_report2_chapter5_manuscript.py`
- Modify: `tests/py/test_report2_documentation.py`

**Interfaces:**
- Consumes: gated summary and audited figure manifest.
- Produces: bounded prose and traceability without new analysis.

- [ ] **Step 1: Write failing manuscript integration tests**

Use the `_approximate_words` helper pattern from
`test_report2_chapter5_manuscript.py`. Assert:

```python
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHAPTER3 = ROOT / "report2" / "phd-thesis-template-2.4" / "Chapter3" / "chapter3.tex"
CHAPTER5 = ROOT / "report2" / "phd-thesis-template-2.4" / "Chapter5" / "chapter5.tex"
CHAPTER6 = ROOT / "report2" / "phd-thesis-template-2.4" / "Chapter6" / "chapter6.tex"
APPENDIX = ROOT / "report2" / "phd-thesis-template-2.4" / "Appendix1" / "appendix1.tex"


def _approximate_words(text: str) -> int:
    without_comments = re.sub(r"(?m)%.*$", "", text)
    without_commands = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^]]*\])?", " ", without_comments)
    without_braces = without_commands.translate(str.maketrans("{}$~", "    "))
    return len(re.findall(r"\b[\w'-]+\b", without_braces))


def test_chapter3_defines_units_freeze_and_uniform_new_timing_protocol():
    chapter = CHAPTER3.read_text(encoding="utf-8")
    assert "grid cells" in chapter and "independent replicates" in chapter
    assert "timing repetition" in chapter and "MCA sample" in chapter
    assert "one excluded warm-up" in chapter and "five measured" in chapter
    assert "declared before" in chapter and "fit windows" in chapter
    assert _approximate_words(chapter) <= 900


def test_chapter5_hardware_result_uses_ladder_and_keeps_causal_boundary():
    chapter = CHAPTER5.read_text(encoding="utf-8")
    assert "$128^2$" in chapter and "$512^2$" in chapter
    assert "workload" in chapter and "one excluded warm-up" in chapter
    assert "kernel" in chapter and "do not identify" in chapter
    assert "HLLD-on-GPU" not in chapter


def test_chapter6_and_appendix_cover_validity_and_traceability():
    discussion = CHAPTER6.read_text(encoding="utf-8")
    appendix = APPENDIX.read_text(encoding="utf-8")
    for phrase in ("construct validity", "internal validity", "external validity"):
        assert phrase in discussion
    assert "experiments/week20/hardware_workload_ladder/summary.json" in appendix
    assert "OMP_NUM_THREADS=1" in appendix
    assert "figure_manifest.json" in appendix


def test_manuscript_hides_internal_experiment_labels():
    prose = "\n".join(path.read_text(encoding="utf-8")
                       for path in (CHAPTER3, CHAPTER5, CHAPTER6))
    assert "week20" not in prose.lower()
    assert "report_grade_pass" not in prose
```

- [ ] **Step 2: Run manuscript tests and verify failure**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_report2_local_evidence_manuscript.py tests\py\test_report2_chapter5_manuscript.py tests\py\test_report2_documentation.py -q
```

Expected: new tests fail against current manuscript and old hardware assertions.

- [ ] **Step 3: Revise Chapter 3 within the existing seven sections**

In Section 3.5, include this content in the student's final voice:

> A deterministic run produced one saved numerical state; its grid cells were
> not treated as independent replicates. A timing repetition sampled end-to-end
> runtime for one fixed binary, configuration and machine, whereas an MCA
> sample represented one stochastic-arithmetic realisation rather than an
> independent physical experiment.

Replace the blanket historical timing sentence with the new primary protocol:
one excluded warm-up, five measured repetitions, median/IQR, paired CPU/GPU
ratios, and subprocess scope. Mention the historical packet only through
provenance, not in main methods. In Section 3.6 include:

> Comparison baselines, resolution cells, fit windows, scope-alignment rules
> and technical gates were declared before aggregate results were inspected;
> failed or negative outcomes did not trigger a changed grid, window or gate.

Update Table 3.1 coverage to show Brio--Wu CPU/GPU at `N=800` and OT CPU/GPU at
`128^2/256^2/512^2`. Remove the unused numerical-SNR definition and repeated
boundary prose until the approximate local count is 840--900 words.

- [ ] **Step 4: Replace the Chapter 5 hardware paragraph and caption**

Read the eight `comparison_cells` from the gated summary. Report only:

- CPU/GPU zero-ULP and zero-absolute agreement across all measured pairs;
- Brio--Wu fp64/fp32 median ratios as the small-workload anchor;
- OT fp64/fp32 ratios at 128, 256, and 512; and
- whether the observed ratio changed monotonically, non-monotonically, or
  remained flat, using the actual summary without treating any outcome as a
  gate.

Keep no more than four numeric ratios in prose; the figure carries the full
ladder. State that subprocess timing combines startup, transfer, launch,
compute, and required output and therefore does not identify a kernel-level
cause. Limit the result to HLL, two cases, two precisions, declared grids, and
one workstation. Update existing Chapter 5 tests to bind the prose numbers to
the new JSON fields rather than hard-coding the old 0.510/0.488/6.174/5.925
packet.

- [ ] **Step 5: Add Chapter 6 validity synthesis**

Under `\section{Limitations}`, add one paragraph with explicit construct,
internal, and external validity sentences:

- construct: saved-state discrepancy is not exact-state accuracy, and
  subprocess time is not kernel throughput;
- internal: the matched design controls declared axes but retains thermal,
  operating-system, I/O, transfer, and launch effects; and
- external: one laptop workstation, CUDA stack, HLL solver, and two cases do
  not establish portable performance.

Do not repeat C5 numbers.

- [ ] **Step 6: Extend the Appendix traceability table**

Add a Figure 5.3 row naming:

- `experiments/week20/hardware_workload_ladder/summary.json`;
- `experiments/week20/hardware_workload_ladder/environment.json`;
- `experiments/week20/hardware_workload_ladder/manifest.json`;
- `experiments/week18/report2_publication_figures/figure_manifest.json`; and
- `scripts/regression/mhd_hardware_workload_ladder.py`.

The table note states HLL, `OMP_NUM_THREADS=1`, one warm-up, five measured
repetitions, end-to-end timing, binary/config hashes, and transient-grid
removal. Keep reproduction routing concise.

- [ ] **Step 7: Update evidence and planning authorities**

Add an evidence-map row with:

- status `report-grade` only if all three gates pass, otherwise `provenance`;
- paper importance `P1`;
- bounded claim: saved-state agreement and workload-dependent repeated timing
  for the tested HLL cells;
- exclusions: kernel attribution, general GPU performance, HLLD/KH/GPU-MCA,
  and portability; and
- retention: summaries, figures, configs/logs/metadata/scalar records retained,
  grids removed.

Route the new workflow in `docs/INDEX.md` and `scripts/README.md`. Mark the
workload-ladder recommendation completed or bounded-failed in both chapter
plans, and update drafting status without promoting Chapters 3/5/6 past the
actual student-rewrite state.

- [ ] **Step 8: Run manuscript and documentation tests**

Run the command from Step 2.

Expected: all pass; Chapter 5 still has five figures and remains within its
1,850--1,950 approximate budget; Chapter 3 is at most 900 approximate words.

- [ ] **Step 9: Build and inspect the standalone PDF**

```powershell
& scripts\build_report2.ps1 -Clean
```

Expected: two pdflatex passes succeed. Inspect Figure 5.3, Table 3.1, the
Appendix traceability row, cross-references, captions, page breaks, and vector
text. Record the formal Overleaf word count separately; the local approximation
is not the submission authority.

- [ ] **Step 10: Commit manuscript and routing changes**

```powershell
git add -- report2/phd-thesis-template-2.4/Chapter3/chapter3.tex report2/phd-thesis-template-2.4/Chapter5/chapter5.tex report2/phd-thesis-template-2.4/Chapter6/chapter6.tex report2/phd-thesis-template-2.4/Appendix1/appendix1.tex docs/experiment_logs/report2_evidence_map.md docs/INDEX.md scripts/README.md report2/planning/chapter3_writing_plan.md report2/planning/chapter5_writing_plan.md report2/planning/drafting_status.md tests/py/test_report2_local_evidence_manuscript.py tests/py/test_report2_chapter5_manuscript.py tests/py/test_report2_documentation.py
git commit -m "docs(report2): integrate hardware workload evidence"
```

---

### Task 9: Final Verification and Release Audit

**Files:**
- Verify all files from Tasks 1--8.
- Modify only if a verification failure identifies a specific defect; rerun the failed gate after every fix.

**Interfaces:**
- Produces: evidence-backed completion status and a clean handoff for student rewrite/Overleaf review.

- [ ] **Step 1: Run the complete targeted Python suite**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_mhd_hardware_workload_ladder.py tests\py\test_mhd_gpu_hardware_axis.py tests\py\test_mhd_week18_supplemental.py tests\py\test_experiment_manifests.py tests\py\test_report2_publication_figures.py tests\py\test_report2_local_evidence_manuscript.py tests\py\test_report2_chapter5_manuscript.py tests\py\test_report2_documentation.py -q
```

Expected: zero failures.

- [ ] **Step 2: Re-run CPU and GPU executable tests**

Run the six executable commands from Task 6 Step 4.

Expected: every command exits 0.

- [ ] **Step 3: Re-aggregate and regenerate publication figures**

Run Task 6 Step 8 and Task 7 Step 5 again.

Expected: gates remain unchanged, source hashes match, and all seven audited
figure pairs pass publication preflight.

- [ ] **Step 4: Audit experiment completeness and retention**

```powershell
$s = Get-Content -Raw -Encoding UTF8 experiments\week20\hardware_workload_ladder\summary.json | ConvertFrom-Json
if (-not $s.gate.report_grade_pass) { throw 'report_grade_pass is false' }
if ($s.matrix.warmups -ne 16 -or $s.matrix.measured_runs -ne 80) { throw 'matrix count mismatch' }
$grids = @(Get-ChildItem experiments\week20\hardware_workload_ladder -Recurse -Filter grid.bin)
if ($grids.Count -ne 0) { throw "retained grid count: $($grids.Count)" }
Write-Output 'EVIDENCE_AUDIT=PASS'
```

Expected: `EVIDENCE_AUDIT=PASS`.

- [ ] **Step 5: Rebuild the Report 2 PDF**

```powershell
& scripts\build_report2.ps1 -Clean
```

Expected: exit 0 and a current `report2/phd-thesis-template-2.4/thesis.pdf`.

- [ ] **Step 6: Inspect final Git scope**

```powershell
git status --short
git log --oneline -8
git diff --check HEAD^
```

Expected: no uncommitted in-scope feature changes, no whitespace errors, and no
build directories or grids in commits. Existing unrelated user changes may
remain and must be reported without modification.

- [ ] **Step 7: Complete student-owned release gates**

The student rewrites AI-assisted prose in their own voice, checks all numbers
against `summary.json`, verifies British English and citations, records the
formal Overleaf word count, and reviews the signed-declaration requirement.
These external gates remain pending until the student confirms them.
