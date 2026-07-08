# Week 14 Brainstorming Prompt

Use this prompt to start the Week 14 planning session.

```text
Use the `superpowers:brainstorming` skill to design the Week 14 plan for this
repository.

Project context:
- The repository is `floatpoint`. The numerical experiment harness is the
  deliverable. Preserve the pipeline shape:
  `config -> build -> run -> measure -> aggregate -> plot`.
- Read first:
  - `docs/INDEX.md`
  - `docs/HARNESS.md`
  - `scripts/README.md`
- Then read the Week 13 handoff:
  - `docs/week13/week13-summary.md`
  - `docs/week13/paper_benchmark_matrix.md`
  - `experiments/week13/solver_compare/summary.md`
  - `experiments/week13/hlld_glm_sweep/summary.md`
  - `experiments/week13/mhd_verificarlo_smoke/summary.md`
- Week 13 decision: HLL is the Week 14 production MHD solver. HLLD exists but
  is deferred because Orszag-Tang showed elevated divB; treat HLLD as diagnostic
  only unless a later decision record changes this.
- Do not change solver numerics, existing cfg defaults, or existing output
  formats unless I explicitly ask.

Follow the brainstorming process:
1. Summarise the Week 14 goal boundary you infer from the context.
2. Ask exactly one clarifying question first. Prefer asking me to choose the
   primary Week 14 objective:
   A. start the HLL production MHD precision-study matrix;
   B. close OT/KH 512^2 validation gaps first;
   C. investigate the HLLD divB root cause first;
   D. prepare a supervisor-facing Report 2 evidence packet first.
3. After my answer, propose 2-3 Week 14 routes with trade-offs and your
   recommendation.
4. After approval, write the design spec to
   `docs/superpowers/specs/YYYY-MM-DD-week14-mhd-plan-design.md`.
5. Self-review the spec, then ask me to review it. Do not implement directly.

The eventual Week 14 plan must stay:
- harness-first: config/build/run/measure/aggregate/plot;
- scripted and logged: generated cfg, stdout/stderr, metadata, summary for each
  run;
- lightweight first: smoke/minimatrix before expensive 512^2 or cluster runs;
- evidence-safe: do not commit build directories or transient binary grids;
- claim-bounded: distinguish morphology evidence, self-reference validation,
  and precision/noise evidence.
```

