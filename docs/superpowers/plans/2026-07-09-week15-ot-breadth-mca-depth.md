# Week 15 — Orszag-Tang 2D Breadth (P1) + MCA-Depth (N=30) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scale the existing dual-solver Orszag-Tang 2D precision-smoke packets from the Week-14-defined P0 pilot tier (8 variants, MCA n=3) to the P1 breadth tier (24 variants, adding `O3` + `fastmath=True`) and P2 MCA-depth tier (n=30), on the `headline256` profile, for both `hll` and `hlld`, without touching the existing P0 evidence.

**Architecture:** Thread an existing-but-unused `variant_set` selector (`mhd_precision_pilot.select_variants("p0"|"p1")` already implements both tiers) through `mhd_orszag_tang_precision_smoke.py`'s plan/run functions and CLI, add a non-blocking `gates.G1.ordering_flags` block by reusing `mhd_precision_pilot_core.ordering_flags` unmodified, then run the real 24-variant builds and N=30 Docker Verificarlo MCA samples for both solvers into new, additively-named evidence subdirectories.

**Tech Stack:** Python 3.11 (project env `floatpoint`), numpy, pytest; C++ solver `hrsc_mhd` built via CMake/Ninja/MSVC; Verificarlo via Docker.

## Global Constraints

- Do not modify `src/mhd/*` numerics, `tests/cases/orszag_tang_2d/orszag_tang.cfg`, `tests/cases/orszag_tang_2d/orszag_tang_mca64.cfg`, or the existing `gate128` / `headline256` (P0) evidence directories. (spec §1)
- `gate128` stays P0-only (8 variants); only `headline256` gets a P1 breadth sibling. (spec §1)
- New evidence is additive: `headline256_p1/` alongside the existing `headline256/`, `mca_n30/` alongside the existing `mca/`. Never overwrite P0 evidence. (spec §3.3)
- `variant_set` (default `"p0"`) must keep every existing call site and test passing unchanged — this is a backward-compatible parameter addition, not a breaking change. (spec §3.1)
- G0 (hard anchor gate: exact `steps`, `divB_max` within 5% rtol, all rows finite) applies unchanged at 24-variant scale — do not loosen tolerances. (spec §4)
- Binary grids (`grid.bin`) are transient — deleted after measurement unless `--keep-grids`; never commit `.bin` files or `build-matrix/` dirs. `experiments/` is gitignored, so committing evidence requires `git add -f`. (spec §1, prior Week-14/15 precedent)
- Before any evidence run, delete `build-matrix/` so `build_variant()` reconfigures from a clean state — ninja's MSVC header-dependency tracking can silently miss changes on this workstation (`docs/INDEX.md` §7 stale-binary pitfall) — and build from a `VsDevCmd.bat`-loaded console. (spec §2, INDEX §7)
- Python invocation on this workstation: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe"` (PowerShell) — has pytest.

---

### Task 1: `variant_set` parameter on `deterministic_plan()`

**Files:**
- Modify: `scripts/regression/mhd_orszag_tang_precision_smoke.py:149-154`
- Test: `tests/py/test_mhd_orszag_tang_precision_smoke.py`

**Interfaces:**
- Consumes: `mhd_precision_pilot.select_variants(phase: str) -> list[BuildVariant]` (already returns 8 variants for `"p0"`, 24 for `"p1"`; existing code, no change needed).
- Produces: `deterministic_plan(solver: str = "hll", profile: str = "gate", variant_set: str = "p0") -> list[dict[str, Any]]` — default behavior byte-identical to today.

- [ ] **Step 1: Write the failing test**

Add to `tests/py/test_mhd_orszag_tang_precision_smoke.py`:

```python
def test_deterministic_plan_p1_variant_set_returns_full_breadth_fan():
    p0_rows = ot.deterministic_plan()
    p1_rows = ot.deterministic_plan(solver="hlld", profile="headline", variant_set="p1")

    assert len(p0_rows) == 8
    assert len(p1_rows) == 24
    assert p1_rows[0]["variant"] == REFERENCE
    assert all(row["solver"] == "hlld" and row["profile"] == "headline" for row in p1_rows)
    p1_names = {row["variant"] for row in p1_rows}
    assert "cpu-double-O3-fastmath-leq" in p1_names
    assert "cpu-float-O3-fastmath-strict" in p1_names
    p0_names = {row["variant"] for row in p0_rows}
    assert p0_names < p1_names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_orszag_tang_precision_smoke.py -k p1_variant_set -v`
Expected: FAIL — `deterministic_plan() got an unexpected keyword argument 'variant_set'`.

- [ ] **Step 3: Add the `variant_set` parameter**

In `scripts/regression/mhd_orszag_tang_precision_smoke.py`, replace:

```python
def deterministic_plan(solver: str = "hll", profile: str = "gate") -> list[dict[str, Any]]:
    """Return P0 deterministic smoke rows with the reference variant first."""
    solver = _normalise_solver(solver)
    profile = _normalise_profile(profile)
    variants = ordered_variants_reference_first(select_variants("p0"))
    return [plan_row(variant, solver, profile) for variant in variants]
```

with:

```python
def deterministic_plan(
    solver: str = "hll", profile: str = "gate", variant_set: str = "p0"
) -> list[dict[str, Any]]:
    """Return deterministic smoke rows for the given variant tier ("p0"=8, "p1"=24), reference first."""
    solver = _normalise_solver(solver)
    profile = _normalise_profile(profile)
    variants = ordered_variants_reference_first(select_variants(variant_set))
    return [plan_row(variant, solver, profile) for variant in variants]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_orszag_tang_precision_smoke.py -v`
Expected: all tests pass (previous tests + the new one).

- [ ] **Step 5: Commit**

```bash
git add scripts/regression/mhd_orszag_tang_precision_smoke.py tests/py/test_mhd_orszag_tang_precision_smoke.py
git commit -m "feat(mhd): add variant_set selector to OT deterministic_plan"
```

---

### Task 2: `variant_set` parameter on `run_deterministic()`

**Files:**
- Modify: `scripts/regression/mhd_orszag_tang_precision_smoke.py:457-531`
- Test: `tests/py/test_mhd_orszag_tang_precision_smoke.py`

**Interfaces:**
- Consumes: same `select_variants` as Task 1.
- Produces: `run_deterministic(out_dir, *, solver="hll", profile="gate", variant_set="p0", variants=None, base_cfg_text=None, builder=build_variant, runner=run_case, reader=read_binary, keep_grids=False) -> dict[str, Any]`. When `variants` is explicitly passed, it still overrides `variant_set` entirely (existing empty/missing-reference validation behavior unchanged).

- [ ] **Step 1: Write the failing test**

Add to `tests/py/test_mhd_orszag_tang_precision_smoke.py`:

```python
def test_run_deterministic_p1_variant_set_builds_all_24_variants(tmp_path):
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
        grid = Path(kwargs["output_bin"])
        grid.parent.mkdir(parents=True, exist_ok=True)
        grid.write_bytes(b"grid")
        meta = {
            "elapsed_wall_s": 0.1,
            "stderr_diagnostics": {"steps": 806, "divB_mean": 0.5, "divB_max": 3.72},
        }
        return object(), meta, "stderr"

    def fake_reader(path):
        return Header(), arr.copy()

    payload = ot.run_deterministic(
        tmp_path / "out",
        solver="hll",
        profile="headline",
        variant_set="p1",
        base_cfg_text=base,
        builder=fake_builder,
        runner=fake_runner,
        reader=fake_reader,
        keep_grids=False,
    )

    assert len(built) == 24
    assert len(payload["rows"]) == 24
    assert payload["gates"]["G0_anchor"]["pass"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_orszag_tang_precision_smoke.py -k p1_variant_set_builds -v`
Expected: FAIL — `run_deterministic() got an unexpected keyword argument 'variant_set'`.

- [ ] **Step 3: Add the `variant_set` parameter**

In `scripts/regression/mhd_orszag_tang_precision_smoke.py`, change the `run_deterministic` signature and body:

```python
def run_deterministic(
    out_dir: str | pathlib.Path,
    *,
    solver: str = "hll",
    profile: str = "gate",
    variant_set: str = "p0",
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
    selected = select_variants(variant_set) if variants is None else list(variants)
```

(the remainder of the function body is unchanged — only the `select_variants("p0")` literal on the `selected = ...` line becomes `select_variants(variant_set)`).

- [ ] **Step 4: Run test to verify it passes**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_orszag_tang_precision_smoke.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/regression/mhd_orszag_tang_precision_smoke.py tests/py/test_mhd_orszag_tang_precision_smoke.py
git commit -m "feat(mhd): add variant_set selector to OT run_deterministic"
```

---

### Task 3: `gates.G1.ordering_flags` in `write_outputs()`

**Files:**
- Modify: `scripts/regression/mhd_orszag_tang_precision_smoke.py:44-59,241-291`
- Test: `tests/py/test_mhd_orszag_tang_precision_smoke.py`

**Interfaces:**
- Consumes: `mhd_precision_pilot_core.ordering_flags(rows: list[dict]) -> list[dict]` (existing Week-14 function — reads `variant, precision, opt, riemann, fastmath, Linf_rho` from each row; OT rows already carry all of these keys). No modification to `ordering_flags` itself.
- Produces: `write_outputs(...)` payload gains `payload["gates"]["G1"] = {"ordering_flags": [...]}`, always present (empty list when no fastmath/ieee pair exists in the rows, e.g. P0-shaped input — no conditional branching needed since `ordering_flags` naturally returns `[]` when it finds no matching pair).

- [ ] **Step 1: Write the failing test**

Add to `tests/py/test_mhd_orszag_tang_precision_smoke.py`:

```python
def test_write_outputs_includes_g1_ordering_flags(tmp_path):
    p0_written = ot.write_outputs(
        tmp_path / "p0",
        [_row(), _row(variant="cpu-float-O2-ieee-leq")],
        solver="hll",
        profile="gate",
        git_commit="deadbeef",
        figures=[],
    )
    assert p0_written["gates"]["G1"]["ordering_flags"] == []

    ieee_row = _row(variant="cpu-float-O3-ieee-leq", solver="hll", profile="headline")
    ieee_row["precision"] = "float"
    ieee_row["opt"] = "O3"
    ieee_row["Linf_rho"] = 0.5
    fastmath_row = _row(variant="cpu-float-O3-fastmath-leq", solver="hll", profile="headline")
    fastmath_row["precision"] = "float"
    fastmath_row["opt"] = "O3"
    fastmath_row["fastmath"] = True
    fastmath_row["Linf_rho"] = 0.2

    p1_written = ot.write_outputs(
        tmp_path / "p1",
        [_row(solver="hll", profile="headline"), ieee_row, fastmath_row],
        solver="hll",
        profile="headline",
        git_commit="deadbeef",
        figures=[],
    )
    flags = p1_written["gates"]["G1"]["ordering_flags"]
    assert len(flags) == 1
    assert flags[0]["axis"] == "fastmath"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_orszag_tang_precision_smoke.py -k g1_ordering_flags -v`
Expected: FAIL — `KeyError: 'G1'`.

- [ ] **Step 3: Add the import and the gate**

In `scripts/regression/mhd_orszag_tang_precision_smoke.py`, change the import line:

```python
from mhd_precision_pilot_core import REFERENCE  # noqa: E402
```

to:

```python
from mhd_precision_pilot_core import REFERENCE, ordering_flags  # noqa: E402
```

Then in `write_outputs()`, change:

```python
    anchor = anchor_gate(safe_rows, solver, profile)
    payload = {
        "experiment": EXPERIMENT,
        "case": CASE.name,
        "solver": solver,
        "profile": profile,
        "git_commit": _jsonable(git_commit),
        "reference_variant": REFERENCE,
        "gates": {"G0": anchor, "G0_anchor": anchor},
        "rows": safe_rows,
```

to:

```python
    anchor = anchor_gate(safe_rows, solver, profile)
    payload = {
        "experiment": EXPERIMENT,
        "case": CASE.name,
        "solver": solver,
        "profile": profile,
        "git_commit": _jsonable(git_commit),
        "reference_variant": REFERENCE,
        "gates": {
            "G0": anchor,
            "G0_anchor": anchor,
            "G1": {"ordering_flags": ordering_flags(safe_rows)},
        },
        "rows": safe_rows,
```

- [ ] **Step 4: Run test to verify it passes**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_orszag_tang_precision_smoke.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/regression/mhd_orszag_tang_precision_smoke.py tests/py/test_mhd_orszag_tang_precision_smoke.py
git commit -m "feat(mhd): report soft fastmath/ieee ordering flags in OT summaries"
```

---

### Task 4: CLI `--phase p0|p1` flag with additive packet-path suffix

**Files:**
- Modify: `scripts/regression/mhd_orszag_tang_precision_smoke.py:543-563`
- Test: `tests/py/test_mhd_orszag_tang_precision_smoke.py`

**Interfaces:**
- Consumes: `run_deterministic(..., variant_set=...)` from Task 2.
- Produces: `parse_args()` gains `--phase` (choices `p0`/`p1`, default `p0`); `main()` appends `_p1` to the profile subdir when `--phase p1` and passes `variant_set=args.phase` through.

- [ ] **Step 1: Write the failing tests**

The two existing `main()` tests call a `fake_run_deterministic` with only `(packet, *, solver, profile, keep_grids)` — since `main()` will now always pass `variant_set` too, update both fakes and add a new phase-suffix test. Replace the two existing tests in `tests/py/test_mhd_orszag_tang_precision_smoke.py`:

```python
def test_main_prints_packet_summary_and_returns_anchor_gate_status(tmp_path, monkeypatch, capsys):
    calls = []

    def fake_run_deterministic(packet, *, solver, profile, variant_set, keep_grids):
        calls.append((packet, solver, profile, variant_set, keep_grids))
        return {"gates": {"G0_anchor": {"pass": True}}}

    monkeypatch.setattr(ot, "run_deterministic", fake_run_deterministic)

    rc = ot.main([
        "--out",
        str(tmp_path),
        "--solver",
        "hlld",
        "--profile",
        "headline",
        "--keep-grids",
    ])

    packet = tmp_path / "headline256"
    assert rc == 0
    assert calls == [(packet, "hlld", "headline", "p0", True)]
    assert capsys.readouterr().out.strip() == str(packet / "summary.md")


def test_main_returns_one_when_anchor_gate_fails(tmp_path, monkeypatch):
    def fake_run_deterministic(packet, *, solver, profile, variant_set, keep_grids):
        return {"gates": {"G0_anchor": {"pass": False}}}

    monkeypatch.setattr(ot, "run_deterministic", fake_run_deterministic)

    assert ot.main(["--out", str(tmp_path), "--solver", "hll", "--profile", "gate"]) == 1


def test_main_phase_p1_appends_suffix_to_packet_dir_and_threads_variant_set(tmp_path, monkeypatch):
    calls = []

    def fake_run_deterministic(packet, *, solver, profile, variant_set, keep_grids):
        calls.append((packet, solver, profile, variant_set, keep_grids))
        return {"gates": {"G0_anchor": {"pass": True}}}

    monkeypatch.setattr(ot, "run_deterministic", fake_run_deterministic)

    rc = ot.main([
        "--out", str(tmp_path), "--solver", "hll", "--profile", "headline", "--phase", "p1",
    ])

    packet = tmp_path / "headline256_p1"
    assert rc == 0
    assert calls == [(packet, "hll", "headline", "p1", False)]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_orszag_tang_precision_smoke.py -k "main_" -v`
Expected: FAIL — `error: unrecognized arguments: --phase p1` (new test) and `TypeError: fake_run_deterministic() missing 1 required keyword-only argument: 'variant_set'` (the two updated tests, since real `main()` doesn't pass `variant_set` yet).

- [ ] **Step 3: Add `--phase` and thread it through**

In `scripts/regression/mhd_orszag_tang_precision_smoke.py`, replace:

```python
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
```

with:

```python
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=None)
    parser.add_argument("--solver", choices=SUPPORTED_SOLVERS, default="hll")
    parser.add_argument("--profile", choices=tuple(PROFILES), default="gate")
    parser.add_argument("--phase", choices=("p0", "p1"), default="p0")
    parser.add_argument("--keep-grids", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    profile = _normalise_profile(args.profile)
    subdir = PROFILES[profile]["subdir"]
    if args.phase == "p1":
        subdir = f"{subdir}_p1"
    packet = resolve_output_dir(args.out, args.solver) / subdir
    payload = run_deterministic(
        packet,
        solver=args.solver,
        profile=args.profile,
        variant_set=args.phase,
        keep_grids=args.keep_grids,
    )
    print(packet / "summary.md")
    return 0 if payload["gates"]["G0_anchor"]["pass"] else 1
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py/test_mhd_orszag_tang_precision_smoke.py -v`
Expected: all tests pass.

- [ ] **Step 5: Run the full Python suite to confirm no regressions**

Run: `& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py -q`
Expected: same pass count as before this plan's changes, plus the new tests from Tasks 1-4 (pre-existing environment-only tmp-dir permission errors on this workstation, unrelated to this change, are not a regression — compare failing test names before/after, not just the totals).

- [ ] **Step 6: Commit**

```bash
git add scripts/regression/mhd_orszag_tang_precision_smoke.py tests/py/test_mhd_orszag_tang_precision_smoke.py
git commit -m "feat(mhd): add --phase p1 CLI flag for OT breadth packets"
```

---

### Task 5: HLL headline256 P1 breadth + N=30 MCA evidence run

**Files:**
- Generated evidence under `experiments/week15/orszag_tang_precision_smoke/headline256_p1/` and `experiments/week15/orszag_tang_precision_smoke/mca_n30/`

- [ ] **Step 1: Clean build-matrix and open a VS-dev-loaded console**

From a `VsDevCmd.bat`-loaded PowerShell console (see `docs/INDEX.md` §7 pitfall):

```powershell
Remove-Item -Recurse -Force build-matrix -ErrorAction SilentlyContinue
```

- [ ] **Step 2: Run the 24-variant deterministic breadth packet**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_orszag_tang_precision_smoke.py --solver hll --profile headline --phase p1
```

Expected: prints `experiments\week15\orszag_tang_precision_smoke\headline256_p1\summary.md` and exits `0`. If it exits `1`, stop — read the summary's `gates.G0_anchor` block, investigate build freshness (re-run Step 1) or cfg drift; do not loosen tolerances.

- [ ] **Step 3: Run the N=30 MCA sampler for both precisions**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/verificarlo/mhd_precision_sampling.py --solver hll --samples 30 --case tests/cases/orszag_tang_2d/orszag_tang_mca64.cfg --out experiments/week15/orszag_tang_precision_smoke/mca_n30 --experiment week15-mhd-mca-n30
```

Expected: prints `experiments\week15\orszag_tang_precision_smoke\mca_n30\summary.json`. This step is long-running (Docker Verificarlo x 30 samples x 2 precisions) — run it in the background and check back rather than blocking on it.

- [ ] **Step 4: Verify gates and transient-grid hygiene**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -c "import json,pathlib; root=pathlib.Path('experiments/week15/orszag_tang_precision_smoke'); s=json.loads((root/'headline256_p1/summary.json').read_text()); print('rows', len(s['rows']), 'G0', s['gates']['G0_anchor']['pass'], 'G1_flags', len(s['gates']['G1']['ordering_flags'])); m=json.loads((root/'mca_n30/summary.json').read_text()); print('p53', m['mca']['p53']['status'], m['mca']['p53']['n'], 'p24', m['mca']['p24']['status'], m['mca']['p24']['n'])"
Get-ChildItem -Path experiments\week15\orszag_tang_precision_smoke\headline256_p1,experiments\week15\orszag_tang_precision_smoke\mca_n30 -Recurse -Include *.bin
```

Expected: `rows 24 G0 True`, `p53 completed 30`, `p24 completed 30`; the `Get-ChildItem` command prints no `.bin` files.

- [ ] **Step 5: Force-add evidence and commit**

```bash
git add -f experiments/week15/orszag_tang_precision_smoke/headline256_p1 experiments/week15/orszag_tang_precision_smoke/mca_n30
git commit -m "test(mhd): HLL Orszag-Tang breadth (P1) + N=30 MCA evidence"
```

---

### Task 6: HLLD headline256 P1 breadth + N=30 MCA evidence run

**Files:**
- Generated evidence under `experiments/week15/orszag_tang_precision_smoke_hlld/headline256_p1/` and `experiments/week15/orszag_tang_precision_smoke_hlld/mca_n30/`

- [ ] **Step 1: Clean build-matrix again (P0 build dirs from Task 5 are stale for a fresh audit)**

```powershell
Remove-Item -Recurse -Force build-matrix -ErrorAction SilentlyContinue
```

- [ ] **Step 2: Run the 24-variant deterministic breadth packet**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/regression/mhd_orszag_tang_precision_smoke.py --solver hlld --profile headline --phase p1
```

Expected: prints `experiments\week15\orszag_tang_precision_smoke_hlld\headline256_p1\summary.md` and exits `0`.

- [ ] **Step 3: Run the N=30 MCA sampler for both precisions**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts/verificarlo/mhd_precision_sampling.py --solver hlld --samples 30 --case tests/cases/orszag_tang_2d/orszag_tang_mca64.cfg --out experiments/week15/orszag_tang_precision_smoke_hlld/mca_n30 --experiment week15-mhd-mca-n30
```

Expected: prints `experiments\week15\orszag_tang_precision_smoke_hlld\mca_n30\summary.json`. Long-running — background it.

- [ ] **Step 4: Verify gates and transient-grid hygiene**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -c "import json,pathlib; root=pathlib.Path('experiments/week15/orszag_tang_precision_smoke_hlld'); s=json.loads((root/'headline256_p1/summary.json').read_text()); print('rows', len(s['rows']), 'G0', s['gates']['G0_anchor']['pass'], 'G1_flags', len(s['gates']['G1']['ordering_flags'])); m=json.loads((root/'mca_n30/summary.json').read_text()); print('p53', m['mca']['p53']['status'], m['mca']['p53']['n'], 'p24', m['mca']['p24']['status'], m['mca']['p24']['n'])"
Get-ChildItem -Path experiments\week15\orszag_tang_precision_smoke_hlld\headline256_p1,experiments\week15\orszag_tang_precision_smoke_hlld\mca_n30 -Recurse -Include *.bin
```

Expected: `rows 24 G0 True`, `p53 completed 30`, `p24 completed 30`; no `.bin` files printed.

- [ ] **Step 5: Force-add evidence and commit**

```bash
git add -f experiments/week15/orszag_tang_precision_smoke_hlld/headline256_p1 experiments/week15/orszag_tang_precision_smoke_hlld/mca_n30
git commit -m "test(mhd): HLLD Orszag-Tang breadth (P1) + N=30 MCA evidence"
```

---

### Task 7: Docs registration

**Files:**
- Modify: `scripts/regression/README.md:26-30`
- Modify: `docs/INDEX.md:216`

- [ ] **Step 1: Update the regression README entry**

In `scripts/regression/README.md`, replace:

```markdown
- `mhd_orszag_tang_precision_smoke.py`: Week-15 solver-aware Orszag-Tang 2D
  precision packets (`--solver hll|hlld` x `--profile gate|headline`):
  deterministic P0 build fan vs the same-solver fp64 reference with an anchor
  gate from the HLLD div(B) follow-up; MCA recorded separately via
  `scripts/verificarlo/mhd_precision_sampling.py --case`.
```

with:

```markdown
- `mhd_orszag_tang_precision_smoke.py`: Week-15 solver-aware Orszag-Tang 2D
  precision packets (`--solver hll|hlld` x `--profile gate|headline` x
  `--phase p0|p1`): deterministic build fan (P0=8 variants, P1=24 variants
  adding O3 + fastmath) vs the same-solver fp64 reference, with an anchor gate
  from the HLLD div(B) follow-up and a soft `gates.G1.ordering_flags`
  fastmath-vs-ieee check; MCA recorded separately via
  `scripts/verificarlo/mhd_precision_sampling.py --case ... --samples N`
  (n=3 smoke in `mca/`, n=30 depth in `mca_n30/`).
```

- [ ] **Step 2: Update the INDEX data-products row**

In `docs/INDEX.md`, replace the `experiments/week15/orszag_tang_precision_smoke[_hlld]/` row with:

```markdown
| `experiments/week15/orszag_tang_precision_smoke[_hlld]/` | Week-15 solver-aware OT 2D precision packets: per-solver `gate128/` + `headline256/` P0 deterministic fans (8 variants) vs same-solver fp64 reference with G0 anchor gates (gate: steps=76, divB_max 1.173/1.085; headline: steps=806/812, divB_max 3.72/24.45); `headline256_p1/` adds the full 24-variant O3+fastmath breadth fan with a soft `gates.G1.ordering_flags` check; Docker Verificarlo MCA at 64², t=0.05 in `mca/` (n=3 smoke) and `mca_n30/` (n=30 depth); unified `summary.{csv,json,md}` + figures |
```

- [ ] **Step 3: Commit**

```bash
git add scripts/regression/README.md docs/INDEX.md
git commit -m "docs(week15): register OT breadth (P1) + MCA-depth (N=30) evidence"
```

---

## Final Reporting

After Task 7, report:

- both breadth summary paths (`headline256_p1/summary.md`, HLL and HLLD) and their G0/G1 results
- both MCA-depth summary paths (`mca_n30/summary.json`, HLL and HLLD), sample counts, and spread fields
- any non-empty `ordering_flags` (report verbatim — these are new, report-worthy signal per the 2026-07-08 design's implementation-axis claim bucket, not a bug)
- explicit boundary: this closes the Week-14-deferred P1/P2 tiers for OT 2D only; Brio-Wu 1D P1/P2 and Kelvin-Helmholtz remain open (separate sub-projects)

Plan complete.
