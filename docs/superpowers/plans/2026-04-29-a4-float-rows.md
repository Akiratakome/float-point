# A4 Float Rows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare the A4 metric pipeline to add real-float MCA p24 rows without changing existing p53 results, and document Athena SLURM reproduction steps.

**Architecture:** Keep the existing A4 metric scripts as the source of truth. Add a precision label parameter to SNR/LoSoS outputs, make the headline table discover all `(solver, precision)` rows present in CSV inputs, and add a CSC Athena README for generating `p24-real-float` sample ensembles.

**Tech Stack:** Python, pytest, Markdown, existing C++/CMake/Verificarlo scripts.

---

### Task 1: Precision Labels

**Files:**
- Modify: `scripts/metrics/snr_metric.py`
- Modify: `scripts/metrics/losos_metric.py`
- Test: `tests/py/test_harness_scripts.py`

- [ ] Add tests that assert both metric CLIs expose `--precision-label`.
- [ ] Run the tests and confirm they fail before implementation.
- [ ] Add `--precision-label` with default `p53` and write that value into the CSV `precision` column.
- [ ] Run the targeted tests and confirm they pass.

### Task 2: Dynamic Headline Rows

**Files:**
- Modify: `scripts/figures/tradeoff_summary_table.py`
- Test: `tests/py/test_harness_scripts.py`

- [ ] Add a test with synthetic p53 and p24 rows that expects four markdown table rows.
- [ ] Run the test and confirm it fails before implementation.
- [ ] Replace the hard-coded two-row table with row discovery from joined CSV inputs.
- [ ] Keep default p53 behavior unchanged when only p53 rows exist.
- [ ] Run targeted tests and confirm they pass.

### Task 3: Athena Reproduction README

**Files:**
- Create: `scripts/cluster/slurm/README_A4_FLOAT_ROWS.md`

- [ ] Document Athena prerequisites: SLURM, `/lsc/opt/verificarlo-2.4.0`, `/usr/bin/clang++`.
- [ ] Document build and `sbatch --array=1-30` commands for HLLC and Rusanov real-float MCA p24.
- [ ] Document how to copy results back and run local A4 metric/table generation.
- [ ] Include a short “how to read the plots/table” section for `sigma_FP`, `SNR`, `LoSoS`, and regime columns.

### Task 4: Verify And Publish

**Files:**
- All files above.

- [ ] Run `python -m pytest tests/py -q`.
- [ ] Run `.\build-double\unit_tests.exe -r compact`.
- [ ] Run `.\build-float\unit_tests.exe -r compact`.
- [ ] Check `git diff --stat`.
- [ ] Commit the intended changes and push the current branch.
