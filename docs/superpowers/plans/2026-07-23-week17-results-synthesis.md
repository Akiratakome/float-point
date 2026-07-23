# Week 17 Results Synthesis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the completed Week 15-16 Report 2 evidence into a bounded Week 17 synthesis packet with machine-readable rankings, final report tables, figures, MPI-omission justification, and current documentation links.

**Architecture:** Add a read-only synthesis layer that consumes committed `summary.json` authorities and writes a new `experiments/week17/report2_synthesis/` packet. The script must aggregate and plot existing evidence only; it must not rerun solvers, change solver numerics, change cfg defaults, or widen any claim beyond `docs/experiment_logs/report2_evidence_map.md`.

**Tech Stack:** Python 3.11, stdlib `json/csv/pathlib/subprocess`, existing pytest suite, matplotlib for report figures.

## Global Constraints

- Follow `config -> build -> run -> measure -> aggregate -> plot`.
- Do not change solver numerics, existing cfg defaults, binary output format, or existing summary schemas.
- Treat `docs/experiment_logs/report2_evidence_map.md` as the current status authority.
- Keep KH MCA as `blocked_environment`; do not make a KH MCA noise-floor claim.
- Keep Week 15 Brio-Wu/OT deterministic-plus-MCA rows provisional until a unified gate exists.
- Do not commit generated grids, build directories, or large transient outputs.
- Record source summary paths and source git commits where available.

## Tasks

### Task 1: Add The Synthesis Data Model

- [ ] Add `tests/py/test_report2_synthesis.py` covering source summary presence, claim boundaries, bounded axis ranking, CLI outputs, and docs registration.
- [ ] Run the test to verify it fails before implementation.
- [ ] Add `scripts/regression/report2_synthesis.py` with `SOURCE_SUMMARIES`, `load_json(repo_root, relative_path)`, and `build_synthesis(repo_root)`.

### Task 2: Compute Bounded Axis Rankings And Tables

- [ ] Extract deterministic `Linf_rho`, temporal `lambda_l1`, GPU ULP/speedup, and OT/KH 512 gate facts from committed summaries.
- [ ] Build a synthesis JSON schema `{"name": "hrsc.report2-synthesis", "version": 1}`.
- [ ] Include fixed claim boundaries for KH MCA, asymptotic convergence, formal Lyapunov exponent, and HLL GPU scope.
- [ ] Flatten the synthesis into CSV rows with `section,item,status,metric,value,authority`.

### Task 3: Write Summary Files And Figures

- [ ] Implement CLI `python scripts/regression/report2_synthesis.py --output-dir experiments/week17/report2_synthesis`.
- [ ] Write `summary.json`, `summary.csv`, `summary.md`.
- [ ] Generate `figures/axis_ranking.png` and `figures/temporal_divergence.png`.

### Task 4: Register Week 17 Documentation

- [ ] Create `docs/week17/week17-plan.md`.
- [ ] Create `docs/week17/week17-summary.md`.
- [ ] Update `docs/INDEX.md`.
- [ ] Update `docs/HARNESS.md` so the MHD/GPU support table reflects the bounded HLL CUDA path.
- [ ] Update `docs/experiment_logs/report2_evidence_map.md` with a Week 17 synthesis row.

### Task 5: Verify, Commit, And Prepare For Merge

- [ ] Run `pytest tests/py/test_report2_synthesis.py -q`.
- [ ] Run `pytest tests/py -q`.
- [ ] Run `git diff --check`.
- [ ] Run `git ls-files | Select-String -Pattern '\.bin$'`.
- [ ] Commit with `feat(report2): add Week 17 synthesis packet`.
