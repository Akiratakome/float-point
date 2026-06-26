# Week 13 Local MHD Smoke-First Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Start local, low-cost Report 2 MHD evidence before the expensive OT/KH `512^2` gates by adding an HLLD GLM sweep and an MHD Verificarlo smoke/probe path.

**Architecture:** Keep the solver and existing cfg defaults unchanged. Each driver copies source cfg text into generated run directories, appends only per-run overrides, saves metadata and scalar summaries, and treats binary grids as transient analysis inputs. The HLLD sweep is deterministic and local; the Verificarlo smoke first probes WSL/Docker/native availability and records a blocked status if no Verificarlo runner is usable.

**Tech Stack:** Python 3 with stdlib + NumPy for binary-grid metrics; existing `hrsc_mhd` executable; optional WSL/Docker/native Verificarlo for MCA smoke; existing `scripts/io_helper.py` binary reader.

---

### Task 1: HLLD GLM Sweep

**Files:**
- Create: `scripts/regression/mhd_hlld_glm_sweep.py`
- Create: `tests/py/test_mhd_hlld_glm_sweep.py`
- Write generated evidence under: `experiments/week13/hlld_glm_sweep/`
- Modify, if appropriate after evidence exists: `docs/week13/week13-summary.md`

- [ ] **Step 1: Write tests for cfg override and summary helpers**

Create `tests/py/test_mhd_hlld_glm_sweep.py` with tests that import helper functions from `scripts.regression.mhd_hlld_glm_sweep`. Test that `replace_or_append_cfg()` changes existing keys and appends missing keys, and that `summarise_rows()` identifies the lowest finite HLLD `divB_max` row without treating it as production adoption.

- [ ] **Step 2: Run tests and verify they fail before implementation**

Run:

```powershell
& "C:\Users\tangy\miniconda3\python.exe" -m pytest tests\py\test_mhd_hlld_glm_sweep.py -q
```

Expected initial result: import failure because `scripts/regression/mhd_hlld_glm_sweep.py` does not exist yet.

- [ ] **Step 3: Implement deterministic sweep driver**

Create `scripts/regression/mhd_hlld_glm_sweep.py` with:

- default case `tests/cases/orszag_tang_2d/orszag_tang.cfg`
- default binary `build-double/hrsc_mhd.exe` on Windows or `build-double/hrsc_mhd` elsewhere
- default output root `experiments/week13/hlld_glm_sweep`
- default `glm_cr` values `0.05,0.1,0.18,0.3,0.5`
- default riemann solvers `hll,hlld`
- optional `--nx` to create a smoke cfg by overriding `nx` and `ny`
- optional `--t-end` to override `t_end` for smoke runs
- optional `--reuse` to skip existing successful run directories

For each run, write:

- `<out>/runs/<solver>_glm<value>/config.cfg`
- `<out>/runs/<solver>_glm<value>/stdout.txt`
- `<out>/runs/<solver>_glm<value>/stderr.txt`
- `<out>/runs/<solver>_glm<value>/metadata.json`

After all runs, write:

- `<out>/summary.csv`
- `<out>/summary.json`
- `<out>/summary.md`

The markdown summary must state that HLLD remains diagnostic/deferred unless a later production decision is recorded separately.

- [ ] **Step 4: Run fast local smoke**

Run:

```powershell
& "C:\Users\tangy\miniconda3\python.exe" scripts\regression\mhd_hlld_glm_sweep.py --nx 64 --t-end 0.05 --glm-cr 0.05 0.18 --riemann hll hlld
```

Expected: four runs complete, `summary.json` parses, no source cfg files changed.

- [ ] **Step 5: Run tests and compile checks**

Run:

```powershell
& "C:\Users\tangy\miniconda3\python.exe" -m pytest tests\py\test_mhd_hlld_glm_sweep.py -q
& "C:\Users\tangy\miniconda3\python.exe" -m py_compile scripts\regression\mhd_hlld_glm_sweep.py
```

Expected: tests pass and py_compile exits 0.

- [ ] **Step 6: Commit Task 1**

Commit only the script, tests, lightweight summaries, and docs. Do not commit generated `.bin` grids or build directories.

### Task 2: MHD Verificarlo Smoke/Probe

**Files:**
- Create: `scripts/verificarlo/mhd_verificarlo_smoke.py`
- Create: `tests/py/test_mhd_verificarlo_smoke.py`
- Write generated evidence under: `experiments/week13/mhd_verificarlo_smoke/`
- Modify, if appropriate after evidence exists: `docs/week13/week13-summary.md`

- [ ] **Step 1: Write tests for runner selection and blocked summary**

Create `tests/py/test_mhd_verificarlo_smoke.py` with tests that import helper functions from `scripts.verificarlo.mhd_verificarlo_smoke`. Test that command probes are represented as structured records, generated cfg text appends `output_format=binary` and `output_file=...`, and blocked summaries explicitly say no Verificarlo MCA result was produced.

- [ ] **Step 2: Run tests and verify they fail before implementation**

Run:

```powershell
& "C:\Users\tangy\miniconda3\python.exe" -m pytest tests\py\test_mhd_verificarlo_smoke.py -q
```

Expected initial result: import failure because `scripts/verificarlo/mhd_verificarlo_smoke.py` does not exist yet.

- [ ] **Step 3: Implement smoke/probe driver**

Create `scripts/verificarlo/mhd_verificarlo_smoke.py` with:

- default case `tests/cases/brio_wu_1d/brio_wu.cfg`
- default samples `3`
- default precision `53`
- default output root `experiments/week13/mhd_verificarlo_smoke`
- `--probe-only` mode that checks native `verificarlo-c++`, WSL `verificarlo-c++`, and Docker availability without running samples
- sample mode that runs only when a supported runner is available
- structured `environment.json`, `summary.json`, and `summary.md`

If no supported Verificarlo runner is available, exit 0 with `status="blocked_environment"` and a markdown summary that records the failed probes and says no MCA evidence was generated.

- [ ] **Step 4: Probe local environment**

Run:

```powershell
& "C:\Users\tangy\miniconda3\python.exe" scripts\verificarlo\mhd_verificarlo_smoke.py --probe-only
```

Expected: `environment.json`, `summary.json`, and `summary.md` are produced. If Docker/WSL/native Verificarlo is unavailable or access-blocked, the status is `blocked_environment`.

- [ ] **Step 5: If a runner is available, run tiny Brio-Wu MCA smoke**

Run:

```powershell
& "C:\Users\tangy\miniconda3\python.exe" scripts\verificarlo\mhd_verificarlo_smoke.py --samples 3
```

Expected if runnable: three MCA samples plus one IEEE/reference or clearly labelled baseline, per-sample metadata, and scalar spread summary. Expected if not runnable: blocked summary only, no false MCA claim.

- [ ] **Step 6: Run tests and compile checks**

Run:

```powershell
& "C:\Users\tangy\miniconda3\python.exe" -m pytest tests\py\test_mhd_verificarlo_smoke.py -q
& "C:\Users\tangy\miniconda3\python.exe" -m py_compile scripts\verificarlo\mhd_verificarlo_smoke.py
```

Expected: tests pass and py_compile exits 0.

- [ ] **Step 7: Commit Task 2**

Commit only the script, tests, lightweight probe/smoke summaries, and docs. Do not commit Docker images, build directories, or generated binary grids.

### Task 3: Final Verification and Status

**Files:**
- Modify: `docs/week13/week13-summary.md` if either Task 1 or Task 2 produces new stable evidence links not already recorded.

- [ ] **Step 1: Run final script checks**

Run:

```powershell
& "C:\Users\tangy\miniconda3\python.exe" -m py_compile scripts\regression\mhd_hlld_glm_sweep.py scripts\verificarlo\mhd_verificarlo_smoke.py
```

Expected: exit 0.

- [ ] **Step 2: Run focused tests**

Run:

```powershell
& "C:\Users\tangy\miniconda3\python.exe" -m pytest tests\py\test_mhd_hlld_glm_sweep.py tests\py\test_mhd_verificarlo_smoke.py -q
```

Expected: all tests pass.

- [ ] **Step 3: Validate JSON summaries**

Run:

```powershell
& "C:\Users\tangy\miniconda3\python.exe" -m json.tool experiments\week13\hlld_glm_sweep\summary.json
& "C:\Users\tangy\miniconda3\python.exe" -m json.tool experiments\week13\mhd_verificarlo_smoke\summary.json
```

Expected: both parse, with Verificarlo allowed to be `blocked_environment`.

- [ ] **Step 4: Check git hygiene**

Run:

```powershell
git status --short --branch --untracked-files=all
git diff --check HEAD
```

Expected: no unintended tracked changes, no whitespace errors, no tracked heavy binaries.

