# Week 15 Solver-Aware Orszag-Tang 2D Precision Smoke Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Spec:** [2026-07-08-week15-ot-2d-precision-design.md](../specs/2026-07-08-week15-ot-2d-precision-design.md) (approved 2026-07-08).
> **Supersedes:** [2026-07-02-week15-ot-2d-precision-smoke.md](2026-07-02-week15-ot-2d-precision-smoke.md) (pre-HLLD-clearance; do not execute).

**Goal:** Land the in-flight HLLD solver-axis work, then deliver a gated, claim-bounded Orszag-Tang 2D precision packet per solver (HLL + HLLD): deterministic P0 build fan at two profiles (gate 128²/t=0.1, headline 256²/t=0.5) plus Docker Verificarlo MCA — CPU only.

**Architecture:** One new driver `scripts/regression/mhd_orszag_tang_precision_smoke.py` orchestrates one `(solver, profile)` packet per invocation, reusing the pilot's build machinery (`build_variant`, `select_variants("p0")`, `ordered_variants_reference_first`) and the shared `_mhd_harness` / `mhd_fields` / `mhd_paper_figures` layers. Every row is measured against the **same-solver** `cpu-double-O2-ieee-leq` reference; the reference row must reproduce the 2026-07-06 HLLD-follow-up anchors. MCA reuses `mhd_precision_sampling.py`, which gains `--case` / `--experiment` passthrough on top of its in-flight `--solver`.

**Tech Stack:** Python 3.11 (`C:\Users\tangy\miniconda3\envs\floatpoint\python.exe`), pytest, CMake/Ninja/MSVC via `build_variant()`, Docker Verificarlo image `verificarlo/verificarlo:cmake`, numpy-only figure layer (`plot_heatmap_panels`).

---

## Global Constraints

- Scope: Orszag-Tang 2D, **CPU only**, solvers `{hll, hlld}` via the existing runtime cfg key `riemann`. `hll` stays the executable's production default.
- Out of scope (do not quietly grow): GPU MHD, Kelvin-Helmholtz, 512² convergence runs, Lyapunov/temporal-divergence fitting (Week 16), cluster runs, changing the production solver default, MCA depth beyond n=3.
- Do not modify `src/mhd/*` numerics, any **existing** cfg file, the `io.hpp` output format, `build_all.sh`, the Euler path, or committed Week-12/13/14 evidence. Adding `tests/cases/orszag_tang_2d/orszag_tang_mca64.cfg` is explicitly allowed (Task 3).
- Profiles are the only sanctioned deterministic configurations (no free-form grid flags): **gate** = 128², `t_end=0.1`; **headline** = 256², `t_end=0.5`.
- Anchors keyed by (solver, profile), from [hlld_divb_followup/summary.md](../../../experiments/week13/hlld_divb_followup/summary.md): gate → `steps=76`, `divB_max` 1.173 (hll) / 1.085 (hlld); headline → `steps=806`, `divB_max=3.72` (hll) / `steps=812`, `divB_max=24.45` (hlld). Steps exact; divB_max within **5 % rtol**. If the gate fails, **investigate — never widen the tolerance**.
- MCA: `p53` + `p24`, **n=3 samples each**, per solver, on the 64²/t=0.05 cfg, experiment label `week15-mhd-mca`, image `verificarlo/verificarlo:cmake`. `blocked_environment` is a valid recorded outcome but the packet is not supervisor-ready without a Docker rerun.
- Run all build/evidence commands from a console with the VS dev environment loaded (`call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64`, [docs/INDEX.md](../../INDEX.md) §4). Before evidence runs, delete the 8 P0 `build-matrix` dirs so `build_variant()` reconfigures from clean (stale-binary pitfall, INDEX §7).
- Binary grids are transient: deleted unless `--keep-grids`; never commit `.bin` files or build dirs. `experiments/` is gitignored — use `git add -f` for evidence files.
- Python tests: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py -q`. New regression-script tests insert `scripts/regression` into `sys.path` themselves (conftest only adds `scripts`, `scripts/metrics`, `scripts/figures`).

## File Map

- Commit as-is (Task 1): the current working-tree changes — solver axis in `scripts/regression/mhd_precision_pilot.py` + `mhd_precision_pilot_core.py` + `scripts/figures/mhd_precision_pilot_plots.py` + `scripts/verificarlo/mhd_precision_sampling.py` + `mhd_verificarlo_smoke.py` (+ 5 test files), HLLD pilot evidence `experiments/week14/mhd_precision_pilot_hlld/`, `scripts/regression/mhd_paper_style_mk2005.py`, resolution-ladder fix, Week-13/14 docs.
- Create: `scripts/regression/mhd_orszag_tang_precision_smoke.py` — Week-15 packet driver (profiles, cfg, measure, anchor gate, summary, figures, CLI).
- Create: `tests/py/test_mhd_orszag_tang_precision_smoke.py` — unit tests with injected builder/runner/reader.
- Create: `tests/cases/orszag_tang_2d/orszag_tang_mca64.cfg` — 64²/t=0.05 MCA smoke grid.
- Modify: `scripts/verificarlo/mhd_precision_sampling.py` + `tests/py/test_mhd_precision_sampling.py` — `case` and `experiment` passthrough.
- Modify (Task 6): `docs/superpowers/plans/2026-07-02-week15-ot-2d-precision-smoke.md` (superseded banner), `scripts/regression/README.md`, `docs/INDEX.md` §6.
- Evidence (Task 5 only): `experiments/week15/orszag_tang_precision_smoke/` (HLL) and `experiments/week15/orszag_tang_precision_smoke_hlld/` (HLLD), each containing `gate128/`, `headline256/`, `mca/`.

---

### Task 1: Land the In-Flight Solver-Axis and Figure Work

The working tree already contains complete, tested changes (73 tests green as of 2026-07-08): the `--solver hll|hlld` axis through the pilot and MCA sampler, the generated HLLD Brio-Wu pilot evidence, the MK2005 paper-style renderer, and the resolution-ladder figure fix. This task verifies and commits them in reviewable slices. **Do not rewrite any of this code.**

**Files:**
- Commit only; no edits.

**Interfaces:**
- Produces (relied on by Tasks 2–5): `mhd_precision_pilot.build_variant(variant) -> pathlib.Path` (clean cmake configure+build into `build-matrix/<name>/`, returns the `hrsc_mhd` binary path), `mhd_precision_pilot.select_variants("p0") -> list[BuildVariant]` (8 variants `{double,float}×{O2,Ofast}×ieee×{leq,strict}`; `BuildVariant` fields: `precision`, `opt_level`, `fast_math`, `strict_riemann`, `hardware`, `.name`), `mhd_precision_pilot.ordered_variants_reference_first(variants) -> list[BuildVariant]`, `mhd_precision_pilot_core.REFERENCE == "cpu-double-O2-ieee-leq"`, `mhd_precision_sampling.sample_precision(out_dir, precision, samples=8, image=DEFAULT_IMAGE, solver="hll") -> dict`.

- [ ] **Step 1: Verify the whole Python suite is green**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py -q
```

Expected: all tests pass (0 failures). If sandbox/temp permission errors appear, retry with `--basetemp` pointing at a writable directory; genuine failures block this task.

- [ ] **Step 2: Verify the HLLD pilot evidence has no transient grids**

Run:

```powershell
Get-ChildItem -Path experiments\week14\mhd_precision_pilot_hlld -Recurse -Include *.bin
```

Expected: no output. If `.bin` files exist, delete them before committing.

- [ ] **Step 3: Commit the solver axis**

```powershell
git add scripts/regression/mhd_precision_pilot.py scripts/regression/mhd_precision_pilot_core.py scripts/figures/mhd_precision_pilot_plots.py scripts/verificarlo/mhd_precision_sampling.py scripts/verificarlo/mhd_verificarlo_smoke.py tests/py/test_mhd_precision_pilot_driver.py tests/py/test_mhd_precision_pilot_plots.py tests/py/test_mhd_precision_pilot_summary.py tests/py/test_mhd_precision_sampling.py tests/py/test_mhd_verificarlo_smoke.py
git commit -m "feat(mhd): add --solver hll|hlld axis to precision pilot and MCA sampler"
```

- [ ] **Step 4: Commit the HLLD pilot evidence and Week-13 decision update**

```powershell
git add -f experiments/week14/mhd_precision_pilot_hlld
git add docs/week13/week13-summary.md
git commit -m "test(mhd): Week-14 HLLD Brio-Wu pilot evidence (solver-axis rerun)"
```

- [ ] **Step 5: Commit the MK2005 renderer and refreshed figures**

```powershell
git add scripts/regression/mhd_paper_style_mk2005.py scripts/regression/mhd_kh_2d.py scripts/regression/mhd_orszag_tang_2d.py scripts/regression/README.md
git add -f experiments/week13/orszag_tang/figures/ot_paper_style.png experiments/week13/kelvin_helmholtz/figures/kh_paper_style.png
git commit -m "feat(figures): MK2005 paper-style Orszag-Tang/KH renderer"
```

- [ ] **Step 6: Commit the resolution-ladder figure fix**

```powershell
git add scripts/regression/mhd_week14_supplemental.py tests/py/test_mhd_week14_supplemental.py
git add -f experiments/week14/mhd_supplemental/resolution_ladder/figure.png
git commit -m "fix(figures): keep resolution-ladder log axis off the zero-error reference point"
```

- [ ] **Step 7: Commit the outstanding Week-13/14 docs**

```powershell
git add docs/week13/week13-supervisor-meeting.md docs/week13/week13-supervisor-meeting-EN.md docs/week13/week14-brainstorming-prompt.md docs/week14 docs/superpowers/specs/2026-07-01-week14-mhd-plan-design.md docs/superpowers/plans/2026-07-01-week14-mhd-precision-pilot.md docs/superpowers/plans/2026-07-02-week15-ot-2d-precision-smoke.md docs/superpowers/plans/2026-07-08-week15-ot-2d-solver-aware-precision-smoke.md
git commit -m "docs: land Week-13/14 meeting notes and Week-14/15 plans"
git status --short
```

Expected final `git status`: clean (only untracked experiment scratch, if any).

---

### Task 2: OT Smoke Profiles, Measurement, Anchor Gate, and Summary Helpers

**Files:**
- Create: `tests/py/test_mhd_orszag_tang_precision_smoke.py`
- Create: `scripts/regression/mhd_orszag_tang_precision_smoke.py`

**Interfaces:**
- Consumes: `select_variants`, `ordered_variants_reference_first`, `build_variant` from `mhd_precision_pilot`; `REFERENCE` from `mhd_precision_pilot_core`; `replace_or_append_cfg`, `point_symmetry_residual`, `git_commit`, `run_case`, `sha256_file` from `_mhd_harness`; `read_binary` from `io_helper`; `field_norms`, `mhd_primitive_fields` from `mhd_fields`; `plot_heatmap_panels` from `mhd_paper_figures`.
- Produces (used by Task 4): `PROFILES: dict[str, dict]` (keys `gate`/`headline`, values with `subdir`, `nx`, `ny`, `t_end`), `OT_ANCHORS: dict[tuple[str, str], tuple[int, float]]`, `plan_row(variant, solver, profile) -> dict`, `deterministic_plan(solver="hll", profile="gate") -> list[dict]`, `orszag_tang_cfg(base_text, *, solver, profile, output_file) -> str`, `case_gamma(cfg_text) -> float`, `measure_pair(plan, arr, ref_arr, *, gamma, dx, dy, diagnostics, walltime_s) -> dict`, `anchor_gate(rows, solver, profile) -> dict`, `write_outputs(out_dir, rows, *, solver, profile, git_commit, figures) -> dict`, `write_figures(out_dir, arr, ref_arr, *, gamma, dx, dy) -> list[str]`, constants `EXPERIMENT`, `DEFAULT_OUT`, `SUPPORTED_SOLVERS`.

- [ ] **Step 1: Write the failing tests**

Create `tests/py/test_mhd_orszag_tang_precision_smoke.py`:

```python
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "regression"))

import mhd_orszag_tang_precision_smoke as ot


def test_default_plan_is_solver_aware_p0_fan():
    rows = ot.deterministic_plan()

    assert len(rows) == 8
    assert rows[0] == {
        "suite": "deterministic",
        "case": "orszag_tang_2d",
        "variant": "cpu-double-O2-ieee-leq",
        "precision": "double",
        "opt": "O2",
        "fast_math": False,
        "riemann": "leq",
        "hardware": "cpu",
        "solver": "hll",
        "profile": "gate",
        "nx": 128,
        "ny": 128,
        "t_end": 0.1,
    }
    assert {row["variant"] for row in rows} == {
        f"cpu-{precision}-{opt}-ieee-{riemann}"
        for precision in ("double", "float")
        for opt in ("O2", "Ofast")
        for riemann in ("leq", "strict")
    }
    headline = ot.deterministic_plan(solver="hlld", profile="headline")
    assert all(row["solver"] == "hlld" and row["nx"] == 256 and row["t_end"] == 0.5 for row in headline)
    with pytest.raises(ValueError):
        ot.deterministic_plan(solver="roe")
    with pytest.raises(ValueError):
        ot.deterministic_plan(profile="huge")


def test_orszag_tang_cfg_overrides_only_harness_keys():
    base = "test = orszag_tang\nnx = 256\nny = 256\nt_end = 0.5\ngamma = 1.6666666666666667\n"

    text = ot.orszag_tang_cfg(base, solver="hlld", profile="gate",
                              output_file=Path("runs/a/grid.bin"))

    assert "test = orszag_tang" in text
    assert "nx = 128" in text
    assert "ny = 128" in text
    assert "t_end = 0.1" in text
    assert "riemann = hlld" in text
    assert "output_format = binary" in text
    assert "output_file = runs/a/grid.bin" in text.replace("\\", "/")
    assert ot.case_gamma(base) == pytest.approx(5.0 / 3.0)


def test_measure_pair_reports_2d_schema_and_norms():
    ref = np.zeros((2, 2, 9), dtype=np.float64)
    ref[..., 0] = 1.0
    ref[..., 4] = 0.5
    ref[..., 5] = 0.25
    ref[..., 7] = 2.0
    arr = ref.copy()
    arr[0, 0, 0] = 1.5
    arr[1, 1, 5] = 0.75
    row = ot.deterministic_plan()[1]

    measured = ot.measure_pair(
        row,
        arr,
        ref,
        gamma=5.0 / 3.0,
        dx=0.5,
        dy=0.5,
        diagnostics={"steps": 76, "divB_mean": 0.2, "divB_max": 1.25},
        walltime_s=0.25,
    )

    assert measured["case"] == "orszag_tang_2d"
    assert measured["finite"] is True
    assert measured["steps"] == 76
    assert measured["divB_mean"] == 0.2
    assert measured["divB_max"] == 1.25
    assert measured["Linf_rho"] == 0.5
    assert measured["Linf_By"] == 0.5
    assert "symmetry_residual_rho" in measured


def test_anchor_gate_checks_reference_row_per_profile():
    good = [
        {"is_reference": True, "finite": True, "steps": 76, "divB_max": 1.15},
        {"is_reference": False, "finite": True, "steps": 76, "divB_max": 1.16},
    ]
    gate = ot.anchor_gate(good, "hll", "gate")
    assert gate["pass"] is True
    assert gate["expected_steps"] == 76
    assert gate["expected_divB_max"] == 1.173

    bad_steps = [dict(good[0], steps=80), good[1]]
    assert ot.anchor_gate(bad_steps, "hll", "gate")["pass"] is False
    bad_divb = [dict(good[0], divB_max=2.5), good[1]]
    assert ot.anchor_gate(bad_divb, "hll", "gate")["pass"] is False
    assert ot.anchor_gate(good, "hlld", "gate")["pass"] is False  # 1.15 vs 1.085 > 5%

    headline = [{"is_reference": True, "finite": True, "steps": 812, "divB_max": 24.0}]
    assert ot.anchor_gate(headline, "hlld", "headline")["pass"] is True


def test_summary_and_report_are_json_safe(tmp_path):
    rows = [
        {
            "variant": "cpu-double-O2-ieee-leq",
            "is_reference": True,
            "finite": True,
            "steps": 76,
            "divB_max": np.float64(1.173),
            "Linf_rho": np.float64(0.0),
            "Linf_By": np.float64(0.0),
            "Linf_p": np.float64(0.0),
        }
    ]

    payload = ot.write_outputs(tmp_path, rows, solver="hll", profile="gate",
                               git_commit="abc123", figures=["figures/rho.png"])

    saved = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert saved["experiment"] == ot.EXPERIMENT
    assert saved["solver"] == "hll"
    assert saved["profile"] == "gate"
    assert saved["git_commit"] == "abc123"
    assert saved["gates"]["G0_anchor"]["pass"] is True
    assert saved["rows"][0]["divB_max"] == 1.173
    report = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "Week 15 Orszag-Tang 2D Precision Smoke" in report
    assert "gate" in report
    assert "Docker Verificarlo" in report
    assert payload["figures"] == ["figures/rho.png"]
    assert (tmp_path / "summary.csv").is_file()


def test_plot_helpers_create_nonempty_pngs(tmp_path):
    ref = np.ones((4, 4, 9), dtype=np.float64)
    ref[..., 4] = 0.5
    ref[..., 5] = 0.25
    ref[..., 7] = 3.0
    arr = ref.copy()
    arr[:, 2:, 0] += 0.125

    out = ot.write_figures(tmp_path, arr, ref, gamma=5.0 / 3.0, dx=0.25, dy=0.25)

    assert out
    for rel in out:
        path = tmp_path / rel
        assert path.is_file()
        assert path.stat().st_size > 0
```

- [ ] **Step 2: Run tests to verify they fail**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_orszag_tang_precision_smoke.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'mhd_orszag_tang_precision_smoke'`.

- [ ] **Step 3: Implement the helper layer**

Create `scripts/regression/mhd_orszag_tang_precision_smoke.py`:

```python
#!/usr/bin/env python3
"""Week-15 solver-aware Orszag-Tang 2D precision smoke.

Points the Week-14 Brio-Wu precision-pilot methodology at the first 2D MHD
case: the P0 deterministic build fan {double,float} x {O2,Ofast} x ieee x
{leq,strict}, run per Riemann solver (`hll` production default, `hlld` axis)
and per profile (gate 128^2/t=0.1, headline 256^2/t=0.5). Every row is
measured against the same-solver cpu-double-O2-ieee-leq reference, which must
reproduce the 2026-07-06 HLLD div(B) follow-up anchors.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASE = ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg"
DEFAULT_OUT = ROOT / "experiments" / "week15" / "orszag_tang_precision_smoke"
EXPERIMENT = "week15-orszag-tang-2d-precision-smoke"
DEFAULT_GAMMA = 5.0 / 3.0
SUPPORTED_SOLVERS = ("hll", "hlld")
# The only sanctioned deterministic configurations (spec section 4.1).
PROFILES = {
    "gate": {"subdir": "gate128", "nx": 128, "ny": 128, "t_end": 0.1},
    "headline": {"subdir": "headline256", "nx": 256, "ny": 256, "t_end": 0.5},
}
# Reference-row anchors measured by the 2026-07-06 HLLD div(B) follow-up
# (experiments/week13/hlld_divb_followup: OT, cfl=0.4, glm_cr=0.18, double
# build). Steps must match exactly; divB_max within OT_ANCHOR_DIVB_RTOL.
OT_ANCHORS = {
    ("hll", "gate"): (76, 1.173),
    ("hlld", "gate"): (76, 1.085),
    ("hll", "headline"): (806, 3.72),
    ("hlld", "headline"): (812, 24.45),
}
OT_ANCHOR_DIVB_RTOL = 0.05

for path in (ROOT / "scripts", ROOT / "scripts" / "metrics", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(path))

from _mhd_harness import (  # noqa: E402
    git_commit,
    point_symmetry_residual,
    replace_or_append_cfg,
    run_case,
    sha256_file,
)
from io_helper import read_binary  # noqa: E402
from mhd_fields import field_norms, mhd_primitive_fields  # noqa: E402
from mhd_paper_figures import plot_heatmap_panels  # noqa: E402
from mhd_precision_pilot import (  # noqa: E402
    build_variant,
    ordered_variants_reference_first,
    select_variants,
)
from mhd_precision_pilot_core import REFERENCE  # noqa: E402


def _normalise_solver(solver: str) -> str:
    solver = str(solver).lower()
    if solver not in SUPPORTED_SOLVERS:
        raise ValueError(f"unsupported OT smoke solver: {solver}")
    return solver


def _normalise_profile(profile: str) -> str:
    profile = str(profile).lower()
    if profile not in PROFILES:
        raise ValueError(f"unsupported OT smoke profile: {profile}")
    return profile


def case_gamma(cfg_text: str) -> float:
    """Read gamma from cfg text, defaulting to the Orszag-Tang gamma=5/3."""
    for line in cfg_text.splitlines():
        content = line.split("#", 1)[0].strip()
        if not content or "=" not in content:
            continue
        key, value = [part.strip() for part in content.split("=", 1)]
        if key == "gamma":
            return float(value)
    return DEFAULT_GAMMA


def plan_row(variant: Any, solver: str, profile: str) -> dict[str, Any]:
    profile = _normalise_profile(profile)
    spec = PROFILES[profile]
    return {
        "suite": "deterministic",
        "case": "orszag_tang_2d",
        "variant": variant.name,
        "precision": variant.precision,
        "opt": variant.opt_level,
        "fast_math": bool(variant.fast_math),
        "riemann": "strict" if variant.strict_riemann else "leq",
        "hardware": variant.hardware,
        "solver": _normalise_solver(solver),
        "profile": profile,
        "nx": int(spec["nx"]),
        "ny": int(spec["ny"]),
        "t_end": float(spec["t_end"]),
    }


def deterministic_plan(solver: str = "hll", profile: str = "gate") -> list[dict[str, Any]]:
    variants = ordered_variants_reference_first(select_variants("p0"))
    return [plan_row(variant, solver, profile) for variant in variants]


def orszag_tang_cfg(
    base_text: str,
    *,
    solver: str,
    profile: str,
    output_file: str | pathlib.Path,
) -> str:
    spec = PROFILES[_normalise_profile(profile)]
    text = replace_or_append_cfg(base_text, "nx", str(int(spec["nx"])))
    text = replace_or_append_cfg(text, "ny", str(int(spec["ny"])))
    text = replace_or_append_cfg(text, "t_end", f"{float(spec['t_end']):g}")
    text = replace_or_append_cfg(text, "riemann", _normalise_solver(solver))
    text = replace_or_append_cfg(text, "output_format", "binary")
    text = replace_or_append_cfg(text, "output_file", pathlib.PurePath(output_file).as_posix())
    return text


def measure_pair(
    plan: Mapping[str, Any],
    arr: np.ndarray,
    ref_arr: np.ndarray,
    *,
    gamma: float,
    dx: float,
    dy: float,
    diagnostics: Mapping[str, Any],
    walltime_s: float,
) -> dict[str, Any]:
    finite = bool(np.isfinite(arr).all() and np.isfinite(ref_arr).all())
    norms = (
        field_norms(arr.astype(np.float64, copy=False), ref_arr.astype(np.float64, copy=False), gamma, dx)
        if finite
        else _zero_norms()
    )
    rho = (
        mhd_primitive_fields(arr.astype(np.float64, copy=False), gamma)["rho"]
        if finite
        else np.zeros(arr.shape[:2])
    )
    row = dict(plan)
    row.update(
        {
            "finite": finite,
            "steps": int(diagnostics.get("steps", 0) or 0),
            "divB_mean": _finite_float(diagnostics.get("divB_mean", 0.0)),
            "divB_max": _finite_float(diagnostics.get("divB_max", 0.0)),
            "walltime_s": _finite_float(walltime_s),
            "dx": _finite_float(dx),
            "dy": _finite_float(dy),
            "symmetry_residual_rho": _finite_float(point_symmetry_residual(rho)),
        }
    )
    row.update({key: _finite_float(value) for key, value in norms.items()})
    return row


def anchor_gate(rows: Sequence[Mapping[str, Any]], solver: str, profile: str) -> dict[str, Any]:
    expected_steps, expected_divb = OT_ANCHORS[(_normalise_solver(solver), _normalise_profile(profile))]
    ref = next((row for row in rows if row.get("is_reference")), None)
    finite_ok = bool(rows) and all(bool(row.get("finite")) for row in rows)
    steps_ok = ref is not None and int(ref.get("steps", -1)) == expected_steps
    divb = float(ref.get("divB_max", float("nan"))) if ref is not None else float("nan")
    divb_ok = math.isfinite(divb) and abs(divb - expected_divb) <= OT_ANCHOR_DIVB_RTOL * expected_divb
    return {
        "pass": bool(finite_ok and steps_ok and divb_ok),
        "finite_ok": finite_ok,
        "steps_ok": bool(steps_ok),
        "divB_ok": bool(divb_ok),
        "expected_steps": expected_steps,
        "expected_divB_max": expected_divb,
        "divB_rtol": OT_ANCHOR_DIVB_RTOL,
    }


def write_outputs(
    out_dir: str | pathlib.Path,
    rows: Sequence[Mapping[str, Any]],
    *,
    solver: str,
    profile: str,
    git_commit: str,
    figures: Sequence[str],
) -> dict[str, Any]:
    solver = _normalise_solver(solver)
    profile = _normalise_profile(profile)
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "experiment": EXPERIMENT,
        "case": str(CASE.relative_to(ROOT)).replace("\\", "/"),
        "solver": solver,
        "profile": profile,
        "git_commit": git_commit,
        "reference_variant": REFERENCE,
        "gates": {"G0_anchor": anchor_gate(rows, solver, profile)},
        "rows": [dict(row) for row in rows],
        "figures": list(figures),
        "mca": {
            "required": True,
            "note": (
                "Docker Verificarlo MCA is recorded separately under the solver "
                "top-level mca/summary.json and remains required for supervisor evidence."
            ),
        },
    }
    (out / "summary.json").write_text(
        json.dumps(_jsonable(payload), indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        keys = sorted({key for row in rows for key in row})
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows([{key: row.get(key, "") for key in keys} for row in rows])
    (out / "summary.md").write_text(_render_markdown(payload), encoding="utf-8")
    return payload


def write_figures(
    out_dir: str | pathlib.Path,
    arr: np.ndarray,
    ref_arr: np.ndarray,
    *,
    gamma: float,
    dx: float,
    dy: float,
) -> list[str]:
    out = pathlib.Path(out_dir)
    fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    prim = mhd_primitive_fields(arr.astype(np.float64, copy=False), gamma)
    ref_prim = mhd_primitive_fields(ref_arr.astype(np.float64, copy=False), gamma)
    paths = [
        # Spec section 4.1: density+pressure panels show the fp64 reference;
        # the drift panels show the candidate against that reference.
        plot_heatmap_panels(
            fig_dir / "ot_density_pressure.png",
            [
                {"title": "rho (fp64 reference)", "field": ref_prim["rho"]},
                {"title": "p (fp64 reference)", "field": ref_prim["p"]},
            ],
            columns=2,
        ),
        plot_heatmap_panels(
            fig_dir / "ot_fp64_reference_drift.png",
            [
                {"title": "abs rho drift", "field": np.abs(prim["rho"] - ref_prim["rho"]), "log10": True},
                {"title": "abs By drift", "field": np.abs(prim["By"] - ref_prim["By"]), "log10": True},
            ],
            columns=2,
        ),
    ]
    return [path.relative_to(out).as_posix() for path in paths]


def _zero_norms() -> dict[str, float]:
    return {f"{norm}_{field}": 0.0 for field in ("rho", "By", "p", "vx") for norm in ("L1", "L2", "Linf")}


def _finite_float(value: Any) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"expected finite number, got {value!r}")
    return number


def _jsonable(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _render_markdown(payload: Mapping[str, Any]) -> str:
    rows = list(payload.get("rows", []))
    gate = payload.get("gates", {}).get("G0_anchor", {})
    finite = sum(1 for row in rows if row.get("finite"))
    max_divb = max((abs(float(row.get("divB_max", 0.0))) for row in rows), default=0.0)
    max_linf_by = max((abs(float(row.get("Linf_By", 0.0))) for row in rows), default=0.0)
    lines = [
        "# Week 15 Orszag-Tang 2D Precision Smoke",
        "",
        f"- Solver: `{payload.get('solver', 'unknown')}` · Profile: `{payload.get('profile', 'unknown')}`",
        f"- Git commit: `{payload.get('git_commit', 'unknown')}`",
        f"- G0 anchor gate: {'PASS' if gate.get('pass') else 'FAIL'}"
        f" (expected steps={gate.get('expected_steps')},"
        f" divB_max={gate.get('expected_divB_max')} ± {gate.get('divB_rtol')} rtol)",
        f"- Finite rows: {finite}/{len(rows)}",
        f"- Max |divB_max|: {max_divb:.3e}",
        f"- Max Linf(By) vs same-solver fp64 reference: {max_linf_by:.3e}",
        "- Docker Verificarlo MCA is required as a separate evidence block.",
        "",
        "## Figures",
        "",
    ]
    lines.extend(f"- `{path}`" for path in payload.get("figures", []))
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "Week-15 P0 packet only: Orszag-Tang 2D on CPU with the HLL/HLLD solver",
            "axis. Deltas are against the same-solver fp64 reference (engineering",
            "consistency, not exact-solution validation). No claims about GPU, 512^2",
            "convergence, Kelvin-Helmholtz, or temporal divergence.",
            "",
        ]
    )
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_orszag_tang_precision_smoke.py -q
```

Expected: `6 passed`.

- [ ] **Step 5: Commit**

```powershell
git add scripts/regression/mhd_orszag_tang_precision_smoke.py tests/py/test_mhd_orszag_tang_precision_smoke.py
git commit -m "test(mhd): Week-15 Orszag-Tang precision-smoke helpers"
```

---

### Task 3: MCA Sampler `--case` / `--experiment` Passthrough + Small OT Cfg

`mhd_verificarlo_smoke.py` already accepts `--case` and `--solver`; the sampler wrapper hardcodes `case=DEFAULT_CASE` (Brio-Wu) and the `week14-mhd-mca` label. This task threads both through. The deterministic OT cfg (256², t=0.5) is far too expensive under Verificarlo instrumentation, so a dedicated small cfg file carries the MCA grid.

**Files:**
- Modify: `tests/py/test_mhd_precision_sampling.py`
- Modify: `scripts/verificarlo/mhd_precision_sampling.py`
- Create: `tests/cases/orszag_tang_2d/orszag_tang_mca64.cfg`

**Interfaces:**
- Consumes: existing `sample_precision(out_dir, precision, samples, image, solver)` and wrappers `_sample_args`, `_base_environment_with_experiment_label`, `_run_with_experiment_label` in `mhd_precision_sampling.py`.
- Produces (used by Task 5): `sample_precision(out_dir, precision, samples=8, image=DEFAULT_IMAGE, solver="hll", case=DEFAULT_CASE, experiment=WEEK14_MCA_EXPERIMENT)`; CLI flags `--case <cfg>` and `--experiment <label>`; `summary.json` gains `"case"` and uses the supplied experiment label. Week-14 defaults unchanged (existing callers and tests stay green).

- [ ] **Step 1: Write the failing test**

Add to `tests/py/test_mhd_precision_sampling.py`:

```python
def test_sample_precision_accepts_explicit_case_and_experiment(monkeypatch, tmp_path):
    case = tmp_path / "ot.cfg"
    case.write_text("test = orszag_tang\ngamma = 1.6666666666666667\n", encoding="utf-8")
    seen = {}

    monkeypatch.setattr(sampler, "probe_runners", lambda image: [{"runner": "docker", "supported": True}])
    monkeypatch.setattr(sampler, "choose_runner", lambda probes: "docker")

    def fake_run(args, probes, runner, experiment=sampler.WEEK14_MCA_EXPERIMENT):
        seen["case"] = args.case
        seen["experiment"] = experiment
        return "blocked_run", [], "stop before aggregation", {"status": "blocked_run"}

    monkeypatch.setattr(sampler, "_run_with_experiment_label", fake_run)

    block = sampler.sample_precision(
        tmp_path / "mca",
        precision=53,
        samples=1,
        image="img",
        solver="hlld",
        case=case,
        experiment="week15-mhd-mca",
    )

    assert seen["case"] == case
    assert seen["experiment"] == "week15-mhd-mca"
    assert block["status"] == "blocked_run"
```

- [ ] **Step 2: Run the test to verify it fails**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_precision_sampling.py::test_sample_precision_accepts_explicit_case_and_experiment -q
```

Expected: FAIL with `TypeError: sample_precision() got an unexpected keyword argument 'case'`.

- [ ] **Step 3: Implement the passthrough**

In `scripts/verificarlo/mhd_precision_sampling.py`, apply these exact changes.

`_sample_args` gains a `case` parameter (replaces the hardcoded `DEFAULT_CASE`):

```python
def _sample_args(
    out_dir: pathlib.Path,
    precision: int,
    samples: int,
    image: str,
    solver: str,
    case: pathlib.Path = DEFAULT_CASE,
) -> argparse.Namespace:
    return argparse.Namespace(
        case=pathlib.Path(case),
        out=pathlib.Path(out_dir),
        samples=int(samples),
        precision=int(precision),
        image=image,
        probe_only=False,
        solver=_normalise_solver(solver),
    )
```

Both experiment-label wrappers gain an `experiment` parameter (replaces the hardcoded `smoke.EXPERIMENT = WEEK14_MCA_EXPERIMENT` assignment inside each):

```python
def _base_environment_with_experiment_label(
    args: argparse.Namespace,
    probes: list[dict[str, Any]],
    runner: str | None,
    experiment: str = WEEK14_MCA_EXPERIMENT,
) -> dict[str, Any]:
    previous = smoke.EXPERIMENT
    smoke.EXPERIMENT = experiment
    try:
        environment = base_environment(args, probes, runner)
        environment["solver"] = args.solver
        return environment
    finally:
        smoke.EXPERIMENT = previous


def _run_with_experiment_label(
    args: argparse.Namespace,
    probes: list[dict[str, Any]],
    runner: str,
    experiment: str = WEEK14_MCA_EXPERIMENT,
) -> tuple[str, list[dict[str, Any]], str, dict[str, Any]]:
    previous = smoke.EXPERIMENT
    smoke.EXPERIMENT = experiment
    try:
        status, sample_rows, reason = run_samples(args, probes, runner)
        environment = base_environment(args, probes, runner)
        environment["solver"] = args.solver
        return status, sample_rows, reason, environment
    finally:
        smoke.EXPERIMENT = previous
```

`sample_precision` signature becomes:

```python
def sample_precision(
    out_dir: pathlib.Path,
    precision: int,
    samples: int = DEFAULT_SAMPLES,
    image: str = DEFAULT_IMAGE,
    solver: str = "hll",
    case: pathlib.Path = DEFAULT_CASE,
    experiment: str = WEEK14_MCA_EXPERIMENT,
) -> dict[str, Any]:
```

with these three call-site changes inside it: `args = _sample_args(pathlib.Path(out_dir), precision, samples, image, solver, pathlib.Path(case))`; the runner-is-None branch calls `_base_environment_with_experiment_label(args, probes, None, experiment)`; the run branch calls `_run_with_experiment_label(args, probes, runner, experiment)`.

`parse_args` gains:

```python
    parser.add_argument("--case", type=pathlib.Path, default=DEFAULT_CASE)
    parser.add_argument("--experiment", default=WEEK14_MCA_EXPERIMENT)
```

`main` normalizes and threads both, and stamps them into the summary:

```python
def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out = resolve_output_dir(args.out, args.solver)
    out.mkdir(parents=True, exist_ok=True)
    case = args.case if args.case.is_absolute() else ROOT / args.case
    mca = {
        "p53": sample_precision(
            out / "p53", precision=53, samples=args.samples, image=args.image,
            solver=args.solver, case=case, experiment=args.experiment,
        ),
        "p24": sample_precision(
            out / "p24", precision=24, samples=args.samples, image=args.image,
            solver=args.solver, case=case, experiment=args.experiment,
        ),
    }
    summary = {
        "experiment": args.experiment,
        "case": str(case),
        "samples": args.samples,
        "solver": args.solver,
        "mca": mca,
    }
    write_json(out / "summary.json", summary)
    print(out / "summary.json")
    return 0
```

- [ ] **Step 4: Create the MCA smoke cfg**

Create `tests/cases/orszag_tang_2d/orszag_tang_mca64.cfg`:

```ini
# Week-15 MCA smoke grid for the Orszag-Tang vortex: same physics as
# orszag_tang.cfg but 64^2 and t_end=0.05 so Verificarlo-instrumented samples
# stay affordable. Deterministic Week-15 runs override orszag_tang.cfg
# in-memory instead of using this file.
test    = orszag_tang
nx      = 64
ny      = 64
xmin    = 0.0
xmax    = 1.0
ymin    = 0.0
ymax    = 1.0
gamma   = 1.6666666666666667
cfl     = 0.4
t_end   = 0.05
glm_cr  = 0.18
bc      = periodic
bc_y    = periodic
```

- [ ] **Step 5: Run the sampler test file to verify everything passes**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_precision_sampling.py -q
```

Expected: all tests pass (the pre-existing tests must stay green — the new parameters all have defaults).

- [ ] **Step 6: Commit**

```powershell
git add scripts/verificarlo/mhd_precision_sampling.py tests/py/test_mhd_precision_sampling.py tests/cases/orszag_tang_2d/orszag_tang_mca64.cfg
git commit -m "feat(verificarlo): MCA sampling from explicit case and experiment label"
```

---

### Task 4: Deterministic Packet Runner and CLI

**Files:**
- Modify: `tests/py/test_mhd_orszag_tang_precision_smoke.py`
- Modify: `scripts/regression/mhd_orszag_tang_precision_smoke.py`

**Interfaces:**
- Consumes: everything Task 2 produced; `build_variant` (real builder), `run_case` (real runner), `read_binary` (real reader) as injectable defaults.
- Produces (used by Task 5): `run_deterministic(out_dir, *, solver="hll", profile="gate", variants=None, base_cfg_text=None, builder=build_variant, runner=run_case, reader=read_binary, keep_grids=False) -> dict` (the `write_outputs` payload; `out_dir` is the **profile packet dir**, e.g. `…/orszag_tang_precision_smoke/gate128`); `resolve_output_dir(path, solver) -> pathlib.Path` (solver **top-level** dir); CLI `python scripts/regression/mhd_orszag_tang_precision_smoke.py --solver {hll,hlld} --profile {gate,headline} [--out DIR] [--keep-grids]` printing the packet `summary.md` path and exiting 0 only when the anchor gate passes.

- [ ] **Step 1: Write the failing tests**

Add to `tests/py/test_mhd_orszag_tang_precision_smoke.py`:

```python
def test_run_deterministic_uses_injected_hooks_and_deletes_grids(tmp_path):
    base = "test = orszag_tang\nnx = 256\nny = 256\nt_end = 0.5\ngamma = 1.6666666666666667\n"

    class Header:
        nx = 4
        ny = 4
        dx = 0.25
        dy = 0.25

    arr = np.zeros((4, 4, 9), dtype=np.float64)
    arr[..., 0] = 1.0
    arr[..., 4] = 0.5
    arr[..., 5] = 0.25
    arr[..., 7] = 3.0

    built = []

    def fake_builder(variant):
        built.append(variant.name)
        binary = tmp_path / "hrsc_mhd.exe"
        binary.write_bytes(b"exe")
        return binary

    def fake_runner(label, cfg_text, run_dir, bin_path, source_cfg, commit, binary_sha256, **kwargs):
        assert "riemann = hlld" in cfg_text
        assert "nx = 128" in cfg_text
        grid = Path(kwargs["output_bin"])
        grid.parent.mkdir(parents=True, exist_ok=True)
        grid.write_bytes(b"grid")
        meta = {
            "elapsed_wall_s": 0.1,
            "stderr_diagnostics": {"steps": 76, "divB_mean": 0.2, "divB_max": 1.085},
        }
        return object(), meta, "stderr"

    def fake_reader(path):
        return Header(), arr.copy()

    payload = ot.run_deterministic(
        tmp_path / "out",
        solver="hlld",
        profile="gate",
        base_cfg_text=base,
        builder=fake_builder,
        runner=fake_runner,
        reader=fake_reader,
        keep_grids=False,
    )

    assert len(payload["rows"]) == 8
    assert len(built) == 8
    assert built[0] == "cpu-double-O2-ieee-leq"
    assert payload["rows"][0]["is_reference"] is True
    assert payload["rows"][1]["metadata_path"].endswith("metadata.json")
    assert payload["gates"]["G0_anchor"]["pass"] is True
    assert payload["figures"]
    assert not list((tmp_path / "out").glob("**/grid.bin"))


def test_resolve_output_dir_and_profile_subdirs():
    assert ot.resolve_output_dir(None, "hll") == ot.DEFAULT_OUT
    assert ot.resolve_output_dir(None, "hlld").name == f"{ot.DEFAULT_OUT.name}_hlld"
    explicit = ot.resolve_output_dir(Path("experiments/x"), "hlld")
    assert explicit.is_absolute()
    assert ot.PROFILES["gate"]["subdir"] == "gate128"
    assert ot.PROFILES["headline"]["subdir"] == "headline256"
```

- [ ] **Step 2: Run the tests to verify they fail**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_orszag_tang_precision_smoke.py -q
```

Expected: the two new tests FAIL with `AttributeError` (`run_deterministic` / `resolve_output_dir` not defined); the six Task-2 tests still pass.

- [ ] **Step 3: Implement `run_deterministic`, `resolve_output_dir`, and the CLI**

Append to `scripts/regression/mhd_orszag_tang_precision_smoke.py`:

```python
def run_deterministic(
    out_dir: str | pathlib.Path,
    *,
    solver: str = "hll",
    profile: str = "gate",
    variants: Sequence[Any] | None = None,
    base_cfg_text: str | None = None,
    builder=build_variant,
    runner=run_case,
    reader=read_binary,
    keep_grids: bool = False,
) -> dict[str, Any]:
    solver = _normalise_solver(solver)
    profile = _normalise_profile(profile)
    out = pathlib.Path(out_dir)
    ordered = ordered_variants_reference_first(list(variants or select_variants("p0")))
    source = base_cfg_text if base_cfg_text is not None else CASE.read_text(encoding="utf-8")
    gamma = case_gamma(source)
    commit = git_commit()
    staged: list[tuple[Any, dict[str, Any], pathlib.Path, pathlib.Path, Any, np.ndarray]] = []
    for variant in ordered:
        run_dir = out / "runs" / variant.name
        grid = run_dir / "grid.bin"
        cfg_text = orszag_tang_cfg(source, solver=solver, profile=profile, output_file=grid)
        binary = pathlib.Path(builder(variant))
        sha = sha256_file(binary) if binary.is_file() else "unknown"
        _, meta, _ = runner(
            variant.name, cfg_text, run_dir, binary, CASE, commit, sha,
            output_bin=grid, experiment=EXPERIMENT,
        )
        header, arr = reader(grid)
        staged.append((variant, meta, run_dir, grid, header, arr))
    ref_header, ref_arr = staged[0][4], staged[0][5]
    rows = []
    for variant, meta, run_dir, grid, header, arr in staged:
        row = measure_pair(
            plan_row(variant, solver, profile),
            arr,
            ref_arr,
            gamma=gamma,
            dx=float(header.dx),
            dy=float(header.dy),
            diagnostics=meta.get("stderr_diagnostics", {}),
            walltime_s=float(meta.get("elapsed_wall_s", 0.0)),
        )
        row["is_reference"] = variant.name == REFERENCE
        row["run_dir"] = str(run_dir)
        row["metadata_path"] = str(run_dir / "metadata.json")
        rows.append(row)
        if not keep_grids and grid.is_file():
            grid.unlink()
    # Drift figure: float-O2-leq (the primary precision axis) against the
    # fp64 reference; falls back to the last variant if the fan was narrowed.
    drift = next(
        (s for s in staged if s[0].precision == "float" and s[0].opt_level == "O2" and not s[0].strict_riemann),
        staged[-1],
    )
    figures = write_figures(
        out, drift[5], ref_arr, gamma=gamma, dx=float(ref_header.dx), dy=float(ref_header.dy)
    )
    return write_outputs(out, rows, solver=solver, profile=profile, git_commit=commit, figures=figures)


def resolve_output_dir(path: pathlib.Path | None, solver: str) -> pathlib.Path:
    solver = _normalise_solver(solver)
    if path is None:
        if solver == "hll":
            return DEFAULT_OUT
        return DEFAULT_OUT.with_name(f"{DEFAULT_OUT.name}_{solver}")
    return path if path.is_absolute() else ROOT / path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=None)
    parser.add_argument("--solver", choices=SUPPORTED_SOLVERS, default="hll")
    parser.add_argument("--profile", choices=tuple(PROFILES), default="gate")
    parser.add_argument("--keep-grids", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    packet = resolve_output_dir(args.out, args.solver) / PROFILES[_normalise_profile(args.profile)]["subdir"]
    payload = run_deterministic(
        packet,
        solver=args.solver,
        profile=args.profile,
        keep_grids=args.keep_grids,
    )
    print(packet / "summary.md")
    return 0 if payload["gates"]["G0_anchor"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run all smoke tests**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_orszag_tang_precision_smoke.py -q
```

Expected: `8 passed`.

- [ ] **Step 5: Commit**

```powershell
git add scripts/regression/mhd_orszag_tang_precision_smoke.py tests/py/test_mhd_orszag_tang_precision_smoke.py
git commit -m "feat(mhd): solver-aware Orszag-Tang deterministic precision packets"
```

---

### Task 5: Week-15 Evidence Run

**Files:**
- Generated evidence under `experiments/week15/orszag_tang_precision_smoke/` and `experiments/week15/orszag_tang_precision_smoke_hlld/`.

**Interfaces:**
- Consumes: the Task-4 CLI, the Task-3 sampler CLI, `tests/cases/orszag_tang_2d/orszag_tang_mca64.cfg`.

- [ ] **Step 1: Force clean builds (stale-binary pitfall)**

From a console with the VS dev environment loaded (`call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64`, INDEX §4):

```powershell
Get-ChildItem build-matrix -Directory | Where-Object { $_.Name -match '^cpu-(double|float)-(O2|Ofast)-ieee-(leq|strict)$' } | Remove-Item -Recurse -Force -Confirm:$false
```

Expected: the 8 P0 variant dirs are gone; `run_deterministic` reconfigures and rebuilds them from clean, so ninja header-dep tracking is regenerated (INDEX §7).

- [ ] **Step 2: Run both gate packets first (fail fast), then both headline packets**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_orszag_tang_precision_smoke.py --solver hll --profile gate
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_orszag_tang_precision_smoke.py --solver hlld --profile gate
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_orszag_tang_precision_smoke.py --solver hll --profile headline
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_orszag_tang_precision_smoke.py --solver hlld --profile headline
```

Expected (each command exits 0 and prints its packet summary):

```text
experiments\week15\orszag_tang_precision_smoke\gate128\summary.md
experiments\week15\orszag_tang_precision_smoke_hlld\gate128\summary.md
experiments\week15\orszag_tang_precision_smoke\headline256\summary.md
experiments\week15\orszag_tang_precision_smoke_hlld\headline256\summary.md
```

A non-zero exit means the G0 anchor gate failed — stop and investigate (fresh build? cfg drift vs the follow-up?); do not loosen `OT_ANCHOR_DIVB_RTOL` or the exact-steps rule. Headline runs take ~1–3 min per variant (806–812 steps at 256²); total deterministic wall time ~30–50 min.

- [ ] **Step 3: Run Docker Verificarlo MCA for both solvers**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/verificarlo/mhd_precision_sampling.py --case tests/cases/orszag_tang_2d/orszag_tang_mca64.cfg --out experiments/week15/orszag_tang_precision_smoke/mca --samples 3 --solver hll --experiment week15-mhd-mca --image verificarlo/verificarlo:cmake
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/verificarlo/mhd_precision_sampling.py --case tests/cases/orszag_tang_2d/orszag_tang_mca64.cfg --out experiments/week15/orszag_tang_precision_smoke_hlld/mca --samples 3 --solver hlld --experiment week15-mhd-mca --image verificarlo/verificarlo:cmake
```

Expected: each prints its `mca\summary.json` path; `p53`/`p24` blocks report `completed` with `n=3` (this image produced the 2026-07-06 HLLD pilot MCA evidence; `floatpoint-verificarlo-cmake:week14` is the fallback image). If Docker is unavailable, the blocks record `blocked_environment` — a valid outcome, but rerun with Docker before calling the packet supervisor-ready.

- [ ] **Step 4: Verify gates, MCA status, and transient-grid hygiene**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -c "import json,pathlib
for name in ('orszag_tang_precision_smoke','orszag_tang_precision_smoke_hlld'):
    root = pathlib.Path('experiments/week15')/name
    for profile in ('gate128','headline256'):
        s = json.loads((root/profile/'summary.json').read_text(encoding='utf-8'))
        print(name, profile, s['solver'], 'G0', s['gates']['G0_anchor']['pass'], 'rows', len(s['rows']),
              'finite', all(r['finite'] for r in s['rows']))
    m = json.loads((root/'mca/summary.json').read_text(encoding='utf-8'))
    print(name, 'mca', m['mca']['p53']['status'], m['mca']['p24']['status'])"
Get-ChildItem -Path experiments\week15 -Recurse -Include *.bin
```

Expected:

```text
orszag_tang_precision_smoke gate128 hll G0 True rows 8 finite True
orszag_tang_precision_smoke headline256 hll G0 True rows 8 finite True
orszag_tang_precision_smoke mca completed completed
orszag_tang_precision_smoke_hlld gate128 hlld G0 True rows 8 finite True
orszag_tang_precision_smoke_hlld headline256 hlld G0 True rows 8 finite True
orszag_tang_precision_smoke_hlld mca completed completed
```

and no `.bin` files listed. Also sanity-read the numbers: fp32 rows should sit orders of magnitude above the fp64 rows (Brio-Wu showed ~1e-6 vs ~1e-15); `p24` spread must be clearly separated from `p53`; and note the `leq`-vs-`strict` deltas per solver (spec §6: any nonzero HLLD 2D result is new signal, a zero result is a legitimate negative finding).

- [ ] **Step 5: Run the full Python suite**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py -q
```

Expected: all tests pass.

- [ ] **Step 6: Force-add evidence and commit**

```powershell
git add -f experiments/week15/orszag_tang_precision_smoke experiments/week15/orszag_tang_precision_smoke_hlld
git commit -m "test(mhd): Week-15 solver-aware Orszag-Tang precision-smoke evidence"
```

(`.bin` grids were already verified absent in Step 4; never commit them.)

---

### Task 6: Docs Registration and Superseded-Plan Banner

**Files:**
- Modify: `docs/superpowers/plans/2026-07-02-week15-ot-2d-precision-smoke.md`
- Modify: `scripts/regression/README.md`
- Modify: `docs/INDEX.md`

- [ ] **Step 1: Mark the 2026-07-02 plan as superseded**

In `docs/superpowers/plans/2026-07-02-week15-ot-2d-precision-smoke.md`, insert directly under the H1 title line:

```markdown
> **SUPERSEDED (2026-07-08):** replaced by
> [2026-07-08-week15-ot-2d-solver-aware-precision-smoke.md](2026-07-08-week15-ot-2d-solver-aware-precision-smoke.md)
> (spec: [2026-07-08-week15-ot-2d-precision-design.md](../specs/2026-07-08-week15-ot-2d-precision-design.md)).
> Written before the 2026-07-06 HLLD div(B) follow-up cleared HLLD; its
> HLL-only constraint and its sampler `--case` task no longer match the code.
> Do not execute this plan.
```

- [ ] **Step 2: Register the smoke driver in `scripts/regression/README.md`**

In the "Report 2 MHD Validation" section, after the `mhd_paper_style_mk2005.py` entry, add:

```markdown
- `mhd_orszag_tang_precision_smoke.py`: Week-15 solver-aware Orszag-Tang 2D
  precision packets (`--solver hll|hlld` × `--profile gate|headline`):
  deterministic P0 build fan vs the same-solver fp64 reference with an anchor
  gate from the HLLD div(B) follow-up; MCA recorded separately via
  `scripts/verificarlo/mhd_precision_sampling.py --case`.
```

- [ ] **Step 3: Register the evidence directory in `docs/INDEX.md` §6**

Add a row to the "Data products map" table, directly below the `experiments/week14/mhd_precision_pilot/` row:

```markdown
| `experiments/week15/orszag_tang_precision_smoke[_hlld]/` | Week-15 solver-aware OT 2D precision packets: per-solver `gate128/` + `headline256/` deterministic fans vs same-solver fp64 reference with G0 anchor gates (gate: steps=76, divB_max 1.173/1.085; headline: steps=806/812, divB_max 3.72/24.45), Docker Verificarlo MCA (64², t=0.05, n=3), unified `summary.{csv,json,md}` + figures |
```

- [ ] **Step 4: Commit**

```powershell
git add docs/superpowers/plans/2026-07-02-week15-ot-2d-precision-smoke.md scripts/regression/README.md docs/INDEX.md
git commit -m "docs(week15): register OT precision packets, supersede the 2026-07-02 plan"
```

---

## Final Reporting

After Task 6, report to the user:

- The five Task-1 landing commits (solver axis, HLLD pilot evidence, MK2005 figures, ladder fix, docs) plus the feature and evidence commits.
- All four packet summary paths and their G0 anchor-gate results (steps, divB_max vs the anchors).
- Max deterministic `Linf(rho)` / `Linf(By)` per (solver, profile), split fp32 vs fp64, and the `leq`-vs-`strict` deltas per solver — call out the HLLD interior-tie `strict` rows specifically (8b91e51 made that axis real for HLLD; any nonzero 2D delta is new, report-worthy signal; a zero result is a legitimate negative finding).
- MCA `p53`/`p24` status, sample counts, and `spread_rho` per solver; flag whether `p24` sits ~2⁻²⁴-like above `p53` as in Week 14.
- Explicit interpretation boundary: CPU-only OT packets; no GPU, no 512² convergence, no KH, no temporal-divergence claims. HLL remains the production default; HLLD is a studied axis.
- Deferred Week-16 candidates for the supervisor: KH 2D packet, 512² convergence gate, GPU MHD (overall.md hardware axis, still unstarted), temporal divergence/Lyapunov (overall.md Week 16).

Plan complete.
