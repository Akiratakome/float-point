# Report 2 Evidence Canonicalization Design

**Date:** 2026-07-22
**Goal:** Turn the current Report 2 work into a stable, claim-bounded evidence
and documentation structure before any branch integration, while preserving
the existing solver numerics, cfg defaults, output formats, and historical
provenance.

## 1. Scope

This reorganization covers documentation, evidence routing, status labels, and
the safe integration of current Report 2 assets. It does not complete the
remaining GPU HLL MHD, hardware-axis, Kelvin-Helmholtz report-grade, or 512^2
work defined in
`2026-07-21-week15-16-completion-design.md`.

### In scope

- Create one canonical Report 2 evidence map.
- Restore Week 14, Week 15, and Week 16 plan/summary navigation.
- Separate current claims from dated supervisor-meeting snapshots.
- Classify report-grade, provisional, morphology-only, invalid, superseded,
  deferred, and local-only evidence.
- Register the temporal-divergence driver in the top-level scripts index.
- Incorporate the untracked Week 15 English meeting material after aligning
  its filename and historical-snapshot status with repository conventions.
- Preserve `week16-evidence-completion` as an audit branch and prepare a
  verified fast-forward integration path.

### Out of scope

- Solver, CUDA, compiler-flag, or cfg changes.
- Re-running or regenerating numerical experiments.
- Changing existing summary schemas or numerical values.
- Physically consolidating the Euler and MHD harness implementations.
- Merging the obsolete `codex/mhd-temporal-divergence` branch.
- Deleting user-owned untracked files, worktrees, branches, logs, or tools.

## 2. Canonical information architecture

The documentation hierarchy becomes:

1. `docs/requirement/overall.md`: baseline requirements and original schedule,
   not a current implementation-status document.
2. `docs/experiment_logs/report2_evidence_map.md`: the single current source
   of truth for Report 2 evidence status, claim boundaries, supersession, and
   remaining gaps.
3. `docs/weekN/weekN-summary.md`: concise weekly outcome and handoff, linking
   to the evidence map and authoritative summaries.
4. `docs/weekN/weekN-plan.md`: the operational plan used for that week.
5. Dated meeting reports, execution prompts, and brainstorming documents:
   historical snapshots or planning provenance, never current status pages.
6. `experiments/**/summary.{json,csv,md}` and report figures: authoritative
   evidence products; large grids and build outputs remain transient.

`docs/INDEX.md` links to this hierarchy and must not hard-code a mutable active
branch name. `docs/HARNESS.md` retains the canonical
`config -> build -> run -> measure -> aggregate -> plot` contract; this phase
only corrects stale status wording and does not redesign the harness.

## 3. Report 2 evidence status model

Every evidence-map entry records:

- case and solver;
- evidence role;
- dimensions/resolution and sample count;
- gate or validation status;
- authoritative summary and figure paths;
- generating commit or embedded provenance status;
- superseded assets;
- supported claim and explicit exclusions;
- retention state: tracked, local-only, transient, or deferred.

The allowed status labels are:

| Status | Meaning |
|---|---|
| `report-grade` | Machine-readable gate and evidence package support the bounded claim. |
| `provisional` | Data exist, but the authoritative gate or combined summary is incomplete. |
| `validation` | Supports solver/method correctness, not a precision-axis headline claim. |
| `morphology-only` | Supports qualitative benchmark structure only. |
| `negative-result` | A gated analysis did not observe the planned contrast; report the bounded result. |
| `invalid` | Known configuration or instrumentation defect prevents evidential use. |
| `superseded` | Replaced by a named stronger package; retained only for provenance. |
| `deferred` | Planned Report 2 work not yet implemented. |

The current temporal-divergence packet is a `negative-result`: it contains 80
successful provenance-complete runs and passes its report-grade technical gate,
but it does not support the planned Orszag-Tang-grows-faster contrast or a
formal physical Lyapunov exponent claim.

Brio-Wu and Orszag-Tang deterministic/MCA packages are not silently upgraded by
this documentation phase. Where their current human-facing statements exceed
their authoritative machine-readable claim state, the evidence map records
them as `provisional` until a later evidence-consolidation task produces a
unified gate.

## 4. Weekly documentation

Week directories follow the existing post-2026-04-28 convention: only the
canonical `weekN-plan.md` and `weekN-summary.md` are primary top-level entries.
Existing meeting and prompt files may remain at their current paths in this
phase to avoid breaking references; they receive a short dated-snapshot notice
and are indexed as historical material. Physical archival moves are deferred
unless a file has no inbound references.

- Week 14 receives a canonical plan that points to the executed precision-pilot
  design/plan and a summary that distinguishes valid deterministic results from
  the invalid HLL MCA configuration.
- Week 15 receives a canonical plan that points to the solver-aware breadth and
  MCA-depth plans and a summary that routes the four principal CPU packages,
  without claiming a unified gate that does not yet exist.
- Week 16 receives a plan that points to the evidence-completion design and a
  summary of the completed temporal phase plus the remaining GPU/KH/512^2
  phases.

The untracked English meeting document is incorporated as
`docs/week15/week15-supervisor-meeting-EN.md`, matching the Week 13/14 naming
convention. Its content remains a dated 2026-07-09 snapshot; a notice points to
the later evidence map rather than rewriting the historical narrative. The
untracked implementation plan is retained as planning provenance with a status
header identifying it as executed.

## 5. Asset and history policy

The following assets are not imported into the canonical branch:

- the obsolete untracked 50-line temporal test in the root worktree, because
  the branch contains the complete tracked 311-line successor;
- `tmp7reev1u0/`, which is fake-run output;
- `tools/icm2026_export_schedule.py`, which is unrelated to this experiment
  harness;
- smoke grids, build directories, and ignored transient binaries;
- the old temporal branch's post-hoc fit implementation or its derived figure.

No user file is deleted. Excluded assets remain in their existing worktrees
until the user separately requests cleanup.

Historical experiment summaries and logs are not rewritten. Invalid and
superseded packages stay available at their original paths and are excluded by
the evidence map. New report-facing material links to the authoritative newer
package.

## 6. Integration strategy

The commit graph from `main` through `week12-mhd-implementation` to
`week16-evidence-completion` is linear. Integration therefore uses this order:

1. Commit the canonicalization design and implementation on
   `week16-evidence-completion`.
2. Verify links, evidence-map completeness, tracked-file policy, Python tests,
   and a clean diff/worktree.
3. Preserve the `week16-evidence-completion` branch as an audit reference.
4. Protect the final commit with a durable local backup reference; remote push
   is a separate operation requiring repository/network authorization.
5. Deal with the root worktree's conflicting untracked test without deleting
   it, then fast-forward the intended integration branch with `--ff-only`.
6. Do not merge or cherry-pick `codex/mhd-temporal-divergence`.

The actual fast-forward is a separate, explicit integration step after the
reorganization passes verification. If the target branch is not `main`, the
user must identify it before that step.

## 7. Verification

The reorganization must pass:

- a Markdown-link audit for all changed permanent documents;
- an evidence-map audit confirming every Report 2 headline package has a
  status, authoritative path, claim boundary, and supersession entry;
- checks that no `.bin`, build output, ignored smoke package, or unrelated
  untracked asset enters the commit;
- `pytest tests/py -q` because script documentation and indexed entry points
  must still match the tested repository;
- `git diff --check` and a clean tracked worktree;
- an explicit ancestry check proving the selected integration can use
  `git merge --ff-only` and does not include the obsolete temporal branch.

## 8. Completion boundary

This phase is complete when the repository has a single navigable Report 2
evidence source, Week 14-16 current summaries, historically accurate meeting
snapshots, and a verified linear integration path. It does not imply that all
Report 2 experiments are complete. GPU HLL MHD, the hardware axis,
Kelvin-Helmholtz report-grade evidence, 512^2 consolidation, and any later
evidence-package gate promotion remain explicit follow-up work.
