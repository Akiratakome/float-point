# Week 14 Execution Prompt

Use this prompt to start the Week 14 implementation-execution session. It drives
the plan at `docs/superpowers/plans/2026-07-01-week14-mhd-precision-pilot.md`.

```text
Use the `superpowers:subagent-driven-development` skill (fallback:
`superpowers:executing-plans`) to implement the Week 14 HLL MHD precision-study
pilot for this repository, task by task.

Plan to execute (authoritative — follow it exactly, in order):
- docs/superpowers/plans/2026-07-01-week14-mhd-precision-pilot.md

Design spec (context; do not re-derive or re-litigate):
- docs/superpowers/specs/2026-07-01-week14-mhd-plan-design.md

Read first (harness contract + reuse map):
- docs/INDEX.md
- docs/HARNESS.md
- scripts/README.md
- docs/week13/week13-summary.md   (Week 13 handoff: HLL is production, HLLD deferred)

Project context:
- The repository is `floatpoint`. The numerical experiment harness is the
  deliverable. Preserve the pipeline shape:
  config -> build -> run -> measure -> aggregate -> plot.
- Week 14 goal: a thin, gated, claim-bounded HLL MHD precision-study pilot on
  Brio-Wu 1D (CPU only). Only Phase P0 is driven to green in this plan; P1/P2
  are flag-only invocations of the same two drivers (no new code).

Hard constraints (from the plan's Global Constraints — do not violate):
- Do NOT change solver numerics, existing cfg defaults, or existing output
  formats. All work is harness-layer (scripts + tests + docs).
- Brio-Wu 1D, HLL, CPU only. OT/KH 2D, 512^2, GPU MHD, HLLD, and Lyapunov are
  OUT of scope (Week 15+).
- HLLD stays diagnostic/deferred; HLL is the production solver.
- Binary grids are transient (deleted after norms unless --keep-grids); never
  commit grids or build dirs.
- `.gitignore` ignores the whole experiments/ tree plus *.bin / *.csv and
  build-matrix/, so committing ANY Week-14 evidence requires `git add -f`.
  A plain `git status` / `git add` silently skips it.
- summary.json is authoritative (nested gates + MCA + claim buckets);
  summary.csv is a flattened convenience view; matrix_summary_report.py is
  generic run/pair checks only, never authoritative here.
- Diagnostic fields: gate on rho/By/p; report vx as a non-gating continuity
  field. The G1 fastmath/ieee ordering check is a SOFT, non-blocking flag.
- Gate G0 is a HARD checkpoint: the reference row cpu-double-O2-ieee-leq must
  reproduce the Brio-Wu anchor (steps=759, divB_max ~= 4.441e-14), all runs
  must be finite, and the unified summary schema must validate (including a
  cleanly represented blocked_environment MCA outcome). If G0 fails, STOP and
  fix the harness — do not scale to P1/P2.

Accepted deviation baked into the plan: matrix.json is generated as a run
manifest, but each entry is executed via _mhd_harness.run_case (NOT
run_matrix.py), because hrsc_mhd emits no [timing] line and run_matrix.py
captures neither MHD wall-time nor the [mhd] divB/steps diagnostic.

Environment (this Windows workstation):
- Run Python via the project env (has pytest):
  & "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe"
- To build hrsc_mhd with MSVC, load VsDevCmd first (see docs/INDEX.md section 4).
- Verificarlo runs via Docker; if unavailable, the MCA path must return a clean
  blocked_environment and P0 must still pass G0.

Execution discipline:
- Follow each task's TDD steps in order: write the failing test, run it to see
  it FAIL, implement the minimal code, run it to see it PASS, then commit.
  One task at a time. Do not batch tasks or skip the red/green checks.
- Use the exact commands and expected outputs printed in each step.
- Between tasks, keep the full Python suite green:
  & "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests/py -q
- Commit per task with the message shown in the plan; use `git add -f` for any
  path under experiments/.
- Terminal deliverable: Task 9 runs P0 end-to-end, confirms G0 pass, and commits
  the force-added evidence packet. Report summary.md and the G0 result.

Do not start P1/P2 or any 2D / 512^2 / GPU / HLLD work — those are Week 15+.
```
