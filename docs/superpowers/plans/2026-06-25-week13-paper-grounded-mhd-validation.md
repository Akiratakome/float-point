# Paper-Grounded Week 12/13 MHD Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade Week 12/13 MHD evidence from engineering/self-reference checks to report-ready, paper-grounded validation figures and summaries.

**Architecture:** Keep solver numerics and cfg defaults unchanged. Add report-facing validation scripts/figures/docs that read existing binary outputs or run scripted cfgs through `hrsc_mhd`, write scalar summaries and paper-style plots, and record provenance. Generated figures must be based on this repository's numerical output; do not copy or redraw copyrighted paper figures.

**Tech Stack:** C++17 existing `hrsc_mhd`; Python 3 via `C:\Users\tangy\miniconda3\python.exe`; numpy/matplotlib only where possible; existing `scripts/regression/_mhd_harness.py`; Markdown summaries under `experiments/week12` / `experiments/week13`.

---

## Global Constraints

- Read `docs/INDEX.md` and `docs/HARNESS.md` before editing.
- Do not change solver numerics, cfg defaults, or existing output formats.
- Figures must be generated from our solver output and styled to be comparable with paper benchmark figures, not copied from papers.
- Keep binary grids transient/ignored. Commit scalar summaries, figure PNGs, scripts, and documentation only.
- Use `C:\Users\tangy\miniconda3\python.exe` for Python.
- Use VS BuildTools `VsDevCmd.bat` for C++ builds on Windows.
- For every experiment run, save generated cfg, stdout/stderr, metadata, and summary.
- Prefer HLL as production solver unless a task explicitly runs HLLD diagnostics.

## Literature Anchors

Use these as the initial benchmark references:

- Brio & Wu 1988, "An upwind differencing scheme for the equations of ideal magnetohydrodynamics", JCP, DOI `10.1016/0021-9991(88)90120-9`.
- Miyoshi & Kusano 2005, "A multi-state HLL approximate Riemann solver for ideal magnetohydrodynamics", JCP, DOI `10.1016/j.jcp.2005.02.017`.
- Dedner et al. 2002, hyperbolic/parabolic divergence cleaning, JCP, DOI `10.1006/jcph.2001.6961`.
- Toth 2000, `div B = 0` constraint and Orszag-Tang benchmark context, JCP, DOI `10.1006/jcph.2000.6519`.
- Frank et al. 1996 MHD Kelvin-Helmholtz simulations, arXiv `astro-ph/9510115`.
- Lecoanet et al. 2015, Kelvin-Helmholtz tests can be ill-posed; use this to bound KH claims, arXiv `1509.03630`.

## File Structure

**Create/modify:**
- `docs/week13/paper_benchmark_matrix.md` - paper-grounded validation matrix.
- `scripts/regression/mhd_paper_figures.py` - shared plotting helpers for MHD report figures.
- `scripts/regression/mhd_brio_wu_paper_figures.py` - Brio-Wu paper-style profile figure script.
- `scripts/regression/mhd_orszag_tang_2d.py` - extend existing OT driver to produce paper-style figures and literature notes.
- `scripts/regression/mhd_kh_2d.py` - extend existing KH driver to produce paper-style figures and literature notes.
- `scripts/regression/mhd_hlld_diagnostics.py` - HLL vs HLLD diagnostic figures.
- `experiments/week12/brio_wu_1d/figures/*.png` and `experiments/week12/brio_wu_1d/paper_summary.md`.
- `experiments/week13/orszag_tang/summary.{csv,json,md}` and `figures/*.png`.
- `experiments/week13/kelvin_helmholtz/summary.{csv,json,md}` and `figures/*.png`.
- `experiments/week13/solver_compare/figures/*.png` and optional update to `summary.md`.
- `docs/week13/week13-summary.md` - update evidence links after new summaries exist.

## Task 1: Paper Benchmark Matrix

**Files:**
- Create: `docs/week13/paper_benchmark_matrix.md`
- Modify: `docs/week13/week13-summary.md`

- [ ] **Step 1: Audit current Week 12/13 evidence**

Run:

```powershell
git ls-files docs/week12 docs/week13 experiments/week12 experiments/week13 scripts/regression | Sort-Object
```

Expected: confirms Week 12 summaries exist, Week 13 solver_compare exists, and OT/KH summaries may be missing before later tasks.

- [ ] **Step 2: Write the benchmark matrix**

Create `docs/week13/paper_benchmark_matrix.md` with a table:

```markdown
# Week 12/13 Paper-Grounded MHD Benchmark Matrix

This matrix maps each local validation run to the literature benchmark it is
allowed to support. Local plots are generated from this repository's solver
outputs; paper figures are not copied.

| local case | production solver | literature anchor | cfg/time | report figure target | current evidence | claim boundary |
|---|---|---|---|---|---|---|
| Brio-Wu 1D | HLL | Brio & Wu 1988, DOI `10.1016/0021-9991(88)90120-9`; standard-problem discussion in Takahashi & Yamada 2012 | `tests/cases/brio_wu_1d/brio_wu.cfg`, `t=0.1` | four-panel profiles: rho, vx, By, p | Week 12 self-reference + paper-style profile figure | validates qualitative wave structure and divergence sentinel; self-reference norms are secondary |
| GLM div(B) cleaning | HLL | Dedner et al. 2002, DOI `10.1006/jcph.2001.6961` | Gaussian divB blob sweep, `glm_cr={0,0.18,0.36}` | divB decay curve and heatmap | Week 12 sweep | demonstrates local cleaning behaviour, not physical MHD benchmark accuracy |
| Orszag-Tang 2D | HLL | Toth 2000, DOI `10.1006/jcph.2000.6519`; Orszag-Tang vortex benchmark context | `tests/cases/orszag_tang_2d/orszag_tang.cfg`, `t=0.5` | density/pressure/divB maps | run in Task 3 | validates benchmark morphology and finite diagnostics; 512-grid self-reference is secondary |
| Kelvin-Helmholtz 2D | HLL | Frank et al. 1996, arXiv `astro-ph/9510115`; Lecoanet et al. 2015, arXiv `1509.03630` limitation | `tests/cases/kelvin_helmholtz_2d/kh.cfg`, `t=1.0` | density, magnetic field magnitude, divB maps | run in Task 4 | bounded morphology/stability evidence; avoid overclaiming convergence because KH can be ill-posed |
| HLLD diagnostic | HLLD only as diagnostic | Miyoshi & Kusano 2005, DOI `10.1016/j.jcp.2005.02.017` | OT `256^2`, `t=0.5`, `riemann=hll|hlld` | HLL/HLLD rho diff and divB comparison | Week 13 solver_compare | HLLD executable but deferred for production due elevated divB |
```

- [ ] **Step 3: Link the matrix from Week 13 summary**

Add one bullet under `docs/week13/week13-summary.md` Evidence:

```markdown
- Paper-grounded benchmark matrix:
  [paper_benchmark_matrix.md](paper_benchmark_matrix.md)
```

- [ ] **Step 4: Verify links and commit**

Run:

```powershell
Test-Path docs/week13/paper_benchmark_matrix.md
git diff -- docs/week13
```

Commit:

```powershell
git add docs/week13/paper_benchmark_matrix.md docs/week13/week13-summary.md
git commit -m "docs(mhd): map Week 12/13 validation to paper benchmarks"
```

## Task 2: Brio-Wu Paper-Style Profiles

**Files:**
- Create: `scripts/regression/mhd_paper_figures.py`
- Create: `scripts/regression/mhd_brio_wu_paper_figures.py`
- Create: `experiments/week12/brio_wu_1d/paper_summary.md`
- Write: `experiments/week12/brio_wu_1d/figures/brio_wu_paper_profiles.png`

- [ ] **Step 1: Create shared plotting helpers**

`scripts/regression/mhd_paper_figures.py` should provide:

```python
RHO, MX, MY, MZ, BX, BY, BZ, E, PSI = range(9)

def mhd_primitive(arr, gamma):
    rho = arr[..., RHO]
    vx = arr[..., MX] / rho
    vy = arr[..., MY] / rho
    vz = arr[..., MZ] / rho
    Bx = arr[..., BX]
    By = arr[..., BY]
    Bz = arr[..., BZ]
    E = arr[..., E]
    kinetic = 0.5 * rho * (vx * vx + vy * vy + vz * vz)
    magnetic = 0.5 * (Bx * Bx + By * By + Bz * Bz)
    p = (gamma - 1.0) * (E - kinetic - magnetic)
    return {"rho": rho, "vx": vx, "vy": vy, "vz": vz, "Bx": Bx, "By": By, "Bz": Bz, "p": p}
```

It should also include small helpers to create `figures/`, save PNGs with dpi >= 180, and write no binary grids.

- [ ] **Step 2: Create the Brio-Wu plotting script**

`scripts/regression/mhd_brio_wu_paper_figures.py` should:

- Reuse existing `experiments/week12/brio_wu_1d/bw_800.bin` if present; otherwise run `build-double/hrsc_mhd(.exe)` with `tests/cases/brio_wu_1d/brio_wu.cfg` and `output_file`.
- Read the binary using `scripts/io_helper.py`.
- Plot a 2x2 panel for `rho`, `vx`, `By`, `p` against cell-centred `x`.
- Save `experiments/week12/brio_wu_1d/figures/brio_wu_paper_profiles.png`.
- Write `experiments/week12/brio_wu_1d/paper_summary.md` describing Brio & Wu 1988 as the paper anchor and saying self-reference convergence is secondary evidence.

- [ ] **Step 3: Verify**

Run:

```powershell
& "C:\Users\tangy\miniconda3\python.exe" -m py_compile scripts/regression/mhd_paper_figures.py scripts/regression/mhd_brio_wu_paper_figures.py
& "C:\Users\tangy\miniconda3\python.exe" scripts/regression/mhd_brio_wu_paper_figures.py
Test-Path experiments/week12/brio_wu_1d/figures/brio_wu_paper_profiles.png
Test-Path experiments/week12/brio_wu_1d/paper_summary.md
```

- [ ] **Step 4: Commit**

```powershell
git add scripts/regression/mhd_paper_figures.py scripts/regression/mhd_brio_wu_paper_figures.py experiments/week12/brio_wu_1d/figures/brio_wu_paper_profiles.png experiments/week12/brio_wu_1d/paper_summary.md
git commit -m "test(mhd): add Brio-Wu paper-style validation profiles"
```

## Task 3: Orszag-Tang Paper-Style Validation Figures

**Files:**
- Modify: `scripts/regression/mhd_orszag_tang_2d.py`
- Write: `experiments/week13/orszag_tang/summary.{csv,json,md}`
- Write: `experiments/week13/orszag_tang/figures/*.png`

- [ ] **Step 1: Extend OT script with figures**

Add figure generation after gates pass:

- `ot_density_pressure.png`: two panels, density and pressure.
- `ot_divb.png`: `abs(divB)` heatmap computed by central differences using `dx,dy`.
- `ot_paper_style.png`: compact report-ready figure with density and magnetic pressure or pressure.

Use matplotlib with fixed colorbars and axis labels. Add literature note to `summary.md`:

```markdown
Paper anchor: Orszag-Tang is used here as a 2D ideal-MHD vortex benchmark in the Toth 2000 div(B)-constraint context. The 512-grid self-reference norms are engineering consistency checks; report validation relies on paper-grounded morphology and finite div(B)/conservation diagnostics.
```

- [ ] **Step 2: Build binary if needed**

Run:

```cmd
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && cmake --build build-double --target hrsc_mhd
```

- [ ] **Step 3: Run OT validation**

Run:

```powershell
& "C:\Users\tangy\miniconda3\python.exe" -m py_compile scripts/regression/mhd_orszag_tang_2d.py
& "C:\Users\tangy\miniconda3\python.exe" scripts/regression/mhd_orszag_tang_2d.py
```

Expected: summary files are produced; gates pass or the script exits with a clear gate failure.

- [ ] **Step 4: Commit**

If gates pass:

```powershell
git add scripts/regression/mhd_orszag_tang_2d.py experiments/week13/orszag_tang/summary.csv experiments/week13/orszag_tang/summary.json experiments/week13/orszag_tang/summary.md experiments/week13/orszag_tang/figures
git commit -m "test(mhd): add paper-style Orszag-Tang validation figures"
```

If gates fail, commit no fabricated summaries; report BLOCKED with stdout/stderr and run metadata paths.

## Task 4: Kelvin-Helmholtz Paper-Style Validation Figures

**Files:**
- Modify: `scripts/regression/mhd_kh_2d.py`
- Write: `experiments/week13/kelvin_helmholtz/summary.{csv,json,md}`
- Write: `experiments/week13/kelvin_helmholtz/figures/*.png`

- [ ] **Step 1: Extend KH script with figures**

Add figure generation after gates pass:

- `kh_density_bmag.png`: density and `sqrt(Bx^2+By^2+Bz^2)`.
- `kh_divb.png`: `abs(divB)` heatmap.
- `kh_paper_style.png`: compact report-ready density/B-field figure.

Add literature note to `summary.md`:

```markdown
Paper anchor: Frank et al. 1996 is used for MHD Kelvin-Helmholtz context; Lecoanet et al. 2015 is used as a limitation that KH morphology alone is not a well-posed convergence proof. This run is bounded validation evidence, not a claim of unique KH reference convergence.
```

- [ ] **Step 2: Run KH validation**

Run:

```powershell
& "C:\Users\tangy\miniconda3\python.exe" -m py_compile scripts/regression/mhd_kh_2d.py
& "C:\Users\tangy\miniconda3\python.exe" scripts/regression/mhd_kh_2d.py
```

Expected: summary files are produced; gates pass or the script exits with a clear gate failure.

- [ ] **Step 3: Commit**

If gates pass:

```powershell
git add scripts/regression/mhd_kh_2d.py experiments/week13/kelvin_helmholtz/summary.csv experiments/week13/kelvin_helmholtz/summary.json experiments/week13/kelvin_helmholtz/summary.md experiments/week13/kelvin_helmholtz/figures
git commit -m "test(mhd): add paper-style Kelvin-Helmholtz validation figures"
```

If gates fail, commit no fabricated summaries; report BLOCKED with stdout/stderr and run metadata paths.

## Task 5: HLLD Diagnostic Figures

**Files:**
- Create: `scripts/regression/mhd_hlld_diagnostics.py`
- Write: `experiments/week13/solver_compare/figures/*.png`
- Modify: `experiments/week13/solver_compare/summary.md`
- Modify: `docs/week13/week13-summary.md`

- [ ] **Step 1: Create HLLD diagnostic plotting script**

The script should consume existing `experiments/week13/solver_compare/ot_256_hll.bin` and `ot_256_hlld.bin` when present; otherwise rerun `scripts/regression/mhd_solver_compare_2d.py`.

Generate:

- `rho_hll_hlld_diff.png`: three panels, HLL rho, HLLD rho, HLLD-HLL rho.
- `divb_hll_hlld.png`: two panels, `abs(divB)` for HLL and HLLD.

Write a small `figures/README.md` explaining that these are diagnostic figures and HLLD remains deferred.

- [ ] **Step 2: Update summaries**

Append to `experiments/week13/solver_compare/summary.md`:

```markdown
## Diagnostic figures

- `figures/rho_hll_hlld_diff.png`
- `figures/divb_hll_hlld.png`

These figures support the deferred-HLLD decision; they are not production validation.
```

Update `docs/week13/week13-summary.md` to link the diagnostic figures.

- [ ] **Step 3: Verify and commit**

Run:

```powershell
& "C:\Users\tangy\miniconda3\python.exe" -m py_compile scripts/regression/mhd_hlld_diagnostics.py
& "C:\Users\tangy\miniconda3\python.exe" scripts/regression/mhd_hlld_diagnostics.py
```

Commit:

```powershell
git add scripts/regression/mhd_hlld_diagnostics.py experiments/week13/solver_compare/figures experiments/week13/solver_compare/summary.md docs/week13/week13-summary.md
git commit -m "test(mhd): add HLLD deferred-decision diagnostic figures"
```

## Final Verification

Run:

```cmd
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && cmake --build build-double --target hrsc_mhd unit_tests && build-double\unit_tests.exe "[mhd]" -r compact && build-double\hrsc_mhd.exe tests\cases\brio_wu_1d\brio_wu.cfg
```

Run:

```powershell
& "C:\Users\tangy\miniconda3\python.exe" -m py_compile scripts/regression/mhd_paper_figures.py scripts/regression/mhd_brio_wu_paper_figures.py scripts/regression/mhd_orszag_tang_2d.py scripts/regression/mhd_kh_2d.py scripts/regression/mhd_hlld_diagnostics.py
& "C:\Users\tangy\miniconda3\python.exe" -m json.tool experiments/week13/solver_compare/summary.json
git status --short --branch --untracked-files=all
```

Expected:

- `[mhd]` unit tests pass.
- Brio-Wu default prints `steps=759` and `divB_max=4.441e-14`.
- Python scripts compile.
- JSON summaries parse.
- Worktree is clean except for intentionally committed outputs.
