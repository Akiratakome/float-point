# Project Architecture Convergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Converge the generic and MHD experiment harnesses, expose compatible Euler/MHD application contracts, record effective build semantics, and add machine-readable experiment lifecycle metadata without changing solver numerics or historical evidence.

**Architecture:** Introduce small shared Python modules under `scripts/harness/`, then adapt the existing public runners through compatibility facades. Add a solver-independent C++ application library for configuration validation and completion reporting, while leaving Euler and MHD numerical kernels in place. Promote lifecycle manifests and a read-only cleanup audit only after the execution contracts are tested.

**Tech Stack:** Python 3.11+, dataclasses, standard-library JSON/subprocess/pathlib, pytest, C++17, CMake 3.18+, Catch2, existing HRSC binary I/O and experiment scripts.

## Global Constraints

- Preserve the pipeline `config -> build -> run -> measure -> aggregate -> plot`.
- Do not change solver numerical expressions, algorithms, tolerances, or existing cfg defaults.
- Preserve existing script paths, imports, binary formats, and summary fields.
- Add canonical metadata fields; do not bulk-rewrite historical metadata.
- Preserve historical build-directory names, including misleading `Ofast-ieee` names; record effective semantics separately.
- CPU remains the default device. MHD `device=gpu` must fail explicitly and must not implement GPU MHD.
- Do not delete experiment artifacts in this plan. Produce only an audited cleanup-candidate report.
- Do not commit build directories, large grids, or transient generated outputs.
- Keep unrelated untracked paths, including `tmp7reev1u0/` and unrelated files under `tools/`, out of every commit.

## File Structure

### New Python Harness Modules

- `scripts/harness/__init__.py`: stable exports for shared harness consumers.
- `scripts/harness/config.py`: cfg line replacement and source-preserving materialization.
- `scripts/harness/contracts.py`: `RunSpec`, `RunRecord`, `BuildSemantics`, artifact and failure types.
- `scripts/harness/metadata.py`: schema-v1 serialization, legacy normalization, and success gates.
- `scripts/harness/runner.py`: subprocess execution, status-line parsing, timing, and artifact validation.
- `scripts/harness/experiment_manifest.py`: experiment lifecycle manifest validation.
- `scripts/audit_experiments.py`: read-only discovery and reporting of nested build artifacts.

### New C++ Application Modules

- `src/app/validation.hpp`, `src/app/validation.cpp`: solver-independent device, domain, physics, and output validation.
- `src/app/run_completion.hpp`, `src/app/run_completion.cpp`: structured run failures, completion gates, and status lines.
- `src/app/mhd_run_config.hpp`, `src/app/mhd_run_config.cpp`: MHD adapter for common device/output behavior.
- `src/app/mhd_result.hpp`, `src/app/mhd_result.cpp`: MHD diagnostics formatting and established binary-output adapter.
- `tests/unit/test_app_run_completion.cpp`: completion and structured-failure tests.
- `tests/unit/test_app_mhd_run_config.cpp`: MHD default/unsupported-device/output compatibility tests.
- `tests/unit/test_app_mhd_result.cpp`: MHD diagnostic formatting and output adapter tests.

### Existing Compatibility Surfaces

- `scripts/run_matrix.py`: remains the canonical generic run entry.
- `scripts/regression/_mhd_harness.py`: remains import-compatible and delegates shared work.
- `scripts/regression/matrix_summary_report.py`: consumes normalized metadata and rejects failed runs.
- `src/main.cpp`: remains the Euler executable entry.
- `src/mhd_main.cpp`: remains the MHD executable entry.

---

### Task 1: Shared cfg Materialization

**Files:**
- Create: `scripts/harness/__init__.py`
- Create: `scripts/harness/config.py`
- Create: `tests/py/test_harness_config.py`
- Modify: `scripts/run_matrix.py`
- Modify: `scripts/regression/_mhd_harness.py`

**Interfaces:**
- Produces: `replace_or_append_cfg(text: str, key: str, value: str) -> str`
- Produces: `materialise_config(source: Path, target: Path, overrides: Mapping[str, str]) -> Path`
- Compatibility: `run_matrix._replace_or_append_cfg_line` and `_mhd_harness.replace_or_append_cfg` remain callable aliases during this task.

- [ ] **Step 1: Write failing cfg-contract tests**

```python
from pathlib import Path

from scripts.harness.config import materialise_config, replace_or_append_cfg


def test_replace_preserves_inline_comment_and_trailing_newline():
    text = "nx = 128  # validation grid\n# ny = 64\n"
    assert replace_or_append_cfg(text, "nx", "256") == (
        "nx = 256  # validation grid\n# ny = 64\n"
    )


def test_materialise_does_not_modify_source(tmp_path: Path):
    source = tmp_path / "source.cfg"
    target = tmp_path / "run" / "config.cfg"
    source.write_text("solver = hllc\n", encoding="utf-8")
    materialise_config(source, target, {"solver": "rusanov", "device": "gpu"})
    assert source.read_text(encoding="utf-8") == "solver = hllc\n"
    assert target.read_text(encoding="utf-8") == "solver = rusanov\ndevice = gpu\n"
```

- [ ] **Step 2: Run the focused tests and verify the import fails**

Run: `python -m pytest tests/py/test_harness_config.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.harness'`.

- [ ] **Step 3: Implement the shared cfg module**

```python
# scripts/harness/config.py
from __future__ import annotations

import shutil
from collections.abc import Mapping
from pathlib import Path


def replace_or_append_cfg(text: str, key: str, value: str) -> str:
    out: list[str] = []
    replaced = False
    for line in text.splitlines():
        if line.strip().startswith("#") or "=" not in line:
            out.append(line)
            continue
        if line.split("=", 1)[0].strip() != key:
            out.append(line)
            continue
        comment_at = line.find("#")
        suffix = ""
        if comment_at >= 0:
            before = line[:comment_at]
            suffix = before[len(before.rstrip()):] + line[comment_at:]
        out.append(f"{key} = {value}{suffix}")
        replaced = True
    if not replaced:
        out.append(f"{key} = {value}")
    return "\n".join(out) + "\n"


def materialise_config(
    source: Path, target: Path, overrides: Mapping[str, str]
) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    if overrides:
        text = target.read_text(encoding="utf-8")
        for key, value in overrides.items():
            text = replace_or_append_cfg(text, str(key), str(value))
        target.write_text(text, encoding="utf-8")
    return target
```

Export both functions from `scripts/harness/__init__.py`. Replace the duplicate implementations in both callers with imports and compatibility aliases. `run_matrix.materialise_run_config` must build one ordered overrides dictionary, with explicit binary output overrides applied last.

- [ ] **Step 4: Run cfg and legacy harness tests**

Run: `python -m pytest tests/py/test_harness_config.py tests/py/test_harness_scripts.py::test_run_matrix_writes_metadata_and_preserves_cfg tests/py/test_harness_scripts.py::test_run_matrix_applies_extra_cfg_overrides tests/py/test_mhd_harness.py::test_replace_or_append_cfg_preserves_inline_comment tests/py/test_mhd_harness.py::test_replace_or_append_cfg_appends_missing_key_with_trailing_newline -q`

Expected: PASS.

- [ ] **Step 5: Commit the cfg extraction**

```bash
git add scripts/harness/__init__.py scripts/harness/config.py scripts/run_matrix.py scripts/regression/_mhd_harness.py tests/py/test_harness_config.py
git commit -m "refactor: share harness config materialization"
```

### Task 2: Versioned Run Contracts and Metadata Compatibility

**Files:**
- Create: `scripts/harness/contracts.py`
- Create: `scripts/harness/metadata.py`
- Create: `tests/py/test_harness_metadata.py`
- Modify: `scripts/harness/__init__.py`

**Interfaces:**
- Produces: `FailureCategory`, `RequiredArtifact`, `BuildSemantics`, `RunSpec`, `RunRecord`
- Produces: `normalise_metadata(raw: Mapping[str, Any]) -> dict[str, Any]`
- Produces: `serialise_record(record: RunRecord, legacy: Mapping[str, Any]) -> dict[str, Any]`
- Produces: `require_successful_metadata(raw: Mapping[str, Any]) -> dict[str, Any]`
- Schema identity: `{"name": "hrsc.run-record", "version": 1}`

- [ ] **Step 1: Write failing legacy/canonical metadata tests**

```python
import pytest

from scripts.harness.metadata import normalise_metadata, require_successful_metadata


def test_legacy_aliases_normalise_without_rewrite():
    raw = {
        "name": "legacy",
        "returncode": 0,
        "output_binary": "grid.bin",
        "elapsed_wall_s": 1.25,
    }
    canonical = normalise_metadata(raw)
    assert canonical["schema"] == {"name": "hrsc.run-record", "version": 1}
    assert canonical["status"] == "success"
    assert canonical["artifacts"]["primary_output"] == "grid.bin"
    assert canonical["timing"]["elapsed_wall_s"] == 1.25


def test_failed_canonical_record_is_rejected():
    raw = {
        "schema": {"name": "hrsc.run-record", "version": 1},
        "status": "failed",
        "failure": {"category": "incomplete_run", "message": "stopped early"},
        "returncode": 2,
    }
    with pytest.raises(ValueError, match="incomplete_run"):
        require_successful_metadata(raw)
```

- [ ] **Step 2: Run tests and verify the contract modules are absent**

Run: `python -m pytest tests/py/test_harness_metadata.py -q`

Expected: FAIL on missing `scripts.harness.metadata`.

- [ ] **Step 3: Implement the dataclasses and normalization rules**

```python
# scripts/harness/contracts.py
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class FailureCategory(str, Enum):
    CONFIGURATION = "configuration_error"
    UNSUPPORTED = "unsupported_capability"
    NUMERICAL = "numerical_failure"
    INCOMPLETE = "incomplete_run"
    INFRASTRUCTURE = "infrastructure_error"
    ARTIFACT = "artifact_error"
    SCHEMA = "schema_error"


@dataclass(frozen=True)
class RequiredArtifact:
    path: Path
    must_be_fresh: bool = True


@dataclass(frozen=True)
class BuildSemantics:
    requested_opt_level: str | None = None
    requested_fast_math: bool | None = None
    effective_math_mode: str = "unknown"
    compiler_id: str | None = None
    compiler_version: str | None = None
    compiler_path: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RunSpec:
    name: str
    experiment: str
    command: tuple[str, ...]
    run_dir: Path
    source_config: Path
    run_config: Path
    cwd: Path | None = None
    timeout_s: float | None = None
    required_artifacts: tuple[RequiredArtifact, ...] = ()
    build_semantics: BuildSemantics | None = None


@dataclass(frozen=True)
class RunRecord:
    spec: RunSpec
    returncode: int
    elapsed_wall_s: float
    stdout_path: Path
    stderr_path: Path
    status: str
    failure: dict[str, str] | None = None
    completion: dict[str, Any] | None = None
```

`normalise_metadata` must:

1. reject schema names other than `hrsc.run-record` and versions greater than 1;
2. treat legacy `returncode == 0` with no status as success;
3. resolve primary output from canonical `artifacts.primary_output`, then `raw_output`, then `output_binary`;
4. resolve elapsed wall time from canonical `timing.elapsed_wall_s`, then `elapsed_wall_s`, then `timing.total_s`;
5. return a new dictionary without mutating the input.

`serialise_record` must emit canonical schema/status/failure/completion/build semantics and merge caller-supplied legacy fields unchanged. `require_successful_metadata` must normalize first and reject every status other than `success`.

- [ ] **Step 4: Run metadata tests**

Run: `python -m pytest tests/py/test_harness_metadata.py -q`

Expected: PASS.

- [ ] **Step 5: Commit the metadata contract**

```bash
git add scripts/harness/__init__.py scripts/harness/contracts.py scripts/harness/metadata.py tests/py/test_harness_metadata.py
git commit -m "feat: add versioned harness run contracts"
```

### Task 3: Shared Process Runner and Generic Matrix Migration

**Files:**
- Create: `scripts/harness/runner.py`
- Create: `tests/py/test_harness_runner.py`
- Modify: `scripts/run_matrix.py`
- Modify: `scripts/regression/matrix_summary_report.py`
- Modify: `tests/py/test_harness_scripts.py`
- Modify: `tests/py/test_matrix_summary_report.py`

**Interfaces:**
- Consumes: `RunSpec`, `RunRecord`, `RequiredArtifact`, `serialise_record`, `normalise_metadata`
- Produces: `execute_run(spec: RunSpec, dry_run: bool = False) -> RunRecord`
- Produces: `parse_run_status(stderr_text: str) -> tuple[str | None, dict[str, Any] | None, dict[str, str] | None]`
- Produces: `git_provenance(repo_root: Path) -> dict[str, Any]`
- Compatibility: `run_matrix.build_metadata` and `run_matrix.run_one` keep their existing signatures.

- [ ] **Step 1: Write failing process/status/artifact tests**

```python
import sys
from pathlib import Path

from scripts.harness.contracts import RequiredArtifact, RunSpec
from scripts.harness.runner import execute_run, parse_run_status


def test_status_parser_reads_last_structured_line():
    status, completion, failure = parse_run_status(
        "[run-status] status=failed reason=incomplete_run\n"
        "[run-status] status=success final_time=0.1 target_time=0.1 steps=4\n"
    )
    assert status == "success"
    assert completion == {"final_time": 0.1, "target_time": 0.1, "steps": 4}
    assert failure is None


def test_missing_required_artifact_marks_record_failed(tmp_path: Path):
    cfg = tmp_path / "config.cfg"
    cfg.write_text("x = 1\n", encoding="utf-8")
    spec = RunSpec(
        name="missing-output",
        experiment="pytest",
        command=(sys.executable, "-c", "print('ok')"),
        run_dir=tmp_path / "run",
        source_config=cfg,
        run_config=cfg,
        required_artifacts=(RequiredArtifact(tmp_path / "missing.bin"),),
    )
    record = execute_run(spec)
    assert record.status == "failed"
    assert record.failure["category"] == "artifact_error"
```

- [ ] **Step 2: Run focused tests and verify failure**

Run: `python -m pytest tests/py/test_harness_runner.py tests/py/test_harness_scripts.py::test_run_matrix_writes_metadata_and_preserves_cfg -q`

Expected: FAIL because `runner.py` and canonical fields do not exist.

- [ ] **Step 3: Implement the process runner**

The runner must create the run directory, open `stdout.txt` and `stderr.txt`, use `time.perf_counter()`, pass `cwd` and `timeout`, and never raise before returning a record. Convert `subprocess.TimeoutExpired` into `infrastructure_error`. After process completion:

```python
_STATUS_RE = re.compile(r"^\[run-status\]\s+(?P<body>.+)$")


def parse_run_status(stderr_text: str):
    parsed = None
    for line in stderr_text.splitlines():
        match = _STATUS_RE.match(line.strip())
        if match:
            parsed = dict(token.split("=", 1) for token in match["body"].split())
    if parsed is None:
        return None, None, None
    if parsed.get("status") == "success":
        return "success", {
            "final_time": float(parsed["final_time"]),
            "target_time": float(parsed["target_time"]),
            "steps": int(parsed["steps"]),
        }, None
    category = parsed.get("reason", "infrastructure_error")
    return "failed", None, {"category": category, "message": category}
```

Exit status is authoritative: nonzero always means failed. A successful structured status cannot override a nonzero return code. Required artifacts are checked only after process success; freshness compares `st_mtime` to the captured wall-clock start. Dry runs write empty stdout, `dry-run\n` stderr, and a successful record with `completion.reported == False`.

`git_provenance` runs `git rev-parse HEAD` and `git status --porcelain --untracked-files=no` in the supplied repository root and returns `{"commit": ..., "dirty": bool}`. On a non-Git input it returns `{"commit": "unknown", "dirty": None}`. Canonical metadata stores this under `provenance.git`; the existing top-level `git_commit` remains unchanged.

- [ ] **Step 4: Adapt `run_matrix.py` without removing legacy fields**

Construct a `RunSpec` in `run_one`, call `execute_run`, and serialize with these legacy fields intact:

```python
legacy = {
    "experiment": experiment,
    "name": run.name,
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "git_commit": git_commit(),
    "binary": str(run.binary),
    "source_config": str(run.source_config),
    "run_config": str(config),
    "precision": run.precision,
    "build": run.build,
    "raw_output": str(run.raw_output) if run.raw_output else None,
    "extra_cfg": run.extra_cfg or {},
    "command": list(spec.command),
    "returncode": record.returncode,
    "timing": {"total_s": parse_timing_total_s(stderr_text)},
    "stdout": str(record.stdout_path),
    "stderr": str(record.stderr_path),
}
```

Keep `build_metadata` as a compatibility wrapper that returns the same legacy keys plus canonical schema fields. Write failed metadata before raising the existing `RuntimeError`.

In `matrix_summary_report._load_runs`, call `require_successful_metadata` before opening outputs. Legacy return-code-zero records continue to pass; canonical failed records raise a `ValueError` naming the failure category.

- [ ] **Step 5: Run generic harness and summary tests**

Run: `python -m pytest tests/py/test_harness_runner.py tests/py/test_harness_scripts.py tests/py/test_matrix_summary_report.py -q`

Expected: PASS, including unchanged assertions for `raw_output`, `timing.total_s`, and matrix paths.

- [ ] **Step 6: Commit the shared runner migration**

```bash
git add scripts/harness/runner.py scripts/run_matrix.py scripts/regression/matrix_summary_report.py tests/py/test_harness_runner.py tests/py/test_harness_scripts.py tests/py/test_matrix_summary_report.py
git commit -m "refactor: run matrices through shared harness"
```

### Task 4: MHD Harness Compatibility Facade

**Files:**
- Modify: `scripts/regression/_mhd_harness.py`
- Modify: `tests/py/test_mhd_harness.py`

**Interfaces:**
- Consumes: shared `RunSpec`, `RequiredArtifact`, `execute_run`, `serialise_record`, cfg helper.
- Preserves: `run_case(...) -> tuple[subprocess.CompletedProcess-like, dict[str, Any], str]`
- Preserves metadata: `output_binary`, `elapsed_wall_s`, hashes, `stderr_diagnostics`, config text.

- [ ] **Step 1: Add a failing compatibility test for canonical and legacy fields**

Extend the existing relative-output test:

```python
assert meta["schema"] == {"name": "hrsc.run-record", "version": 1}
assert meta["status"] == "success"
assert meta["output_binary"] == str(abs_out)
assert meta["artifacts"]["primary_output"] == str(abs_out)
assert meta["elapsed_wall_s"] == meta["timing"]["elapsed_wall_s"]
assert meta["stderr_diagnostics"] == {}
```

Add a second test whose Python command exits 7 and assert that `metadata.json` exists, contains `status == "failed"`, and `run_case` raises its existing `RuntimeError` after writing metadata.

- [ ] **Step 2: Run the MHD harness tests and verify canonical assertions fail**

Run: `python -m pytest tests/py/test_mhd_harness.py -q`

Expected: FAIL because MHD metadata lacks schema/status/artifacts.

- [ ] **Step 3: Delegate process and artifact handling**

Keep pure numerical helpers and `parse_mhd_diagnostics` in `_mhd_harness.py`. Replace only process timing, stdout/stderr management, and artifact freshness checks with `execute_run`. Build legacy metadata exactly as today, then call `serialise_record`. Return a lightweight `subprocess.CompletedProcess(record.spec.command, record.returncode)` to preserve callers that inspect `.returncode`.

Do not remove `resolve_binary`, `sha256_file`, `git_commit`, `ROOT`, or the re-exported `read_binary`.

- [ ] **Step 4: Run MHD harness and dependent driver tests**

Run: `python -m pytest tests/py/test_mhd_harness.py tests/py/test_mhd_precision_pilot_driver.py tests/py/test_mhd_temporal_divergence.py -q`

Expected: PASS with no historical summary regeneration.

- [ ] **Step 5: Commit the facade conversion**

```bash
git add scripts/regression/_mhd_harness.py tests/py/test_mhd_harness.py
git commit -m "refactor: adapt MHD runner to shared harness"
```

### Task 5: Effective Compiler and Math Semantics

**Files:**
- Create: `cmake/build_semantics.json.in`
- Modify: `cmake/CompilerFlags.cmake`
- Modify: `CMakeLists.txt`
- Modify: `scripts/build_matrix.py`
- Modify: `scripts/harness/contracts.py`
- Modify: `scripts/run_matrix.py`
- Modify: `tests/py/test_build_matrix_filter.py`
- Modify: `tests/py/test_cmake_compiler_flags.py`
- Modify: `tests/py/test_harness_scripts.py`

**Interfaces:**
- Produces: `BuildVariant.effective_math_mode -> str`
- Produces: `${CMAKE_BINARY_DIR}/build_semantics.json` at CMake configure time.
- Produces: `load_build_semantics(path: Path, fallback_label: str | None) -> BuildSemantics`
- Compatibility: `BuildVariant.name` and `build_dir` remain byte-for-byte unchanged.

- [ ] **Step 1: Write failing semantics tests**

```python
def test_ofast_is_recorded_as_effective_fast_without_renaming():
    variant = BuildVariant("double", "Ofast", False, False)
    assert variant.name == "cpu-double-Ofast-ieee-leq"
    assert variant.effective_math_mode == "fast"


def test_o2_without_fast_math_is_compiler_default_not_claimed_ieee():
    variant = BuildVariant("double", "O2", False, False)
    assert variant.name == "cpu-double-O2-ieee-leq"
    assert variant.effective_math_mode == "compiler-default"
```

Extend the CMake source test to require `HRSC_EFFECTIVE_MATH_MODE`, an `Ofast` fast branch, a `FAST_MATH` fast branch, and a `STRICT_IEEE` strict branch. Extend run-matrix metadata tests to load a temporary `build_semantics.json` beside the fake binary and assert compiler ID/version and effective mode appear under canonical `build_semantics`.

- [ ] **Step 2: Run semantics tests and verify failure**

Run: `python -m pytest tests/py/test_build_matrix_filter.py tests/py/test_cmake_compiler_flags.py tests/py/test_harness_scripts.py -q`

Expected: FAIL on missing `effective_math_mode` and build metadata.

- [ ] **Step 3: Add effective semantics without changing variant names**

```python
@property
def effective_math_mode(self) -> str:
    if self.opt_level == "Ofast" or self.fast_math:
        return "fast"
    return "compiler-default"
```

At the end of `CompilerFlags.cmake`, set:

```cmake
if(STRICT_IEEE)
    set(HRSC_EFFECTIVE_MATH_MODE "strict")
elseif(FAST_MATH OR OPT_LEVEL STREQUAL "Ofast")
    set(HRSC_EFFECTIVE_MATH_MODE "fast")
else()
    set(HRSC_EFFECTIVE_MATH_MODE "compiler-default")
endif()
```

Generate `build_semantics.json` from CMake with schema `hrsc.build-semantics` version 1 and fields `compiler.id`, `compiler.version`, `compiler.path`, `requested.opt_level`, `requested.fast_math`, `requested.strict_ieee`, and `effective_math_mode`. Normalize the compiler path to forward slashes before `configure_file` so Windows JSON remains valid.

Use valid JSON booleans and this exact template shape:

```cmake
set(HRSC_FAST_MATH_JSON false)
if(FAST_MATH)
    set(HRSC_FAST_MATH_JSON true)
endif()
set(HRSC_STRICT_IEEE_JSON false)
if(STRICT_IEEE)
    set(HRSC_STRICT_IEEE_JSON true)
endif()
file(TO_CMAKE_PATH "${CMAKE_CXX_COMPILER}" HRSC_CXX_COMPILER_JSON_PATH)
configure_file(
    ${CMAKE_SOURCE_DIR}/cmake/build_semantics.json.in
    ${CMAKE_BINARY_DIR}/build_semantics.json
    @ONLY)
```

```json
{
  "schema": {"name": "hrsc.build-semantics", "version": 1},
  "compiler": {
    "id": "@CMAKE_CXX_COMPILER_ID@",
    "version": "@CMAKE_CXX_COMPILER_VERSION@",
    "path": "@HRSC_CXX_COMPILER_JSON_PATH@"
  },
  "requested": {
    "opt_level": "@OPT_LEVEL@",
    "fast_math": @HRSC_FAST_MATH_JSON@,
    "strict_ieee": @HRSC_STRICT_IEEE_JSON@
  },
  "effective_math_mode": "@HRSC_EFFECTIVE_MATH_MODE@",
  "flag_evidence": {
    "optimization": "@_hrsc_opt_flags_msg@",
    "fast_math": "@_hrsc_fast_math_flags_msg@",
    "strict_ieee": "@HRSC_STRICT_IEEE_FLAG_EVIDENCE@"
  }
}
```

Initialize the three flag-evidence variables to empty strings before their branches. For strict mode, set `HRSC_STRICT_IEEE_FLAG_EVIDENCE` to `target-specific strict CPU/CUDA flags from hrsc_apply_strict_ieee_*`; this avoids claiming flags that were not applied while still identifying the authoritative CMake functions.

- [ ] **Step 4: Load configure-time semantics in new run metadata**

`run_matrix.normalise_run` or `run_one` must look for `run.binary.parent / "build_semantics.json"`. If absent, derive only `requested_opt_level`, `requested_fast_math`, and effective mode from the stable build label; leave compiler fields `None`. Never infer `strict` from a name containing `ieee`.

- [ ] **Step 5: Run semantics and compatibility tests**

Run: `python -m pytest tests/py/test_build_matrix_filter.py tests/py/test_cmake_compiler_flags.py tests/py/test_harness_scripts.py tests/py/test_harness_metadata.py -q`

Expected: PASS, and all historical name-list assertions remain unchanged.

- [ ] **Step 6: Commit build semantics**

```bash
git add cmake/build_semantics.json.in cmake/CompilerFlags.cmake CMakeLists.txt scripts/build_matrix.py scripts/harness/contracts.py scripts/run_matrix.py tests/py/test_build_matrix_filter.py tests/py/test_cmake_compiler_flags.py tests/py/test_harness_scripts.py
git commit -m "feat: record effective floating point build semantics"
```

### Task 6: Common C++ Validation and Completion Contracts

**Files:**
- Create: `src/app/validation.hpp`
- Create: `src/app/validation.cpp`
- Create: `src/app/run_completion.hpp`
- Create: `src/app/run_completion.cpp`
- Create: `tests/unit/test_app_run_completion.cpp`
- Modify: `src/app/run_config.hpp`
- Modify: `src/app/run_config.cpp`
- Modify: `tests/unit/test_app_run_config.cpp`
- Modify: `CMakeLists.txt`

**Interfaces:**
- Produces: `enum class Device { Cpu, Gpu };`
- Produces: `Device parse_device(const Config& cfg);`
- Produces: existing validation functions at unchanged `hrsc::app` names.
- Produces: `RunFailure`, `FailureCategory`, `require_run_complete`, `write_run_success`, `write_run_failure`.

- [ ] **Step 1: Write failing device and completion unit tests**

```cpp
TEST_CASE("parse_device defaults to CPU and validates values", "[app][config]") {
    Config cfg;
    REQUIRE(parse_device(cfg) == Device::Cpu);
    cfg.set("device", "gpu");
    REQUIRE(parse_device(cfg) == Device::Gpu);
    cfg.set("device", "typo");
    REQUIRE_THROWS_WITH(parse_device(cfg),
                        "Invalid device='typo'; expected 'cpu' or 'gpu'");
}

TEST_CASE("run completion rejects early and non-finite final times", "[app][run]") {
    REQUIRE_NOTHROW(require_run_complete(0.1, 0.1, 4));
    REQUIRE_THROWS_AS(require_run_complete(0.09, 0.1, 4), RunFailure);
    REQUIRE_THROWS_AS(
        require_run_complete(std::numeric_limits<double>::quiet_NaN(), 0.1, 4),
        RunFailure);
}
```

Also assert that the early failure category is `IncompleteRun`, the non-finite category is `NumericalFailure`, and success serialization is exactly:

```text
[run-status] status=success final_time=0.1 target_time=0.1 steps=4
```

- [ ] **Step 2: Reconfigure and verify the new unit tests fail**

Run: `cmake -S . -B build-double -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release`

Run: `cmake --build build-double --target unit_tests`

Expected: compile failure because validation/completion interfaces are absent. Reconfiguration is required because test discovery changes.

- [ ] **Step 3: Extract solver-independent validation**

Move `parse_output_times`, `validate_domain`, `validate_physics`, `validate_output_precision`, and `validate_output_options` from `run_config.cpp` into `validation.cpp`; keep their namespace and signatures unchanged. `run_config.hpp` includes `app/validation.hpp`, so existing callers continue compiling.

Implement device parsing as:

```cpp
Device parse_device(const Config& cfg) {
    const std::string value = cfg.get_string("device", "cpu");
    if (value == "cpu") return Device::Cpu;
    if (value == "gpu") return Device::Gpu;
    throw std::runtime_error(
        "Invalid device='" + value + "'; expected 'cpu' or 'gpu'");
}
```

- [ ] **Step 4: Implement structured completion**

```cpp
enum class FailureCategory {
    ConfigurationError,
    UnsupportedCapability,
    NumericalFailure,
    IncompleteRun,
    ArtifactError,
};

class RunFailure : public std::runtime_error {
public:
    RunFailure(FailureCategory category, const std::string& message);
    FailureCategory category() const noexcept { return category_; }
private:
    FailureCategory category_;
};
```

`require_run_complete` throws `NumericalFailure` when final or target time is non-finite, throws `IncompleteRun` when `final_time < target_time`, and otherwise returns. It does not alter the solver stopping condition or introduce a numerical tolerance. `write_run_failure` emits one tokenized status line plus the existing human-readable `[error]` line.

- [ ] **Step 5: Split the CMake app targets and fix test discovery**

```cmake
add_library(hrsc_app_common STATIC
    src/app/run_completion.cpp
    src/app/validation.cpp)
target_link_libraries(hrsc_app_common PUBLIC hrsc_core)

target_link_libraries(hrsc_app PUBLIC hrsc_app_common hrsc_euler)

file(GLOB TEST_SOURCES CONFIGURE_DEPENDS tests/unit/test_*.cpp)
```

Keep Euler-only cases/diagnostics/output/run-config in `hrsc_app`. Link `unit_tests` to both libraries through existing public dependencies.

- [ ] **Step 6: Build and run focused C++ tests**

Run: `cmake --build build-double --target unit_tests`

Run: `.\build-double\unit_tests.exe "[app]" -r compact`

Expected: all app tests pass.

- [ ] **Step 7: Commit the common application contracts**

```bash
git add CMakeLists.txt src/app/validation.hpp src/app/validation.cpp src/app/run_completion.hpp src/app/run_completion.cpp src/app/run_config.hpp src/app/run_config.cpp tests/unit/test_app_run_config.cpp tests/unit/test_app_run_completion.cpp
git commit -m "refactor: add common application run contracts"
```

### Task 7: Enforce Euler Completion Before Authoritative Output

**Files:**
- Modify: `src/main.cpp`
- Modify: `src/gpu/euler_gpu_solver.cu`
- Modify: `tests/unit/test_gpu_solver_e2e.cpp`
- Create: `tests/py/test_application_status_contract.py`

**Interfaces:**
- Consumes: `parse_device`, `require_run_complete`, `RunFailure`, status writers.
- Behavior: CPU/GPU final binary or table output occurs only after completion succeeds.
- Behavior: GPU non-finite or non-positive `dt` is a numerical failure, never a successful early return.

- [ ] **Step 1: Write failing executable contract tests**

The Python test locates `build-double/hrsc[.exe]` and skips only when the target is absent. It creates a valid tiny Sod cfg with `t_end = 0`, runs it, and asserts return code 0 plus a success status line. A second source-contract assertion requires the final `write_binary` calls in both `run_normal` and `run_normal_gpu` to follow `require_run_complete`.

For CUDA builds, add this Catch2 case:

```cpp
TEST_CASE("EulerGpuSolver rejects a non-positive CFL step", "[gpu][completion]") {
    Grid2D<double, EulerNVars> grid(4, 1);
    grid.dx = 0.25;
    grid.dy = 0.25;
    setup_sod<double>(grid.view(), 1.4);
    EulerGpuSolver<double> solver(
        std::move(grid), 0.0, 0.0, 1.4, 0.0, 0.1,
        FluxScheme::Rusanov, BoundaryType::Outflow, BoundaryType::Outflow);
    REQUIRE_THROWS(solver.run());
}
```

- [ ] **Step 2: Run CPU contract tests and verify missing status**

Run: `python -m pytest tests/py/test_application_status_contract.py -q`

Expected: FAIL because Euler does not emit `[run-status]`.

- [ ] **Step 3: Apply completion gates to every Euler normal path**

Replace manual string device validation with `parse_device`. After each CPU solver run and before `Finished:` or final output, call:

```cpp
require_run_complete(
    static_cast<double>(solver.time()), t_end, solver.step_count());
write_run_success(
    std::cerr, static_cast<double>(solver.time()), t_end, solver.step_count());
```

For GPU, call the same gate using `current_time()` before downloading/writing the final grid. Do not gate intermediate diagnostic dumps or explicitly named checkpoint outputs as authoritative final results.

Wrap only the calls that advance a solver (`solver.run`, `run_with_diagnostics`, `run_with_binary_checkpoints`, and `EulerGpuSolver::run`) so a non-`RunFailure` exception becomes `RunFailure(FailureCategory::NumericalFailure, error.what())`. Configuration parsing remains outside these wrappers.

Catch `RunFailure` before `std::exception` in `main`, emit `write_run_failure`, and return 2. Map a remaining generic exception to `ConfigurationError`, emit the same structured failure line plus the existing `[error]` message, and return 2. This makes configuration, numerical, and incomplete failures distinguishable without changing solver code.

- [ ] **Step 4: Make GPU invalid time steps fail explicitly**

In `EulerGpuSolver::run`, replace the early break:

```cpp
if (!std::isfinite(static_cast<double>(dt)) || dt <= TimeReal(0)) {
    throw std::runtime_error("EulerGpuSolver produced a non-finite or non-positive dt");
}
```

Include `<cmath>`. Do not change CFL calculation, clipping, update order, allocations, or synchronization.

- [ ] **Step 5: Build and run available Euler tests**

Run: `cmake --build build-double --target hrsc unit_tests`

Run: `.\build-double\unit_tests.exe "[app]" -r compact`

Run: `python -m pytest tests/py/test_application_status_contract.py tests/py/test_output_times.py -q`

Expected: PASS. When a configured CUDA build is available, also run `.\build-cuda-double-strict\unit_tests.exe "[gpu][completion]" -r compact`; otherwise record the skip in the final verification task.

- [ ] **Step 6: Commit Euler completion enforcement**

```bash
git add src/main.cpp src/gpu/euler_gpu_solver.cu tests/unit/test_gpu_solver_e2e.cpp tests/py/test_application_status_contract.py
git commit -m "fix: reject incomplete Euler runs"
```

### Task 8: Adapt MHD to Common Device, Output, and Completion Interfaces

**Files:**
- Create: `src/app/mhd_run_config.hpp`
- Create: `src/app/mhd_run_config.cpp`
- Create: `tests/unit/test_app_mhd_run_config.cpp`
- Modify: `src/mhd_main.cpp`
- Modify: `CMakeLists.txt`
- Modify: `tests/py/test_application_status_contract.py`
- Create: `src/app/mhd_result.hpp`
- Create: `src/app/mhd_result.cpp`
- Create: `tests/unit/test_app_mhd_result.cpp`

**Interfaces:**
- Produces: `MhdRunOptions parse_mhd_run_options(const Config& cfg)`
- Produces: `void require_mhd_device_supported(Device device)`
- Produces: `MhdDiagnostics collect_mhd_diagnostics(...)` and `write_mhd_result(...)` under `hrsc::app`.
- Preserves: absent `device` means CPU; absent `output_format` preserves existing output-file behavior.
- Rejects: MHD GPU and MHD checkpoint output times with `UnsupportedCapability`.

- [ ] **Step 1: Write failing MHD adapter unit tests**

```cpp
TEST_CASE("MHD run options preserve legacy CPU binary behavior", "[app][mhd]") {
    Config cfg;
    cfg.set("output_file", "grid.bin");
    const auto options = parse_mhd_run_options(cfg);
    REQUIRE(options.device == Device::Cpu);
    REQUIRE(options.output_format == "binary");
    REQUIRE(options.output_file == "grid.bin");
}

TEST_CASE("MHD GPU is an explicit unsupported capability", "[app][mhd]") {
    Config cfg;
    cfg.set("device", "gpu");
    const auto options = parse_mhd_run_options(cfg);
    try {
        require_mhd_device_supported(options.device);
        FAIL("expected RunFailure");
    } catch (const RunFailure& failure) {
        REQUIRE(failure.category() == FailureCategory::UnsupportedCapability);
    }
}
```

Add cases for explicit `output_format=binary`, invalid `output_format=table`, and nonempty `output_times`.

In `test_app_mhd_result.cpp`, construct a small finite MHD grid, assert the formatted diagnostic line retains the existing keys `t`, `steps`, `divB_mean`, and `divB_max`, and write a temporary binary through `write_mhd_result`. Read the header back with the existing binary reader contract and assert `nvars == MhdNVars` and the recorded time is unchanged.

- [ ] **Step 2: Reconfigure/build and verify tests fail**

Run: `cmake -S . -B build-double -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release`

Run: `cmake --build build-double --target unit_tests`

Expected: compile failure because the MHD adapter is absent.

- [ ] **Step 3: Implement the MHD application adapter**

```cpp
struct MhdRunOptions {
    Device device = Device::Cpu;
    std::string output_format;
    std::string output_file;
};
```

Rules:

- `output_file` empty and `output_format` absent means no output.
- `output_file` nonempty and `output_format` absent means binary, preserving current behavior.
- explicit `output_format=binary` requires `output_file`.
- `table` and other values are configuration errors because MHD has never emitted the Euler table format.
- nonempty `output_times` is unsupported, not silently ignored.
- `device=gpu` throws `UnsupportedCapability` with message `device=gpu is not supported by hrsc_mhd`.

Move the application-level divB collection/formatting and conditional binary write out of `mhd_main.cpp` into `mhd_result`. The adapter calls the existing `compute_divB_norms` and `write_binary` templates; it must preserve the exact stderr field names and binary layout.

- [ ] **Step 4: Adapt `mhd_main.cpp` at the application boundary**

Use common `validate_domain` and `validate_physics`; keep MHD-only `glm_cr` and `x0` checks local. Parse `MhdRunOptions` before solver construction. Wrap solver execution errors as `NumericalFailure`, then call `require_run_complete` before delegating divB diagnostics and binary output to `write_mhd_result`. Emit one success status line after completion.

Catch `RunFailure` first and emit its structured failure line. Map remaining pre-solver exceptions to `ConfigurationError`; solver execution itself is already wrapped as `NumericalFailure`. Keep usage return code 1 and all application failures return code 2. Do not change MHD initial conditions, flux selection, boundary implementation, solver loop, or binary writer.

Link `hrsc_mhd` to `hrsc_app_common` and compile `mhd_run_config.cpp` into that library.

- [ ] **Step 5: Run MHD unit and executable contract tests**

Run: `cmake --build build-double --target hrsc_mhd unit_tests`

Run: `.\build-double\unit_tests.exe "[app][mhd]" -r compact`

Run: `.\build-double\unit_tests.exe "[mhd]" -r compact`

Run: `python -m pytest tests/py/test_application_status_contract.py tests/py/test_mhd_harness.py -q`

Expected: CPU MHD smoke returns success status; GPU cfg returns code 2 with `reason=unsupported_capability`; no binary is produced for the rejected GPU run.

- [ ] **Step 6: Commit the MHD adapter**

```bash
git add CMakeLists.txt src/app/mhd_run_config.hpp src/app/mhd_run_config.cpp src/app/mhd_result.hpp src/app/mhd_result.cpp src/mhd_main.cpp tests/unit/test_app_mhd_run_config.cpp tests/unit/test_app_mhd_result.cpp tests/py/test_application_status_contract.py
git commit -m "refactor: align MHD application run interface"
```

### Task 9: Experiment Lifecycle Manifests

**Files:**
- Create: `scripts/harness/experiment_manifest.py`
- Create: `tests/py/test_experiment_manifests.py`
- Create: `experiments/week12/brio_wu_1d/manifest.json`
- Create: `experiments/week12/mhd_2d/brio_wu_2d/manifest.json`
- Create: `experiments/week12/mhd_2d/divb_clean/manifest.json`
- Create: `experiments/week13/hlld_divb_followup/manifest.json`
- Create: `experiments/week13/orszag_tang/manifest.json`
- Create: `experiments/week13/kelvin_helmholtz/manifest.json`
- Create: `experiments/week14/mhd_precision_pilot/manifest.json`
- Create: `experiments/week14/mhd_precision_pilot_hlld/manifest.json`
- Create: `experiments/week15/brio_wu_precision_pilot_p1/manifest.json`
- Create: `experiments/week15/brio_wu_precision_pilot_hlld_p1/manifest.json`
- Create: `experiments/week15/orszag_tang_precision_smoke/manifest.json`
- Create: `experiments/week15/orszag_tang_precision_smoke_hlld/manifest.json`
- Create: `experiments/week15/mhd_temporal_divergence/manifest.json`

**Interfaces:**
- Produces: `validate_manifest(path: Path, repo_root: Path) -> list[str]`
- Produces: `load_valid_manifest(path: Path, repo_root: Path) -> dict[str, Any]`
- Allowed lifecycle values: `canonical`, `provenance`, `superseded`, `invalid`, `generated`.

- [ ] **Step 1: Write failing manifest schema tests**

```python
from pathlib import Path

from scripts.harness.experiment_manifest import load_valid_manifest


ROOT = Path(__file__).resolve().parents[2]
MANIFESTS = (
    "experiments/week12/brio_wu_1d/manifest.json",
    "experiments/week12/mhd_2d/brio_wu_2d/manifest.json",
    "experiments/week12/mhd_2d/divb_clean/manifest.json",
    "experiments/week13/hlld_divb_followup/manifest.json",
    "experiments/week13/orszag_tang/manifest.json",
    "experiments/week13/kelvin_helmholtz/manifest.json",
    "experiments/week14/mhd_precision_pilot/manifest.json",
    "experiments/week14/mhd_precision_pilot_hlld/manifest.json",
    "experiments/week15/brio_wu_precision_pilot_p1/manifest.json",
    "experiments/week15/brio_wu_precision_pilot_hlld_p1/manifest.json",
    "experiments/week15/orszag_tang_precision_smoke/manifest.json",
    "experiments/week15/orszag_tang_precision_smoke_hlld/manifest.json",
    "experiments/week15/mhd_temporal_divergence/manifest.json",
)


def test_report2_promoted_manifests_are_valid_and_evidence_exists():
    manifests = [load_valid_manifest(ROOT / path, ROOT) for path in MANIFESTS]
    assert {item["lifecycle"] for item in manifests} >= {
        "canonical", "superseded", "invalid"
    }
```

Add temporary-invalid-manifest tests for unknown lifecycle, missing pipeline stages, missing evidence, `superseded` without replacement, and `invalid` without exclusion reason.

- [ ] **Step 2: Run manifest tests and verify files are absent**

Run: `python -m pytest tests/py/test_experiment_manifests.py -q`

Expected: FAIL on missing module/manifests.

- [ ] **Step 3: Implement standard-library validation**

Required manifest shape:

```json
{
  "schema": {"name": "hrsc.experiment-manifest", "version": 1},
  "id": "report2-week12-brio-wu-1d",
  "report": "report2",
  "lifecycle": "canonical",
  "purpose": "Validate monotonic Brio-Wu 1D MHD convergence.",
  "pipeline": {
    "config": ["tests/cases/brio_wu_1d/brio_wu.cfg"],
    "build": ["scripts/build_all.sh"],
    "run": ["scripts/regression/mhd_brio_wu_1d.py"],
    "measure": ["scripts/regression/mhd_brio_wu_1d.py"],
    "aggregate": ["experiments/week12/brio_wu_1d/summary.json"],
    "plot": ["experiments/week12/brio_wu_1d/figures/brio_wu_convergence.png"]
  },
  "evidence": ["experiments/week12/brio_wu_1d/summary.md"],
  "retention": {
    "keep": ["summary.*", "figures/"],
    "transient": ["generated grids"]
  }
}
```

Before writing each real manifest, verify its actual script/config paths with `rg` and its summary. Use `canonical` for the current bounded Week 12/13/15 authorities, `invalid` for Week 14 HLL (include `exclusion_reason`), and `superseded` for Week 14 HLLD (include `replacement`). OT manifests may list both `headline256_p1` deterministic and `mca_n30` evidence. Do not invent missing generating commits; use `provenance.notes` when Git history is the only authority.

- [ ] **Step 4: Validate all manifests and existing evidence routing**

Run: `python -m pytest tests/py/test_experiment_manifests.py tests/py/test_report2_documentation.py -q`

Expected: PASS.

- [ ] **Step 5: Force-add only the explicitly reviewed manifests and commit**

Because `experiments/` is globally ignored, use exact paths with `git add -f`; do not force-add directories recursively.

```bash
git add scripts/harness/experiment_manifest.py tests/py/test_experiment_manifests.py
git add -f experiments/week12/brio_wu_1d/manifest.json experiments/week12/mhd_2d/brio_wu_2d/manifest.json experiments/week12/mhd_2d/divb_clean/manifest.json experiments/week13/hlld_divb_followup/manifest.json experiments/week13/orszag_tang/manifest.json experiments/week13/kelvin_helmholtz/manifest.json experiments/week14/mhd_precision_pilot/manifest.json experiments/week14/mhd_precision_pilot_hlld/manifest.json experiments/week15/brio_wu_precision_pilot_p1/manifest.json experiments/week15/brio_wu_precision_pilot_hlld_p1/manifest.json experiments/week15/orszag_tang_precision_smoke/manifest.json experiments/week15/orszag_tang_precision_smoke_hlld/manifest.json experiments/week15/mhd_temporal_divergence/manifest.json
git commit -m "docs: add Report 2 experiment lifecycle manifests"
```

### Task 10: Read-Only Cleanup Audit and Documentation Routing

**Files:**
- Create: `scripts/audit_experiments.py`
- Create: `tests/py/test_experiment_cleanup_audit.py`
- Create: `docs/experiment_logs/experiment_cleanup_candidates.md`
- Modify: `docs/experiment_logs/experiments_retention.md`
- Modify: `docs/experiment_logs/report2_evidence_map.md`
- Modify: `docs/HARNESS.md`
- Modify: `docs/INDEX.md`
- Modify: `scripts/README.md`
- Modify: `tests/py/test_report2_documentation.py`

**Interfaces:**
- Produces: `tracked_experiment_paths(repo_root: Path) -> list[Path]`
- Produces: `find_nested_build_roots(paths: Iterable[Path]) -> dict[Path, list[Path]]`
- Produces CLI: `python scripts/audit_experiments.py --format markdown`
- Behavior: reports candidates only; never deletes or moves files.

- [ ] **Step 1: Write failing cleanup-audit tests**

```python
def test_known_week14_nested_builds_are_reported_without_deletion():
    tracked = tracked_experiment_paths(ROOT)
    groups = find_nested_build_roots(tracked)
    expected = {
        Path("experiments/week14/mhd_precision_pilot_hlld/mca/p24/build-vfc-p53"),
        Path("experiments/week14/mhd_precision_pilot_hlld/mca/p53/build-vfc-p53"),
    }
    assert set(groups) == expected
    assert sum(len(files) for files in groups.values()) == 36
    assert all((ROOT / path).exists() for files in groups.values() for path in files)
```

Add a CLI/output test asserting the Markdown includes `reference audit required`, `no deletion performed`, both paths, and total 36.

- [ ] **Step 2: Run audit tests and verify failure**

Run: `python -m pytest tests/py/test_experiment_cleanup_audit.py -q`

Expected: FAIL because the audit module/report do not exist.

- [ ] **Step 3: Implement a deterministic, read-only audit**

Use `git ls-files experiments` to enumerate tracked paths. Identify a build root when any ancestor name starts with `build` and its tracked files include a marker such as `CMakeCache.txt`, `build.ninja`, `.ninja_deps`, or `CMakeFiles`. Normalize output paths to repository-relative POSIX form and sort roots/files before emitting JSON or Markdown.

The CLI supports only `--format json|markdown` and optional `--output`; it has no delete flag. The committed report records audit date, root, tracked file count, reference-audit status, and deferred action.

- [ ] **Step 4: Update documentation responsibilities**

Update `HARNESS.md` with:

- schema-v1 canonical and legacy alias table;
- success/completion gate;
- effective math mode versus stable historical build name;
- CPU/GPU support matrix;
- manifest lifecycle and validation command.

Update retention docs with the five manifest lifecycle values and link the cleanup report. Update `INDEX.md` and `scripts/README.md` to point to `scripts/harness/`, the architecture spec, manifests, and audit entry. Update the Report 2 evidence map to state that lifecycle manifests complement, but do not replace, bounded evidential statuses such as `provisional` and `negative-result`.

Do not rewrite historical weekly commands or experiment summaries.

- [ ] **Step 5: Generate and verify the cleanup report and docs**

Run: `python scripts/audit_experiments.py --format markdown --output docs/experiment_logs/experiment_cleanup_candidates.md`

Run: `python -m pytest tests/py/test_experiment_cleanup_audit.py tests/py/test_report2_documentation.py -q`

Expected: PASS, report lists exactly two roots and 36 tracked files, and every candidate remains present.

- [ ] **Step 6: Commit audit and documentation routing**

```bash
git add scripts/audit_experiments.py tests/py/test_experiment_cleanup_audit.py docs/experiment_logs/experiment_cleanup_candidates.md docs/experiment_logs/experiments_retention.md docs/experiment_logs/report2_evidence_map.md docs/HARNESS.md docs/INDEX.md scripts/README.md tests/py/test_report2_documentation.py
git commit -m "docs: route harness and experiment lifecycle authority"
```

### Task 11: Full Compatibility and Architecture Verification

**Files:**
- Modify only if verification exposes a scoped defect in files already covered by Tasks 1-10.
- Do not update experiment summaries or regenerate report figures.

**Interfaces:**
- Verifies all acceptance criteria from the approved design.

- [ ] **Step 1: Run all Python tests**

Run: `python -m pytest tests/py -q`

Expected: all tests pass; environment-dependent tests may skip only with their existing explicit reasons.

- [ ] **Step 2: Reconfigure and build CPU double and float targets**

Run: `cmake -S . -B build-double -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release`

Run: `cmake --build build-double`

Run: `cmake -S . -B build-float -DFLOAT_PRECISION=float -DCMAKE_BUILD_TYPE=Release`

Run: `cmake --build build-float`

Expected: both builds succeed; each build directory contains `build_semantics.json` with the actual compiler ID/version and no tracked build changes.

- [ ] **Step 3: Run complete CPU C++ suites**

Run: `.\build-double\unit_tests.exe -r compact`

Run: `.\build-float\unit_tests.exe -r compact`

Expected: all CPU tests pass.

- [ ] **Step 4: Run public-path smoke checks**

Run in PowerShell:

```powershell
@{
    experiment = "architecture-smoke"
    output_root = (Join-Path $env:TEMP "hrsc-architecture-smoke")
    runs = @(@{
        name = "sod-double"
        binary = "build-double/hrsc.exe"
        config = "tests/cases/toro_1d/sod.cfg"
        precision = "double"
        build = "cpu-double-O2-ieee-leq"
    })
} | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 (Join-Path $env:TEMP "hrsc-architecture-dry-run.json")
```

Run: `python scripts/run_matrix.py "$env:TEMP\hrsc-architecture-dry-run.json" --dry-run`

Expected: old CLI path succeeds and metadata contains both legacy and canonical fields.

Run: `python -c "import sys; sys.path.insert(0, 'scripts/regression'); import _mhd_harness; print(_mhd_harness.run_case.__name__)"`

Expected: prints `run_case`.

Run an MHD CPU zero-time cfg through `build-double/hrsc_mhd`; expect success status. Run the same cfg with `device=gpu`; expect return code 2, `reason=unsupported_capability`, and no final binary.

- [ ] **Step 5: Run CUDA checks when available**

If a configured CUDA build and supported device are present:

Run: `cmake --build build-cuda-double-strict --target hrsc unit_tests`

Run: `.\build-cuda-double-strict\unit_tests.exe "[gpu]" -r compact`

Expected: all GPU tests pass, including invalid-dt completion behavior. If CUDA is unavailable, record the exact missing toolchain/device reason in the completion report; do not claim GPU verification.

- [ ] **Step 6: Verify docs, manifests, whitespace, and worktree scope**

Run: `python -m pytest tests/py/test_report2_documentation.py tests/py/test_experiment_manifests.py tests/py/test_experiment_cleanup_audit.py -q`

Run: `git diff --check`

Run: `git status --short`

Expected: documentation tests pass, no whitespace errors, no build/grid artifacts staged, and unrelated untracked paths remain untouched.

- [ ] **Step 7: Request final code review before integration**

Use `superpowers:requesting-code-review` against the full implementation range. Address only findings within the approved architecture scope, rerun the affected focused tests, then rerun Steps 1, 3, and 6.

Any verified review fix receives its own commit containing only the concrete files named by that finding. When review finds no issue, create no extra commit.
