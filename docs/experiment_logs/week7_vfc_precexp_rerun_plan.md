# vfc_precexp Per-Function Rerun Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a real per-function / per-call `vfc_precexp` rerun plan and execution path without reclassifying the old whole-program `experiments/verificarlo/precexp/` outputs as per-function evidence.

**Architecture:** Keep the solver and cfg defaults unchanged. Add a small harness layer around Verificarlo: define candidate functions, build an instrumented CSC binary, run `vfc_precexp` with explicit `exrun`/`excmp`, normalize the produced precision assignments into stable CSV/JSON/Markdown, and record logs and limitations. The deliverable follows `config -> build -> run -> measure -> aggregate -> report`; no raw grids are kept unless needed as explicit provenance.

**Tech Stack:** Bash, Python 3.11, Pandas, existing HRSC CMake build, Verificarlo `vfc_precexp`, existing `scripts/run_matrix.py` metadata conventions, pytest.

---

## Scope And Non-Goals

This plan belongs to the Week 7.5 supervisor-response cleanup in `docs/week7.5/week7.5-plan.md`, especially Task 8. It does not run the rerun locally and does not claim the existing artefacts are per-function evidence.

Do not change:

- solver numerics,
- existing cfg defaults,
- existing output formats,
- CUDA kernels or mixed-precision policies.

The only code changes planned here are scripts, tests, and CSC job templates that make the rerun reproducible.

## Current Artefact Boundary

`experiments/verificarlo/precexp/` currently contains:

- `exrun`,
- `excmp`,
- `reference/sod.txt`,
- `prec_*/run_*.txt`.

Those files prove only a coarse whole-program precision sweep with a global density L1 acceptance criterion. They do not contain a function-level or call-site precision assignment table. Report text must describe them as partial historical evidence only.

## Target Output Bundle

Final rerun output should be:

```text
experiments/week7/vfc_precexp/
├── manifest.json
├── function_precision.csv
├── function_precision.json
├── summary.md
├── logs/
│   ├── environment.txt
│   ├── configure_stdout.txt
│   ├── configure_stderr.txt
│   ├── build_stdout.txt
│   ├── build_stderr.txt
│   ├── vfc_precexp_stdout.txt
│   └── vfc_precexp_stderr.txt
└── scripts/
    ├── exrun
    └── excmp
```

`function_precision.csv` schema:

| column | meaning |
|---|---|
| `case` | test case name, e.g. `sod`, `stationary_contact` |
| `solver` | `hllc` or `rusanov` |
| `symbol` | function or call-site symbol reported by `vfc_precexp` |
| `component` | curated group: `muscl`, `hancock`, `flux`, `eos`, `cfl`, `io`, `unknown` |
| `minimum_precision_bits` | smallest accepted precision reported by the rerun |
| `status` | `accepted`, `rejected`, `not_reported`, or `tool_unsupported` |
| `criterion` | short name of acceptance criterion |
| `reference` | path to trusted reference used by `excmp` |
| `notes` | limitation or interpretation note |

## Candidate Function Groups

Track at least these groups:

| component | symbol / source area | reason |
|---|---|---|
| `muscl` | `src/euler/muscl.hpp`, GPU analogues only as future work | Week 3 evidence says reconstruction is a likely FP bottleneck |
| `hancock` | `src/euler/hancock.hpp` | Predictor combines reconstructed states and flux differences |
| `flux` | `src/euler/hllc.hpp`, `src/euler/rusanov.hpp` | Supervisor asked whether flux choice matters; expected not dominant |
| `eos` | `src/core/eos.hpp` | Pressure computation has subtractive cancellation |
| `cfl` | CFL reduction / timestep path | Can affect trajectory if precision changes timestep |

Start with CPU 1D Euler. Keep 2D LW3 as an optional extension after the 1D pipeline is proven.

---

## Task 1: Preserve The Artefact Boundary

**Files:**
- Modify: `docs/experiment_logs/week7_supervisor_requirements_gap_audit.md`
- Modify: `docs/experiment_logs/week7_vfc_precexp_rerun_plan.md`

- [ ] **Step 1: Verify old artefacts are not per-function output**

Run:

```powershell
Get-Content experiments\verificarlo\precexp\exrun
Get-Content experiments\verificarlo\precexp\excmp
Get-ChildItem experiments\verificarlo\precexp -Recurse -File |
  Select-Object FullName,Length |
  Sort-Object FullName |
  Format-Table -AutoSize
rg -n "function|call-site|minimum|symbol|vfc_precexp" experiments\verificarlo\precexp docs scripts -g "!*.bin"
```

Expected:

- `exrun` runs one Sod executable invocation into a directory.
- `excmp` checks a global density L1 relative error threshold.
- No function-level precision assignment table exists.

- [ ] **Step 2: Keep the gap audit language strict**

Ensure `docs/experiment_logs/week7_supervisor_requirements_gap_audit.md` says:

```markdown
| `vfc_precexp` per-function precision analysis | partial only | `experiments/verificarlo/precexp/prec_*` contains whole-program precision-labelled outputs plus `exrun`/`excmp`, not a function or call-site precision table | run the CSC `vfc_precexp` plan in `docs/experiment_logs/week7_vfc_precexp_rerun_plan.md` |
```

- [ ] **Step 3: Commit the documentation-only boundary**

Run:

```powershell
git add docs\experiment_logs\week7_supervisor_requirements_gap_audit.md docs\experiment_logs\week7_vfc_precexp_rerun_plan.md
git commit -m "docs: clarify vfc_precexp rerun boundary"
```

Expected: one documentation commit; no generated data.

---

## Task 2: Add A Manifest Generator

**Files:**
- Create: `scripts/verificarlo/precexp_manifest.py`
- Create: `tests/py/test_precexp_manifest.py`
- Write: `experiments/week7/vfc_precexp/manifest.json`

- [ ] **Step 1: Write the failing manifest test**

Create `tests/py/test_precexp_manifest.py`:

```python
from scripts.verificarlo.precexp_manifest import build_manifest


def test_build_manifest_contains_required_function_groups() -> None:
    manifest = build_manifest(cases=["sod"], solvers=["hllc"])
    groups = {entry["component"] for entry in manifest["candidate_symbols"]}
    assert {"muscl", "hancock", "flux", "eos", "cfl"}.issubset(groups)
    assert manifest["cases"] == ["sod"]
    assert manifest["solvers"] == ["hllc"]
    assert manifest["output_root"] == "experiments/week7/vfc_precexp"
```

- [ ] **Step 2: Run the failing test**

Run:

```powershell
C:\Users\tangy\anaconda3\python.exe -m pytest tests\py\test_precexp_manifest.py -q
```

Expected: fail with `ModuleNotFoundError` because `scripts.verificarlo.precexp_manifest` does not exist.

- [ ] **Step 3: Implement the manifest generator**

Create `scripts/verificarlo/precexp_manifest.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_OUTPUT_ROOT = "experiments/week7/vfc_precexp"

CANDIDATE_SYMBOLS = [
    {
        "component": "muscl",
        "symbol_hint": "reconstruct_* / minmod / limiter path",
        "source": "src/euler/muscl.hpp",
        "reason": "slope reconstruction can amplify cancellation near discontinuities",
    },
    {
        "component": "hancock",
        "symbol_hint": "hancock_* predictor path",
        "source": "src/euler/hancock.hpp",
        "reason": "predictor combines reconstructed states and flux differences",
    },
    {
        "component": "flux",
        "symbol_hint": "hllc_flux / rusanov_flux",
        "source": "src/euler/hllc.hpp; src/euler/rusanov.hpp",
        "reason": "supervisor asked whether flux choice is the FP bottleneck",
    },
    {
        "component": "eos",
        "symbol_hint": "pressure / sound_speed / cons_to_prim",
        "source": "src/core/eos.hpp",
        "reason": "pressure subtracts kinetic energy from total energy",
    },
    {
        "component": "cfl",
        "symbol_hint": "CFL / timestep computation",
        "source": "src/euler/euler_solver.hpp; src/gpu/* future",
        "reason": "precision changes in timestep can alter trajectories",
    },
]


def build_manifest(cases: list[str], solvers: list[str], output_root: str = DEFAULT_OUTPUT_ROOT) -> dict:
    return {
        "experiment": "week7-vfc-precexp",
        "output_root": output_root,
        "cases": cases,
        "solvers": solvers,
        "candidate_symbols": CANDIDATE_SYMBOLS,
        "acceptance_criterion": "density_l1_relative_and_pressure_linf_against_ieee_reference",
        "old_artifact_boundary": "experiments/verificarlo/precexp is whole-program only",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", action="append", default=["sod", "stationary_contact"])
    parser.add_argument("--solver", action="append", default=["hllc", "rusanov"])
    parser.add_argument("--out", type=Path, default=Path(DEFAULT_OUTPUT_ROOT) / "manifest.json")
    args = parser.parse_args()
    manifest = build_manifest(args.case, args.solver)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test and generate manifest**

Run:

```powershell
C:\Users\tangy\anaconda3\python.exe -m pytest tests\py\test_precexp_manifest.py -q
C:\Users\tangy\anaconda3\python.exe scripts\verificarlo\precexp_manifest.py
```

Expected:

- test passes,
- `experiments/week7/vfc_precexp/manifest.json` is written.

- [ ] **Step 5: Commit**

Run:

```powershell
git add scripts\verificarlo\precexp_manifest.py tests\py\test_precexp_manifest.py experiments\week7\vfc_precexp\manifest.json
git commit -m "feat: add vfc_precexp rerun manifest"
```

---

## Task 3: Add CSC `vfc_precexp` Job Template

**Files:**
- Create: `scripts/cluster/slurm/vfc_precexp_rerun.sh`
- Create: `tests/py/test_vfc_precexp_job_template.py`

- [ ] **Step 1: Write a smoke test for the job template**

Create `tests/py/test_vfc_precexp_job_template.py`:

```python
from pathlib import Path


def test_vfc_precexp_job_template_records_logs_and_does_not_edit_cfg() -> None:
    text = Path("scripts/cluster/slurm/vfc_precexp_rerun.sh").read_text(encoding="utf-8")
    assert "set -euo pipefail" in text
    assert "vfc_precexp" in text
    assert "logs/environment.txt" in text
    assert "scripts/exrun" in text
    assert "scripts/excmp" in text
    assert "tests/cases/toro_1d/sod.cfg" in text
    assert "cp " in text or "Copy-Item" not in text
    assert "sed -i" not in text
```

- [ ] **Step 2: Run the failing test**

Run:

```powershell
C:\Users\tangy\anaconda3\python.exe -m pytest tests\py\test_vfc_precexp_job_template.py -q
```

Expected: fail because the template does not exist.

- [ ] **Step 3: Create the CSC job template**

Create `scripts/cluster/slurm/vfc_precexp_rerun.sh`:

```bash
#!/usr/bin/env bash
#SBATCH --job-name=hrsc-vfc-precexp
#SBATCH --output=experiments/week7/vfc_precexp/logs/slurm-%j.out
#SBATCH --error=experiments/week7/vfc_precexp/logs/slurm-%j.err
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G

set -euo pipefail

ROOT="${ROOT:-$(pwd)}"
OUT="${OUT:-${ROOT}/experiments/week7/vfc_precexp}"
LOG="${OUT}/logs"
SCRIPT_DIR="${OUT}/scripts"
BUILD_DIR="${ROOT}/build-vfc-precexp"

mkdir -p "${LOG}" "${SCRIPT_DIR}"

{
  date -u
  hostname
  command -v verificarlo-c++ || true
  command -v vfc_precexp || true
  verificarlo-c++ --version || true
  vfc_precexp --help | head -80 || true
  cmake --version || true
  git rev-parse HEAD || true
} > "${LOG}/environment.txt" 2>&1

cat > "${SCRIPT_DIR}/exrun" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
OUTPUT_DIR="$1"
ROOT="${ROOT:-$(pwd)}"
mkdir -p "${OUTPUT_DIR}"
"${ROOT}/build-vfc-precexp/hrsc" "${OUTPUT_DIR}/config.cfg" > "${OUTPUT_DIR}/stdout.txt" 2> "${OUTPUT_DIR}/stderr.txt"
EOF
chmod +x "${SCRIPT_DIR}/exrun"

cat > "${SCRIPT_DIR}/excmp" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
REF_DIR="$1"
CUR_DIR="$2"
python "${ROOT}/scripts/verificarlo/precexp_compare.py" \
  --reference "${REF_DIR}/grid.bin" \
  --candidate "${CUR_DIR}/grid.bin" \
  --density-l1-rel-max 1.0e-2 \
  --pressure-linf-rel-max 5.0e-2
EOF
chmod +x "${SCRIPT_DIR}/excmp"

cmake -S "${ROOT}" -B "${BUILD_DIR}" \
  -DCMAKE_BUILD_TYPE=Release \
  -DFLOAT_PRECISION=double \
  -DENABLE_OPENMP=OFF \
  -DCMAKE_CXX_COMPILER=verificarlo-c++ \
  > "${LOG}/configure_stdout.txt" \
  2> "${LOG}/configure_stderr.txt"

cmake --build "${BUILD_DIR}" -j1 \
  > "${LOG}/build_stdout.txt" \
  2> "${LOG}/build_stderr.txt"

cp "${ROOT}/tests/cases/toro_1d/sod.cfg" "${OUT}/config.cfg"
python "${ROOT}/scripts/verificarlo/precexp_prepare_cfg.py" \
  --source "${OUT}/config.cfg" \
  --output "${OUT}/reference/config.cfg" \
  --grid "${OUT}/reference/grid.bin"

mkdir -p "${OUT}/reference"
"${BUILD_DIR}/hrsc" "${OUT}/reference/config.cfg" > "${OUT}/reference/stdout.txt" 2> "${OUT}/reference/stderr.txt"

ROOT="${ROOT}" vfc_precexp \
  --exrun "${SCRIPT_DIR}/exrun" \
  --excmp "${SCRIPT_DIR}/excmp" \
  "${OUT}/reference" \
  > "${LOG}/vfc_precexp_stdout.txt" \
  2> "${LOG}/vfc_precexp_stderr.txt"
```

- [ ] **Step 4: Run template test**

Run:

```powershell
C:\Users\tangy\anaconda3\python.exe -m pytest tests\py\test_vfc_precexp_job_template.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

Run:

```powershell
git add scripts\cluster\slurm\vfc_precexp_rerun.sh tests\py\test_vfc_precexp_job_template.py
git commit -m "feat: add vfc_precexp csc job template"
```

---

## Task 4: Add Config Preparation Helper

**Files:**
- Create: `scripts/verificarlo/precexp_prepare_cfg.py`
- Create: `tests/py/test_precexp_prepare_cfg.py`

- [ ] **Step 1: Write failing cfg materialization test**

Create `tests/py/test_precexp_prepare_cfg.py`:

```python
from pathlib import Path

from scripts.verificarlo.precexp_prepare_cfg import materialise_cfg


def test_materialise_cfg_overrides_output_without_editing_source(tmp_path: Path) -> None:
    source = tmp_path / "sod.cfg"
    source.write_text("test = sod\noutput_file = old.bin\n", encoding="utf-8")
    target = tmp_path / "run" / "config.cfg"
    grid = tmp_path / "run" / "grid.bin"

    materialise_cfg(source, target, grid)

    assert source.read_text(encoding="utf-8") == "test = sod\noutput_file = old.bin\n"
    text = target.read_text(encoding="utf-8")
    assert "output_format = binary" in text
    assert f"output_file = {grid}" in text
```

- [ ] **Step 2: Run the failing test**

Run:

```powershell
C:\Users\tangy\anaconda3\python.exe -m pytest tests\py\test_precexp_prepare_cfg.py -q
```

Expected: fail because helper does not exist.

- [ ] **Step 3: Implement cfg helper**

Create `scripts/verificarlo/precexp_prepare_cfg.py`:

```python
from __future__ import annotations

import argparse
from pathlib import Path


def replace_or_append_cfg_line(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or "=" not in line:
            out.append(line)
            continue
        lhs = line.split("=", 1)[0].strip()
        if lhs == key:
            out.append(f"{key} = {value}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"{key} = {value}")
    return "\n".join(out) + "\n"


def materialise_cfg(source: Path, target: Path, grid: Path) -> None:
    text = source.read_text(encoding="utf-8")
    text = replace_or_append_cfg_line(text, "output_format", "binary")
    text = replace_or_append_cfg_line(text, "output_file", str(grid))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--grid", type=Path, required=True)
    args = parser.parse_args()
    materialise_cfg(args.source, args.output, args.grid)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test**

Run:

```powershell
C:\Users\tangy\anaconda3\python.exe -m pytest tests\py\test_precexp_prepare_cfg.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

Run:

```powershell
git add scripts\verificarlo\precexp_prepare_cfg.py tests\py\test_precexp_prepare_cfg.py
git commit -m "feat: add vfc_precexp cfg materializer"
```

---

## Task 5: Add Reference-Aware Comparator

**Files:**
- Create: `scripts/verificarlo/precexp_compare.py`
- Create: `tests/py/test_precexp_compare.py`
- Read: `scripts/io_helper.py`

- [ ] **Step 1: Write failing comparator test**

Create `tests/py/test_precexp_compare.py`:

```python
import numpy as np

from scripts.verificarlo.precexp_compare import compare_primitive_arrays


def test_compare_primitive_arrays_accepts_small_density_and_pressure_errors() -> None:
    ref = np.array([[[1.0, 0.0, 0.0, 1.0], [0.5, 0.0, 0.0, 0.5]]])
    cand = ref.copy()
    cand[..., 0] *= 1.001
    cand[..., 3] *= 0.999

    result = compare_primitive_arrays(
        ref,
        cand,
        density_l1_rel_max=1.0e-2,
        pressure_linf_rel_max=5.0e-2,
    )

    assert result["accepted"] is True
    assert result["density_l1_rel"] < 1.0e-2
    assert result["pressure_linf_rel"] < 5.0e-2
```

- [ ] **Step 2: Run the failing test**

Run:

```powershell
C:\Users\tangy\anaconda3\python.exe -m pytest tests\py\test_precexp_compare.py -q
```

Expected: fail because comparator does not exist.

- [ ] **Step 3: Implement comparator**

Create `scripts/verificarlo/precexp_compare.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts.io_helper import cons_to_prim, read_binary


def _relative_l1(ref: np.ndarray, cand: np.ndarray) -> float:
    denom = float(np.sum(np.abs(ref)))
    if denom == 0.0:
        return float("inf")
    return float(np.sum(np.abs(cand - ref)) / denom)


def _relative_linf(ref: np.ndarray, cand: np.ndarray) -> float:
    denom = float(np.max(np.abs(ref)))
    if denom == 0.0:
        return float("inf")
    return float(np.max(np.abs(cand - ref)) / denom)


def compare_primitive_arrays(
    ref: np.ndarray,
    cand: np.ndarray,
    density_l1_rel_max: float,
    pressure_linf_rel_max: float,
) -> dict:
    if ref.shape != cand.shape:
        return {"accepted": False, "reason": f"shape mismatch {ref.shape} vs {cand.shape}"}
    density_l1_rel = _relative_l1(ref[..., 0], cand[..., 0])
    pressure_linf_rel = _relative_linf(ref[..., 3], cand[..., 3])
    accepted = (
        density_l1_rel <= density_l1_rel_max
        and pressure_linf_rel <= pressure_linf_rel_max
    )
    return {
        "accepted": accepted,
        "density_l1_rel": density_l1_rel,
        "pressure_linf_rel": pressure_linf_rel,
        "criterion": "density_l1_relative_and_pressure_linf_relative",
    }


def compare_binary(reference: Path, candidate: Path, gamma: float, density_l1_rel_max: float, pressure_linf_rel_max: float) -> dict:
    _, ref_cons = read_binary(reference)
    _, cand_cons = read_binary(candidate)
    ref = cons_to_prim(ref_cons.astype(np.float64), gamma)
    cand = cons_to_prim(cand_cons.astype(np.float64), gamma)
    return compare_primitive_arrays(ref, cand, density_l1_rel_max, pressure_linf_rel_max)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--gamma", type=float, default=1.4)
    parser.add_argument("--density-l1-rel-max", type=float, required=True)
    parser.add_argument("--pressure-linf-rel-max", type=float, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    result = compare_binary(
        args.reference,
        args.candidate,
        args.gamma,
        args.density_l1_rel_max,
        args.pressure_linf_rel_max,
    )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if result["accepted"] else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run comparator tests**

Run:

```powershell
C:\Users\tangy\anaconda3\python.exe -m pytest tests\py\test_precexp_compare.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

Run:

```powershell
git add scripts\verificarlo\precexp_compare.py tests\py\test_precexp_compare.py
git commit -m "feat: add vfc_precexp reference comparator"
```

---

## Task 6: Add Aggregator For `vfc_precexp` Output

**Files:**
- Create: `scripts/verificarlo/precexp_aggregate.py`
- Create: `tests/py/test_precexp_aggregate.py`
- Write: `experiments/week7/vfc_precexp/function_precision.csv`
- Write: `experiments/week7/vfc_precexp/function_precision.json`
- Write: `experiments/week7/vfc_precexp/summary.md`

- [ ] **Step 1: Write failing parser/aggregator test**

Create `tests/py/test_precexp_aggregate.py`:

```python
from pathlib import Path

from scripts.verificarlo.precexp_aggregate import classify_component, parse_precision_rows


def test_classify_component_maps_known_symbols() -> None:
    assert classify_component("hrsc::hllc_flux<double>") == "flux"
    assert classify_component("hrsc::pressure<double>") == "eos"
    assert classify_component("hrsc::minmod<double>") == "muscl"


def test_parse_precision_rows_accepts_csv_like_output(tmp_path: Path) -> None:
    raw = tmp_path / "vfc_precexp_stdout.txt"
    raw.write_text(
        "symbol,minimum_precision_bits,status\n"
        "hrsc::hllc_flux<double>,24,accepted\n"
        "hrsc::pressure<double>,40,accepted\n",
        encoding="utf-8",
    )

    rows = parse_precision_rows(raw, case="sod", solver="hllc", reference="reference/grid.bin")

    assert rows[0]["component"] == "flux"
    assert rows[0]["minimum_precision_bits"] == 24
    assert rows[1]["component"] == "eos"
```

- [ ] **Step 2: Run the failing test**

Run:

```powershell
C:\Users\tangy\anaconda3\python.exe -m pytest tests\py\test_precexp_aggregate.py -q
```

Expected: fail because aggregator does not exist.

- [ ] **Step 3: Implement aggregator**

Create `scripts/verificarlo/precexp_aggregate.py`:

```python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import pandas as pd


COMPONENT_HINTS = {
    "muscl": ["muscl", "minmod", "limiter", "reconstruct"],
    "hancock": ["hancock", "predict"],
    "flux": ["hllc", "rusanov", "flux"],
    "eos": ["pressure", "sound_speed", "cons_to_prim", "eos"],
    "cfl": ["cfl", "timestep", "max_wave"],
}


def classify_component(symbol: str) -> str:
    lower = symbol.lower()
    for component, hints in COMPONENT_HINTS.items():
        if any(hint in lower for hint in hints):
            return component
    return "unknown"


def parse_precision_rows(path: Path, case: str, solver: str, reference: str) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return [{
            "case": case,
            "solver": solver,
            "symbol": "",
            "component": "unknown",
            "minimum_precision_bits": "",
            "status": "tool_unsupported",
            "criterion": "density_l1_relative_and_pressure_linf_relative",
            "reference": reference,
            "notes": "vfc_precexp stdout was empty",
        }]

    rows: list[dict] = []
    try:
        reader = csv.DictReader(lines)
        for raw in reader:
            symbol = raw.get("symbol") or raw.get("function") or raw.get("callsite") or ""
            bits_raw = raw.get("minimum_precision_bits") or raw.get("precision") or ""
            rows.append({
                "case": case,
                "solver": solver,
                "symbol": symbol,
                "component": classify_component(symbol),
                "minimum_precision_bits": int(bits_raw) if str(bits_raw).isdigit() else "",
                "status": raw.get("status", "accepted"),
                "criterion": "density_l1_relative_and_pressure_linf_relative",
                "reference": reference,
                "notes": "",
            })
    except csv.Error:
        rows = []

    if not rows:
        rows.append({
            "case": case,
            "solver": solver,
            "symbol": "",
            "component": "unknown",
            "minimum_precision_bits": "",
            "status": "not_reported",
            "criterion": "density_l1_relative_and_pressure_linf_relative",
            "reference": reference,
            "notes": "Could not parse vfc_precexp output; inspect logs manually",
        })
    return rows


def write_outputs(rows: list[dict], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "function_precision.csv", index=False)
    (out_dir / "function_precision.json").write_text(
        json.dumps(rows, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# vfc_precexp Function Precision Summary",
        "",
        "This summary reports only rows parsed from the new CSC rerun logs.",
        "",
        "| component | rows | min bits | max bits |",
        "|---|---:|---:|---:|",
    ]
    for component, group in df.groupby("component"):
        bits = pd.to_numeric(group["minimum_precision_bits"], errors="coerce").dropna()
        min_bits = "" if bits.empty else int(bits.min())
        max_bits = "" if bits.empty else int(bits.max())
        lines.append(f"| {component} | {len(group)} | {min_bits} | {max_bits} |")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stdout", type=Path, default=Path("experiments/week7/vfc_precexp/logs/vfc_precexp_stdout.txt"))
    parser.add_argument("--case", default="sod")
    parser.add_argument("--solver", default="hllc")
    parser.add_argument("--reference", default="experiments/week7/vfc_precexp/reference/grid.bin")
    parser.add_argument("--out-dir", type=Path, default=Path("experiments/week7/vfc_precexp"))
    args = parser.parse_args()
    rows = parse_precision_rows(args.stdout, args.case, args.solver, args.reference)
    write_outputs(rows, args.out_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run aggregator tests**

Run:

```powershell
C:\Users\tangy\anaconda3\python.exe -m pytest tests\py\test_precexp_aggregate.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

Run:

```powershell
git add scripts\verificarlo\precexp_aggregate.py tests\py\test_precexp_aggregate.py
git commit -m "feat: add vfc_precexp aggregation"
```

---

## Task 7: Execute On CSC

**Files:**
- Read: `scripts/cluster/slurm/vfc_precexp_rerun.sh`
- Write: `experiments/week7/vfc_precexp/logs/*`
- Write: `experiments/week7/vfc_precexp/function_precision.*`
- Write: `experiments/week7/vfc_precexp/summary.md`

- [ ] **Step 1: Upload or pull current branch on CSC**

Run on CSC:

```bash
git status --short --branch
git rev-parse HEAD
```

Expected: current branch contains the manifest, comparator, cfg helper, job template, and aggregator.

- [ ] **Step 2: Submit the rerun job**

Run on CSC:

```bash
sbatch scripts/cluster/slurm/vfc_precexp_rerun.sh
```

Expected: SLURM job id is printed.

- [ ] **Step 3: Inspect job logs**

Run on CSC after job completion:

```bash
tail -100 experiments/week7/vfc_precexp/logs/slurm-*.out
tail -100 experiments/week7/vfc_precexp/logs/slurm-*.err
cat experiments/week7/vfc_precexp/logs/environment.txt
```

Expected:

- Verificarlo commands are recorded.
- Build succeeds.
- `vfc_precexp_stdout.txt` and `vfc_precexp_stderr.txt` exist.

- [ ] **Step 4: Aggregate the rerun**

Run on CSC:

```bash
python scripts/verificarlo/precexp_aggregate.py \
  --stdout experiments/week7/vfc_precexp/logs/vfc_precexp_stdout.txt \
  --case sod \
  --solver hllc \
  --reference experiments/week7/vfc_precexp/reference/grid.bin \
  --out-dir experiments/week7/vfc_precexp
```

Expected:

- `function_precision.csv` exists,
- `function_precision.json` exists,
- `summary.md` exists.

- [ ] **Step 5: Copy back summary artefacts only**

Copy back:

```text
experiments/week7/vfc_precexp/manifest.json
experiments/week7/vfc_precexp/function_precision.csv
experiments/week7/vfc_precexp/function_precision.json
experiments/week7/vfc_precexp/summary.md
experiments/week7/vfc_precexp/logs/environment.txt
experiments/week7/vfc_precexp/logs/vfc_precexp_stdout.txt
experiments/week7/vfc_precexp/logs/vfc_precexp_stderr.txt
```

Do not copy raw grid files unless needed to debug a failed comparator.

---

## Task 8: Report Integration And Evidence Update

**Files:**
- Modify: `docs/experiment_logs/week7_supervisor_requirements_gap_audit.md`
- Modify: `docs/experiment_logs/week7_verificarlo_refresh.md`
- Modify: `docs/experiment_logs/report1_evidence_index.md`
- Read: `experiments/week7/vfc_precexp/summary.md`

- [ ] **Step 1: If CSC rerun produced parseable rows, update gap audit**

Use this wording only if `function_precision.csv` has function/call-site rows:

```markdown
| `vfc_precexp` per-function precision analysis | rerun completed | `experiments/week7/vfc_precexp/function_precision.csv`; `experiments/week7/vfc_precexp/summary.md` | cite as preliminary per-function evidence with CSC/tooling limitations |
```

- [ ] **Step 2: If CSC tooling did not produce function rows, keep status partial**

Use this wording if logs are empty, unparseable, or whole-program only:

```markdown
| `vfc_precexp` per-function precision analysis | blocked by tool output | `experiments/week7/vfc_precexp/logs/vfc_precexp_stdout.txt`; `experiments/week7/vfc_precexp/logs/vfc_precexp_stderr.txt` | report as attempted rerun; do not cite as completed per-function evidence |
```

- [ ] **Step 3: Add evidence index row**

Add to `docs/experiment_logs/report1_evidence_index.md`:

```markdown
| Cross-cutting: Verificarlo per-function precision exploration | `vfc_precexp` rerun attempt | `docs/experiment_logs/week7_vfc_precexp_rerun_plan.md`; `experiments/week7/vfc_precexp/summary.md`; `experiments/week7/vfc_precexp/function_precision.csv` | preliminary / cite only if function rows exist | Verificarlo refresh |
```

- [ ] **Step 4: Commit summary artefacts**

Run:

```powershell
git add docs\experiment_logs\week7_supervisor_requirements_gap_audit.md docs\experiment_logs\week7_verificarlo_refresh.md docs\experiment_logs\report1_evidence_index.md
git add -f experiments\week7\vfc_precexp\manifest.json experiments\week7\vfc_precexp\function_precision.csv experiments\week7\vfc_precexp\function_precision.json experiments\week7\vfc_precexp\summary.md experiments\week7\vfc_precexp\logs\environment.txt experiments\week7\vfc_precexp\logs\vfc_precexp_stdout.txt experiments\week7\vfc_precexp\logs\vfc_precexp_stderr.txt
git commit -m "docs: record vfc_precexp rerun evidence"
```

Expected: summary/log artefacts committed; no raw grids.

---

## Task 9: Verification Gate

**Files:**
- Test: `tests/py/test_precexp_manifest.py`
- Test: `tests/py/test_vfc_precexp_job_template.py`
- Test: `tests/py/test_precexp_prepare_cfg.py`
- Test: `tests/py/test_precexp_compare.py`
- Test: `tests/py/test_precexp_aggregate.py`

- [ ] **Step 1: Run all targeted tests**

Run:

```powershell
C:\Users\tangy\anaconda3\python.exe -m pytest `
  tests\py\test_precexp_manifest.py `
  tests\py\test_vfc_precexp_job_template.py `
  tests\py\test_precexp_prepare_cfg.py `
  tests\py\test_precexp_compare.py `
  tests\py\test_precexp_aggregate.py `
  -q
```

Expected: all tests pass.

- [ ] **Step 2: Verify no solver or cfg defaults changed**

Run:

```powershell
git diff -- src tests\cases cmake CMakeLists.txt
```

Expected: no diff, unless a later explicitly approved task changes scripts only outside solver/cfg defaults.

- [ ] **Step 3: Verify no raw grids are staged**

Run:

```powershell
git diff --cached --name-only | rg "grid\.bin|reference\.bin|build-"
```

Expected: no matches.

- [ ] **Step 4: Verify report wording does not overclaim**

Run:

```powershell
rg -n "completed per-function|function-level.*complete|per-call.*complete" docs\experiment_logs docs\week7.5
```

Expected: matches only if `function_precision.csv` has parseable function/call-site rows and the wording points to those rows.

---

## Execution Notes

- Treat `vfc_precexp` as a CSC rerun. Local Windows execution is only for script tests and documentation.
- Keep `experiments/verificarlo/precexp/` labelled as historical whole-program sweep.
- `sod` is the first case because the old `exrun`/`excmp` already used it. Add `stationary_contact` only after the Sod pipeline is proven.
- Use HLLC first. Rusanov can be added after parser and comparator are proven.
- If `vfc_precexp` cannot emit function or call-site assignments in the installed CSC version, record `tool_unsupported` and stop. Do not invent function-level evidence from whole-program precision rows.
- Do not commit build directories, raw `grid.bin` files, or large transient Verificarlo working trees.
