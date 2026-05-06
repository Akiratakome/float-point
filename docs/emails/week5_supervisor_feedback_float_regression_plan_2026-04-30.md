# Supervisor Feedback — Float-vs-Double Regression Metric Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Origin:** Standalone plan from Philip's email (2026-04-30) — NOT scoped to any week. Driven by the supervisor's three asks:
1. Change the regression numerator from `||sim − exact||` to `||float − double||`.
2. Use a single highest-precision exact reference (no separate `exact_f` / `exact_d`).
3. In 2D, approximate "exact" by a higher-resolution run downsampled to the target grid.

**Goal:** Implement Philip's metric `||q_f − q_d||_1 / ||q_d − q_ref||_1` for both 1D and 2D float-regression, alongside a higher-precision rendering of the existing per-side metric, then compare the two methods on the same data and pick the keeper.

**Architecture:**
- 1D: bump stdout numeric precision in `run_convergence` so the existing per-side metric is no longer rounded to "1.000". Add an env-var-driven binary dump of the largest-resolution final grid for both float and double builds. Python report reads those binaries and computes Philip's metric, using the existing convergence CSV's `||double − exact||_1` as the denominator.
- 2D: pure Python addition to the report — read the existing `float_NNN.bin` / `double_NNN.bin` pairs and the `reference_800.bin`; compute `||f − d||_1` on the candidate grid, normalize by `||d − ref↓||_1` from the existing downsample machinery.
- Decision artifact: a brief markdown comparing both metrics on the produced data, recommending which to keep.

**Tech Stack:** C++17 HRSC solver (`src/main.cpp`, `src/utils/io.hpp`), Python 3 (numpy, no scipy), bash, the existing report pipeline at [scripts/regression/float_regression_report.py](scripts/regression/float_regression_report.py), pytest tests under [tests/py/](tests/py/).

---

## File Structure

**Create:**
- `tests/py/test_float_regression_report.py` — unit tests for the report script (1D Philip metric, 2D Philip metric, high-precision rendering).
- `docs/emails/week5_philip_feedback_method_comparison_2026-04-30.md` — decision artifact comparing both metrics on the produced data.

**Modify:**
- `src/main.cpp` — bump `setprecision(6)` → `setprecision(15)` in `run_convergence`; add env-var-driven binary dump of the final grid at the largest convergence resolution.
- `scripts/regression/float_regression_1d.sh` — export `HRSC_DUMP_DIR` and per-run `HRSC_DUMP_TAG` so the convergence runs also produce per-cell binary dumps.
- `scripts/regression/float_regression_report.py` — `_report_1d` reads the new binaries, computes Philip's metric, renders both metrics with full precision; `_report_2d` adds Philip's float-vs-double metric per resolution.

**Untouched:** the 2D bash script and 2D cfg files — the existing artefacts already include everything needed.

---

## Task 1: Bump 1D convergence stdout precision

**Files:**
- Modify: [src/main.cpp:136](src/main.cpp#L136)

The current `setprecision(6)` is the proximate cause of every 1D `d/f` ratio printing as `1.000`. Sufficient digits expose the real difference even before the metric itself is changed.

- [ ] **Step 1: Edit `src/main.cpp:136`**

Change:

```cpp
    std::cout << std::setprecision(6) << std::scientific;
```

to:

```cpp
    std::cout << std::setprecision(15) << std::scientific;
```

- [ ] **Step 2: Build both precisions**

Run:

```bash
cmake --build build-double -j
cmake --build build-float -j
```

Expected: both succeed.

- [ ] **Step 3: Re-run the 1D regression bash script**

Run:

```bash
bash scripts/regression/float_regression_1d.sh
```

Expected: `experiments/week4/float_regression/1d/sod_double.csv` now shows ~15 significant digits per column.

- [ ] **Step 4: Eyeball the new summary**

Run:

```bash
cat experiments/week4/float_regression/1d/summary.md
```

Expected: at least some `d/f` ratios deviate from `1.000` once rendered with finer precision (the report script's own `:.3f` will still flatten — the Python rendering bump comes in Task 6, but the underlying CSV must already carry the real digits before that step is meaningful). Confirm the CSV content has the digits (the summary table view will be widened in Task 6).

- [ ] **Step 5: Commit**

```bash
git add src/main.cpp experiments/week4/float_regression/1d
git commit -m "feat(solver): bump 1D convergence stdout to 15 sig figs

Surfaces the float/double divergence that was being rounded to 1.000
in the regression summary."
```

---

## Task 2: Add env-var-driven binary dump of the final grid in `run_convergence`

**Files:**
- Modify: [src/main.cpp:118-191](src/main.cpp#L118-L191)

Drive the dump from environment variables (`HRSC_DUMP_DIR`, `HRSC_DUMP_TAG`) so the 1D bash script can request per-precision outputs without having to maintain N separate cfg files. We dump only the largest convergence resolution (the one that the report already reduces to `N_last`).

- [ ] **Step 1: Add the includes if missing**

At the top of `src/main.cpp`, ensure `<cstdlib>` (for `std::getenv`) and `"utils/io.hpp"` (for `write_binary`) are included. Inspect the current top-of-file; add the missing include only if it is not already present.

- [ ] **Step 2: Capture the largest resolution before the loop**

Inside `run_convergence`, just after `auto resolutions = cfg.get_int_list("resolutions");`, add:

```cpp
    if (resolutions.empty()) {
        throw std::runtime_error("convergence: resolutions list is empty");
    }
    int largest_nx = *std::max_element(resolutions.begin(), resolutions.end());
```

Make sure `<algorithm>` is included near the top of the file (add it if it is not already there).

- [ ] **Step 3: After the per-resolution norm computation, dump the largest grid**

Inside the `for (int nx : resolutions)` loop, immediately after the `std::cout << ... << err_p.Linf << "\n";` line and before the closing `}` of the loop body, add:

```cpp
        if (nx == largest_nx) {
            const char* dump_dir = std::getenv("HRSC_DUMP_DIR");
            const char* dump_tag = std::getenv("HRSC_DUMP_TAG");
            if (dump_dir && dump_tag && dump_dir[0] && dump_tag[0]) {
                std::string path = std::string(dump_dir) + "/" + test
                                 + "_" + dump_tag + "_grid.bin";
                write_binary<Real, EulerNVars>(
                    path, solver.grid_view(),
                    nx, 1,
                    static_cast<Real>(dx), static_cast<Real>(dx),
                    static_cast<Real>(solver.time()));
                std::cerr << "[dump] wrote " << path << "\n";
            }
        }
```

This re-uses the same `write_binary` helper that `run_normal` and the 2D path already use, so `scripts/io_helper.read_binary` will read the new files without modification.

- [ ] **Step 4: Build both precisions**

```bash
cmake --build build-double -j
cmake --build build-float -j
```

Expected: both succeed.

- [ ] **Step 5: Smoke-test the dump path manually**

```bash
mkdir -p /tmp/hrsc_dump_smoke
HRSC_DUMP_DIR=/tmp/hrsc_dump_smoke HRSC_DUMP_TAG=double \
    build-double/hrsc tests/cases/toro_1d/convergence_sod.cfg > /dev/null
ls -la /tmp/hrsc_dump_smoke/sod_double_grid.bin
HRSC_DUMP_DIR=/tmp/hrsc_dump_smoke HRSC_DUMP_TAG=float \
    build-float/hrsc tests/cases/toro_1d/convergence_sod.cfg > /dev/null
ls -la /tmp/hrsc_dump_smoke/sod_float_grid.bin
python3 -c "
import sys
sys.path.insert(0, 'scripts')
from io_helper import read_binary
hd, cd = read_binary('/tmp/hrsc_dump_smoke/sod_double_grid.bin')
hf, cf = read_binary('/tmp/hrsc_dump_smoke/sod_float_grid.bin')
print('double:', hd.nx, hd.ny, hd.precision_tag, cd.shape, cd.dtype)
print('float :', hf.nx, hf.ny, hf.precision_tag, cf.shape, cf.dtype)
assert hd.nx == 800 and hf.nx == 800
assert hd.precision_tag == 8 and hf.precision_tag == 4
"
```

Expected: both files exist, header reports `nx=800, ny=1`, dtypes are float64 and float32 respectively.

- [ ] **Step 6: Sanity check — no env vars means no dump**

```bash
rm -rf /tmp/hrsc_dump_smoke_noenv
mkdir -p /tmp/hrsc_dump_smoke_noenv
unset HRSC_DUMP_DIR
unset HRSC_DUMP_TAG
build-double/hrsc tests/cases/toro_1d/convergence_sod.cfg > /dev/null
ls /tmp/hrsc_dump_smoke_noenv
```

Expected: directory is empty — the dump path is opt-in.

- [ ] **Step 7: Commit**

```bash
git add src/main.cpp
git commit -m "feat(solver): env-var-driven binary dump of largest convergence grid

HRSC_DUMP_DIR + HRSC_DUMP_TAG opt the convergence runner into writing
the final-state primitive grid at the coarsest resolution loop pass.
Used by the upcoming float-vs-double Philip-metric pipeline."
```

---

## Task 3: Wire the 1D bash script to request per-precision dumps

**Files:**
- Modify: [scripts/regression/float_regression_1d.sh](scripts/regression/float_regression_1d.sh)

- [ ] **Step 1: Add env-var-driven dump exports around each binary invocation**

In the `for test in "${TESTS[@]}"` loop, change the two execution lines from:

```bash
    "$BUILD_DOUBLE" "$cfg" > "${OUT_DIR}/${test}_double.csv"
    "$BUILD_FLOAT" "$cfg" > "${OUT_DIR}/${test}_float.csv"
```

to:

```bash
    HRSC_DUMP_DIR="$OUT_DIR" HRSC_DUMP_TAG="double" \
        "$BUILD_DOUBLE" "$cfg" > "${OUT_DIR}/${test}_double.csv"
    HRSC_DUMP_DIR="$OUT_DIR" HRSC_DUMP_TAG="float" \
        "$BUILD_FLOAT" "$cfg" > "${OUT_DIR}/${test}_float.csv"
```

- [ ] **Step 2: Re-run the 1D pipeline end-to-end**

```bash
bash scripts/regression/float_regression_1d.sh
```

Expected: stderr lines `[dump] wrote experiments/week4/float_regression/1d/sod_double_grid.bin` etc., one pair per test.

- [ ] **Step 3: Verify all 12 dump files (6 tests × 2 precisions) exist**

```bash
ls experiments/week4/float_regression/1d/*_grid.bin | wc -l
```

Expected: `12`.

- [ ] **Step 4: Commit**

```bash
git add scripts/regression/float_regression_1d.sh \
        experiments/week4/float_regression/1d/*_grid.bin
git commit -m "feat(regression): 1D bash dumps per-precision final grid

Sets HRSC_DUMP_DIR and HRSC_DUMP_TAG so each convergence run also
emits the largest-resolution primitive grid, which the report script
will read to compute the float-vs-double Philip metric."
```

---

## Task 4: Test fixtures for the report script

**Files:**
- Create: `tests/py/test_float_regression_report.py`

Set up a tmp-dir-per-test pattern that fabricates both a fake convergence CSV and a fake binary grid, so the report script can be exercised hermetically. We will add the actual Philip-metric assertions in Tasks 5 and 7.

- [ ] **Step 1: Write the failing test (1D wiring sanity)**

Create `tests/py/test_float_regression_report.py`:

```python
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "regression"))

import float_regression_report as frr  # noqa: E402  (after sys.path tweak)
from io_helper import IDX_RHO, IDX_E, IDX_RHOU, IDX_RHOV  # noqa: E402


def _write_convergence_csv(path: Path, nx_last: int, l1_rho: float) -> None:
    header = (
        "# N        dx            L1_rho        L2_rho        Linf_rho      "
        "L1_u          L2_u          Linf_u        L1_p          L2_p          Linf_p\n"
    )
    body = (
        f"{nx_last}  1e-3  {l1_rho:.15e}  2e-3  3e-3  "
        f"4e-3  5e-3  6e-3  7e-3  8e-3  9e-3\n"
    )
    path.write_text(header + body, encoding="utf-8")


def _write_grid_bin(path: Path, nx: int, dtype: np.dtype, rho_value: float, gamma: float = 1.4) -> None:
    """Write an HRSC binary with constant primitive state (rho=rho_value, u=v=0, p=1.0)."""
    p = 1.0
    e_internal = p / (gamma - 1.0)
    cons = np.zeros((1, nx, 4), dtype=dtype)
    cons[..., IDX_RHO] = rho_value
    cons[..., IDX_RHOU] = 0.0
    cons[..., IDX_RHOV] = 0.0
    cons[..., IDX_E] = e_internal  # rho * (0.5*v^2 + e_internal/rho); v=0 so just e_internal
    precision_tag = 8 if dtype == np.float64 else 4
    header = struct.pack("<4siiiidddd20s",
                         b"HRSC", nx, 1, 4, precision_tag,
                         0.0, 1.0 / nx, 1.0 / nx, b"\x00" * 20)
    assert len(header) == 64, len(header)
    with open(path, "wb") as f:
        f.write(header)
        f.write(cons.tobytes(order="C"))


def test_1d_report_pipeline_runs(tmp_path: Path) -> None:
    """The 1D report runs end-to-end against fabricated CSV + grid pairs."""
    for test in frr.TESTS_1D:
        _write_convergence_csv(tmp_path / f"{test}_double.csv", nx_last=800, l1_rho=1.0)
        _write_convergence_csv(tmp_path / f"{test}_float.csv",  nx_last=800, l1_rho=1.0)
        _write_grid_bin(tmp_path / f"{test}_double_grid.bin", 800, np.float64, rho_value=1.0)
        _write_grid_bin(tmp_path / f"{test}_float_grid.bin",  800, np.float32, rho_value=1.0)

    summary = frr._report_1d(tmp_path)
    assert summary["mode"] == "1d"
    assert (tmp_path / "summary.md").is_file()
    assert (tmp_path / "summary.json").is_file()
```

- [ ] **Step 2: Run it — expect failure**

Run:

```bash
pytest tests/py/test_float_regression_report.py -v
```

Expected: this should currently PASS (the existing `_report_1d` does not yet require grid binaries) — verifying the harness is wired. If it FAILs because of a path/import problem, fix the import wiring before moving on. Note the result and proceed.

- [ ] **Step 3: Commit the harness**

```bash
git add tests/py/test_float_regression_report.py
git commit -m "test(regression): scaffold report-script test harness

Fabricates convergence CSVs and HRSC binary grids per case so the
1D and 2D report code paths can be exercised hermetically."
```

---

## Task 5: Compute Philip's metric in `_report_1d`

**Files:**
- Modify: [scripts/regression/float_regression_report.py](scripts/regression/float_regression_report.py)
- Modify: `tests/py/test_float_regression_report.py`

The denominator `||d − exact||_1` is taken from the existing convergence CSV (final row `L1_rho`, `L1_u`, `L1_p`). The numerator `||f − d||_1` is computed from the new grid binaries. Both metrics live in the summary side-by-side so we can compare in Task 8.

- [ ] **Step 1: Write the failing test for the new metric**

Append to `tests/py/test_float_regression_report.py`:

```python
def test_1d_report_emits_philip_metric(tmp_path: Path) -> None:
    """Numerator ||f-d|| and ratio ||f-d||/||d-exact|| appear in summary.json."""
    test = "sod"
    # 800 cells, dx=1/800: the float grid differs from double by 1e-7 in rho everywhere.
    nx = 800
    dx = 1.0 / nx
    _write_convergence_csv(tmp_path / f"{test}_double.csv", nx_last=nx, l1_rho=1.0e-3)
    _write_convergence_csv(tmp_path / f"{test}_float.csv",  nx_last=nx, l1_rho=1.0e-3)
    _write_grid_bin(tmp_path / f"{test}_double_grid.bin", nx, np.float64, rho_value=1.0)
    _write_grid_bin(tmp_path / f"{test}_float_grid.bin",  nx, np.float32, rho_value=1.0 + 1.0e-7)
    # Stub the other tests with identical pairs so _report_1d does not raise.
    for other in [t for t in frr.TESTS_1D if t != test]:
        _write_convergence_csv(tmp_path / f"{other}_double.csv", 800, 1.0e-3)
        _write_convergence_csv(tmp_path / f"{other}_float.csv",  800, 1.0e-3)
        _write_grid_bin(tmp_path / f"{other}_double_grid.bin", 800, np.float64, 1.0)
        _write_grid_bin(tmp_path / f"{other}_float_grid.bin",  800, np.float32, 1.0)

    summary = frr._report_1d(tmp_path)
    sod = summary["tests"][test]
    # ||f - d||_1 ≈ 1e-7 * (nx*dx) = 1e-7 * 1.0 = 1.0e-7 for rho.
    assert sod["philip"]["L1_rho_fmd"] == pytest.approx(1.0e-7, rel=1e-3)
    # ratio = ||f-d||_1 / ||d - exact||_1 = 1e-7 / 1e-3 = 1e-4.
    assert sod["philip"]["L1_rho_ratio"] == pytest.approx(1.0e-4, rel=1e-3)
```

- [ ] **Step 2: Run — expect failure on the missing `philip` key**

```bash
pytest tests/py/test_float_regression_report.py::test_1d_report_emits_philip_metric -v
```

Expected: KeyError on `summary["tests"]["sod"]["philip"]`.

- [ ] **Step 3: Implement Philip's 1D metric in the report**

Edit `scripts/regression/float_regression_report.py`. Add a helper near the top (under `_safe_ratio`):

```python
def _l1_norm_diff(a: np.ndarray, b: np.ndarray, dx: float) -> float:
    return float(np.sum(np.abs(a - b)) * dx)


def _read_grid_primitive(path: Path, gamma: float) -> tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    """Return (dx, rho, u, p) from a 1D HRSC binary (ny == 1)."""
    header, cons = read_binary(path)
    if header.ny != 1:
        raise ValueError(f"{path}: expected 1D dump (ny=1), got ny={header.ny}")
    cons_f64 = cons.astype(np.float64)
    prim = cons_to_prim(cons_f64, gamma)
    rho = prim[0, :, 0]
    u   = prim[0, :, 1]
    p   = prim[0, :, 3]
    return float(header.dx), rho, u, p
```

Update the imports at the top of the file to bring `read_binary`, `cons_to_prim` (already imported) into the same scope as the helpers above.

In `_report_1d`, inside the `for test in TESTS_1D:` loop, after the existing `ratios = { ... }` block and before assigning into `per_test[test]`, add:

```python
        gamma = 1.4  # all 1D Toro/Sod cases use gamma = 1.4; matches the cfgs.
        gd = input_dir / f"{test}_double_grid.bin"
        gf = input_dir / f"{test}_float_grid.bin"
        if not gd.is_file() or not gf.is_file():
            raise FileNotFoundError(f"Missing grid pair for {test}: {gd} / {gf}")
        dx_d, rho_d, u_d, p_d = _read_grid_primitive(gd, gamma)
        dx_f, rho_f, u_f, p_f = _read_grid_primitive(gf, gamma)
        if rho_d.shape != rho_f.shape:
            raise ValueError(
                f"Grid shape mismatch for {test}: {rho_d.shape} vs {rho_f.shape}")
        if abs(dx_d - dx_f) > 1e-12:
            raise ValueError(f"dx mismatch for {test}: {dx_d} vs {dx_f}")
        philip = {
            "L1_rho_fmd": _l1_norm_diff(rho_f, rho_d, dx_d),
            "L1_u_fmd":   _l1_norm_diff(u_f,   u_d,   dx_d),
            "L1_p_fmd":   _l1_norm_diff(p_f,   p_d,   dx_d),
            "L1_rho_ratio": _safe_ratio(_l1_norm_diff(rho_f, rho_d, dx_d), r_double["L1_rho"]),
            "L1_u_ratio":   _safe_ratio(_l1_norm_diff(u_f,   u_d,   dx_d), r_double["L1_u"]),
            "L1_p_ratio":   _safe_ratio(_l1_norm_diff(p_f,   p_d,   dx_d), r_double["L1_p"]),
        }
```

Then extend the `per_test[test]` dict with `"philip": philip,` as a new key alongside `"ratio_float_over_double"`.

- [ ] **Step 4: Run the test — expect PASS**

```bash
pytest tests/py/test_float_regression_report.py::test_1d_report_emits_philip_metric -v
```

Expected: PASS.

- [ ] **Step 5: Run on real data**

```bash
python3 scripts/regression/float_regression_report.py --mode 1d \
    --input experiments/week4/float_regression/1d
```

Expected: stdout JSON shows a `"philip"` block per test with `L1_rho_ratio` near 1e-5 to 1e-6 (Philip's predicted magnitude).

- [ ] **Step 6: Commit**

```bash
git add scripts/regression/float_regression_report.py \
        tests/py/test_float_regression_report.py \
        experiments/week4/float_regression/1d/summary.json
git commit -m "feat(regression): compute Philip's 1D float-vs-double metric

Adds ||f - d||_1 from the new grid dumps and the ratio against the
double-vs-exact convergence-CSV norm. Both metrics live in summary.json
side-by-side so we can compare them before deciding."
```

---

## Task 6: Render both metrics with full precision in the 1D summary table

**Files:**
- Modify: [scripts/regression/float_regression_report.py:115-119](scripts/regression/float_regression_report.py#L115-L119)
- Modify: `tests/py/test_float_regression_report.py`

The current Markdown table uses `:.3f` for the legacy ratio, hiding the variation we now want to see; we also want Philip's ratio in the table.

- [ ] **Step 1: Failing test on summary.md content**

Append to `tests/py/test_float_regression_report.py`:

```python
def test_1d_summary_md_renders_high_precision_and_philip(tmp_path: Path) -> None:
    nx = 800
    for test in frr.TESTS_1D:
        _write_convergence_csv(tmp_path / f"{test}_double.csv", nx, 1.0e-3)
        _write_convergence_csv(tmp_path / f"{test}_float.csv",  nx, 1.0e-3)
        _write_grid_bin(tmp_path / f"{test}_double_grid.bin", nx, np.float64, 1.0)
        _write_grid_bin(tmp_path / f"{test}_float_grid.bin",  nx, np.float32, 1.0 + 1.0e-7)

    frr._report_1d(tmp_path)
    md = (tmp_path / "summary.md").read_text(encoding="utf-8")
    # Legacy ratio shown with at least 6 decimal digits, not 3.
    assert "L1_rho d/f" in md
    # Philip's column header is present.
    assert "L1_rho fmd/d_err" in md
    # Philip ratio for sod is rendered in scientific notation, not "1.000".
    sod_line = next(line for line in md.splitlines() if line.startswith("| sod "))
    assert "1.000" not in sod_line  # legacy column, no longer rounded to identity
```

- [ ] **Step 2: Run — expect failure on missing column header**

```bash
pytest tests/py/test_float_regression_report.py::test_1d_summary_md_renders_high_precision_and_philip -v
```

Expected: FAIL on the `L1_rho fmd/d_err` assertion.

- [ ] **Step 3: Replace the markdown table builder in `_report_1d`**

Replace the `md_lines = [` block and the `md_lines.append(f"| {test} | ..."` row with:

```python
    md_lines = [
        "# Float vs Double Regression (1D)",
        "",
        "Two metrics per test are reported side-by-side:",
        "",
        "- **legacy d/f**: `||float - exact||_p / ||double - exact||_p` (the original ratio).",
        "- **philip fmd/d_err**: `||float - double||_1 / ||double - exact||_1` (supervisor 2026-04-30).",
        "",
        "| test | N_last | L1_rho d/f | L2_rho d/f | Linf_rho d/f | L1_u d/f | L2_u d/f | Linf_u d/f | L1_p d/f | L2_p d/f | Linf_p d/f | L1_rho fmd/d_err | L1_u fmd/d_err | L1_p fmd/d_err |",
        "|------|-------:|-----------:|-----------:|-------------:|---------:|---------:|-----------:|---------:|---------:|-----------:|-----------------:|---------------:|---------------:|",
    ]
```

And the per-row append becomes:

```python
        md_lines.append(
            f"| {test} | {r_double['N']} | "
            f"{ratios['L1_rho_ratio']:.6e} | {ratios['L2_rho_ratio']:.6e} | {ratios['Linf_rho_ratio']:.6e} | "
            f"{ratios['L1_u_ratio']:.6e} | {ratios['L2_u_ratio']:.6e} | {ratios['Linf_u_ratio']:.6e} | "
            f"{ratios['L1_p_ratio']:.6e} | {ratios['L2_p_ratio']:.6e} | {ratios['Linf_p_ratio']:.6e} | "
            f"{philip['L1_rho_ratio']:.6e} | {philip['L1_u_ratio']:.6e} | {philip['L1_p_ratio']:.6e} |"
        )
```

- [ ] **Step 4: Run — expect PASS**

```bash
pytest tests/py/test_float_regression_report.py -v
```

Expected: all 1D tests pass.

- [ ] **Step 5: Re-run on real data**

```bash
python3 scripts/regression/float_regression_report.py --mode 1d \
    --input experiments/week4/float_regression/1d
cat experiments/week4/float_regression/1d/summary.md
```

Expected: the markdown table shows fine-grained legacy ratios (no longer all `1.000`) and the new Philip column with values around 1e-5 to 1e-6.

- [ ] **Step 6: Commit**

```bash
git add scripts/regression/float_regression_report.py \
        tests/py/test_float_regression_report.py \
        experiments/week4/float_regression/1d/summary.md \
        experiments/week4/float_regression/1d/summary.json
git commit -m "feat(regression): render legacy + Philip metric side-by-side (1D)

Bumps the legacy d/f column from 3 decimal places to 6-significant-digit
scientific so the rounding to 1.000 disappears, and adds the Philip
||f-d||/||d-exact|| ratio per test."
```

---

## Task 7: Compute Philip's metric in `_report_2d`

**Files:**
- Modify: [scripts/regression/float_regression_report.py:126-206](scripts/regression/float_regression_report.py#L126-L206)
- Modify: `tests/py/test_float_regression_report.py`

For each resolution (200, 400) we already have float and double binaries on the same grid. The denominator `||d − ref↓||_1` is already computed by `compare_candidate_to_reference` for the double cases — we re-use that value rather than recomputing.

- [ ] **Step 1: Failing test**

Append to `tests/py/test_float_regression_report.py`:

```python
def _write_2d_grid_bin(path: Path, nx: int, ny: int, dtype: np.dtype,
                       rho_value: float, gamma: float = 1.4) -> None:
    p = 1.0
    e_internal = p / (gamma - 1.0)
    cons = np.zeros((ny, nx, 4), dtype=dtype)
    cons[..., IDX_RHO] = rho_value
    cons[..., IDX_E]   = e_internal
    precision_tag = 8 if dtype == np.float64 else 4
    header = struct.pack("<4siiiidddd20s",
                         b"HRSC", nx, ny, 4, precision_tag,
                         0.0, 1.0 / nx, 1.0 / ny, b"\x00" * 20)
    with open(path, "wb") as f:
        f.write(header)
        f.write(cons.tobytes(order="C"))


def test_2d_report_emits_philip_metric(tmp_path: Path) -> None:
    # ref = 1.0 everywhere; double_200 = 1.0; float_200 = 1.0 + 1e-6 → ||f-d||_1 = 1e-6.
    _write_2d_grid_bin(tmp_path / "reference_800.bin", 800, 800, np.float64, 1.0)
    _write_2d_grid_bin(tmp_path / "double_200.bin",   200, 200, np.float64, 1.0)
    _write_2d_grid_bin(tmp_path / "float_200.bin",    200, 200, np.float32, 1.0 + 1.0e-6)
    _write_2d_grid_bin(tmp_path / "double_400.bin",   400, 400, np.float64, 1.0)
    _write_2d_grid_bin(tmp_path / "float_400.bin",    400, 400, np.float32, 1.0 + 1.0e-6)

    summary = frr._report_2d(tmp_path, gamma=1.4, smooth_sigma=0.5,
                              allow_ssim_fallback=True)
    fvd_200 = summary["cases"]["float_200"]["philip"]
    assert fvd_200["L1_rho_fmd"] == pytest.approx(1.0e-6, rel=1e-3)
    # ref ≡ double here, so ||d - ref↓||_1 = 0 → ratio is +inf by _safe_ratio.
    assert fvd_200["L1_rho_ratio"] == float("inf")
```

- [ ] **Step 2: Run — expect failure (`philip` key missing)**

```bash
pytest tests/py/test_float_regression_report.py::test_2d_report_emits_philip_metric -v
```

Expected: KeyError.

- [ ] **Step 3: Implement Philip's 2D metric**

In `_report_2d`, just after the `for label, cand_path in cases:` loop completes its existing per-case work (after `out_cases[label] = {...}` and before `md_lines.append(f"| {label} | ...")`), and *inside* the same iteration, additionally compute and store the Philip metric.

Restructure the loop so each iteration:
1. Reads the candidate (existing behavior).
2. Computes `compare_candidate_to_reference` (existing).
3. Computes `phase_metrics` (existing).
4. **New:** if the label is `float_NNN`, also pair it with `double_NNN` to compute `||f − d||_1` per primitive variable.
5. Stores everything in `out_cases[label]`.

Concretely, after the existing `out_cases[label] = { ... }` assignment, append:

```python
        philip_metrics: dict[str, float] = {}
        if label.startswith("float_"):
            res_tag = label.split("_", 1)[1]
            twin_label = f"double_{res_tag}"
            twin_path = input_dir / f"double_{res_tag}.bin"
            if not twin_path.is_file():
                raise FileNotFoundError(
                    f"Missing double twin for {label}: {twin_path}")
            _, twin_cons = read_binary(twin_path)
            twin_prim = cons_to_prim(twin_cons.astype(np.float64), gamma)
            cell_area = float(cand_header.dx * cand_header.dy)
            for var_name, idx in (("rho", 0), ("u", 1), ("v", 2), ("p", 3)):
                fmd = float(np.sum(np.abs(cand_prim[..., idx] - twin_prim[..., idx])) * cell_area)
                philip_metrics[f"L1_{var_name}_fmd"] = fmd
                # Denominator: the *double* twin's L1-vs-ref from the existing
                # downsample machinery -- avoids recomputation and keeps a
                # single definition of "approximation error".
                d_err = float(out_cases[twin_label]["downsample_metrics"][var_name]["L1"])  # type: ignore[index]
                philip_metrics[f"L1_{var_name}_ratio"] = _safe_ratio(fmd, d_err)
        out_cases[label]["philip"] = philip_metrics  # type: ignore[index]
```

This relies on the iteration order putting `double_NNN` before `float_NNN` for each resolution — which the existing `cases` list already does. Add a comment locking that contract:

Just above the `cases = [` line:

```python
    # Order matters: each "double_NNN" must precede its "float_NNN" twin so
    # the Philip metric can read the double's pre-computed L1-vs-ref denominator.
```

- [ ] **Step 4: Surface Philip's ratio in the 2D markdown table**

Replace the existing 2D header and per-row `md_lines.append(...)` to include three new columns. Update the header:

```python
    md_lines = [
        "# Float vs Double Regression (2D)",
        "",
        "**Two metrics per case:**",
        "",
        "- **L1_rho** etc.: `||candidate - reference_800↓||_1` (legacy: candidate vs downsampled high-res reference).",
        "- **L1_rho fmd/d_err**: `||float - double||_1 / ||double - reference_800↓||_1` (supervisor 2026-04-30; only populated for float_* rows).",
        "",
        "| case | L1_rho | L2_rho | Linf_rho | ssim_rho | delta_x_shock | delta_y_shock | L1_rho fmd/d_err | L1_u fmd/d_err | L1_p fmd/d_err |",
        "|------|-------:|-------:|---------:|---------:|--------------:|--------------:|-----------------:|---------------:|---------------:|",
    ]
```

And replace the row-append with:

```python
        philip = out_cases[label].get("philip", {})  # type: ignore[union-attr]
        def _f(key: str) -> str:
            v = philip.get(key)
            return f"{v:.6e}" if isinstance(v, (int, float)) and np.isfinite(v) else "—"
        md_lines.append(
            f"| {label} | {rho_norms['L1']:.6e} | {rho_norms['L2']:.6e} | {rho_norms['Linf']:.6e} | "
            f"{float(phase_metrics['ssim_rho']):.6f} | {float(phase_metrics['delta_x_shock']):.6e} | "
            f"{float(phase_metrics['delta_y_shock']):.6e} | "
            f"{_f('L1_rho_ratio')} | {_f('L1_u_ratio')} | {_f('L1_p_ratio')} |"
        )
```

- [ ] **Step 5: Run the new test — expect PASS**

```bash
pytest tests/py/test_float_regression_report.py::test_2d_report_emits_philip_metric -v
```

Expected: PASS.

- [ ] **Step 6: Re-run on real data**

```bash
python3 scripts/regression/float_regression_report.py --mode 2d \
    --input experiments/week4/float_regression/2d
cat experiments/week4/float_regression/2d/summary.md
```

Expected: the markdown shows the Philip ratio for each `float_NNN` row, em-dash for `double_NNN` rows.

- [ ] **Step 7: Commit**

```bash
git add scripts/regression/float_regression_report.py \
        tests/py/test_float_regression_report.py \
        experiments/week4/float_regression/2d/summary.md \
        experiments/week4/float_regression/2d/summary.json
git commit -m "feat(regression): compute Philip's 2D float-vs-double metric

Adds ||f - d||_1 per resolution and the ratio against the existing
||d - reference_800↓||_1 norm, populated on float_* rows."
```

---

## Task 8: Method-comparison decision artefact

**Files:**
- Create: `docs/emails/week5_philip_feedback_method_comparison_2026-04-30.md`

A short note that places both metrics' actual numbers side-by-side and recommends which becomes the canonical regression metric. This is the deliverable to send back to Philip.

- [ ] **Step 1: Re-read both summary files end-to-end**

```bash
cat experiments/week4/float_regression/1d/summary.md
cat experiments/week4/float_regression/2d/summary.md
```

Capture: per-test legacy ratios (now high-precision), per-test Philip ratios, and the per-resolution 2D Philip ratios. Note any anomalies (e.g. a Philip ratio above 1e-3 — that would be unexpected and worth flagging).

- [ ] **Step 2: Write the comparison document**

Create `docs/emails/week5_philip_feedback_method_comparison_2026-04-30.md`:

```markdown
# Float-vs-Double Regression: Method Comparison

**Date:** 2026-04-30
**Driver:** Philip's email of 2026-04-30 (typed-up version of in-meeting whiteboard).
**Status:** Decision proposal — pending supervisor sign-off.

## TL;DR

Recommendation: **adopt Philip's metric as the canonical pass/fail signal**, and keep the legacy per-side metric only as a secondary diagnostic in the same summary.

## What "legacy" means in this doc

`||sim_p − exact_p||_1` per precision p ∈ {float, double}, where the exact
solution is computed in double regardless of the simulator's working
precision (see `src/main.cpp::run_convergence`). The summary reports the
ratio `legacy_float / legacy_double`.

Failure mode observed: this ratio is dominated by the discretization
error and rounds to ~1 even when the float and double trajectories
differ at the rounding-error level. The numerator and denominator
move together because both simulations approximate the same exact.

## What "Philip" means in this doc

`||sim_float − sim_double||_1 / ||sim_double − exact||_1` (1D)
or `||sim_float − sim_double||_1 / ||sim_double − reference_800↓||_1` (2D).

The numerator measures the pure arithmetic-precision difference; the
denominator gives a magnitude reference (the discretization error of
double, the simulation we trust). The expected size is 1e-5 to 1e-6.

## Numbers (1D, N=800)

| test | legacy L1_rho ratio | Philip L1_rho ratio | comment |
|------|--------------------:|--------------------:|---------|
| sod                  | <fill from summary> | <fill from summary> | |
| toro2                | <fill>              | <fill>              | |
| toro3                | <fill>              | <fill>              | |
| toro4                | <fill>              | <fill>              | |
| toro5                | <fill>              | <fill>              | |
| stationary_contact   | <fill>              | <fill>              | |

## Numbers (2D, Liska-Wendroff config 3)

| resolution | legacy double L1_rho | legacy float L1_rho | Philip L1_rho ratio | comment |
|------------|---------------------:|--------------------:|--------------------:|---------|
| 200        | <fill>               | <fill>              | <fill>              | |
| 400        | <fill>               | <fill>              | <fill>              | |

## Why prefer Philip's metric

1. **It isolates what we are trying to measure.** Single vs double precision is an arithmetic question; the legacy ratio drowns it in O(Δx) discretization noise.
2. **It has a predictable expected magnitude.** ~1e-5 to 1e-6 for HLLC + RK; deviations are signal, not measurement noise.
3. **It still uses the same trusted reference solution as the legacy metric.** No new ground truth is introduced; only the numerator changes.

## Why keep the legacy metric in the summary anyway

Detects a different failure: if either build's discretization error grows abnormally relative to the other's, the legacy ratio departs from 1 and tells us that one build's *convergence behavior* (not just rounding) regressed. Cheap to keep, complements Philip's metric.

## Open questions for Philip

- For 2D, should the denominator use `||double − ref↓||_1` (current choice) or a smoothed version to avoid shock-region domination?
- Should we add an Linf variant of the Philip ratio for shock-localized regressions?
```

Fill the `<fill>` cells from the actual summary files before committing.

- [ ] **Step 3: Verify the doc renders and references are correct**

```bash
test -f docs/emails/week5_philip_feedback_method_comparison_2026-04-30.md
grep -c "<fill>" docs/emails/week5_philip_feedback_method_comparison_2026-04-30.md
```

Expected: file exists; grep returns `0` (all placeholders replaced).

- [ ] **Step 4: Commit**

```bash
git add docs/emails/week5_philip_feedback_method_comparison_2026-04-30.md
git commit -m "docs(supervisor): method comparison for Philip's metric

Side-by-side numbers from the 1D and 2D summaries, with the
recommendation to adopt the Philip metric as the canonical signal
while keeping the legacy ratio as a secondary diagnostic."
```

---

## Self-Review Notes

**Spec coverage:**
- Philip's three points: (1) numerator change → Tasks 5, 7. (2) single high-precision exact → already true in 1D (`exact_riemann_sample` is double-only inside `run_convergence`); 2D uses `reference_800.bin` which is a double build. Documented in Task 8. (3) 2D high-res downsampling → already in place (`reference_800.bin` + `compare_candidate_to_reference`). Verified in Task 7.
- User's "increase decimal precision on the current method" ask → Task 1 (C++ output) + Task 6 (Markdown rendering).
- User's "decide which method is better" ask → Task 8.

**Placeholder scan:** the only `<fill>` markers are inside the comparison-doc template at Task 8, and Step 2 explicitly requires the engineer to replace them before commit. No TBDs elsewhere.

**Type/name consistency:** the dict key `"philip"` is used identically across `_report_1d` and `_report_2d`; sub-keys `L1_<var>_fmd` and `L1_<var>_ratio` match across 1D and 2D; env vars `HRSC_DUMP_DIR` / `HRSC_DUMP_TAG` are spelled identically in C++ (Task 2) and bash (Task 3); test fixture helper `_write_grid_bin` (1D) and `_write_2d_grid_bin` (2D) share the same header layout from `scripts/io_helper.py`.
