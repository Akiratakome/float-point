# Week 14 — HLL MHD Precision-Study Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the harness for an HLL MHD floating-point precision-study pilot on Brio-Wu 1D — a deterministic build-axis fan plus a Verificarlo MCA sampling strand — that emits one unified, claim-bucketed `summary.{csv,json,md}`.

**Architecture:** Pure-numeric metric helpers (MHD primitive fields, field norms, MCA spread) are unit-tested in isolation; two harness drivers wire them to execution. The deterministic driver generates a `matrix.json` manifest and executes each variant through the existing Week-13 MHD runner `_mhd_harness.run_case` (records wall-time + `[mhd]` divB/steps), computes same-grid field deltas vs the `cpu-double-O2-ieee-leq` reference row, folds in the MCA aggregate, evaluates phase gates, and writes the unified summary. The MCA sampler inherits the Week-13 smoke's runner-probe + `blocked_environment` discipline.

**Tech Stack:** Python 3.11 (project env `floatpoint`), numpy, matplotlib (Agg), pytest; C++ solver `hrsc_mhd` built via CMake/Ninja; Verificarlo via Docker (optional, degrades to `blocked_environment`).

## Global Constraints

- Preserve pipeline shape `config → build → run → measure → aggregate → plot`; every run logs generated cfg + stdout/stderr + metadata + summary. (HARNESS.md)
- Do **not** change solver numerics, existing cfg defaults, or existing output formats. (overall.md MHD fallback discipline; spec §1)
- Week 14 = **Brio-Wu 1D, HLL, CPU only**. OT/KH 2D, 512², GPU MHD, HLLD, Lyapunov are out of scope. (spec §1)
- HLLD stays diagnostic/deferred; HLL is the production solver. (Week 13 decision)
- Binary grids are transient — deleted after norms unless `--keep-grids`; never commit grids or build dirs. (spec §6, §9)
- `.gitignore` ignores the whole `experiments/` tree (plus `*.bin`/`*.csv`/`build-matrix/`), so committing any Week-14 evidence requires `git add -f`; a plain `git status`/`git add` silently skips it. (verified against `.gitignore` lines 4, 21-25)
- `summary.json` is authoritative (nested gates/MCA/claims); `summary.csv` is a flattened convenience view; `matrix_summary_report.py` is reused only for generic checks, never authoritative. (spec §6)
- Diagnostic fields: gate core `rho, By, p`; `vx` computed/reported as a non-gating continuity field. (spec §5)
- MCA `blocked_environment` is a valid, non-failing outcome; fail only if the schema cannot represent it. (spec §6)
- Brio-Wu anchor (double reference): `steps=759`, `divB_max≈4.441e-14`. (spec §2)
- Reference row label: `cpu-double-O2-ieee-leq`. (spec §2)
- Python invocation on this workstation: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe"` (has pytest). (docs/INDEX.md §4)

**Spec deviation (approved-at-handoff):** `matrix.json` is generated as the run manifest, but execution uses `_mhd_harness.run_case`, not `run_matrix.py`, because `hrsc_mhd` emits no `[timing]` line and `run_matrix.py` captures neither MHD wall-time nor the `[mhd]` divB/steps diagnostic.

**Phase scaling (no new code):** P0 (pilot), P1 (deterministic breadth), P2 (MCA depth) differ only by CLI flags on the same two drivers — `--phase`, variant filter, and `--samples`. Only P0 is exercised to green in this plan; P1/P2 are invocations (Task 9).

---

### Task 1: Additive `filter=` kwarg on `build_matrix.generate_variants()`

**Files:**
- Modify: `scripts/build_matrix.py:37-53`
- Test: `tests/py/test_build_matrix_filter.py`

**Interfaces:**
- Consumes: existing `BuildVariant` dataclass (`.name`, `.precision`, `.opt_level`, `.fast_math`, `.strict_riemann`).
- Produces: `generate_variants(..., filter: Callable[[BuildVariant], bool] | None = None) -> list[BuildVariant]` — default output byte-identical to today (24 variants); `filter` selects only from the already-defined variant space.

- [ ] **Step 1: Write the failing test**

```python
# tests/py/test_build_matrix_filter.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.build_matrix import BuildVariant, generate_variants


def test_default_output_unchanged():
    variants = generate_variants()
    assert len(variants) == 24
    names = [v.name for v in variants]
    assert names == sorted(set(names), key=names.index)  # order-stable, no dups
    assert "cpu-double-O2-ieee-leq" in names
    assert "cpu-float-Ofast-fastmath-strict" in names


def _p0(v: BuildVariant) -> bool:
    return v.opt_level in ("O2", "Ofast") and v.fast_math is False


def test_filter_selects_exactly_p0_eight():
    variants = generate_variants(filter=_p0)
    names = sorted(v.name for v in variants)
    assert names == sorted([
        "cpu-double-O2-ieee-leq", "cpu-double-O2-ieee-strict",
        "cpu-double-Ofast-ieee-leq", "cpu-double-Ofast-ieee-strict",
        "cpu-float-O2-ieee-leq", "cpu-float-O2-ieee-strict",
        "cpu-float-Ofast-ieee-leq", "cpu-float-Ofast-ieee-strict",
    ])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_build_matrix_filter.py -v`
Expected: FAIL — `generate_variants() got an unexpected keyword argument 'filter'`.

- [ ] **Step 3: Add the optional filter kwarg**

```python
# scripts/build_matrix.py — replace generate_variants signature + return
from typing import Callable, Optional  # add near top imports


def generate_variants(
    precisions: tuple[str, ...] = ("double", "float"),
    opt_levels: tuple[str, ...] = ("O2", "O3", "Ofast"),
    fast_math_values: tuple[bool, ...] = (False, True),
    strict_values: tuple[bool, ...] = (False, True),
    filter: Optional[Callable[["BuildVariant"], bool]] = None,
) -> list[BuildVariant]:
    variants = [
        BuildVariant(
            precision=precision,
            opt_level=opt_level,
            fast_math=fast_math,
            strict_riemann=strict,
        )
        for precision, opt_level, fast_math, strict in product(
            precisions, opt_levels, fast_math_values, strict_values
        )
    ]
    if filter is not None:
        variants = [v for v in variants if filter(v)]
    return variants
```

- [ ] **Step 4: Run test to verify it passes**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_build_matrix_filter.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Confirm `build_all.sh` still sees identical variants**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -c "from scripts.build_matrix import generate_variants; print(len(generate_variants()))"`
Expected: `24`.

- [ ] **Step 6: Commit**

```bash
git add scripts/build_matrix.py tests/py/test_build_matrix_filter.py
git commit -m "feat(harness): optional filter kwarg on build_matrix.generate_variants"
```

---

### Task 2: MHD primitive fields + same-grid field norms

**Files:**
- Create: `scripts/metrics/mhd_fields.py`
- Test: `tests/py/test_mhd_fields.py`

**Interfaces:**
- Consumes: numpy arrays shaped `(ny, nx, 9)` in conserved MHD order `RHO,MX,MY,MZ,BX,BY,BZ,E,PSI`.
- Produces:
  - `mhd_primitive_fields(arr, gamma) -> dict[str, np.ndarray]` keys `{"rho","vx","By","p"}`.
  - `FIELD_NAMES = ("rho", "vx", "By", "p")`, `GATE_FIELDS = ("rho", "By", "p")`.
  - `field_norms(candidate, reference, gamma, dx) -> dict[str, float]` keys `L1_<f>/L2_<f>/Linf_<f>` for each `FIELD_NAMES`.

- [ ] **Step 1: Write the failing test**

```python
# tests/py/test_mhd_fields.py
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "metrics"))

from mhd_fields import mhd_primitive_fields, field_norms, FIELD_NAMES, GATE_FIELDS


def _cell(rho, vx, By, p, gamma):
    # Build one conserved cell with vy=vz=0, Bx=Bz=0 so p reduces cleanly.
    E = p / (gamma - 1.0) + 0.5 * rho * vx * vx + 0.5 * By * By
    return [rho, rho * vx, 0.0, 0.0, 0.0, By, 0.0, E, 0.0]


def test_primitive_fields_roundtrip():
    gamma = 5.0 / 3.0
    arr = np.array([[_cell(2.0, 0.5, 0.3, 1.5, gamma)]], dtype=np.float64)  # (1,1,9)
    prim = mhd_primitive_fields(arr, gamma)
    assert np.isclose(prim["rho"][0, 0], 2.0)
    assert np.isclose(prim["vx"][0, 0], 0.5)
    assert np.isclose(prim["By"][0, 0], 0.3)
    assert np.isclose(prim["p"][0, 0], 1.5)


def test_field_norms_zero_on_identical():
    gamma = 5.0 / 3.0
    arr = np.array([[_cell(1.0, 0.2, 0.1, 1.0, gamma)],
                    [_cell(1.3, 0.0, 0.2, 0.7, gamma)]], dtype=np.float64)  # (2,1,9)
    norms = field_norms(arr, arr, gamma, dx=0.5)
    for f in FIELD_NAMES:
        assert norms[f"L1_{f}"] == 0.0
        assert norms[f"Linf_{f}"] == 0.0
    assert set(GATE_FIELDS) == {"rho", "By", "p"}


def test_field_norms_scale_with_dx():
    gamma = 5.0 / 3.0
    a = np.array([[_cell(1.0, 0.0, 0.0, 1.0, gamma)]], dtype=np.float64)
    b = np.array([[_cell(1.5, 0.0, 0.0, 1.0, gamma)]], dtype=np.float64)
    norms = field_norms(a, b, gamma, dx=0.25)
    assert np.isclose(norms["L1_rho"], 0.5 * 0.25)
    assert np.isclose(norms["Linf_rho"], 0.5)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_fields.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mhd_fields'`.

- [ ] **Step 3: Implement the module**

```python
# scripts/metrics/mhd_fields.py
"""MHD primitive-field extraction and same-grid field norms for the Week-14
precision pilot. Conserved order mirrors src/mhd/mhd_state.hpp:
RHO,MX,MY,MZ,BX,BY,BZ,E,PSI. Pressure uses the ideal-MHD relation
p = (gamma-1) * (E - 0.5*rho*v^2 - 0.5*B^2); GLM psi does not enter pressure.
"""
from __future__ import annotations

import numpy as np

RHO, MX, MY, MZ, BX, BY, BZ, E, PSI = range(9)

FIELD_NAMES = ("rho", "vx", "By", "p")   # vx is a non-gating continuity field
GATE_FIELDS = ("rho", "By", "p")


def mhd_primitive_fields(arr: np.ndarray, gamma: float) -> dict[str, np.ndarray]:
    if arr.shape[-1] != 9:
        raise ValueError(f"expected MHD nvars=9 on last axis, got {arr.shape}")
    rho = arr[..., RHO]
    inv_rho = 1.0 / rho
    vx = arr[..., MX] * inv_rho
    By = arr[..., BY]
    v2 = (arr[..., MX] ** 2 + arr[..., MY] ** 2 + arr[..., MZ] ** 2) * inv_rho * inv_rho
    b2 = arr[..., BX] ** 2 + arr[..., BY] ** 2 + arr[..., BZ] ** 2
    p = (gamma - 1.0) * (arr[..., E] - 0.5 * rho * v2 - 0.5 * b2)
    return {"rho": rho, "vx": vx, "By": By, "p": p}


def field_norms(candidate: np.ndarray, reference: np.ndarray, gamma: float,
                dx: float) -> dict[str, float]:
    if candidate.shape != reference.shape:
        raise ValueError(f"shape mismatch {candidate.shape} vs {reference.shape}")
    cf = mhd_primitive_fields(candidate, gamma)
    rf = mhd_primitive_fields(reference, gamma)
    out: dict[str, float] = {}
    for name in FIELD_NAMES:
        diff = np.abs(cf[name] - rf[name]).ravel()
        out[f"L1_{name}"] = float(diff.sum() * dx)
        out[f"L2_{name}"] = float(np.sqrt((diff ** 2).sum() * dx))
        out[f"Linf_{name}"] = float(diff.max())
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_fields.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add scripts/metrics/mhd_fields.py tests/py/test_mhd_fields.py
git commit -m "feat(metrics): MHD primitive fields + same-grid field norms"
```

---

### Task 3: MCA field-specific spread + SNR aggregation

**Files:**
- Modify: `scripts/metrics/mhd_fields.py` (append `mca_field_spread`)
- Test: `tests/py/test_mhd_fields.py` (append)

**Interfaces:**
- Consumes: `snr_metric.compute_sigma_fp_field(samples)` (per-cell std over samples, ddof=1); `mhd_primitive_fields`.
- Produces: `mca_field_spread(samples, gamma) -> dict[str, float]` keys `spread_rho/By/p/vx`, `snr_rho/By/p`, `rho_mean_spread`. `samples` shape `(n, ny, nx, 9)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/py/test_mhd_fields.py  (append)
from mhd_fields import mca_field_spread


def test_mca_field_spread_zero_when_identical():
    gamma = 5.0 / 3.0
    one = np.array([[_cell(1.0, 0.2, 0.1, 1.0, gamma)]], dtype=np.float64)  # (1,1,9)
    samples = np.stack([one, one, one], axis=0)  # (3,1,1,9)
    out = mca_field_spread(samples, gamma)
    assert out["spread_rho"] == 0.0
    assert out["spread_By"] == 0.0
    assert out["rho_mean_spread"] == 0.0
    assert "snr_p" in out


def test_mca_field_spread_detects_rho_variation():
    gamma = 5.0 / 3.0
    s0 = np.array([[_cell(1.0, 0.0, 0.1, 1.0, gamma)]], dtype=np.float64)
    s1 = np.array([[_cell(1.2, 0.0, 0.1, 1.0, gamma)]], dtype=np.float64)
    samples = np.stack([s0, s1], axis=0)
    out = mca_field_spread(samples, gamma)
    assert out["spread_rho"] > 0.0
    assert np.isclose(out["rho_mean_spread"], 0.2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_fields.py -k mca -v`
Expected: FAIL — `cannot import name 'mca_field_spread'`.

- [ ] **Step 3: Implement `mca_field_spread`**

```python
# scripts/metrics/mhd_fields.py  (append; add imports at top)
import sys as _sys
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from snr_metric import compute_sigma_fp_field  # noqa: E402

_SQRT_EPS = float(np.sqrt(np.finfo(np.float64).eps))


def mca_field_spread(samples: np.ndarray, gamma: float) -> dict[str, float]:
    """Field-specific FP spread + a simple global SNR across MCA samples.

    samples: (n, ny, nx, 9). spread_<f> = max per-cell std; snr_<f> =
    mean(|field|) / mean(per-cell std), floored to avoid div-by-zero.
    """
    if samples.ndim != 4 or samples.shape[-1] != 9:
        raise ValueError(f"expected (n, ny, nx, 9), got {samples.shape}")
    n = samples.shape[0]
    out: dict[str, float] = {}
    for name in FIELD_NAMES:
        stacked = np.stack(
            [mhd_primitive_fields(samples[k], gamma)[name] for k in range(n)], axis=0)
        sigma = compute_sigma_fp_field(stacked)          # (ny, nx)
        out[f"spread_{name}"] = float(np.abs(sigma).max())
        if name in GATE_FIELDS:
            mean_abs = float(np.abs(stacked.mean(axis=0)).mean())
            sigma_mean = float(np.abs(sigma).mean()) or _SQRT_EPS
            out[f"snr_{name}"] = mean_abs / sigma_mean
    rho_means = np.stack(
        [mhd_primitive_fields(samples[k], gamma)["rho"] for k in range(n)], axis=0
    ).reshape(n, -1).mean(axis=1)
    out["rho_mean_spread"] = float(rho_means.max() - rho_means.min())
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_fields.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add scripts/metrics/mhd_fields.py tests/py/test_mhd_fields.py
git commit -m "feat(metrics): MHD MCA field-specific spread + SNR aggregation"
```

---

### Task 4: Pure aggregation core — gates, ordering flags, unified summary

**Files:**
- Create: `scripts/regression/mhd_precision_pilot_core.py`
- Test: `tests/py/test_mhd_precision_pilot_summary.py`

**Interfaces:**
- Consumes: deterministic `rows` (list of dicts with `variant, precision, opt, fastmath, riemann, finite, rc, steps, divB_max, walltime_s`, plus `L*_<field>` from Task 2, and `is_reference`); `mca` dict `{ "p53": {...}, "p24": {...} }` each a full MCA block (see `blocked_mca_block`).
- Produces:
  - `REFERENCE = "cpu-double-O2-ieee-leq"`, `ANCHOR_STEPS = 759`, `ANCHOR_DIVB_MAX = 4.441e-14`.
  - `MCA_FIELD_KEYS`, `blocked_mca_block(status, reason) -> dict` (shared null-field MCA block; also used by Task 6).
  - `schema_valid(rows, mca) -> bool` (required-key validation feeding G0).
  - `gate_g0(rows, mca) -> dict`, `ordering_flags(rows) -> list[dict]`, `gate_g1(rows) -> dict`, `gate_g2(mca) -> dict`.
  - `assemble_summary(rows, mca, git_commit) -> dict` (the authoritative `summary.json` payload with `gates` G0/G1/G2 and `claims`).

- [ ] **Step 1: Write the failing test**

```python
# tests/py/test_mhd_precision_pilot_summary.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "regression"))

from mhd_precision_pilot_core import (
    REFERENCE, ANCHOR_STEPS, ANCHOR_DIVB_MAX,
    gate_g0, gate_g1, gate_g2, ordering_flags, assemble_summary,
    blocked_mca_block, schema_valid,
)


def _row(variant, precision, opt, fastmath, riemann, *, steps, divb, linf_rho,
         finite=True, is_ref=False):
    return {
        "variant": variant, "precision": precision, "opt": opt,
        "fastmath": fastmath, "riemann": riemann, "finite": finite, "rc": 0,
        "steps": steps, "divB_max": divb, "walltime_s": 0.01,
        "is_reference": is_ref,
        "L1_rho": 0.0 if is_ref else 0.01, "L2_rho": 0.0 if is_ref else 0.02,
        "Linf_rho": 0.0 if is_ref else linf_rho,
        "L1_By": 0.0, "L2_By": 0.0, "Linf_By": 0.0,
        "L1_p": 0.0, "L2_p": 0.0, "Linf_p": 0.0,
        "L1_vx": 0.0, "L2_vx": 0.0, "Linf_vx": 0.0,
    }


def _reference_row():
    return _row(REFERENCE, "double", "O2", False, "leq",
                steps=ANCHOR_STEPS, divb=ANCHOR_DIVB_MAX, linf_rho=0.0, is_ref=True)


def _blocked_mca():
    return {"p53": blocked_mca_block("blocked_environment", "no runner"),
            "p24": blocked_mca_block("blocked_environment", "no runner")}


def test_g0_passes_on_anchor_and_finite_and_blocked_mca():
    rows = [_reference_row()]
    g0 = gate_g0(rows, _blocked_mca())
    assert g0["pass"] is True
    assert g0["anchor_reproduced"] is True
    assert g0["mca_representable"] is True
    assert g0["schema_valid"] is True


def test_schema_valid_rejects_missing_row_key():
    rows = [_reference_row()]
    bad = dict(rows[0]); bad.pop("Linf_By")
    assert schema_valid([bad], _blocked_mca()) is False
    assert gate_g0([bad], _blocked_mca())["pass"] is False


def test_g0_fails_when_reference_anchor_wrong():
    rows = [_row(REFERENCE, "double", "O2", False, "leq",
                 steps=700, divb=ANCHOR_DIVB_MAX, linf_rho=0.0, is_ref=True)]
    assert gate_g0(rows, _blocked_mca())["pass"] is False


def test_g2_pending_before_depth_then_evaluated():
    assert gate_g2(_blocked_mca())["status"] == "pending_depth"
    completed = {"p53": {"status": "completed", "n": 30, "spread_rho": 1e-16,
                         "spread_By": 1e-16, "spread_p": 1e-16},
                 "p24": {"status": "completed", "n": 30, "spread_rho": 1e-7,
                         "spread_By": 1e-7, "spread_p": 1e-7}}
    g2 = gate_g2(completed)
    assert g2["status"] == "evaluated"
    assert g2["p24_float_scale"] is True


def test_ordering_flags_detects_fastmath_inversion():
    rows = [
        _reference_row(),
        _row("cpu-float-O3-ieee-leq", "float", "O3", False, "leq", steps=760, divb=1e-6, linf_rho=0.5),
        _row("cpu-float-O3-fastmath-leq", "float", "O3", True, "leq", steps=760, divb=1e-6, linf_rho=0.2),
    ]
    flags = ordering_flags(rows)
    assert len(flags) == 1
    assert flags[0]["axis"] == "fastmath"


def test_assemble_summary_shape_and_claims():
    rows = [_reference_row()]
    summary = assemble_summary(rows, _blocked_mca(), git_commit="deadbeef")
    assert summary["reference"] == REFERENCE
    assert summary["case"] == "brio_wu_1d" and summary["solver"] == "hll"
    assert summary["gates"]["G0"]["pass"] is True
    assert summary["gates"]["G2"]["status"] == "pending_depth"
    assert set(summary["claims"]) == {"morphology", "self_reference", "precision_noise"}
    assert summary["mca"]["p53"]["status"] == "blocked_environment"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_precision_pilot_summary.py -v`
Expected: FAIL — `No module named 'mhd_precision_pilot_core'`.

- [ ] **Step 3: Implement the pure core**

```python
# scripts/regression/mhd_precision_pilot_core.py
"""Pure aggregation core for the Week-14 MHD precision pilot: phase gates,
soft ordering flags, and the authoritative summary.json payload. No I/O or
subprocess here so it is fully unit-testable."""
from __future__ import annotations

from typing import Any

REFERENCE = "cpu-double-O2-ieee-leq"
ANCHOR_STEPS = 759
ANCHOR_DIVB_MAX = 4.441e-14
ANCHOR_DIVB_ABS_TOL = 1e-13

# Field keys every MCA block must carry (null when blocked) so the schema is
# stable across P0/P1/P2 and blocked_environment renders cleanly.
MCA_FIELD_KEYS = ("spread_rho", "spread_By", "spread_p", "spread_vx",
                  "snr_rho", "snr_By", "snr_p", "rho_mean_spread")

_REQUIRED_ROW_KEYS = ("variant", "finite", "steps", "divB_max",
                      "Linf_rho", "Linf_By", "Linf_p")
_REQUIRED_MCA_KEYS = ("status", "n", "spread_rho", "spread_By", "spread_p")

CLAIMS = {
    "morphology": (
        "Brio-Wu wave structure vs Brio & Wu 1988 — established Week 12, "
        "referenced only."),
    "self_reference": (
        "Deterministic deltas are precision/compiler/implementation deltas vs "
        "the cpu-double-O2-ieee-leq baseline (engineering consistency), NOT a "
        "point-wise match to an exact solution."),
    "precision_noise": (
        "MCA noise floor + SNR = significant-digits-actually-delivered evidence."),
}


def _reference_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    for r in rows:
        if r.get("variant") == REFERENCE:
            return r
    return None


def _anchor_ok(ref: dict[str, Any] | None) -> bool:
    if ref is None:
        return False
    steps_ok = ref.get("steps") == ANCHOR_STEPS
    divb = ref.get("divB_max")
    divb_ok = isinstance(divb, (int, float)) and abs(divb - ANCHOR_DIVB_MAX) <= ANCHOR_DIVB_ABS_TOL
    return bool(steps_ok and divb_ok)


def blocked_mca_block(status: str, reason: str) -> dict[str, Any]:
    """A schema-complete MCA block with null field metrics (shared by the
    sampler and the --skip-mca path). `status` is typically
    'blocked_environment' or 'blocked_run'."""
    block: dict[str, Any] = {"status": status, "reason": reason, "n": 0,
                             "mca_evidence_generated": False}
    block.update({k: None for k in MCA_FIELD_KEYS})
    return block


def schema_valid(rows: list[dict[str, Any]], mca: dict[str, Any]) -> bool:
    """Real end-to-end schema check: deterministic rows and MCA blocks carry the
    required keys (values may be null for blocked MCA)."""
    if not rows:
        return False
    if any(not all(k in r for k in _REQUIRED_ROW_KEYS) for r in rows):
        return False
    for block in mca.values():
        if not isinstance(block, dict):
            return False
        if not all(k in block for k in _REQUIRED_MCA_KEYS):
            return False
    return True


def gate_g0(rows: list[dict[str, Any]], mca: dict[str, Any]) -> dict[str, Any]:
    all_finite = all(bool(r.get("finite")) for r in rows) and len(rows) > 0
    anchor = _anchor_ok(_reference_row(rows))
    mca_representable = all(isinstance(v, dict) and "status" in v for v in mca.values())
    valid = schema_valid(rows, mca)
    return {
        "pass": bool(all_finite and anchor and mca_representable and valid),
        "all_finite": bool(all_finite),
        "anchor_reproduced": bool(anchor),
        "schema_valid": bool(valid),
        "mca_representable": bool(mca_representable),
    }


def ordering_flags(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Soft, non-blocking: flag any fastmath run whose Linf_rho is BELOW its
    ieee twin (same precision/opt/riemann). FP can be non-monotone; hold such
    orderings back from report claims until reviewed."""
    by_key: dict[tuple, dict[bool, dict]] = {}
    for r in rows:
        if r.get("variant") == REFERENCE:
            continue
        key = (r.get("precision"), r.get("opt"), r.get("riemann"))
        by_key.setdefault(key, {})[bool(r.get("fastmath"))] = r
    flags: list[dict[str, Any]] = []
    for (prec, opt, riem), pair in by_key.items():
        if True in pair and False in pair:
            fm = float(pair[True]["Linf_rho"])
            ie = float(pair[False]["Linf_rho"])
            if fm < ie:
                flags.append({
                    "axis": "fastmath",
                    "variants": [pair[False]["variant"], pair[True]["variant"]],
                    "metric": "Linf_rho",
                    "note": (f"fastmath Linf_rho {fm:.3e} < ieee {ie:.3e} "
                             f"(expected >=); review before claiming."),
                })
    return flags


def gate_g1(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "all_finite": all(bool(r.get("finite")) for r in rows) and len(rows) > 0,
        "anchor_ok": _anchor_ok(_reference_row(rows)),
        "ordering_flags": ordering_flags(rows),
    }


def gate_g2(mca: dict[str, Any]) -> dict[str, Any]:
    """MCA-depth sanity. Reports a status even before P2 depth runs; it is a
    soft/sanity gate, never blocking here."""
    def _completed(p: str) -> bool:
        return isinstance(mca.get(p), dict) and mca[p].get("status") == "completed"

    p53 = mca.get("p53", {}) if isinstance(mca.get("p53"), dict) else {}
    p24 = mca.get("p24", {}) if isinstance(mca.get("p24"), dict) else {}
    any_completed = _completed("p53") or _completed("p24")
    return {
        "status": "evaluated" if any_completed else "pending_depth",
        "p53_status": p53.get("status"),
        "p24_status": p24.get("status"),
        "p53_near_eps": bool(_completed("p53") and float(p53.get("spread_rho") or 1.0) < 1e-12),
        "p24_float_scale": bool(_completed("p24")),
    }


def assemble_summary(rows: list[dict[str, Any]], mca: dict[str, Any],
                     git_commit: str) -> dict[str, Any]:
    return {
        "experiment": "week14-mhd-precision-pilot",
        "case": "brio_wu_1d",
        "solver": "hll",
        "reference": REFERENCE,
        "git_commit": git_commit,
        "deterministic": rows,
        "mca": mca,
        "gates": {
            "G0": gate_g0(rows, mca),
            "G1": gate_g1(rows),
            "G2": gate_g2(mca),
        },
        "claims": CLAIMS,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_precision_pilot_summary.py -v`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
git add scripts/regression/mhd_precision_pilot_core.py tests/py/test_mhd_precision_pilot_summary.py
git commit -m "feat(regression): pure gate/ordering/summary core for MHD precision pilot"
```

---

### Task 5: Summary serialisation (csv/json/md) + pilot figures

**Files:**
- Modify: `scripts/regression/mhd_precision_pilot_core.py` (append `write_summaries`)
- Create: `scripts/figures/mhd_precision_pilot_plots.py`
- Test: `tests/py/test_mhd_precision_pilot_summary.py` (append serialisation test)

**Interfaces:**
- Consumes: the `assemble_summary` payload.
- Produces:
  - `write_summaries(summary, out_dir) -> None` writing `summary.json` (authoritative), `summary.csv` (flattened deterministic rows), `summary.md`.
  - `plot_precision_variant_norms(summary, path) -> None`, `plot_mca_noise_floor(summary, path) -> None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/py/test_mhd_precision_pilot_summary.py  (append)
import json


def test_write_summaries_emits_three_files(tmp_path):
    from mhd_precision_pilot_core import assemble_summary, write_summaries, REFERENCE, ANCHOR_STEPS, ANCHOR_DIVB_MAX
    rows = [{
        "variant": REFERENCE, "precision": "double", "opt": "O2",
        "fastmath": False, "riemann": "leq", "finite": True, "rc": 0,
        "steps": ANCHOR_STEPS, "divB_max": ANCHOR_DIVB_MAX, "walltime_s": 0.01,
        "is_reference": True,
        "L1_rho": 0.0, "L2_rho": 0.0, "Linf_rho": 0.0,
        "L1_By": 0.0, "L2_By": 0.0, "Linf_By": 0.0,
        "L1_p": 0.0, "L2_p": 0.0, "Linf_p": 0.0,
        "L1_vx": 0.0, "L2_vx": 0.0, "Linf_vx": 0.0,
    }]
    mca = {"p53": {"status": "blocked_environment", "n": 0},
           "p24": {"status": "blocked_environment", "n": 0}}
    summary = assemble_summary(rows, mca, git_commit="deadbeef")
    write_summaries(summary, tmp_path)
    loaded = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert loaded["gates"]["G0"]["pass"] is True
    assert (tmp_path / "summary.csv").read_text(encoding="utf-8").splitlines()[0].startswith("variant,")
    assert "Claim buckets" in (tmp_path / "summary.md").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_precision_pilot_summary.py -k write_summaries -v`
Expected: FAIL — `cannot import name 'write_summaries'`.

- [ ] **Step 3: Implement `write_summaries`**

```python
# scripts/regression/mhd_precision_pilot_core.py  (append)
import csv
import json
from pathlib import Path

_CSV_FIELDS = [
    "variant", "precision", "opt", "fastmath", "riemann", "is_reference",
    "finite", "rc", "steps", "divB_max", "walltime_s",
    "L1_rho", "L2_rho", "Linf_rho", "L1_By", "L2_By", "Linf_By",
    "L1_p", "L2_p", "Linf_p", "L1_vx", "L2_vx", "Linf_vx",
]


def write_summaries(summary: dict[str, Any], out_dir: Path) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    with (out_dir / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in summary["deterministic"]:
            writer.writerow(row)

    g0 = summary["gates"]["G0"]
    lines = [
        "# Week 14 MHD Precision Pilot (Brio-Wu 1D, HLL)",
        "",
        f"Reference row: `{summary['reference']}`. `summary.json` is authoritative.",
        "",
        f"G0 pass: **{g0['pass']}** (anchor_reproduced={g0['anchor_reproduced']}, "
        f"all_finite={g0['all_finite']}, mca_representable={g0['mca_representable']})",
        "",
        "## Deterministic variants",
        "",
        "| variant | Linf_rho | Linf_By | Linf_p | divB_max | steps | wall s |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in summary["deterministic"]:
        lines.append(
            f"| {r['variant']} | {r['Linf_rho']:.3e} | {r['Linf_By']:.3e} | "
            f"{r['Linf_p']:.3e} | {r['divB_max']:.3e} | {r.get('steps','')} | "
            f"{r.get('walltime_s', float('nan')):.3f} |")
    lines += ["", "## MCA (Verificarlo)", "",
              "| virtual p | status | n | spread_rho | spread_By | spread_p |",
              "|---|---|---:|---:|---:|---:|"]
    for p, m in summary["mca"].items():
        lines.append(
            f"| {p} | {m.get('status')} | {m.get('n','')} | "
            f"{m.get('spread_rho','')} | {m.get('spread_By','')} | {m.get('spread_p','')} |")
    flags = summary["gates"]["G1"]["ordering_flags"]
    lines += ["", "## Ordering flags (soft, non-blocking)", ""]
    lines += [f"- {fl['note']} ({'/'.join(fl['variants'])})" for fl in flags] or ["- none"]
    lines += ["", "## Claim buckets", ""]
    lines += [f"- **{k}**: {v}" for k, v in summary["claims"].items()]
    lines.append("")
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")
```

- [ ] **Step 4: Run serialisation test to verify it passes**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_precision_pilot_summary.py -v`
Expected: PASS (7 passed).

- [ ] **Step 5: Write the plotting figure test**

```python
# tests/py/test_mhd_precision_pilot_plots.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "figures"))
sys.path.insert(0, str(ROOT / "scripts" / "regression"))

from mhd_precision_pilot_plots import plot_precision_variant_norms, plot_mca_noise_floor
from mhd_precision_pilot_core import assemble_summary, REFERENCE, ANCHOR_STEPS, ANCHOR_DIVB_MAX


def _summary():
    rows = [{
        "variant": REFERENCE, "precision": "double", "opt": "O2", "fastmath": False,
        "riemann": "leq", "finite": True, "rc": 0, "steps": ANCHOR_STEPS,
        "divB_max": ANCHOR_DIVB_MAX, "walltime_s": 0.01, "is_reference": True,
        "L1_rho": 0.0, "L2_rho": 0.0, "Linf_rho": 0.0, "L1_By": 0.0, "L2_By": 0.0,
        "Linf_By": 0.0, "L1_p": 0.0, "L2_p": 0.0, "Linf_p": 0.0,
        "L1_vx": 0.0, "L2_vx": 0.0, "Linf_vx": 0.0,
    }, {
        "variant": "cpu-float-O2-ieee-leq", "precision": "float", "opt": "O2",
        "fastmath": False, "riemann": "leq", "finite": True, "rc": 0, "steps": 760,
        "divB_max": 1e-6, "walltime_s": 0.01, "is_reference": False,
        "L1_rho": 0.01, "L2_rho": 0.02, "Linf_rho": 0.05, "L1_By": 0.0, "L2_By": 0.0,
        "Linf_By": 0.01, "L1_p": 0.0, "L2_p": 0.0, "Linf_p": 0.02,
        "L1_vx": 0.0, "L2_vx": 0.0, "Linf_vx": 0.0,
    }]
    mca = {"p53": {"status": "completed", "n": 8, "spread_rho": 1e-16, "spread_By": 1e-16, "spread_p": 1e-16},
           "p24": {"status": "completed", "n": 8, "spread_rho": 1e-7, "spread_By": 1e-7, "spread_p": 1e-7}}
    return assemble_summary(rows, mca, git_commit="deadbeef")


def test_plots_write_nonempty_png(tmp_path):
    a = tmp_path / "norms.png"
    b = tmp_path / "mca.png"
    plot_precision_variant_norms(_summary(), a)
    plot_mca_noise_floor(_summary(), b)
    assert a.stat().st_size > 0
    assert b.stat().st_size > 0
```

- [ ] **Step 6: Implement the plotters**

```python
# scripts/figures/mhd_precision_pilot_plots.py
"""Week-14 MHD precision-pilot figures. Agg backend so it runs headless."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def plot_precision_variant_norms(summary: dict[str, Any], path: Path) -> None:
    rows = [r for r in summary["deterministic"] if not r.get("is_reference")]
    labels = [r["variant"].replace("cpu-", "") for r in rows]
    fig, ax = plt.subplots(figsize=(max(6, len(rows) * 0.9), 4))
    ax.bar(range(len(rows)), [r["Linf_rho"] for r in rows], color="#3366aa")
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Linf(rho) vs " + summary["reference"])
    ax.set_title("Week 14 Brio-Wu 1D — deterministic precision deltas")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_mca_noise_floor(summary: dict[str, Any], path: Path) -> None:
    mca = summary["mca"]
    ps = list(mca.keys())
    fields = ("spread_rho", "spread_By", "spread_p")
    fig, ax = plt.subplots(figsize=(6, 4))
    width = 0.25
    for i, fld in enumerate(fields):
        vals = [float(mca[p].get(fld) or 0.0) for p in ps]
        ax.bar([x + i * width for x in range(len(ps))], vals, width, label=fld)
    ax.set_yscale("symlog", linthresh=1e-17)
    ax.set_xticks([x + width for x in range(len(ps))])
    ax.set_xticklabels(ps)
    ax.set_ylabel("per-cell max spread")
    ax.set_title("Week 14 Brio-Wu 1D — MCA noise floor (p53 vs p24)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
```

- [ ] **Step 7: Run the plot test to verify it passes**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_precision_pilot_plots.py -v`
Expected: PASS (1 passed).

- [ ] **Step 8: Commit**

```bash
git add scripts/regression/mhd_precision_pilot_core.py scripts/figures/mhd_precision_pilot_plots.py tests/py/test_mhd_precision_pilot_summary.py tests/py/test_mhd_precision_pilot_plots.py
git commit -m "feat(regression): summary serialisation + pilot figures for MHD precision pilot"
```

---

### Task 6: MCA sampler `mhd_precision_sampling.py` (field-specific, blocked-safe)

**Files:**
- Create: `scripts/verificarlo/mhd_precision_sampling.py`
- Test: `tests/py/test_mhd_precision_sampling.py`

**Interfaces:**
- Consumes: `mhd_verificarlo_smoke` reusable pieces (`probe_runners`, `choose_runner`, `run_samples`, `base_environment`, `write_json`); `mhd_fields.mca_field_spread`; `io_helper.stack_samples`; `mhd_precision_pilot_core.blocked_mca_block`. Overrides `smoke.EXPERIMENT` so evidence is labelled `week14-mhd-mca`, not `week13-…`.
- Produces: `sample_precision(out_dir, precision, samples, image) -> dict` returning a schema-complete MCA block with `status` in `{completed, blocked_environment, blocked_run}` and, when `completed`, `spread_*`/`snr_*`/`rho_mean_spread`/`n`. `main()` writes `mca/p53/` and `mca/p24/` plus a top-level `mca/summary.json`.

- [ ] **Step 1: Write the failing test (blocked-environment path, no Docker needed)**

```python
# tests/py/test_mhd_precision_sampling.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "verificarlo"))

import mhd_precision_sampling as sampler


def test_blocked_environment_is_valid_outcome(tmp_path, monkeypatch):
    # Force "no runner discoverable" so we exercise the blocked-safe path.
    monkeypatch.setattr(sampler, "choose_runner", lambda probes: None)
    monkeypatch.setattr(sampler, "probe_runners", lambda image: [])
    block = sampler.sample_precision(tmp_path / "p53", precision=53, samples=8,
                                     image="verificarlo/verificarlo")
    assert block["status"] == "blocked_environment"
    assert block["n"] == 0
    assert block["mca_evidence_generated"] is False
    # schema must still carry the field keys as null so the aggregator can render them
    assert "spread_rho" in block and block["spread_rho"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_precision_sampling.py -v`
Expected: FAIL — `No module named 'mhd_precision_sampling'`.

- [ ] **Step 3: Implement the sampler (reusing the smoke's machinery)**

```python
# scripts/verificarlo/mhd_precision_sampling.py
"""Week-14 N-sample MHD Verificarlo MCA sampler (p53 noise floor + p24 float
surrogate) with field-specific spread/SNR. Reuses the Week-13 smoke's
runner-probe + sample-running machinery and inherits its status vocabulary
(completed / blocked_environment / blocked_run). p24 is a virtual-precision
surrogate on the double build (VFC_MCA_PRECISION_BINARY64), not a float build."""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from types import SimpleNamespace

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "verificarlo"))
sys.path.insert(0, str(ROOT / "scripts" / "regression"))
sys.path.insert(0, str(ROOT / "scripts" / "metrics"))
sys.path.insert(0, str(ROOT / "scripts"))

import mhd_verificarlo_smoke as smoke  # noqa: E402  (module handle to override EXPERIMENT)
from mhd_verificarlo_smoke import (  # noqa: E402
    probe_runners, choose_runner, run_samples, base_environment, write_json,
    DEFAULT_CASE, DEFAULT_IMAGE,
)
from mhd_fields import mca_field_spread  # noqa: E402
from io_helper import stack_samples  # noqa: E402
from mhd_precision_pilot_core import blocked_mca_block  # noqa: E402

WEEK14_MCA_EXPERIMENT = "week14-mhd-mca"


def sample_precision(out_dir: pathlib.Path, precision: int, samples: int,
                     image: str, gamma: float = 5.0 / 3.0) -> dict:
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    probes = probe_runners(image)
    runner = choose_runner(probes)
    if runner is None:
        return blocked_mca_block(
            "blocked_environment",
            "No supported native/WSL/Docker Verificarlo runner found.")
    args = SimpleNamespace(case=DEFAULT_CASE, out=out_dir, samples=samples,
                           precision=precision, image=image, probe_only=False)
    # The smoke's run_samples/base_environment stamp metadata with its module
    # EXPERIMENT constant. Override it only for this call (restore in finally)
    # so Week-14 evidence is labelled week14-mhd-mca without polluting the module.
    prev_experiment = smoke.EXPERIMENT
    smoke.EXPERIMENT = WEEK14_MCA_EXPERIMENT
    try:
        status, sample_rows, reason = run_samples(args, probes, runner)
        environment = {**base_environment(args, probes, runner), "status": status}
    finally:
        smoke.EXPERIMENT = prev_experiment
    write_json(out_dir / "environment.json", environment)
    if status != "completed":
        return blocked_mca_block("blocked_run", reason)
    _, samples_arr, _ = stack_samples(out_dir / "runs")
    block = {"status": "completed", "reason": reason, "n": len(sample_rows),
             "runner": runner, "mca_evidence_generated": True}
    block.update(mca_field_spread(samples_arr, gamma))
    return block


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path,
                        default=ROOT / "experiments" / "week14" / "mhd_precision_pilot" / "mca")
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    args = parser.parse_args(argv)
    out = args.out if args.out.is_absolute() else ROOT / args.out
    blocks = {f"p{p}": sample_precision(out / f"p{p}", p, args.samples, args.image)
              for p in (53, 24)}
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "summary.json", {"experiment": "week14-mhd-mca", "mca": blocks})
    print(json.dumps({k: v["status"] for k, v in blocks.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_precision_sampling.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add scripts/verificarlo/mhd_precision_sampling.py tests/py/test_mhd_precision_sampling.py
git commit -m "feat(verificarlo): N-sample MHD MCA sampler with field-specific spread"
```

---

### Task 7: Deterministic driver `mhd_precision_pilot.py` (build → run → measure → aggregate → plot)

**Files:**
- Create: `scripts/regression/mhd_precision_pilot.py`
- Test: `tests/py/test_mhd_precision_pilot_driver.py`

**Interfaces:**
- Consumes: `build_matrix.generate_variants(filter=...)`, `_mhd_harness.run_case`/`resolve_binary`/`git_commit`/`sha256_file`/`parse_mhd_diagnostics`, `io_helper.read_binary`, `mhd_fields.field_norms`, `mhd_precision_pilot_core.*`, `mhd_precision_pilot_plots.*`.
- Produces:
  - `p0_filter(v) -> bool` (the 8-variant selector) and `build_variant(variant) -> Path`.
  - `write_matrix_json(variants, out_dir) -> Path`.
  - `measure_run(variant, arr, ref_arr, gamma, dx, diagnostics, walltime_s) -> dict` (one deterministic row).
  - `main(argv) -> int`.

- [ ] **Step 1: Write the failing test (pure `measure_run` row assembly + matrix.json)**

```python
# tests/py/test_mhd_precision_pilot_driver.py
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "regression"))
sys.path.insert(0, str(ROOT))

from scripts.build_matrix import BuildVariant
import mhd_precision_pilot as drv


def _cell(rho, vx, By, p, gamma):
    E = p / (gamma - 1.0) + 0.5 * rho * vx * vx + 0.5 * By * By
    return [rho, rho * vx, 0.0, 0.0, 0.0, By, 0.0, E, 0.0]


def test_p0_filter_picks_eight():
    from scripts.build_matrix import generate_variants
    assert len(generate_variants(filter=drv.p0_filter)) == 8


def test_measure_run_reference_is_zero_delta():
    gamma = 5.0 / 3.0
    ref = np.array([[_cell(1.0, 0.1, 0.2, 1.0, gamma)]], dtype=np.float64)
    v = BuildVariant("double", "O2", False, False)
    row = drv.measure_run(v, ref, ref, gamma, dx=0.5,
                          diagnostics={"steps": 759, "divB_max": 4.441e-14},
                          walltime_s=0.02)
    assert row["variant"] == "cpu-double-O2-ieee-leq"
    assert row["is_reference"] is True
    assert row["Linf_rho"] == 0.0
    assert row["steps"] == 759 and row["finite"] is True


def test_write_matrix_json(tmp_path):
    from scripts.build_matrix import generate_variants
    variants = generate_variants(filter=drv.p0_filter)
    path = drv.write_matrix_json(variants, tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["experiment"] == "week14-mhd-precision-pilot"
    assert len(data["runs"]) == 8
    assert all(r["config"].endswith("brio_wu.cfg") for r in data["runs"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_precision_pilot_driver.py -v`
Expected: FAIL — `No module named 'mhd_precision_pilot'`.

- [ ] **Step 3: Implement the driver**

```python
# scripts/regression/mhd_precision_pilot.py
"""Week-14 HLL MHD precision-study pilot driver (Brio-Wu 1D, CPU).

Flow: build selected variants -> generate matrix.json manifest -> run each via
_mhd_harness.run_case (wall-time + [mhd] divB/steps) -> same-grid field deltas
vs cpu-double-O2-ieee-leq -> fold MCA aggregate -> gates + summary + figures.
Grids are deleted after norms unless --keep-grids."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "metrics"))
sys.path.insert(0, str(ROOT / "scripts" / "regression"))
sys.path.insert(0, str(ROOT / "scripts" / "figures"))
sys.path.insert(0, str(ROOT / "scripts" / "verificarlo"))  # for the dynamic MCA sampler import in main()

from scripts.build_matrix import BuildVariant, generate_variants  # noqa: E402
from io_helper import read_binary  # noqa: E402
from mhd_fields import field_norms  # noqa: E402
from _mhd_harness import (  # noqa: E402
    run_case, resolve_binary, git_commit, sha256_file, parse_mhd_diagnostics,
    replace_or_append_cfg,
)
import mhd_precision_pilot_core as core  # noqa: E402
from mhd_precision_pilot_plots import plot_precision_variant_norms, plot_mca_noise_floor  # noqa: E402

BASE_CFG = ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg"
OUT = ROOT / "experiments" / "week14" / "mhd_precision_pilot"
GAMMA = 5.0 / 3.0
EXPERIMENT = "week14-mhd-precision-pilot"


def p0_filter(v: BuildVariant) -> bool:
    return v.opt_level in ("O2", "Ofast") and v.fast_math is False


def build_variant(variant: BuildVariant) -> Path:
    build_dir = ROOT / variant.build_dir
    binary = build_dir / "hrsc_mhd"
    # Configure only when the build dir is fresh; always (re)build the target so
    # a stale binary from an earlier run is never silently reused. cmake --build
    # is incremental, so this is cheap when already up to date.
    if not (build_dir / "CMakeCache.txt").is_file():
        subprocess.run(["cmake", "-B", str(build_dir), "-G", "Ninja",
                        "-DCMAKE_BUILD_TYPE=Release", *variant.cmake_args()],
                       cwd=str(ROOT), check=True)
    subprocess.run(["cmake", "--build", str(build_dir), "--target", "hrsc_mhd"],
                   cwd=str(ROOT), check=True)
    return resolve_binary(binary)


def write_matrix_json(variants: list[BuildVariant], out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    runs = [{
        "name": v.name,
        "binary": str((ROOT / v.build_dir / "hrsc_mhd")),
        "config": str(BASE_CFG),
        "precision": v.precision,
        "build": v.name,
        "output_file": "grid.bin",
    } for v in variants]
    path = out_dir / "matrix.json"
    path.write_text(json.dumps(
        {"experiment": EXPERIMENT, "output_root": str(out_dir), "runs": runs},
        indent=2) + "\n", encoding="utf-8")
    return path


def measure_run(variant: BuildVariant, arr: np.ndarray, ref_arr: np.ndarray,
                gamma: float, dx: float, diagnostics: dict, walltime_s: float) -> dict:
    finite = bool(np.all(np.isfinite(arr)))
    row = {
        "variant": variant.name, "precision": variant.precision,
        "opt": variant.opt_level,
        "fastmath": bool(variant.fast_math),
        "riemann": "strict" if variant.strict_riemann else "leq",
        "is_reference": variant.name == core.REFERENCE,
        "finite": finite, "rc": 0,
        "steps": diagnostics.get("steps"),
        "divB_max": diagnostics.get("divB_max"),
        "walltime_s": walltime_s,
    }
    row.update(field_norms(arr, ref_arr, gamma, dx))
    return row


def _run_and_read(variant: BuildVariant, bin_path: Path, commit: str) -> tuple[np.ndarray, dict, float]:
    run_dir = OUT / "runs" / variant.name
    grid = run_dir / "grid.bin"
    cfg_text = replace_or_append_cfg(BASE_CFG.read_text(encoding="utf-8"),
                                     "output_format", "binary")
    cfg_text = replace_or_append_cfg(cfg_text, "output_file", str(grid))
    t0 = time.perf_counter()
    _, meta, stderr_text = run_case(
        variant.name, cfg_text, run_dir, bin_path, BASE_CFG, commit,
        sha256_file(bin_path), output_bin=str(grid), experiment=EXPERIMENT)
    walltime = time.perf_counter() - t0
    header, arr = read_binary(grid)
    return arr.astype(np.float64), {**parse_mhd_diagnostics(stderr_text),
                                    "dx": header.dx, "meta_wall": meta["elapsed_wall_s"]}, walltime


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["p0", "p1"], default="p0")
    parser.add_argument("--keep-grids", action="store_true")
    parser.add_argument("--skip-mca", action="store_true")
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--mca-summary", type=Path, default=None,
                        help="Fold an existing mca/summary.json instead of sampling")
    args = parser.parse_args(argv)

    OUT.mkdir(parents=True, exist_ok=True)
    variants = generate_variants(filter=p0_filter) if args.phase == "p0" else generate_variants()
    commit = git_commit()

    # Build + run the reference first; keep its grid array in memory for deltas.
    ref_variant = next(v for v in variants if v.name == core.REFERENCE)
    ref_bin = build_variant(ref_variant)
    ref_arr, ref_diag, ref_wall = _run_and_read(ref_variant, ref_bin, commit)
    dx = float(ref_diag["dx"])

    rows: list[dict] = []
    for v in variants:
        bin_path = ref_bin if v.name == ref_variant.name else build_variant(v)
        arr, diag, wall = (ref_arr, ref_diag, ref_wall) if v.name == ref_variant.name \
            else _run_and_read(v, bin_path, commit)
        rows.append(measure_run(v, arr, ref_arr, GAMMA, dx, diag, wall))

    # Transient-grid discipline: after all norms are computed, delete every grid
    # (including the reference) unless --keep-grids is set.
    if not args.keep_grids:
        for v in variants:
            grid = OUT / "runs" / v.name / "grid.bin"
            if grid.is_file():
                grid.unlink()

    write_matrix_json(variants, OUT)

    if args.mca_summary is not None:
        mca = json.loads(Path(args.mca_summary).read_text(encoding="utf-8"))["mca"]
    elif args.skip_mca:
        mca = {"p53": core.blocked_mca_block("blocked_environment", "MCA skipped via --skip-mca"),
               "p24": core.blocked_mca_block("blocked_environment", "MCA skipped via --skip-mca")}
    else:
        import mhd_precision_sampling as sampler
        mca = {f"p{p}": sampler.sample_precision(OUT / "mca" / f"p{p}", p, args.samples,
                                                 sampler.DEFAULT_IMAGE) for p in (53, 24)}

    summary = core.assemble_summary(rows, mca, commit)
    core.write_summaries(summary, OUT)
    (OUT / "figures").mkdir(parents=True, exist_ok=True)
    plot_precision_variant_norms(summary, OUT / "figures" / "precision_variant_norms.png")
    plot_mca_noise_floor(summary, OUT / "figures" / "mca_noise_floor.png")

    print((OUT / "summary.md").read_text(encoding="utf-8"))
    if not summary["gates"]["G0"]["pass"]:
        raise SystemExit("G0 failed: reference anchor / finiteness / MCA schema not satisfied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the driver unit test to verify it passes**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_precision_pilot_driver.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add scripts/regression/mhd_precision_pilot.py tests/py/test_mhd_precision_pilot_driver.py
git commit -m "feat(regression): Week-14 MHD precision-pilot deterministic driver"
```

---

### Task 8: Confirm ignore coverage, experiment README, and harness registration

**Files:**
- Create: `experiments/week14/mhd_precision_pilot/README.md`
- Modify: `scripts/README.md` (Canonical Entry Points note)
- Modify: `docs/INDEX.md` (§6 data products pointer)

**Ignore-rule reality (verified):** `.gitignore` already ignores `experiments/`
(line 21), `*.bin`/`*.csv`/`*.dat` (lines 22-25), and `build-matrix/` (line 4).
So transient grids and build dirs are already safe — **no new ignore rules are
needed**. The consequence is the opposite of a gap: **every Week-14 file we do
want to commit lives under `experiments/` and must be added with `git add -f`**
(this is how the existing Week-12/13 evidence was tracked).

- [ ] **Step 1: Confirm transient grids are ignored (no `.gitignore` edit)**

Run: `git check-ignore experiments/week14/mhd_precision_pilot/runs/cpu-float-O2-ieee-leq/grid.bin build-matrix/`
Expected: both paths are echoed (ignored). No `.gitignore` change is required.

- [ ] **Step 2: Confirm evidence files also need `-f` (they are under the ignored tree)**

Run: `git check-ignore experiments/week14/mhd_precision_pilot/summary.json experiments/week14/mhd_precision_pilot/summary.csv`
Expected: both paths are echoed (ignored) — so evidence commits below use `git add -f`.

- [ ] **Step 3: Write the experiment README**

```markdown
<!-- experiments/week14/mhd_precision_pilot/README.md -->
# Week 14 — HLL MHD Precision Pilot (Brio-Wu 1D)

Harness pilot for the Report 2 MHD floating-point precision study. HLL solver,
CPU only. `summary.json` is authoritative (nested gates, MCA aggregate, claim
buckets); `summary.csv` is a flattened convenience view.

Run (P0, deterministic-only, no Docker):

    & "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_precision_pilot.py --phase p0 --skip-mca

Run (P0 with MCA if a Verificarlo runner is available):

    & "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_precision_pilot.py --phase p0 --samples 8

Claim buckets: **morphology** (Brio-Wu structure, Week-12 evidence, referenced
only); **self-reference** (deterministic deltas vs cpu-double-O2-ieee-leq —
engineering consistency, not an exact-solution match); **precision/noise** (MCA
noise floor + SNR). Grids are transient (deleted unless `--keep-grids`); build
dirs are not committed.
```

- [ ] **Step 4: Register canonical entry point in `scripts/README.md`**

Under "Canonical Entry Points", add a row:

```markdown
| Summarise (MHD precision) | `regression/mhd_precision_pilot.py` | **canonical** Week-14 MHD precision-study aggregator; authoritative `summary.json`. `matrix_summary_report.py` is generic-checks-only here. |
```

- [ ] **Step 5: Add a data-products pointer in `docs/INDEX.md` §6**

```markdown
| `experiments/week14/mhd_precision_pilot/` | Week-14 HLL MHD precision pilot (Brio-Wu 1D): deterministic build-axis deltas vs `cpu-double-O2-ieee-leq` + Verificarlo MCA aggregate; unified `summary.{csv,json,md}` + figures |
```

- [ ] **Step 6: Commit**

```bash
git add -f experiments/week14/mhd_precision_pilot/README.md
git add scripts/README.md docs/INDEX.md
git commit -m "docs(week14): register MHD precision pilot experiment + entry points"
```

---

### Task 9: End-to-end P0 execution + phase-scaling notes (no new code)

**Files:** none created — this task runs the harness and records evidence.

- [ ] **Step 1: Run the full unit suite (Python) to confirm green**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py -q`
Expected: all tests pass (including the 5 new test modules).

- [ ] **Step 2: Execute P0 deterministic-only (no Docker) end-to-end**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_precision_pilot.py --phase p0 --skip-mca`
Expected: prints `summary.md`; **G0 pass: True** (reference reproduces `steps=759`, `divB_max≈4.441e-14`; all 8 runs finite; MCA blocks represented as `blocked_environment`). Exit code 0.

- [ ] **Step 3: Inspect the authoritative summary**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -c "import json; d=json.load(open('experiments/week14/mhd_precision_pilot/summary.json')); print(d['gates']['G0']); print(len(d['deterministic']), 'variants')"`
Expected: `{'pass': True, ...}` and `8 variants`.

- [ ] **Step 4: (Optional) Execute P0 with MCA if Docker/Verificarlo is available**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_precision_pilot.py --phase p0 --samples 8`
Expected: MCA blocks show `status: completed` with `p53` spreads ≈ machine ε and `p24` spreads at float-surrogate scale — OR a clean `blocked_environment` if no runner (still G0 pass).

- [ ] **Step 5: Confirm transient grids are gone (ignore-aware check)**

Run: `git status --porcelain --ignored experiments/week14`
Expected: no `*.bin` and no `build-matrix/` entries. `--ignored` is required — because `experiments/` is gitignored, a plain `git status` shows nothing here. Grids were deleted post-norm by Task 7's cleanup pass; only `summary.{csv,json,md}`, `matrix.json`, `figures/*.png`, per-run `config.cfg`/`stdout.txt`/`stderr.txt`/`metadata.json`, and `README.md` should exist on disk (all listed as ignored `!!` until force-added).

- [ ] **Step 6: Commit the P0 evidence packet (force-add — the tree is gitignored)**

`-f` is mandatory: every path below is under the gitignored `experiments/` tree (and `summary.csv` also matches `*.csv`). Grids are already deleted, so force-adding `runs/` will not sweep in any `*.bin`.

```bash
git add -f experiments/week14/mhd_precision_pilot/summary.json \
           experiments/week14/mhd_precision_pilot/summary.csv \
           experiments/week14/mhd_precision_pilot/summary.md \
           experiments/week14/mhd_precision_pilot/matrix.json \
           experiments/week14/mhd_precision_pilot/figures \
           experiments/week14/mhd_precision_pilot/runs
git commit -m "test(mhd): Week-14 P0 precision-pilot evidence (Brio-Wu 1D, HLL)"
```

- [ ] **Step 7: Record phase-scaling recipe (P1/P2) in the experiment README**

Append to `experiments/week14/mhd_precision_pilot/README.md`:

```markdown
## Phase scaling (no new code)

- **P1 (deterministic breadth, 24 variants):**
  `mhd_precision_pilot.py --phase p1 --skip-mca` -- same schema, full
  precision x opt x fastmath x riemann fan. Review `gates.G1.ordering_flags`
  (fastmath/ieee inversions) before making any ordering claim.
- **P2 (MCA depth):** run the sampler once --
  `mhd_precision_sampling.py --samples 30` (writes `mca/summary.json`) -- then
  fold it without re-sampling:
  `mhd_precision_pilot.py --phase p0 --mca-summary experiments/week14/mhd_precision_pilot/mca/summary.json`.
  `blocked_environment` remains a valid, non-failing outcome.
```

- [ ] **Step 8: Commit the scaling notes**

```bash
git add experiments/week14/mhd_precision_pilot/README.md
git commit -m "docs(week14): P1/P2 phase-scaling recipe for MHD precision pilot"
```

---

## Self-Review

**1. Spec coverage** (spec §-by-§):
- §1 scope (Brio-Wu 1D / HLL / CPU; out-of-scope) → Global Constraints + Task 7 `p0_filter`/`--phase`; P1/P2 as invocations (Task 9).
- §2 preconditions (hrsc_mhd target, `<=`/`<` axis, reference label, anchor, MCA vocab) → Tasks 1, 4, 6, 7.
- §3 phases + gates (G0 hard incl. real `schema_valid`, G1 soft ordering, G2) → Task 4 (`gate_g0`/`gate_g1`/`gate_g2`/`ordering_flags`/`schema_valid`); G2 emits `pending_depth` before P2 depth runs.
- §4 directory layout → Tasks 7 (`runs/`, `matrix.json`, `figures/`), 6 (`mca/`), 8 (README/ignore).
- §5 fields (rho/By/p gate + vx continuity) → Task 2 `FIELD_NAMES`/`GATE_FIELDS`.
- §6 unified schema + claim buckets + `blocked_environment` + csv/json authority → Tasks 4, 5, 6.
- §7 new code + additive filter + `--keep-grids` + untouched surface → Tasks 1, 6, 7 (grid deletion), Global Constraints.
- §8 verification (pilot schema test, filter test, anchor assertion, no-Euler-regression) → Tasks 1, 4, 5, 7 tests; Task 9 Steps 1–2.
- §9 risks (docker, disk, non-monotonicity, transient discipline, scope) → blocked-safe MCA (Task 6), sequential builds (Task 7), soft flags (Task 4), ignore rules (Task 8).
- §10 Week 15 handoff / §11 resolved decisions → README P1/P2 notes (Task 9).

**2. Placeholder scan:** No "TBD/TODO/handle edge cases/similar to Task N". Every code step shows complete code; every run step shows an exact command + expected output.

**3. Type consistency:** `FIELD_NAMES`/`GATE_FIELDS` defined once (Task 2) and imported by Tasks 3, 6, 7. `REFERENCE`/`ANCHOR_*` defined once (Task 4) and reused by Tasks 5, 7 tests. Row dict keys (`variant, precision, opt, fastmath, riemann, is_reference, finite, rc, steps, divB_max, walltime_s, L*_<field>`) are produced by `measure_run` (Task 7) and consumed by `gate_*`/`assemble_summary`/`write_summaries` (Tasks 4–5) — matched. MCA block keys (`status, n, spread_*, snr_*, rho_mean_spread, mca_evidence_generated`) come from a single shared `blocked_mca_block` (Task 4 core, `MCA_FIELD_KEYS`) reused by the sampler (Task 6) and the driver's `--skip-mca` path (Task 7), or from `mca_field_spread` on `completed`; `schema_valid` (Task 4) enforces the required subset and `write_summaries` (Task 5) renders them — matched.
